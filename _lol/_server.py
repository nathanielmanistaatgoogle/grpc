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
"""Server fixtures."""

import logging
import threading

import grpc
import grpc_testing
from grpc_testing import _common

_CLIENT_INACTIVE = object()


class _State(object):

    def __init__(self, invocation_metadata, deadline):
        self.condition = threading.Condition()
        self.invocation_metadata = _common.fuss_with_metadata(
            invocation_metadata)
        self.initial_metadata_sent = False
        self.deadline = deadline
        self.pending_trailing_metadata = None
        self.pending_code = None
        self.pending_details = None
        self.rpc_errors = []
        self.callbacks = []


class _RequestIterator(object):

    def __init__(self, state, handler, request_deserializer):
        self._state = state
        self._handler = handler
        self._request_deserializer = request_deserializer

    def _next(self):
        read = self._handler.take_request()
        if read.no_more_requests:
            raise StopIteration()
        elif read.terminated:
            rpc_error = grpc.RpcError()
            with self._state.condition:
                self._state.rpc_errors.append(rpc_error)
            raise rpc_error
        else:
            return _common.deserialize_request(
                self._request_deserializer, read.request)[0]

    def __iter__(self):
        return self

    def __next__(self):
        return self._next()

    def next(self):
        return self._next()


def _ensure_initial_metadata_sent(state, handler):
    if not state.initial_metadata_sent:
        handler.send_initial_metadata(_common.FUSSED_EMPTY_METADATA)
        state.initial_metadata_sent = True


def _call_back(state):
    callbacks = tuple(state.callbacks)
    state.callbacks = None

    def call_back():
        for callback in callbacks:
            try:
                callback()
            except Exception:  # pylint: disable=broad-except
                logging.exception('Exception calling server-side callback!')

    callback_calling_thread = threading.Thread(target=call_back)
    callback_calling_thread.start()


def _terminate(state, handler, trailing_metadata, code, details):
    if state.callbacks is not None:
        handler.send_termination(trailing_metadata, code, details)
        _call_back(state)
        state.condition.notify_all()


def _complete(state, handler):
    if state.pending_trailing_metadata is None:
        trailing_metadata = _common.FUSSED_EMPTY_METADATA
    else:
        trailing_metadata = state.pending_trailing_metadata
    if state.pending_code is None:
        code = grpc.StatusCode.OK
    else:
        code = state.pending_code
    details = '' if state.pending_details is None else state.pending_details
    _terminate(state, handler, trailing_metadata, code, details)


def _abort(state, handler, code, details):
    _terminate(state, handler, _common.FUSSED_EMPTY_METADATA, code, details)


def _expire(state, handler):
    with state.condition:
        _abort(
            state, handler, grpc.StatusCode.DEADLINE_EXCEEDED,
            'Took too much time!')


class _ServicerContext(grpc.ServicerContext):

    def __init__(self, state, handler, time):
        self._state = state
        self._handler = handler
        self._time = time

    def is_active(self):
        with self._state.condition:
            if self._state.callbacks is None:
                return False
            else:
                client_active = self._handler.is_active()
                if client_active:
                    return True
                else:
                    # NOTE(nathaniel): If _common.ServerRpcHandler.is_active
                    # were given a more detailed return type then the status
                    # code used here could vary from CANCELLED to... whatever
                    # is the status that represents network disconnection.
                    _abort(
                        self._state, self._handler, grpc.StatusCode.UNKNOWN,
                        'Client no longer active!')

    def time_remaining(self):
        with self._state.condition:
            if self._handler.is_active():
                if self._state.timeout is None:
                    return None
                else:
                    return max(0, self._state.deadline - self._time.time())
            else:
                return 0

    def cancel(self):
        with self._state.condition:
            _abort(
                self._state, self._handler, grpc.StatusCode.CANCELLED,
                'Cancelled by server-side application!')

    def add_callback(self, callback):
        with self._state.condition:
            if self._state.callbacks is None:
                return False
            else:
                self._state.callbacks.append(callback)
                return True

    def invocation_metadata(self):
        with self._state.condition:
            return self._state.invocation_metadata

    def peer(self):
        raise NotImplementedError()

    def peer_identities(self):
        raise NotImplementedError()

    def peer_identity_key(self):
        raise NotImplementedError()

    def auth_context(self):
        raise NotImplementedError()

    def send_initial_metadata(self, initial_metadata):
        with self._state.condition:
            if self._state.initial_metadata_sent:
                raise ValueError(
                    'ServicerContext.send_initial_metadata called too late!')
            else:
                self._handler.send_initial_metadata(
                    _common.fuss_with_metadata(initial_metadata))
                self._state.initial_metadata_sent = True

    def set_trailing_metadata(self, trailing_metadata):
        with self._state.condition:
            self._state.pending_trailing_metadata = _common.fuss_with_metadata(
                trailing_metadata)

    def set_code(self, code):
        with self._state.condition:
            self._state.pending_code = code

    def set_details(self, details):
        with self._state.condition:
            self._state.pending_details = details


