var serverURL = 'http://intent-parser-server.bbn.com'

var versionString = '1.0-git'

function onOpen() {
  var ui = DocumentApp.getUi()
  var menu = ui.createMenu('Parse Intent')

  menu.addItem('Analyze from top', 'sendAnalyzeFromTop').addToUi()
  menu.addItem('Analyze from cursor', 'sendAnalyzeFromCursor').addToUi()
  menu.addItem('Add to SynBioHub', 'addToSynBioHub').addToUi()
  menu.addItem('Suggest Additions by Spelling from top', 'addBySpelling').addToUi()
  menu.addItem('Suggest Additions by Spelling from cursor', 'addBySpellingFromCursor').addToUi()
  menu.addItem('Generate Report', 'sendGenerateReport').addToUi()
  menu.addItem('Help', 'showHelp').addToUi()

  resetScan();
}

function showHelp() {
  helpHTML = '\
<p>\
Intent Parser version %s\
</p>\
<p>\
The purpose of the intent parser add-on is to create a suite of tools that aids the user in creating well documented experimental plans.\
</p>\
<p>\
Right now, there are three different actions that can be performed to help the user.  The first action is <i>analyzing</i> the document, which searches for terms present in the SD2 spreadsheet dictionary and offers to insert links to the SynbioHub definition of those terms.  Additionally, the document can be scanned for terms that do not exist in the <i>spelling</i> dictionary and suggest them as terms to possibly add into the SD2 spreadsheet dictionary or to have a link manually added.  Users can also highlight arbitrary terms and <i>add</i> a definition to SynbioHub for that term.  This <i>add</i> dialog will also query SynbioHub for matches to the selected term and links to those terms can be added.\
</p>\
'
  verFormattedHTML = Utilities.formatString(helpHTML, versionString)
  showModalDialog(verFormattedHTML, 'Help', 600, 600)
}

function validate_uri(uri) {
    try {
        var response = UrlFetchApp.fetch(uri)
        if (response.getResponseCode() == 200) {
            return true
        } else {
            return false
        }
    } catch (e) {
        return false
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
            return [true, text]
        } else { // If URI is invalid, reprompt
            var result = ui.prompt('Entered URI was invalid!\n' + title, msg, ui.ButtonSet.OK_CANCEL);
            button = result.getSelectedButton();
            text = result.getResponseText()
        }
    }
    return [false, text]
}

function sendMessage(message) {
  var request = {
    'message': message
  }

  var requestJSON = JSON.stringify(request);

  var options = {
    'method' : 'post',
    'payload' : requestJSON
  };

  UrlFetchApp.fetch(serverURL + '/message', options)
}

function buttonClick(buttonName) {
  sendPost('/buttonClick', {'buttonId' : buttonName})
}

function processActions(response) {
  if( typeof(response.actions) == 'undefined' ) {
    return
  }

  var actions = response.actions

  for( var actionKey in actions) {
    var actionDesc = actions[actionKey]

    switch(actionDesc['action']) {
      case 'highlightText':
        var paragraphIndex = actionDesc['paragraph_index']
        var offset = actionDesc['offset']
        var endOffset = actionDesc['end_offset']
        highlightDocText(paragraphIndex, offset, endOffset)
        break

      case 'linkText':
        var paragraphIndex = actionDesc['paragraph_index']
        var offset = actionDesc['offset']
        var endOffset = actionDesc['end_offset']
        var url = actionDesc['url']
        linkDocText(paragraphIndex, offset, endOffset, url)
        break

      case 'showSidebar':
        showSidebar(actionDesc['html'])
        break

      case 'reportContent':
        processReportContent(actionDesc['report'])
        break

      case 'showModalDialog':
        showModalDialog(actionDesc['html'], actionDesc['title'],
                        actionDesc['width'], actionDesc['height'])
        break

      default:
        break
    }
  }
}

function showSidebar(html) {
    var ui = DocumentApp.getUi()
    var htmlOutput = HtmlService.createHtmlOutput(html)
    ui.showSidebar(htmlOutput)
}

function showModalDialog(html, title, width, height) {
    var ui = DocumentApp.getUi()
    var htmlOutput = HtmlService.createHtmlOutput(html)
    htmlOutput.setWidth(width)
    htmlOutput.setHeight(height)

    ui.showModalDialog(htmlOutput, title)
}

function highlightDocText(paragraphIndex, offset, endOffset) {
  var doc = DocumentApp.getActiveDocument()
  var body = doc.getBody()
  var paragraph = body.getParagraphs()[paragraphIndex]
  var docText = paragraph.editAsText()
  var selectionRange = doc.newRange()

  selectionRange.addElement(docText, offset, endOffset)

  doc.setSelection(selectionRange.build())
}

function linkDocText(paragraphIndex, offset, endOffset, url) {
  var doc = DocumentApp.getActiveDocument()
  var body = doc.getBody()
  var paragraph = body.getParagraphs()[paragraphIndex]
  var docText = paragraph.editAsText()

  docText.setLinkUrl(offset, endOffset, url)
}

function sendPost(resource, data) {
  var docId = DocumentApp.getActiveDocument().getId();
  var user = Session.getActiveUser();
  var userEmail = user.getEmail();

  var request = {
    'documentId': docId,
    'user': user,
    'userEmail': userEmail
  }

  if( typeof(data) != 'undefined' ) {
    request['data'] = data;
  }

  var requestJSON = JSON.stringify(request);

  var options = {
    'method' : 'post',
    'payload' : requestJSON
  };

  response = UrlFetchApp.fetch(serverURL + resource, options)
  var responseText = response.getContentText()
  var responseOb = JSON.parse(responseText)

  processActions(responseOb)

  return responseOb.results
}

