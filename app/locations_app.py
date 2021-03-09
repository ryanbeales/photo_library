from locations.locations import Locations
from processed_images.processed_images import ProcessedImages
from progress.bar import Bar

if __name__ == '__main__':
    reprocess = False

    locations=Locations(history_file='/work/stash/Backup/Google Location History/Location History.json', history_db_dir='/work/stash/src/classification_output/', reload=False)

    # Scan for locations.
    photos = ProcessedImages(db_dir='/work/stash/src/classification_output/')
    photos.load()
    
    if reprocess:
        photolist = photos.get_file_list()
    else:
        photolist = photos.get_empty_locations()

    if not photolist:
        print('Everything already has a location, doing nothing')
        exit()

    progress = Bar('Processing photo locations', width=110, max=len(photolist), suffix='%(index)d/%(max)d - %(eta)ds')

    for photo in photolist:
        p = photos.retrieve(photo)
        # Check if it's already in the Exif here...

        # We're looking for these:
        #     "EXIF:GPSLatitudeRef": "N",
        #     "EXIF:GPSLatitude": 50.1818237302778,
        #     "EXIF:GPSLongitudeRef": "W",
        #     "EXIF:GPSLongitude": 120.526573181111,
        # If latitude ref is S, then negate latitude number
        # If longitude ref is E, then negate longitude number
        # This might be better data than location history? I'd hope not.


        if all([key in p.exif_data for key in ['EXIF:GPSLatitudeRef','EXIF:GPSLatitude','EXIF:GPSLongitudeRef','EXIF:GPSLongitude']]):
            lat = p.exif_data['EXIF:GPSLatitude']
            lng = p.exif_data['EXIF:GPSLongitude']

            if p.exif_data['EXIF:GPSLatitudeRef'] == 'S':
                lat = -lat
            if p.exif_data['EXIF:GPSLongitudeRef'] == 'E':
                lng = -lng
            l = [lat,lng]
        else:
            l = locations.get_location_at_timestamp(p.date_taken)
        progress.next()

    progress.finish()
    photos.commit()
    photos.close()