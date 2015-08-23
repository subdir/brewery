#!/usr/bin/env python3
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

from __future__ import generator_stop

import os, sys, time
import threading
import logging
from logging import log, INFO
from contextlib import contextmanager
from operator import ge, le
from collections import namedtuple

from brewery.units import *
from brewery.util import open_phidget
from brewery.relay import Relay, RelayController, ComplexRelay
from brewery.valve import MotorValve, SolenoidValve
from brewery.scale import Scale
from brewery.stove import Stove
from brewery.temperature import Thermocouple

from Phidgets.Devices.InterfaceKit import InterfaceKit
from Phidgets.Devices.Bridge import Bridge, BridgeGain
from Phidgets.Devices.TemperatureSensor import TemperatureSensor, ThermocoupleType


class Boiler(namedtuple('Boiler', [
    'valve_cleanwater_in',
    'valve_water_in',
    'valve_wort_out',
    'valve_flush',
    'valve_to_mashtank',
    'valve_from_mashtank',
    'temp_sensor',
    'scale',
    'stove',
])):
    def fill_with_cleanwater(self, weight):
        with self.valve_cleanwater_in.opened_ctx():
            self.scale.wait_for(weight)

    def heat_to(self, temperature):
        with self.stove.enabled_ctx():
            self.temp_sensor.wait_for(temperature)


class Brewery(namedtuple('Brewery', [
    'boiler',
    'mashtank',
    'boiler_to_mashtank_pump',
])):
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

        # Закрываем все клапаны
        for valve in (
            brewery.boiler.valve_water_in,
            brewery.boiler.valve_wort_out,
            brewery.boiler.valve_flush,
            brewery.boiler.valve_to_mashtank,
            brewery.boiler.valve_from_mashtank,
        ):
            print("Closing valve: {}...".format(valve.name))
            valve.close()

        # Набираем воду
        with brewery.boiler.valve_water_in.opened_ctx():
            with brewery.boiler.scale.enabled_ctx():
                while brewery.boiler.scale.read_weight_avg() < 30:
                    time.sleep(1)
                    print("filling", brewery.boiler.scale.read_weight())

        # Нагреваем
        with brewery.boiler.stove.enabled_ctx():
            while brewery.boiler.temp_sensor.read() < 45:
                time.sleep(1)
                print("heating", brewery.boiler.temp_sensor.read())

        # Сливаем
        with brewery.boiler.valve_flush.opened_ctx():
            with brewery.boiler.scale.enabled_ctx():
                while brewery.boiler.scale.read_weight_avg() > 7:
                    time.sleep(1)
                    print("flushing", brewery.boiler.scale.read_weight())

        import code
        code.interact(local=locals())
        sys.exit(0)


if __name__ == '__main__':
    main()

