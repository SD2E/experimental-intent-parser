Overview

  This directory contains the source code for the Intent Parser
  server.  The Intent Parser server receives requests from the Intent
  Parser App Script, which run on a Google Docs document.

Dependencies

  The Intent Parser Server requires Python version 3.

  The Intent Parser Server requires the PySBOL library to access
  SynBioHub, and some Google libraries to access Google Documents.
  The PySBOL library is available in binary form at the following
  repository:

    https://github.com/SynBioDex/pySBOL

  Alternatively, to build pySBOL from source, clone the following
  repository:

    https://github.com/SynBioDex/libSBOL


  The Google python libraries can be installed with the following
  command:

    pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib

Running

  The Intent Parser server accepts the following command line arguments:

    -h --help            - show this message
    -p --pasword         - SynBioHub password
    -u --username        - SynBioHub username
    -c --collection      - collection url
    -i --spreadsheet-id  - dictionary spreadsheet id
    -s --spoofing-prefix - SBH spoofing prefix

  The collection url specifies the collection to which new items are
  added.  The spreadsheet id identifies the dictionary spreadsheet,
  and the spoofing prefix is used for testing on the SynBioHub staging
  instance.

  Running with -h will show the default values for -c, -i, and -s.
  You must at a minimum specify the -u and -p options to log into
  SynBioHub.  The first time you run, python should open a web browser
  to log into Google.  This will allow the Intent Parser Server to
  manipulate the Dictionary Spreadsheet, and to analyze documents.
  After authentication a file called "token.pickle" will be created.
  The Google account that you log into must have permission to edit
  the Dictionary spreadsheet, as well as any Google documents the
  Intent Parser will be run on.

