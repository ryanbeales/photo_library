from config import config
from processed_images.processed_images import LockingProcessedImages
from progress.bar import Bar

from datetime import datetime

import folium
import folium.plugins as folium_plugins

import os

import base64
import io
from PIL import Image

from concurrent.futures import ThreadPoolExecutor, wait, ALL_COMPLETED

import logging
logger = logging.getLogger(__name__)


def make_popup(imagedata):
    img = Image.open(io.BytesIO(base64.b64decode(imagedata)))
    width, height = 128, 128
    img.thumbnail((width, height, ))

    buffered = io.BytesIO()
    img.save(buffered, format="JPEG")
    result = base64.b64encode(buffered.getvalue()).decode('utf-8')

    html = '<img src="data:image/jpeg;base64,{}">'.format
    iframe = folium.IFrame(html(result), width=width+20, height=height+20)
    return folium.Popup(iframe, max_width=width+20)

def single_image_process(photos, photo, progress_callback):
    p = photos.retrieve(photo)

    location = [p.latitude, p.longitude]
    popup = make_popup(p.thumbnail)
    icon = folium.Icon(color='red', icon='ok')

    progress_callback()
    return location, popup, icon

    

def date_range_map(photos, start_date, end_date):
    print(f'Generating marker cluster map for date range: {start_date} - {end_date}')

    photodaterange = photos.get_file_list_date_range(start_date, end_date)

    mapdata = []
    mappopups = []
    mapicons = []

    print('Launching threads to process markers')

    progress = Bar('Making markers', width=110, max=len(photodaterange), suffix='%(index)d/%(max)d - %(eta)ds')

    with ThreadPoolExecutor() as executor:
        results = [
            executor.submit(
                single_image_process,
                photos, 
                photo, 
                progress.next
            )
            for photo in photodaterange
        ]
        wait(results, return_when=ALL_COMPLETED)

        print('Threads completed, getting results')
        for result in results:
            if result.result():
                location, popup, icon = result.result()
                mapdata.append(location)
                mappopups.append(popup)
                mapicons.append(icon)

    progress.finish()

    print('Adding points to map...')
    mc = folium_plugins.MarkerCluster(
        locations = mapdata,
        popups = mappopups,
        icons = mapicons
    )

    m = folium.Map(control_scale=True)
    m.add_child(mc)
    m.save(config['DEFAULT']['output_dir'] + os.sep + 'marker_cluster.html')

    print('Marker cluster map generated!')


def heatmap(photos):
    print('Generating heat map')
    m = folium.Map(control_scale=True)
    locations = photos.get_locations()
    data = [[r[1],r[2]] for r in locations]
    heatmap = folium_plugins.HeatMap(data)
    m.add_child(heatmap)
    m.save(config['DEFAULT']['output_dir'] + os.sep + 'heatmap.html')
    print('Done generating heat map')


if __name__ == '__main__':
    photos = LockingProcessedImages(db_dir=config['photo_database']['database_dir'])
    photos.load()
    
    if config['map_maker'].getboolean('heatmap'):
        heatmap(photos)

    if config['map_maker'].getboolean('date_range_map'):
        start_date = datetime.strptime(config['map_maker']['date_range_start'], '%d-%m-%Y')
        end_date = datetime.strptime(config['map_maker']['date_range_end'], '%d-%m-%Y')
        date_range_map(photos, start_date, end_date)

    photos.close()