from googleapiclient.discovery import build
import logging
import time

class GoogleSpreadsheetAccessor:

    logger = logging.getLogger('intent_parser_google_doc_accessor')

    _REQUESTS_PER_SEC = 0.5

    def __init__(self, credentials):
        self._sheet_service = build('sheets', 'v4', credentials=credentials, cache_discovery=False)

    def create_new_spreadsheet(self, name):
        """Creates a new spreadsheet.

        Args:
            name - Name of spreadsheet

        Returns:
            A string to represent the id of the created spreadsheet.
            An empty string is returned if no spreadsheet was created.
        """
        spreadsheet_metadata = {
            'properties': {
                'title': name
            }
        }

        response = self._sheet_service.spreadsheets().create(body=spreadsheet_metadata,
                                                             fields='spreadsheetId').execute()
        return response['spreadsheetId']


    def execute_requests(self, requests, spreadsheet_id):
        """Executes a list of request
        Args:
            request: A list of requests
        Returns:
            Response of executing multiple requests in the form of a json object.
        """
        body = {'requests': requests}
        batch_request = self._sheet_service.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id,
                                                                       body=body)
        time.sleep(len(requests) / self._REQUESTS_PER_SEC)
        return batch_request.execute()

    def get_tab_data(self, tab, spreadsheet_id):
        """
        Retrieve data from a spreadsheet tab.
        """
        return self._sheet_service.spreadsheets().values().get(spreadsheetId=spreadsheet_id, range=tab).execute()

    def set_tab_data(self, tab, values, spreadsheet_id):
        """
        Write data to a spreadsheet tab.
        """
        body = {'values': values,
                'range': tab,
                'majorDimension': "ROWS"}

        update_request = self._sheet_service.spreadsheets().values().update(spreadsheetId=spreadsheet_id,
                                                                            range=tab,
                                                                            body=body,
                                                                            valueInputOption='RAW')
        self._execute_request(update_request)
