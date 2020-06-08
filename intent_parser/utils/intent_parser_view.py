"""
Contains functionalities for generating views related to intent parser
"""
from intent_parser.accessor.catalog_accessor import CatalogAccessor
from intent_parser.utils.html_builder import AddHtmlBuilder, AnalyzeHtmlBuilder, ControlsTableHtmlBuilder, MeasurementTableHtmlBuilder, ParameterTableHtmlBuilder
import logging

logger = logging.getLogger('intent_parser_server')

def create_table_template(position_in_document, table_data, table_type, col_sizes):
    create_table = {}
    create_table['action'] = 'addTable'
    create_table['cursorChildIndex'] = position_in_document
    create_table['tableData'] = table_data
    create_table['tableType'] = table_type
    create_table['colSizes'] = col_sizes
    return [create_table]

def create_controls_table_dialog(cursor_index):
    catalog_accessor = CatalogAccessor()
    control_types_html = generate_html_options(catalog_accessor.get_control_type()) 
    control_types_html = control_types_html.replace('\n', ' ')
    builder = ControlsTableHtmlBuilder()
    builder.cursor_child_index_html(cursor_index) 
    builder.control_types_html(control_types_html)
    html = builder.build()
    dialog_action = modal_dialog(html, 'Create Controls Table', 600, 600)
    return dialog_action
    
def create_parameter_table_template(cursor_child_index, protocol_options):
    html_protocols = generate_html_options(protocol_options)
    builder = ParameterTableHtmlBuilder()
    builder.cursor_child_index_html(cursor_child_index)
    builder.protocol_options_html(html_protocols)
    html_parameter = builder.build() 
    
    dialog_action = modal_dialog(html_parameter, 'Create Parameter Table', 600, 600)
    return dialog_action

def create_measurement_table_template(cursor_child_index):
    catalog_accessor = CatalogAccessor()
    local_file_types = catalog_accessor.get_file_types().copy()
    local_file_types.insert(0,'---------------')
    local_file_types.insert(0,'CSV')
    local_file_types.insert(0,'PLAIN')
    local_file_types.insert(0,'FASTQ')
    local_file_types.insert(0,'FCS')

    lab_ids_html = generate_html_options(catalog_accessor.get_lab_ids())
    measurement_types_html = generate_html_options(catalog_accessor.get_measurement_types())
    file_types_html = generate_html_options(local_file_types)

    measurement_types_html = measurement_types_html.replace('\n', ' ')
    file_types_html = file_types_html.replace('\n', ' ')
    
    builder = MeasurementTableHtmlBuilder()
    builder.cursor_child_index_html(cursor_child_index) 
    builder.lab_ids_html(lab_ids_html) 
    builder.measurement_types_html(measurement_types_html) 
    builder.file_types_html(file_types_html)
    html = builder.build()

    dialog_action = modal_dialog(html, 'Create Measurements Table', 600, 600)
    return dialog_action


def generate_existing_link_html(title, target, two_col = False):
        if two_col:
            width = 175
        else:
            width = 350

        html  = '<tr>\n'
        html += '  <td style="max-width: %dpx; word-wrap: break-word; padding:5px">\n' % width
        html += '    <a href=' + target + ' target=_blank name="theLink">' + title + '</a>\n'
        html += '  </td>\n'
        html += '  <td>\n'
        html += '    <input type="button" name=' + target + ' value="Link"\n'
        html += '    title="Create a link with this URL." onclick="linkItem(thisForm, this.name)">\n'
        if not two_col:
            html += '  </td>\n'
            html += '  <td>\n'
        else:
            html += '  <br/>'
        html += '    <input type="button" name=' + target + ' value="Link All"\n'
        html += '    title="Create a link with this URL and apply it to all matching terms." onclick="linkAll(thisForm, this.name)">\n'
        html += '  </td>\n'
        html += '</tr>\n'

        return html
           
def generate_html_options(options):
    options_html = ''
    for item_type in options:
        options_html += '          '
        options_html += '<option>'
        options_html += item_type
        options_html += '</option>\n'

    return options_html
    
def get_download_link(host, document_id):
    return '<a href=http://' + host + '/document_request?' + document_id + ' target=_blank>here</a> \n\n'

