# DRAFT REFERENCE, TO BE REVIEWED AND REWRITTEN BY THE TEAM.
# SI Console skeleton code. Reference only. Not for Fallen submission.
# GPIO pin map, Rev R2, from ARCHITECTURE.md section 7 and the
# Rev R2 blueprint. This file is the single source of truth for
# pins. gpio_test.py and the bridge GPIO layer import from here.
# Do not copy pin numbers into other files. Import them.
# BCM numbers in code, physical pin numbers in comments.
# Buttons are inputs, GPIO to ground, internal pull up, active low.
# LEDs are outputs to ULN2003 inputs, not direct to LEDs. The
# ULN2003 sinks current only. Its output is open collector. It
# pulls down to ground when its input is HIGH. It never drives
# HIGH. The LED path is 5V, then resistor, then LED anode, then LED
# cathode to the ULN2003 output, then chip GND. GPIO HIGH turns
# the LED on. GPIO LOW turns it off.
# ULN2003 pinout, VERIFIED from the datasheet: inputs pins 1 to 7,
# GND pin 8, COM pin 9 to the 5V load rail, outputs pins 16 to 10
# in reverse order. IN1 drives OUT1, IN2 drives OUT2, and so on.
# What changed in Rev R2, 2026-11-22, and why the old names are gone:
# The R1 map named the LEDs signal, risk, execution, coordinator,
# with COORD on GPIO19 and AGENT 1 on GPIO5. The Rev R2 map names
# them COORD, AGENT 1, AGENT 2, GUARD, with COORD on GPIO5 and
# GUARD on GPIO19. The old names are deleted. Do not use them.
# The green LED resistor changed from 200 ohm in R1 to 150 ohm in
# Rev R2. IN7 is tied to GND, not through a resistor. GPIO26 is
# free, not wired. The R2 drawings and ARCHITECTURE.md sections 7
# and 9 carry the same map. If this file and the drawings disagree,
# the drawings are wrong until the team confirms the change.
"""GPIO pin map, Rev R2. Single source of truth for pins."""

from __future__ import annotations

# --- Buttons, inputs, active low ---------------------------------------
GREEN_BUTTON = 17   # physical pin 11, approve
RED_BUTTON = 27     # physical pin 13, reject
KILL_SWITCH = 22    # physical pin 15, NC, LOW normal, HIGH frozen
PTT_BUTTON = 23     # physical pin 16, push to talk
LANG_TOGGLE = 24    # physical pin 18, EN / ZH toggle

# --- Status LEDs, outputs to ULN2003 inputs -----------------------------
# Rev R2 names and pins. All 6 LEDs run through the ULN2003.
LED_COORD = 5       # physical pin 29, green, 150 ohm, ULN2003 Ch1
LED_AGENT1 = 6      # physical pin 31, red, 220 ohm, ULN2003 Ch2
LED_AGENT2 = 13     # physical pin 33, blue, 100 ohm, ULN2003 Ch3
LED_GUARD = 19      # physical pin 35, yellow, 220 ohm, ULN2003 Ch4

# --- Button LEDs, also through the ULN2003, from 5V, not from GPIO -----
LED_GREEN_BUTTON = 20  # physical pin 38, ULN2003 Ch5
LED_RED_BUTTON = 21    # physical pin 40, ULN2003 Ch6

# --- Free pin ------------------------------------------------------------
# GPIO26, physical pin 37, is FREE in Rev R2. Do not wire it.
# ULN2003 IN7 is tied to GND. Do not leave it floating.
GPIO26_FREE = 26

# --- ULN2003 channel map -------------------------------------------------
# Channel: (ULN2003 input pin, ULN2003 output pin, GPIO pin, LED name)
ULN2003_CHANNELS = {
    1: (1, 16, LED_COORD, "COORD"),
    2: (2, 15, LED_AGENT1, "AGENT 1"),
    3: (3, 14, LED_AGENT2, "AGENT 2"),
    4: (4, 13, LED_GUARD, "GUARD"),
    5: (5, 12, LED_GREEN_BUTTON, "green button"),
    6: (6, 11, LED_RED_BUTTON, "red button"),
}

# --- LED names and pins, for the test script and the screens -------------
STATUS_LEDS = {
    "COORD": LED_COORD,
    "AGENT 1": LED_AGENT1,
    "AGENT 2": LED_AGENT2,
    "GUARD": LED_GUARD,
}
BUTTON_LEDS = {
    "green button": LED_GREEN_BUTTON,
    "red button": LED_RED_BUTTON,
}

# --- Resistors, ohms, from ARCHITECTURE.md section 9, Rev R2 -----------
# R equals (5V minus Vf minus Vce_sat) divided by I. Vce_sat about
# 0.8V at 10 to 20 mA, ASSUMED. Green Vf 2.2V gives 13.3 mA at 150
# ohm. Red Vf 2.0V gives 10.0 mA at 220 ohm. Yellow Vf 2.1V gives
# 9.5 mA at 220 ohm. Blue Vf 3.2V gives 10.0 mA at 100 ohm.
# The green Vf is disputed: ARCHITECTURE.md uses 2.2V, LEAD_CHECKS.md
# uses 3.0V. Both are ASSUMED. The R2 schematic used the 3.0V value
# with the wrong arithmetic, (5 - 3.0 - 1.0) / 150 is 6.7 mA, not
# 13.3 mA. The R3 drawings use the 2.2V value and flag the conflict
# in red. Measure the real Vf with a multimeter on the bench before
# soldering. Do not guess. Button LEDs: EG STARTS style, 5V LED
# with a built in resistor, LIKELY. If the button LED has a built
# in resistor, do not add another one. Check the part before wiring.
LED_RESISTORS_OHM = {
    "COORD": 150,
    "AGENT 1": 220,
    "AGENT 2": 100,
    "GUARD": 220,
}

# --- Timing ---------------------------------------------------------------
# Debounce: gpiozero Button with bounce_time 0.05 s for green, red,
# and push to talk. Kill switch bounce_time 0.02 s. Kill poll every
# 100 ms. Use gpiozero, not RPi.GPIO. RPi.GPIO does not work on Pi 5.
DEBOUNCE_SECONDS = 0.05
KILL_DEBOUNCE_SECONDS = 0.02
KILL_POLL_SECONDS = 0.1
