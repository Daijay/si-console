# DRAFT REFERENCE, TO BE REVIEWED AND REWRITTEN BY THE TEAM.
# SI Console skeleton tests. Reference only. Not for Fallen submission.
# These tests check the GPIO pin map in gpio_map.py. No test
# touches real GPIO. No test needs a Pi. The map is the single
# source of truth. gpio_test.py imports it, it does not copy it.
# Run with: cd scratch && python3 -m pytest tests/test_gpio_map.py -v
"""GPIO map tests. Pins, channels, and resistors."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from si_console import gpio_map, gpio_test


def test_status_led_pins():
    # COORD GPIO5, AGENT 1 GPIO6, AGENT 2 GPIO13, GUARD GPIO19.
    assert gpio_map.STATUS_LEDS == {
        "COORD": 5,
        "AGENT 1": 6,
        "AGENT 2": 13,
        "GUARD": 19,
    }
    assert gpio_map.LED_COORD == 5
    assert gpio_map.LED_AGENT1 == 6
    assert gpio_map.LED_AGENT2 == 13
    assert gpio_map.LED_GUARD == 19


def test_button_pins():
    assert gpio_map.GREEN_BUTTON == 17
    assert gpio_map.RED_BUTTON == 27
    assert gpio_map.KILL_SWITCH == 22
    assert gpio_map.PTT_BUTTON == 23
    assert gpio_map.LANG_TOGGLE == 24


def test_button_led_pins():
    assert gpio_map.BUTTON_LEDS == {
        "green button": 20,
        "red button": 21,
    }
    assert gpio_map.LED_GREEN_BUTTON == 20
    assert gpio_map.LED_RED_BUTTON == 21


def test_gpio26_is_free_and_unused():
    assert gpio_map.GPIO26_FREE == 26
    used = set(gpio_map.STATUS_LEDS.values())
    used |= set(gpio_map.BUTTON_LEDS.values())
    used |= {
        gpio_map.GREEN_BUTTON,
        gpio_map.RED_BUTTON,
        gpio_map.KILL_SWITCH,
        gpio_map.PTT_BUTTON,
        gpio_map.LANG_TOGGLE,
    }
    assert 26 not in used


def test_no_pin_is_used_twice():
    pins = list(gpio_map.STATUS_LEDS.values())
    pins += list(gpio_map.BUTTON_LEDS.values())
    pins += [
        gpio_map.GREEN_BUTTON,
        gpio_map.RED_BUTTON,
        gpio_map.KILL_SWITCH,
        gpio_map.PTT_BUTTON,
        gpio_map.LANG_TOGGLE,
    ]
    assert len(pins) == len(set(pins))


def test_uln2003_channel_map():
    # Six channels used, IN7 tied to GND. Each channel maps one GPIO
    # pin to one ULN2003 input and output pin.
    assert len(gpio_map.ULN2003_CHANNELS) == 6
    assert 7 not in gpio_map.ULN2003_CHANNELS
    assert gpio_map.ULN2003_CHANNELS[1] == (1, 16, 5, "COORD")
    assert gpio_map.ULN2003_CHANNELS[2] == (2, 15, 6, "AGENT 1")
    assert gpio_map.ULN2003_CHANNELS[3] == (3, 14, 13, "AGENT 2")
    assert gpio_map.ULN2003_CHANNELS[4] == (4, 13, 19, "GUARD")
    assert gpio_map.ULN2003_CHANNELS[5] == (5, 12, 20, "green button")
    assert gpio_map.ULN2003_CHANNELS[6] == (6, 11, 21, "red button")


def test_led_resistors():
    # COORD green 150, AGENT 1 white 100, AGENT 2 blue 100, GUARD
    # yellow 220. Button LEDs have built-in resistors, so none here.
    assert gpio_map.LED_RESISTORS_OHM == {
        "COORD": 150,
        "AGENT 1": 100,
        "AGENT 2": 100,
        "GUARD": 220,
    }


def test_gpio_test_imports_the_same_map():
    # gpio_test.py must import the map, not keep its own copy. If
    # the map changes in gpio_map.py, the test script follows.
    assert gpio_test.STATUS_LEDS is gpio_map.STATUS_LEDS
    assert gpio_test.BUTTON_LEDS is gpio_map.BUTTON_LEDS
    assert gpio_test.GREEN_BUTTON == gpio_map.GREEN_BUTTON
    assert gpio_test.KILL_SWITCH == gpio_map.KILL_SWITCH
    assert gpio_test.LANG_TOGGLE == gpio_map.LANG_TOGGLE
