#!/usr/bin/python
# coding: utf-8
#
# Требования:
#
# 1. Запретить взаимоисключающие состояния. Для экономии,
#    одна и та же релюшка может управлять сразу парой устройств.
#    Например, двумя клапанами A и B из разных "слоев", при этом еще
#    одна релюшка переключает активный "слой" клапанов. Таким образом,
#    физически нельзя открыть одновременно A и B, и нужно чтобы попытки
#    сделать это отлавливались и запрещались автоматически.
#
# 2. В случае аварийного завершения нужно убедиться, что все оборудование
#    находится в безопасном состоянии. Например, мы не хотим, чтобы из-за
#    непойманного исключения, клапан подачи воды в бойлер оставался открытым
#    после завершения программы.
#

from __future__ import print_function, with_statement

import os, sys, time
import threading
import logging
from logging import log, INFO
from contextlib import contextmanager
from operator import ge, le

from greenlet import greenlet

from green_phidgets.scheduler import start_scheduler, sched

from brewery.units import *
from brewery.util import struct, open_phidget
from brewery.relay import Relay, RelayController, ComplexRelay
from brewery.valve import MotorValve, SolenoidValve
from brewery.scale import Scale
from brewery.stove import Stove
from brewery.temperature import Thermocouple

from Phidgets.Devices.InterfaceKit import InterfaceKit
from Phidgets.Devices.Bridge import Bridge, BridgeGain
from Phidgets.Devices.TemperatureSensor import TemperatureSensor, ThermocoupleType

@struct
class Boiler(object):
    def __init__(self, 
        valve_cleanwater_in,
        valve_water_in,
        valve_wort_out,
        valve_flush,
        valve_to_mashtank,
        valve_from_mashtank,
        temp_sensor,
        scale,
        stove,
    ):
        pass

    def fill_with_cleanwater(self, weight):
        with self.valve_cleanwater_in.opened_ctx():
            self.scale.wait_for(weight)

    def heat_to(self, temperature):
        with self.stove.enabled_ctx():
            self.temp_sensor.wait_for(temperature)

@struct
class Brewery(object):
    def __init__(self, boiler, mashtank, boiler_to_mashtank_pump):
        pass

    @contextmanager
    def pouring_from_boiler_to_mashtank_ctx(self, weight):
        with \
            self.boiler.valve_to_mashtank.opened_ctx(), \
            self.mashtank.valve_from_boiler.opened_ctx() \
        :
            time.sleep(2)
            with self.boiler_to_mashtank_pump.enabled_ctx():
                yield
            time.sleep(2)

def main():
    logging.basicConfig(level=INFO)

    with \
        open_phidget(InterfaceKit, 262521) as relay_kit1, \
        open_phidget(InterfaceKit, 259263) as relay_kit2, \
        open_phidget(Bridge, 141089) as bridge, \
        open_phidget(TemperatureSensor, 167013) as temperature_sensor, \
        open_phidget(InterfaceKit, 150045) as interface_kit \
    :
        ctl = RelayController(
            direction_relay = Relay(relay_kit1, 7),
            layer_relay = Relay(relay_kit1, 3),
            control_relays = [
                Relay(relay_kit1, 0),
                Relay(relay_kit1, 1),
                Relay(relay_kit1, 2),
                Relay(relay_kit1, 4),
                Relay(relay_kit1, 5),
                Relay(relay_kit1, 6),
            ],
        )

        brewery = Brewery(
            boiler = Boiler(
                valve_cleanwater_in = SolenoidValve('boiler_valve_cleanwater_in',       ComplexRelay(ctl, 1, layer=1)),
                valve_water_in      = MotorValve.from_ctl('boiler_valve_water_in',      ctl, 4, layer=1),
                valve_wort_out      = MotorValve.from_ctl('boiler_valve_wort_out',      ctl, 0, layer=1),
                valve_flush         = MotorValve.from_ctl('boiler_valve_flush',         ctl, 2, layer=1),
                valve_to_mashtank   = MotorValve.from_ctl('boiler_valve_to_mashtank',   ctl, 5, layer=1),
                valve_from_mashtank = MotorValve.from_ctl('boiler_valve_from_mashtank', ctl, 3, layer=1),
                temp_sensor         = Thermocouple(temperature_sensor, 0, ThermocoupleType.PHIDGET_TEMPERATURE_SENSOR_K_TYPE),
                scale               = Scale(bridge, 3, a=91.85688697010055, b=22.855995958296976),
                stove               = Stove(
                    power_relay = Relay(relay_kit2, 2),
                    on_off_relay = Relay(relay_kit2, 0),
                    program_relay = Relay(relay_kit2, 1),
                ),
            ),
            mashtank = """MashTank(
                scale       = Scale(bridge, 2, a=1.0, b=-0.1242447059),
                temp_sensor = Thermocouple(
                    temperature_sensor,
                    index = 1,
                    thermocouple_type = ThermocoupleType.PHIDGET_TEMPERATURE_SENSOR_K_TYPE),
            )""",
            boiler_to_mashtank_pump = """Pump(Relay(relay_kit2, 3))""",
        )

        sched(All(
            Call(brewery.boiler.fill_with_cleanwater, Kilos(20)),
            Call(lambda: sched(Sleep(10)); brewery.boiler.heat_to(ge, Celcius(80))),
        ))


        def keep_boiler_water_level(comp, ):
            brewery.boiler.scale.wait(le, )
        def keep_boiler_water_temp(ge, Celcius(80)):

        with \
            brewery.mashtank.stiring_ctx(), \
            brewery.pouring_from_boiler_to_mashtank_ctx() \
        :
            brewery.mashtank.temp_sensor.wait_for(lambda t: t >= Celcius(65))

#        task heater:
#            brewery.boiler.fill_with_cleanwater(Kilos(20))
#            brewery.boiler.keep_heated_to(Celcius(90))

        brewery.mashtank.stir(Minutes(1))
        time.sleep(Minutes(30))
 #       kill heater
        brewery.boiler.heat_to(Celcius(90))
        brewery.pour_from_boiler_to_mashtank(Kilos(5))

        import code
        code.interact(local=locals())
        sys.exit(0)

if __name__ == '__main__':
    start_scheduler(entry_func=main)

