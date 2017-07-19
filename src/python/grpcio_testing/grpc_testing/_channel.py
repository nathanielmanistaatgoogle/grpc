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
"""Channel fixtures."""

import collections
import logging
import threading

import grpc
import grpc_testing
from grpc_testing import _common

_NOT_YET_OBSERVED = object()


def _handler_cancel(handler):
    return handler.cancel(grpc.StatusCode.CANCELLED, 'Locally cancelled!')


def _handler_is_active(handler):
    return handler.is_active()


def _handler_time_remaining(unused_handler):
    raise NotImplementedError()


def _handler_add_callback(handler, callback):
    return handler.add_callback(callback)


def _handler_initial_metadata(handler):
    return handler.initial_metadata()


def _handler_trailing_metadata(handler):
    trailing_metadata, unused_code, unused_details = handler.terminate()
    return trailing_metadata


def _handler_code(handler):
    unused_trailing_metadata, code, unused_details = handler.terminate()
    return code


def _handler_details(handler):
    unused_trailing_metadata, unused_code, details = handler.terminate()
    return details


class _Call(grpc.Call):

    def __init__(self, handler):
        self._handler = handler

    def cancel(self):
        _handler_cancel(self._handler)

    def is_active(self):
        return _handler_is_active(self._handler)

    def time_remaining(self):
        return _handler_time_remaining(self._handler)

    def add_callback(self, callback):
        return _handler_add_callback(self._handler, callback)

    def initial_metadata(self):
        return _handler_initial_metadata(self._handler)

    def trailing_metadata(self):
        return _handler_trailing_metadata(self._handler)

    def code(self):
        return _handler_code(self._handler)

    def details(self):
        return _handler_details(self._handler)


class _RpcErrorCall(grpc.RpcError, grpc.Call):

    def __init__(self, handler):
        self._handler = handler

    def cancel(self):
        _handler_cancel(self._handler)

    def is_active(self):
        return _handler_is_active(self._handler)

    def time_remaining(self):
        return _handler_time_remaining(self._handler)

    def add_callback(self, callback):
        return _handler_add_callback(self._handler, callback)

    def initial_metadata(self):
        return _handler_initial_metadata(self._handler)

    def trailing_metadata(self):
        return _handler_trailing_metadata(self._handler)

    def code(self):
        return _handler_code(self._handler)

    def details(self):
        return _handler_details(self._handler)


def _handler_next(handler):
    read = handler.take_response()
    if read.code is None:
        return read.response
    elif read.code is grpc.StatusCode.OK:
        raise StopIteration()
    else:
        raise _RpcErrorCall(handler)


class _ResponseIteratorCall(grpc.Call):

    def __init__(self, handler):
        self._handler = handler

    def __iter__(self):
        return self

    def __next__(self):
        return _handler_next(self._handler)

    def next(self):
        return _handler_next(self._handler)

    def cancel(self):
        _handler_cancel(self._handler)

    def is_active(self):
        return _handler_is_active(self._handler)

    def time_remaining(self):
        return _handler_time_remaining(self._handler)

    def add_callback(self, callback):
        return _handler_add_callback(self._handler, callback)

    def initial_metadata(self):
        return _handler_initial_metadata(self._handler)

    def trailing_metadata(self):
        return _handler_trailing_metadata(self._handler)

    def code(self):
        return _handler_code(self._handler)

    def details(self):
        return _handler_details(self._handler)


class _HandlerExtras(object):

    def __init__(self):
        self.condition = threading.Condition()
        self.unary_response = _NOT_YET_OBSERVED
        self.cancelled = False


def _handler_with_extras_cancel(handler, extras):
    with extras.condition:
        if handler.cancel(grpc.StatusCode.CANCELLED, 'Locally cancelled!'):
            extras.cancelled = True
            return True
        else:
            return False


def _extras_without_handler_cancelled(extras):
    with extras.condition:
        return extras.cancelled


def _handler_running(handler):
    return handler.is_active()


def _handler_done(handler):
    return not handler.is_active()


def _handler_with_extras_unary_response(handler, extras):
    with extras.condition:
        if extras.unary_response is _NOT_YET_OBSERVED:
            read = handler.take_response()
            if read.code is None:
                extras.unary_response = read.response
                return read.response
            else:
                raise _RpcErrorCall(handler)
        else:
            return extras.unary_response


