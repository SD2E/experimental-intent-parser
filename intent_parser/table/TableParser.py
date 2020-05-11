class TableParser(object):
    def parse_cell(self, cell):
        pass
    
    def parse_header_row(self, header_row):
        pass
    
class GoogleTableParser(TableParser):
    
    def parse_control_table(self, table): 
        pass 
    
    def parse_header_row(self, header_row):
        TableParser.parse_header_row(self, header_row)
    
    def parse_cell(self, cell):
        content = cell['content']
        for paragraph in content['paragraph']:
            url = None
            
            if 'url' in paragraph['link']:
                url = paragraph['link']['url']
                
            list_of_contents = []
            for element in paragraph['elements']: 
                for text_run in element['textRun']:
                    result = text_run['content']
                    list_of_contents.append(result)
            flatten_content = ''.join(list_of_contents)
            yield flatten_content, url