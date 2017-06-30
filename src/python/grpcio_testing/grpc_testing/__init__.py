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

from google.protobuf import descriptor

import grpc
import six


class UnaryUnaryChannelRpc(six.with_metaclass(abc.ABCMeta)):
    """Fixture for a unary-unary RPC invoked by a system under test.

    Enables users to "play server" for the RPC.
    """

    @abc.abstractmethod
    def send_initial_metadata(self, initial_metadata):
        """Sends the RPC's initial metadata to the system under test.

        Args:
          initial_metadata: The RPC's initial metadata to be "sent" to
            the system under test.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def cancelled(self):
        """Blocks until the system under test has cancelled the RPC."""
        raise NotImplementedError()

    @abc.abstractmethod
    def terminate(self, response, trailing_metadata, code, details):
        """Terminates the RPC.

        Args:
          response: The response for the RPC.
          trailing_metadata: The RPC's trailing metadata.
          code: The RPC's status code.
          details: The RPC's status details.
        """
        raise NotImplementedError()


class UnaryStreamChannelRpc(six.with_metaclass(abc.ABCMeta)):
    """Fixture for a unary-stream RPC invoked by a system under test.

    Enables users to "play server" for the RPC.
    """

    @abc.abstractmethod
    def send_initial_metadata(self, initial_metadata):
        """Sends the RPC's initial metadata to the system under test.

        Args:
          initial_metadata: The RPC's initial metadata to be "sent" to
            the system under test.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def send_response(self, response):
        """Sends a response to the system under test.

        Args:
          response: A response message to be "sent" to the system under test.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def cancelled(self):
        """Blocks until the system under test has cancelled the RPC."""
        raise NotImplementedError()

    @abc.abstractmethod
    def terminate(self, trailing_metadata, code, details):
        """Terminates the RPC.

        Args:
          trailing_metadata: The RPC's trailing metadata.
          code: The RPC's status code.
          details: The RPC's status details.
        """
        raise NotImplementedError()


class StreamUnaryChannelRpc(six.with_metaclass(abc.ABCMeta)):
    """Fixture for a stream-unary RPC invoked by a system under test.

    Enables users to "play server" for the RPC.
    """

    @abc.abstractmethod
    def send_initial_metadata(self, initial_metadata):
        """Sends the RPC's initial metadata to the system under test.

        Args:
          initial_metadata: The RPC's initial metadata to be "sent" to
            the system under test.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def take_request(self):
        """Draws one of the requests added to the RPC by the system under test.

        Successive calls to this method return requests in the same order in
        which the system under test added them to the RPC.

        Returns:
          A request message added to the RPC by the system under test.
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
    def terminate(self, response, trailing_metadata, code, details):
        """Terminates the RPC.

        Args:
          response: The response for the RPC.
          trailing_metadata: The RPC's trailing metadata.
          code: The RPC's status code.
          details: The RPC's status details.
        """
        raise NotImplementedError()


class StreamStreamChannelRpc(six.with_metaclass(abc.ABCMeta)):
    """Fixture for a stream-stream RPC invoked by a system under test.

    Enables users to "play server" for the RPC.
    """

    @abc.abstractmethod
    def send_initial_metadata(self, initial_metadata):
        """Sends the RPC's initial metadata to the system under test.

        Args:
          initial_metadata: The RPC's initial metadata to be "sent" to the
            system under test.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def take_request(self):
        """Draws one of the requests added to the RPC by the system under test.

        Successive calls to this method return requests in the same order in
        which the system under test added them to the RPC.

        Returns:
          A request message added to the RPC by the system under test.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def send_response(self, response):
        """Sends a response to the system under test.

        Args:
          response: A response messages to be "sent" to the system under test.
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
        """Terminates the RPC.

        Args:
          trailing_metadata: The RPC's trailing metadata.
          code: The RPC's status code.
          details: The RPC's status details.
        """
        raise NotImplementedError()