def _unary_request(state, handler, request_deserializer):
    read = handler.take_request()
    if read.no_more_requests:
        with state.condition:
            _abort(
                state, handler, grpc.StatusCode.UNIMPLEMENTED,
                'Cardinality violation: needed one request; got zero!')
        return None, False
    elif read.terminated:
        with state.condition:
            _abort(
                state, handler, grpc.StatusCode.UNKNOWN,
                'Client no longer active!')
        return None, False
    else:
        return _common.deserialize_request(
            request_deserializer, read.request)[0], True


def _unary_response(argument, implementation, state, handler, servicer_context, response_serializer):
    try:
        response = implementation(argument, servicer_context)
    except Exception as exception:  # pylint: disable=broad-except
        with state.condition:
            if exception not in state.rpc_errors:
                details = 'Exception calling application: {}'.format(exception)
                logging.exception(details)
                _abort(state, handler, grpc.StatusCode.UNKNOWN, details)
    else:
        with state.condition:
            _ensure_initial_metadata_sent(state, handler)
            handler.add_response(
                _common.serialize_response(response_serializer, response)[0])
            _complete(state, handler)


def _stream_response(
        argument, implementation, state, handler, servicer_context, response_serializer):
    try:
        response_iterator = implementation(argument, servicer_context)
    except Exception as exception:  # pylint: disable=broad-except
        with state.condition:
            if exception not in state.rpc_errors:
                details = 'Exception calling application: {}'.format(exception)
                logging.exception(details)
                _abort(state, handler, grpc.StatusCode.UNKNOWN, details)
    else:
        while True:
            try:
                response = next(response_iterator)
            except StopIteration:
                with state.condition:
                    _ensure_initial_metadata_sent(state, handler)
                    _complete(state, handler)
                break
            except Exception as exception:  # pylint: disable=broad-except
                with state.condition:
                    if exception not in state.rpc_errors:
                        details = 'Exception iterating responses: {}'.format(
                            exception)
                        logging.exception(details)
                        _abort(state, handler, grpc.StatusCode.UNKNOWN, details)
            else:
                with state.condition:
                    _ensure_initial_metadata_sent(state, handler)
                    handler.add_response(
                        _common.serialize_response(
                            response_serializer, response)[0])


def _service_unary_unary(implementation, state, handler, servicer_context, request_deserializer, response_serializer):
    request, proceed = _unary_request(state, handler, request_deserializer)
    if proceed:
        _unary_response(
            request, implementation, state, handler, servicer_context, response_serializer)


def _service_unary_stream(implementation, state, handler, servicer_context, request_deserializer, response_serializer):
    request, proceed = _unary_request(state, handler, request_deserializer)
    if proceed:
        _stream_response(
            request, implementation, state, handler, servicer_context, response_serializer)


def _service_stream_unary(implementation, state, handler, servicer_context, request_deserializer, response_serializer):
    _unary_response(
        _RequestIterator(state, handler, request_deserializer), implementation, state, handler,
        servicer_context, response_serializer)


def _service_stream_stream(implementation, state, handler, servicer_context, request_deserializer, response_serializer):
    _stream_response(
        _RequestIterator(state, handler, request_deserializer), implementation, state, handler,
        servicer_context, response_serializer)


def _service(description, implementation, state, handler, time):
  try:#TODO
    servicer_context = _ServicerContext(state, handler, time)
    request_deserializer = description.request_class.FromString
    response_serializer = description.response_class.SerializeToString
    if description.request_unary:
        if description.response_unary:
            _service_unary_unary(implementation, state, handler, servicer_context, request_deserializer, response_serializer)
        else:
            _service_unary_stream(implementation, state, handler, servicer_context, request_deserializer, response_serializer)
    else:
        if description.response_unary:
            _service_stream_unary(implementation, state, handler, servicer_context, request_deserializer, response_serializer)
        else:
            _service_stream_stream(implementation, state, handler, servicer_context, request_deserializer, response_serializer)

  except Exception:
    import logging
    logging.exception('Wha?')


def _description_and_implementation(
        servicers_to_descriptions, service_name, method_name):
    for servicer, service_description in servicers_to_descriptions.items():
        if service_description.name == service_name:
            for method_description in service_description.methods:
                if method_description.name == method_name:
                    return method_description, getattr(servicer, method_name)


