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

      case 'showSidebar':
        showSidebar(actionDesc['html'])
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

function highlightDocText(paragraphIndex, offset, endOffset) {
  var doc = DocumentApp.getActiveDocument()
  var body = doc.getBody()
  var paragraph = body.getParagraphs()[paragraphIndex]
  var docText = paragraph.editAsText()
  var selectionRange = doc.newRange()

  selectionRange.addElement(docText, offset, endOffset)

  doc.setSelection(selectionRange.build())
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


function generateItemMap() {
  itemMap = {} //new Object();

  itemMap["Kan"] = "https://hub.sd2e.org/user/sd2e/design/Kan/1"
  itemMap["Chloramphenicol"] = "https://hub.sd2e.org/user/sd2e/design/CAT_C0378/1"
  itemMap["MG1655"] = "https://hub.sd2e.org/user/sd2e/design/MG1655_PhlF_Gate/1"
  itemMap["MG1655_WT"] = "https://hub.sd2e.org/user/sd2e/design/MG1655_WT/1"
  itemMap["arabinose"] = "https://hub.sd2e.org/user/sd2e/design/Larabinose/1"
  itemMap["IPTG"] = "https://hub.sd2e.org/user/sd2e/design/IPTG/1"
  itemMap["PhlF"] = "https://hub.sd2e.org/user/sd2e/design/MG1655_PhlF_Gate/1"
  itemMap["IcaR"] = "https://hub.sd2e.org/user/sd2e/design/MG1655_IcaR_Gate/1"
  itemMap["NAND"] = "https://hub.sd2e.org/user/sd2e/design/UWBF_8542/1"
  itemMap["pBAD"] = "https://hub.sd2e.org/user/sd2e/design/pBAD/1"
  
  return itemMap
}
