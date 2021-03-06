from datetime import timedelta
import logging
logger = logging.getLogger(__name__)


class HDRFinder(object):
    def __init__(self, processed_image=None, max_duration_for_set=5):
        logger.debug(f'Creating HDR Finder, max duration between photos = {max_duration_for_set} seconds')
        if processed_image != None:
            self.processed_image = processed_image
        self.HDR_group = []
        self.max_duration_for_set = timedelta(seconds=max_duration_for_set)
    
    def check(self, metadata):
        if metadata.bracket_mode == 1:
            logger.debug(f'found bracketed photo {metadata.filename}, should be {metadata.bracket_shot_count} photos in set')

            self.HDR_group.append(metadata)
            if len(self.HDR_group) == metadata.bracket_shot_count:
                logger.debug(f'found {metadata.bracket_shot_count} photos, checking if HDR group')
                logger.debug(f'first photo taken at {self.HDR_group[1].date_taken}, last photo taken at {self.HDR_group[-1].date_taken}')
                if (self.HDR_group[-1].date_taken - self.HDR_group[1].date_taken) <= self.max_duration_for_set:
                    filenames = [i.filename for i in self.HDR_group]
                    logger.info(f"found HDR set {','.join(filenames)}")
                    self.processed_image.create_hdr_set(filenames)

                    logger.debug('resetting hdr group list to find more')
                    self.HDR_group = []