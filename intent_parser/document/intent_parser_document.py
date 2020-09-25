class IntentParserDocument(object):
    """
    An internal data structure for representing the contents of a table cell.
    """

    def __init__(self):
        self.paragraphs = []

    def add_paragraph(self, paragraph):
        self.paragraphs.append(paragraph)

    def get_paragraphs(self):
        return self.paragraphs
