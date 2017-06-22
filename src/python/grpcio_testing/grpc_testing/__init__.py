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
"""Fixtures for use in testing gRPC Python-using application code."""

import abc
import collections

import grpc
import six


class ChannelRpc(six.with_metaclass(abc.ABCMeta)):
    """Fixture for an in-progress RPC invoked by a system under test.

    Enables users to "play a server" for such RPCs by reading requests,
    supplying responses, and supplying status.
    """

    @abc.abstractmethod
    def invocation_metadata(self):
        """Accesses the metadata passed by the system under test.

        Returns:
          The invocation metadata supplied by the system under test at
            RPC-invocation-time.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def initial_metadata(self, initial_metadata):
        """Accepts the initial metadata to be passed to the system under test.

        Args:
          initial_metadata: The RPC's initial metadata to be passed to the
            system under test.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def take_request_as_message(self):
        """Draws one of the requests added to the RPC by the system under test.

        Successive calls to this method return requests in the same order in
        which the system under test added them to the RPC.

        Returns:
          A deserialized request message added to the RPC by the system under
            test.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def add_responses_as_messages(self, responses):
        """Accepts responses to be passed to the system under test.

        Args:
          responses: An iterable of deserialized response messages to be passed
            to the system under test.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def no_more_requests(self):
        """Blocks until the system under test has closed the request stream."""
        raise NotImplementedError()

    @abc.abstractmethod
    def cancelled(self):
        """Blocks until the system under test has cancelled the RPC."""
        raise NotImplementedError()

    @abc.abstractmethod
    def terminate(self, trailing_metadata, code, details):
        """Accepts the RPC's trailing metadata, status code, and status details.

        This method implicitly closes the RPC's response stream and, from the
        perspective of the test code that is "playing server", terminates the
        RPC.
        """
        raise NotImplementedError()


class ChannelFixture(six.with_metaclass(abc.ABCMeta)):
    """Fixture for a channel on which a system under test invokes RPCs."""

    @abc.abstractmethod
    def channel(self):
        """Accesses the grpc.Channel on which the system under test makes RPCs.

        Returns:
          The grpc.Channel on which the system under test should make RPCs.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def take_rpc_by_service_and_method_names(self, service_name, method_name):
        """Draws an RPC currently being made by the system under test.

        If no RPC with the given names is currently being made by the system
        under test, this method blocks until such an RPC is made by the system
        under test.

        This method is mutative; for each RPC made by the system under test
        exactly one ChannelRpc will be returned from this method. If two calls
        to this method are made by test code but only one RPC is invoked by the
        system under test, the second call to this method will block
        indefinitely.

        Args:
          service_name: An RPC service name (such as "my_package.MyService").
          method_name: An RPC method name (such as "MyMethod").

        Returns:
          A ChannelRpc that allows test code to "play server" and interact with
            the system under test.
        """
        raise NotImplementedError()


class ServerRpc(six.with_metaclass(abc.ABCMeta)):
    """Fixture for an in-progress RPC serviced by a system under test.

    Enables users to "play a client" for such RPCs by supplying requests,
    reading responses, and cancelling.
    """

    @abc.abstractmethod
    def initial_metadata(self):
        """Accesses the initial metadata emitted by the system under test.

        This method blocks until the system under test has added initial
        metadata to the RPC (or has provided one or more response messages or
        has terminated the RPC, either of which will cause gRPC Python to
        synthesize initial metadata for the RPC).

        Returns:
          The initial metadata for the RPC.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def add_requests_as_messages(self, requests):
        """Accepts requests to be passed to the system under test.

        Args:
          requests: An iterable of deserialized request messages to be passed
            to the system under test.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def take_response_as_message(self):
        """Draws one of the responses added to the RPC by the system under test.

        Successive calls to this method return responses in the same order in
        which the system under test added them to the RPC.

        Returns:
          A deserialized response message added to the RPC by the system under
            test.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def no_more_requests(self):
        """Indicates the end of the RPC's request stream."""
        raise NotImplementedError()

    @abc.abstractmethod
    def cancel(self):
        """Cancel's the RPC."""
        raise NotImplementedError()

    @abc.abstractmethod
    def terminate(self):
        """Blocks until the system under test has terminated the RPC."""
        raise NotImplementedError()


class ServerFixture(six.with_metaclass(abc.ABCMeta)):
    """Fixture for a server in which a system under test services RPCs."""

    @abc.abstractmethod
    def invoke_rpc_by_service_and_method_names(self, service_name, method_name,
                                               invocation_metadata, requests,
                                               no_more_requests, timeout):
        """Invokes an RPC to be serviced by the system under test.

        Args:
          service_name: An RPC service name (such as "my_package.MyService").
          method_name: An RPC method name (such as "MyMethod").
          invocation_metadata: The metadata supplied at RPC-invocation-time by
            the invoker of the RPC.
          requests: An iterable of request messages with which to start the RPC.
            These are just a start; they need not be all requests that will ever
            be added to the RPC.
          no_more_requests: True if all requests are known and passed in this
            call and the RPC's request stream should be closed; False if test
            code may add more requests later or wishes to hold the request
            stream open until a later time.
          timeout: A duration of time in seconds for the RPC.
        """
        raise NotImplementedError()


