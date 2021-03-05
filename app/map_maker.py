import folium
import folium.plugins as folium_plugins

import logging
logger = logging.getLogger(__name__)


class MapMaker(object):
    def __init__(self, processed_images):
        self.processed_images = processed_images
    
    def make_map(self, filename):
        m = folium.Map(control_scale=True)

        def make_popup(imagedata):
            width, height = 64, 64
            html = '<img src="data:image/jpeg;base64,{}">'.format
            iframe = folium.IFrame(html(imagedata), width=width+20, height=height+20)
            return folium.Popup(iframe, max_width=64)

        mc = folium_plugins.MarkerCluster(
            locations = [i['location'] for i in self.processed_images.images.values()],
            popups = [make_popup(v['thumbnail']) for v in self.processed_images.images.values()],
            icons = [folium.Icon(color='red', icon='ok') for i in self.processed_images.images.values()]
        )

        m.add_child(mc)
        m.save(filename)