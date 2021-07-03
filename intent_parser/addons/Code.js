var serverURL = 'http://intentparser.sd2e.org';
var versionString = '3.3';

function onOpen() {
    const ui = DocumentApp.getUi();
    const tablesMenu = ui.createMenu('Create table templates');
    tablesMenu.addItem('Controls', 'createControlsTable');
    tablesMenu.addItem('Measurements', 'createTableMeasurements');
    tablesMenu.addItem('Parameters', 'createParameterTable');

    const tableHelpMenu = ui.createMenu('Tables');
    tableHelpMenu.addItem('Controls', 'reportControlsInfo');
    tableHelpMenu.addItem('Lab', 'reportLabInfo');
    tableHelpMenu.addItem('Measurements', 'reportMeasurementsInfo');
    tableHelpMenu.addItem('Parameters', 'reportParametersInfo');

    const runExperimentMenu = ui.createMenu('Run Experiment');
    runExperimentMenu.addItem('with OPIL', 'executeOpilExperiment');
    runExperimentMenu.addItem('with Structured Request', 'executeExperiment');

    const helpMenu = ui.createMenu('Help');
    helpMenu.addSubMenu(tableHelpMenu);
    helpMenu.addItem('About', 'showHelp');

    const analyzeMenu = ui.createMenu('Analyze and link keywords');
    analyzeMenu.addItem('from cursor', 'sendAnalyzeFromCursor');
    analyzeMenu.addItem('from top', 'sendAnalyzeFromTop');

    const generateMenu = ui.createMenu('Generate');
    generateMenu.addItem('OPIL', 'sendOpilRequest');
    generateMenu.addItem('Report', 'sendGenerateReport');
    generateMenu.addItem('Structured Request', 'sendGenerateStructuredRequest');

    const addBySpellingMenu = ui.createMenu('Suggest adding terms to SynBioHub');
    addBySpellingMenu.addItem('from cursor', 'addBySpellingFromCursor');
    addBySpellingMenu.addItem('from top', 'addBySpelling');

    const menu = ui.createMenu('Parse Intent');
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
    const doc = DocumentApp.getActiveDocument();
    const childIndex = getCursorLocation(doc);
    const data = {
        'childIndex': childIndex,
        'tableType': 'experimentProtocols'
    };
    sendPost('/createTableTemplate', data);
}

function reportParametersInfo() {
    const docId = DocumentApp.getActiveDocument().getId();
    const data = {
        'tableType': 'parameter',
        'documentId': docId
    };
    const options = {
        'method': 'post',
        'contentType': 'application/json',
        'payload': JSON.stringify(data)
    };

    const response = UrlFetchApp.fetch(serverURL + '/tableInformation', options);
    const param_info = response.getContentText();
    showSidebar(param_info, "Parameters Table Information");
}

function reportControlsInfo() {
    const docId = DocumentApp.getActiveDocument().getId();
    const response = UrlFetchApp.fetch(serverURL + '/control_information/d/' + docId);
    const html_content = response.getContentText();
    showSidebar(html_content, "Controls Table Information");
}

function reportLabInfo() {
    const docId = DocumentApp.getActiveDocument().getId();
    const response = UrlFetchApp.fetch(serverURL + '/lab_information/d/' + docId);
    const html_content = response.getContentText();
    showSidebar(html_content, "Lab Table Information");
}

function reportMeasurementsInfo() {
    const docId = DocumentApp.getActiveDocument().getId();
    const response = UrlFetchApp.fetch(serverURL + '/measurement_information/d/' + docId);
    const html_content = response.getContentText();
    showSidebar(html_content, "Measurement Table Information");
}

function showHelp() {
    const response = UrlFetchApp.fetch(serverURL + '/about');
    const html_content = response.getContentText();
    showModalDialog(html_content, 'Help', 450, 350);
}

function executeExperiment() {
    sendPost('/run_experiment');
}

function executeOpilExperiment() {
    sendPost('/run_opil_experiment');
}

function reportExperimentStatus() {
    const doc = DocumentApp.getActiveDocument();
    const childIndex = getCursorLocation(doc);
    const data = {'childIndex': childIndex};
    sendPost('/experiment_status', data);
}

function buttonClick(buttonName) {
    sendPost('/buttonClick', {'buttonId': buttonName});
}

