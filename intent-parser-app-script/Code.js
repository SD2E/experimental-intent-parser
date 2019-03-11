var gItemMap = null
var gCurrentRange = null
var serverURL = 'http://dsumorok.mooo.com:7775'

function onOpen() {
  var ui = DocumentApp.getUi()
  var menu = ui.createMenu('Parse Intent')

  menu.addItem('Analyze Document', 'sendAnalyzeRequest').addToUi()

  resetScan();
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

function processActions(actions) {
  for( var actionKey in actions) {
    var actionDesc = actions[actionKey]

    switch(actionDesc['action']) {
      case 'highlightText':
        var paragraphIndex = actionDesc['paragraph_index']
        var offset = actionDesc['offset']
        var endOffset = actionDesc['end_offset']
        highlightDocText(paragraphIndex, offset, endOffset)
        break;

      case 'linkText':
        var paragraphIndex = actionDesc['paragraph_index']
        var offset = actionDesc['offset']
        var endOffset = actionDesc['end_offset']
        var url = actionDesc['url']
        linkDocText(paragraphIndex, offset, endOffset, url)
        break;

      case 'showSidebar':
        showSidebar(actionDesc['html'])
        break;

      case 'showModalDialog':
        showModalDialog(actionDesc['html'], actionDesc['title'],
                        actionDesc['width'], actionDesc['height'])
        break;

      default:
        break;
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

  var request = {
    'documentId': docId
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
  var actions = JSON.parse(responseText)

  processActions(actions)
}

function sendAnalyzeRequest() {
  sendPost('/analyzeDocument')
}
