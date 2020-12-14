from flask import jsonify, make_response
from http import HTTPStatus

def handle_intent_parser_errors(error):
    message = error.get_message()
    res = jsonify(errors=[message],
                  warnings=[])
    return make_response(res, HTTPStatus.INTERNAL_SERVER_ERROR)

def handle_request_errors(error):
    status_code = error.get_http_status()
    res = jsonify(errors=error.get_errors(),
                  warnings=error.get_warnings())
    return make_response(res, status_code)