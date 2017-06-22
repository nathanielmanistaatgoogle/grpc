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

from grpc.framework.foundation import logging_pool
import grpc_testing

from grpc.tests.testing import _application_common
from grpc.tests.testing import _application_testing_common
from grpc.tests.testing import _client_application
from grpc.tests.testing import _server_application


class ConnectionTest(unittest.TestCase):

    def setUp(self):
        self._application_thread_pool = logging_pool.pool(1)
        self._fake_time = grpc_testing.fake_time(time.time())
        self._real_time = grpc_testing.real_time()
        self._fake_time_connection = (
            grpc_testing.connection_from_descriptions(
                {_server_application.Servicer():
                 _application_testing_common.FIRST_SERVICE},
                self._fake_time))
        self._real_time_connection = (
            grpc_testing.connection_from_descriptions(
                {_server_application.Servicer():
                 _application_testing_common.FIRST_SERVICE},
                self._real_time))

    def tearDown(self):
        self._application_thread_pool.shutdown(wait=True)

    def test_successful_unary_unary(self):
        application_future = self._application_thread_pool.submit(
            _client_application.run, _client_application.Scenario.UNARY_UNARY,
            self._real_time_connection.channel())
        application_return_value = application_future.result()

        self.assertIs(
            application_return_value.kind,
            _client_application.Outcome.Kind.SATISFACTORY)

    def test_successful_unary_stream(self):
        application_future = self._application_thread_pool.submit(
            _client_application.run, _client_application.Scenario.UNARY_STREAM,
            self._real_time_connection.channel())
        application_return_value = application_future.result()

        self.assertIs(
            application_return_value.kind,
            _client_application.Outcome.Kind.SATISFACTORY)

    def test_successful_stream_unary(self):
        application_future = self._application_thread_pool.submit(
            _client_application.run, _client_application.Scenario.STREAM_UNARY,
            self._real_time_connection.channel())
        application_return_value = application_future.result()

        self.assertIs(
            application_return_value.kind,
            _client_application.Outcome.Kind.SATISFACTORY)

    def test_successful_stream_stream(self):
        application_future = self._application_thread_pool.submit(
            _client_application.run, _client_application.Scenario.STREAM_STREAM,
            self._real_time_connection.channel())
        application_return_value = application_future.result()

        self.assertIs(
            application_return_value.kind,
            _client_application.Outcome.Kind.SATISFACTORY)

    def test_concurrent_stream_stream(self):
        application_future = self._application_thread_pool.submit(
            _client_application.run,
            _client_application.Scenario.CONCURRENT_STREAM_STREAM,
            self._real_time_connection.channel())
        application_return_value = application_future.result()

        self.assertIs(
            application_return_value.kind,
            _client_application.Outcome.Kind.SATISFACTORY)

    def test_infinite_request_stream_real_time(self):
        application_future = self._application_thread_pool.submit(
            _client_application.run,
            _client_application.Scenario.INFINITE_REQUEST_STREAM,
            self._real_time_connection.channel())
        application_return_value = application_future.result()

        self.assertIs(
            application_return_value.kind,
            _client_application.Outcome.Kind.SATISFACTORY)

    def test_infinite_request_stream_fake_time(self):
        application_future = self._application_thread_pool.submit(
            _client_application.run,
            _client_application.Scenario.INFINITE_REQUEST_STREAM,
            self._fake_time_connection.channel())
        self._fake_time.sleep_for(
            _application_common.INFINITE_REQUEST_STREAM_TIMEOUT)
        application_return_value = application_future.result()

        self.assertIs(
            application_return_value.kind,
            _client_application.Outcome.Kind.SATISFACTORY)


if __name__ == '__main__':
    unittest.main(verbosity=2)
