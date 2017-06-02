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

"""Fixtures for use in testing gRPC Python-using application code."""

import abc
import collections

import grpc
import six

# TODO(nathaniel): better name than "fixture"? "Manager"? "Master"?


class Method(six.with_metaclass(abc.ABCMeta)):
    """A description of an RPC method.

    Attributes:
      name: The method name.
      request_class: The class of the method's requests.
      response_class: The class of the method's responses.
      request_unary: True if the method requires exactly one request
        message being sent per RPC; False otherwise.
      response_unary: True if the method requires exactly one response
        message being sent per RPC; False otherwise.
    """


class Service(six.with_metaclass(abc.ABCMeta)):
    """A description of an RPC service.

    Attributes:
      name: The service name.
      methods: A sequence of Methods describing the service's methods.
    """


class ChannelRPC(six.with_metaclass(abc.ABCMeta)):
    """"""

    @abc.abstractmethod
    def invocation_metadata(self):
        """"""
        raise NotImplementedError()

    @abc.abstractmethod
    def initial_metadata(self, metadata):
        """"""
        raise NotImplementedError()

    @abc.abstractmethod
    def take_request_as_message(self):
        """"""
        raise NotImplementedError()

    @abc.abstractmethod
    def add_responses_as_messages(self, responses):
        """"""
        raise NotImplementedError()

    @abc.abstractmethod
    def no_more_requests(self):
        """"""
        raise NotImplementedError()

    @abc.abstractmethod
    def cancelled(self):
        """"""
        raise NotImplementedError()
    
    @abc.abstractmethod
    def terminate(self, metadata, code, details):
        """"""
        raise NotImplementedError()


class ChannelFixture(six.with_metaclass(abc.ABCMeta)):
    """"""

    @abc.abstractmethod
    def get_channel(self):
        """"""
        raise NotImplementedError()

    @abc.abstractmethod
    def take_rpc_by_descriptor(self, descriptor):
        """"""
        raise NotImplementedError()


# TODO(google/protobuf/3167, google/protobuf/3168): Eliminate this and
# use Descriptor objects instead.
class Method(six.with_metaclass(abc.ABCMeta)):
    """A description of an RPC method.

    Attributes:
      name: The method name.
      request_class: The class of the method's requests.
      response_class: The class of the method's responses.
      request_unary: True if the method requires exactly one request
        message being sent per RPC; False otherwise.
      response_unary: True if the method requires exactly one response
        message being sent per RPC; False otherwise.
    """


# TODO(google/protobuf 3167, google/protobuf 3168): Eliminate this and
# use Descriptor objects instead.
class Service(six.with_metaclass(abc.ABCMeta)):
    """A description of an RPC service.

    Attributes:
      name: The service name.
      methods: A sequence of Methods describing the service's methods.
    """


class _Method(
        Method,
        collections.namedtuple(
            '_Method',
            ('name', 'request_class', 'response_class', 'request_unary',
             'response_unary',))):
    pass


class _Service(
        Service, collections.namedtuple('_Service', ('name', 'methods',))):
    pass


def method(name, request_class, response_class, request_unary, response_unary):
    """Creates a Method from the given parameters."""
    return _Method(
        name, request_class, response_class, request_unary, response_unary)


def service(name, methods):
    """Creates a Service from the given parameters."""
    return _Service(name, methods)


def channel_fixture_from_descriptions(descriptions):
    """"""
    from grpc_testing import _channel
    return _channel.fixture_from_descriptions(descriptions)
