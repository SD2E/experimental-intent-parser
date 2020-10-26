"""
Functions for generating views related to intent parser
"""
from intent_parser.accessor.catalog_accessor import CatalogAccessor
from intent_parser.utils.html_builder import AddHtmlBuilder, AnalyzeHtmlBuilder, ControlsTableHtmlBuilder, MeasurementTableHtmlBuilder, ParameterTableHtmlBuilder
import intent_parser.constants.ip_app_script_constants as addon_constants
import intent_parser.constants.intent_parser_constants as ip_constants
import logging

logger = logging.getLogger('intent_parser_server')


def generate_results_pagination_html(offset, count):
    curr_set_str = '%d - %d' % (offset, offset + ip_constants.SPARQL_LIMIT)
    firstHTML = '<a onclick="refreshList(%d)" href="#first" >First</a>' % 0
    lastHTML = '<a onclick="refreshList(%d)" href="#last" >Last</a>' % (count - ip_constants.SPARQL_LIMIT)
    prevHTML = '<a onclick="refreshList(%d)" href="#previous" >Previous</a>' % max(0, offset - ip_constants.SPARQL_LIMIT - 1)
    nextHTML = '<a onclick="refreshList(%d)" href="#next" >Next</a>' % min(count - ip_constants.SPARQL_LIMIT,
                                                                           offset + ip_constants.SPARQL_LIMIT + 1)

    html = '<tr>\n'
    html += '  <td align="center" colspan = 3 style="max-width: 250px; word-wrap: break-word;">\n'
    html += '    Showing %s of %s\n' % (curr_set_str, count)
    html += '  </td>\n'
    html += '</tr>\n'
    html += '<tr>\n'
    html += '  <td align="center" colspan = 3 style="max-width: 250px; word-wrap: break-word;">\n'
    html += '    %s, %s, %s, %s\n' % (firstHTML, prevHTML, nextHTML, lastHTML)
    html += '  </td>\n'
    html += '</tr>\n'

    return html

def create_optional_fields_checkbox(optional_fields, table_field_id='optionalFieldTable'):
    html_rows = []
    html_table = '''<table id=%s>''' % table_field_id
    for index in range(len(optional_fields)):
        html_checkbox = '''<input type="checkbox" id="chkOption%s">''' % str(index)
        html_label = '''<label for="chkOption%s">%s</label>''' % (str(index), optional_fields[index])
        html_col1 = '''<td>%s</td>''' % html_checkbox
        html_col2 = '''<td>%s</td>''' % html_label
        html_row = '''<tr>%s %s</tr>''' % (html_col1, html_col2)
        html_rows.append(html_row)
    # close tag after html table is completely filled in
    html_table += '</table>'
    # return ''.join(html_rows)
    return ','.join(optional_fields)

def create_table_template(position_in_document, table_data, table_type, col_sizes, additional_info={}):
    create_table = {'action': 'addTable',
                    addon_constants.CURSOR_CHILD_INDEX: position_in_document,
                    addon_constants.TABLE_DATA: table_data,
                    addon_constants.TABLE_TYPE: table_type,
                    'colSizes': col_sizes}
    if additional_info:
        for k, v in additional_info.items():
            create_table[k] = v
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

def create_parameter_table_dialog(cursor_child_index,
                                  protocol_names,
                                  timeseries_optional_fields=[],
                                  growthcurve_optional_fields=[],
                                  obstaclecourse_optional_fields=[],
                                  cellfreeriboswitch_options=[]):
    html_protocols = generate_html_options(protocol_names)
    builder = ParameterTableHtmlBuilder()
    builder.cursor_child_index_html(cursor_child_index)
    builder.protocol_names_html(html_protocols)

    builder.growthcurve_optional_parameter_fields(create_optional_fields_checkbox(growthcurve_optional_fields))
    builder.obstaclecourse_optional_parameter_fields(create_optional_fields_checkbox(obstaclecourse_optional_fields))
    builder.timeseries_optional_parameter_fields(create_optional_fields_checkbox(timeseries_optional_fields))
    builder.cellfreeriboswitch_optional_parameter_fields(create_optional_fields_checkbox(cellfreeriboswitch_options))
    html_parameter = builder.build() 
    dialog_action = modal_dialog(html_parameter, 'Create Parameters Table', 600, 600)
    return dialog_action

