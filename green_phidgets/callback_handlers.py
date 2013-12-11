
class Handler(object):
    def __init__(self, sched_event):
        self.lock = threading.Lock()
        self.counter = 0
        self.last_event = None
        self.sched_event = sched_event

    def __call__(self, event):
        with self.lock:
            self.counter += 1
            self.last_event = event
            self.sched_event.set()

    def get_last_event(self):
        with self.lock:
            return self.last_event, self.counter

class HandlerReader(object):
    def __init__(self, handler):
        self.handler = handler
        event, counter = handler.get_last_event()
        self.init_counter = counter

    def get_event(self):
        event, counter = self.handler.get_last_event()
        if counter > self.init_counter:
            return event if counter > self.init_counter else None

class DeviceIndexHandler(object):
    def __init__(self, sched_event):
        self.lock = threading.Lock()
        self.sched_event = sched_event
        self.last_events = defaultdict()
        self.counters = defaultdict(count)

    def __call__(self, event):
        with self.lock:
            next(self.counters[event.index])
            self.last_phidget_events[event.index] = event
            self.sched_event.set()

