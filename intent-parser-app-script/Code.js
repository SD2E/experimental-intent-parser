var gItemMap = null
var gCurrentRange = null
var serverURL = 'http://dsumorok.mooo.com:7775'

function onOpen() {
  var ui = DocumentApp.getUi()
  var menu = ui.createMenu('Parse Intent')
  
  menu.addItem('Scan Document', 'scanDocument').addToUi()
  menu.addItem('Reset Scan', 'resetScan').addToUi()
  menu.addItem('Fetch Test', 'sendAnalyzeRequest').addToUi()
  
  resetScan();
}

function processBody(body) {
}

function fetchTest() {
  //x = 6
  //var response = UrlFetchApp.fetch('http://dsumorok.mooo.com:2531/')
  //Logger.log(response.getContent())
  //x = 3
  
  var response = UrlFetchApp.fetch('http://www.boston.com/')
  var responseBlob = Utilities.newBlob(response, 'text/plain')
  //Logger.log(responseBlob.getDataAsString())
  
  var resumeBlob = Utilities.newBlob('Hire me!', 'text/plain', 'resume.txt');
  var formData = {
    'name': 'Bob Smith',
    'email': 'bob@example.com',
    'resume': resumeBlob
  };
  
  var docId = DocumentApp.getActiveDocument().getId();

  var test = {
    'documentId': docId
  }
  
  var testJSON = JSON.stringify(test);
  
  var options = {
    'method' : 'post',
    'payload' : testJSON
  };
  
  response = UrlFetchApp.fetch('http://dsumorok.mooo.com:7775/analyzeDocument', options)
  var responseText = response.getContentText()
}

function sendEmptyMessage() {
  sendMessage('test')
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
  sendMessage('Clicked ' + buttonName)
}

