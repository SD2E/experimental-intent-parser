var gItemMap = null
var gCurrentRange = null

function onOpen() {
  var ui = DocumentApp.getUi()
  var menu = ui.createMenu('Parse Intent')
  
  menu.addItem('Scan Document', 'scanDocument').addToUi()
  menu.addItem('Reset Scan', 'resetScan').addToUi()
  
  resetScan();
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

function showSidebar(result) {
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

