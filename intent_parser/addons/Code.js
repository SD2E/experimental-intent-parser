var serverURL = 'http://intentparser.sd2e.org';
var versionString = '2.10';

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

	const helpMenu = ui.createMenu('Help');
	helpMenu.addSubMenu(tableHelpMenu);
	helpMenu.addItem('About', 'showHelp');

	const menu = ui.createMenu('Parse Intent');
	menu.addItem('Add to SynBioHub', 'addToSynBioHub');
	menu.addItem('Analyze from cursor', 'sendAnalyzeFromCursor');
	menu.addItem('Analyze from top', 'sendAnalyzeFromTop');
	menu.addItem('Calculate samples for measurements table', 'calculateSamples');
    menu.addItem('Generate OPIL', 'sendOpilRequest');
	menu.addItem('Generate Report', 'sendGenerateReport');
	menu.addItem('Generate Structured Request', 'sendGenerateStructuredRequest');
	menu.addItem('Report Experiment Status', 'reportExperimentStatus');
	menu.addItem('Request Experiment Execution', 'executeExperiment');
	menu.addItem('Suggest Additions by Spelling from cursor', 'addBySpellingFromCursor');
	menu.addItem('Suggest Additions by Spelling from top', 'addBySpelling');
	menu.addItem('Update experimental results', 'updateExperimentalResults');
	menu.addItem('Validate Structured Request', 'sendValidateStructuredRequest');
	menu.addSubMenu(tablesMenu);
	menu.addItem('File Issues', 'reportIssues');
	menu.addSubMenu(helpMenu);
	menu.addToUi();
}

function reportControlsInfo(){
	html_content = '<h2> Controls Table </h2>\n' +
		'<p><b>Description</b>: control definition based on time, strain, contents, etc.</p>\n' +
		'<b>Required fields:</b>\n' +
		'<ul>\n' +
		'\t<li><a href="https://schema.catalog.sd2e.org/schemas/control_type.json"> <b>Type</b></a>: an expected type for this control. <i>Example:</i> HIGH_FITC</li>\n' +
		'\t<li><b>Strains</b>: a list of one or more text values representing a strain listed in the SBOL Dictionary lab name. <i>Example:</i> B_subtilis_comKS_mCherry_1x</li>\n' +
		'</ul>\n' +
		'<b>Optional fields:</b>\n' +
		'<ul>\n' +
		'\t<li><b>Channel</b>: a text value representing FCS channel. <i>Example:</i> BL1-A</li>\n' +
		'\t<li><b>Contents</b>: a list of one or more text values representing the content of a control. A content can come in the form of a name or a name followed by a value, followed by a timepoint unit. <i>Example:</i> beta_estradiol or beta_estradiol 0.05 micromole</li>\n' +
		'\t<li><b><a href="https://schema.catalog.sd2e.org/schemas/time_unit.json">Timepoints</a></b>: a list of one or more text values representing point in a time series. <i>Example:</i> 2, 4 hours</li>\n' +
		'</ul>';
	showSidebar(html_content);
}

function reportLabInfo(){
	html_content = '<h2> Lab Table </h2>\n' +
		'<p><b>Description</b>: information linked to a lab.</p>\n' +
		'<b>Required fields:</b>\n' +
		'<ul>\n' +
		'\t<li><a href="https://schema.catalog.sd2e.org/schemas/lab.json"> <b>Lab</b></a>: a text value representing the lab that performed this experiment. <i>Example:</i> TACC</li>\n' +
		'</ul>\n' +
		'<b>Optionalfields:</b>\n' +
		'<ul>\n' +
		'\t<li><b>Experiment_id</b>: a text identifier, namespaced performer, for the experiment <i>Example:</i> 123</li>\n' +
		'</ul>'
	showSidebar(html_content);
}

