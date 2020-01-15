import json
import os
import requests
import unittest

class TestGETGeneratedStruturalRequest(unittest.TestCase):
    """
    Class to test RESTful API calls to generate a structural request from intent parser. 
    """
    
    def setUp(self):
        curr_path = os.path.dirname(os.path.realpath(__file__))
        self.data_dir = os.path.join(curr_path, '../tests/data')
        self.request_uri = 'http://intentparser.sd2e.org/document_request?'
        
    def tearDown(self):
        pass
   
         
    def test_document_request1(self):
        doc_id = '13tJ1JdCxL9bA9x3oNxGPm-LymW91-OT7SRW6fHyEBCo'
        doc_req_uri = self.request_uri + doc_id
        response = requests.get(doc_req_uri)
        self.assertEqual(200, response.status_code)
        actual_data = response.json()
        
        with open(os.path.join(self.data_dir, doc_id + '_expected.json'), 'r') as file:
            expected_data = json.load(file)
            self.assertEqual(expected_data, actual_data)
    
    def test_document_request2(self):
        doc_id = '1WOa8crKEpJX0ZFJv4NtMjVaI-35__sdEMc5aPxb1al4'
        doc_req_uri = self.request_uri + doc_id
        response = requests.get(doc_req_uri)
        self.assertEqual(200, response.status_code)
        actual_data = response.json()
        
        with open(os.path.join(self.data_dir, doc_id + '_expected.json'), 'r') as file:
            expected_data = json.load(file)
            self.assertEqual(expected_data, actual_data)

    def test_document_request3(self):
        doc_id = '1uv_X7CSD5cONEjW7yq4ecI89XQxPQuG5lnmaqshj47o'
        doc_req_uri = self.request_uri + doc_id
        response = requests.get(doc_req_uri)
        self.assertEqual(200, response.status_code)
        actual_data = response.json()
        
        with open(os.path.join(self.data_dir, doc_id + '_expected.json'), 'r') as file:
            expected_data = json.load(file)
            self.assertEqual(expected_data, actual_data)


    def test_document_request4(self):
        doc_id = '1XFC1onvvrhggNHiAci-iu2msXZQg3_SyiGdKnKUwrpM'
        doc_req_uri = self.request_uri + doc_id
        response = requests.get(doc_req_uri)
        self.assertEqual(200, response.status_code)
        actual_data = response.json()
        
        with open(os.path.join(self.data_dir, doc_id + '_expected.json'), 'r') as file:
            expected_data = json.load(file)
            self.assertEqual(expected_data, actual_data)

    def test_document_request5(self):
        doc_id = '1v5UHLS4qvVovMK8GP9MgoboiPGsg_YzgyE9H4E5DTHg'
        doc_req_uri = self.request_uri + doc_id
        response = requests.get(doc_req_uri)
        self.assertEqual(200, response.status_code)
        actual_data = response.json()
        
        with open(os.path.join(self.data_dir, doc_id + '_expected.json'), 'r') as file:
            expected_data = json.load(file)
            self.assertEqual(expected_data, actual_data)


    def test_document_request6(self):
        doc_id = '15aMX9WdN1gyvjG30sXQZYPdTSTGbxoIRJbqtOvoKyQ0'
        doc_req_uri = self.request_uri + doc_id
        response = requests.get(doc_req_uri)
        self.assertEqual(200, response.status_code)
        actual_data = response.json()
        
        with open(os.path.join(self.data_dir, doc_id + '_expected.json'), 'r') as file:
            expected_data = json.load(file)
            self.assertEqual(expected_data, actual_data)

    def test_document_request7(self):
        doc_id = '1N0i5RPY-xEsM_MIjqeWZI6cjb9rj3B7L1PGR-Q-ufe0'
        doc_req_uri = self.request_uri + doc_id
        response = requests.get(doc_req_uri)
        self.assertEqual(200, response.status_code)
        actual_data = response.json()
        
        with open(os.path.join(self.data_dir, doc_id + '_expected.json'), 'r') as file:
            expected_data = json.load(file)
            self.assertEqual(expected_data, actual_data)

    def test_document_request8(self):
        doc_id = '16p9WmU9_dEz6wGN5_maotPl5uGrAIxPZ3-pNq1hipfI'
        doc_req_uri = self.request_uri + doc_id
        response = requests.get(doc_req_uri)
        self.assertEqual(200, response.status_code)
        actual_data = response.json()
        
        with open(os.path.join(self.data_dir, doc_id + '_expected.json'), 'r') as file:
            expected_data = json.load(file)
            self.assertEqual(expected_data, actual_data)
    
    def test_document_request9(self):
        doc_id = '1ZPLjkEODVzRlqRA110cDVT3wK6nvvNr4wKMMPoDLnTY'
        doc_req_uri = self.request_uri + doc_id
        response = requests.get(doc_req_uri)
        self.assertEqual(200, response.status_code)
        actual_data = response.json()
        
        with open(os.path.join(self.data_dir, doc_id + '_expected.json'), 'r') as file:
            expected_data = json.load(file)
            self.assertEqual(expected_data, actual_data)

    def test_document_request10(self):
        doc_id = '16eroq4UtIPhP89_PiKnvfi4wxV52vdKtUwPmBBu6OMc'
        doc_req_uri = self.request_uri + doc_id
        response = requests.get(doc_req_uri)
        self.assertEqual(200, response.status_code)
        actual_data = response.json()
        
        with open(os.path.join(self.data_dir, doc_id + '_expected.json'), 'r') as file:
            expected_data = json.load(file)
            self.assertEqual(expected_data, actual_data)
    
    def test_document_request11(self):
        doc_id = '1IlR2-ufP_vVfHt15uYocExhyQfEkPnOljYf3Y-rB08g'
        doc_req_uri = self.request_uri + doc_id
        response = requests.get(doc_req_uri)
        self.assertEqual(200, response.status_code)
        actual_data = response.json()
        
        with open(os.path.join(self.data_dir, doc_id + '_expected.json'), 'r') as file:
            expected_data = json.load(file)
            self.assertEqual(expected_data, actual_data)
        
    def test_document_request12(self):
        doc_id = '1ISVqTR3GfnzWB7pq66CbAWdVTn2RHBs4rgBbQt9N2Oo'
        doc_req_uri = self.request_uri + doc_id
        response = requests.get(doc_req_uri)
        self.assertEqual(200, response.status_code)
        actual_data = response.json()
        
        with open(os.path.join(self.data_dir, doc_id + '_expected.json'), 'r') as file:
            expected_data = json.load(file)
            self.assertEqual(expected_data, actual_data)

    def test_document_request13(self):
        doc_id = '138hHqZ-HT6owJ3DxANcrds67j8dZG8GPt4KLTTS1jU4'
        doc_req_uri = self.request_uri + doc_id
        response = requests.get(doc_req_uri)
        self.assertEqual(200, response.status_code)
        actual_data = response.json()
        
        with open(os.path.join(self.data_dir, doc_id + '_expected.json'), 'r') as file:
            expected_data = json.load(file)
            self.assertEqual(expected_data, actual_data)

    def test_document_request14(self):
        doc_id = '1PmSRNQUpvFTjANQpktjxjrfItPMTNgGVry5fT3mLmzc'
        doc_req_uri = self.request_uri + doc_id
        response = requests.get(doc_req_uri)
        self.assertEqual(200, response.status_code)
        actual_data = response.json()
        
        with open(os.path.join(self.data_dir, doc_id + '_expected.json'), 'r') as file:
            expected_data = json.load(file)
            self.assertEqual(expected_data, actual_data)
        
    def test_document_request15(self):
        doc_id = '1IagstOKKIp-JiHXUYqoWKaGhoUuc2pwKflknqRdZMhU'
        doc_req_uri = self.request_uri + doc_id
        response = requests.get(doc_req_uri)
        self.assertEqual(200, response.status_code)
        actual_data = response.json()
        
        with open(os.path.join(self.data_dir, doc_id + '_expected.json'), 'r') as file:
            expected_data = json.load(file)
            self.assertEqual(expected_data, actual_data)
        
    def test_document_request16(self):
        doc_id = '1snxxOPbR-kBHSvkQc94BwDcxm0CdG2dcvegW5OeSSfI'
        doc_req_uri = self.request_uri + doc_id
        response = requests.get(doc_req_uri)
        self.assertEqual(200, response.status_code)
        actual_data = response.json()
        
        with open(os.path.join(self.data_dir, doc_id + '_expected.json'), 'r') as file:
            expected_data = json.load(file)
            self.assertEqual(expected_data, actual_data)
        
    def test_document_request17(self):
        doc_id = '1oIBd-a_n8pGNtoM9zYkWjhlsG04B2lmfYKhlLSAkRFw'
        doc_req_uri = self.request_uri + doc_id
        response = requests.get(doc_req_uri)
        self.assertEqual(200, response.status_code)
        actual_data = response.json()
        
        with open(os.path.join(self.data_dir, doc_id + '_expected.json'), 'r') as file:
            expected_data = json.load(file)
            self.assertEqual(expected_data, actual_data)
        
    def test_document_request18(self):
        doc_id = '1h_VBtGgUa4pFrR5pTksogFpzSMuE6cyRRjJmFuJpKSk'
        doc_req_uri = self.request_uri + doc_id
        response = requests.get(doc_req_uri)
        self.assertEqual(200, response.status_code)
        actual_data = response.json()
        
        with open(os.path.join(self.data_dir, doc_id + '_expected.json'), 'r') as file:
            expected_data = json.load(file)
            self.assertEqual(expected_data, actual_data)

    def test_document_request19(self):
        doc_id = '1b81XIA-e_5D6we8nVnMJe6fahizTw4qNSxlOkTI2PNs'
        doc_req_uri = self.request_uri + doc_id
        response = requests.get(doc_req_uri)
        self.assertEqual(200, response.status_code)
        actual_data = response.json()
        
        with open(os.path.join(self.data_dir, doc_id + '_expected.json'), 'r') as file:
            expected_data = json.load(file)
            self.assertEqual(expected_data, actual_data)


if __name__ == "__main__":
    unittest.main()