# coding: utf-8

import time
import heapq
import threading
from collections import defaultdict, deque, namedtuple
from Queue import Queue, Empty

from greenlet import greenlet, GreenletExit

class SchedulerError(Exception):
    pass

def get_root():
    gr = greenlet.getcurrent()
    while gr.parent is not None:
        gr = gr.parent
    return gr

SchedulerCommand = namedtuple('SchedulerCommand', 'task activator')

def sched(command):
    return get_root().switch(SchedulerCommand(greenlet.getcurrent(), command))

class Scheduler(object):
    def __init__(self):
        self.run_queue = Queue()
        self.frozen = set()
        self.sleeping = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        while not self.run_queue.empty():
            task, args, kwargs = self.run_queue.get()
            task.throw()
        for task in self.frozen:
            task.throw()

    def put_to_sleep(self, seconds, return_to_caller):
        heapq.heappush(self.sleeping, (time.time() + seconds, return_to_caller))

    def enqueue_task(self, task, *args, **kwargs):
        self.run_queue.put((task, args, kwargs))

    @staticmethod
    def _make_return_to_caller(frozen, run_queue, task):
        def return_to_caller(result):
            frozen.remove(task) # падаем, если задачи нет в замороженных
            run_queue.put((task, [result], {}))
        return return_to_caller

    def start(self):
        while not self.run_queue.empty() or self.frozen:
            now = time.time()
            while self.sleeping and self.sleeping[0][0] < now:
                heapq.heappop(self.sleeping)[1](None)

            try:
                task, args, kwargs = self.run_queue.get(
                    block = True,
                    timeout = (self.sleeping[0][0] - now) if self.sleeping else 1.0,
                )
                result = task.switch(*args, **kwargs)
                if isinstance(result, SchedulerCommand):
                    self.frozen.add(result.task)
                    result.activator(
                        self,
                        self._make_return_to_caller(self.frozen, self.run_queue, task),
                    )
                elif result is None:
                    pass
                else:
                    raise SchedulerError('Unexpected result after switching to {!r}: {!r}'.format(
                        task, result
                    ))
            except Empty:
                pass

def start_scheduler(entry_func, *args, **kwargs):
    assert get_root() is greenlet.getcurrent(), "Scheduler must be run in root greenlet"
    with Scheduler() as scheduler:
        scheduler.enqueue_task(greenlet(entry_func))
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
        scheduler.enqueue_task(greenlet(
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