def create_add_to_synbiohub_dialog(selection, 
                                   display_id, 
                                   start_paragraph, 
                                   start_offset, 
                                   end_paragraph, 
                                   end_offset, 
                                   item_types_html,
                                   lab_ids_html, 
                                   document_id, 
                                   isSpellcheck):
    
    html_builder = AddHtmlBuilder().common_name(selection) \
                                   .display_id(display_id) \
                                   .start_paragraph(str(start_paragraph)) \
                                   .start_offset(str(start_offset)) \
                                   .end_paragraph(str(end_paragraph)) \
                                   .end_offset(str(end_offset)) \
                                   .item_types_html(item_types_html) \
                                   .lab_ids_html(lab_ids_html) \
                                   .selection(selection) \
                                   .document_id(document_id) \
                                   .isSpellcheck(str(isSpellcheck)) 
    submit_button_html = '        <input type="button" value="Submit" id="submitButton" onclick="submitToSynBioHub()">'
    if isSpellcheck:
        submit_button_html = """
            <input type="button" value="Submit" id="submitButton" onclick="submitToSynBioHub()">
            <input type="button" value="Submit, Link All" id="submitButtonLinkAll" onclick="submitToSynBioHubAndLinkAll()">
        """
    
    html = html_builder.submit_button(submit_button_html).build()

    dialog_action = modal_dialog(html, 'Add to SynBioHub', 600, 600)
    return dialog_action
    
def invalid_request_model_dialog(messages):
    text_area_rows = 33
    height = 600
    title = 'Structured request validation: Failed!'
    buttons = [('Ok', 'process_nop')]
    validation_message = '\n'.join(messages)
    msg = "<textarea cols='80' rows='%d'> %s </textarea>" % (text_area_rows, validation_message)
    return simple_modal_dialog(msg, buttons, title, 500, height)


def highlight_text(paragraph_index, offset, end_offset):
    highlight_text = {}
    highlight_text['action'] = 'highlightText'
    highlight_text['paragraph_index'] = paragraph_index
    highlight_text['offset'] = offset
    highlight_text['end_offset'] = end_offset

    return highlight_text

def link_text(paragraph_index, offset, end_offset, url):
    link_text = {}
    link_text['action'] = 'linkText'
    link_text['paragraph_index'] = paragraph_index
    link_text['offset'] = offset
    link_text['end_offset'] = end_offset
    link_text['url'] = url

    return link_text

def modal_dialog(html, title, width, height):
    action = {}
    action['action'] = 'showModalDialog'
    action['html'] = html
    action['title'] = title
    action['width'] = width
    action['height'] = height

    return action

def operation_failed(message):
    return {'results': {'operationSucceeded': False,
                        'message': message}
    }

def progress_sidebar_dialog():
    """
    Generate the HTML to display analyze progress in a sidebar.
    """
    htmlMessage  = '''
    <script>
    var interval = 1250; // ms
    var expected = Date.now() + interval;
    setTimeout(progressUpdate, 10);
    function progressUpdate() {
        var dt = Date.now() - expected; // the drift (positive for overshooting)
        if (dt > interval) {
            // something really bad happened. Maybe the browser (tab) was inactive?
            // possibly special handling to avoid futile "catch up" run
        }

        google.script.run.withSuccessHandler(refreshProgress).getAnalyzeProgress();

        expected += interval;
        setTimeout(progressUpdate, Math.max(0, interval - dt)); // take into account drift
    }

    function refreshProgress(prog) {
        var table = document.getElementById('progressTable')
        table.innerHTML = '<i>Analyzing, ' + prog + '% complete</i>'
    }

    var table = document.getElementById('progressTable')
    table.innerHTML = '<i>Analyzing, 0% complete</i>'
    </script>

    <center>
      <table stype="width:100%" id="progressTable">
      </table>
    </center>
        '''

    action = {}
    action['action'] = 'showProgressbar'
    action['html'] = htmlMessage

    return action