def create_measurement_table_dialog(cursor_child_index):
    catalog_accessor = CatalogAccessor()
    local_file_types = catalog_accessor.get_file_types().copy()
    local_file_types.insert(0, '---------------')
    local_file_types.insert(0, 'CSV')
    local_file_types.insert(0, 'PLAIN')
    local_file_types.insert(0, 'FASTQ')
    local_file_types.insert(0, 'FCS')

    lab_ids_html = generate_html_options(catalog_accessor.get_lab_ids())
    time_unit_html = generate_html_options(catalog_accessor.get_time_units())

    measurement_types_html = generate_html_options(catalog_accessor.get_measurement_types())
    measurement_types_html = measurement_types_html.replace('\n', ' ')

    file_types_html = generate_html_options(local_file_types)
    file_types_html = file_types_html.replace('\n', ' ')
    
    builder = MeasurementTableHtmlBuilder()
    builder.cursor_child_index_html(cursor_child_index) 
    builder.lab_ids_html(lab_ids_html) 
    builder.measurement_types_html(measurement_types_html) 
    builder.file_types_html(file_types_html)
    builder.time_unit_html(time_unit_html)
    html = builder.build()
    dialog_action = modal_dialog(html, 'Create Measurements Table', 600, 600)
    return dialog_action

def generate_existing_link_html(title, target, two_col = False):
    if two_col:
        width = 175
    else:
        width = 350

    html = '<tr>\n'
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
                                   is_spellcheck):
    
    html_builder = AddHtmlBuilder().common_name(selection) \
                                   .display_id(display_id) \
                                   .start_paragraph(str(start_paragraph)) \
                                   .start_offset(str(start_offset)) \
                                   .end_paragraph(str(end_paragraph)) \
                                   .end_offset(str(end_offset)) \
                                   .item_types_html(item_types_html) \
                                   .lab_ids_html(lab_ids_html) \
                                   .selected_term(selection) \
                                   .document_id(document_id) \
                                   .is_spell_check(str(is_spellcheck))
    submit_button_html = '        <input type="button" value="Submit" id="submitButton" onclick="submitToSynBioHub()">'
    if is_spellcheck:
        submit_button_html = """
            <input type="button" value="Submit" id="submitButton" onclick="submitToSynBioHub()">
            <input type="button" value="Submit, Link All" id="submitButtonLinkAll" onclick="submitToSynBioHubAndLinkAll()">
        """
    html = html_builder.submit_button(submit_button_html).build()
    dialog_action = modal_dialog(html, 'Add to SynBioHub', 600, 600)
    return dialog_action
    
def invalid_request_model_dialog(title, messages):
    text_area_rows = 33
    height = 600
    # title = 'Structured request validation: Failed!'
    buttons = [('Ok', 'process_nop')]
    validation_message = '\n'.join(messages)
    msg = "<textarea cols='80' rows='%d'> %s </textarea>" % (text_area_rows, validation_message)
    return simple_modal_dialog(msg, buttons, title, 500, height)

def highlight_text(paragraph_index, offset, end_offset):
    return {'action': 'highlightText',
            'paragraph_index': paragraph_index,
            'offset': offset,
            'end_offset': end_offset}

def link_text(paragraph_index, offset, end_offset, url):
    return {'action': 'linkText',
            'paragraph_index': paragraph_index,
            'offset': offset,
            'end_offset': end_offset,
            'url': url}

def modal_dialog(html, title, width, height):
    return {'action': 'showModalDialog',
            'html': html,
            'title': title,
            'width': width,
            'height': height}

def operation_failed(message):
    return {'results': {'operationSucceeded': False,
                        'message': message}
    }

