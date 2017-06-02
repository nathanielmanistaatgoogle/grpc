# Copyright 2017, Google Inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
#
#     * Redistributions of source code must retain the above copyright
# notice, this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above
# copyright notice, this list of conditions and the following disclaimer
# in the documentation and/or other materials provided with the
# distribution.
#     * Neither the name of Google Inc. nor the names of its
# contributors may be used to endorse or promote products derived from
# this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import unittest
from concurrent import futures

import grpc_testing

from tests.testing import _client_application
from tests.testing.proto import requests_pb2
from tests.testing.proto import services_pb2

_FIRST_SERVICE_UNUN = grpc_testing.method(
    'UnUn', requests_pb2.Up, services_pb2.Down, True, True)
_FIRST_SERVICE_UNSTRE = grpc_testing.method(
    'UnStre', requests_pb2.Charm, services_pb2.Strange, True, False)
_FIRST_SERVICE_STREUN = grpc_testing.method(
    'StreUn', requests_pb2.Charm, services_pb2.Strange, False, True)
_FIRST_SERVICE_STRESTRE = grpc_testing.method(
    'StreStre', requests_pb2.Top, services_pb2.Bottom, False, False)
_SECOND_SERVICE_UNSTRE = grpc_testing.method(
    'UnStre', services_pb2.Strange, requests_pb2.Charm, True, False)
_FIRST_SERVICE = grpc_testing.service(
    'tests_of_grpc_testing.FirstService',
    (_FIRST_SERVICE_UNUN,
     _FIRST_SERVICE_UNSTRE,
     _FIRST_SERVICE_STREUN,
     _FIRST_SERVICE_STRESTRE,))
_SECOND_SERVICE = grpc_testing.service(
    'tests_of_grpc_testing.SecondService', (_SECOND_SERVICE_UNSTRE,))
_DESCRIPTIONS = (
    _FIRST_SERVICE,
    _SECOND_SERVICE,
)


class ClientTest(unittest.TestCase):

    def setUp(self):
        self._application_thread_pool = futures.ThreadPoolExecutor(
            max_workers=1)
        self._channel_fixture = grpc_testing.channel_fixture_from_descriptions(
            _DESCRIPTIONS)

    def tearDown(self):
        self._application_thread_pool.shutdown(wait=True)

    def test_client_against_correctly_behaving_server(self):
        application_future = self._application_thread_pool.submit(
            _client_application.run, self._channel_fixture.channel())
        rpc = self._channel_fixture.take_rpc_by_service_and_method_names(
            _client_application.SERVICE_NAME, _client_application.METHOD_NAME)
        observed_invocation_metadata = rpc.invocation_metadata()
        first_request = rpc.take_request_as_message()
        rpc.add_responses_as_messages(
            (_client_application.RESPONSE, _client_application.RESPONSE,))
        second_request = rpc.take_request_as_message()
        rpc.add_responses_as_messages(
            (_client_application.RESPONSE, _client_application.RESPONSE,))
        rpc.no_more_requests()
        rpc.terminate((), grpc.StatusCode.OK, '')
        application_return_value = application_future.result()

        self.assertEqual(_client_application.REQUEST, first_request)
        self.assertEqual(_client_application.REQUEST, second_request)
        self.assertTrue(application_return_value)

    def test_client_against_incorrectly_behaving_server(self):
        application_future = self._application_thread_pool.submit(
            _client_application.run, self._channel_fixture.channel())
        rpc = self._channel_fixture.take_rpc_by_service_and_method_names(
            _client_application.SERVICE_NAME, _client_application.METHOD_NAME)
        observed_invocation_metadata = rpc.invocation_metadata()
        first_request = rpc.take_request_as_message()
        rpc.add_responses_as_messages(
            (_client_application.RESPONSE,) * 3)
        second_request = rpc.take_request_as_message()
        rpc.add_responses_as_messages(
            (_client_application.RESPONSE,) * 3)
        rpc.no_more_requests()
        rpc.terminate((), grpc.StatusCode.OK, '')
        application_return_value = application_future.result()

        self.assertEqual(_client_application.REQUEST, first_request)
        self.assertEqual(_client_application.REQUEST, second_request)
        self.assertFalse(application_return_value)


if __name__ == '__main__':
    unittest.main(verbosity=2)
