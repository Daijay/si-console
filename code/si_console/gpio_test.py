# GPIO test script. Run this on the Pi before connecting the bridge
# program. It tests buttons, LEDs through the ULN2003, the kill
# switch, and the language toggle, one at a time, with plain output.
# Usage on the Pi: python3 -m si_console.gpio_test
# Run it on a breadboard first. Solder later. Do not run it on a
# laptop. It needs real GPIO. It needs gpiozero, which does not work
# on a laptop. On a laptop it will fail at import, and that is fine.
# GPIO map imported from si_console/gpio_map.py. That file is the
# single source of truth for pins. Do not copy pin numbers here. The
# status LED names are COORD, AGENT 1, AGENT 2, GUARD. COORD is
# GPIO5, AGENT 1 is GPIO6, AGENT 2 is GPIO13, GUARD is GPIO19.
# All 6 LEDs run through the ULN2003. GPIO26 is free. ULN2003 IN7 is
# tied to GND.
# Buttons are inputs, GPIO to ground, internal pull up, active low.
# Green approve GPIO17, physical pin 11. Red reject GPIO27, pin 13.
# Kill freeze GPIO22, physical pin 15, wired normally closed.
# Push to talk GPIO23, physical pin 16.
# Language toggle GPIO24, physical pin 18.
# LEDs are outputs to ULN2003 inputs, not direct to LEDs. The
# ULN2003 inverts the signal and sinks current only. Its output is
# open collector. It pulls down to ground when its input is HIGH.
# It never drives HIGH. The LED path is 5V, then resistor, then LED
# anode, then LED cathode to the ULN2003 output, then chip GND.
# GPIO HIGH turns the LED on. GPIO LOW turns it off.
# ULN2003 pinout, VERIFIED from the datasheet: inputs pins 1 to 7,
# GND pin 8, COM pin 9 to the 5V load rail, outputs pins 16 to 10
# in reverse order. IN1 drives OUT1, IN2 drives OUT2, and so on.
# Channel map:
#   Ch1 IN1 pin 1 from GPIO5, OUT1 pin 16 to COORD LED, green, 150 ohm
#   Ch2 IN2 pin 2 from GPIO6, OUT2 pin 15 to AGENT 1 LED, white, 100 ohm
#   Ch3 IN3 pin 3 from GPIO13, OUT3 pin 14 to AGENT 2 LED, blue, 100 ohm
#   Ch4 IN4 pin 4 from GPIO19, OUT4 pin 13 to GUARD LED, yellow, 220 ohm
#   Ch5 IN5 pin 5 from GPIO20, OUT5 pin 12 to green button LED
#   Ch6 IN6 pin 6 from GPIO21, OUT6 pin 11 to red button LED
#   Ch7 spare. IN7 pin 7 tied to GND. Do not leave it floating.
# Resistor math: see docs/GPIO_PIN_MAP.md. Every Vf is ASSUMED.
# Measure the current with a multimeter on the bench. Do not guess.
# Button LEDs run from 5V through their built-in resistors. Do not add
# another resistor.
# ULN2003 input at 3.3V is test first, not guaranteed. The chip is
# sized for 5V TTL logic. Bench test every channel at 3.3V before
# soldering. If a channel is dim or warm, use a different driver,
# for example a logic level MOSFET per LED, or a TBD62083A, which is
# a 3.3V friendly Darlington array, LIKELY. Do not solder first.
# Kill switch logic: not pressed, NC closed, GPIO22 reads LOW,
# normal. Pressed and latched, NC open, GPIO22 reads HIGH, frozen.
# A broken wire also reads HIGH, frozen. That is fail safe. Test
# with a multimeter before trusting code. Poll every 100 ms. Do not
# rely on an edge event only.
# Debounce: gpiozero Button with bounce_time 0.05 s for green, red,
# and push to talk. Kill switch bounce_time 0.02 s. Test with 100
# button presses, no double execution. Use gpiozero, not RPi.GPIO.
# RPi.GPIO does not work on Pi 5.
"""GPIO test script. Buttons, LEDs via ULN2003, kill, toggle."""

from __future__ import annotations

import time

# GPIO map, Rev R2. Imported, not copied. gpio_map.py is the truth.
from si_console.gpio_map import (
    BUTTON_LEDS,
    GREEN_BUTTON,
    DEBOUNCE_SECONDS,
    KILL_DEBOUNCE_SECONDS,
    KILL_POLL_SECONDS,
    KILL_SWITCH,
    LANG_TOGGLE,
    PTT_BUTTON,
    RED_BUTTON,
    STATUS_LEDS,
)


