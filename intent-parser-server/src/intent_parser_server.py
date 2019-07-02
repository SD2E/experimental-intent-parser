import socket
import threading
import json
from socket_manager import SocketManager
from google_accessor import GoogleAccessor
from sbh_accessor import SBHAccessor
import http_message;
import traceback
import sbol
import sys
import getopt
import re
import time
import os
import signal
from datetime import datetime
from operator import itemgetter

from spellchecker import SpellChecker

from difflib import Match

class ConnectionException(Exception):
    def __init__(self, code, message, content=""):
        super(ConnectionException, self).__init__(message);
        self.code = code
        self.message = message
        self.content = content


class IntentParserServer:

    dict_path = 'dictionaries'

    lab_ids_list = sorted(['BioFAB UID',
                            'Ginkgo UID',
                            'Transcriptic UID',
                            'LBNL UID',
                            'EmeraldCloud UID'])

    item_types = {
            'component': {
                'Bead'     : 'http://purl.obolibrary.org/obo/NCIT_C70671',
                'CHEBI'    : 'http://identifiers.org/chebi/CHEBI:24431',
                'DNA'      : 'http://www.biopax.org/release/biopax-level3.owl#DnaRegion',
                'Protein'  : 'http://www.biopax.org/release/biopax-level3.owl#Protein',
                'RNA'      : 'http://www.biopax.org/release/biopax-level3.owl#RnaRegion'
            },
            'module': {
                'Strain'   : 'http://purl.obolibrary.org/obo/NCIT_C14419',
                'Media'    : 'http://purl.obolibrary.org/obo/NCIT_C85504',
                'Stain'    : 'http://purl.obolibrary.org/obo/NCIT_C841',
                'Buffer'   : 'http://purl.obolibrary.org/obo/NCIT_C70815',
                'Solution' : 'http://purl.obolibrary.org/obo/NCIT_C70830'
            },
            'collection': {
                'Challenge Problem' : '',
                'Collection' : ''
            },
            'external': {
                'Attribute' : ''
            }
        }

    # Define the percentage of length of the search term that must
    # be matched in order to have a valid partial match
    partial_match_thresh = 0.75

    # Terms below a certain size should be force to have an exact match
    partial_match_min_size = 3

    # How many results we allow
    sparql_limit = 5

    def __init__(self, bind_port=8080, bind_ip="0.0.0.0",
                 sbh_collection_uri=None,
                 sbh_spoofing_prefix=None,
                 spreadsheet_id=None,
                 sbh_username=None, sbh_password=None,
                 sbh_link_hosts=['hub-staging.sd2e.org',
                                 'hub.sd2e.org'],
                 init_server=True,
                 init_sbh=True):

        self.sbh = None
        self.server = None
        self.shutdownThread = False
        self.event = threading.Event()

        self.my_path = os.path.dirname(os.path.realpath(__file__))

        f = open(self.my_path + '/add.html', 'r')
        self.add_html = f.read()
        f.close()

        f = open(self.my_path + '/analyze_sidebar.html', 'r')
        self.analyze_html = f.read()
        f.close()

        f = open(self.my_path + '/findSimilar.sparql', 'r')
        self.sparql_similar_query = f.read()
        f.close()

        f = open(self.my_path + '/findSimilarCount.sparql', 'r')
        self.sparql_similar_count = f.read()
        f.close()

        self.sparql_similar_count_cache = {}

        if init_sbh:
            self.initialize_sbh(sbh_collection_uri=sbh_collection_uri,
                 sbh_spoofing_prefix=sbh_spoofing_prefix,
                 spreadsheet_id=spreadsheet_id,
                 sbh_username=sbh_username, sbh_password=sbh_password,
                 sbh_link_hosts=sbh_link_hosts)

        if init_server:
            self.initialize_server(bind_port=bind_port, bind_ip=bind_ip)

        self.spellCheckers = {}

        if not os.path.exists(self.dict_path):
            os.makedirs(self.dict_path)

    def initialize_sbh(self, *,
                 sbh_collection_uri,
                 spreadsheet_id,
                 sbh_spoofing_prefix=None,
                 sbh_username=None, sbh_password=None,
                 sbh_link_hosts=['hub-staging.sd2e.org',
                                 'hub.sd2e.org']):
        """
        Initialize the connection to SynbioHub.
        """

        if sbh_collection_uri[:8] == 'https://':
            sbh_url_protocol = 'https://'
            sbh_collection_path = sbh_collection_uri[8:]

        elif sbh_collection_uri[:7] == 'http://':
            sbh_url_protocol = 'http://'
            sbh_collection_path = sbh_collection_uri[7:]

        else:
            raise Exception('Invalid collection url: ' + sbh_collection_uri)

        sbh_collection_path_parts = sbh_collection_path.split('/')
        if len(sbh_collection_path_parts) != 6:
            raise Exception('Invalid collection url: ' + sbh_collection_uri)

        sbh_collection = sbh_collection_path_parts[3]
        sbh_collection_user = sbh_collection_path_parts[2]
        sbh_collection_version = sbh_collection_path_parts[5]
        sbh_url = sbh_url_protocol + sbh_collection_path_parts[0]

        if sbh_collection_path_parts[4] != (sbh_collection + '_collection'):
            raise Exception('Invalid collection url: ' + sbh_collection_uri)

        self.sbh = None
        if sbh_url is not None:
            # log into Syn Bio Hub
            if sbh_username is None:
                print('SynBioHub username was not specified')
                usage()
                sys.exit(2)

            if sbh_password is None:
                print('SynBioHub password was not specified')
                usage()
                sys.exit(2)

            self.sbh = SBHAccessor(sbh_url=sbh_url)
            self.sbh_collection = sbh_collection
            self.sbh_spoofing_prefix = sbh_spoofing_prefix
            self.sbh_url = sbh_url
            self.sbh_link_hosts = sbh_link_hosts

            if sbh_spoofing_prefix is not None:
                self.sbh.spoof(sbh_spoofing_prefix)
                self.sbh_collection_uri = sbh_spoofing_prefix \
                    + '/user/' + sbh_collection_user \
                    + '/' + sbh_collection + '/' \
                    + sbh_collection + '_collection/' \
                    + sbh_collection_version
            else:
                self.sbh_collection_uri = sbh_url + '/'
                self.sbh_collection_uri = sbh_url \
                    + '/user/' + sbh_collection_user \
                    + '/' + sbh_collection + '/' \
                    + sbh_collection + '_collection/' \
                    + sbh_collection_version

            self.sbh_uri_prefix = sbh_url \
                + '/user/' + sbh_collection_user \
                + '/' + sbh_collection + '/'

        self.google_accessor = GoogleAccessor.create()
        self.spreadsheet_id = spreadsheet_id
        self.google_accessor.set_spreadsheet_id(self.spreadsheet_id)
        self.spreadsheet_tabs = self.google_accessor.type_tabs.keys()

        self.client_state_map = {}
        self.client_state_lock = threading.Lock()
        self.item_map_lock = threading.Lock()
        self.item_map_lock.acquire()
        self.item_map = self.generate_item_map(use_cache=True)
        self.item_map_lock.release()

        # Inverse map of typeTabs
        self.type2tab = {}
        for tab_name in self.google_accessor.type_tabs.keys():
            for type_name in self.google_accessor.type_tabs[tab_name]:
                self.type2tab[type_name] = tab_name

        if self.sbh is not None:
            self.sbh.login(sbh_username, sbh_password)
            print('Logged into {}'.format(sbh_url))

        self.housekeeping_thread = \
            threading.Thread(target=self.housekeeping)
        self.housekeeping_thread.start()

    def initialize_server(self, *, bind_port=8080, bind_ip="0.0.0.0"):
        """
        Initialize the server.
        """

        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind((bind_ip, bind_port))

        self.server.listen(5)
        print('listening on {}:{}'.format(bind_ip, bind_port))

    def serverRunLoop(self, *, background=False):
        if background:
            run_thread = threading.Thread(target=self.serverRunLoop)
            print('Start background thread')
            run_thread.start()
            return

        print('Start Listener')

        while True:
            try:
                if self.shutdownThread:
                    return

                client_sock, __ = self.server.accept()
            except ConnectionAbortedError:
                # Shutting down
                return
            except OSError:
                # Shutting down
                return
            except InterruptedError:
                # Received when server is shutting down
                return
            except Exception as e:
                raise e

            client_handler = threading.Thread(
                target=self.handle_client_connection,
                args=(client_sock,)  # without comma you'd get a... TypeError: handle_client_connection() argument after * must be a sequence, not _socketobject
            )
            client_handler.start()

    def handle_client_connection(self, client_socket):
        print('Connection')
        sm = SocketManager(client_socket)

        try:
            while True:
                httpMessage = http_message.HttpMessage(sm)

                if httpMessage.get_state() == http_message.State.ERROR:
                    client_socket.close()
                    return

                method = httpMessage.get_method()

                try:
                    if method == 'POST':
                        self.handlePOST(httpMessage, sm)
                    elif method == 'GET':
                        self.handleGET(httpMessage, sm)
                    else:
                        self.send_response(501, 'Not Implemented', 'Unrecognized request method\n',
                                           sm)

                except ConnectionException as ex:
                    self.send_response(ex.code, ex.message, ex.content, sm)

                except Exception as ex:
                    print(''.join(traceback.format_exception(etype=type(ex), value=ex, tb=ex.__traceback__)))
                    self.send_response(504, 'Internal Server Error', 'Internal Server Error\n', sm)

        except Exception as e:
            print('Exception: {}'.format(e))

        client_socket.close()

    def send_response(self, code, message, content, sm, content_type='text/html'):
            response = http_message.HttpMessage()
            response.set_response_code(code, message)
            response.set_header('content-type', content_type)
            response.set_body(content.encode('utf-8'))
            response.send(sm)

    def handlePOST(self, httpMessage, sm):
        resource = httpMessage.get_resource()

        if resource == '/analyzeDocument':
            self.process_analyze_document(httpMessage, sm)
        elif resource == '/message':
            self.process_message(httpMessage, sm)
        elif resource == '/buttonClick':
            self.process_button_click(httpMessage, sm)
        elif resource == '/addToSynBioHub':
            self.process_add_to_syn_bio_hub(httpMessage, sm)
        elif resource == '/addBySpelling':
            self.process_add_by_spelling(httpMessage, sm)
        elif resource == '/searchSynBioHub':
            self.process_search_syn_bio_hub(httpMessage, sm)
        elif resource == '/submitForm':
            self.process_submit_form(httpMessage, sm)
        else:
            self.send_response(404, 'Not Found', 'Resource Not Found\n', sm)

    def get_json_body(self, httpMessage):
        body = httpMessage.get_body()
        if body == None or len(body) == 0:
            errorMessage = 'No POST data\n'
            raise ConnectionException(400, 'Bad Request', errorMessage)

        bodyStr = body.decode('utf-8')

        try:
            return json.loads(bodyStr)
        except json.decoder.JSONDecodeError as e:
            errorMessage = 'Failed to decode JSON data: {}\n'.format(e);
            raise ConnectionException(400, 'Bad Request', errorMessage)

    def process_button_click(self, httpMessage, sm):
        (json_body, client_state) = self.get_client_state(httpMessage)

        if 'data' not in json_body:
            errorMessage = 'Missing data'
            raise ConnectionException(400, 'Bad Request', errorMessage)
        data = json_body['data']

        if 'buttonId' not in data:
            errorMessage = 'data missing buttonId'
            raise ConnectionException(400, 'Bad Request', errorMessage)
        if type(data['buttonId']) is dict:
            buttonDat = data['buttonId']
            buttonId = buttonDat['buttonId']
        else:
            buttonId = data['buttonId']

        method = getattr( self, buttonId )

        try:
            actionList = method(json_body, client_state)
            actions = {'actions': actionList}
            self.send_response(200, 'OK', json.dumps(actions), sm,
                               'application/json')
        except Exception as e:
            raise e
        finally:
            self.release_connection(client_state)

    def process_generate_report(self, httpMessage, sm):
        resource = httpMessage.get_resource()
        document_id = resource.split('?')[1]
        #client_state = {}

        try:
            doc = self.google_accessor.get_document(
                document_id=document_id
                )
        except Exception as ex:
            print(''.join(traceback.format_exception(etype=type(ex), value=ex, tb=ex.__traceback__)))
            raise ConnectionException('404', 'Not Found',
                                      'Failed to access document ' +
                                      document_id)

        text_runs = self.get_element_type(doc, 'textRun')
        text_runs = list(filter(lambda x: 'textStyle' in x,
                                text_runs))
        text_runs = list(filter(lambda x: 'link' in x['textStyle'],
                                text_runs))
        links_info = list(map(lambda x: (x['content'],
                                         x['textStyle']['link']),
                              text_runs))

        mapped_names = []
        term_map = {}
        for link_info in links_info:
            try:
                term = link_info[0].strip()
                url = link_info[1]['url']
                if len(term) == 0:
                    continue

                if term in term_map:
                    if term_map[term] == url:
                        continue

                url_host = url.split('/')[2]
                if url_host not in self.sbh_link_hosts:
                    continue

                term_map[term] = url
                mapped_name = {}
                mapped_name['label'] = term
                mapped_name['sbh_url'] = url
                mapped_names.append(mapped_name)
            except:
                continue

        client_state = {}
        client_state['doc'] = doc
        self.analyze_document(client_state, doc, 0)

        report = {}
        report['challenge_problem_id'] = 'undefined'
        report['experiment_reference_url'] = \
            'https://docs.google.com/document/d/' + document_id
        report['labs'] = []

        report['mapped_names'] = mapped_names

        self.send_response(200, 'OK', json.dumps(report), sm,
                           'application/json')

    def process_message(self, httpMessage, sm):
        json_body = self.get_json_body(httpMessage)
        if 'message' in json_body:
            print(json_body['message'])
        self.send_response(200, 'OK', '{}', sm,
                           'application/json')


    def get_client_state(self, httpMessage):
        json_body = self.get_json_body(httpMessage)

        if 'documentId' not in json_body:
            raise ConnectionException('400', 'Bad Request',
                                      'Missing documentId')
        document_id = json_body['documentId']

        try:
            client_state = self.get_connection(document_id)
        except:
            client_state = None

        return (json_body, client_state)

    def process_analyze_document(self, httpMessage, sm):
        start = time.time()
        json_body = self.get_json_body(httpMessage)

        if 'documentId' not in json_body:
            raise ConnectionException('400', 'Bad Request',
                                      'Missing documentId')
        document_id = json_body['documentId']

        try:
            doc = self.google_accessor.get_document(
                document_id=document_id
                )
        except Exception as ex:
            print(''.join(traceback.format_exception(etype=type(ex), value=ex, tb=ex.__traceback__)))
            raise ConnectionException('404', 'Not Found',
                                      'Failed to access document ' +
                                      document_id)

        client_state = self.new_connection(document_id)
        client_state['doc'] = doc

        if 'data' in json_body:
            body = doc.get('body');
            doc_content = body.get('content')
            paragraphs = self.get_paragraphs(doc_content)

            data = json_body['data']
            paragraph_index = data['paragraphIndex']
            offset = data['offset']
            paragraph = paragraphs[ paragraph_index ]
            first_element = paragraph['elements'][0]
            paragraph_offset = first_element['startIndex']
            start_offset = paragraph_offset + offset
        else:
            start_offset = 0

        try:
            actionList = self.analyze_document(client_state, doc, start_offset)
            actions = {'actions': actionList}
            self.send_response(200, 'OK', json.dumps(actions), sm,
                               'application/json')
            end = time.time()
            print('Analyzed entire document in %0.2fms' %((end - start) * 1000))
        except Exception as e:
            raise e

        finally:
            self.release_connection(client_state)

    def add_link(self, search_result, new_link=None):
        paragraph_index = search_result['paragraph_index']
        offset = search_result['offset']
        end_offset = search_result['end_offset']
        if new_link is None:
            link = search_result['uri']
        else:
            link = new_link
        search_result['link'] = link

        action = self.link_text(paragraph_index, offset,
                                end_offset, link)

        return [action]


    def report_search_results(self, client_state):
        while True:
            search_results = client_state['search_results']
            search_result_index = client_state['search_result_index']
            if search_result_index >= len(search_results):
                return []

            client_state['search_result_index'] += 1

            search_result = search_results[ search_result_index ]
            paragraph_index = search_result['paragraph_index']
            offset = search_result['offset']
            term = search_result['term']
            uri = search_result['uri']
            link = search_result['link']
            content_term = search_result['text']
            end_offset = search_result['end_offset']

            actions = []

            self.item_map_lock.acquire()
            item_map = self.item_map
            self.item_map_lock.release()

            if link is not None and link == item_map[term]:
                continue

            highlightTextAction = self.highlight_text(paragraph_index, offset,
                                                      end_offset)
            actions.append(highlightTextAction)

            html  = ''
            html += '<center>'
            html += 'Link ' + content_term + ' to ';
            html += '<a href=' + uri + ' target=_blank>'
            html += term + '</a> ?'
            html += '</center>'


            buttons = [('Yes', 'process_analyze_yes'),
                       ('No', 'process_analyze_no'),
                       ('Link All', 'process_link_all'),
                       ('No to All', 'process_no_to_all')]

            buttonHTML = ''
            buttonScript = ''
            for button in buttons:
                buttonHTML += '<input id=' + button[1] + 'Button value="'
                buttonHTML += button[0] + '" type="button" onclick="'
                buttonHTML += button[1] + 'Click()" />\n'

                buttonScript += 'function ' + button[1] + 'Click() {\n'
                buttonScript += '  google.script.run.withSuccessHandler'
                buttonScript += '(onSuccess).buttonClick(\''
                buttonScript += button[1]  + '\')\n'
                buttonScript += '}\n\n'

            buttonHTML += '<input id=EnterLinkButton value="Manually Enter Link" type="button" onclick="EnterLinkClick()" />'
            # Script for the EnterLinkButton is already in the HTML

            html = self.analyze_html

            # Update parameters in html
            html = html.replace('${SELECTEDTERM}', term)
            html = html.replace('${SELECTEDURI}', uri)
            html = html.replace('${CONTENT_TERM}', content_term)
            html = html.replace('${TERM_URI}', uri)
            html = html.replace('${DOCUMENTID}', client_state['document_id'])
            html = html.replace('${BUTTONS}', buttonHTML)
            html = html.replace('${BUTTONS_SCRIPT}', buttonScript)

            dialogAction = self.sidebar_dialog(html)

            actions.append(dialogAction)

            return actions

    def get_paragraphs(self, element):
        return self.get_element_type(element, 'paragraph')

    def get_element_type(self, element, element_type):
        elements = []
        if type(element) is dict:
            for key in element:
                if key == element_type:
                    elements.append(element[key])

                elements += self.get_element_type(element[key],
                                                  element_type)

        elif type(element) is list:
            for entry in element:
                elements += self.get_element_type(entry,
                                                  element_type)

        return elements


    def fetch_spreadsheet_data(self):
        tab_data = {}
        for tab in self.spreadsheet_tabs:
            tab_data[tab] = self.google_accessor.get_row_data(tab=tab)
            print('Fetched data from tab ' + tab)

        return tab_data


    def analyze_document(self, client_state, doc, start_offset):
        body = doc.get('body');
        doc_content = body.get('content')
        paragraphs = self.get_paragraphs(doc_content)

        search_results = []

        self.item_map_lock.acquire()
        item_map = self.item_map
        self.item_map_lock.release()

        for term in item_map.keys():
            results = self.find_text(term, start_offset, paragraphs)
            for result in results:
                search_results.append(
                                { 'paragraph_index' : result[0],
                                  'offset'          : result[1],
                                  'end_offset'      : result[2],
                                  'term'            : term,
                                  'uri'             : item_map[term],
                                  'link'            : result[3],
                                  'text'            : result[4]})

        if len(search_results) == 0:
            return []

        # Remove any matches that overlap, taking the longest match
        search_results = self.cull_overlapping(search_results);

        search_results = sorted(search_results,
                                key=itemgetter('paragraph_index',
                                               'offset')
                                )

        client_state['search_results'] = search_results
        client_state['search_result_index'] = 0

        return self.report_search_results(client_state)

    def cull_overlapping(self, search_results):
        """
        Find any results that overlap and take the one with the largest term.
        """
        new_results = []
        ignore_idx = set()
        for idx in range(0, len(search_results)):
            if idx in ignore_idx:
                continue;

            overlaps, max_idx, overlap_idx = self.find_overlaps(idx, search_results, ignore_idx)
            if len(overlaps) > 1:
                new_results.append(search_results[max_idx])
                ignore_idx = ignore_idx.union(overlap_idx)
            else:
                new_results.append(search_results[idx])
        return new_results

    def find_overlaps(self, start_idx, search_results, ignore_idx = set()):
        """
        Given a start index, find any entries in the results that overlap with the result at the start index
        """
        query = search_results[start_idx]
        overlaps = [query]
        overlap_idx = [start_idx]
        max_overlap_idx = start_idx
        max_overlap_len = query['end_offset'] - query['offset']
        for idx in range(start_idx + 1, len(search_results)):

            if idx in ignore_idx:
                continue;
            comp = search_results[idx]

            if not comp['paragraph_index'] == query['paragraph_index']:
                continue
            overlap = max(0, min(comp['end_offset'], query['end_offset']) - max(comp['offset'], query['offset'])) > 0
            if overlap:
                overlaps.append(comp)
                overlap_idx.append(idx)
                if comp['end_offset'] - comp['offset'] > max_overlap_len:
                    max_overlap_idx = idx
                    max_overlap_len = comp['end_offset'] - comp['offset']

        return overlaps, max_overlap_idx, overlap_idx

    def process_analyze_yes(self, json_body, client_state):
        """
        Handle "Yes" button as part of analyze document.
        """
        search_results = client_state['search_results']
        search_result_index = client_state['search_result_index'] - 1
        search_result = search_results[search_result_index]

        if type(json_body['data']['buttonId']) is dict:
            new_link = json_body['data']['buttonId']['link']
        else:
            new_link = None

        actions = self.add_link(search_result, new_link);
        actions += self.report_search_results(client_state)
        return actions

    def process_analyze_no(self, json_body, client_state):
        """
        Handle "No" button as part of analyze document.
        """
        json_body # Remove unused warning
        return self.report_search_results(client_state)

    def process_link_all(self, json_body, client_state):
        """
        Handle "Link all" button as part of analyze document.
        """
        search_results = client_state['search_results']
        search_result_index = client_state['search_result_index'] - 1
        search_result = search_results[search_result_index]
        term = search_result['term']
        term_search_results = list(filter(lambda x : x['term'] == term,
                                          search_results))

        if type(json_body['data']['buttonId']) is dict:
            new_link = json_body['data']['buttonId']['link']
        else:
            new_link = None

        actions = []

        for term_result in term_search_results:
            actions += self.add_link(term_result, new_link);

        actions += self.report_search_results(client_state)

        return actions

    def process_no_to_all(self, json_body, client_state):
        """
        Handle "No to all" button as part of analyze document.
        """
        json_body # Remove unused warning
        curr_idx = client_state['search_result_index'] - 1
        next_idx = curr_idx + 1
        search_results = client_state['search_results']
        while next_idx < len(search_results) and search_results[curr_idx]['term'] == search_results[next_idx]['term']:
            next_idx = next_idx + 1
        # Are we at the end? Then just exit
        if next_idx >= len(search_results):
            return []

        term_to_ignore = search_results[curr_idx]['term']
        # Generate results without term to ignore
        new_search_results = [r for r in search_results if not r['term'] == term_to_ignore ]

        # Find out what term to point to
        new_idx = new_search_results.index(search_results[next_idx])
        # Update client state
        client_state['search_results'] = new_search_results
        client_state['search_result_index'] = new_idx

        return self.report_search_results(client_state)


    def highlight_text(self, paragraph_index, offset, end_offset):
        highlight_text = {}
        highlight_text['action'] = 'highlightText'
        highlight_text['paragraph_index'] = paragraph_index
        highlight_text['offset'] = offset
        highlight_text['end_offset'] = end_offset

        return highlight_text

    def link_text(self, paragraph_index, offset, end_offset, url):
        link_text = {}
        link_text['action'] = 'linkText'
        link_text['paragraph_index'] = paragraph_index
        link_text['offset'] = offset
        link_text['end_offset'] = end_offset
        link_text['url'] = url

        return link_text

    def simple_sidebar_dialog(self, message, buttons, specialButtons=[]):
        htmlMessage  = '<script>\n\n'
        htmlMessage += 'function onSuccess() { \n\
                         google.script.host.close()\n\
                      }\n\n'
        for button in buttons:
            # Regular buttons, generate script automatically
            if button[2] == 0:
                htmlMessage += 'function ' + button[1] + 'Click() {\n'
                htmlMessage += '  google.script.run.withSuccessHandler'
                htmlMessage += '(onSuccess).buttonClick(\''
                htmlMessage += button[1]  + '\')\n'
                htmlMessage += '}\n\n'
            elif button[2] == 1: # Special buttons, define own script
                htmlMessage += button[1]
        htmlMessage += '</script>\n\n'

        htmlMessage += '<p>' + message + '<p>\n'
        htmlMessage += '<center>'
        for button in buttons:
            if button[2] == 0:
                htmlMessage += '<input id=' + button[1] + 'Button value="'
                htmlMessage += button[0] + '" type="button" onclick="'
                htmlMessage += button[1] + 'Click()" />\n'
            elif button[2] == 1: # Special buttons, define own script
                htmlMessage += '<input id=' + button[3] + 'Button value="'
                htmlMessage += button[0] + '" type="button" onclick="'
                htmlMessage += button[3] + 'Click()" />\n'
        htmlMessage += '</center>'

        action = {}
        action['action'] = 'showSidebar'
        action['html'] = htmlMessage

        return action

    def simple_modal_dialog(self, message, buttons, title, width, height):
        htmlMessage = '<script>\n\n'
        htmlMessage += 'function onSuccess() { \n\
                         google.script.host.close()\n\
                      }\n\n'
        for button in buttons:
            htmlMessage += 'function ' + button[1] + 'Click() {\n'
            htmlMessage += '  google.script.run.withSuccessHandler'
            htmlMessage += '(onSuccess).buttonClick(\''
            htmlMessage += button[1]  + '\')\n'
            htmlMessage += '}\n\n'
        htmlMessage += '</script>\n\n'

        htmlMessage += '<p>' + message + '<p>\n'
        htmlMessage += '<center>'
        for button in buttons:
            htmlMessage += '<input id=' + button[1] + 'Button value="'
            htmlMessage += button[0] + '" type="button" onclick="'
            htmlMessage += button[1] + 'Click()" />\n'
        htmlMessage += '</center>'

        return self.modal_dialog(htmlMessage, title, width, height)

    def modal_dialog(self, html, title, width, height):
        action = {}
        action['action'] = 'showModalDialog'
        action['html'] = html
        action['title'] = title
        action['width'] = width
        action['height'] = height

        return action

    def sidebar_dialog(self, htmlMessage):
        action = {}
        action['action'] = 'showSidebar'
        action['html'] = htmlMessage

        return action

    def get_paragraph_text(self, paragraph):
        elements = paragraph['elements']
        paragraph_text = '';

        for element_index in range( len(elements) ):
            element = elements[ element_index ]

            if 'textRun' not in element:
                continue
            text_run = element['textRun']

            #end_index = element['endIndex']
            #start_index = element['startIndex']

            paragraph_text += text_run['content']

        return paragraph_text

    def find_exact_text(self, text, starting_pos, paragraphs):
        """
        Search through the whole document, beginning at starting_pos and return the first exact match to text.
        """
        elements = []

        for paragraph_index in range( len(paragraphs )):
            paragraph = paragraphs[ paragraph_index ]
            elements = paragraph['elements']

            for element_index in range( len(elements) ):
                element = elements[ element_index ]

                if 'textRun' not in element:
                    continue
                text_run = element['textRun']

                end_index = element['endIndex']
                if end_index < starting_pos:
                    continue

                start_index = element['startIndex']
                if start_index < starting_pos:
                    find_start = starting_pos - start_index
                else:
                    find_start = 0

                content = text_run['content']
                offset = content.lower().find(text.lower(), find_start)

                # Check for whitespace before found text
                if offset > 0 and content[offset-1].isalpha():
                    continue

                # Check for whitespace after found text
                next_offset = offset + len(text)
                if next_offset < len(content) and content[next_offset].isalpha():
                    continue

                if offset < 0:
                    continue

                content_text = content[offset:(offset+len(text))]

                first_index = elements[0]['startIndex']
                offset += start_index - first_index

                link = None

                if 'textStyle' in text_run:
                    text_style = text_run['textStyle']
                    if 'link' in text_style:
                        link = text_style['link']
                        if 'url' in link:
                            link = link['url']

                pos = first_index + offset
                return (paragraph_index, offset, pos, link,
                        content_text)

        return None

    def find_common_substrings(self, content, dict_term):
        """
        Scan dict_term finding any common substrings from dict_term.  For each possible common substring, only the first one is found.
        """
        results = []
        len_content = len(content)
        len_term = len(dict_term)
        i = 0
        while i < len_content:
            match_start = -1
            matched_chars = 0
            # Ignore white space
            if content[i].isspace():
                i += 1
                continue;
            match = None
            for j in range(len_term):
                char_match = (i + j < len_content and content[i + matched_chars] == dict_term[j])
                if char_match and match_start == -1:
                    match_start = j
                elif match_start > -1 and not char_match:
                    match = Match(i, match_start, j - match_start)
                    break
                if char_match:
                    matched_chars += 1
            # Check for match at the end
            if match is None and match_start > -1:
                match = Match(i, match_start, len_term - match_start)
            # Process content match
            if not match is None:
                # Ignore matches if they aren't big enough
                # No partial matches for small terms
                if len_term <= self.partial_match_min_size:
                    if match.size >= len_term:
                        results.append(match)
                # If the term is larger, we can have content partial match
                elif match.size >= int(len_term * self.partial_match_thresh):
                    results.append(match)
                i += match.size
            else:
                i += 1

        return results

    def find_text(self, text, abs_start_offset, paragraphs):
        """
        Search through the whole document and return a collection of matches, including partial, to the search term.
        """
        results = []
        for paragraph_index in range( len(paragraphs )):
            paragraph = paragraphs[ paragraph_index ]
            elements = paragraph['elements']

            for element_index in range( len(elements) ):
                element = elements[ element_index ]

                if 'textRun' not in element:
                    continue
                text_run = element['textRun']

                # Don't start the search until after the starting position
                end_index = element['endIndex']
                if end_index < abs_start_offset:
                    continue

                start_index = element['startIndex']
                content = text_run['content']

                # Trim off content if it starts after the starting position
                start_offset = max(0,abs_start_offset - start_index)
                if start_offset > 0:
                    content = content[start_offset:]

                matches = self.find_common_substrings(content.lower(), text.lower())
                for match in matches:
                    # Need to exceed partial match threshold
                    if match.size < int(len(text) * self.partial_match_thresh):
                        continue

                    offset = match.a

                    # Check for whitespace before found text
                    if offset > 0 and content[offset-1].isalpha():
                        continue

                    # Check for whitespace after found text
                    next_offset = offset + match.size
                    if next_offset < len(content) and content[next_offset].isalpha():
                        continue

                    content_text = content[offset:(offset + match.size)]

                    first_index = elements[0]['startIndex']
                    offset += (start_index + start_offset) - first_index

                    link = None

                    if 'textStyle' in text_run:
                        text_style = text_run['textStyle']
                        if 'link' in text_style:
                            link = text_style['link']
                            if 'url' in link:
                                link = link['url']
                    results.append((paragraph_index, offset, offset + match.size - 1, link, content_text))
        return results

    def handleGET(self, httpMessage, sm):
        resource = httpMessage.get_path()

        if resource == "/status":
            self.send_response(200, 'OK', 'Intent Parser Server is Up and Running\n', sm)
        elif resource == '/document_report':
            self.process_generate_report(httpMessage, sm)
        else:
            print('Did not find ' + resource)
            raise ConnectionException(404, 'Not Found', 'Resource Not Found')

    def new_connection(self, document_id):
        self.client_state_lock.acquire()
        if document_id in self.client_state_map:
            if self.client_state_map[document_id]['locked']:
                self.client_state_lock.release()
                raise ConnectionException(503, 'Service Unavailable',
                                          'This document is busy')

        client_state = {}
        client_state['document_id'] = document_id
        client_state['locked'] = True

        self.client_state_map[document_id] = client_state

        self.client_state_lock.release()

        return client_state

    def get_connection(self, document_id):
        self.client_state_lock.acquire()
        if document_id not in self.client_state_map:
            self.client_state_lock.release()
            raise ConnectionException(404, 'Bad Request',
                                      'Invalid session')

        client_state = self.client_state_map[document_id]

        if client_state['locked']:
            self.client_state_lock.release()
            raise ConnectionException(503, 'Service Unavailable',
                                      'This document is busy')
        client_state['locked'] = True
        self.client_state_lock.release()

        return client_state

    def release_connection(self, client_state):
        if client_state is None:
            return

        self.client_state_lock.acquire()

        document_id = client_state['document_id']

        if document_id in self.client_state_map:
            client_state = self.client_state_map[document_id]
            client_state['locked'] = False

        self.client_state_lock.release()

    def stop(self):
        ''' Stop the intent parser server
        '''
        if self.sbh is not None:
            self.sbh.stop()

        print('Signaling shutdown...')
        self.shutdownThread = True
        self.event.set()

        if self.server is not None:
            print('Closing server...')
            self.server.shutdown(socket.SHUT_RDWR)
            self.server.close()
        print('Shutdown complete')

    def housekeeping(self):
        while True:
            self.event.wait(3600)
            if self.shutdownThread:
                return

            try:
                item_map = self.generate_item_map(use_cache=False)

            except Exception as ex:
                print(''.join(traceback.format_exception(etype=type(ex),
                                                         value=ex,
                                                         tb=ex.__traceback__)))
                continue

            self.item_map_lock.acquire()
            self.item_map = item_map
            self.item_map_lock.release()


    def generate_item_map(self, *, use_cache=True):
        item_map = {}

        if use_cache:
            try:
                f = open(self.my_path + '/item-map.json', 'r')
                item_map = json.loads(f.read())
                f.close()
                return item_map

            except:
                pass

        sheet_data = self.fetch_spreadsheet_data()
        for tab in sheet_data:
            for row in sheet_data[tab]:
                if not 'Common Name' in row :
                    continue

                if len(row['Common Name']) == 0 :
                    continue

                if not 'SynBioHub URI' in row :
                    continue

                if len(row['SynBioHub URI']) == 0 :
                    continue

                common_name = row['Common Name']
                uri = row['SynBioHub URI']
                item_map[common_name] = uri

        f = open(self.my_path + '/item-map.json', 'w')
        f.write(json.dumps(item_map))
        f.close()

        return item_map

    def generate_html_options(self, options):
        options_html = ''
        for item_type in options:
            options_html += '          '
            options_html += '<option>'
            options_html += item_type
            options_html += '</option>\n'

        return options_html

    def generate_existing_link_html(self, title, target, two_col = False):
        if two_col:
            width = 175
        else:
            width = 350

        html  = '<tr>\n'
        html += '  <td style="max-width: %dpx; word-wrap: break-word; padding:5px">\n' % width
        html += '    <a href=' + target + ' target=_blank name="theLink">' + title + '</a>\n'
        html += '  </td>\n'
        html += '  <td>\n'
        html += '    <input type="button" name=' + target + ' value="Link"\n'
        html += '    onclick="linkItem(thisForm, this.name)">\n'
        if not two_col:
            html += '  </td>\n'
            html += '  <td>\n'
        else:
            html += '  <br/>'
        html += '    <input type="button" name=' + target + ' value="Link All"\n'
        html += '    onclick="linkAll(thisForm, this.name)">\n'
        html += '  </td>\n'
        html += '</tr>\n'

        return html

    def generate_results_pagination_html(self, offset, count):
        curr_set_str = '%d - %d' % (offset, offset + self.sparql_limit)
        firstHTML = '<a onclick="refreshList(%d)" href="#first" >First</a>' % 0
        lastHTML  = '<a onclick="refreshList(%d)" href="#last" >Last</a>' % (count - self.sparql_limit)
        prevHTML  = '<a onclick="refreshList(%d)" href="#previous" >Previous</a>' % max(0, offset - self.sparql_limit - 1)
        nextHTML  = '<a onclick="refreshList(%d)" href="#next" >Next</a>'  % min(count - self.sparql_limit, offset + self.sparql_limit + 1)

        html  = '<tr>\n'
        html += '  <td align="center" colspan = 3 style="max-width: 250px; word-wrap: break-word;">\n'
        html += '    Showing %s of %s\n' % (curr_set_str, count)
        html += '  </td>\n'
        html += '</tr>\n'
        html += '<tr>\n'
        html += '  <td align="center" colspan = 3 style="max-width: 250px; word-wrap: break-word;">\n'
        html += '    %s, %s, %s, %s\n' % (firstHTML, prevHTML, nextHTML, lastHTML)
        html += '  </td>\n'
        html += '</tr>\n'

        return html

    def process_add_to_syn_bio_hub(self, httpMessage, sm):
        try:
            json_body = self.get_json_body(httpMessage)

            data = json_body['data']
            start = data['start']
            end = data['end']
            document_id = json_body['documentId']

            start_paragraph = start['paragraphIndex'];
            end_paragraph = end['paragraphIndex'];

            start_offset = start['offset']
            end_offset = end['offset'] + 1

            dialog_action = self.internal_add_to_syn_bio_hub(document_id, start_paragraph, end_paragraph,
                                                             start_offset, end_offset)
            actionList = [dialog_action]
            actions = {'actions': actionList}

            self.send_response(200, 'OK', json.dumps(actions), sm, 'application/json')
        except Exception as e:
            raise e


    def internal_add_to_syn_bio_hub(self, document_id, start_paragraph, end_paragraph, start_offset, end_offset, isSpellcheck=False):
        try:

            item_type_list = []
            for sbol_type in self.item_types:
                item_type_list += self.item_types[sbol_type].keys()

            item_type_list = sorted(item_type_list)
            item_types_html = self.generate_html_options(item_type_list)

            lab_ids_html = self.generate_html_options(self.lab_ids_list)

            try:
                doc = self.google_accessor.get_document(
                    document_id=document_id
                )
            except Exception as ex:
                print(''.join(traceback.format_exception(etype=type(ex),
                                                         value=ex,
                                                         tb=ex.__traceback__)))
                raise ConnectionException('404', 'Not Found',
                                          'Failed to access document ' +
                                          document_id)

            body = doc.get('body');
            doc_content = body.get('content')
            paragraphs = self.get_paragraphs(doc_content)

            paragraph_text = self.get_paragraph_text(
                paragraphs[start_paragraph])


            selection = paragraph_text[start_offset:end_offset]
            # Remove leading/trailing space
            selection = selection.strip()
            display_id = self.sanitize_name_to_display_id(selection)

            html = self.add_html

            # Update parameters in html
            html = html.replace('${COMMONNAME}', selection)
            html = html.replace('${DISPLAYID}', display_id)
            html = html.replace('${STARTPARAGRAPH}', str(start_paragraph))
            html = html.replace('${STARTOFFSET}', str(start_offset))
            html = html.replace('${ENDPARAGRAPH}', str(end_paragraph))
            html = html.replace('${ENDOFFSET}', str(end_offset))
            html = html.replace('${ITEMTYPEOPTIONS}', item_types_html)
            html = html.replace('${LABIDSOPTIONS}', lab_ids_html)
            html = html.replace('${SELECTEDTERM}', selection)
            html = html.replace('${DOCUMENTID}', document_id)
            html = html.replace('${ISSPELLCHECK}', str(isSpellcheck))

            if isSpellcheck:
                replaceButtonHtml = """
        <input type="button" value="Submit" id="submitButton" onclick="submitToSynBioHub()">
        <input type="button" value="Submit, Link All" id="submitButtonLinkAll" onclick="submitToSynBioHubAndLinkAll()">
                """
                html = html.replace('${SUBMIT_BUTTON}', replaceButtonHtml)
            else:
                html = html.replace('${SUBMIT_BUTTON}', '        <input type="button" value="Submit" id="submitButton" onclick="submitToSynBioHub()">')

            dialog_action = self.modal_dialog(html, 'Add to SynBioHub',
                                              600, 600)
            return dialog_action
        except Exception as e:
            raise e

    def char_is_not_wordpart(self, ch):
        """ Determines if a character is part of a word or not
        This is used when parsing the text to tokenize words.
        """
        return ch is not '\'' and not ch.isalnum()

    def strip_leading_trailing_punctuation(self, word):
        """ Remove any leading of trailing punctuation (non-alphanumeric characters
        """
        start_index = 0
        end_index = len(word)
        while start_index < len(word) and not word[start_index].isalnum():
            start_index +=1
        while end_index > 0 and not word[end_index - 1].isalnum():
            end_index -= 1

        # If the word was only non-alphanumeric, we could get into a strange case
        if (end_index <= start_index):
            return ''
        else:
            return word[start_index:end_index]

    def should_ignore_token(self, word):
        """ Determines if a token/word should be ignored
        For example, if a token contains no alphabet characters, we should ignore it.
        """

        contains_alpha = False
        # This was way too slow
        #term_exists_in_sbh = len(self.simple_syn_bio_hub_search(word)) > 0
        term_exists_in_sbh = False
        for ch in word:
            contains_alpha |= ch.isalpha()

        return not contains_alpha  or term_exists_in_sbh

    def process_add_by_spelling(self, http_message, sm):
        """ Function that sets up the results for additions by spelling
        This will start from a given offset (generally 0) and searches the rest of the
        document, looking for words that are not in the dictionary.  Any words that
        don't match are then used as suggestions for additions to SynBioHub.

        Users can add words to the dictionary, and added words are saved by a user id.
        This comes from the email address, but if that's not available the document id
        is used instead.
        """
        try:
            client_state = None
            json_body = self.get_json_body(http_message)

            document_id = json_body['documentId']
            user = json_body['user']
            userEmail = json_body['userEmail']

            if not userEmail is '':
                userId = userEmail
            elif user:
                userId = user
            else:
                userId = document_id

            if not userId in self.spellCheckers:
                self.spellCheckers[userId] = SpellChecker()
                dict_path = os.path.join(self.dict_path, userId + '.json')
                if os.path.exists(dict_path):
                    print('Loaded dictionary for userId, path: %s' % dict_path)
                    self.spellCheckers[userId].word_frequency.load_dictionary(dict_path)

            try:
                doc = self.google_accessor.get_document(
                    document_id=document_id
                )
            except Exception as ex:
                print(''.join(traceback.format_exception(etype=type(ex),
                                                         value=ex,
                                                         tb=ex.__traceback__)))
                raise ConnectionException('404', 'Not Found',
                                          'Failed to access document ' +
                                          document_id)

            if 'data' in json_body:
                body = doc.get('body');
                doc_content = body.get('content')
                paragraphs = self.get_paragraphs(doc_content)

                data = json_body['data']
                paragraph_index = data['paragraphIndex']
                offset = data['offset']
                paragraph = paragraphs[ paragraph_index ]
                first_element = paragraph['elements'][0]
                paragraph_offset = first_element['startIndex']
                starting_pos = paragraph_offset + offset
            else:
                starting_pos = 0

            # Used to store session information
            client_state = self.new_connection(document_id)
            client_state['doc'] = doc
            client_state['user_id'] = userId

            body = doc.get('body');
            doc_content = body.get('content')
            paragraphs = self.get_paragraphs(doc_content)

            start = time.time()

            spellCheckResults = [] # Store results metadata
            missedTerms = [] # keep track of lists of misspelt words
            # Second list can help us remove results by word

            for pIdx in range(0, len(paragraphs)):
                paragraph = paragraphs[ pIdx ]
                elements = paragraph['elements']
                firstIdx = elements[0]['startIndex']
                for element_index in range( len(elements) ):
                    element = elements[ element_index ]

                    if 'textRun' not in element:
                        continue
                    text_run = element['textRun']

                    end_index = element['endIndex']
                    if end_index < starting_pos:
                        continue

                    start_index = element['startIndex']

                    if start_index < starting_pos:
                        wordStart = starting_pos - start_index
                    else:
                        wordStart = 0

                    # If this text run is already linked, we don't need to process it
                    if 'textStyle' in text_run and 'link' in text_run['textStyle']:
                        continue

                    content = text_run['content']
                    endIdx = len(content);
                    currIdx = wordStart + 1
                    while currIdx < endIdx:
                        # Check for end of word
                        if self.char_is_not_wordpart(content[currIdx]):
                            word = content[wordStart:currIdx]
                            word = self.strip_leading_trailing_punctuation(word)
                            word = word.lower()
                            if not word in self.spellCheckers[userId] and not self.should_ignore_token(word):
                                # Convert from an index into the content string,
                                # to an offset into the paragraph string
                                absoluteIdx =  wordStart + (start_index - firstIdx)
                                result = {
                                   'term' : word,
                                   'select_start' : {'paragraph_index' : pIdx,
                                                        'cursor_index' : absoluteIdx,
                                                        'element_index': element_index},
                                   'select_end' : {'paragraph_index' : pIdx,
                                                        'cursor_index' : absoluteIdx + len(word) - 1,
                                                        'element_index': element_index}
                                   }
                                spellCheckResults.append(result)
                                missedTerms.append(word)
                            # Find start of next word
                            while currIdx < endIdx and self.char_is_not_wordpart(content[currIdx]):
                                currIdx += 1
                            # Store word start
                            wordStart = currIdx
                            currIdx += 1
                        else: # continue until we find word end
                            currIdx += 1

                    # Check for tailing word that wasn't processed
                    if currIdx - wordStart > 1:
                        word = content[wordStart:currIdx]
                        if not word in self.spellCheckers[userId]:
                            absoluteIdx =  wordStart + (start_index - firstIdx)
                            result = {
                               'term' : word,
                               'select_start' : {'paragraph_index' : pIdx,
                                                    'cursor_index' : absoluteIdx,
                                                    'element_index': element_index},
                               'select_end' : {'paragraph_index' : pIdx,
                                                    'cursor_index' : absoluteIdx + len(word) - 1,
                                                    'element_index': element_index}
                               }
                            spellCheckResults.append(result)
                            missedTerms.append(word)
            end = time.time()
            print('Scanned entire document in %0.2fms' %((end - start) * 1000))

            # If we have a spelling mistake, highlight text and update user
            if len(spellCheckResults) > 0:
                client_state['spelling_results'] = spellCheckResults
                client_state['spelling_index'] = 0
                client_state['spelling_size'] = len(spellCheckResults)
                actionList = self.report_spelling_results(client_state)
                actions = {'actions': actionList}
                self.send_response(200, 'OK', json.dumps(actions), sm, 'application/json')
            else: # No spelling mistakes!
                buttons = [('Ok', 'process_nop')]
                dialog_action = self.simple_modal_dialog('Found no words not in spelling dictionary!', buttons, 'No misspellings!', 400, 450)
                actionList = [dialog_action]
                actions = {'actions': actionList}
                self.send_response(200, 'OK', json.dumps(actions), sm,
                                   'application/json')
        except Exception as e:
            raise e

        finally:
            if not client_state is None:
                self.release_connection(client_state)

    def report_spelling_results(self, client_state):
        """Generate actions for client, given the current spelling results index
        """
        spellCheckResults = client_state['spelling_results']
        resultIdx = client_state['spelling_index']

        actionList = []

        start_par = spellCheckResults[resultIdx]['select_start']['paragraph_index']
        start_cursor = spellCheckResults[resultIdx]['select_start']['cursor_index']
        end_par = spellCheckResults[resultIdx]['select_end']['paragraph_index']
        end_cursor = spellCheckResults[resultIdx]['select_end']['cursor_index']
        if not start_par == end_par:
            print('Received a highlight request across paragraphs, which is currently unsupported!')
        highlightTextAction = self.highlight_text(start_par, start_cursor, end_cursor)
        actionList.append(highlightTextAction)

        html  = ''
        html += '<center>'
        html += 'Term ' + spellCheckResults[resultIdx]['term'] + ' not found in dictionary, potential addition? ';
        html += '</center>'

        manualLinkScript = """

    function EnterLinkClick() {
        google.script.run.withSuccessHandler(enterLinkHandler).enterLinkPrompt('Manually enter a SynbioHub link for this term.', 'Enter URI:');
    }

    function enterLinkHandler(result) {
        var shouldProcess = result[0];
        var text = result[1];
        if (shouldProcess) {
            var data = {'buttonId' : 'spellcheck_link',
                     'link' : text}
            google.script.run.withSuccessHandler(onSuccess).buttonClick(data)
        }
    }

        """

        buttons = [('Ignore', 'spellcheck_add_ignore', 0),
                   ('Ignore All', 'spellcheck_add_ignore_all', 0),
                   ('Add to SynBioHub', 'spellcheck_add_synbiohub', 0),
                   ('Add to Spellchecker Dictionary', 'spellcheck_add_dictionary', 0),
                   ('Manually Enter Link', manualLinkScript, 1, 'EnterLink'),
                   ('Include Previous Word', 'spellcheck_add_select_previous', 0),
                   ('Include Next Word', 'spellcheck_add_select_next', 0),
                   ('Remove First Word', 'spellcheck_add_drop_first', 0),
                   ('Remove Last Word', 'spellcheck_add_drop_last', 0)]

        dialogAction = self.simple_sidebar_dialog(html, buttons)
        actionList.append(dialogAction)
        return actionList

    def spellcheck_remove_term(self, client_state):
        """ Removes the current term from the result set, returning True if a term was removed else False.
        False will be returned if there are no terms after the term being removed.
        """
        curr_idx = client_state['spelling_index']
        next_idx = curr_idx + 1
        spelling_results = client_state['spelling_results']
        while next_idx < client_state['spelling_size'] and spelling_results[curr_idx]['term'] == spelling_results[next_idx]['term']:
            next_idx = next_idx + 1
        # Are we at the end? Then just exit
        if next_idx >= client_state['spelling_size']:
            return False

        term_to_ignore = spelling_results[curr_idx]['term']
        # Generate results without term to ignore
        new_spelling_results = [r for r in spelling_results if not r['term'] == term_to_ignore ]

        # Find out what term to point to
        new_idx = new_spelling_results.index(spelling_results[next_idx])
        # Update client state
        client_state['spelling_results'] = new_spelling_results
        client_state['spelling_index'] = new_idx
        client_state['spelling_size'] = len(new_spelling_results)
        return True

    def spellcheck_add_ignore(self, json_body, client_state):
        """ Ignore button action for additions by spelling
        """
        json_body # Remove unused warning
        client_state['spelling_index'] += 1
        if client_state['spelling_index'] >= client_state['spelling_size']:
            # We are at the end, nothing else to do
            return []
        else:
            return self.report_spelling_results(client_state)

    def spellcheck_add_ignore_all(self, json_body, client_state):
        """ Ignore All button action for additions by spelling
        """
        json_body # Remove unused warning
        if self.spellcheck_remove_term(client_state):
            return self.report_spelling_results(client_state)

    def spellcheck_add_synbiohub(self, json_body, client_state):
        """ Add to SBH button action for additions by spelling
        """
        json_body # Remove unused warning

        doc_id = client_state['document_id']
        spell_index = client_state['spelling_index']
        spell_check_result = client_state['spelling_results'][spell_index]
        select_start = spell_check_result['select_start']
        select_end = spell_check_result['select_end']

        start_paragraph = select_start['paragraph_index']
        start_offset = select_start['cursor_index']

        end_paragraph = select_end['cursor_index']
        end_offset = select_end['cursor_index'] + 1

        dialog_action = self.internal_add_to_syn_bio_hub(doc_id, start_paragraph, end_paragraph,
                                                             start_offset, end_offset, isSpellcheck=True)

        actionList = [dialog_action]

        # Show side bar with current entry, in case the dialog is canceled
        # If the form is successully submitted, the next term will get displayed at that time
        for action in self.report_spelling_results(client_state):
            actionList.append(action)

        return actionList

    def spellcheck_add_dictionary(self, json_body, client_state):
        """ Add to spelling dictionary button action for additions by spelling
        """
        json_body # Remove unused warning
        user_id = client_state['user_id']

        spell_index = client_state['spelling_index']
        spell_check_result = client_state['spelling_results'][spell_index]
        new_word = spell_check_result['term']

        # Add new word to frequency list
        self.spellCheckers[user_id].word_frequency.add(new_word)

        # Save updated frequency list for later loading
        # We could probably do this later, but it ensures no updated state is lost
        dict_path = os.path.join(self.dict_path, user_id + '.json')
        self.spellCheckers[user_id].export(dict_path)

        # Since we are adding this term to the spelling dict, we want to ignore any other results
        self.spellcheck_remove_term(client_state)
        # Removing the term automatically updates the spelling index
        #client_state["spelling_index"] += 1
        if client_state['spelling_index'] >= client_state['spelling_size']:
            # We are at the end, nothing else to do
            return []

        return self.report_spelling_results(client_state)

    def spellcheck_link(self, json_body, client_state):
        """
        Handle creating a link button as part of additions by spelling.
        """
        spell_index = client_state['spelling_index']
        spell_check_result = client_state['spelling_results'][spell_index]

        if type(json_body['data']['buttonId']) is dict:
            new_link = json_body['data']['buttonId']['link']
        else:
            new_link = None
            print('spellcheck_link received a json_body without a link in it!')

        start_par = spell_check_result['select_start']['paragraph_index']
        start_cursor = spell_check_result['select_start']['cursor_index']
        end_cursor = spell_check_result['select_end']['cursor_index']

        actions = [self.link_text(start_par, start_cursor, end_cursor, new_link)]
        client_state['spelling_index'] += 1
        if client_state['spelling_index'] < client_state['spelling_size']:
            for action in self.report_spelling_results(client_state):
                actions.append(action)
        return actions

    def spellcheck_add_select_previous(self, json_body, client_state):
        """ Select previous word button action for additions by spelling
        """
        json_body # Remove unused warning
        return self.spellcheck_select_word_from_text(client_state, True, True)

    def spellcheck_add_select_next(self, json_body, client_state):
        """ Select next word button action for additions by spelling
        """
        json_body # Remove unused warning
        return self.spellcheck_select_word_from_text(client_state, False, True)

    def spellcheck_add_drop_first(self, json_body, client_state):
        """ Remove selection previous word button action for additions by spelling
        """
        json_body # Remove unused warning
        return self.spellcheck_select_word_from_text(client_state, True, False)

    def spellcheck_add_drop_last(self, json_body, client_state):
        """ Remove selection next word button action for additions by spelling
        """
        json_body # Remove unused warning
        return self.spellcheck_select_word_from_text(client_state, False, False)

    def spellcheck_select_word_from_text(self, client_state, isPrev, isSelect):
        """ Given a client state with a selection from a spell check result,
        select or remove the selection on the next or previous word, based upon parameters.
        """
        if isPrev:
            select_key = 'select_start'
        else:
            select_key = 'select_end'

        spell_index = client_state['spelling_index']
        spell_check_result = client_state['spelling_results'][spell_index]

        starting_pos = spell_check_result[select_key]['cursor_index']
        para_index = spell_check_result[select_key]['paragraph_index']
        doc = client_state['doc']
        body = doc.get('body');
        doc_content = body.get('content')
        paragraphs = self.get_paragraphs(doc_content)
        # work on the paragraph text directly
        paragraph_text = self.get_paragraph_text(paragraphs[para_index])
        para_text_len = len(paragraph_text)

        # Determine which directions to search in, based on selection or removal, prev/next
        if isSelect:
            if isPrev:
                edge_check = lambda x : x > 0
                increment = -1
            else:
                edge_check = lambda x : x < para_text_len
                increment = 1
            firstCheck = self.char_is_not_wordpart
            secondCheck = lambda x : not self.char_is_not_wordpart(x)
        else:
            if isPrev:
                edge_check = lambda x : x < para_text_len
                increment = 1
            else:
                edge_check = lambda x : x > 0
                increment = -1
            secondCheck = self.char_is_not_wordpart
            firstCheck = lambda x : not self.char_is_not_wordpart(x)

        if starting_pos < 0:
            print('Error: got request to select previous, but the starting_pos was negative!')
            return

        if para_text_len < starting_pos:
            print('Error: got request to select previous, but the starting_pos was past the end!')
            return

        # Move past the end/start of the current word
        currIdx = starting_pos + increment

        # Skip over space/non-word parts to the next word
        while edge_check(currIdx) and firstCheck(paragraph_text[currIdx]):
            currIdx += increment
        # Find the beginning/end of word
        while edge_check(currIdx) and secondCheck(paragraph_text[currIdx]):
            currIdx += increment

        # If we don't hit the beginning, we need to cut off the last space
        if currIdx > 0 and isPrev and isSelect:
            currIdx += 1

        if not isPrev and isSelect and paragraph_text[currIdx].isspace():
            currIdx += -1

        spell_check_result[select_key]['cursor_index'] = currIdx

        return self.report_spelling_results(client_state)

    def simple_syn_bio_hub_search(self, term, offset=0, filter_uri=None):
        """
        Search for similar terms in SynbioHub, using the cached sparql similarity query.
        This query requires the specification of a term, a limit on the number of results, and an offset.
        """
        if filter_uri is None:
            extra_filter = ''
        else:
            extra_filter = 'FILTER( !regex(?member, "%s"))' % filter_uri

        if offset == 0 or not term in self.sparql_similar_count_cache:
            start = time.time()
            sparql_count = self.sparql_similar_count.replace('${TERM}', term).replace('${EXTRA_FILTER}', extra_filter)
            query_results = self.sbh.sparqlQuery(sparql_count)
            bindings = query_results['results']['bindings']
            self.sparql_similar_count_cache[term] = bindings[0]['count']['value']
            end = time.time()
            print('Simple SynbioHub count for %s took %0.2fms (found %s results)' %(term, (end - start) * 1000, bindings[0]['count']['value']))

        start = time.time()
        sparql_query = self.sparql_similar_query.replace('${TERM}', term).replace('${LIMIT}', str(self.sparql_limit)).replace('${OFFSET}', str(offset)).replace('${EXTRA_FILTER}', extra_filter)
        query_results = self.sbh.sparqlQuery(sparql_query)
        bindings = query_results['results']['bindings']
        search_results = []
        for binding in bindings:
            title = binding['title']['value']
            target = binding['member']['value']
            if self.sbh_spoofing_prefix is not None:
                target = target.replace(self.sbh_spoofing_prefix, self.sbh_url)
            search_results.append({'title': title, 'target': target})

        end = time.time()
        print('Simple SynbioHub search for %s took %0.2fms' %(term, (end - start) * 1000))
        return search_results, self.sparql_similar_count_cache[term]

    def sanitize_name_to_display_id(self, name):
        displayIDfirstChar = '[a-zA-Z_]'
        displayIDlaterChar = '[a-zA-Z0-9_]'

        sanitized = ''
        for i in range(len(name)):
            character = name[i]
            if i==0:
                if re.match(displayIDfirstChar, character):
                    sanitized += character
                else:
                    sanitized += '_' # avoid starting with a number
                    if re.match(displayIDlaterChar, character):
                        sanitized += character
                    else:
                        sanitized += '0x{:x}'.format(ord(character))
            else:
                if re.match(displayIDlaterChar, character):
                    sanitized += character;
                else:
                    sanitized += '0x{:x}'.format(ord(character))

        return sanitized

    def set_item_properties(self, entity, data):
        item_type = data['itemType']
        item_name = data['commonName']
        item_definition_uri = data['definitionURI']
        item_lab_ids = data['labId']

        sbol.TextProperty(entity, 'http://purl.org/dc/terms/title', '0', '1',
                          item_name)

        time_stamp = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S-00')
        sbol.TextProperty(entity, 'http://purl.org/dc/terms/created', '0', '1',
                          time_stamp)
        sbol.TextProperty(entity, 'http://purl.org/dc/terms/modified', '0', '1',
                          time_stamp)

        if item_type in self.item_types['collection']:
            return

        if len(item_definition_uri) > 0:
            if item_type == 'CHEBI':
                if not item_definition_uri.startswith('http://identifiers.org/chebi/CHEBI'):
                    item_definition_uri = 'http://identifiers.org/chebi/CHEBI:' + \
                        item_definition_uri
            else:
                sbol.URIProperty(entity, 'http://www.w3.org/ns/prov#wasDerivedFrom',
                                 '0', '1', item_definition_uri)

        if len(item_lab_ids) > 0:
            lab_id_tag = data['labIdSelect'].replace(' ', '_')
            tp = None
            for item_lab_id in item_lab_ids.split(','):
                if tp is None:
                    tp = sbol.TextProperty(entity, 'http://sd2e.org#' + lab_id_tag, '0', '1',
                                           item_lab_id)
                else:
                    tp.add(item_lab_id)

    def operation_failed(self, message):
        return {'results': {'operationSucceeded': False,
                            'message': message}
        }

    def create_dictionary_entry(self, data, document_url, item_definition_uri):
        item_type = data['itemType']
        item_name = data['commonName']
        item_lab_ids = data['labId']
        item_lab_id_tag = data['labIdSelect']

        #sbh_uri_prefix = self.sbh_uri_prefix
        if self.sbh_spoofing_prefix is not None:
            item_uri = document_url.replace(self.sbh_url,
                                            self.sbh_spoofing_prefix)
        else:
            item_uri = document_url

        tab_name = self.type2tab[item_type]

        try:
            tab_data = self.google_accessor.get_row_data(tab=tab_name)
        except:
            raise Exception('Failed to access dictionary spreadsheet')

        # Get common names
        item_map = {}
        for row_data in tab_data:
            common_name = row_data['Common Name']
            if common_name is None or len(common_name) == 0:
                continue
            item_map[common_name] = row_data

        if item_name in item_map:
            raise Exception('"' + item_name + '" already exists in dictionary spreadsheet')

        dictionary_entry = {}
        dictionary_entry['tab'] = tab_name
        dictionary_entry['row'] = len(tab_data) + 3
        dictionary_entry['Common Name'] = item_name
        dictionary_entry['Type'] = item_type
        if tab_name == 'Reagent':
            dictionary_entry['Definition URI / CHEBI ID'] = \
                item_definition_uri
        else:
            dictionary_entry['Definition URI'] = \
                item_definition_uri

        if item_type != 'Attribute':
            dictionary_entry['Stub Object?'] = 'YES'

        dictionary_entry[item_lab_id_tag] = item_lab_ids
        dictionary_entry['SynBioHub URI'] = item_uri

        try:
            self.google_accessor.set_row_data(dictionary_entry)
        except:
            raise Exception('Failed to add entry to the dictionary spreadsheet')

    def create_sbh_stub(self, data):
        # Extract some fields from the form
        try:
            item_type = data['itemType']
            item_name = data['commonName']
            item_definition_uri = data['definitionURI']
            item_display_id = data['displayId']

        except Exception as e:
            return self.operation_failed('Form sumission missing key: ' + str(e))

        # Make sure Common Name was specified
        if len(item_name) == 0:
            return self.operation_failed('Common Name must be specified')

        # Sanitize the display id
        if len(item_display_id) > 0:
            display_id = self.sanitize_name_to_display_id(item_display_id)
            if display_id != item_display_id:
                return self.operation_failed('Illegal display_id')
        else:
            display_id = self.sanitize_name_to_display_id(item_name)

        # Derive document URL
        document_url = self.sbh_uri_prefix + display_id + '/1'

        # Make sure document does not already exist
        try:
            if self.sbh.exists(document_url):
                return self.operation_failed('"' + display_id +
                                             '" already exists in SynBioHub')
        except:
            return self.operation_failed('Failed to access SynBioHub')

        # Look up sbol type uri
        sbol_type = None
        for sbol_type_key in self.item_types:
            sbol_type_map = self.item_types[ sbol_type_key ]
            if item_type in sbol_type_map:
                sbol_type = sbol_type_key
                break;

        # Fix CHEBI URI
        if item_type == 'CHEBI':
            if len(item_definition_uri) == 0:
                item_definition_uri = sbol_type_map[ item_type ]
            else:
                if not item_definition_uri.startswith('http://identifiers.org/chebi/CHEBI'):
                    item_definition_uri = 'http://identifiers.org/chebi/CHEBI:' + \
                        item_definition_uri

        # Create a dictionary entry for the item
        try:
            self.create_dictionary_entry(data, document_url, item_definition_uri)

        except Exception as e:
            return self.operation_failed(str(e))

        # Create an entry in SynBioHub
        try:
            document = sbol.Document()
            document.addNamespace('http://sd2e.org#', 'sd2')
            document.addNamespace('http://purl.org/dc/terms/', 'dcterms')
            document.addNamespace('http://www.w3.org/ns/prov#', 'prov')

            if sbol_type == 'component':
                if item_type == 'CHEBI':
                    item_sbol_type = item_definition_uri
                else:
                    item_sbol_type = sbol_type_map[ item_type ]

                component = sbol.ComponentDefinition(display_id, item_sbol_type)

                sbol.TextProperty(component, 'http://sd2e.org#stub_object', '0', '1', 'true')
                self.set_item_properties(component, data)

                document.addComponentDefinition(component)

            elif sbol_type == 'module':
                module = sbol.ModuleDefinition(display_id)
                sbol.TextProperty(module, 'http://sd2e.org#stub_object', '0', '1', 'true')

                module.roles = sbol_type_map[ item_type ]
                self.set_item_properties(module, data)

                document.addModuleDefinition(module)

            elif sbol_type == 'external':
                top_level = sbol.TopLevel('http://http://sd2e.org/types/#attribute', display_id)
                self.set_item_properties(top_level, data)

                document.addTopLevel(top_level)

            elif sbol_type == 'collection':
                collection = sbol.Collection(display_id)
                self.set_item_properties(collection, data)
                document.addCollection(collection)

            else:
                raise Exception()

            self.sbh.submit(document, self.sbh_collection_uri, 3)

            paragraph_index = data['selectionStartParagraph']
            offset = data['selectionStartOffset']
            end_offset = data['selectionEndOffset']

            action = self.link_text(paragraph_index, offset,
                                    end_offset, document_url)

        except Exception as e:
            print(''.join(traceback.format_exception(etype=type(e),
                                                     value=e,
                                                     tb=e.__traceback__)))

            message = 'Failed to add "' + display_id + '" to SynBioHub'
            return self.operation_failed(message)

        return_info = {'actions': [action],
                       'results': {'operationSucceeded': True}
                      }

        return return_info

    def process_nop(self, httpMessage, sm):
        httpMessage # Fix unused warning
        sm # Fix unused warning
        return []

    def process_submit_form(self, httpMessage, sm):
        (json_body, client_state) = self.get_client_state(httpMessage)
        try:
            data = json_body['data']
            action = data['extra']['action']

            result = {}

            if action == 'submit':
                result = self.create_sbh_stub(data)
                if result['results']['operationSucceeded'] and data['isSpellcheck'] == 'True':
                    client_state["spelling_index"] += 1
                    if client_state['spelling_index'] < client_state['spelling_size']:
                        for action in self.report_spelling_results(client_state):
                            result['actions'].append(action)
            elif action == 'submitLinkAll':
                result = self.create_sbh_stub(data)
                if result['results']['operationSucceeded']:
                    uri = result['actions'][0]['url']
                    data['extra']['link'] = uri
                    linkActions = self.process_form_link_all(data)
                    for action in linkActions:
                        result['actions'].append(action)
                    if bool(data['isSpellcheck']):
                        client_state["spelling_index"] += 1
                        if client_state['spelling_index'] < client_state['spelling_size']:
                            for action in self.report_spelling_results(client_state):
                                result['actions'].append(action)
            elif action == 'link':
                search_result = \
                    {'paragraph_index' : data['selectionStartParagraph'],
                     'offset'          : int(data['selectionStartOffset']),
                     'end_offset'      : int(data['selectionEndOffset']),
                     'uri'             : data['extra']['link']
                    }
                # The end offsets are exclusive in spellcheck search, so subtract one
                if data['isSpellcheck'] == 'True':
                    search_result['end_offset'] -= 1
                actions = self.add_link(search_result)
                result = {'actions': actions,
                          'results': {'operationSucceeded': True}
                }
                if data['isSpellcheck'] == 'True':
                    client_state["spelling_index"] += 1
                    if client_state['spelling_index'] < client_state['spelling_size']:
                        for action in self.report_spelling_results(client_state):
                            result['actions'].append(action)
            elif action == 'linkAll':
                actions = self.process_form_link_all(data)
                result = {'actions': actions,
                          'results': {'operationSucceeded': True}
                }
                if data['isSpellcheck'] == 'True':
                    if self.spellcheck_remove_term(client_state):
                        reportActions = self.report_spelling_results(client_state)
                        for action in reportActions:
                            result['actions'].append(action)

            else:
                print('Unsupported form action: {}'.format(action))

            self.send_response(200, 'OK', json.dumps(result), sm,
                               'application/json')
        finally:
            self.release_connection(client_state)

    def process_form_link_all(self, data):
        document_id = data['documentId']
        doc = self.google_accessor.get_document(
            document_id=document_id
        )
        body = doc.get('body');
        doc_content = body.get('content')
        paragraphs = self.get_paragraphs(doc_content)
        selected_term = data['selectedTerm']
        uri = data['extra']['link']

        actions = []

        pos = 0
        while True:
            result = self.find_exact_text(selected_term, pos, paragraphs)

            if result is None:
                break

            search_result = { 'paragraph_index' : result[0],
                              'offset'          : result[1],
                              'end_offset'      : result[1] + len(selected_term) - 1,
                              'term'            : selected_term,
                              'uri'             : uri,
                              'link'            : result[3],
                              'text'            : result[4]}

            actions += self.add_link(search_result)

            pos = result[2] + len(selected_term)

        return actions

    def process_search_syn_bio_hub(self, httpMessage, sm):
        json_body = self.get_json_body(httpMessage)
        data = json_body['data']

        try:
            offset = 0
            if 'offset' in data:
                offset = int(data['offset'])
            # Bounds check offset value
            if offset < 0:
                offset = 0
            if data['term'] in self.sparql_similar_count_cache:
                # Ensure offset isn't past the end of the results
                if offset > int(self.sparql_similar_count_cache[data['term']]) - self.sparql_limit:
                    offset = max(0, int(self.sparql_similar_count_cache[data['term']]) - self.sparql_limit)
            else:
                # Don't allow a non-zero offset if we haven't cached the size of the query
                if offset > 0:
                    offset = 0

            if 'analyze' in data:
                analyze = True
                filter_uri = data['selected_uri']
            else:
                analyze = False
                filter_uri = None

            search_results, results_count = self.simple_syn_bio_hub_search(data['term'], offset, filter_uri)

            table_html = ''
            for search_result in search_results:
                title = search_result['title']
                target = search_result['target']
                table_html += self.generate_existing_link_html(title, target, analyze)
            table_html += self.generate_results_pagination_html(offset, int(results_count))

            response = {'results':
                        {'operationSucceeded': True,
                         'search_results': search_results,
                         'table_html': table_html
                        }}


        except Exception as err:
            print(str(err))
            response = self.operation_failed('Failed to search SynBioHub')

        self.send_response(200, 'OK', json.dumps(response), sm,
                           'application/json')

