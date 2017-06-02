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

"""An example gRPC Python-using client-side application."""

import grpc

from tests.testing.proto import requests_pb2
from tests.testing.proto import services_pb2

SERVICE_NAME = 'tests_of_grpc_testing.FirstService'
METHOD_NAME = 'StreStre'
REQUEST = requests_pb2.Top(first_top_field=77)
RESPONSE = services_pb2.Bottom(first_bottom_field=88)


class _Pipe(object):

    def __init__(self):
        self._condition = threading.Condition()
        self._values = []
        self._open = True

    def __iter__(self):
        return self

    def _next(self):
        with self._condition:
            while not self._values and self._open:
                self._condition.wait()
                if self._values:
                    return self._values.pop(0)
                else:
                    raise StopIteration()
    
    def __next__(self):  # (Python 3 Iterator Protocol)
        return self._next()
    
    def next(self):  # (Python 2 Iterator Protocol)
        return self._next()

    def add(self, value):
        with self._condition:
            self._values.append(value)
            self._condition.notify()

    def close(self):
        with self._condition:
            self._open = False
            self._condition.notify()


def run(channel):
    stub = services_pb2.FirstServiceStub(channel)
    request_pipe = _Pipe()
    response_iterator = stub.StreStre(request_pipe)
    request_pipe.add(REQUEST)
    first_two_responses = next(response_iterator), next(response_iterator),
    request_pipe.add(REQUEST)
    second_two_responses = next(response_iterator), next(response_iterator),
    request_pipe.close()
    try:
        third_two_responses = next(response_iterator), next(response_iterator)
    except StopIteration:
        third_two_responses = None
    return (
        first_two_responses == (RESPONSE, RESPONSE) and
        second_two_responses == (RESPONSE, RESPONSE) and
        third_two_responses is None)