function reportMeasurementsInfo(){
	html_content = '<h2> Measurements Table </h2>\n' +
		'<p><b>Description</b>: measurements expected to be produced for a run, broken down by measurement type and sample conditions</p>\n' +
		'<b>Required fields:</b>\n' +
		'<ul>\n' +
		'\t<li><a href="https://schema.catalog.sd2e.org/schemas/measurement_type.json"> <b>Measurement Type</b></a>: an expected file type for this measurement. <i>Example:</i> RNA_SEQ</li>\n' +
		'\t<li><a href="https://schema.catalog.sd2e.org/schemas/filetype_label.json"> <b>File Type</b></a>: a list of one or more expected file type for this measurement. <i>Example:</i> MSWORD, SPREADSHEET</li>\n' +
		'</ul>\n' +
		'<b>Optional fields:</b>\n' +
		'<ul>\n' +
		'\t<li><b>Batch</b>: a list of one or more numerical values representing the batches a measurement belongs to. <i>Example:</i> 1, 2, 3</li>\n' +
		'\t<li><b>Controls</b>: a list of Control Table captions for representing expected control elements for this run <i>Example:</i> Table 1, Table 2</li>\n' +
		'\t<li><b>Ods</b>: a list of one or more numerical values representing expected optical densities for this measurement. <i>Example:</i> 5</li>\n' +
		'\t<li><b>Replicates</b>: a list of one or more numerical values representing expected number of replicates. <i>Example:</i> 6</li>\n' +
		'\t<li><b>Strains</b>: a list of one or more string values representing expected strains for this measurement. Strains listed in this field must have a hyperlink that references to a SBH URI. <i>Example:</i> UWBF_6390</li>\n' +
		'\t<li><a href="https://schema.catalog.sd2e.org/schemas/temperature.json"><b>Temperatures</b></a>: a list of one or more numerical values followed by a temperature unit representing expected temperatures for this measurement. <i>Example</i>: 30 celsius</li>\n' +
		'\t<li><a href="https://schema.catalog.sd2e.org/schemas/time_unit.json"><b>Timepoints</b></a>: a list of one or more numerical values followed by a timepoint unit representing expected timepoints for this run. <i>Example:</i> 0, 4, 8, 12, 16 hour</li>\n' +
		'\t<li><b>Column_id</b>: a list of one or more numerical values to signify which column of which run received which inducer concentration. <i>Example:</i> 2</li>\n' +
		'\t<li><b>Row_id</b>: a list of one or more numerical values signify which row of which run received which inducer concentration. <i>Example:</i> 1</li>\n' +
		'\t<li><b>lab_id</b>: a list of one or more text values to specify lab ids. <i>Example:</i> abc</li>\n' +
		'\t<li><b>Number of Negative Controls</b>: a list of integers. <i>Example:</i> 1, 2, 3</li>\n' +
		'\t<li><b>Use RNAse Inhibitor in Reaction</b>: a list of boolean values. <i>Example:</i> True, False</li>\n' +
		'\t<li><b>DNA Reaction Concentration</b>: a list of integers. <i>Example:</i> 1, 2, 3</li>\n' +
		'\t<li><b>Template DNA</b>: a list of string. <i>Example:</i> a, b, c</li>\n' +
		'</ul>';
	showSidebar(html_content);
}

function showHelp() {
	var helpHTML = '\
		<p>\
		Intent Parser version %s\
		</p>\
		<p>\
		The purpose of the intent parser add-on is to create a suite of tools that aids the user in creating well documented experimental plans.\
		</p>\
		<p>\
		Several different actions help users link terms to SynbioHub, to create a better trail of documentation.  \
		The first action is <b><i>analyzing</i></b> the document, which searches for terms present in the SD2 spreadsheet dictionary and offers to insert links to the SynbioHub definition of those terms.  \
		Additionally, the document can be scanned for terms that do not exist in the <b><i>spelling</i></b> dictionary and suggest them as terms to possibly additions into the SD2 spreadsheet dictionary or to have a link manually added.  \
		Users can also highlight arbitrary terms and <b><i>add</i></b> a definition to SynbioHub for that term.  \
		This <b><i>add</i></b> dialog will also query SynbioHub for matches to the selected term and links to those terms can be added.\
		</p>\
		<p>\
		Intent parser can also help create structured requests from the experimental request document.  \
		This works by creating a table for the measurements which can be parsed.  \
		The first step in this is creating a measurements table template, using the <b><i>create table templates</i></b> file menu option.  \
		The measurements table template dialog will ask a few questions about the table, and then insert the table template into the document.  \
		Users will need to enter the reagent names in the blank columns and fill in the rest of the table.  \
		Each table cell can accept a comma separated list of values and units should be specified where appropriate.  \
		If only one value in the comma-separated list has a unit, that unit will be used for all entries in the list.  \
		For instance, the entry "0, 4, 8, 12 hour" will use the unit of hour for each entry.  \
		Once the measurements table is complete, a structured request can be generated with the <b><i>Generate Structured Request</i></b> file menu option, which will create a json file that can be saved for later use.  \
		Additionally, the <b><i>Validate Structured Request</i></b> option can be used to generate and validate a structured request.  \
		If the request fails validation, an error message will be printed which indicates that the request failed validation, and why.  \
		</p>\
		<p>\
		Problems? <a href="https://gitlab.sd2e.org/sd2program/experimental-intent-parser/issues"  target=_blank>File and issue</a>\
		</p>\
		';
		verFormattedHTML = Utilities.formatString(helpHTML, versionString);
		showModalDialog(verFormattedHTML, 'Help', 600, 600);
}

