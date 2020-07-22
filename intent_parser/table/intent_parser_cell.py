class IntentParserCell(object):
    """
    An internal data structure for representing the contents of a table cell.
    """

    def __init__(self):
        self.paragraphs = []
        self.properties = {}
        self.start_index = None
        self.end_index = None
    
    def add_paragraph(self, content, link=None, bookmark_id=None):
        """
        Insert a paragraph to this cell.
        Args:
            content: A string
            link: A string reprsenting a url. Default value set to None is no value is provided.
            bookmark_id: A String representing a bookmark id.
        """
        self.paragraphs.append(self.Paragraph(content, link, bookmark_id))
    
    def get_bookmark_ids(self):
        return [p.bookmark_id for p in self.paragraphs if p.bookmark_id]

    def get_start_index(self):
        return self.start_index

    def get_end_index(self):
        return self.end_index
                  
    def get_text(self):
        flatten = [p.paragraph for p in self.paragraphs]
        return ' '.join(flatten)
    
    def get_text_with_url(self):
        return {p.paragraph: p.link for p in self.paragraphs}

    def set_start_index(self, index):
        self.start_index = index

    def set_end_index(self, index):
        self.end_index = index
        
    class Paragraph(object):
        def __init__(self, paragraph, link, bookmark_id):
            self.paragraph = paragraph
            self.link = link
            self.bookmark_id = bookmark_id
            
  
        