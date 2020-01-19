from test_generate_structured_request import GenerateStruturedRequestTest
from test_integration_ips import IntegrationIpsTest
from test_integration_sbh import IntegrationSbhTest 
from test_measurement_table import MeasurementTableTest
from test_table_utils import TableUtilsTest 
from test_unit_ips_analyze_sd2dict import IpsAnalyzeSd2dictTest
from test_unit_ips_generate import IpsGenerateTest
from test_unit_ips_spellcheck import IpsSpellcheckTest
from test_unit_ips_utils import IpsUtilsTest

def suite():
    suite = unittest.TestSuite()
    suite.addTest(GenerateStruturedRequestTest)
    suite.addTest(IntegrationIpsTest)
    suite.addTest(IntegrationSbhTest)
    suite.addTest(IpsAnalyzeSd2dictTest)
    suite.addTest(IpsSpellcheckTest)
    suite.addTest(IpsUtilsTest)
    suiteTest(IpsGenerateTest)
    suite.addTest(MeasurementTableTest)
    suite.addTest(TableUtilsTest)
    return suite


if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.run(suite())