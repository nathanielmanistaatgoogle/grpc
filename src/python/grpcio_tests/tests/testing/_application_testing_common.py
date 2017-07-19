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

import grpc_testing

from tests.testing.proto import services_pb2

# TODO(https://github.com/grpc/grpc/issues/11657): Eliminate this.
_SERVICES = services_pb2.DESCRIPTOR.services_by_name
FIRST_SERVICE = _SERVICES['FirstService']
SECOND_SERVICE = _SERVICES['SecondService']
FIRST_SERVICE_UNUN = FIRST_SERVICE.methods_by_name['UnUn']
FIRST_SERVICE_UNSTRE = FIRST_SERVICE.methods_by_name['UnStre']
FIRST_SERVICE_STREUN = FIRST_SERVICE.methods_by_name['StreUn']
FIRST_SERVICE_STRESTRE = FIRST_SERVICE.methods_by_name['StreStre']
SECOND_SERVICE_UNSTRE = SECOND_SERVICE.methods_by_name['UnStre']
