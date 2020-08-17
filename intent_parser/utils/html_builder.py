import intent_parser.utils.intent_parser_utils as intent_parser_utils
import os

class AddHtmlBuilder(object):
    def __init__(self):
        _curr_path = os.path.dirname(os.path.realpath(__file__))
        html_file = intent_parser_utils.load_file(os.path.join(_curr_path, 'add.html'))
        self.html = html_file 
        
    def common_name(self, common_name):
        self.html = self.html.replace('${COMMONNAME}', common_name)
        return self
    def display_id(self, display_id):
        self.html = self.html.replace('${DISPLAYID}', display_id)
        return self
    def start_paragraph(self, start_paragraph):
        self.html = self.html.replace('${STARTPARAGRAPH}', start_paragraph)
        return self
    def end_paragraph(self, end_paragraph):
        self.html = self.html.replace('${ENDPARAGRAPH}', end_paragraph)
        return self
    def start_offset(self, start_offset):
        self.html = self.html.replace('${STARTOFFSET}', start_offset)
        return self
    def end_offset(self, item_types_html):
        self.html = self.html.replace('${ENDOFFSET}', item_types_html)
        return self
    def item_types_html(self, item_types_html):
        self.html = self.html.replace('${ITEMTYPEOPTIONS}', item_types_html)
        return self
    def lab_ids_html(self, lab_ids_html):
        self.html = self.html.replace('${LABIDSOPTIONS}', lab_ids_html)
        return self
    def selected_term(self, selection):
        self.html = self.html.replace('${SELECTEDTERM}', selection)
        return self
    def document_id(self, document_id):
        self.html = self.html.replace('${DOCUMENTID}', document_id)
        return self
    def is_spell_check(self, isSpellcheck):
        self.html = self.html.replace('${ISSPELLCHECK}', isSpellcheck)
        return self
    def submit_button(self, submit_button):
        self.html = self.html.replace('${SUBMIT_BUTTON}', submit_button)
        return self
    def build(self):
        return self.html

class AnalyzeHtmlBuilder(object):
    def __init__(self):
        _curr_path = os.path.dirname(os.path.realpath(__file__))
        html_file = intent_parser_utils.load_file(os.path.join(_curr_path, 'analyze_sidebar.html'))
        self.html = html_file 
    def selected_term(self, selected_term):
        self.html = self.html.replace('${SELECTEDTERM}', selected_term)
    def selected_uri(self, selected_uri):
        self.html = self.html.replace('${SELECTEDURI}', selected_uri)
    def content_term(self, content_term):
        self.html = self.html.replace('${CONTENT_TERM}', content_term)
    def term_uri(self, term_uri):
        self.html = self.html.replace('${TERM_URI}', term_uri)
    def document_id(self, document_id):
        self.html = self.html.replace('${DOCUMENTID}', document_id)
    def button_html(self, button_html):
        self.html = self.html.replace('${BUTTONS}', button_html)
    def button_script(self, button_script):
        self.html = self.html.replace('${BUTTONS_SCRIPT}', button_script)
    def build(self):
        return self.html

class ControlsTableHtmlBuilder(object):
    def __init__(self):
        _curr_path = os.path.dirname(os.path.realpath(__file__))
        html_file = intent_parser_utils.load_file(os.path.join(_curr_path, 'create_controls_table.html'))
        self.html = html_file  
    def cursor_child_index_html(self, cursor_child_index):
        self.html = self.html.replace('${CURSOR_CHILD_INDEX}', cursor_child_index)
    def control_types_html(self, control_types_html):
        self.html = self.html.replace('${CONTROLTYPEOPTIONS}', control_types_html)
    def build(self):
        return self.html

class MeasurementTableHtmlBuilder(object):
    def __init__(self):
        _curr_path = os.path.dirname(os.path.realpath(__file__))
        html_file = intent_parser_utils.load_file(os.path.join(_curr_path, 'create_measurements_table.html'))
        self.html = html_file 
    def cursor_child_index_html(self, cursor_child_index):
        self.html = self.html.replace('${CURSOR_CHILD_INDEX}', cursor_child_index)
    def lab_ids_html(self, lab_ids_html):
        self.html = self.html.replace('${LABIDSOPTIONS}', lab_ids_html)
    def measurement_types_html(self, measurement_types_html):
        self.html = self.html.replace('${MEASUREMENTOPTIONS}', measurement_types_html)
    def file_types_html(self, file_types_html):
        self.html = self.html.replace('${FILETYPEOPTIONS}', file_types_html)
    def time_unit_html(self, time_unit_html):
        self.html = self.html.replace('${TIMEUNITOPTION}', time_unit_html)
    def build(self):
        return self.html
    
class ParameterTableHtmlBuilder(object):
    def __init__(self):
        _curr_path = os.path.dirname(os.path.realpath(__file__))
        html_file = intent_parser_utils.load_file(os.path.join(_curr_path, 'create_parameter_table.html'))
        self.html = html_file
    def cursor_child_index_html(self, cursor_child_index):
        self.html = self.html.replace('${CURSOR_CHILD_INDEX}', cursor_child_index)
    def protocol_options_html(self, html_protocols):
        self.html = self.html.replace('${PROTOCOLOPTIONS}', html_protocols)
    def build(self):
        return self.html
