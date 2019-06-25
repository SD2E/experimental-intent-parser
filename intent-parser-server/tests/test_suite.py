#!/usr/bin/env python3

import unittest, os, sys

try:
    from intent_parser_server import IntentParserServer
except Exception as e:
    sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)),'../src'))
    from intent_parser_server import IntentParserServer

def suite():
    loader = unittest.TestLoader()
    tests_dir = os.path.dirname(os.path.realpath(__file__))
    suite = loader.discover(tests_dir)
    return suite

if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.run(suite())