var serverURL = 'http://intentparser.sd2e.org';
var versionString = '3.3';

function onOpen() {
    let ui = DocumentApp.getUi();
    let tablesMenu = ui.createMenu('Create table templates');
    tablesMenu.addItem('Controls', 'createControlsTable');
    tablesMenu.addItem('Measurements', 'createTableMeasurements');
    tablesMenu.addItem('Parameters', 'createParameterTable');

    let tableHelpMenu = ui.createMenu('Tables');
    tableHelpMenu.addItem('Controls', 'reportControlsInfo');
    tableHelpMenu.addItem('Lab', 'reportLabInfo');
    tableHelpMenu.addItem('Measurements', 'reportMeasurementsInfo');
    tableHelpMenu.addItem('Parameters', 'reportParametersInfo');

    let runExperimentMenu = ui.createMenu('Run Experiment');
    runExperimentMenu.addItem('with OPIL', 'executeOpilExperiment');
    runExperimentMenu.addItem('with Structured Request', 'executeExperiment');

    let helpMenu = ui.createMenu('Help');
    helpMenu.addSubMenu(tableHelpMenu);
    helpMenu.addItem('About', 'showHelp');

    let analyzeMenu = ui.createMenu('Analyze and link keywords');
    analyzeMenu.addItem('from cursor', 'sendAnalyzeFromCursor');
    analyzeMenu.addItem('from top', 'sendAnalyzeFromTop');

    let generateMenu = ui.createMenu('Generate');
    generateMenu.addItem('OPIL', 'sendOpilRequest');
    generateMenu.addItem('Report', 'sendGenerateReport');
    generateMenu.addItem('Structured Request', 'sendGenerateStructuredRequest');

    let addBySpellingMenu = ui.createMenu('Suggest adding terms to SynBioHub');
    addBySpellingMenu.addItem('from cursor', 'addBySpellingFromCursor');
    addBySpellingMenu.addItem('from top', 'addBySpelling');

    let menu = ui.createMenu('Parse Intent');
    menu.addItem('Add selection to SynBioHub', 'addToSynBioHub');
    menu.addSubMenu(analyzeMenu);
    menu.addItem('Calculate samples for measurements table', 'calculateSamples');
    menu.addSubMenu(tablesMenu);
    menu.addItem('Import Experimental Protocol template', 'experimentalProtocol');
    menu.addSubMenu(generateMenu);
    menu.addItem('Report Experiment Status', 'reportExperimentStatus');
    menu.addSubMenu(runExperimentMenu);
    menu.addSubMenu(addBySpellingMenu);
    menu.addItem('Update experimental results', 'updateExperimentalResults');
    menu.addItem('Validate Structured Request', 'sendValidateStructuredRequest');

    menu.addItem('File Issues', 'reportIssues');
    menu.addSubMenu(helpMenu);
    menu.addToUi();
}

function experimentalProtocol() {
    let doc = DocumentApp.getActiveDocument();
    let cursorPosition = doc.getCursor();

    if (cursorPosition == null) {
        // Cursor position is null, so assume a selection
        const selectionRange = doc.getSelection();
        const rangeElement = selectionRange.getRangeElements()[0];
        // Extract element and offset from end of selection
        var el = rangeElement.getElement();
    } else {
        // Select element and off set from current position
        var el = cursorPosition.getElement();
    }
    const childIndex = doc.getBody().getChildIndex(el);
    const data = {'childIndex': childIndex, 'tableType': 'experimentProtocols'};
    sendPost('/createTableTemplate', data);
}


function reportParametersInfo() {
    var docId = DocumentApp.getActiveDocument().getId();
    const data = {
        'tableType': 'parameter',
        'documentId': docId
    };
    var options = {
        'method': 'post',
        'contentType': 'application/json',
        'payload': JSON.stringify(data)
    };

    var response = UrlFetchApp.fetch(serverURL + '/tableInformation', options);
    var param_info = response.getContentText();
    showSidebar(param_info, "Parameters Table Information");
}

function reportControlsInfo() {
    const docId = DocumentApp.getActiveDocument().getId();
    let response = UrlFetchApp.fetch(serverURL + '/control_information/d/' + docId);
    let html_content = response.getContentText();
    showSidebar(html_content, "Controls Table Information");
}

