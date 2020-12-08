
class DocumentLocation(object):

    def __init__(self):
        self.paragraph_index = 0
        self.start_offset = 0

    def get_paragraph_index(self):
        return self.paragraph_index

    def get_start_offset(self):
        return self.start_offset

    def set_paragraph_index(self, index_value):
        self.paragraph_index = index_value

    def set_start_offset(self, offset_value):
        self.start_offset = offset_value

