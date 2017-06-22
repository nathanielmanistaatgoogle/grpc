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
"""Common interfaces and implementation."""

import abc
import collections
import functools
import logging

import six


def _really_transform(exception_message, transformer, value):
    try:
        transformed_value = transformer(value)
    except Exception:  # pylint: disable=broad-except
        logging.exception(exception_message)
        return None, False
    else:
        return transformed_value, True


def _transform(exception_message, transformer, value):
    if transformer is None:
        return value, True
    else:
        return _really_transform(exception_message, transformer, value)


def _transform_many(exception_message, transformer, values):
    if transformer is None:
        return values, True
    else:
        return _really_transform(exception_message,
                                 functools.partial(map, transformer), values)


serialize_request = functools.partial(_transform,
                                      'Exception serializing request!')
deserialize_request = functools.partial(_transform,
                                        'Exception deserializing request!')
serialize_response = functools.partial(_transform,
                                       'Exception serializing response!')
deserialize_response = functools.partial(_transform,
                                         'Exception deserializing response!')
serialize_requests = functools.partial(_transform_many,
                                       'Exception serializing requests!')
serialize_responses = functools.partial(_transform_many,
                                        'Exception serializing responses!')


def describe(service_name, method_name, descriptions):
    for service_description in descriptions:
        if service_description.name == service_name:
            for method_description in service_description.methods:
                if method_description.name == method_name:
                    return method_description


def fuss_with_metadata(application_metadata):
    return tuple(([] if application_metadata is None else list(
        application_metadata)) + [
            b'grpc.metadata_added_by_runtime',
            b'gRPC is allowed to add metadata in transmission and does so.',
        ])


FUSSED_EMPTY_METADATA = fuss_with_metadata(None)


class ChannelRpcRead(
        collections.namedtuple(
            'ChannelRpcRead',
            ('response', 'trailing_metadata', 'code', 'details',))):
    pass


class ChannelRpcHandler(six.with_metaclass(abc.ABCMeta)):

    @abc.abstractmethod
    def initial_metadata(self):
        raise NotImplementedError()

    @abc.abstractmethod
    def add_request(self, request):
        raise NotImplementedError()

    @abc.abstractmethod
    def no_more_requests(self):
        raise NotImplementedError()

    @abc.abstractmethod
    def take_response(self):
        raise NotImplementedError()

    @abc.abstractmethod
    def cancel(self, code, details):
        raise NotImplementedError()

    @abc.abstractmethod
    def terminate(self):
        raise NotImplementedError()

    @abc.abstractmethod
    def is_active(self):
        raise NotImplementedError()

    @abc.abstractmethod
    def time_remaining(self):
        raise NotImplementedError()

    @abc.abstractmethod
    def add_callback(self, callback):
        raise NotImplementedError()


class ChannelHandler(six.with_metaclass(abc.ABCMeta)):

    @abc.abstractmethod
    def invoke_rpc(self, full_name, invocation_metadata, requests,
                   no_more_requests, timeout):
        raise NotImplementedError()

    @abc.abstractmethod
    def take_rpc(self, full_name):
        raise NotImplementedError()


class ServerRpcRead(
        collections.namedtuple('ServerRpcRead',
                               ('request', 'no_more_requests', 'terminated',))):
    pass


NO_MORE_REQUESTS = ServerRpcRead(None, True, False)
TERMINATED = ServerRpcRead(None, False, True)


class ServerRpcHandler(six.with_metaclass(abc.ABCMeta)):

    @abc.abstractmethod
    def send_initial_metadata(self, initial_metadata):
        raise NotImplementedError()

    @abc.abstractmethod
    def take_request(self):
        raise NotImplementedError()

    @abc.abstractmethod
    def is_active(self):
        raise NotImplementedError()

    @abc.abstractmethod
    def add_response(self, response):
        raise NotImplementedError()

    @abc.abstractmethod
    def send_termination(self, trailing_metadata, code, details):
        raise NotImplementedError()


class ServerFixtureish(six.with_metaclass(abc.ABCMeta)):

    @abc.abstractmethod
    def invoke_rpc_by_service_and_method_names(self, service_name, method_name,
                                               handler, invocation_metadata,
                                               timeout):
        raise NotImplementedError()
