# Intent Parser

This repository creates a tool to help in the authorship of experimental requests.
This tool is exposed to users via a Google Docs add-on.
The add-on allows users to scan a document for terms in the SD2 dictionary and link the term back to SynBioHub.
It can also parse the document to generated structured request json files (see the [cp-requests repository](https://gitlab.sd2e.org/sd2program/cp-request)).
The google application script (GAS) add-on communications with a Python server that performs most of the processing work.

## Troubleshooting:

429 Errors: 

- Google add-on script Resource quota has been reached. Calling create() methods to create a new Google App Script Project will hit miximum quota of 50. Online says users are given 60 but experimenting on intent parser will limit to 50. Resolve by waiting for 24 hours for quota to reset to 0.  

```
b'{\n  "error": {\n    "code": 429,\n    "message": "Resource has been exhausted (e.g. check quota).",\n    "status": "RESOURCE_EXHAUSTED"\n  }\n}\n'
```

- Google add-on script metric quota has been reached. This will occur when calling update methods to the API. Resolve by waiting every 300 seconds

```
b'{\n  "error": {\n    "code": 429,\n    "message": "Quota exceeded for quota metric \'Management requests\' and limit \'Management requests per minute per user\' of service \'script.googleapis.com\' for consumer \'project_number:15437614630\'.",\n    "status": "RESOURCE_EXHAUSTED",\n    "details": [\n      {\n        "@type": "type.googleapis.com/google.rpc.Help",\n        "links": [\n          {\n            "description": "Google developer console API key",\n            "url": "https://console.developers.google.com/project/15437614630/apiui/credential"\n          }\n        ]\n      }\n    ]\n  }\n}\n'
```