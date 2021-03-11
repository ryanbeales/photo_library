from datetime import timedelta
import logging
logger = logging.getLogger(__name__)

from processed_images.processed_images import ProcessedImages, ProcessedImage

HDR_query = """
Select filename1, filename2, filename3, exc1, exc2, exc3 from (
	SELECT 
		filename1, filename2, filename3, exc1, exc2, exc3,
		LAG (filename1, 1, 0) OVER (ORDER BY filename3, filename2, filename1) AS last_filename1
	FROM (
	SELECT filename1, filename2, filename3, exc1, exc2, exc3 FROM (
		SELECT filename AS filename1,
			CAST(json_extract(exif_data, '$.EXIF:ExposureCompensation') AS REAL) AS exc1, 
			LAG (filename, 1, 0) OVER (ORDER BY filename, date_taken) AS filename2,
			CAST(LAG (json_extract(exif_data, '$.EXIF:ExposureCompensation'), 1, 0) OVER (ORDER BY filename, date_taken) AS REAL) AS exc2,
			LAG (filename, 2, 0) OVER (ORDER BY filename, date_taken) AS filename3,
			CAST(LAG (json_extract(exif_data, '$.EXIF:ExposureCompensation'), 2, 0) OVER (ORDER BY filename, date_taken) AS REAL) AS exc3
		FROM photos)
		WHERE
			exc1 != exc2
		AND exc2 != exc3
		AND exc3 != exc1
		AND ((exc1 = 0 AND ABS(exc2) = ABS(exc3)) OR (exc2 = 0 AND ABS(exc1) = ABS(exc3)) OR (exc3 = 0 AND ABS(exc1) = ABS(exc2)))
	)
	)
WHERE
  filename2 != last_filename1 AND filename3 != last_filename1
;
"""

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

if __name__ == '__main__':
    # Scan for HDRs.
    # EXIF:ExposureCompensation is what we want.
    photos = ProcessedImages(db_dir='/work/stash/src/classification_output/')
    for photo in photos.get_file_list():
        p = photos.retrieve(photo)
        print(f'Photo: {p.filename} taken at {p.date_taken}')
    
