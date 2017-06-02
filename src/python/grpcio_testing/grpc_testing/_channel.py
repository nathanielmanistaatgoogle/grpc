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

"""Channel fixtures."""

import collections
import threading

import grpc
import grpc_testing


class _RPCState(object):

    def __init__(self):
        self.condition = threading.Condition()


class _ChannelState(object):

    def __init__(self):
        self.lock = threading.Lock()
        self.rpc_states = collections.defaultdict(list)


class _StreamStreamMultiCallable(grpc.StreamStreamMultiCallable):

    def __call__(
            self, request_iterator, timeout=None, metadata=None,
            credentials=None):
        
        

class _Channel(grpc.Channel):

    def __init__(self, state):
        self._state = state

    def subscribe(self, callback, try_to_connect=False):
        raise NotImplementedError()

    def unsubscribe(self, callback):
        raise NotImplementedError()

    def unary_unary(
            self, method, request_serializer=None, request_deserializer=None):
        raise NotImplementedError()

    def unary_stream(
            self, method, request_serializer=None, request_deserializer=None):
        raise NotImplementedError()

    def stream_unary(
            self, method, request_serializer=None, request_deserializer=None):
        raise NotImplementedError()

    def stream_stream(
            self, method, request_serializer=None, request_deserializer=None):
        raise NotImplementedError()


class _ChannelRPC(grpc_testing.ChannelRPC):
    """"""

    def invocation_metadata(self):
        """"""
        raise NotImplementedError()
    
    def initial_metadata(self, metadata):
        """"""
        raise NotImplementedError()

    def take_request_as_message(self):
        """"""
        raise NotImplementedError()

    def add_responses_as_messages(self, responses):
        """"""
        raise NotImplementedError()

    def no_more_requests(self):
        pass

    def cancelled(self):
        raise NotImplementedError()

    def terminate(self, metadata, code, details):
        """"""
        raise NotImplementedError()


class _ChannelFixture(grpc_testing.ChannelFixture):

    def __init__(self, descriptions):
        self._descriptions = descriptions
        self._state = _ChannelState()

    def get_channel(self):
        return _Channel(self._state)

    def take_rpc_by_descriptor(self, descriptor):
        raise NotImplementedError()


def fixture_from_descriptions(descriptions):
    """"""
    return _ChannelFixture(descriptions)
