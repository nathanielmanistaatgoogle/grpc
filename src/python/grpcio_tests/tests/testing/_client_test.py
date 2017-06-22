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
from grpc.framework.foundation import logging_pool
from tests.unit.framework.common import test_constants
import grpc_testing

from tests.testing import _application_common
from tests.testing import _application_testing_common
from tests.testing import _client_application


class ClientTest(unittest.TestCase):

    def setUp(self):
        self._application_thread_pool = logging_pool.pool(1)
        self._fake_time = grpc_testing.fake_time(time.time())
        self._real_time = grpc_testing.real_time()
        self._fake_time_fixture = (
            grpc_testing.channel_fixture_from_descriptions(
                iter(_application_testing_common.DESCRIPTIONS),
                self._fake_time))
        self._real_time_fixture = (
            grpc_testing.channel_fixture_from_descriptions(
                _application_testing_common.DESCRIPTIONS, self._real_time))

    def tearDown(self):
        self._application_thread_pool.shutdown(wait=True)

    def test_successful_unary_unary(self):
        application_future = self._application_thread_pool.submit(
            _client_application.run, _client_application.Scenario.UNARY_UNARY,
            self._real_time_fixture.channel())
        rpc = self._real_time_fixture.take_rpc_by_service_and_method_names(
            _application_common.SERVICE_NAME,
            _application_common.UNARY_UNARY_METHOD_NAME)
        rpc.invocation_metadata()
        request = rpc.take_request_as_message()
        rpc.no_more_requests()
        rpc.initial_metadata(())
        rpc.add_responses_as_messages(
            (_application_common.UNARY_UNARY_RESPONSE,))
        rpc.terminate((), grpc.StatusCode.OK, '')
        application_return_value = application_future.result()

        self.assertEqual(_application_common.UNARY_UNARY_REQUEST, request)
        self.assertIs(application_return_value.kind,
                      _client_application.Outcome.Kind.SATISFACTORY)

    def test_successful_unary_stream(self):
        application_future = self._application_thread_pool.submit(
            _client_application.run, _client_application.Scenario.UNARY_STREAM,
            self._fake_time_fixture.channel())
        rpc = self._fake_time_fixture.take_rpc_by_service_and_method_names(
            _application_common.SERVICE_NAME,
            _application_common.UNARY_STREAM_METHOD_NAME)
        request = rpc.take_request_as_message()
        rpc.no_more_requests()
        rpc.initial_metadata(())
        rpc.terminate((), grpc.StatusCode.OK, '')
        application_return_value = application_future.result()

        self.assertEqual(_application_common.UNARY_STREAM_REQUEST, request)
        self.assertIs(application_return_value.kind,
                      _client_application.Outcome.Kind.SATISFACTORY)

    def test_successful_stream_unary(self):
        application_future = self._application_thread_pool.submit(
            _client_application.run, _client_application.Scenario.STREAM_UNARY,
            self._real_time_fixture.channel())
        rpc = self._real_time_fixture.take_rpc_by_service_and_method_names(
            _application_common.SERVICE_NAME,
            _application_common.STREAM_UNARY_METHOD_NAME)
        rpc.initial_metadata(())
        first_request = rpc.take_request_as_message()
        second_request = rpc.take_request_as_message()
        third_request = rpc.take_request_as_message()
        rpc.add_responses_as_messages(
            (_application_common.STREAM_UNARY_RESPONSE,))
        rpc.terminate((), grpc.StatusCode.OK, '')
        application_return_value = application_future.result()

        self.assertEqual(_application_common.STREAM_UNARY_REQUEST,
                         first_request)
        self.assertEqual(_application_common.STREAM_UNARY_REQUEST,
                         second_request)
        self.assertEqual(_application_common.STREAM_UNARY_REQUEST,
                         third_request)
        self.assertIs(application_return_value.kind,
                      _client_application.Outcome.Kind.SATISFACTORY)

    def test_successful_stream_stream(self):
        application_future = self._application_thread_pool.submit(
            _client_application.run, _client_application.Scenario.STREAM_STREAM,
            self._fake_time_fixture.channel())
        rpc = self._fake_time_fixture.take_rpc_by_service_and_method_names(
            _application_common.SERVICE_NAME,
            _application_common.STREAM_STREAM_METHOD_NAME)
        observed_invocation_metadata = rpc.invocation_metadata()
        first_request = rpc.take_request_as_message()
        rpc.add_responses_as_messages(
            _application_common.TWO_STREAM_STREAM_RESPONSES)
        second_request = rpc.take_request_as_message()
        rpc.add_responses_as_messages(
            _application_common.TWO_STREAM_STREAM_RESPONSES)
        rpc.no_more_requests()
        rpc.terminate((), grpc.StatusCode.OK, '')
        application_return_value = application_future.result()

        self.assertEqual(_application_common.STREAM_STREAM_REQUEST,
                         first_request)
        self.assertEqual(_application_common.STREAM_STREAM_REQUEST,
                         second_request)
        self.assertIs(application_return_value.kind,
                      _client_application.Outcome.Kind.SATISFACTORY)

    def test_concurrent_stream_stream(self):
        application_future = self._application_thread_pool.submit(
            _client_application.run,
            _client_application.Scenario.CONCURRENT_STREAM_STREAM,
            self._real_time_fixture.channel())
        rpcs = []
        for _ in range(test_constants.RPC_CONCURRENCY):
            rpcs.append(
                self._real_time_fixture.take_rpc_by_service_and_method_names(
                    _application_common.SERVICE_NAME,
                    _application_common.STREAM_STREAM_METHOD_NAME))
        for rpc in rpcs:
            rpc.invocation_metadata()
        requests = {}
        for rpc in rpcs:
            requests[rpc] = [rpc.take_request_as_message()]
        for rpc in rpcs:
            rpc.add_responses_as_messages(
                _application_common.TWO_STREAM_STREAM_RESPONSES)
        for rpc in rpcs:
            requests[rpc].append(rpc.take_request_as_message())
        for rpc in rpcs:
            rpc.add_responses_as_messages(
                _application_common.TWO_STREAM_STREAM_RESPONSES)
        for rpc in rpcs:
            rpc.no_more_requests()
        for rpc in rpcs:
            rpc.terminate((), grpc.StatusCode.OK, '')
        application_return_value = application_future.result()

        for requests_of_one_rpc in requests.values():
            for request in requests_of_one_rpc:
                self.assertEqual(_application_common.STREAM_STREAM_REQUEST,
                                 request)
        self.assertIs(application_return_value.kind,
                      _client_application.Outcome.Kind.SATISFACTORY)

    def test_cancelled_unary_unary(self):
        application_future = self._application_thread_pool.submit(
            _client_application.run,
            _client_application.Scenario.CANCEL_UNARY_UNARY,
            self._fake_time_fixture.channel())
        rpc = self._fake_time_fixture.take_rpc_by_service_and_method_names(
            _application_common.SERVICE_NAME,
            _application_common.UNARY_UNARY_METHOD_NAME)
        request = rpc.take_request_as_message()
        rpc.no_more_requests()
        rpc.initial_metadata(())
        rpc.cancelled()
        application_return_value = application_future.result()

        self.assertEqual(_application_common.UNARY_UNARY_REQUEST, request)
        self.assertIs(application_return_value.kind,
                      _client_application.Outcome.Kind.SATISFACTORY)

    def test_status_stream_unary(self):
        application_future = self._application_thread_pool.submit(
            _client_application.run,
            _client_application.Scenario.CONCURRENT_STREAM_UNARY,
            self._fake_time_fixture.channel())
        rpcs = tuple(
            self._fake_time_fixture.take_rpc_by_service_and_method_names(
                _application_common.SERVICE_NAME,
                _application_common.STREAM_UNARY_METHOD_NAME)
            for _ in range(test_constants.THREAD_CONCURRENCY))
        for rpc in rpcs:
            rpc.take_request_as_message()
            rpc.take_request_as_message()
            rpc.take_request_as_message()
            rpc.no_more_requests()
            rpc.initial_metadata((('my_metadata_key', 'My Metadata Value!',),))
            rpc.add_responses_as_messages(
                (_application_common.STREAM_UNARY_RESPONSE,))
        for rpc in rpcs[:-1]:
            rpc.terminate((), grpc.StatusCode.OK, '')
        rpcs[-1].terminate((), grpc.StatusCode.RESOURCE_EXHAUSTED,
                           'nope; not able to handle all those RPCs!')
        application_return_value = application_future.result()

        self.assertIs(application_return_value.kind,
                      _client_application.Outcome.Kind.UNSATISFACTORY)

    def test_status_stream_stream(self):
        code = grpc.StatusCode.DEADLINE_EXCEEDED
        details = 'test deadline exceeded!'

        application_future = self._application_thread_pool.submit(
            _client_application.run, _client_application.Scenario.STREAM_STREAM,
            self._real_time_fixture.channel())
        rpc = self._real_time_fixture.take_rpc_by_service_and_method_names(
            _application_common.SERVICE_NAME,
            _application_common.STREAM_STREAM_METHOD_NAME)
        observed_invocation_metadata = rpc.invocation_metadata()
        first_request = rpc.take_request_as_message()
        rpc.add_responses_as_messages(
            _application_common.TWO_STREAM_STREAM_RESPONSES)
        second_request = rpc.take_request_as_message()
        rpc.add_responses_as_messages(
            _application_common.TWO_STREAM_STREAM_RESPONSES)
        rpc.no_more_requests()
        rpc.terminate((), code, details)
        application_return_value = application_future.result()

        self.assertEqual(_application_common.STREAM_STREAM_REQUEST,
                         first_request)
        self.assertEqual(_application_common.STREAM_STREAM_REQUEST,
                         second_request)
        self.assertIs(application_return_value.kind,
                      _client_application.Outcome.Kind.RPC_ERROR)
        self.assertIs(application_return_value.code, code)
        self.assertEqual(application_return_value.details, details)

    def test_misbehaving_server_unary_unary(self):
        application_future = self._application_thread_pool.submit(
            _client_application.run, _client_application.Scenario.UNARY_UNARY,
            self._fake_time_fixture.channel())
        rpc = self._fake_time_fixture.take_rpc_by_service_and_method_names(
            _application_common.SERVICE_NAME,
            _application_common.UNARY_UNARY_METHOD_NAME)
        request = rpc.take_request_as_message()
        rpc.no_more_requests()
        rpc.initial_metadata(())
        rpc.add_responses_as_messages(
            (_application_common.ERRONEOUS_UNARY_UNARY_RESPONSE,))
        rpc.terminate((), grpc.StatusCode.OK, '')
        application_return_value = application_future.result()

        self.assertEqual(_application_common.UNARY_UNARY_REQUEST, request)
        self.assertIs(application_return_value.kind,
                      _client_application.Outcome.Kind.UNSATISFACTORY)

    def test_misbehaving_server_stream_stream(self):
        application_future = self._application_thread_pool.submit(
            _client_application.run, _client_application.Scenario.STREAM_STREAM,
            self._real_time_fixture.channel())
        rpc = self._real_time_fixture.take_rpc_by_service_and_method_names(
            _application_common.SERVICE_NAME,
            _application_common.STREAM_STREAM_METHOD_NAME)
        observed_invocation_metadata = rpc.invocation_metadata()
        first_request = rpc.take_request_as_message()
        rpc.add_responses_as_messages(
            (_application_common.STREAM_STREAM_RESPONSE,) * 3)
        second_request = rpc.take_request_as_message()
        rpc.add_responses_as_messages(
            (_application_common.STREAM_STREAM_RESPONSE,) * 3)
        rpc.no_more_requests()
        rpc.terminate((), grpc.StatusCode.OK, '')
        application_return_value = application_future.result()

        self.assertEqual(_application_common.STREAM_STREAM_REQUEST,
                         first_request)
        self.assertEqual(_application_common.STREAM_STREAM_REQUEST,
                         second_request)
        self.assertIs(application_return_value.kind,
                      _client_application.Outcome.Kind.UNSATISFACTORY)

    def test_infinite_request_stream_real_time(self):
        application_future = self._application_thread_pool.submit(
            _client_application.run,
            _client_application.Scenario.INFINITE_REQUEST_STREAM,
            self._real_time_fixture.channel())
        rpc = self._real_time_fixture.take_rpc_by_service_and_method_names(
            _application_common.SERVICE_NAME,
            _application_common.STREAM_UNARY_METHOD_NAME)
        rpc.initial_metadata(())
        first_request = rpc.take_request_as_message()
        second_request = rpc.take_request_as_message()
        third_request = rpc.take_request_as_message()
        self._real_time.sleep_for(
            _application_common.INFINITE_REQUEST_STREAM_TIMEOUT)
        rpc.terminate((), grpc.StatusCode.DEADLINE_EXCEEDED, '')
        application_return_value = application_future.result()

        self.assertEqual(_application_common.STREAM_UNARY_REQUEST,
                         first_request)
        self.assertEqual(_application_common.STREAM_UNARY_REQUEST,
                         second_request)
        self.assertEqual(_application_common.STREAM_UNARY_REQUEST,
                         third_request)
        self.assertIs(application_return_value.kind,
                      _client_application.Outcome.Kind.SATISFACTORY)


if __name__ == '__main__':
    unittest.main(verbosity=2)