function validate_uri(uri) {
	try {
		var response = UrlFetchApp.fetch(uri);
		if (response.getResponseCode() == 200) {
			return true;
		}
		else {
			return false;
		}
	}
	catch (e) {
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
		}
		else { // If URI is invalid, reprompt
			var result = ui.prompt('Entered URI was invalid!\n' + title, msg, ui.ButtonSet.OK_CANCEL);
			button = result.getSelectedButton();
			text = result.getResponseText();
		}
	}
	return [false, text];
}

function executeExperiment() {
	sendPost('/executeExperiment');
}

function reportExperimentStatus() {
	let doc = DocumentApp.getActiveDocument();
	let cursorPosition = doc.getCursor();

	if(cursorPosition == null) {
		// Cursor position is null, so assume a selection
		const selectionRange = doc.getSelection();
		const rangeElement = selectionRange.getRangeElements()[0];
		// Extract element and offset from end of selection
		var el = rangeElement.getElement();
	}
	else {
		// Select element and off set from current position
		var el = cursorPosition.getElement();
	}
	const childIndex = doc.getBody().getChildIndex(el);
	const data = {'childIndex' : childIndex};
	sendPost('/reportExperimentStatus', data);
}

function sendMessage(message) {
	var request = {'message': message};
	var requestJSON = JSON.stringify(request);
	var options = {'method' : 'post',
				   'payload' : requestJSON };
	UrlFetchApp.fetch(serverURL + '/message', options);
}

function buttonClick(buttonName) {
	sendPost('/buttonClick', {'buttonId' : buttonName});
}

