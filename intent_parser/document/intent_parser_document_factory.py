from intent_parser.document.intent_parser_document import IntentParserDocument
import intent_parser.constants.google_doc_api_constants as doc_constants

class IntentParserDocumentFactory(object):

    def __init__(self):
        self._google_document_parser = GoogleDocumentParser()

    def from_google_doc(self, document):
        ip_document = self._google_document_parser.parse_document(document)
        return ip_document

class DocumentParser(object):

    def parse_document(self, document):
        pass


class GoogleDocumentParser(DocumentParser):

    def __init__(self):
        pass

    def parse_document(self, document):
        intent_parser_doc = IntentParserDocument()
        doc_properties = document[doc_constants.BODY][doc_constants.CONTENT]
        paragraph_index = 0
        while len(doc_properties) > 0:
            property = doc_properties.pop(0)
            if doc_constants.PARAGRAPH in property:
                paragraph = self._parse_paragraphs(property[doc_constants.PARAGRAPH])
                paragraph.set_start_index(property[doc_constants.START_INDEX])
                paragraph.set_end_index(property[doc_constants.END_INDEX])
                paragraph.set_paragraph_index(paragraph_index)
                intent_parser_doc.add_paragraph(paragraph)
                paragraph_index += 1
            elif doc_constants.TABLE in property:
                doc_properties = self._get_properties_from_table(property[doc_constants.TABLE]) + doc_properties

        return intent_parser_doc

    def _get_properties_from_table(self, table_property):
        properties = []

        if doc_constants.TABLE_ROWS in table_property:
            for row_property in table_property[doc_constants.TABLE_ROWS]:
                properties.extend(self._get_properties_from_table_row(row_property))
        return properties

    def _get_properties_from_table_row(self, row_property):
        properties = []

        if doc_constants.TABLE_CELLS in row_property:
            for cell_property in row_property[doc_constants.TABLE_CELLS]:
               if doc_constants.CONTENT in cell_property:
                   for content_property in cell_property[doc_constants.CONTENT]:
                        properties.append(content_property)
        return properties

    def _parse_paragraphs(self, paragraph):
        ip_paragraph = self.Paragraph()
        for element in paragraph[doc_constants.ELEMENTS]:
            text_run = element[doc_constants.TEXT_RUN]
            text = text_run[doc_constants.CONTENT]
            if doc_constants.TEXT_STYLE in text_run and doc_constants.LINK in text_run[doc_constants.TEXT_STYLE]:
                link = text_run[doc_constants.TEXT_STYLE][doc_constants.LINK]
                if doc_constants.URL in link:
                    url = link[doc_constants.URL]
                    ip_element = self.Element(text, element[doc_constants.START_INDEX], element[doc_constants.END_INDEX], hyperlink=url)
                    ip_paragraph.add_element(ip_element)
            else:
                ip_element = self.Element(text, element[doc_constants.START_INDEX], element[doc_constants.END_INDEX])
                ip_paragraph.add_element(ip_element)
        return ip_paragraph

    class Paragraph(object):
        def __init__(self):
            self.element = []
            self._start_index = None
            self._end_index = None
            self._paragraph_index = None

        def add_element(self, element):
            self.element.append(element)

        def get_paragraph_index(self):
            return self._paragraph_index

        def get_text(self):
            flatten = [e.text for e in self.element]
            return ''.join(flatten)

        def get_elements_with_hyperlink(self):
            hyperlinked_elements = []
            for element in self.element:
                if element.hyperlink:
                    hyperlinked_elements.append(element)
            return hyperlinked_elements

        def get_start_index(self):
            return self._start_index

        def get_end_index(self):
            return self._end_index

        def set_start_index(self, value):
            self._start_index = value

        def set_end_index(self, value):
            self._end_index = value

        def set_paragraph_index(self, value):
            self._paragraph_index = value

    class Element(object):
        def __init__(self, text, start_index, end_index, hyperlink=None):
            self.text = text
            self.start_index = start_index
            self.end_index = end_index
            self.hyperlink = hyperlink