function reportLabInfo() {
    const docId = DocumentApp.getActiveDocument().getId();
    let response = UrlFetchApp.fetch(serverURL + '/lab_information/d/' + docId);
    let html_content = response.getContentText();
    showSidebar(html_content, "Lab Table Information");
}

function reportMeasurementsInfo() {
    const docId = DocumentApp.getActiveDocument().getId();
    let response = UrlFetchApp.fetch(serverURL + '/measurement_information/d/' + docId);
    let html_content = response.getContentText();
    showSidebar(html_content, "Measurement Table Information");
}

function showHelp() {
    let response = UrlFetchApp.fetch(serverURL + '/about');
    let html_content = response.getContentText();
    showModalDialog(html_content, 'Help', 450, 350);
}

function validate_uri(uri) {
    try {
        var response = UrlFetchApp.fetch(uri);
        if (response.getResponseCode() == 200) {
            return true;
        } else {
            return false;
        }
    } catch (e) {
        return false;
    }
}

function enterLinkPrompt(title, msg) {
    var ui = DocumentApp.getUi();
    var result = ui.prompt(title, msg, ui.ButtonSet.OK_CANCEL);
    // Process the user's response.
    var button = result.getSelectedButton();
    var text = result.getResponseText();
    while (button == ui.Button.OK) {
        if (validate_uri(text)) {
            return [true, text];
        } else { // If URI is invalid, reprompt
            var result = ui.prompt('Entered URI was invalid!\n' + title, msg, ui.ButtonSet.OK_CANCEL);
            button = result.getSelectedButton();
            text = result.getResponseText();
        }
    }
    return [false, text];
}

function executeExperiment() {
    sendPost('/run_experiment');
}

function executeOpilExperiment() {
    sendPost('/run_opil_experiment');
}

function reportExperimentStatus() {
    let doc = DocumentApp.getActiveDocument();
    let cursorPosition = doc.getCursor();

    if (cursorPosition == null) {
        // Cursor position is null, so assume a selection
        const selectionRange = doc.getSelection();
        const rangeElement = selectionRange.getRangeElements()[0];
        // Extract element and offset from end of selection
        var el = rangeElement.getElement();
    } else {
        // Select element and off set from current position
        var el = cursorPosition.getElement();
    }
    const childIndex = doc.getBody().getChildIndex(el);
    const data = {'childIndex': childIndex};
    sendPost('/experiment_status', data);
}

function sendMessage(message) {
    var request = {'message': message};
    var requestJSON = JSON.stringify(request);
    var options = {
        'method': 'post',
        'payload': requestJSON
    };
    UrlFetchApp.fetch(serverURL + '/message', options);
}

function buttonClick(buttonName) {
    sendPost('/buttonClick', {'buttonId': buttonName});
}