def _handler_exception(unused_handler):
    raise NotImplementedError('TODO!')


def _handler_traceback(unused_handler):
    raise NotImplementedError('TODO!')


def _handler_add_done_callback(handler, callback, future):
    adapted_callback = lambda: callback(future)
    if not handler.add_callback(adapted_callback):
        callback(future)


class _FutureCall(grpc.Future, grpc.Call):

    def __init__(self, handler, extras):
        self._handler = handler
        self._extras = extras

    def cancel(self):
        return _handler_with_extras_cancel(self._handler, self._extras)

    def cancelled(self):
        return _extras_without_handler_cancelled(self._extras)

    def running(self):
        return _handler_running(self._handler)

    def done(self):
        return _handler_done(self._handler)

    def result(self):
        return _handler_with_extras_unary_response(self._handler, self._extras)

    def exception(self):
        return _handler_exception(self._handler)

    def traceback(self):
        return _handler_traceback(self._handler)

    def add_done_callback(self, fn):
        _handler_add_done_callback(self._handler, fn, self)

    def is_active(self):
        return _handler_is_active(self._handler)

    def time_remaining(self):
        return _handler_time_remaining(self._handler)

    def add_callback(self, callback):
        return _handler_add_callback(self._handler, callback)

    def initial_metadata(self):
        return _handler_initial_metadata(self._handler)

    def trailing_metadata(self):
        return _handler_trailing_metadata(self._handler)

    def code(self):
        return _handler_code(self._handler)

    def details(self):
        return _handler_details(self._handler)


def _handler_consume_requests(request_iterator, handler):

    def _consume():
        while True:
            try:
                request = next(request_iterator)
                added = handler.add_request(request)
                if not added:
                    break
            except StopIteration:
                handler.no_more_requests()
                break
            except Exception:  # pylint: disable=broad-except
                details = 'Exception iterating requests!'
                logging.exception(details)
                handler.cancel(grpc.StatusCode.UNKNOWN, details)

    consumption = threading.Thread(target=_consume)
    consumption.start()


def _handler_blocking_unary_response(handler):
    read = handler.take_response()
    if read.code is None:
        unused_trailing_metadata, code, unused_details = handler.terminate()
        if code is grpc.StatusCode.OK:
            return read.response
        else:
            raise _RpcErrorCall(handler)
    else:
        raise _RpcErrorCall(handler)


# All per-call credentials parameters are unused by this test infrastructure.
# pylint: disable=unused-argument
class _UnaryUnaryMultiCallable(grpc.UnaryUnaryMultiCallable):

    def __init__(self, full_name, channel_handler):
        self._full_name = full_name
        self._channel_handler = channel_handler

    def __call__(self, request, timeout=None, metadata=None, credentials=None):
        handler = self._channel_handler.invoke_rpc(
            self._full_name, _common.fuss_with_metadata(metadata), [request],
            True, timeout)
        return _blocking_unary_response(handler)

    def with_call(self, request, timeout=None, metadata=None, credentials=None):
        handler = self._channel_handler.invoke_rpc(
            self._full_name,
            _common.fuss_with_metadata(metadata),
            [request],
            True, timeout)
        response = _blocking_unary_response(handler)
        return response, _Call(handler)

    def future(self, request, timeout=None, metadata=None, credentials=None):
        handler = self._channel_handler.invoke_rpc(
            self._full_name,
            _common.fuss_with_metadata(metadata),
            [request],
            True, timeout)
        return _FutureCall(handler, _HandlerExtras())


class _UnaryStreamMultiCallable(grpc.StreamStreamMultiCallable):

    def __init__(self, full_name, channel_handler):
        self._full_name = full_name
        self._channel_handler = channel_handler

    def __call__(self, request, timeout=None, metadata=None, credentials=None):
        handler = self._channel_handler.invoke_rpc(
            self._full_name,
            _common.fuss_with_metadata(metadata),
            [request],
            True, timeout)
        return _ResponseIteratorCall(handler)