function processActions(actions) {
  for( var actionKey in actions) {
    var actionDesc = actions[actionKey]

    switch(actionDesc['action']) {
      case 'highlightText':
        var startIndex = actionDesc['start_index']
        var endIndex = actionDesc['end_index']
        //highlightDocText(startIndex, endIndex)
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

function highlightDocText(startIndex, endIndex) {
  var doc = DocumentApp.getActiveDocument()
  var body = doc.getBody()
  var docText = body.editAsText()
  var selectionRange = doc.newRange()

  selectionRange.addElement(docText, startIndex, endIndex)

  doc.setSelection(selectionRange.build())
}

function sendAnalyzeRequest() {
  var docId = DocumentApp.getActiveDocument().getId();

  var request = {
    'documentId': docId
  }
  
  var requestJSON = JSON.stringify(request);
  
  var options = {
    'method' : 'post',
    'payload' : requestJSON
  };
  
  response = UrlFetchApp.fetch(serverURL + '/analyzeDocument', options)
  var responseText = response.getContentText()
  var actions = JSON.parse(responseText)
  
  processActions(actions)

  return

  if( 'highlight_start' in client_state ) {
    var highlight_start = client_state['highlight_start']
    var highlight_end = client_state['highlight_end']

    var selectionRange = doc.newRange()
    selectionRange.addElement(docText, highlight_start,
                              highlight_end)
    doc.setSelection(selectionRange.build())
  }

  if( 'html' in client_state ) {
    var ui = DocumentApp.getUi()
    var htmlMessage = client_state['html']
    var htmlOutput = HtmlService.createHtmlOutput(htmlMessage)
    ui.showSidebar(htmlOutput)
  }
  
  var searchType = DocumentApp.ElementType.PARAGRAPH
  
  var count = 0;
  searchResult = null;
  
  while( true ) {
    searchResult = body.findElement(searchType, searchResult)
    if( searchResult == null ) {
      break;
    }
    
    ++count;
  }

  var endIndex = count
}


function resetScan() {
  var itemMap = generateItemMap()

  var itemKeys = []
  for(key in itemMap) {
    itemKeys.push(key)
  }
  
  var userProperties = PropertiesService.getUserProperties()
  userProperties.deleteAllProperties()
  
  var scanState = {}
  scanState['ITEM_MAP'] = itemMap
  scanState['ITEM_KEYS'] = itemKeys
  scanState['KEY_INDEX'] = 0
  scanState['RESULT_INDEX'] = 0
  
  userProperties.setProperty('SCAN_STATE', JSON.stringify(scanState))
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

function findNextItem(doc, scanState) {
  var body = doc.getBody()

  var itemMap = scanState['ITEM_MAP']
  var itemKeys = scanState['ITEM_KEYS']
  var keyIndex = scanState['KEY_INDEX']
  var resultIndex = scanState['RESULT_INDEX']
  
  while(keyIndex < itemKeys.length) {
    var key = itemKeys[keyIndex]
    var foundRange = null;
    var i = 0;

    for(i=0; i<=resultIndex; ++i) {
      if(foundRange == null) {
        foundRange = body.findText(key)
      } else {
        foundRange = body.findText(key, foundRange)
      }

      if(foundRange == null) {
        ++keyIndex;
        break;
      }
    }

    if(foundRange == null) {
      continue
    }

    scanState['KEY_INDEX'] = keyIndex
    scanState['RESULT_INDEX'] = i;
    var result = {range:foundRange,
                  key:key,
                  value:itemMap[key]}
      
    return result
  }

  return null;  

  if(keyIndex >= itemKeys.length) {
    return null;
  }
}

function findNextItem2(doc, startRange, scanState) {
  var body = doc.getBody()

  var itemMap = scanState['ITEM_MAP']

  for(key in itemMap) {
    var foundRange = null;
    
    if(startRange == null) {
      foundRange = body.findText(key)
    } else {
      foundRange = body.findText(key, startRange)
    }

    if(foundRange == null) {
      continue
    }
    
    var result = {range:foundRange,
                    key:key,
                  value:itemMap[key]}

    return result
  }
  
  return null;
}

function replaceValue() {
  var userProperties = PropertiesService.getUserProperties()
  var scanState = JSON.parse( userProperties.getProperty('SCAN_STATE') )

  var doc = DocumentApp.openById('1E10P6bH13naJp2eB5_epEgqUklCU6RHmzmLsyfNUPOw')

  scanState['RESULT_INDEX'] -= 1

  result = findNextItem(doc, scanState)
  
  var itemKeys = scanState['ITEM_KEYS']
  var keyIndex = scanState['KEY_INDEX']
  var itemMap = scanState['ITEM_MAP']
  var oldText = itemKeys[keyIndex]
  var newText = itemMap[oldText]
  
  var currentRange = result.range;

  var startOffset = currentRange.getStartOffset()
  var endOffset = currentRange.getEndOffsetInclusive()
  var element = currentRange.getElement()
  var text = element.asText()
  
  //text.deleteText(startOffset, endOffset)
  //text.insertText(startOffset, newText)
  text.setLinkUrl(startOffset, endOffset, newText)
}

function yesClick() {
  replaceValue();
  scanDocument();
}

function noClick() {
  scanDocument();
}

function scanDocument() {
  var userProperties = PropertiesService.getUserProperties()
  var scanState = JSON.parse( userProperties.getProperty('SCAN_STATE') )

  var doc = DocumentApp.openById('1E10P6bH13naJp2eB5_epEgqUklCU6RHmzmLsyfNUPOw')

  result = findNextItem(doc, scanState)
  
  userProperties.setProperty('SCAN_STATE', JSON.stringify(scanState))

  if(result == null) {
    return
  }
  
  var currentRange = result.range;

  var startOffset = currentRange.getStartOffset()
  var endOffset = currentRange.getEndOffsetInclusive()
  var selectionRange = doc.newRange()
  var element = currentRange.getElement()
  var text = element.asText()

  // Select word
  selectionRange.addElement(text, startOffset, endOffset)
  doc.setSelection(selectionRange.build())

  showSidebar(result)
}

function showSidebar2(result) {
  var ui = DocumentApp.getUi()
  var htmlMessage = ''

  htmlMessage += "<script>"
  htmlMessage += 'function yesClick() { '
  htmlMessage += '  google.script.run.yesClick() '
  htmlMessage += '}'
  htmlMessage += "</script>"
  
  htmlMessage += "<script>"
  htmlMessage += 'function noClick() { '
  htmlMessage += '  google.script.run.noClick() '
  htmlMessage += '}'
  htmlMessage += "</script>"

  //htmlMessage += '<p>Replace "' + result.key + '" with "'
  //  + result.value + '" ?<p>'
   
  htmlMessage += '<p>Link "' + result.key + '" to "'
    + result.value + '" ?<p>'
  htmlMessage += '<input id="yesButton" value="Yes" type="button" onclick="yesClick()" />'
  htmlMessage += '<input id="noButton" value="No" type="button" onclick="noClick()" />'
    
  var htmlOutput = HtmlService.createHtmlOutput(htmlMessage)

  ui.showSidebar(htmlOutput)
}