function processActions(response) {
    if (typeof (response.actions) == 'undefined') {
        return;
    }
    var actions = response.actions;
    waitForMoreActions = false;
    for (var actionKey in actions) {
        var actionDesc = actions[actionKey];
        switch (actionDesc['action']) {
            case 'highlightText':
                var paragraphIndex = actionDesc['paragraph_index'];
                var offset = actionDesc['offset'];
                var endOffset = actionDesc['end_offset'];
                highlightDocText(paragraphIndex, offset, endOffset);
                break;
            case 'linkText':
                var paragraphIndex = actionDesc['paragraph_index'];
                var offset = actionDesc['offset'];
                var endOffset = actionDesc['end_offset'];
                var url = actionDesc['url'];
                linkDocText(paragraphIndex, offset, endOffset, url);
                break;
            case 'calculateSamples':
                var tableIds = actionDesc['tableIds'];
                var sampleIndices = actionDesc['sampleIndices'];
                var sampleValues = actionDesc['sampleValues'];
                var doc = DocumentApp.getActiveDocument();
                var body = doc.getBody();
                var tables = body.getTables();
                for (var tIdx = 0; tIdx < tableIds.length; tIdx++) {
                    sampleColIdx = sampleIndices[tIdx];
                    var numRows = tables[tableIds[tIdx]].getNumRows();
                    // Samples column doesn't exist
                    if (sampleColIdx < 0) {
                        // Create new column for samples
                        var numCols = tables[tableIds[tIdx]].getRow(0).getNumCells();
                        tables[tableIds[tIdx]].getRow(0).appendTableCell("samples");
                        for (var rowIdx = 1; rowIdx < numRows; rowIdx++) {
                            tables[tableIds[tIdx]].getRow(rowIdx).appendTableCell();
                        }
                        sampleColIdx = numCols;
                    }
                    for (var rowIdx = 1; rowIdx < numRows; rowIdx++) {
                        var tableCell = tables[tableIds[tIdx]].getRow(rowIdx).getCell(sampleColIdx);
                        tableCell.setText(sampleValues[tIdx][rowIdx - 1]);
                    }
                }
                break
            case 'addTable':
                try {
                    var childIndex = actionDesc['cursorChildIndex'];
                    var tableData = actionDesc['tableData'];
                    var colSizes = actionDesc['colSizes'];
                    var doc = DocumentApp.getActiveDocument();
                    var body = doc.getBody();
                    var newTable = body.insertTable(childIndex, tableData);
                    var headerRow = newTable.getRow(0);

                    // Reset formatting
                    var tableStyle = {};
                    tableStyle[DocumentApp.Attribute.HORIZONTAL_ALIGNMENT] = DocumentApp.HorizontalAlignment.LEFT;
                    tableStyle[DocumentApp.Attribute.FONT_SIZE] = 11;
                    tableStyle[DocumentApp.Attribute.FONT_SIZE] = 11;
                    tableStyle[DocumentApp.Attribute.BOLD] = false;
                    tableStyle[DocumentApp.Attribute.ITALIC] = false;
                    tableStyle[DocumentApp.Attribute.BACKGROUND_COLOR] = '#FFFFFF';
                    tableStyle[DocumentApp.Attribute.FOREGROUND_COLOR] = '#000000';
                    newTable.setAttributes(tableStyle);

                    var style = {};
                    style[DocumentApp.Attribute.HORIZONTAL_ALIGNMENT] = DocumentApp.HorizontalAlignment.CENTER;
                    style[DocumentApp.Attribute.FONT_SIZE] = 11;
                    style[DocumentApp.Attribute.BOLD] = true;
                    headerRow.setAttributes(style);

                    for (var idx = 0; idx < colSizes.length; ++idx) {
                        newTable.setColumnWidth(idx, colSizes[idx] * 7);
                    }

                    if (actionDesc['tableType'] == 'measurements') {
                        labTableData = actionDesc['tableLab'];
                        var newLabTable = body.insertTable(childIndex, labTableData);
                        newLabTable.setAttributes(tableStyle);
                    }
                } catch (err) {
                    console.log(err);
                }
                break
            case 'updateExperimentResults':
                var headerIdx = actionDesc['headerIdx'];
                var contentIdx = actionDesc['contentIdx'];
                var expData = actionDesc['expData'];
                var expLinks = actionDesc['expLinks'];

                var doc = DocumentApp.getActiveDocument();
                var body = doc.getBody();

                if (headerIdx != -1 && contentIdx != -1) {
                    var paragraphs = body.getParagraphs();
                    para = paragraphs[contentIdx];
                    para.setText('\n');
                    for (var i = 0; i < expData.length; i++) {
                        for (var p = 0; p < expData[i].length; p++) {
                            newTxt = para.appendText(expData[i][p]);
                            if (i < expLinks.length && expLinks[i][p] != '') {
                                newTxt.setLinkUrl(expLinks[i][p]);
                            } else {
                                newTxt.setLinkUrl('');
                            }
                        }
                    }
                } else {
                    var header_para = body.appendParagraph('Experiment Results');
                    header_para.setHeading(DocumentApp.ParagraphHeading.HEADING2);
                    para = body.appendParagraph('\n');
                    for (var i = 0; i < expData.length; i++) {
                        for (var p = 0; p < expData[i].length; p++) {
                            newTxt = para.appendText(expData[i][p]);
                            if (i < expLinks.length && expLinks[i][p] != '') {
                                newTxt.setLinkUrl(expLinks[i][p]);
                            } else {
                                newTxt.setLinkUrl('');
                            }
                        }
                    }
                }
                break;
            case 'updateProgress':
                waitForMoreActions = true;
                var p = PropertiesService.getDocumentProperties();
                p.setProperty("analyze_progress", actionDesc['progress']);
                break;
            case 'reportContent':
                processReportContent(actionDesc['report']);
                break;

            case 'showModalDialog':
                showModalDialog(actionDesc['html'], actionDesc['title'],
                    actionDesc['width'], actionDesc['height']);
                break;

            default:
                break;
        }
    }
    return waitForMoreActions;
}

