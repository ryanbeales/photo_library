from config import config

import sys
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
        #         output_filename TEXT NOT NULL
        #     );
        # ''')
        # #self.conn.execute('''CREATE UNIQUE INDEX IF NOT EXISTS photos_filename_ids on photos(filename);''')

    def find_hdr_groups(self):
        # STEP 1: Create a view of all sequences of three photos:
        logger.debug('''Create temp table of all sequences of three raw photos''')
        self._run_query("""
            CREATE TEMP VIEW IF NOT EXISTS v_raw_sequence AS
                SELECT 
                    -- First photo in sequence, two rows previous ordered by filename/ date taken
                    LAG (filename, 2, 0) OVER (ORDER BY filename, date_taken) AS filename1,
                    CAST(LAG (json_extract(exif_data, '$.EXIF:ExposureCompensation'), 2, 0) OVER (ORDER BY filename, date_taken) AS REAL) AS exc1,

                    -- Second photo in sequence, one row previous ordered by filename/date taken
                    LAG (filename, 1, 0) OVER (ORDER BY filename, date_taken) AS filename2,
                    CAST(LAG (json_extract(exif_data, '$.EXIF:ExposureCompensation'), 1, 0) OVER (ORDER BY filename, date_taken) AS REAL) AS exc2,

                    -- Third photo in sequence (this row)
                    filename AS filename3,
                    CAST(json_extract(exif_data, '$.EXIF:ExposureCompensation') AS REAL) AS exc3
                FROM photos 
                WHERE filetype = 'RAW'
        """)


        # STEP 2: Of those three photos, make sure the exposure compensation is:
        # - one exposure compensation is 0,
        # - The other two values are the same absolute value (abs(-1) = abs(1))
        # - The other two values are not equal to each other (-1 != 1)
        # So we have one of these six combinations that we can find:
        #  0,+,-; 0,-,+; -,0,+; +,0,-; -,+,0; +,-,0
        logger.debug('''Create temporary table of all potential AEB's in that sequence of all photos''')
        self._run_query("""
            CREATE TEMP VIEW IF NOT EXISTS v_raw_aeb_sequence AS
                SELECT 
                    filename1, exc1, 
                    filename2, exc2, 
                    filename3, exc3 
                FROM temp.v_raw_sequence
                WHERE
                    (
                        (exc1 = 0 AND ABS(exc2) = ABS(exc3) AND exc2 != exc3) 
                        OR (exc2 = 0 AND ABS(exc1) = ABS(exc3) AND exc1 != exc3) 
                        OR (exc3 = 0 AND ABS(exc1) = ABS(exc2) AND exc1 != exc2)
                    );
        """)

        # STEP 3: Of all potential AEB sequences, find only the unique sets of three:
        logger.debug('Find all unique sequences of AEB sets')
        rs = self._run_query("""
            SELECT
                filename1, exc1,
                filename2, exc2,
                filename3, exc3,
                previous_filename2, 
                previous_filename3
            FROM (
                SELECT 
                    filename1, exc1,
                    filename2, exc2,
                    filename3, exc3,
                    LAG(filename2, 1 ,0) OVER (ORDER BY filename1) previous_filename2,
                    LAG(filename3, 1 ,0) OVER (ORDER BY filename1) previous_filename3
                FROM
                    temp.v_raw_aeb_sequence
                ORDER BY
                    filename1)
            WHERE
                filename1 != previous_filename2
                AND filename1 != previous_filename3
            ORDER BY
                filename1
        """)
        return rs.fetchall()

    def process_hdr(self, group_id):
        pass

if __name__ == '__main__':
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

    logger.info('Loading Photo Database...')
    output_directory = config['hdr_finder']['output_directory']
    photos = HDRProcessedImages(db_dir=config['photo_database']['database_dir'])
    photos.load()

    # Find HDRs and update database
    logger.info('Running HDR Query...')
    r = photos.find_hdr_groups()

    # Make HDRs
    # OpenCV? 

    pprint(r)

    photos.close()