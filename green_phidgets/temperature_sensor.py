import greenlet

class GreenTemperatureSensor(object):
    def __init__(self, scheduler, serial_num):
        self.scheduler

    def read_temperature(self, index):
        event = self.scheduler.wait_callback(
            self.phdiget, [
                ('setOnTemperatureChangeHandler', lambda e: e.index == index),
            ]
        )
        

