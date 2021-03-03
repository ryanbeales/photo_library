import json

class ProcessedImages(object):
    def __init__(self, saved_filename=None):
        self.saved_filename = saved_filename
        self.load()
        
    def load(self):
        if self.saved_filename:
            try:
                with open(self.saved_filename) as f:
                    self.images = json.load(f)
            except:
                self.images = {}

    def add(self, metadata):
        self.images[metadata['filename']] = metadata

    def add_metadata(self, filenames, metadata_fieldname, metadata_value):
        for filename in filenames:
            self.images[filename][metadata_fieldname] = metadata_value
    
    def retrieve(self, filename):
        if filename in self.images.keys():
            return self.images[filename]
        else:
            return None
    
    def save(self):
        with open(self.saved_filename, 'w') as f:
            f.write(json.dumps(self.images))
    def commit(self):
        pass