class Channel(six.with_metaclass(abc.ABCMeta), grpc.Channel):
    """A grpc.Channel double with which to test a system that invokes RPCs."""

    @abc.abstractmethod
    def take_unary_unary(self, descriptor):
        """Draws an RPC currently being made by the system under test.

        If the given descriptor does not identify any RPC currently being made
        by the system under test, this method blocks until the system under
        test invokes such an RPC.

        Args:
          descriptor: A descriptor.MethodDescriptor describing a unary-unary
            RPC method.

        Returns:
          A (invocation_metadata, request, unary_unary_channel_rpc) tuple of
            the RPC's invocation metadata, its request, and a
            UnaryUnaryChannelRpc with which to "play server" for the RPC.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def take_unary_stream(self, descriptor):
        """Draws an RPC currently being made by the system under test.

        If the given descriptor does not identify any RPC currently being made
        by the system under test, this method blocks until the system under
        test invokes such an RPC.

        Args:
          descriptor: A descriptor.MethodDescriptor describing a unary-stream
            RPC method.

        Returns:
          A (invocation_metadata, request, unary_stream_channel_rpc) tuple of
            the RPC's invocation metadata, its request, and a
            UnaryStreamChannelRpc with which to "play server" for the RPC.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def take_stream_unary(self, descriptor):
        """Draws an RPC currently being made by the system under test.

        If the given descriptor does not identify any RPC currently being made
        by the system under test, this method blocks until the system under
        test invokes such an RPC.

        Args:
          descriptor: A descriptor.MethodDescriptor describing a stream-unary
            RPC method.

        Returns:
          A (invocation_metadata, stream_unary_channel_rpc) tuple of the RPC's
            invocation metadata and a StreamUnaryChannelRpc with which to "play
            server" for the RPC.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def take_stream_stream(self, descriptor):
        """Draws an RPC currently being made by the system under test.

        If the given descriptor does not identify any RPC currently being made
        by the system under test, this method blocks until the system under
        test invokes such an RPC.

        Args:
          descriptor: A descriptor.MethodDescriptor describing a stream-stream
            RPC method.

        Returns:
          A (invocation_metadata, stream_stream_channel_rpc) tuple of the RPC's
            invocation metadata and a StreamStreamChannelRpc with which to
            "play server" for the RPC.
        """
        raise NotImplementedError()


class UnaryUnaryServerRpc(six.with_metaclass(abc.ABCMeta)):
    """Fixture for a unary-unary RPC serviced by a system under test.

    Enables users to "play client" for the RPC.
    """

    @abc.abstractmethod
    def get_initial_metadata(self):
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
    def cancel(self):
        """Cancels the RPC."""
        raise NotImplementedError()

    @abc.abstractmethod
    def terminate(self):
        """Blocks until the system under test has terminated the RPC.

        Returns:
          A (response, trailing_metadata, code, details) tuple with the RPC's
            response, trailing metadata, code, and details.
        """
        raise NotImplementedError()


class UnaryStreamServerRpc(six.with_metaclass(abc.ABCMeta)):
    """Fixture for a unary-stream RPC serviced by a system under test.

    Enables users to "play client" for the RPC.
    """

    @abc.abstractmethod
    def get_initial_metadata(self):
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
    def take_response(self):
        """Draws one of the responses added to the RPC by the system under test.

        Successive calls to this method return responses in the same order in
        which the system under test added them to the RPC.

        Returns:
          A response message added to the RPC by the system under test.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def cancel(self):
        """Cancels the RPC."""
        raise NotImplementedError()

    @abc.abstractmethod
    def terminate(self):
        """Blocks until the system under test has terminated the RPC.

        Returns:
          A (trailing_metadata, code, details) tuple with the RPC's trailing
            metadata, code, and details.
        """
        raise NotImplementedError()


class StreamUnaryServerRpc(six.with_metaclass(abc.ABCMeta)):
    """Fixture for a stream-unary RPC serviced by a system under test.

    Enables users to "play client" for the RPC.
    """

    @abc.abstractmethod
    def get_initial_metadata(self):
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
    def send_request(self, request):
        """Sends a request to the system under test.

        Args:
          request: A request message for the RPC to be "sent" to the system
            under test.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def no_more_requests(self):
        """Indicates the end of the RPC's request stream."""
        raise NotImplementedError()
    
    @abc.abstractmethod
    def cancel(self):
        """Cancels the RPC."""
        raise NotImplementedError()

    @abc.abstractmethod
    def terminate(self):
        """Blocks until the system under test has terminated the RPC.

        Returns:
          A (response, trailing_metadata, code, details) tuple with the RPC's
            response, trailing metadata, code, and details.
        """
        raise NotImplementedError()


