from config import config
from processed_images.processed_images import LockingProcessedImages, ProcessedImage

from graphene import ObjectType, String, Schema, DateTime, List, Int, Field, Float

from flask import Flask
from flask_graphql import GraphQLView

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


class Query(ObjectType):
    photolist = List(String, startdatetime=DateTime(required=True), enddatetime=DateTime(required=True))
    photo = Field(Photo, filename=String(required=True))

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
                     longitude=p.longitude)

# GraphQL schema created:
schema = Schema(query=Query)

# Flask init
app = Flask(__name__)
app.add_url_rule('/graphql', view_func=GraphQLView.as_view(
    'graphql',
    schema=schema,
    graphiql=True
))

# Serve this out via flask to be picked up in React:
queries = """
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
  }
}

Variables:
{
  "filename": "/work/stash/Photos/Canon EOS M6 II/2020/03/01/CR3/_MG_1014.CR3"
}
"""

if __name__ == '__main__':
    app.run(host='0.0.0.0')