class _StreamUnaryMultiCallable(grpc.StreamUnaryMultiCallable):

    def __init__(self, full_name, channel_handler):
        self._full_name = full_name
        self._channel_handler = channel_handler

    def __call__(self,
                 request_iterator,
                 timeout=None,
                 metadata=None,
                 credentials=None):
        handler = self._channel_handler.invoke_rpc(
            self._full_name,
            _common.fuss_with_metadata(metadata), [], False, timeout)
        _handler_consume_requests(request_iterator, handler)
        return _handler_blocking_unary_response(handler)

    def with_call(self,
                  request_iterator,
                  timeout=None,
                  metadata=None,
                  credentials=None):
        handler = self._channel_handler.invoke_rpc(
            self._full_name,
            _common.fuss_with_metadata(metadata), [], False, timeout)
        _handler_consume_requests(request_iterator, handler)
        response = _handler_blocking_unary_response(handler)
        return response, _Call(handler)

    def future(self,
               request_iterator,
               timeout=None,
               metadata=None,
               credentials=None):
        handler = self._channel_handler.invoke_rpc(
            self._full_name,
            _common.fuss_with_metadata(metadata), [], False, timeout)
        _handler_consume_requests(request_iterator, handler)
        return _FutureCall(handler, _HandlerExtras())


class _StreamStreamMultiCallable(grpc.StreamStreamMultiCallable):

    def __init__(self, full_name, channel_handler):
        self._full_name = full_name
        self._channel_handler = channel_handler

    def __call__(self,
                 request_iterator,
                 timeout=None,
                 metadata=None,
                 credentials=None):
        handler = self._channel_handler.invoke_rpc(
            self._full_name,
            _common.fuss_with_metadata(metadata), [], False, timeout)
        _consume_requests(request_iterator, handler)
        return _ResponseIteratorCall(handler)
# pylint: enable=unused-argument


class _RpcState(object):

        def __init__(self, invocation_metadata, requests, requests_closed):
            self.condition = threading.Condition()
            self.invocation_metadata = invocation_metadata
            self.requests = requests
            self.requests_closed = requests_closed
            self.initial_metadata = None
            self.responses = []
            self.trailing_metadata = None
            self.code = None
            self.details = None


def _state_add_request(state, request):
    with state.condition:
        if state.code is None and not state.requests_closed:
            state.requests.append(request)
            state.condition.notify_all()
            return True
        else:
            return False


def _state_no_more_requests(state):
    with state.condition:
        if state.code is None and not state.requests_closed:
            state.requests_closed = True
            state.condition.notify_all()


def _state_take_response(state):
    with state.condition:
        while True:
            if state.code is grpc.StatusCode.OK:
                if state.responses:
                    response = state.responses.pop(0)
                    return _common.ChannelRpcRead(response, None, None, None)
                else:
                    return _common.ChannelRpcRead(None, state.trailing_metadata,
                                                  grpc.StatusCode.OK,
                                                  state.details)
            elif state.code is None:
                if state.responses:
                    response = state.responses.pop(0)
                    return _common.ChannelRpcRead(response, None, None, None)
                else:
                    state.condition.wait()
            else:
                return _common.ChannelRpcRead(None, state.trailing_metadata,
                                              state.code, state.details)


def _state_cancel(state, code, details):
    with state.condition:
        if state.code is None:
            if state.initial_metadata is None:
                state.initial_metadata = _common.FUSSED_EMPTY_METADATA
                state.trailing_metadata = _common.FUSSED_EMPTY_METADATA
                state.code = code
                state.details = details
                state.condition.notify_all()
                return True
            else:
                return False


def _state_terminate(state):
    with state.condition:
        while True:
            if state.code is None:
                state.condition.wait()
            else:
                return state.trailing_metadata, state.code, state.details


def _state_is_active(state):
    with state.condition:
        return state.code is None


def _state_time_remaining(unused_state):
    raise NotImplementedError()


def _state_add_callback(unused_state, unused_callback):
    raise NotImplementedError()


def _state_initial_metadata(state):
    with state.condition:
        while True:
            if state.initial_metadata is None:
                if state.code is None:
                    state.condition.wait()
                else:
                    return _common.FUSSED_EMPTY_METADATA
            else:
                return state.initial_metadata


def _state_trailing_metadata(state):
    with state.condition:
        while True:
            if state.trailing_metadata is None:
                state.condition.wait()
            else:
                return state.trailing_metadata