def create_search_result_dialog(term, uri, content_term, document_id, paragraph_index, offset, end_offset):
    actions = []
    actions.append(highlight_text(paragraph_index, offset, end_offset))
    
    buttons = [('Yes', 'process_analyze_yes', 'Creates a hyperlink for the highlighted text, using the suggested URL.'),
               ('No', 'process_analyze_no', 'Skips this term without creating a link.'),
               ('Yes to All', 'process_link_all', 'Creates a hyperlink for the highilghted text and every instance of it in the document, using the suggested URL.'),
               ('No to All', 'process_no_to_all', 'Skips this term and every other instance of it in the document.'),
               ('Never Link', 'process_never_link', 'Never suggest links to this term, in this document or any other.')]

    buttonHTML = ''
    buttonScript = ''
    for button in buttons:
        buttonHTML += '<input id=' + button[1] + 'Button value="'
        buttonHTML += button[0] + '" type="button" title="'
        buttonHTML += button[2] + '" onclick="'
        buttonHTML += button[1] + 'Click()" />\n'

        buttonScript += 'function ' + button[1] + 'Click() {\n'
        buttonScript += '  google.script.run.withSuccessHandler'
        buttonScript += '(onSuccess).buttonClick(\''
        buttonScript += button[1]  + '\')\n'
        buttonScript += '}\n\n'

    buttonHTML += '<input id=EnterLinkButton value="Manually Enter Link" type="button" title="Enter a link for this term manually." onclick="EnterLinkClick()" />'
    # Script for the EnterLinkButton is already in the HTML

    html = AnalyzeHtmlBuilder().selected_term(term) \
                               .selected_uri(uri) \
                               .content_term(content_term) \
                               .term_uri(uri) \
                               .document_id(document_id) \
                               .button(buttonHTML) \
                               .buttonScript(buttonScript).build()

    dialogAction = sidebar_dialog(html)
    actions.append(dialogAction)
    return actions

def report_spelling_results(client_state):
    """Generate actions for client, given the current spelling results index
    """
    spellCheckResults = client_state['spelling_results']
    resultIdx = client_state['spelling_index']

    actionList = []

    start_par = spellCheckResults[resultIdx]['select_start']['paragraph_index']
    start_cursor = spellCheckResults[resultIdx]['select_start']['cursor_index']
    end_par = spellCheckResults[resultIdx]['select_end']['paragraph_index']
    end_cursor = spellCheckResults[resultIdx]['select_end']['cursor_index']
    
    if not start_par == end_par:
        logger.error('Received a highlight request across paragraphs, which is currently unsupported!')
    
    highlightTextAction = highlight_text(start_par, start_cursor, end_cursor)
    actionList.append(highlightTextAction)

    html = '<center>'
    html += 'Term %s not found in dictionary, potential addition?' % spellCheckResults[resultIdx]['term']
    html += '</center>'

    manualLinkScript = """

    function EnterLinkClick() {
        google.script.run.withSuccessHandler(enterLinkHandler).enterLinkPrompt('Manually enter a SynbioHub link for this term.', 'Enter URI:');
    }

    function enterLinkHandler(result) {
        var shouldProcess = result[0];
        var text = result[1];
        if (shouldProcess) {
            var data = {'buttonId' : 'spellcheck_link',
                     'link' : text}
            google.script.run.withSuccessHandler(onSuccess).buttonClick(data)
        }
    }

        """

    buttons = [{'value': 'Ignore', 'id': 'spellcheck_add_ignore', 'title' : 'Skip the current term.'},
               {'value': 'Ignore All', 'id': 'spellcheck_add_ignore_all', 'title' : 'Skip the current term and any other instances of it.'},
               {'value': 'Add to Spellchecker Dictionary', 'id': 'spellcheck_add_dictionary', 'title' : 'Add term to the spellchecking dictionary, so it won\'t be considered again.'},
               {'value': 'Add to SynBioHub', 'id': 'spellcheck_add_synbiohub', 'title' : 'Bring up dialog to add current term to SynbioHub.'},
               {'value': 'Manually Enter Link', 'id': 'EnterLink', 'click_script' : manualLinkScript, 'title' : 'Manually enter URL to link for this term.'},
               {'value': 'Include Previous Word', 'id': 'spellcheck_add_select_previous', 'title' : 'Move highlighting to include the word before the highlighted word(s).'},
               {'value': 'Include Next Word', 'id': 'spellcheck_add_select_next', 'title' : 'Move highlighting to include the word after the highlighted word(s).'},
               {'value': 'Remove First Word', 'id': 'spellcheck_add_drop_first', 'title' : 'Move highlighting to remove the word at the beggining of the highlighted words.'},
               {'value': 'Remove Last Word', 'id': 'spellcheck_add_drop_last', 'title' : 'Move highlighting to remove the word at the end of the highlighted words.'}]

    # If this entry was previously linked, add a button to reuse that link
    if 'prev_link' in spellCheckResults[resultIdx]:
        buttons.insert(4, {'value' : 'Reuse previous link', 'id': 'spellcheck_reuse_link', 'title' : 'Reuse the previous link: %s' % spellCheckResults[resultIdx]['prev_link']})

    dialogAction = simple_sidebar_dialog(html, buttons)
    actionList.append(dialogAction)
    return actionList