def test_leds() -> None:
    """Turn on each LED for 1 second, in order. Watch each one.
    If a LED stays dark, check the resistor, the LED direction, the
    ULN2003 channel, and the 5V rail, in that order. If a LED is
    dim, check the resistor value and the 3.3V input to the ULN2003.
    If the chip is warm, stop. Check COM pin 9 to 5V, GND pin 8 to
    GND, and that no output is tied to 5V."""
    from gpiozero import LED

    print("LED test. Each LED should light for 1 second.")
    for name, pin in {**STATUS_LEDS, **BUTTON_LEDS}.items():
        print(f"  {name} GPIO{pin} on")
        led = LED(pin)
        led.on()
        time.sleep(1)
        led.off()
        led.close()
    print("LED test done. All LEDs off.")


def test_buttons() -> None:
    """Press each button once when asked. Prints what it saw.
    Green and red are active low. Kill is LOW normal, HIGH frozen.
    The toggle is read on change. Press Ctrl+C to stop."""
    from gpiozero import Button

    print("Button test. Press each button when asked. Ctrl+C to stop.")
    green = Button(GREEN_BUTTON, bounce_time=DEBOUNCE_SECONDS)
    red = Button(RED_BUTTON, bounce_time=DEBOUNCE_SECONDS)
    ptt = Button(PTT_BUTTON, bounce_time=DEBOUNCE_SECONDS)
    kill = Button(KILL_SWITCH, bounce_time=KILL_DEBOUNCE_SECONDS)
    lang = Button(LANG_TOGGLE, bounce_time=DEBOUNCE_SECONDS)
    try:
        input("Press green, then Enter: ")
        print(f"  green pressed: {green.is_pressed} (expect True)")
        input("Press red, then Enter: ")
        print(f"  red pressed: {red.is_pressed} (expect True)")
        input("Hold push to talk, then Enter: ")
        print(f"  push to talk held: {ptt.is_pressed} (expect True)")
        print(f"  kill frozen (HIGH): {kill.is_pressed} (expect False when normal)")
        print(f"  toggle state: {lang.is_pressed} (EN or ZH, label the switch)")
    finally:
        green.close()
        red.close()
        ptt.close()
        kill.close()
        lang.close()
    print("Button test done.")


def test_kill_loop(seconds: int = 10) -> None:
    """Poll the kill switch every 100 ms for N seconds. Print the
    state each time it changes. Press and release the kill switch
    during the test. A missed edge must not miss a kill, so polling
    is the rule, not edge events only."""
    from gpiozero import Button

    print(f"Kill poll test for {seconds} seconds. Press and release kill.")
    kill = Button(KILL_SWITCH, bounce_time=KILL_DEBOUNCE_SECONDS)
    last = kill.is_pressed
    print(f"  start frozen: {last} (expect False)")
    end = time.time() + seconds
    while time.time() < end:
        now = kill.is_pressed
        if now != last:
            print(f"  kill changed to frozen: {now}")
            last = now
        time.sleep(KILL_POLL_SECONDS)
    kill.close()
    print("Kill poll test done.")


def test_100_presses() -> None:
    """Press green 100 times. Counts presses. No double execution
    means the count is 100, not more. If one press counts twice,
    raise bounce_time from 0.05 s to 0.1 s and test again."""
    from gpiozero import Button

    print("100 press test. Press green 100 times, then Ctrl+C.")
    green = Button(GREEN_BUTTON, bounce_time=DEBOUNCE_SECONDS)
    count = [0]

    def on_press() -> None:
        count[0] += 1
        if count[0] % 10 == 0:
            print(f"  count {count[0]}")

    green.when_pressed = on_press
    try:
        while count[0] < 100:
            time.sleep(KILL_POLL_SECONDS)
    except KeyboardInterrupt:
        pass
    finally:
        green.close()
    print(f"100 press test done. Count: {count[0]} (expect 100).")


def main() -> None:
    """Run all tests in order: LEDs, buttons, kill poll."""
    import sys

    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    if which in ("all", "leds"):
        test_leds()
    if which in ("all", "buttons"):
        test_buttons()
    if which in ("all", "kill"):
        test_kill_loop()
    if which == "presses":
        test_100_presses()
    print("GPIO test done.")


if __name__ == "__main__":
    main()
