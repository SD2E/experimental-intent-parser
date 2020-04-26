from apiclient.http import MediaIoBaseUpload
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import AuthorizedSession, Request
from io import BytesIO
import pickle
import os.path
import time

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets',
          'https://www.googleapis.com/auth/drive',
          'https://www.googleapis.com/auth/drive.appdata',
          'https://www.googleapis.com/auth/drive.file',
          'https://www.googleapis.com/auth/documents',]


REQUESTS_PER_SEC = 0.5

class GoogleAccessor:

    def __init__(self, *, spreadsheet_id: str, credentials):
        self._sheet_service = build('sheets', 'v4',
                                    credentials=credentials)
        self._drive_service = build('drive', 'v2',
                                    credentials=credentials)
        self._docs_service = build('docs', 'v1',
                                   credentials=credentials)
        
        self._authed_session = AuthorizedSession(credentials)
        self._spreadsheet_id = spreadsheet_id
        self._tab_headers = dict()
        self._inverse_tab_headers = dict()
        self.MAPPING_FAILURES = 'Mapping Failures'

        self.type_tabs = {
            'Attribute': ['Attribute'],  
            'Reagent': ['Bead', 'CHEBI', 'Protein',
                        'Media', 'Stain', 'Buffer',
                        'Solution'],
            'Genetic Construct': ['DNA', 'RNA'],
            'Strain': ['Strain'],
            'Protein': ['Protein'],
            'Collections': ['Challenge Problem']
        }

        self._dictionary_headers = ['Common Name',
                                    'Type',
                                    'SynBioHub URI',
                                    'Stub Object?',
                                    'Definition URI',
                                    'Definition URI / CHEBI ID',
                                    'Status']

        self.mapping_failures_headers = [
            'Experiment/Run',
	    'Lab',
            'Item Name',
            'Item ID',
            'Item Type (Strain or Reagent Tab)',
            'Status'
            ]

        # Lab Names
        self.labs = ['BioFAB', 'Ginkgo',
                     'Transcriptic', 'LBNL', 'EmeraldCloud', 'CalTech', 'PennState (Salis)']

    @staticmethod
    def create(*, spreadsheet_id=None, console=False):
        """Ensures that the user is logged in and returns a `GoogleAccessor`.

        Credentials are initially read from the `credentials.json` file, and
        are subsequently stored in the file `token.pickle` that stores the
        user's access and refresh tokens.
        The file `token.pickle` is created automatically when the authorization
        flow completes for the first time.
        """
        creds = None
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', SCOPES)
                if console:
                    creds = flow.run_console()
                else:
                    creds = flow.run_local_server()
            # Save the credentials for the next run
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)

        return GoogleAccessor(spreadsheet_id=spreadsheet_id, credentials=creds)

    def create_new_spreadsheet(self, name, folder_id=None):
        """Creates a new spreadsheet. 
        
        Args:
            name - Name of the new spreadsheet
            folder_id: id of a Google Drive folder to create a new spreadsheet in. 
                       The new spreadsheet will be created in the user's Drive folder if no folder id is given.
                       
        Returns:
            A string to represent the id of the created spreadsheet.
            An empty string is returned if no spreadsheet was created.
        """
        spreadsheet_metadata = {
            'properties': {
                'title': name
                }
            }
            
        spreadsheets = self._sheet_service.spreadsheets()
        create_sheets_request = spreadsheets.create(body=spreadsheet_metadata,
                                                    fields='spreadsheetId').execute()
        
        if 'spreadsheetId' not in create_sheets_request:
            return ''
        sheet_id = create_sheets_request['spreadsheetId']
        if folder_id:
            res = self._drive_service.files().update(fileId=sheet_id, 
                                                     addParents=folder_id, 
                                                     removeParents='root').execute()
        return sheet_id
    
    def delete_file(self, file_id: str):
        """Delete an existing file
          
        Args:
            file_id - the file to delete
        Returns:
            A boolean value. True if the file has been deleted successfully and False, otherwise.
        """
        response = self._drive_service.files().delete(fileId=file_id).execute()
        return not response
   
    def upload_revision(self, document_name, document, folder_id, original_format, title='Untitled', target_format='*/*'):
        """Upload file to a Google Drive folder.
        
        Args:
            document_name: Name of the document
            document: content of the document to upload.
            folder_id: id of the Google Drive folder
            original_format: file format of the document content
            title: document title
            target_format: file format that that the uploaded file will transform into.
            
        Returns:
            A string to represent the uploaded file's id.
        """
        file_metadata = {
            'name': document_name,
            'title': title,
            'parents': [folder_id],
            'mimeType': target_format
        }
        fh = BytesIO(document)
        media = MediaIoBaseUpload(fh, mimetype=original_format, resumable=True) 
        file = self._drive_service.files().insert(body=file_metadata,
                                    media_body=media,
                                    convert=True,
                                    fields='id').execute()
        print ('File ID: ' + file.get('id'))
        return file.get('id')
    
    
    def get_file_with_revision(self, file_id, revision_id, mime_type):
        """Download a Google Doc base on a Doc's id and its revision.
        
        Args:
            fild_id: Google Doc ID
            revision_id: Google Doc revision ID
            mime_type: format to download the Google Doc in. 
            Visit https://developers.google.com/drive/api/v3/ref-export-formats to get a list of file formats that Google can export to
        
        Returns:
            An HTML response of the requested Google Doc revision.
        """
        revisions = self.get_document_revisions(document_id=file_id)
        filter_by_revision =[revision for revision in revisions['items'] if revision['id'] == revision_id]
        
        if len(filter_by_revision) < 1:
            raise ValueError('Revision not found.')
        
        url = filter_by_revision[0]['exportLinks'][mime_type]
        response = self._authed_session.request('GET', url)
        return response
    
    def copy_file(self, file_id: str, new_title: str):
        """Copy an existing file.
        
        Args:
            file_id   - the file to delete
            new_title - title of new copy

        Returns:
            document id of new file
        """
        files = self._drive_service.files()
        request = files.copy(fileId=file_id,
                             body={'name': new_title})
        return self._execute_request(request).get('id')

    def create_dictionary_sheets(self):
        """ Creates the standard tabs on the current spreadsheet.
            The tabs are not populated with any data
        """
        add_sheet_requests = list(map(lambda x: self.add_sheet_request(x),
                                    list(self.type_tabs.keys())))
        # Mapping Failures tab
        add_sheet_requests.append(
            self.add_sheet_request( self.MAPPING_FAILURES )
        )
        self._execute_requests(add_sheet_requests)

        # Add sheet column headers
        headers = self._dictionary_headers
        headers += list(map(lambda x: x + ' UID', self.labs))

        for tab in self.type_tabs.keys():
            self._set_tab_data(tab=tab + '!2:2', values=[headers])

        self._set_tab_data(tab=self.MAPPING_FAILURES + '!2:2',
                           values=[self.mapping_failures_headers])

    def add_sheet_request(self, sheet_title: str):
        """ Creates a Google request to add a tab to the current spreadsheet

        Args:
            sheet_title: name of the new tab
        """

        request = {
            'addSheet': {
                'properties': {
                    'title': sheet_title
                    }
                }
            }
        return request

    def _execute_requests(self, requests: []):
        body = {
            'requests': requests
            }
        batch_request = self._sheet_service.spreadsheets().batchUpdate(
            spreadsheetId=self._spreadsheet_id,
            body=body)
        time.sleep(len(requests) / REQUESTS_PER_SEC)
        return batch_request.execute()

    def _execute_request(self, request):
        time.sleep(1.0 / REQUESTS_PER_SEC)
        return request.execute()

    def set_spreadsheet_id(self, spreadsheet_id: str):
        """
        Select the spreadsheet that is being operated on.
        """
        self._spreadsheet_id = spreadsheet_id
        self._clear_tab_header_cache()

    def _get_tab_data(self, tab):
        """
        Retrieve all the data from a spreadsheet tab.
        """
        values = self._sheet_service.spreadsheets().values()
        get = values.get(spreadsheetId=self._spreadsheet_id, range=tab)
        return self._execute_request(get)

    def _set_tab_data(self, *, tab, values):
        """
        Write data to a spreadsheet tab.
        """
        body = {}
        body['values'] = values
        body['range'] = tab
        body['majorDimension'] = "ROWS"

        values = self._sheet_service.spreadsheets().values()
        update_request = values.update(spreadsheetId=self._spreadsheet_id,
                                       range=tab, body=body,
                                       valueInputOption='RAW')
        self._execute_request(update_request)

    def _cache_tab_headers(self, tab):
        """
        Cache the headers (and locations) in a tab
        returns a map that maps headers to column indexes
        """
        tab_data = self._get_tab_data(tab + "!2:2")

        if 'values' not in tab_data:
            raise Exception('No header values found in tab "' +
                            tab + '"')

        header_values = tab_data['values'][0]
        header_map = {}
        for index in range(len(header_values)):
            header_map[header_values[index]] = index

        inverse_header_map = {}
        for key in header_map.keys():
            inverse_header_map[header_map[key]] = key

        self._tab_headers[tab] = header_map
        self._inverse_tab_headers[tab] = inverse_header_map

    def _clear_tab_header_cache(self):
        self._tab_headers.clear()
        self._inverse_tab_headers.clear()

    def get_tab_headers(self, tab):
        """
        Get the headers (and locations) in a tab
        returns a map that maps headers to column indexes
        """
        if tab not in self._tab_headers.keys():
            self._cache_tab_headers(tab)

        return self._tab_headers[tab]

    def _get_tab_inverse_headers(self, tab):
        """
        Get the headers (and locations) in a tab
        returns a map that maps column indexes to headers
        """
        if tab not in self._inverse_tab_headers.keys():
            self._cache_tab_headers(tab)

        return self._inverse_tab_headers[tab]

    def get_row_data(self, *, tab, row=None):
        """
        Retrieve data in a tab.  Returns a list of maps, where each list
        element maps a header name to the corresponding row value.  If
        no row is specified all rows are returned
        """
        if tab not in self._tab_headers.keys():
            self._cache_tab_headers(tab)

        header_value = self._inverse_tab_headers[tab]

        if row is None:
            value_range = tab + '!3:9999'
        else:
            value_range = tab + '!' + str(row) + ":" + str(row)

        tab_data = self._get_tab_data(value_range)
        row_data = []
        if 'values' not in tab_data:
            return row_data

        values = tab_data['values']
        row_index = 3
        for row_values in values:
            this_row_data = {}
            for i in range(len(header_value)):
                if i >= len(row_values):
                    break

                header = header_value[i]
                value = row_values[i]

                if value is not None:
                    this_row_data[header] = value

            if len(this_row_data) > 0:
                this_row_data['row'] = row_index
                this_row_data['tab'] = tab
                row_data.append(this_row_data)

            row_index += 1

        return row_data

    def set_row_data(self, entry):
        """
        Write a row to the spreadsheet.  The entry is a map that maps
        column headers to the corresponding values, with an additional
        set of keys that specify the tab and the spreadsheet row
        """
        tab = entry['tab']
        row = entry['row']
        row_data = self.gen_row_data(entry=entry, tab=tab)
        row_range = '{}!{}:{}'.format(tab, row, row)
        self._set_tab_data(tab=row_range, values=[row_data])

    def set_row_value(self, *, entry, column):
        """
        Write a single cell value, given an entry, and the column name
        of the entry to be written
        """
        return self.set_cell_value(
            tab=entry['tab'],
            row=entry['row'],
            column=column,
            value=entry[column]
        )

    def set_cell_value(self, *, tab, row, column, value):
        """
        Write a single cell value, given an tab, row, column name, and value.
        """
        headers = self.get_tab_headers(tab)
        if column not in headers:
            raise Exception('No column "{}" on tab "{}"'.
                            format(column, tab))

        col = chr(ord('A') + headers[column])
        row_range = tab + '!' + col + str(row)
        self._set_tab_data(tab=row_range, values=[[value]])

    def gen_row_data(self, *, entry, tab):
        """
        Generate a list of spreadsheet row value given a map the maps
        column headers to values
        """
        headers = self._get_tab_inverse_headers(tab)
        row_data = [''] * (max(headers.keys()) + 1)

        for index in headers.keys():
            header = headers[index]
            if header not in entry:
                continue
            row_data[index] = entry[header]

        return row_data

    def get_document(self, *, document_id):
        return self._docs_service.documents().get(documentId=document_id).execute()

    def create_document(self, *, title):
        body = { 'title': title }
        return self._docs_service.documents().create(body=body).execute()

    def get_document_revisions(self, *, document_id):
        """
        Returns the list of revisions for the given document_id
        """
        return self._drive_service.revisions().list(fileId=document_id).execute()

    def get_head_revision(self, document_id):
        revisions = self.get_document_revisions(document_id=document_id)
        revision_ids = [int(revision['id']) for revision in revisions['items']]
        if len(revision_ids) < 1:
            raise ValueError('Revision not found.')
        
        return str(max(revision_ids))
    
    def get_document_metadata(self, *, document_id):
        return self._drive_service.files().get(fileId=document_id).execute()

    def get_document_parents(self, *, document_id):
        return self._drive_service.parents().list(fileId=document_id).execute()
