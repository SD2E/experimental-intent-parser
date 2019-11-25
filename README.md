# Intent Parser

This repository creates a tool to help in the authorship of experimental requests.
This tool is exposed to users via a Google Docs add-on.
The add-on allows users to scan a document for terms in the SD2 dictionary and link the term back to SynBioHub.
It can also parse the document to generated structured request json files (see the [cp-requests repository](https://gitlab.sd2e.org/sd2program/cp-request)).
The google application script (GAS) add-on communications with a Python server that performs most of the processing work.