function showSidebar(html, sidebarTitle) {
    let ui = DocumentApp.getUi();
    const htmlOutput = HtmlService.createHtmlOutput(html).setTitle(sidebarTitle);
    ui.showSidebar(htmlOutput);
}

function showModalDialog(html, title, width, height) {
    var ui = DocumentApp.getUi();
    var htmlOutput = HtmlService.createHtmlOutput(html);
    htmlOutput.setWidth(width);
    htmlOutput.setHeight(height);

    ui.showModalDialog(htmlOutput, title);
}

function highlightDocText(paragraphIndex, offset, endOffset) {
    var doc = DocumentApp.getActiveDocument();
    var body = doc.getBody();
    var paragraph = body.getParagraphs()[paragraphIndex];
    var docText = paragraph.editAsText();
    var selectionRange = doc.newRange();

    selectionRange.addElement(docText, offset, endOffset);
    doc.setSelection(selectionRange.build());
}

function linkDocText(paragraphIndex, offset, endOffset, url) {
    var doc = DocumentApp.getActiveDocument();
    var body = doc.getBody();
    var paragraph = body.getParagraphs()[paragraphIndex];
    var docText = paragraph.editAsText();

    docText.setLinkUrl(offset, endOffset, url);
}

function sendPost(resource, data) {
    var docId = DocumentApp.getActiveDocument().getId();
    var user = Session.getActiveUser();
    var userEmail = user.getEmail();
    var request = {
        'documentId': docId,
        'user': user,
        'userEmail': userEmail
    };

    if (typeof (data) != 'undefined') {
        request['data'] = data;
    }

    var requestJSON = JSON.stringify(request);
    var options = {
        'method': 'post',
        'payload': requestJSON,
        'contentType': 'application/json'
    };

    shouldProcessActions = true;
    while (shouldProcessActions) {
        response = UrlFetchApp.fetch(serverURL + resource, options);
        var responseText = response.getContentText();
        var responseOb = JSON.parse(responseText);

        shouldProcessActions = processActions(responseOb);
    }

    return responseOb.results;
}

//Identifies a paragraph with an array of hierarchy indicies
function identifyParagraph(element) {
    var foundParagraph = true;
    var identity = [];
    var parent = element.getParent();
    while (parent != null) {
        elementType = element.getType();
        var idx = parent.getChildIndex(element);
        identity.push(idx);
        element = parent;
        parent = element.getParent();
    }

    return identity.reverse();
}

function identity2str(identity) {
    str = '';
    for (i = 0; i < identity.length; ++i) {
        val = identity[i];
        str += '' + val + '.';
    }

    return str;
}

function compareIdentities(identity1, identity2) {
    for (var idx = 0; idx < identity1.length; ++idx) {
        if (idx >= identity2.length) {
            // identity2 is smaller
            // This compare function returns true here because
            // identity1 is a parent of identity2
            return 0;
        }

        if (identity1[idx] < identity2[idx]) {
            // identity1 is smaller
            return -1;
        }

        if (identity1[idx] > identity2[idx]) {
            // identity1 is larger
            return 1;
        }
    }

    if (identity2.length > identity1.length) {
        // identity1 is smaller
        return -1;
    }

    // identity1 and identity2 are equal
    return 0;
}

