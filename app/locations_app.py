from locations.locations import Locations
from processed_images.processed_images import ProcessedImages

if __name__ == '__main__':
    locations=Locations(history_file='/work/stash/Backup/Google Location History/Location History.json', history_db_dir='/work/stash/src/classification_output/', reload=False)

    # Scan for locations.
    photos = ProcessedImages(db_dir='/work/stash/src/classification_output/')
    photos.load()
    
    for photo in photos.get_file_list():
        p = photos.retrieve(photo)
        l = locations.get_location_at_timestamp(p.date_taken)
        print(f'Photo: {p.filename} taken at {p.date_taken}, likely taken at coords {l}')