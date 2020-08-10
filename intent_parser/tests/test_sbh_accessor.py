from http import HTTPStatus
from intent_parser.accessor.sbh_accessor import SBHAccessor
from intent_parser.intent_parser_sbh import IntentParserSBH
import intent_parser.constants.intent_parser_constants as ip_constants
import json
import unittest
import os

class SBHAccessorTest(unittest.TestCase):

    def setUp(self):
        self.sbh = SBHAccessor(sbh_url='https://hub.sd2e.org/user/sd2e')
        credential_file = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                       '../accessor/intent_parser_api_keys.json')

        with open(credential_file, 'r') as file:
            content = json.load(file)
            self.sbh.login(content['sbh_username'], content['sbh_password'])

    def tearDown(self):
        self.sbh.stop()

    def test_sbh_query_response(self):

        target_collection = '%s/user/%s/experiment_test/experiment_test_collection/1' % (
                            'https://hub.sd2e.org', 'https://hub.sd2e.org/user/sd2e/design/design_collection/1')

        query = """
                PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
                PREFIX sbol: <http://sbols.org/v2#>
                PREFIX sd2: <http://sd2e.org#>
                PREFIX prov: <http://www.w3.org/ns/prov#>
                PREFIX dcterms: <http://purl.org/dc/terms/>
                SELECT DISTINCT ?entity ?timestamp ?title WHERE {
                        <%s> sbol:member ?entity .
                        ?entity rdf:type sbol:Experiment .
                        ?entity dcterms:created ?timestamp .
                        ?entity dcterms:title ?title
                }
                """ % (target_collection)
        response = self.sbh.sparqlQuery(query)
        self.assertEqual(HTTPStatus.OK, response.status_code)
        content = response.json()
        self.assertTrue('results' in content)



if __name__ == '__main__':
    unittest.main()