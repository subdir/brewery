#!/usr/bin/env python3
#
# pylint: disable=bad-continuation
# pylint: disable=missing-docstring

from __future__ import generator_stop

import sys, time, logging

from brewery_setup import make_brewery


def main():
    logging.basicConfig(level=logging.INFO)

    with make_brewery() as brewery:
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