// Identifies a paragraph with an array of hierarchy indicies
function identifyParagraph(element) {
  var foundParagraph = true;
  var identity = []

  var parent = element.getParent();
  while(parent != null) {
    elementType = element.getType();

    var idx = parent.getChildIndex(element)
    identity.push(idx)

    element = parent;
    parent = element.getParent();
  }

  return identity.reverse();
}

function identity2str(identity) {
  str = ''
  for(i=0; i<identity.length; ++i) {
    val = identity[i]
    str += '' + val + '.'
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
      return -1
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

// Find a paragraph identified by an array or hierarchy
// indicies using a binary search
function findParagraph(identity, paragraphList) {
  if(paragraphList.length < 4) {
    // If the list size is less than 4, do a brute force
    // search
    for(var idx=0; idx<paragraphList.length; ++idx) {
      var pCompare = paragraphList[idx]
      var valIdentity = identifyParagraph(pCompare)
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
    var startIndex = 0

  } else {

    var newList = paragraphList.slice(middle,
                                      paragraphList.length)
    startIndex = middle
  }

  return startIndex + findParagraph(identity, newList);
}

// Finds TEXT element under element
function findTEXT(element) {
  var elType = element.getType()

  if(elType == elType.TEXT) {
    return element;
  }

  if(typeof element.getNumChildren != 'function') {
    return null;
  }

  for(var i=0; i<element.getNumChildren(); ++i) {
    var child = element.getChild(i)

    var result = findTEXT(child)
    if(result != null) {
      return result
    }
  }

  return null;
}

// Find the cursor location
function findCursor() {
  var doc = DocumentApp.getActiveDocument()

  var cursorPosition = doc.getCursor()

  if(cursorPosition == null) {
    // Cursor position is null, so assume a selection
    selectionRange = doc.getSelection()
    rangeElement = selectionRange.getRangeElements()[0]

    // Extract element and offset from end of selection
    var el = rangeElement.getElement()
    var offset = rangeElement.getEndOffsetInclusive()

  } else {
    // Select element and off set from current position
    var el = cursorPosition.getElement()
    var offset = cursorPosition.getOffset()
  }

  var elementType = el.getType()
  // Handle special case of cursor at the end of a paragraph
  if(elementType != elementType.TEXT) {
    var textElement = findTEXT(el)
    if(textElement != null) {
      var length = textElement.getText().length
      offset = length - 1
    }
  }

  return getLocation(el, offset)
}

function getLocation(el, offset) {
  var doc = DocumentApp.getActiveDocument()

  // Get the ordared list of paragraphs
  var plist = doc.getBody().getParagraphs()

  // Identify the element by its location in the
  // document hierarchy.
  identity = identifyParagraph(el);

  // Find the index in plist of the paragraph with the
  // same
  var result = findParagraph(identity, plist)

  if(result == null) {
    return null
  } else {
    return {'paragraphIndex': result,
            'offset': offset}
  }
}

function sendAnalyzeFromTop() {
  sendPost('/analyzeDocument')
}

function sendAnalyzeFromCursor() {
  var cursorLocation = findCursor()

  sendPost('/analyzeDocument', cursorLocation)
}

function sendGenerateReport() {
  var docId = DocumentApp.getActiveDocument().getId();

  var html = ''
  html += '<script>\n'
  html += 'function onSuccess() {\n'
  html += '  google.script.host.close()\n'
  html += '}\n'
  html += '</script>\n'
  html += '\n'
  html += '<p>'
  html += '<center>'

  html += 'Download Report '
  html += '<a href=' + serverURL + '/document_report?'
  html += docId + ' target=_blank>here</a>'

  html += '</p>'
  html += '\n'
  html += '<input id=okButton Button value="Done" '
  html += 'type="button" onclick="onSuccess()" />\n'
  html += '</center>'

  showModalDialog(html, 'Download', 300, 100)
}

function addToSynBioHub() {
  var doc = DocumentApp.getActiveDocument()
  selectionRange = doc.getSelection()

  if(selectionRange == null) {
    return
  }

    // Cursor position is null, so assume a selection
  var selectionRange = doc.getSelection()
  var rangeElements = selectionRange.getRangeElements()
  var firstElement = rangeElements[0]
  var lastElement = rangeElements[ rangeElements.length - 1 ]

  // Extract element and offset from end of selection
  var startEl = firstElement.getElement()
  var startOffset = firstElement.getStartOffset()
  var startLocation = getLocation(startEl, startOffset)

  var endEl = lastElement.getElement()
  var endOffset = lastElement.getEndOffsetInclusive()
  var endLocation = getLocation(endEl, endOffset);

  var selection = {'start': startLocation,
                   'end': endLocation}

  sendPost('/addToSynBioHub', selection)
}

function addBySpelling() {
  sendPost('/addBySpelling')
}

function addBySpellingFromCursor() {
  var cursorLocation = findCursor()

  sendPost('/addBySpelling', cursorLocation)
}

function submitForm(formData) {
  return sendPost('/submitForm', formData)
}

function postFromClient(postInfo) {
  return sendPost(postInfo.resource, postInfo.data)
}