//Find a paragraph identified by an array or hierarchy
//indicies using a binary search
function findParagraph(identity, paragraphList) {
    if (paragraphList.length < 4) {
        // If the list size is less than 4, do a brute force
        // search
        for (var idx = 0; idx < paragraphList.length; ++idx) {
            var pCompare = paragraphList[idx];
            var valIdentity = identifyParagraph(pCompare);
            if (compareIdentities(identity, valIdentity) == 0) {
                return idx;
            }
        }
        return null;
    }

    // Use the middle element to decide whether to search
    // the first half of entries of the second half of
    // entries
    var middle = Math.floor(paragraphList.length / 2);
    var middleElement = paragraphList[middle];
    var middleIdentity = identifyParagraph(middleElement);

    if (compareIdentities(identity, middleIdentity) < 0) {
        var newList = paragraphList.slice(0, middle);
        var startIndex = 0;

    } else {

        var newList = paragraphList.slice(middle,
            paragraphList.length);
        startIndex = middle;
    }

    return startIndex + findParagraph(identity, newList);
}

//Finds TEXT element under element
function findTEXT(element) {
    var elType = element.getType();

    if (elType == elType.TEXT) {
        return element;
    }

    if (typeof element.getNumChildren != 'function') {
        return null;
    }

    for (var i = 0; i < element.getNumChildren(); ++i) {
        var child = element.getChild(i);

        var result = findTEXT(child);
        if (result != null) {
            return result;
        }
    }

    return null;
}

//Find the cursor location
function findCursor() {
    var doc = DocumentApp.getActiveDocument();

    var cursorPosition = doc.getCursor();

    if (cursorPosition == null) {
        // Cursor position is null, so assume a selection
        selectionRange = doc.getSelection();
        rangeElement = selectionRange.getRangeElements()[0];

        // Extract element and offset from end of selection
        var el = rangeElement.getElement();
        var offset = rangeElement.getEndOffsetInclusive();

    } else {
        // Select element and off set from current position
        var el = cursorPosition.getElement();
        var offset = cursorPosition.getOffset();
    }

    var elementType = el.getType();
    // Handle special case of cursor at the end of a paragraph
    // Paragraphs appear to only have an offset of 0 or 1 (beginning or end)
    // If we are at the end of a paragraph, we want to instead use the end of the text element in the paragraph
    if (elementType != elementType.TEXT && offset > 0) {
        var textElement = findTEXT(el);
        if (textElement != null) {
            var length = textElement.getText().length;
            offset = length - 1;
        }
    }

    return getLocation(el, offset);
}

function getLocation(el, offset) {
    var doc = DocumentApp.getActiveDocument();

    // Get the ordared list of paragraphs
    var plist = doc.getBody().getParagraphs();

    // Identify the element by its location in the
    // document hierarchy.
    identity = identifyParagraph(el);

    // Find the index in plist of the paragraph with the
    // same
    var result = findParagraph(identity, plist);

    if (result == null) {
        return null;
    } else {
        return {
            'paragraphIndex': result,
            'offset': offset
        };
    }
}

function updateExperimentalResults() {
    sendPost('/updateExperimentalResults');
}

function calculateSamples() {
    sendPost('/calculateSamples');
}

function sendAnalyzeFromTop() {
    sendPost('/analyzeDocument');
}

function sendAnalyzeFromCursor() {
    var cursorLocation = findCursor();
    sendPost('/analyzeDocument', cursorLocation);
}

function sendGenerateReport() {
    var docId = DocumentApp.getActiveDocument().getId();
    var html = '';
    html += '<script>\n';
    html += 'function onSuccess() {\n';
    html += '  google.script.host.close()\n';
    html += '}\n';
    html += '</script>\n';
    html += '\n';
    html += '<p>';
    html += '<center>';
    html += 'Download Report ';
    html += '<a href=' + serverURL + '/document_report/d/';
    html += docId + ' target=_blank>here</a>';
    html += '</p>';
    html += '\n';
    html += '<input id=okButton Button value="Done" ';
    html += 'type="button" onclick="onSuccess()" />\n';
    html += '</center>';
    showModalDialog(html, 'Download', 300, 100);
}

function reportIssues() {
    const helpHTML = '\
		<p>Something unexpected happen with the intent-parser plugin?</p> \
		<p>Want to request a feature support?</p> \
		<p>Send a bug report <a href="https://gitlab.sd2e.org/sd2program/experimental-intent-parser/issues"  target=_blank>here</a>.</p> \
		';
    let verFormattedHTML = Utilities.formatString(helpHTML, versionString);
    showModalDialog(verFormattedHTML, 'Issues', 400, 200);
}

