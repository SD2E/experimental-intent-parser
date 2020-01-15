from test_get_generated_structured_request import TestGETGeneratedStruturedRequest
from test_measurement_table import MeasurementTableTest
from test_table_utils import TableUtilsTest 


def suite():
    suite = unittest.TestSuite()
    suite.addTest(TestGETGeneratedStruturedRequest)
    suite.addTest(MeasurementTableTest)
    suite.addTest(TableUtilsTest)
    return suite


if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.run(suite())