class _RpcRpcHandler(_common.ServerRpcHandler, grpc_testing.ServerRpc):

    def __init__(
        self, requests, no_more_requests, request_serializer,
        response_deserializer):
        self._condition = threading.Condition()
        self._request_serializer = request_serializer
        self._response_deserializer = response_deserializer
        self._requests = requests
        self._no_more_requests = no_more_requests
        self._initial_metadata = None
        self._responses = []
        self._trailing_metadata = None
        self._code = None
        self._details = None

    def send_initial_metadata(self, initial_metadata):
        with self._condition:
            self._initial_metadata = initial_metadata
            self._condition.notify_all()

    def take_request(self):
        with self._condition:
            while True:
                if self._code is None:
                    if self._requests:
                        request = self._requests.pop(0)
                        self._condition.notify_all()
                        return _common.ServerRpcRead(request, False, False)
                    elif self._no_more_requests:
                        return _common.NO_MORE_REQUESTS
                    else:
                        self._condition.wait()
                else:
                    return _common.TERMINATED

    def is_active(self):
        with self._condition:
            return self._code is None

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

    def initial_metadata(self):
        with self._condition:
            while True:
                if self._initial_metadata is None:
                    if self._code is None:
                        self._condition.wait()
                    else:
                        raise ValueError(
                            'No initial metadata despite status code!')
                else:
                    return self._initial_metadata

    def add_requests_as_messages(self, requests):
        with self._condition:
            self._requests.extend(
                _common.serialize_requests(
                    self._request_serializer, requests)[0])
            self._condition.notify_all()

    def take_response_as_message(self):
        with self._condition:
            while True:
                if self._responses:
                    response = _common.deserialize_response(
                        self._response_deserializer, self._responses.pop(0))[0]
                    self._condition.notify_all()
                    return response
                elif self._code is None:
                    self._condition.wait()
                else:
                    raise ValueError('No more responses!')

    def no_more_requests(self):
        with self._condition:
            self._no_more_requests = True
            self._condition.notify_all()

    def cancel(self):
        with self._condition:
            if self._code is None:
                self._code = _CLIENT_INACTIVE
                self._condition.notify_all()

    def terminate(self):
        with self._condition:
            while True:
                if self._code is _CLIENT_INACTIVE:
                    raise ValueError('Huh? Cancelled but wanting status?')
                elif self._code is None:
                    self._condition.wait()
                else:
                    return self._trailing_metadata, self._code, self._details,


class _Fixtureish(_common.ServerFixtureish):

    def __init__(self, servicers_to_descriptions, time):
        self._servicers_to_descriptions = servicers_to_descriptions
        self._time = time

    def invoke_rpc_by_service_and_method_names(
            self, service_name, method_name, handler, invocation_metadata,
            timeout):
        method_description, implementation = _description_and_implementation(
            self._servicers_to_descriptions, service_name, method_name)
        if timeout is None:
            state = _State(invocation_metadata, None)
        else:
            state = _State(invocation_metadata, self._time.time() + timeout)
            with state.condition:
                expiration_future = self._time.call_in(
                    lambda: _expire(state, handler), timeout)
                state.callbacks.append(expiration_future.cancel)
        service_thread = threading.Thread(
            target=_service,
            args=(method_description, implementation, state, handler, self._time,))
        service_thread.start()


class _Fixture(grpc_testing.ServerFixture):

    def __init__(self, fixtureish, descriptions):
        self._fixtureish = fixtureish
        self._descriptions = descriptions

    def invoke_rpc_by_service_and_method_names(
            self, service_name, method_name, invocation_metadata, requests,
            no_more_requests, timeout):
        method_description = _common.method_description(service_name, method_name, self._descriptions)
        request_serializer = method_description.request_class.SerializeToString
        response_deserializer = method_description.response_class.FromString
        rpc_rpc_handler = _RpcRpcHandler(
            list(_common.serialize_requests(request_serializer, requests)[0]),
            no_more_requests, request_serializer, response_deserializer)
        self._fixtureish.invoke_rpc_by_service_and_method_names(
            service_name, method_name, rpc_rpc_handler, invocation_metadata,
            timeout)
        return rpc_rpc_handler


def fixtureish_from_descriptions(servicers_to_descriptions, time):
    return _Fixtureish(servicers_to_descriptions, time)


def fixture_from_descriptions(servicers_to_descriptions, time):
    """"""
    descriptions = tuple(servicers_to_descriptions.values())
    return _Fixture(_Fixtureish(servicers_to_descriptions, time), descriptions)