function sendOpilRequest() {
    sendPost('/generateOpilRequest', getBookmarks());
}

function sendValidateStructuredRequest() {
    sendPost('/validateStructuredRequest', getBookmarks());
}

function sendGenerateStructuredRequest() {
    sendPost('/generateStructuredRequest', getBookmarks());
}

function getBookmarks() {
    var doc = DocumentApp.getActiveDocument();
    var bookmarks = doc.getBookmarks();
    var result = [];
    for (var bookmark of bookmarks) {
        var bookmark_id = bookmark.getId();
        var bookmark_text = bookmark.getPosition().getElement().asText().getText();
        result.push({id: bookmark_id, text: bookmark_text});
    }
    return {'bookmarks': result};
}

function addToSynBioHub() {
    var doc = DocumentApp.getActiveDocument();
    selectionRange = doc.getSelection();

    if (selectionRange == null) {
        return;
    }

    // Cursor position is null, so assume a selection
    var selectionRange = doc.getSelection();
    var rangeElements = selectionRange.getRangeElements();
    var firstElement = rangeElements[0];
    var lastElement = rangeElements[rangeElements.length - 1];

    // Extract element and offset from end of selection
    var startEl = firstElement.getElement();
    var startOffset = firstElement.getStartOffset();
    var startLocation = getLocation(startEl, startOffset);

    var endEl = lastElement.getElement();
    var endOffset = lastElement.getEndOffsetInclusive();
    var endLocation = getLocation(endEl, endOffset);

    var selection = {
        'start': startLocation,
        'end': endLocation
    };
    sendPost('/addToSynBioHub', selection);
}

function addBySpelling() {
    sendPost('/addBySpelling');
}

function addBySpellingFromCursor() {
    const cursorLocation = findCursor();
    sendPost('/addBySpelling', cursorLocation);
}

function submitForm(formData) {
    return sendPost('/submitForm', formData);
}

function postFromClient(postInfo) {
    return sendPost(postInfo.resource, postInfo.data);
}

function createControlsTable() {
    let doc = DocumentApp.getActiveDocument();
    let cursorPosition = doc.getCursor();

    if (cursorPosition == null) {
        // Cursor position is null, so assume a selection
        const selectionRange = doc.getSelection();
        const rangeElement = selectionRange.getRangeElements()[0];
        // Extract element and offset from end of selection
        var el = rangeElement.getElement();
    } else {
        // Select element and off set from current position
        var el = cursorPosition.getElement();
    }
    const childIndex = doc.getBody().getChildIndex(el);
    const data = {'childIndex': childIndex, 'tableType': 'controls'};
    sendPost('/createTableTemplate', data);
}

function createTableMeasurements() {
    let doc = DocumentApp.getActiveDocument();
    let cursorPosition = doc.getCursor();

    if (cursorPosition == null) {
        // Cursor position is null, so assume a selection
        const selectionRange = doc.getSelection();
        const rangeElement = selectionRange.getRangeElements()[0];
        // Extract element and offset from end of selection
        var el = rangeElement.getElement();
    } else {
        // Select element and off set from current position
        var el = cursorPosition.getElement();
    }
    const childIndex = doc.getBody().getChildIndex(el);
    const data = {'childIndex': childIndex, 'tableType': 'measurements'};
    sendPost('/createTableTemplate', data);
}

function createParameterTable() {
    let doc = DocumentApp.getActiveDocument();
    let cursorPosition = doc.getCursor();

    if (cursorPosition == null) {
        // Cursor position is null, so assume a selection
        const selectionRange = doc.getSelection();
        const rangeElement = selectionRange.getRangeElements()[0];
        // Extract element and offset from end of selection
        var el = rangeElement.getElement();
    } else {
        // Select element and off set from current position
        var el = cursorPosition.getElement();
    }
    const childIndex = doc.getBody().getChildIndex(el);
    const data = {'childIndex': childIndex, 'tableType': 'parameters'};
    sendPost('/createTableTemplate', data);
}