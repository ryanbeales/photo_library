from datetime import timedelta

class HDRFinder(object):
    def __init__(self, processed_image=None, max_duration_for_set=5):
        if processed_image != None:
            self.processed_image = processed_image
        self.HDR_group = []
        self.max_duration_for_set = timedelta(seconds=max_duration_for_set)
    
    def check(self, metadata):
        if metadata['bracket_mode'] == 1:
            self.HDR_group.append(metadata)
            if len(self.HDR_group) == metadata['bracket_shot_count']:
                if (self.HDR_group[-1].get_photo_date() - self.HDR_group[1].get_photo_date()) <= self.max_duration_for_set:
                    filenames = [i['filename'] for i in self.HDR_group]
                    self.processed_image.add_metadata(filenames, 'hdr_group', filenames)
            
                    # Reset group
                    self.HDR_group = []