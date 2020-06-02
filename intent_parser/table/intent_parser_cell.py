
class IntentParserCell(object):
    """
    An internal data structure for representing the contents of a table cell.
    """

    def __init__(self):
        self.paragraphs = []
    
    def add_paragraph(self, content, link=None, bookmark_id=None):
        self.paragraphs.append(self.Paragraph(content, link, bookmark_id))
    
    def get_bookmark_ids(self):
        return [p.bookmark_id for p in self.paragraphs if p.bookmark_id]
                  
    def get_text(self):
        flatten = [p.paragraph for p in self.paragraphs]
        return ''.join(flatten)
    
    def get_text_with_url(self):
        return {p.paragraph: p.link for p in self.paragraphs}
        
    class Paragraph(object):
        def __init__(self, paragraph, link, bookmark_id):
            self.paragraph = paragraph
            self.link = link
            self.bookmark_id = bookmark_id
            


        
        