def progress_sidebar_dialog():
    """
    Generate the HTML to display analyze progress in a sidebar.
    """
    html_message = '''
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
    action = {'action': 'showProgressbar',
              'html': html_message}
    return action

def create_search_result_dialog(term, uri, content_term, document_id, paragraph_index, offset, end_offset):
    """
    Args:
        term: term in document represented as a string
        uri: a SBH uri that the hyperlink text will reference to
        content_term: matched keyword found in sbol dictionary
        document_id: id of a document
        paragraph_index: an integer value to represent the paragraph where the term is found in the document
        offset: an integer value to mark the starting position where the terms appears in the document paragraph
        end_offset: an integer value to mark the ending position where the terms appears in the document paragraph
    """
    actions = [highlight_text(paragraph_index, offset, end_offset)]

    yes_button = ('Yes', addon_constants.ANALYZE_YES, 'Creates a hyperlink for the highlighted text, using the suggested URL.')
    no_button = ('No', addon_constants.ANALYZE_NO, 'Skips this term without creating a link.')
    yes_to_all_button = ('Yes to All', addon_constants.ANALYZE_YES_TO_ALL, 'Creates a hyperlink for the highilghted text and every instance of it in the document, using the suggested URL.')
    no_to_all_button = ('No to All', addon_constants.ANALYZE_NO_TO_ALL, 'Skips this term and every other instance of it in the document.')
    never_link_button = ('Never Link', addon_constants.ANALYZE_NEVER_LINK, 'Never suggest links to this term, in this document or any other.')
    buttons = [yes_button, no_button, yes_to_all_button, no_to_all_button, never_link_button]

    button_HTML = ''
    button_script = ''

    data = {addon_constants.DOCUMENT_ID: document_id,
            addon_constants.ANALYZE_LINK: uri,
            addon_constants.ANALYZE_PARAGRAPH_INDEX: paragraph_index,
            addon_constants.ANALYZE_OFFSET: offset,
            addon_constants.ANALYZE_END_OFFSET: end_offset,
            addon_constants.ANALYZE_CONTENT_TERM: content_term,
            addon_constants.ANALYZE_TERM: term}
    for button in buttons:
        button_HTML += '<input id=' + button[1] + 'Button value="'
        button_HTML += button[0] + '" type="button" title="'
        button_HTML += button[2] + '" onclick="'
        button_HTML += button[1] + 'Click()" />\n'

        button_script += """
        function %sClick() {
            var data = %s;
            var extra = "%s";
            data.buttonId = extra; 
            busy('Linking to SynBioHub entry');

            google.script.run.withSuccessHandler(onSuccess).buttonClick(data);}
        """ % (button[1], data, button[1])

    button_HTML += '<input id=EnterLinkButton value="Manually Enter Link" type="button" title="Enter a link for this term manually." onclick="EnterLinkClick()" />'
    # Script for the EnterLinkButton is already in the HTML

    html_builder = AnalyzeHtmlBuilder()
    if term:
        html_builder.selected_term(term)
    if uri:
        html_builder.selected_uri(uri)
        html_builder.term_uri(uri)
    if content_term:
        html_builder.content_term(content_term)
    if document_id:
        html_builder.document_id(document_id)
    if button_HTML:
        html_builder.button_html(button_HTML)
    if button_script:
        html_builder.button_script(button_script)

    dialog_action = sidebar_dialog(html_builder.build())
    actions.append(dialog_action)
    return actions

def report_spelling_results(client_state):
    """Generate actions for client, given the current spelling results index
    """
    spell_check_results = client_state['spelling_results']
    result_idx = client_state['spelling_index']
    action_list = []

    start_par = spell_check_results[result_idx]['select_start']['paragraph_index']
    start_cursor = spell_check_results[result_idx]['select_start']['cursor_index']
    end_par = spell_check_results[result_idx]['select_end']['paragraph_index']
    end_cursor = spell_check_results[result_idx]['select_end']['cursor_index']
    
    if not start_par == end_par:
        logger.error('Received a highlight request across paragraphs, which is currently unsupported!')
    highlight_text_action = highlight_text(start_par, start_cursor, end_cursor)
    action_list.append(highlight_text_action)

    html = '<center>'
    html += 'Term %s not found in dictionary, potential addition?' % spell_check_results[result_idx]['term']
    html += '</center>'
    manual_link_script = """
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
               {'value': 'Manually Enter Link', 'id': 'EnterLink', 'click_script' : manual_link_script, 'title' : 'Manually enter URL to link for this term.'},
               {'value': 'Include Previous Word', 'id': 'spellcheck_add_select_previous', 'title' : 'Move highlighting to include the word before the highlighted word(s).'},
               {'value': 'Include Next Word', 'id': 'spellcheck_add_select_next', 'title' : 'Move highlighting to include the word after the highlighted word(s).'},
               {'value': 'Remove First Word', 'id': 'spellcheck_add_drop_first', 'title' : 'Move highlighting to remove the word at the beggining of the highlighted words.'},
               {'value': 'Remove Last Word', 'id': 'spellcheck_add_drop_last', 'title' : 'Move highlighting to remove the word at the end of the highlighted words.'}]

    # If this entry was previously linked, add a button to reuse that link
    if 'prev_link' in spell_check_results[result_idx]:
        buttons.insert(4, {'value': 'Reuse previous link', 'id': 'spellcheck_reuse_link', 'title' : 'Reuse the previous link: %s' % spell_check_results[result_idx]['prev_link']})
    dialog_action = simple_sidebar_dialog(html, buttons)
    action_list.append(dialog_action)
    return action_list

def sidebar_dialog(html_message):
    return {'action': 'showSidebar',
            'html': html_message}

def message_dialog(title, message):
    height = 150
    buttons = [('Ok', 'process_nop')]
    return simple_modal_dialog(message, buttons, title, 200, height)

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

def create_execute_experiment_dialog(link):
    dialog_title = 'Submit Experiment'
    html_message = '''
    <script>
    function onSuccess() { google.script.host.close(); }
    function authExperimentExecutionClick(){
        window.open('%s');
        onSuccess();
    } 

    </script>
    <p>Please click Authenticate to complete your request.</p> 
    <center>
        <input id=authExperimentExecution type="button", onclick="authExperimentExecutionClick()" value="Authenticate" />
    </center> 
    ''' % (link)
    return modal_dialog(html_message, dialog_title, 300, 150)

def simple_modal_dialog(message, buttons, title, width, height):
    html_message = '<script>\n\n'
    html_message += 'function onSuccess() { \n\
                     google.script.host.close()\n\
                  }\n\n'
    for button in buttons:
        html_message += 'function ' + button[1] + 'Click() {\n'
        html_message += '  google.script.run.withSuccessHandler'
        html_message += '(onSuccess).buttonClick(\''
        html_message += button[1]  + '\')\n'
        html_message += '}\n\n'
    html_message += '</script>\n\n'
    html_message += '<p>' + message + '</p>\n'
    html_message += '<center>'
    for button in buttons:
        html_message += '<input id=' + button[1] + 'Button value="'
        html_message += button[0] + '" type="button" onclick="'
        html_message += button[1] + 'Click()" />\n'
    html_message += '</center>'
    return modal_dialog(html_message, title, width, height)

def simple_sidebar_dialog(message, buttons):
    html_message = '<script>\n\n'
    html_message += 'function onSuccess() { \n\
                     google.script.host.close()\n\
                  }\n\n'
    for button in buttons:
        if 'click_script' in button: # Special buttons, define own script
            html_message += button['click_script']
        else: # Regular buttons, generate script automatically
            html_message += 'function ' + button['id'] + 'Click() {\n'
            html_message += '  google.script.run.withSuccessHandler'
            html_message += '(onSuccess).buttonClick(\''
            html_message += button['id']  + '\')\n'
            html_message += '}\n\n'
    html_message += '</script>\n\n'
    html_message += '<p>' + message + '<p>\n'
    html_message += '<center>'
    for button in buttons:
        if 'click_script' in button: # Special buttons, define own script
            html_message += '<input id=' + button['id'] + 'Button value="'
            html_message += button['value'] + '" type="button"'
            if 'title' in button:
                html_message += 'title="' + button['title'] + '"'
            html_message += ' onclick="' + button['id'] + 'Click()" />\n'
        else:
            html_message += '<input id=' + button['id'] + 'Button value="'
            html_message += button['value'] + '" type="button"'
            if 'title' in button:
                html_message += 'title="' + button['title'] + '"'
            html_message += 'onclick="' + button['id'] + 'Click()" />\n'
    html_message += '</center>'
    action = {'action': 'showSidebar',
              'html': html_message}
    return action
