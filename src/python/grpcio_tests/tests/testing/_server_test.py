# Copyright 2017 gRPC authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import time
import unittest

import grpc
from tests.unit.framework.common import test_constants
import grpc_testing

from tests.testing import _application_common
from tests.testing import _application_testing_common
from tests.testing import _server_application


class FirstServiceServicerTest(unittest.TestCase):

    def setUp(self):
        self._real_time = grpc_testing.real_time()
        self._fake_time = grpc_testing.fake_time(time.time())
        self._real_time_server = (
            grpc_testing.server_from_map({
                _server_application.FirstServiceServicer():
                _application_testing_common.FIRST_SERVICE,
            }, self._real_time))
        self._fake_time_server = (
            grpc_testing.server_fixture_from_descriptions({
                _server_application.FirstServiceServicer():
                _application_testing_common.FIRST_SERVICE,
            }, self._fake_time))

    def test_successful_unary_unary(self):
        rpc = self._real_time_server.invoke_unary_unary(
            _application_testing_common.FIRST_SERVICE_UNUN, (),
            _application_common.UNARY_UNARY_REQUEST, None)
        initial_metadata = rpc.get_initial_metadata()
        response, trailing_metadata, code, details = rpc.terminate()

        self.assertEqual(_application_common.UNARY_UNARY_RESPONSE, response)
        self.assertIs(code, grpc.StatusCode.OK)

    def test_successful_unary_stream(self):
        rpc = self._real_time_server.invoke_unary_stream(
            _application_testing_common.FIRST_SERVICE_UNSTRE, (),
            _application_common.UNARY_STREAM_REQUEST, None)
        initial_metadata = rpc.get_initial_metadata()
        trailing_metadata, code, details = rpc.terminate()

        self.assertIs(code, grpc.StatusCode.OK)

    def test_successful_stream_unary(self):
        rpc = self._real_time_server.invoke_stream_unary(
            _application_testing_common.FIRST_SERVICE_STREUN, (), None)
        rpc.send_request(_application_common.STREAM_UNARY_REQUEST)
        rpc.send_request(_application_common.STREAM_UNARY_REQUEST)
        rpc.send_request(_application_common.STREAM_UNARY_REQUEST)
        rpc.no_more_requests()
        initial_metadata = rpc.get_initial_metadata()
        response, trailing_metadata, code, details = rpc.terminate()

        self.assertEqual(_application_common.STREAM_UNARY_RESPONSE, response)
        self.assertIs(code, grpc.StatusCode.OK)

    def test_successful_stream_stream(self):
        rpc = self._real_time_server.invoke_stream_stream(
            _application_testing_common.FIRST_SERVICE_STRESTRE, (), None)
        rpc.send_request(_application_common.STREAM_STREAM_REQUEST)
        initial_metadata = rpc.get_initial_metadata()
        responses = [
            rpc.take_response(),
            rpc.take_response(),
        ]
        rpc.send_request(_application_common.STREAM_STREAM_REQUEST)
        rpc.send_request(_application_common.STREAM_STREAM_REQUEST)
        responses.extend((
            rpc.take_response(),
            rpc.take_response(),
            rpc.take_response(),
            rpc.take_response(),
        ))
        rpc.no_more_requests()
        trailing_metadata, code, details = rpc.terminate()

        for response in responses:
            self.assertEqual(_application_common.STREAM_STREAM_RESPONSE,
                             response)
        self.assertIs(code, grpc.StatusCode.OK)

    def test_misbehaving_client_unary_unary(self):
        rpc = self._real_time_server.invoke_unary_unary(
            _application_common.FIRST_SERVICE_UNUN, (),
            _application_common.ERRONEOUS_UNARY_UNARY_REQUEST, None)
        initial_metadata = rpc.get_initial_metadata()
        response, trailing_metadata, code, details = rpc.terminate()

        self.assertIsNot(code, grpc.StatusCode.OK)

    def test_infinite_request_stream_real_time(self):
        rpc = self._real_time_server.invoke_stream_unary(
            _application_testing_common.FIRST_SERVICE_STREUN, (),
            _application_common.INFINITE_REQUEST_STREAM_TIMEOUT)
        rpc.send_request(_application_common.STREAM_UNARY_REQUEST)
        rpc.send_request(_application_common.STREAM_UNARY_REQUEST)
        rpc.send_request(_application_common.STREAM_UNARY_REQUEST)
        initial_metadata = rpc.get_initial_metadata()
        self._real_time.sleep_for(
            _application_common.INFINITE_REQUEST_STREAM_TIMEOUT * 2)
        rpc.send_request(_application_common.STREAM_UNARY_REQUEST)
        response, trailing_metadata, code, details = rpc.terminate()

        self.assertIs(code, grpc.StatusCode.DEADLINE_EXCEEDED)

    def test_infinite_request_stream_fake_time(self):
        rpc = self._fake_time_server.invoke_stream_unary(
            _application_testing_common.FIRST_SERVICE_STREUN, (),
            _application_common.INFINITE_REQUEST_STREAM_TIMEOUT)
        rpc.send_request(_application_common.STREAM_UNARY_REQUEST)
        rpc.send_request(_application_common.STREAM_UNARY_REQUEST)
        rpc.send_request(_application_common.STREAM_UNARY_REQUEST)
        initial_metadata = rpc.get_initial_metadata()
        self._fake_time.sleep_for(
            _application_common.INFINITE_REQUEST_STREAM_TIMEOUT * 2)
        rpc.send_request(_application_common.STREAM_UNARY_REQUEST)
        rpc.send_request(_application_common.STREAM_UNARY_REQUEST)
        response, trailing_metadata, code, details = rpc.terminate()

        self.assertIs(code, grpc.StatusCode.DEADLINE_EXCEEDED)


if __name__ == '__main__':
    unittest.main(verbosity=2)
