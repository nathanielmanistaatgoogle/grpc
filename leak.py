# Copyright 2015, Google Inc.
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

"""A demonstration of a memory leak."""

from concurrent import futures
import threading

import grpc

_CALLBACK = lambda ignored_future: None


def _handle(request, context):
    raise ValueError()


class _RpcHandler(grpc.GenericRpcHandler):

    def __init__(self):
        self._method_handler = grpc.unary_unary_rpc_method_handler(_handle)

    def service(self, handler_call_details):
        return self._method_handler


def run():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=100))
    server.add_generic_rpc_handlers((_RpcHandler(),))
    port = server.add_insecure_port('[::]:0')
    server.start()
    channel = grpc.insecure_channel('localhost:{}'.format(port))
    multi_callable = channel.unary_unary('meffod')
    request = b'you' * 300000
    while True:
        response_future = multi_callable.future(request)
        response_future.add_done_callback(_CALLBACK)


if __name__ == '__main__':
    run()
