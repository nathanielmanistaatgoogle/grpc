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

import grpc_testing

from tests.testing.proto import requests_pb2
from tests.testing.proto import services_pb2

_FIRST_SERVICE_UNUN = grpc_testing.method('UnUn', requests_pb2.Up,
                                          services_pb2.Down, True, True)
_FIRST_SERVICE_UNSTRE = grpc_testing.method('UnStre', requests_pb2.Charm,
                                            services_pb2.Strange, True, False)
_FIRST_SERVICE_STREUN = grpc_testing.method('StreUn', requests_pb2.Charm,
                                            services_pb2.Strange, False, True)
_FIRST_SERVICE_STRESTRE = grpc_testing.method('StreStre', requests_pb2.Top,
                                              services_pb2.Bottom, False, False)
_SECOND_SERVICE_UNSTRE = grpc_testing.method('UnStre', services_pb2.Strange,
                                             requests_pb2.Charm, True, False)
FIRST_SERVICE = grpc_testing.service('tests_of_grpc_testing.FirstService', (
    _FIRST_SERVICE_UNUN, _FIRST_SERVICE_UNSTRE, _FIRST_SERVICE_STREUN,
    _FIRST_SERVICE_STRESTRE,))
SECOND_SERVICE = grpc_testing.service('tests_of_grpc_testing.SecondService',
                                      (_SECOND_SERVICE_UNSTRE,))
DESCRIPTIONS = (FIRST_SERVICE, SECOND_SERVICE,)