def sidebar_dialog(htmlMessage):
    action = {}
    action['action'] = 'showSidebar'
    action['html'] = htmlMessage

    return action

def open_new_window(link=None):
    html = "<script>window.open('" + link + "');google.script.host.close();</script>"
    return modal_dialog(html, 'Validation Passed', 500, 300)
    
def valid_request_model_dialog(warnings, link=None):
    text_area_rows = 15
    height = 300
    title = 'Structured request validation: Passed!'
    msg = ''
    if link:
        msg = 'Download Structured Request ' + link
    
    msg += "<textarea cols='80' rows='%d'> %s </textarea>" % (text_area_rows, '\n'.join(warnings))
    buttons = [('Ok', 'process_nop')] 
    return simple_modal_dialog(msg, buttons, title, 500, height)

def simple_modal_dialog(message, buttons, title, width, height):
    htmlMessage = '<script>\n\n'
    htmlMessage += 'function onSuccess() { \n\
                     google.script.host.close()\n\
                  }\n\n'
    for button in buttons:
        htmlMessage += 'function ' + button[1] + 'Click() {\n'
        htmlMessage += '  google.script.run.withSuccessHandler'
        htmlMessage += '(onSuccess).buttonClick(\''
        htmlMessage += button[1]  + '\')\n'
        htmlMessage += '}\n\n'
    htmlMessage += '</script>\n\n'

    htmlMessage += '<p>' + message + '</p>\n'
    htmlMessage += '<center>'
    for button in buttons:
        htmlMessage += '<input id=' + button[1] + 'Button value="'
        htmlMessage += button[0] + '" type="button" onclick="'
        htmlMessage += button[1] + 'Click()" />\n'
    htmlMessage += '</center>'

    return modal_dialog(htmlMessage, title, width, height)

def simple_sidebar_dialog(message, buttons):
    htmlMessage  = '<script>\n\n'
    htmlMessage += 'function onSuccess() { \n\
                     google.script.host.close()\n\
                  }\n\n'
    for button in buttons:
        if 'click_script' in button: # Special buttons, define own script
            htmlMessage += button['click_script']
        else: # Regular buttons, generate script automatically
            htmlMessage += 'function ' + button['id'] + 'Click() {\n'
            htmlMessage += '  google.script.run.withSuccessHandler'
            htmlMessage += '(onSuccess).buttonClick(\''
            htmlMessage += button['id']  + '\')\n'
            htmlMessage += '}\n\n'
    htmlMessage += '</script>\n\n'

    htmlMessage += '<p>' + message + '<p>\n'
    htmlMessage += '<center>'
    for button in buttons:
        if 'click_script' in button: # Special buttons, define own script
            htmlMessage += '<input id=' + button['id'] + 'Button value="'
            htmlMessage += button['value'] + '" type="button"'
            if 'title' in button:
                htmlMessage += 'title="' + button['title'] + '"'
            htmlMessage += ' onclick="' + button['id'] + 'Click()" />\n'
        else:
            htmlMessage += '<input id=' + button['id'] + 'Button value="'
            htmlMessage += button['value'] + '" type="button"'
            if 'title' in button:
                htmlMessage += 'title="' + button['title'] + '"'
            htmlMessage += 'onclick="' + button['id'] + 'Click()" />\n'
    htmlMessage += '</center>'

    action = {}
    action['action'] = 'showSidebar'
    action['html'] = htmlMessage

    return action
