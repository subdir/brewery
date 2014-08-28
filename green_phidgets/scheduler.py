# coding: utf-8

import time
import heapq
import threading
from collections import defaultdict, deque, namedtuple
from Queue import Queue, Empty

from greenlet import greenlet as Greenlet, GreenletExit

class SchedulerError(Exception):
    pass

def get_root():
    gr = Greenlet.getcurrent()
    while gr.parent is not None:
        gr = gr.parent
    return gr

SchedulerCommand = namedtuple('SchedulerCommand', 'greenlet activator')
Sleeper = namedtuple('Sleeper', 'wakeup_time return_to_caller')

def sched(command):
    return get_root().switch(SchedulerCommand(Greenlet.getcurrent(), command))

class Scheduler(object):
    def __init__(self):
        self.run_queue = Queue()
        self.frozen = set()
        self.sleeping = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        while not self.run_queue.empty():
            greenlet, args, kwargs = self.run_queue.get()
            greenlet.throw()
        for greenlet in self.frozen:
            greenlet.throw()

    def put_to_sleep(self, seconds, return_to_caller):
        heapq.heappush(self.sleeping, Sleeper(time.time() + seconds, return_to_caller))

    def enqueue_greenlet(self, greenlet, *args, **kwargs):
        self.run_queue.put((greenlet, args, kwargs))

    @staticmethod
    def _make_return_to_caller(frozen, run_queue, greenlet):
        def return_to_caller(result):
            frozen.remove(greenlet) # падаем, если задачи нет в замороженных
            run_queue.put((greenlet, [result], {}))
        return return_to_caller

    def start(self):
        while not self.run_queue.empty() or self.frozen:
            now = time.time()
            while self.sleeping and self.sleeping[0].wakeup_time <= now:
                heapq.heappop(self.sleeping).return_to_caller(None)

            try:
                greenlet, args, kwargs = self.run_queue.get(
                    block = True,
                    timeout = (self.sleeping[0].wakeup_time - now) if self.sleeping else 1.0,
                )
                result = greenlet.switch(*args, **kwargs)
                if isinstance(result, SchedulerCommand):
                    self.frozen.add(result.greenlet)
                    result.activator(
                        self,
                        self._make_return_to_caller(self.frozen, self.run_queue, greenlet),
                    )
                elif result is None and greenlet.dead:
                    pass
                else:
                    raise SchedulerError('Unexpected result after switching to {!r}: {!r}'.format(
                        greenlet, result
                    ))
            except Empty:
                pass

def start_scheduler(entry_func, *args, **kwargs):
    assert get_root() is Greenlet.getcurrent(), "Scheduler must be run in root greenlet"
    with Scheduler() as scheduler:
        scheduler.enqueue_greenlet(Greenlet(entry_func))
        scheduler.start()

def Yield():
    def YieldInstance(scheduler, return_to_caller):
        return_to_caller(None)
    return YieldInstance

def Sleep(seconds):
    def SleepInstance(scheduler, return_to_caller):
        scheduler.put_to_sleep(seconds, return_to_caller)
    return SleepInstance

def Call(func, *args, **kwargs):
    def CallInstance(scheduler, return_to_caller):
        scheduler.enqueue_greenlet(Greenlet(
            lambda: return_to_caller(func(*args, **kwargs))
        ))
    return CallInstance

def ReadPhidget(handler):
    def ReadPhidgetInstance(scheduler, return_to_caller):
        handler.add_trigger(return_to_caller)
    return ReadPhidgetInstance

def All(*commands):
    waiting = set(xrange(len(commands)))
    results = [None] * len(commands)

    def command_finished(return_to_caller, index):
        def command_finished(result):
            if index not in waiting:
                raise SchedulerError('Internal error: Event #{!r}: {!r} probably triggered twise!'.format(
                    index, commands[index]
                ))
            else:
                waiting.remove(index)
                results[index] = result
            if not waiting:
                return_to_caller(results)
        return command_finished

    def AllInstance(scheduler, return_to_caller):
        for idx, command in enumerate(commands):
            command(scheduler, command_finished(return_to_caller, idx))

    return AllInstance

def Any(**commands):
    results = {}

    def command_finished(return_to_caller, key):
        def command_finished(result):
            if key in results:
                raise SchedulerError('Internal error: Event {!r} ({!r}) probably triggered twise!'.format(
                    key, commands[key]
                ))
            else:
                results[key] = result
            if len(results) == 1:
                return_to_caller(results)
        return command_finished

    def AnyInstance(scheduler, return_to_caller):
        for name, command in commands.iteritems():
            command(scheduler, command_finished(return_to_caller, name))

    return AnyInstance

