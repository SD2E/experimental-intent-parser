"""
Contains functionalities for generating views related to intent parser
"""
import logging

logger = logging.getLogger('intent_parser_server')

def generate_html_options(self, options):
        options_html = ''
        for item_type in options:
            options_html += '          '
            options_html += '<option>'
            options_html += item_type
            options_html += '</option>\n'

        return options_html
    



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

def get_download_link(host, document_id):
    return '<a href=http://' + host + '/document_request?' + document_id + ' target=_blank>here</a> \n\n'

def invalid_request_model_dialog(warnings, errors):
    text_area_rows = 33
    height = 600
    title = 'Structured request validation: Failed!'
    buttons = [('Ok', 'process_nop')] 
    validation_message = '\n'.join(warnings.extend(errors))
    msg = "<textarea cols='80' rows='%d'> %s </textarea>" % (text_area_rows, validation_message)
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