class StreamStreamServerRpc(six.with_metaclass(abc.ABCMeta)):
    """Fixture for a stream-stream RPC serviced by a system under test.

    Enables users to "play client" for the RPC.
    """

    @abc.abstractmethod
    def get_initial_metadata(self):
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
    def send_request(self, request):
        """Sends a request to the system under test.

        Args:
          request: A request message for the RPC to be "sent" to the system
            under test.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def no_more_requests(self):
        """Indicates the end of the RPC's request stream."""
        raise NotImplementedError()

    @abc.abstractmethod
    def take_response(self):
        """Draws one of the responses added to the RPC by the system under test.

        Successive calls to this method return responses in the same order in
        which the system under test added them to the RPC.

        Returns:
          A response message added to the RPC by the system under test.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def cancel(self):
        """Cancels the RPC."""
        raise NotImplementedError()

    @abc.abstractmethod
    def terminate(self):
        """Blocks until the system under test has terminated the RPC.

        Returns:
          A (trailing_metadata, code, details) tuple with the RPC's trailing
            metadata, code, and details.
        """
        raise NotImplementedError()


class Server(six.with_metaclass(abc.ABCMeta)):
    """A server with which to test a system that services RPCs."""

    @abc.abstracmethod
    def invoke_unary_unary(
            self, descriptor, invocation_metadata, request, timeout):
        """Invokes an RPC to be serviced by the system under test.

        Args:
          descriptor: A descriptor.MethodDescriptor describing a unary-unary
            RPC method.
          invocation_metadata: The RPC's invocation metadata.
          request: The RPC's request.
          timeout: A duration of time in seconds for the RPC or None to
            indicate that the RPC has no time limit.

        Returns:
          A UnaryUnaryServerRpc with which to "play client" for the RPC.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def invoke_unary_stream(
            self, descriptor, invocation_metadata, request, timeout):
        """Invokes an RPC to be serviced by the system under test.

        Args:
          descriptor: A descriptor.MethodDescriptor describing a unary-stream
            RPC method.
          invocation_metadata: The RPC's invocation metadata.
          request: The RPC's request.
          timeout: A duration of time in seconds for the RPC or None to
            indicate that the RPC has no time limit.

        Returns:
          A UnaryStreamServerRpc with which to "play client" for the RPC.
        """
        raise NotImplementedError()

    @abc.abstracmethod
    def invoke_stream_unary(self, descriptor, invocation_metadata, timeout):
        """Invokes an RPC to be serviced by the system under test.

        Args:
          descriptor: A descriptor.MethodDescriptor describing a stream-unary
            RPC method.
          invocation_metadata: The RPC's invocation metadata.
          timeout: A duration of time in seconds for the RPC or None to
            indicate that the RPC has no time limit.

        Returns:
          A StreamUnaryServerRpc with which to "play client" for the RPC.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def invoke_stream_stream(self, descriptor, invocation_metadata, timeout):
        """Invokes an RPC to be serviced by the system under test.

        Args:
          descriptor: A descriptor.MethodDescriptor describing a stream-stream
            RPC method.
          invocation_metadata: The RPC's invocation metadata.
          timeout: A duration of time in seconds for the RPC or None to
            indicate that the RPC has no time limit.

        Returns:
          A StreamStreamServerRpc with which to "play client" for the RPC.
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


def channel(descriptors, time):
    """Creates a Channel for use in tests of a gRPC Python-using system.

    Args:
      descriptions: An iterable of protobuf.ServiceDescriptors describing the
        RPCs that will be made on the returned Channel by the system under
        test.
      time: A Time to be used for tests.

    Returns:
      A Channel for use in tests.
    """
    from grpc_testing import _channel
    description_sequence = tuple(descriptions)
    return _channel.Channel(
        description_sequence,
        _channel.ChannelHandler(description_sequence), time)


def server_from_map(servicers_to_descriptors, time):
    """Creates a Server for use in tests of a gRPC Python-using system.

    Args:
      servicers_to_descriptors: A dictionary from servicer objects (usually
        instances of classes that implement "Servicer" interfaces defined in
        generated "_pb2_grpc" modules) to protobuf.ServiceDescriptors
        describing the RPC services implemented by the servicer objects.
      time: A Time to be used for tests.

    Returns:
      A Server for use in tests.
    """
    from grpc_testing import _server
    return _server.server_from_map(servicers_to_descriptions, time)
