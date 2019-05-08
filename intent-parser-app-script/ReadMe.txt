This directory contains the Google App script.  Currently, since it is
not yet released on the Google App Store, the app script needs to be
manually installed on a document.  To install the app script on a
Google Document, first select "Script Editor" from the Document's
"Tools" menu.  This should bring up the Script Editor web interface.
Paste the contents of Code.js into the Script Editor window.  The
first line in Code.js specifies the URL of the Intent Parser Server.
Next, save the script in the script editor, and go back to the
original document and reload the web page.  An "Intent Parser" menu
should appear in the document menu bar.

Most of the Intent Parser menu options cause the App Script to
communicate with the Intent Parser Server.  The Intent Parser Server
logs into Google using an existing Google Account.  The document needs
to be shared with that Google account to enable the Intent Parser
Server to access the document.