spreadsheet_id = '1wHX8etUZFMrvmsjvdhAGEVU1lYgjbuRX5mmYlKv7kdk'
sbh_spoofing_prefix=None
sbh_collection_uri = 'https://hub-staging.sd2e.org/user/sd2e/intent_parser/intent_parser_collection/1'
bind_port = 8080
bind_host = '0.0.0.0'

def usage():
    print('')
    print('intent_parser_server.py: [options]')
    print('')
    print('    -h --help            - show this message')
    print('    -p --pasword         - SynBioHub password')
    print('    -u --username        - SynBioHub username')
    print('    -c --collection      - collection url (default={})'. \
          format(sbh_collection_uri))
    print('    -i --spreadsheet-id  - dictionary spreadsheet id (default={})'. \
          format(spreadsheet_id))
    print('    -s --spoofing-prefix - SBH spoofing prefix (default={})'.
          format(sbh_spoofing_prefix))
    print('    -b --bind-host       - IP address to bind to (default={})'.
          format(bind_host))
    print('    -l --bind-port       - TCP Port to listen on (default={})'.
          format(bind_port))
    print('')

def main(argv):
    sbh_username = None
    sbh_password = None

    global spreadsheet_id
    global sbh_spoofing_prefix
    global sbh_collection_uri
    global bind_port
    global bind_host
    global sbhPlugin

    try:
        opts, __ = getopt.getopt(argv, "u:p:hc:i:s:b:l:",
                                   ["username=",
                                    "password=",
                                    "help",
                                    "collection=",
                                    "spreadsheet-id=",
                                    "spoofing-prefix=",
                                    "bind-host=",
                                    "bind-port="])
    except getopt.GetoptError as err:
        print(str(err))
        usage()
        sys.exit(2);

    for opt,arg in opts:
        if opt in ('-u', '--username'):
            sbh_username = arg

        elif opt in ('-p', '--password'):
            sbh_password = arg

        elif opt in ('-h', '--help'):
            usage()
            sys.exit(0)

        elif opt in ('-c', '--collection'):
            sbh_collection_uri = arg

        elif opt in ('-i', '--spreadsheet-id'):
            spreadsheet_id = arg

        elif opt in ('-s', '--spoofing-prefix'):
            sbh_spoofing_prefix = arg

        elif opt in ('-b', '--bind-host'):
            bind_host = arg

        elif opt in ('-l', '--bind-port'):
            bind_port = int(arg)

    try:
        sbhPlugin = IntentParserServer(sbh_collection_uri=sbh_collection_uri,
                                       sbh_spoofing_prefix=sbh_spoofing_prefix,
                                       sbh_username=sbh_username,
                                       sbh_password=sbh_password,
                                       spreadsheet_id=spreadsheet_id,
                                       bind_ip=bind_host,
                                       bind_port=bind_port)
    except Exception as e:
        print(e)
        usage()
        sys.exit(5)

    sbhPlugin.serverRunLoop()

def signal_int_handler(sig, frame):
    '''  Handling SIG_INT: shutdown intent parser server and wait for it to finish.
    '''
    global sbhPlugin
    global sigIntCount

    sigIntCount += 1
    sig # Remove unused warning
    frame # Remove unused warning

    # Try to cleanly exit on the first try
    if sigIntCount == 1:
        print('\nStopping intent parser server...')
        sbhPlugin.stop()
    # If we receive enough SIGINTs, die
    if sigIntCount > 3:
        sys.exit(0)

signal.signal(signal.SIGINT, signal_int_handler)
sigIntCount = 0


if __name__ == "__main__":
    main(sys.argv[1:])
