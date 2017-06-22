# Copyright 2017 The gRPC Authors.
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
from grpc.tests.unit.framework.common import test_constants
import grpc_testing

from grpc.tests.testing import _application_common
from grpc.tests.testing import _application_testing_common
from grpc.tests.testing import _server_application


class ServicerTest(unittest.TestCase):

    def setUp(self):
        self._real_time = grpc_testing.real_time()
        self._fake_time = grpc_testing.fake_time(time.time())
        self._real_time_fixture = (
            grpc_testing.server_fixture_from_descriptions(
                {_server_application.Servicer():
                 _application_testing_common.FIRST_SERVICE},
                self._real_time))
        self._fake_time_fixture = (
            grpc_testing.server_fixture_from_descriptions(
                {_server_application.Servicer():
                 _application_testing_common.FIRST_SERVICE},
                self._fake_time))

    def test_successful_unary_unary(self):
        rpc = self._real_time_fixture.invoke_rpc_by_service_and_method_names(
            _application_common.SERVICE_NAME,
            _application_common.UNARY_UNARY_METHOD_NAME,
            (), (_application_common.UNARY_UNARY_REQUEST,), True, None)
        initial_metadata = rpc.initial_metadata()
        response = rpc.take_response_as_message()
        trailing_metadata, code, details = rpc.terminate()

        self.assertEqual(_application_common.UNARY_UNARY_RESPONSE, response)
        self.assertIs(code, grpc.StatusCode.OK)

    def test_successful_unary_stream(self):
        rpc = self._real_time_fixture.invoke_rpc_by_service_and_method_names(
            _application_common.SERVICE_NAME,
            _application_common.UNARY_STREAM_METHOD_NAME,
            (), (_application_common.UNARY_STREAM_REQUEST,), True, None)
        initial_metadata = rpc.initial_metadata()
        trailing_metadata, code, details = rpc.terminate()

        self.assertIs(code, grpc.StatusCode.OK)

    def test_successful_stream_unary(self):
        rpc = self._real_time_fixture.invoke_rpc_by_service_and_method_names(
            _application_common.SERVICE_NAME,
            _application_common.STREAM_UNARY_METHOD_NAME,
            (), (), False, None)
        rpc.add_requests_as_messages(
            (_application_common.STREAM_UNARY_REQUEST,
            _application_common.STREAM_UNARY_REQUEST,))
        rpc.add_requests_as_messages(
            (_application_common.STREAM_UNARY_REQUEST,))
        rpc.no_more_requests()
        initial_metadata = rpc.initial_metadata()
        response = rpc.take_response_as_message()
        trailing_metadata, code, details = rpc.terminate()

        self.assertEqual(_application_common.STREAM_UNARY_RESPONSE, response)
        self.assertIs(code, grpc.StatusCode.OK)

    def test_successful_stream_stream(self):
        rpc = self._real_time_fixture.invoke_rpc_by_service_and_method_names(
            _application_common.SERVICE_NAME,
            _application_common.STREAM_STREAM_METHOD_NAME,
            (), (), False, None)
        rpc.add_requests_as_messages(
            (_application_common.STREAM_STREAM_REQUEST,))
        initial_metadata = rpc.initial_metadata()
        responses = [
            rpc.take_response_as_message(),
            rpc.take_response_as_message(),
        ]
        rpc.add_requests_as_messages((_application_common.STREAM_STREAM_REQUEST,) * 2)
        responses.extend(
            [
                rpc.take_response_as_message(),
                rpc.take_response_as_message(),
                rpc.take_response_as_message(),
                rpc.take_response_as_message(),
            ])
        rpc.no_more_requests()
        trailing_metadata, code, details = rpc.terminate()

        for response in responses:
            self.assertEqual(_application_common.STREAM_STREAM_RESPONSE, response)
        self.assertIs(code, grpc.StatusCode.OK)

    def test_misbehaving_client_unary_unary(self):
        rpc = self._real_time_fixture.invoke_rpc_by_service_and_method_names(
            _application_common.SERVICE_NAME,
            _application_common.UNARY_UNARY_METHOD_NAME,
            (), (_application_common.ERRONEOUS_UNARY_UNARY_REQUEST,), True,
            None)
        initial_metadata = rpc.initial_metadata()
        response = rpc.take_response_as_message()
        trailing_metadata, code, details = rpc.terminate()

        self.assertIsNot(code, grpc.StatusCode.OK)

    def test_infinite_request_stream_real_time(self):
        rpc = self._real_time_fixture.invoke_rpc_by_service_and_method_names(
            _application_common.SERVICE_NAME,
            _application_common.STREAM_UNARY_METHOD_NAME,
            (), (), False, _application_common.INFINITE_REQUEST_STREAM_TIMEOUT)
        rpc.add_requests_as_messages(
            (_application_common.STREAM_UNARY_REQUEST,
            _application_common.STREAM_UNARY_REQUEST,))
        rpc.add_requests_as_messages(
            (_application_common.STREAM_UNARY_REQUEST,))
        initial_metadata = rpc.initial_metadata()
        self._real_time.sleep_for(
            _application_common.INFINITE_REQUEST_STREAM_TIMEOUT * 2)
        rpc.add_requests_as_messages(
            (_application_common.STREAM_UNARY_REQUEST,))
        trailing_metadata, code, details = rpc.terminate()

        self.assertIs(code, grpc.StatusCode.DEADLINE_EXCEEDED)

    def test_infinite_request_stream_fake_time(self):
        rpc = self._fake_time_fixture.invoke_rpc_by_service_and_method_names(
            _application_common.SERVICE_NAME,
            _application_common.STREAM_UNARY_METHOD_NAME,
            (), (), False, _application_common.INFINITE_REQUEST_STREAM_TIMEOUT)
        rpc.add_requests_as_messages(
            (_application_common.STREAM_UNARY_REQUEST,
            _application_common.STREAM_UNARY_REQUEST,))
        rpc.add_requests_as_messages(
            (_application_common.STREAM_UNARY_REQUEST,))
        initial_metadata = rpc.initial_metadata()
        self._fake_time.sleep_for(
            _application_common.INFINITE_REQUEST_STREAM_TIMEOUT * 2)
        rpc.add_requests_as_messages(
            (_application_common.STREAM_UNARY_REQUEST,) *
            test_constants.STREAM_LENGTH)
        trailing_metadata, code, details = rpc.terminate()

        self.assertIs(code, grpc.StatusCode.DEADLINE_EXCEEDED)


if __name__ == '__main__':
    unittest.main(verbosity=2)
