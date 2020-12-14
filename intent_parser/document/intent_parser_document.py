
class IntentParserDocument(object):
    """
    An internal data structure for representing the contents of a document.
    """

    def __init__(self):
        self.paragraphs = []

    def add_paragraph(self, paragraph):
        self.paragraphs.append(paragraph)

    def get_paragraph(self, index):
        if index < 0 or index >= len(self.paragraphs):
            raise IndexError('Getting a paragraph from Intent Parser Document has to be within range %d to %d but got %d.' % (0, len(self.paragraphs)-1, index))

        return self.paragraphs[index]

    def get_paragraphs(self):
        return self.paragraphs
