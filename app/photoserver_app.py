from config import config
from processed_images.processed_images import LockingProcessedImages, ProcessedImage
from hdr_finder_app import HDRProcessedImages

from graphene import ObjectType, String, Schema, DateTime, List, Int, Field, Float, JSONString

from flask import Flask
from flask_graphql import GraphQLView
from flask_cors import CORS


import logging
import sys


photos = LockingProcessedImages(db_dir=config['photo_database']['database_dir'])
photos.load()

class Photo(ObjectType):
    filetype = String()
    filename = String(required=True)
    thumbnail = String()
    datetaken = DateTime()
    latitude = Float()
    longitude = Float()
    exifdata = JSONString()

class HDRGroup(ObjectType):
  group = List(String)

class Query(ObjectType):
    photolist = List(String, startdatetime=DateTime(required=True), enddatetime=DateTime(required=True))
    photo = Field(Photo, filename=String(required=True))
    hdrgroups = List(HDRGroup)

    @staticmethod
    def resolve_photolist(root, info, startdatetime, enddatetime):
        return photos.get_file_list_date_range(startdatetime, enddatetime)

    @staticmethod
    def resolve_photo(root, info, filename):
        p = photos.retrieve(filename)

        return Photo(filetype=p.filetype, 
                     filename=p.filename, 
                     thumbnail=p.thumbnail, 
                     datetaken=p.date_taken, 
                     latitude=p.latitude, 
                     longitude=p.longitude,
                     exifdata=p.exif_data)

    @staticmethod
    def resolve_hdrgroups(root, info):
        return [HDRGroup(group=[
            '/work/stash/Photos/M3/2017/03/04/CR2/IMG_4719.CR2',
            '/work/stash/Photos/M3/2017/03/04/CR2/IMG_4720.CR2',
            '/work/stash/Photos/M3/2017/03/04/CR2/IMG_4721.CR2'
        ])]


# GraphQL schema created:
schema = Schema(query=Query)

# Flask init
app = Flask(__name__)
CORS(app)

app.add_url_rule('/graphql', view_func=GraphQLView.as_view(
    'graphql',
    schema=schema,
    graphiql=True
))

# Serve this out via flask to be picked up in React:
@app.route('/queries')
def queries():
  return """
query getPhotolist {
  photolist(startdatetime: "2020-03-01T00:00:00", enddatetime: "2020-03-02T00:00:00")
}

query getPhoto($filename: String!) {
  photo(filename: $filename) {
    filetype
    filename
    datetaken
    latitude
    longitude
    thumbnail
    exifdata
  }
}

query gethdrgroups {
  hdrgroups {
    group
  }
}
"""

if __name__ == '__main__':
    app.run(host='0.0.0.0')