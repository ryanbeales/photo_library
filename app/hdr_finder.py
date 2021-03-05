from datetime import timedelta
import logging
logger = logging.getLogger(__name__)


class HDRFinder(object):
    def __init__(self, processed_image=None, max_duration_for_set=5):
        if processed_image != None:
            self.processed_image = processed_image
        self.HDR_group = []
        self.max_duration_for_set = timedelta(seconds=max_duration_for_set)
    
    def check(self, metadata):
        if metadata.bracket_mode == 1:
            print('found a bracketed photo', metadata.filename, metadata.bracket_shot_count)
            self.HDR_group.append(metadata)
            if len(self.HDR_group) == metadata.bracket_shot_count:
                print('weve got the right number of photoos now...')
                if (self.HDR_group[-1].date_taken - self.HDR_group[1].date_taken) <= self.max_duration_for_set:
                    print('this is a HDR set:')
                    filenames = [i.filename for i in self.HDR_group]
                    print('filenames:', filenames)
                    self.processed_image.create_hdr_set(filenames)
                    # Reset group
                    self.HDR_group = []