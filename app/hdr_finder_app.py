from config import config

from datetime import timedelta
import logging
logger = logging.getLogger(__name__)

from pprint import pprint

from processed_images.processed_images import ProcessedImages, ProcessedImage


class HDRProcessedImages(ProcessedImages):
    def __init__(self, db_dir):
        super().__init__(db_dir)

        # logger.debug('Create aeb table if not exists')
        # self.conn.execute('''
        #     CREATE TABLE IF NOT EXISTS aeb_groups (
        #         group_id TEXT NOT NULL,
        #         filename1 TEXT NOT NULL,
        #         filename2 TEXT NOT NULL,
        #         filename3 TEXT NOT NULL,
        #         processed TEXT NOT NULL
        #     );
        # ''')
        # #self.conn.execute('''CREATE UNIQUE INDEX IF NOT EXISTS photos_filename_ids on photos(filename);''')

    def find_hdr_groups(self):
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

        rs = self.conn.execute(HDR_query)
        return rs

    def process_hdr(self, group_id):
        pass

if __name__ == '__main__':
    photos = HDRProcessedImages(db_dir=config['photo_database']['database_dir'])

    r = photos.find_hdr_groups()
    
    pprint(r)