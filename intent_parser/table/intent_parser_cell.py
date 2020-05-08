
class IntentParserCell(object):
    """
    An internal data structure for representing the contents of a table cell.
    """

    def __init__(self, cell):
        self._cell = cell
        self.links = {}
    
    def get_contents(self):
        list_of_contents = []
        content = self._cell['content']
        for paragraph in content['paragraph']:
            for element in paragraph['elements']: 
                for text_run in element['textRun']:
                    result = text_run['content']
                    list_of_contents.append(result)
        return ''.join(list_of_contents)
        
    
    def get_link_from_paragraph(self, paragraph):
        return paragraph['link']['url']
        
        
        