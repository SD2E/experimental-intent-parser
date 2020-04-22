from strateos_accessor import StrateosAccessor
import intent_parser_constants
import pprint
import unittest


class StrateosAccessorTest(unittest.TestCase):


    def test_get_growth_curve_protocol(self):
        strateos_api = StrateosAccessor()
        protocol = strateos_api.get_protocol(intent_parser_constants.GROWTH_CURVE_PROTOCOL)
        self.assertTrue(protocol)
        pp = pprint.PrettyPrinter(indent=4)
        pp.pprint(protocol)
    
    def test_get_obstacle_course_protocol(self):
        strateos_api = StrateosAccessor()
        protocol = strateos_api.get_protocol(intent_parser_constants.OBSTACLE_COURSE_PROTOCOL)
        self.assertTrue(protocol)
        
    def test_get_time_series_protocol(self):
        strateos_api = StrateosAccessor()
        protocol = strateos_api.get_protocol(intent_parser_constants.TIME_SERIES_HTP_PROTOCOL)
        self.assertTrue(protocol)
        pp = pprint.PrettyPrinter(indent=4)
        pp.pprint(protocol)
       


if __name__ == "__main__":
    unittest.main()