function processActions(response) {
    let waitForMoreActions = false;
    if (typeof (response.actions) == 'undefined') {
        return waitForMoreActions;
    }
    const actions = response.actions;
    for (const actionKey in actions) {
        const actionDesc = actions[actionKey];
        switch (actionDesc['action']) {
            case 'highlightText':
                highlightDocText(actionDesc['paragraph_index'],
                    actionDesc['offset'],
                    actionDesc['end_offset']);
                break;
            case 'linkText':
                linkDocText(actionDesc['paragraph_index'],
                    actionDesc['offset'],
                    actionDesc['end_offset'],
                    actionDesc['url']);
                break;
            case 'calculateSamples':
                const tableIds = actionDesc['tableIds'];
                const sampleIndices = actionDesc['sampleIndices'];
                const sampleValues = actionDesc['sampleValues'];
                calculateDocSamples(tableIds, sampleIndices, sampleValues)
                break
            case 'addTable':
                try {
                    const childIndex = actionDesc['cursorChildIndex'];
                    const tableData = actionDesc['tableData'];
                    const colSizes = actionDesc['colSizes'];
                    addDocTable(childIndex, tableData, colSizes);
                    if (actionDesc['tableType'] === 'measurements') {
                        addDocTable(childIndex, actionDesc['tableLab'], colSizes);
                    }
                } catch (err) {
                    console.log(err);
                }
                break
            case 'updateExperimentResults':
                const headerIdx = actionDesc['headerIdx'];
                const contentIdx = actionDesc['contentIdx'];
                const expData = actionDesc['expData'];
                const expLinks = actionDesc['expLinks'];
                updateExperimentResultSection(headerIdx, contentIdx, expData, expLinks);
                break;
            case 'updateProgress':
                waitForMoreActions = true;
                const p = PropertiesService.getDocumentProperties();
                p.setProperty("analyze_progress", actionDesc['progress']);
                break;
            case 'showSidebar':
			    showSidebar(actionDesc['html'], actionDesc['sidebarTitle']);
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

function calculateDocSamples(tableIds, sampleIndices, sampleValues) {
    const doc = DocumentApp.getActiveDocument();
    const body = doc.getBody();
    const tables = body.getTables();
    for (let tIdx = 0; tIdx < tableIds.length; tIdx++) {
        let sampleColIdx = sampleIndices[tIdx];
        const numRows = tables[tableIds[tIdx]].getNumRows();
        // Samples column doesn't exist
        if (sampleColIdx < 0) {
            // Create new column for samples
            const numCols = tables[tableIds[tIdx]].getRow(0).getNumCells();
            tables[tableIds[tIdx]].getRow(0).appendTableCell("samples");
            for (let rowIdx = 1; rowIdx < numRows; rowIdx++) {
                tables[tableIds[tIdx]].getRow(rowIdx).appendTableCell();
            }
            sampleColIdx = numCols;
        }
        for (let rowIdx = 1; rowIdx < numRows; rowIdx++) {
            const tableCell = tables[tableIds[tIdx]].getRow(rowIdx).getCell(sampleColIdx);
            tableCell.setText(sampleValues[tIdx][rowIdx - 1]);
        }
    }
}

function updateExperimentResultSection(headerIdx, contentIdx, expData, expLinks) {
    const doc = DocumentApp.getActiveDocument();
    const body = doc.getBody();
    if (headerIdx !== -1 && contentIdx !== -1) {
        const paragraphs = body.getParagraphs();
        let para = paragraphs[contentIdx];
        para.setText('\n');
        for (let i = 0; i < expData.length; i++) {
            for (let p = 0; p < expData[i].length; p++) {
                const newTxt = para.appendText(expData[i][p]);
                if (i < expLinks.length && expLinks[i][p] !== '') {
                    newTxt.setLinkUrl(expLinks[i][p]);
                } else {
                    newTxt.setLinkUrl('');
                }
            }
        }
    } else {
        const header_para = body.appendParagraph('Experiment Results');
        header_para.setHeading(DocumentApp.ParagraphHeading.HEADING2);
        let para = body.appendParagraph('\n');
        for (let i = 0; i < expData.length; i++) {
            for (let p = 0; p < expData[i].length; p++) {
                const newTxt = para.appendText(expData[i][p]);
                if (i < expLinks.length && expLinks[i][p] !== '') {
                    newTxt.setLinkUrl(expLinks[i][p]);
                } else {
                    newTxt.setLinkUrl('');
                }
            }
        }
    }
}

function addDocTable(childIndex, tableData, colSizes) {
    const doc = DocumentApp.getActiveDocument();
    const body = doc.getBody();
    const newTable = body.insertTable(childIndex, tableData);
    const headerRow = newTable.getRow(0);

    // Reset formatting
    const tableStyle = {};
    tableStyle[DocumentApp.Attribute.HORIZONTAL_ALIGNMENT] = DocumentApp.HorizontalAlignment.LEFT;
    tableStyle[DocumentApp.Attribute.FONT_SIZE] = 11;
    tableStyle[DocumentApp.Attribute.FONT_SIZE] = 11;
    tableStyle[DocumentApp.Attribute.BOLD] = false;
    tableStyle[DocumentApp.Attribute.ITALIC] = false;
    tableStyle[DocumentApp.Attribute.BACKGROUND_COLOR] = '#FFFFFF';
    tableStyle[DocumentApp.Attribute.FOREGROUND_COLOR] = '#000000';
    newTable.setAttributes(tableStyle);

    const style = {};
    style[DocumentApp.Attribute.HORIZONTAL_ALIGNMENT] = DocumentApp.HorizontalAlignment.CENTER;
    style[DocumentApp.Attribute.FONT_SIZE] = 11;
    style[DocumentApp.Attribute.BOLD] = true;
    headerRow.setAttributes(style);

    for (let idx = 0; idx < colSizes.length; ++idx) {
        newTable.setColumnWidth(idx, colSizes[idx] * 7);
    }
}

function showSidebar(html, sidebarTitle) {
    const ui = DocumentApp.getUi();
    const htmlOutput = HtmlService.createHtmlOutput(html).setTitle(sidebarTitle);
    ui.showSidebar(htmlOutput);
}

function showModalDialog(html, title, width, height) {
    const ui = DocumentApp.getUi();
    const htmlOutput = HtmlService.createHtmlOutput(html);
    htmlOutput.setWidth(width);
    htmlOutput.setHeight(height);
    ui.showModalDialog(htmlOutput, title);
}

function highlightDocText(paragraphIndex, offset, endOffset) {
    const doc = DocumentApp.getActiveDocument();
    const body = doc.getBody();
    const paragraph = body.getParagraphs()[paragraphIndex];
    const docText = paragraph.editAsText();
    const selectionRange = doc.newRange();
    selectionRange.addElement(docText, offset, endOffset);
    doc.setSelection(selectionRange.build());
}

function linkDocText(paragraphIndex, offset, endOffset, url) {
    const doc = DocumentApp.getActiveDocument();
    const body = doc.getBody();
    const paragraph = body.getParagraphs()[paragraphIndex];
    const docText = paragraph.editAsText();
    docText.setLinkUrl(offset, endOffset, url);
}

/**
 * Send POST requests to Intent Parser server and process each response and apply to document.
 * @param resource
 * @param data
 * @returns {SpeechRecognitionResultList | number}
 */
function sendPost(resource, data) {
    const docId = DocumentApp.getActiveDocument().getId();
    const user = Session.getActiveUser();
    const userEmail = user.getEmail();
    const request = {
        'documentId': docId,
        'user': user,
        'userEmail': userEmail
    };

    if (typeof (data) != 'undefined') {
        request['data'] = data;
    }

    const requestJSON = JSON.stringify(request);
    const options = {
        'method': 'post',
        'payload': requestJSON,
        'contentType': 'application/json'
    };

    let shouldProcessActions = true;
    let responseOb = null;
    while (shouldProcessActions) {
        const response = UrlFetchApp.fetch(serverURL + resource, options);
        const responseText = response.getContentText();
        responseOb = JSON.parse(responseText);

        shouldProcessActions = processActions(responseOb);
    }
}

/**
 * Identifies a paragraph with an array of hierarchy indicies
 * @param element
 * @returns {*[]}
 */
function identifyParagraph(element) {
    const identity = [];
    let currentElement = element;
    let parent = element.getParent();
    while (parent != null) {
        const idx = parent.getChildIndex(currentElement);
        identity.push(idx);
        currentElement = parent;
        parent = currentElement.getParent();
    }
    return identity.reverse();
}

function identity2str(identity) {
    let str = '';
    for (let i = 0; i < identity.length; ++i) {
        const val = identity[i];
        str += '' + val + '.';
    }
    return str;
}

function compareIdentities(identity1, identity2) {
    for (let idx = 0; idx < identity1.length; ++idx) {
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

/**
 * Find a paragraph identified by an array or hierarchy indicies using a binary search
 * @param identity
 * @param paragraphList
 * @returns {null|number|*}
 */
function findParagraph(identity, paragraphList) {
    if (paragraphList.length < 4) {
        // If the list size is less than 4, do a brute force
        // search
        for (let idx = 0; idx < paragraphList.length; ++idx) {
            const pCompare = paragraphList[idx];
            const valIdentity = identifyParagraph(pCompare);
            if (compareIdentities(identity, valIdentity) === 0) {
                return idx;
            }
        }
        return null;
    }

    // Use the middle element to decide whether to search
    // the first half of entries of the second half of
    // entries
    const middle = Math.floor(paragraphList.length / 2);
    const middleElement = paragraphList[middle];
    const middleIdentity = identifyParagraph(middleElement);
    let startIndex = 0;
    if (compareIdentities(identity, middleIdentity) < 0) {
        let newList = paragraphList.slice(0, middle);
        startIndex = 0;
        return startIndex + findParagraph(identity, newList);
    } else {
        let newList = paragraphList.slice(middle, paragraphList.length);
        startIndex = middle;
        return startIndex + findParagraph(identity, newList);
    }
}

/**
 * Finds TEXT element under element
 * @param element
 * @returns {null|*}
 */
function findTEXT(element) {
    const elType = element.getType();
    if (elType === elType.TEXT) {
        return element;
    }

    if (typeof element.getNumChildren != 'function') {
        return null;
    }

    for (let i = 0; i < element.getNumChildren(); ++i) {
        const child = element.getChild(i);
        const result = findTEXT(child);
        if (result != null) {
            return result;
        }
    }
    return null;
}

/**
 * Find the cursor location
 * @returns {null|{offset: *, paragraphIndex: (number|*)}}
 */
function findCursor() {
    const doc = DocumentApp.getActiveDocument();
    const cursorPosition = doc.getCursor();
    let el = null;
    let offset = null;
    if (cursorPosition == null) {
        // Cursor position is null, so assume a selection
        const selectionRange = doc.getSelection();
        const rangeElement = selectionRange.getRangeElements()[0];

        // Extract element and offset from end of selection
        el = rangeElement.getElement();
        offset = rangeElement.getEndOffsetInclusive();

    } else {
        // Select element and off set from current position
        el = cursorPosition.getElement();
        offset = cursorPosition.getOffset();
    }

    const elementType = el.getType();
    // Handle special case of cursor at the end of a paragraph
    // Paragraphs appear to only have an offset of 0 or 1 (beginning or end)
    // If we are at the end of a paragraph, we want to instead use the end of the text element in the paragraph
    if (elementType !== elementType.TEXT && offset > 0) {
        const textElement = findTEXT(el);
        if (textElement != null) {
            const length = textElement.getText().length;
            offset = length - 1;
        }
    }
    return getLocation(el, offset);
}

function getLocation(element, offset) {
    const doc = DocumentApp.getActiveDocument();
    const paragraphs = doc.getBody().getParagraphs();

    // Identify the element by its location in the
    // document hierarchy.
    const targetedParagraph = identifyParagraph(element);
    const result = findParagraph(targetedParagraph, paragraphs);
    if (result == null) {
        return null;
    } else {
        return {
            'paragraphIndex': result,
            'offset': offset
        };
    }
}

/**
 * Insert to document experimental results.
 */
function updateExperimentalResults() {
    sendPost('/updateExperimentalResults');
}

/**
 * Process and calculate samples from measurement table.
 */
function calculateSamples() {
    sendPost('/calculateSamples');
}

/**
 * Perform analysis from start of document.
 */
function sendAnalyzeFromTop() {
    sendPost('/analyzeDocument');
}

/**
 * Perform analysis from cursor.
 */
function sendAnalyzeFromCursor() {
    const cursorLocation = findCursor();
    sendPost('/analyzeDocument', cursorLocation);
}

/**
 * Show dialog to generate a structured request report.
 */
function sendGenerateReport() {
    const docId = DocumentApp.getActiveDocument().getId();
    let html = '';
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

/**
 * Show dialog to report issues.
 */
function reportIssues() {
    const helpHTML = '\
		<p>Something unexpected happen with the intent-parser plugin?</p> \
		<p>Want to request a feature support?</p> \
		<p>Send a bug report <a href="https://gitlab.sd2e.org/sd2program/experimental-intent-parser/issues"  target=_blank>here</a>.</p> \
		';
    let verFormattedHTML = Utilities.formatString(helpHTML, versionString);
    showModalDialog(verFormattedHTML, 'Issues', 400, 200);
}

/**
 * Generate OPIL data from contents processed in active document.
 */
function sendOpilRequest() {
    sendPost('/generateOpilRequest', getBookmarks());
}

/**
 * Validate active document to see if its content conforms to the structured request schema.
 */
function sendValidateStructuredRequest() {
    sendPost('/validateStructuredRequest', getBookmarks());
}

/**
 * Generate a Structured Request from contents processed in active document.
 */
function sendGenerateStructuredRequest() {
    sendPost('/generateStructuredRequest', getBookmarks());
}

/**
 * Get bookmarks from active document.
 * @returns {{bookmarks: []}}
 */
function getBookmarks() {
    const doc = DocumentApp.getActiveDocument();
    const bookmarks = doc.getBookmarks();
    const result = [];
    for (const bookmark of bookmarks) {
        const bookmark_id = bookmark.getId();
        const bookmark_text = bookmark.getPosition().getElement().asText().getText();
        result.push({
            'id': bookmark_id,
            'text': bookmark_text
        });
    }
    return {'bookmarks': result};
}

/**
 * Add selected terms to SynBioHub.
 */
function addToSynBioHub() {
    const doc = DocumentApp.getActiveDocument();
    const selectionRange = doc.getSelection();
    if (selectionRange == null) {
        return;
    }

    const rangeElements = selectionRange.getRangeElements();
    const firstElement = rangeElements[0];
    const lastElement = rangeElements[rangeElements.length - 1];

    // Extract element and offset from end of selection
    const startEl = firstElement.getElement();
    const startOffset = firstElement.getStartOffset();
    const startLocation = getLocation(startEl, startOffset);

    const endEl = lastElement.getElement();
    const endOffset = lastElement.getEndOffsetInclusive();
    const endLocation = getLocation(endEl, endOffset);

    const selection = {
        'start': startLocation,
        'end': endLocation
    };
    sendPost('/addToSynBioHub', selection);
}

/**
 * Perform Add by spelling from start of document.
 */
function addBySpelling() {
    sendPost('/addBySpelling');
}

/**
 * Perform Add by spelling from cursor.
 */
function addBySpellingFromCursor() {
    const cursorLocation = findCursor();
    sendPost('/addBySpelling', cursorLocation);
}

/**
 * Process an Intent Parser submission dialog.
 * @param formData
 * @returns {*}
 */
function submitForm(formData) {
    sendPost('/submitForm', formData);
}

/**
 * Show dialog to create a Controls Table template.
 */
function createControlsTable() {
    const doc = DocumentApp.getActiveDocument();
    const childIndex = getCursorLocation(doc);
    const data = {
        'childIndex': childIndex,
        'tableType': 'controls'
    };
    sendPost('/createTableTemplate', data);
}

/**
 * Show dialog to create a Measurement Table template.
 */
function createTableMeasurements() {
    const doc = DocumentApp.getActiveDocument();
    const childIndex = getCursorLocation(doc);
    const data = {
        'childIndex': childIndex,
        'tableType': 'measurements'
    };
    sendPost('/createTableTemplate', data);
}

/**
 * Show dialog to create a Parameter Table template.
 */
function createParameterTable() {
    const doc = DocumentApp.getActiveDocument();
    const childIndex = getCursorLocation(doc);
    const data = {
        'childIndex': childIndex,
        'tableType': 'parameters'
    };
    sendPost('/createTableTemplate', data);
}

/**
 * Get index where cursor is located in current document.
 * @param doc
 * @returns {number}
 */
function getCursorLocation(doc) {
    const cursorPosition = doc.getCursor();
    let element = null;
    if (cursorPosition == null) {
        // Cursor position is null, so assume a selection
        const selectionRange = doc.getSelection();
        const rangeElement = selectionRange.getRangeElements()[0];
        // Extract element and offset from end of selection
        element = rangeElement.getElement();
    } else {
        // Select element and off set from current position
        element = cursorPosition.getElement();
    }
    const childIndex = doc.getBody().getChildIndex(element);
    return childIndex;
}