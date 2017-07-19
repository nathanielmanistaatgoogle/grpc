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
# Tests that run in real time can either wait for the scheduler to
# eventually run what needs to be run (and risk timing out) or declare
# that the scheduler didn't schedule work reasonably fast enough. We
# choose the latter for this test.
_PATHOLOGICAL_SCHEDULING = 'pathological thread scheduling!'


class _TimeNoter(object):

    def __init__(self, time):
        self._condition = threading.Condition()
        self._time = time
        self._call_time = None

    def __call__(self):
        with self._condition:
            self._call_time = self._time.time()

    def call_time(self):
        with self._condition:
            return self._call_time


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
        time_noter = _TimeNoter(self._time)

        start_time = self._time.time()
        self._time.call_in(time_noter, _QUANTUM)
        self._time.sleep_for(_QUANTUM * 2)
        call_time = time_noter.call_time()

        self.assertIsNotNone(call_time, msg=_PATHOLOGICAL_SCHEDULING)
        self.assertLessEqual(start_time + _QUANTUM, call_time)

    def test_call_at(self):
        time_noter = _TimeNoter(self._time)

        start_time = self._time.time()
        self._time.call_at(time_noter, self._time.time() + _QUANTUM)
        self._time.sleep_for(_QUANTUM * 2)
        call_time = time_noter.call_time()

        self.assertIsNotNone(call_time, msg=_PATHOLOGICAL_SCHEDULING)
        self.assertLessEqual(start_time + _QUANTUM, call_time)

    def test_cancel(self):
        time_noter = _TimeNoter(self._time)

        future = self._time.call_in(time_noter, _QUANTUM * 2)
        self._time.sleep_for(_QUANTUM)
        cancelled = future.cancel()
        self._time.sleep_for(_QUANTUM * 2)
        call_time = time_noter.call_time()

        self.assertIsNone(call_time, msg=_PATHOLOGICAL_SCHEDULING)
        self.assertTrue(cancelled)
        self.assertTrue(future.cancelled())

    def test_many(self):
        test_events = tuple(threading.Event() for _ in range(_MANY))
        possibly_cancelled_futures = {}
        cancelled_at_test_end_futures = []

        for test_event in test_events:
            possibly_cancelled_futures[test_event] = self._time.call_in(
                test_event.set, _QUANTUM * (2 + random.random()))
        for _ in range(_MANY):
            cancelled_at_test_end_futures.append(
                self._time.call_in(threading.Event().set, _QUANTUM * 1000 *
                                   random.random()))
        self._time.sleep_for(_QUANTUM)
        cancelled = set()
        for test_event, test_future in possibly_cancelled_futures.items():
            if bool(random.randint(0, 1)) and test_future.cancel():
                cancelled.add(test_event)
        self._time.sleep_for(_QUANTUM * 3)

        for test_event in test_events:
            (self.assertFalse if test_event in cancelled else
             self.assertTrue)(test_event.is_set())
        for other_future in cancelled_at_test_end_futures:
            other_future.cancel()


class RealTimeTest(TimeTest, unittest.TestCase):

    def setUp(self):
        self._time = grpc_testing.real_time()


class FakeTimeTest(TimeTest, unittest.TestCase):

    def setUp(self):
        self._time = grpc_testing.fake_time(random.randint(0, int(time.time())))


if __name__ == '__main__':
    unittest.main(verbosity=2)