class Connection(six.with_metaclass(abc.ABCMeta)):
    """Fixture for testing a system that is both a client and a server."""

    @abc.abstractmethod
    def channel(self):
        """Accesses the grpc.Channel on which the system under test makes RPCs.

        Returns:
          The grpc.Channel on which the system under test should make RPCs.
        """
        raise NotImplementedError()


class Time(six.with_metaclass(abc.ABCMeta)):
    """A simulation of time.

    Implementations needn't be connected with real time as provided by the
    Python interpreter, but as long as systems under test use
    RpcContext.is_active and RpcContext.time_remaining for querying RPC liveness
    implementations may be used to change passage of time in tests.
    """

    @abc.abstractmethod
    def time(self):
        """Accesses the current test time.

        Returns:
          The current test time (over which this object has authority).
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def call_in(self, behavior, delay):
        """Adds a behavior to be called after some time.

        Args:
          behavior: A behavior to be called with no arguments.
          delay: A duration of time in seconds after which to call the behavior.

        Returns:
          A grpc.Future with which the call of the behavior may be cancelled
            before it is executed.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def call_at(self, behavior, time):
        """Adds a behavior to be called at a specific time.

        Args:
          behavior: A behavior to be called with no arguments.
          time: The test time at which to call the behavior.

        Returns:
          A grpc.Future with which the call of the behavior may be cancelled
            before it is executed.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def sleep_for(self, duration):
        """Blocks for some length of test time.

        Args:
          duration: A duration of test time in seconds for which to block.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def sleep_until(self, time):
        """Blocks until some test time.

        Args:
          time: The test time until which to block.
        """
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


class _Method(Method,
              collections.namedtuple('_Method',
                                     ('name', 'request_class', 'response_class',
                                      'request_unary', 'response_unary',))):
    pass


class _Service(Service, collections.namedtuple('_Service',
                                               ('name', 'methods',))):
    pass


def real_time():
    """Creates a Time backed by the Python interpreter's time.

    Returns:
      A Time backed by the "system" (Python interpreter's) time.
    """
    from grpc_testing import _time
    return _time.RealTime()


def fake_time(now):
    """Creates a Time that can be manipulated by test code.

    The returned instance maintains an internal representation of time
    independent of real time. This internal representation only advances
    when user code calls the instance's sleep_for and sleep_until methods.

    Returns:
      A Time that simulates the passage of time.
    """
    from grpc_testing import _time
    return _time.FakeTime(now)


def method(name, request_class, response_class, request_unary, response_unary):
    """Creates a Method from the given parameters.

    Args:
      name: The method name.
      request_class: The class of the method's requests.
      response_class: The class of the method's responses.
      request_unary: True if the method requires exactly one request
        message being sent per RPC; False otherwise.
      response_unary: True if the method requires exactly one response
        message being sent per RPC; False otherwise.

    Returns:
      A Method from the given parameters.
    """
    return _Method(name, request_class, response_class, request_unary,
                   response_unary)


def service(name, methods):
    """Creates a Service from the given parameters.

    Args:
      name: The service name.
      methods: An iterable of Methods describing the service's methods.

    Returns:
      A service from the given parameters.
    """
    return _Service(name, tuple(methods))


def channel_fixture_from_descriptions(descriptions, time):
    """Creates a ChannelFixture for use in tests of a gRPC Python-using system.

    Args:
      descriptions: An iterable of Services describing the RPCs that will be
        made by the system under test.
      time: A Time to be used for tests.

    Returns:
      A ChannelFixture for use in tests.
    """
    from grpc_testing import _channel
    description_sequence = tuple(descriptions)
    return _channel.ChannelFixture(
        description_sequence,
        _channel.ChannelHandler(description_sequence), time)


def server_fixture_from_descriptions(servicers_to_descriptions, time):
    """Creates a ServerFixture for use in tests of a gRPC Python-using system.

    Args:
      servicers_to_descriptions: A dictionary from servicer objects (usually
        instances of classes that implement "Servicer" interfaces defined in
        generated "_pb2_grpc" modules) to Service values describing the RPC
        services implemented by the servicer objects.
      time: A Time to be used for tests.

    Returns:
      A ServerFixture for use in tests.
    """
    from grpc_testing import _server
    return _server.fixture_from_descriptions(servicers_to_descriptions, time)


def connection_from_descriptions(servicers_to_descriptions, time):
    """Creates a Connection for use in tests of a gRPC Python-using system.

    Args:
      servicers_to_descriptions: A dictionary from servicer objects (usually
        instances of classes that implement "Servicer" interfaces defined in
        generated "_pb2_grpc" modules) to Service values describing the RPC
        services implemented by the servicer objects.
      time: A Time to be used for tests.

    Returns:
      A Connection for use in tests in which the system under test is both the
        client-side application and the server-side application involved in
        RPCs.
    """
    from grpc_testing import _connection
    return _connection.from_descriptions(servicers_to_descriptions, time)