def _state_code(state):
    with state.condition:
        while True:
            if state.code is None:
                state.condition.wait()
            else:
                return state.code


def _state_details(state):
    with state.condition:
        while True:
            if state.details is None:
                state.condition.wait()
            else:
                return state.details


class _RpcStateChannelRpcHandler(_common.ChannelRpcHandler):

    def __init__(self, state):
        self._state = state

    def initial_metadata(self):
        return _state_initial_metadata(self._state)

    def add_request(self, request):
        return _state_add_request(self._state, request)

    def no_more_requests(self):
        _state_no_more_requests(self._state)

    def take_response(self):
        return _state_take_response(self._state)

    def cancel(self, code, details):
        return _state_cancel(self._state, code, details)

    def terminate(self):
        return _state_terminate(self._state)

    def is_active(self):
        return _state_is_active(self._state)

    def time_remaining(self):
        return _state_time_remaining(self._state)

    def add_callback(self, callback):
        return _state_add_callback(self._state, callback)


class ChannelHandler(_common.ChannelHandler):

    def __init__(self, descriptions):
        self._descriptions = descriptions
        self._state = _ChannelState()

    def invoke_rpc(self, full_name, invocation_metadata, requests,
                   no_more_requests, timeout):
        rpc_state = _RpcState(invocation_metadata, requests, no_more_requests)
        with self._state.condition:
            self._state.rpc_states[full_name].append(rpc_state)
            self._state.condition.notify_all()
        return _RpcStateChannelRpcHandler(rpc_state)

    def take_rpc(self, full_name):
        service_name, method_name = full_name.split('/')[1:3]
        method_description = _common.describe(
            service_name, method_name, self._descriptions)
        request_deserializer = method_description.request_class.FromString
        response_serializer = method_description.response_class.SerializeToString
        with self._state.condition:
            while True:
                try:
                    rpc_state = self._state.rpc_states[full_name].pop(0)
                except IndexError:
                    self._state.condition.wait()
                else:
                    return _ChannelRpc(rpc_state, request_deserializer,
                                       response_serializer)


class ChannelFixture(grpc_testing.ChannelFixture):

    def __init__(self, descriptions, handler, time):
        self._descriptions = descriptions
        self._handler = handler
        self._time = time

    def channel(self):
        return _Channel(self._handler)

    def take_rpc_by_service_and_method_names(self, service_name, method_name):
        full_name = '/{}/{}'.format(service_name, method_name)
        return self._handler.take_rpc(full_name)


class _UnaryUnaryChannelRpc(grpc_testing.UnaryUnaryChannelRpc):

    def __init__(self):
        raise NotImplementedError()

    def send_initial_metadata(self, initial_metadata):
        raise NotImplementedError()

    def cancelled(self):
        raise NotImplementedError()

    def terminate(self, response, trailing_metadata, code, details):
        raise NotImplementedError()


class _TestingChannel(grpc_testing.Channel):

    def __init__(self, handler):
        self._handler = handler

    def subscribe(self, callback, try_to_connect=False):
        raise NotImplementedError()

    def unsubscribe(self, callback):
        raise NotImplementedError()

    def unary_unary(
            self, method, request_serializer=None, response_deserializer=None):
        return _UnaryUnaryMultiCallable(method, self._handler)

    def unary_stream(self, method, request_serializer=None, response_deserializer=None):
        return _UnaryStreamMultiCallable(method, self._handler)

    def stream_unary(
            self, method,
            request_serializer=None,
            response_deserializer=None):
        return _StreamUnaryMultiCallable(method, self._handler)

    def stream_stream(
            self, method, request_serializer=None, response_deserializer=None):
        return _StreamStreamMultiCallable(method, self._handler)

    def take_unary_unary(self, descriptor):
        with self._state.condition:
            while True:
                try:
                    rpc_state = self._state.rpc_states[descriptor]

    def take_unary_stream(self, descriptor):
        raise NotImplementedError()

    def take_stream_unary(self, descriptor):
        raise NotImplementedError()

    def take_stream_stream(self, descriptor):
        raise NotImplementedError()


def testing_channel(descriptors, time):
    return _TestingChannel(descriptors, time)
