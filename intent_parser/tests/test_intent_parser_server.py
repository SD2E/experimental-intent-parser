from intent_parser.server.intent_parser_processor import IntentParserProcessor
from unittest.mock import Mock, patch
import intent_parser.server.intent_parser_server as ip_server
import pytest
import unittest

@pytest.fixture(scope='module')
def test_client():
    flask_app = ip_server.main()

    # Flask provides a way to test your application by exposing the Werkzeug test Client
    # and handling the context locals for you.
    testing_client = flask_app.test_client()

    # Establish an application context before running the tests.
    ctx = flask_app.app_context()
    ctx.push()

    yield testing_client  # this is where the testing happens!

    ctx.pop()

def test_status(test_client):
    """
    GIVEN a Flask application
    WHEN the '/' page is requested (GET)
    THEN check the response is valid
    """
    response = test_client.get('/status')
    assert response.status_code == 200
    assert b"Intent Parser Server is Up and Running" in response.data


if __name__ == "__main__":
    unittest.main()