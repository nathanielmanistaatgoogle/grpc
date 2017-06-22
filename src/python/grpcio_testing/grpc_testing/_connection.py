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
"""Connections."""

import threading

import grpc_testing
from grpc_testing import _channel
from grpc_testing import _common
from grpc_testing import _server


class _Pipe(_common.ChannelRpcHandler, _common.ServerRpcHandler):

    def __init__(self, requests, no_more_requests):
        self._condition = threading.Condition()
        self._initial_metadata = None
        self._requests = requests
        self._no_more_requests = no_more_requests
        self._responses = []
        self._cancelled = False
        self._trailing_metadata = None
        self._code = None
        self._details = None

    def initial_metadata(self):
        with self._condition:
            while True:
                if self._initial_metadata is None:
                    if self._code is None and not self._cancelled:
                        self._condition.wait()
                    else:
                        return _common.FUSSED_EMPTY_METADATA
                else:
                    return self._initial_metadata

    def add_request(self, request):
        with self._condition:
            if self._no_more_requests:
                raise ValueError('Request added after request stream closed?')
            elif self._cancelled or self._code is not None:
                return False
            else:
                self._requests.append(request)
                self._condition.notify_all()
                return True

    def no_more_requests(self):
        with self._condition:
            self._no_more_requests = True
            self._condition.notify_all()

    def take_response(self):
        with self._condition:
            while True:
                if self._responses:
                    response = self._responses.pop(0)
                    return _common.ChannelRpcRead(response, None, None, None)
                elif self._code is None:
                    self._condition.wait()
                else:
                    return _common.ChannelRpcRead(None, self._trailing_metadata,
                                                  self._code, self._details)

    def cancel(self, code, details):
        with self._condition:
            self._cancelled = True
            self._condition.notify_all()

    def terminate(self):
        with self._condition:
            while True:
                if self._code is None:
                    self._condition.wait()
                else:
                    return self._trailing_metadata, self._code, self._details,

    def is_active(self):
        with self._condition:
            return not self._cancelled and self._code is None

    def time_remaining(self):
        raise NotImplementedError()

    def add_callback(self, callback):
        raise NotImplementedError()

    def send_initial_metadata(self, initial_metadata):
        with self._condition:
            self._initial_metadata = initial_metadata
            self._condition.notify_all()

    def take_request(self):
        with self._condition:
            while True:
                if self._cancelled or self._code is not None:
                    return _common.TERMINATED
                elif self._requests:
                    request = self._requests.pop(0)
                    self._condition.notify_all()
                    return _common.ServerRpcRead(request, False, False)
                elif self._no_more_requests:
                    return _common.NO_MORE_REQUESTS
                else:
                    self._condition.wait()

    def add_response(self, response):
        with self._condition:
            self._responses.append(response)
            self._condition.notify_all()

    def send_termination(self, trailing_metadata, code, details):
        with self._condition:
            self._trailing_metadata = trailing_metadata
            self._code = code
            self._details = details
            self._condition.notify_all()


class _ChannelHandler(_common.ChannelHandler):

    def __init__(self, server_fixturish):
        self._server_fixturish = server_fixturish

    def invoke_rpc(self, full_name, invocation_metadata, requests,
                   no_more_requests, timeout):
        service_name, method_name = full_name.split('/')[1:3]
        pipe = _Pipe(requests, no_more_requests)
        self._server_fixturish.invoke_rpc_by_service_and_method_names(
            service_name, method_name, pipe, invocation_metadata, timeout)
        return pipe

    def take_rpc(self, full_name):
        raise NotImplementedError()


class _Connection(grpc_testing.Connection):

    def __init__(self, servicers_to_descriptions, time):
        server_fixturish = _server.fixtureish_from_descriptions(
            servicers_to_descriptions, time)
        self._channel_fixture = _channel.ChannelFixture(
            tuple(servicers_to_descriptions),
            _ChannelHandler(server_fixturish), time)

    def channel(self):
        return self._channel_fixture.channel()


def from_descriptions(servicers_to_descriptions, time):
    return _Connection(servicers_to_descriptions, time)
