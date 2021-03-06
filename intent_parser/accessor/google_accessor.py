from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from intent_parser.accessor.google_app_script_accessor import GoogleAppScriptAccessor
from intent_parser.accessor.google_doc_accessor import GoogleDocAccessor
from intent_parser.accessor.google_drive_accessor import GoogleDriveV2Accessor, GoogleDriveV3Accessor
from intent_parser.accessor.google_spreadsheet_accessor import GoogleSpreadsheetAccessor
import os.path
import logging
import pickle

class GoogleAccessor(object):

    logger = logging.getLogger('intent_parser_google_accessor')

    _USER_ACCOUNT = {
        "domain": 'gmail.com',
        "email": 'bbn.intentparser@gmail.com',
        "name": 'bbn intentparser'}

    _CURR_PATH = os.path.dirname(os.path.realpath(__file__))
    _CREDENTIALS_FILE = os.path.join(_CURR_PATH, 'credentials.json')
    _TOKEN_PICKLE_FILE = os.path.join(_CURR_PATH, 'token.pickle')

    # If modifying these scopes, delete the file token.pickle.
    _SCOPES = ['https://www.googleapis.com/auth/documents',
               'https://www.googleapis.com/auth/drive',
               'https://www.googleapis.com/auth/drive.appdata',
               'https://www.googleapis.com/auth/drive.file',
               'https://www.googleapis.com/auth/drive.metadata',
               'https://www.googleapis.com/auth/script.deployments',
               'https://www.googleapis.com/auth/script.projects',
               'https://www.googleapis.com/auth/spreadsheets']

    _CREDENTIALS = None
    _GOOGLE_ACCESSOR = None
    _GOOGLE_APP_SCRIPT_ACCESSOR = None
    _GOOGLE_DOC_ACCESSOR = None
    _GOOGLE_DRIVE_V2_ACCESSOR = None
    _GOOGLE_DRIVE_V3_ACCESSOR = None
    _GOOGLE_SPREADSHEET_ACCESSOR = None

    def __init__(self):
        pass

    def __new__(cls, *args, **kwargs):
        if not cls._GOOGLE_ACCESSOR:
            cls._GOOGLE_ACCESSOR = super(GoogleAccessor, cls).__new__(cls, *args, **kwargs)
            cls._GOOGLE_ACCESSOR._authenticate_credentials()

        return cls._GOOGLE_ACCESSOR

    def _authenticate_credentials(self):
        """
        Authenticate credentials for script
        """
        self._CREDENTIALS = None
        # The file token.pickle stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists(self._TOKEN_PICKLE_FILE):
            with open(self._TOKEN_PICKLE_FILE, 'rb') as token:
                self._CREDENTIALS = pickle.load(token)
        # If there are no (valid) credentials available, let the user log in.
        if not self._CREDENTIALS or not self._CREDENTIALS.valid:
            if self._CREDENTIALS and self._CREDENTIALS.expired and self._CREDENTIALS.refresh_token:
                self._CREDENTIALS.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self._CREDENTIALS_FILE, self._SCOPES)
                self._CREDENTIALS = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open(self._TOKEN_PICKLE_FILE, 'wb') as token:
                pickle.dump(self._CREDENTIALS, token)

    def get_google_app_script_accessor(self):
        return GoogleAppScriptAccessor(self._CREDENTIALS)

    def get_google_doc_accessor(self):
        return GoogleDocAccessor(self._CREDENTIALS)

    def get_google_drive_accessor(self, version=2):
        if version == 3:
            return GoogleDriveV3Accessor(self._CREDENTIALS)

        return GoogleDriveV2Accessor(self._CREDENTIALS)

    def get_google_spreadsheet_accessor(self):
        return GoogleSpreadsheetAccessor(self._CREDENTIALS)