function processActions(response) {
	if( typeof(response.actions) == 'undefined' ) {
		return;
	}
	var actions = response.actions;
	waitForMoreActions = false;
	for( var actionKey in actions) {
		var actionDesc = actions[actionKey];
		switch(actionDesc['action']) {
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
				if (sampleColIdx < 0){
					// Create new column for samples
					var numCols = tables[tableIds[tIdx]].getRow(0).getNumCells();
					tables[tableIds[tIdx]].getRow(0).appendTableCell("samples");
					for (var rowIdx = 1; rowIdx < numRows; rowIdx++)
					{
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
			try{
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

				for(var idx=0; idx < colSizes.length; ++idx) {
					newTable.setColumnWidth(idx, colSizes[idx] * 7);
				}

				if (actionDesc['tableType'] == 'measurements') {
					labTableData = actionDesc['tableLab'];
					var newLabTable = body.insertTable(childIndex, labTableData);
					newLabTable.setAttributes(tableStyle);
				}
			}
			catch (err){
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
		case 'showSidebar':
			showSidebar(actionDesc['html']);
			break;
		case 'showProgressbar':
			showSidebar(actionDesc['html']);
			var p = PropertiesService.getDocumentProperties();
			p.setProperty("analyze_progress", '0');
			waitForMoreActions = true;
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

function getAnalyzeProgress() {
	var p = PropertiesService.getDocumentProperties();
	return p.getProperty("analyze_progress");
}

function showSidebar(html) {
	var user = Session.getActiveUser();
	var userEmail = user.getEmail();

	var ui = DocumentApp.getUi();
	var htmlOutput = HtmlService.createHtmlOutput(html);
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

	if( typeof(data) != 'undefined' ) {
		request['data'] = data;
	}

	var requestJSON = JSON.stringify(request);
	var options = {
			'method' : 'post',
			'payload' : requestJSON,
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
	while(parent != null) {
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
		for(i=0; i<identity.length; ++i) {
			val = identity[i];
			str += '' + val + '.';
		}

	return str;
}

function compareIdentities(identity1, identity2) {
	for(var idx=0; idx<identity1.length; ++idx) {
		if(idx >= identity2.length) {
			// identity2 is smaller
			// This compare function returns true here because
			// identity1 is a parent of identity2
			return 0;
		}

		if(identity1[idx] < identity2[idx]) {
			// identity1 is smaller
			return -1;
		}

		if(identity1[idx] > identity2[idx]) {
			// identity1 is larger
			return 1;
		}
	}

	if(identity2.length > identity1.length) {
		// identity1 is smaller
		return -1;
	}

	// identity1 and identity2 are equal
	return 0;
}

//Find a paragraph identified by an array or hierarchy
//indicies using a binary search
function findParagraph(identity, paragraphList) {
	if(paragraphList.length < 4) {
		// If the list size is less than 4, do a brute force
		// search
		for(var idx=0; idx<paragraphList.length; ++idx) {
			var pCompare = paragraphList[idx];
			var valIdentity = identifyParagraph(pCompare);
			if(compareIdentities(identity, valIdentity) == 0) {
				return idx;
			}
		}
		return null;
	}

	// Use the middle element to decide whether to search
	// the first half of entries of the second half of
	// entries
	var middle = Math.floor(paragraphList.length / 2);
	var middleElement = paragraphList[ middle ];
	var middleIdentity = identifyParagraph(middleElement);

	if(compareIdentities(identity, middleIdentity) < 0) {
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

	if(elType == elType.TEXT) {
		return element;
	}

	if(typeof element.getNumChildren != 'function') {
		return null;
	}

	for(var i=0; i<element.getNumChildren(); ++i) {
		var child = element.getChild(i);

		var result = findTEXT(child);
		if(result != null) {
			return result;
		}
	}

	return null;
}

//Find the cursor location
function findCursor() {
	var doc = DocumentApp.getActiveDocument();

	var cursorPosition = doc.getCursor();

	if(cursorPosition == null) {
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
	if(elementType != elementType.TEXT && offset > 0) {
		var textElement = findTEXT(el);
		if(textElement != null) {
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

	if(result == null) {
		return null;
	} else {
		return {'paragraphIndex': result,
			'offset': offset};
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
		html += '<a href=' + serverURL + '/document_report?';
		html += docId + ' target=_blank>here</a>';
		html += '</p>';
		html += '\n';
		html += '<input id=okButton Button value="Done" ';
		html += 'type="button" onclick="onSuccess()" />\n';
		html += '</center>';
		showModalDialog(html, 'Download', 300, 100);
}

function reportIssues(){
	helpHTML = '\
		<p>Something unexpected happen with the intent-parser plugin?</p> \
		<p>Want to request a feature support?</p> \
		<p>Send a bug report <a href="https://gitlab.sd2e.org/sd2program/experimental-intent-parser/issues"  target=_blank>here</a>.</p> \
		';
		verFormattedHTML = Utilities.formatString(helpHTML, versionString);
		showModalDialog(verFormattedHTML, 'Issues', 400, 200);
}

function sendOpilRequest(){
    sendPost('/generateOpilRequest', getBookmarks());
}

function sendValidateStructuredRequest() {
	sendPost('/validateStructuredRequest', getBookmarks());
}

function sendGenerateStructuredRequest() {
	sendPost('/generateStructuredRequest', getBookmarks());
}

function getBookmarks(){
	var doc = DocumentApp.getActiveDocument();
	var bookmarks = doc.getBookmarks();
	var result = [];
	for(var bookmark of bookmarks){
		var bookmark_id = bookmark.getId();
		var bookmark_text = bookmark.getPosition().getElement().asText().getText();
		result.push({id:bookmark_id, text: bookmark_text});
	}
	return {'bookmarks': result};
}

function addToSynBioHub() {
	var doc = DocumentApp.getActiveDocument();
	selectionRange = doc.getSelection();

	if(selectionRange == null) {
		return;
	}

	// Cursor position is null, so assume a selection
	var selectionRange = doc.getSelection();
	var rangeElements = selectionRange.getRangeElements();
	var firstElement = rangeElements[0];
	var lastElement = rangeElements[ rangeElements.length - 1 ];

	// Extract element and offset from end of selection
	var startEl = firstElement.getElement();
	var startOffset = firstElement.getStartOffset();
	var startLocation = getLocation(startEl, startOffset);

	var endEl = lastElement.getElement();
	var endOffset = lastElement.getEndOffsetInclusive();
	var endLocation = getLocation(endEl, endOffset);

	var selection = {'start': startLocation,
					 'end': endLocation};
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

function createControlsTable(){
	let doc = DocumentApp.getActiveDocument();
	let cursorPosition = doc.getCursor();

	if(cursorPosition == null) {
		// Cursor position is null, so assume a selection
		const selectionRange = doc.getSelection();
		const rangeElement = selectionRange.getRangeElements()[0];
		// Extract element and offset from end of selection
		var el = rangeElement.getElement();
	}
	else {
		// Select element and off set from current position
		var el = cursorPosition.getElement();
	}
	const childIndex = doc.getBody().getChildIndex(el);
	const data = {'childIndex' : childIndex, 'tableType' : 'controls'};
	sendPost('/createTableTemplate', data);
}

function createTableMeasurements() {
	let doc = DocumentApp.getActiveDocument();
	let cursorPosition = doc.getCursor();

	if(cursorPosition == null) {
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
	const data = {'childIndex' : childIndex, 'tableType' : 'measurements'};
	sendPost('/createTableTemplate', data);
}

function createParameterTable(){
	let doc = DocumentApp.getActiveDocument();
	let cursorPosition = doc.getCursor();

	if(cursorPosition == null) {
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
	const data = {'childIndex' : childIndex, 'tableType' : 'parameters'};
	sendPost('/createTableTemplate', data);
}

