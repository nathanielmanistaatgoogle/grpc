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

import threading
import time
import random
import unittest

import grpc_testing

_QUANTUM = 0.3
_MANY = 10000


class TimeTest(object):

    def test_sleep_for(self):
        start_time = self._time.time()
        self._time.sleep_for(_QUANTUM)
        end_time = self._time.time()

        self.assertLessEqual(start_time + _QUANTUM, end_time)

    def test_sleep_until(self):
        start_time = self._time.time()
        self._time.sleep_until(start_time + _QUANTUM)
        end_time = self._time.time()

        self.assertLessEqual(start_time + _QUANTUM, end_time)

    def test_call_in(self):
        event = threading.Event()

        self._time.call_in(event.set, _QUANTUM)
        self._time.sleep_for(_QUANTUM * 2)

        self.assertTrue(event.is_set())

    def test_call_at(self):
        event = threading.Event()

        self._time.call_at(event.set, self._time.time() + _QUANTUM)
        self._time.sleep_for(_QUANTUM * 2)

        self.assertTrue(event.is_set())

    def test_cancel(self):
        event = threading.Event()

        future = self._time.call_in(event.set, _QUANTUM * 2)
        self._time.sleep_for(_QUANTUM)
        cancelled = future.cancel()
        self._time.sleep_for(_QUANTUM * 2)

        if cancelled:
            self.assertFalse(event.is_set())
            self.assertTrue(future.cancelled())
        else:
            self.assertTrue(event.is_set())

    def test_many(self):
        test_events = tuple(threading.Event() for _ in range(_MANY))
        test_futures = {}
        other_futures = []

        for test_event in test_events:
            test_futures[test_event] = self._time.call_in(
                test_event.set, _QUANTUM * (2 + random.random()))
        for _ in range(_MANY):
            other_futures.append(
                self._time.call_in(threading.Event().set, _QUANTUM * 1000 *
                                   random.random()))
        self._time.sleep_for(_QUANTUM)
        cancelled = set()
        for test_event, test_future in test_futures.items():
            if bool(random.randint(0, 1)) and test_future.cancel():
                cancelled.add(test_event)
        self._time.sleep_for(_QUANTUM * 3)

        for test_event in test_events:
            (self.assertFalse if test_event in cancelled else
             self.assertTrue)(test_event.is_set())
        for other_future in other_futures:
            other_future.cancel()


class RealTimeTest(TimeTest, unittest.TestCase):

    def setUp(self):
        self._time = grpc_testing.real_time()


class FakeTimeTest(TimeTest, unittest.TestCase):

    def setUp(self):
        self._time = grpc_testing.fake_time(random.randint(0, int(time.time())))


if __name__ == '__main__':
    unittest.main(verbosity=2)
