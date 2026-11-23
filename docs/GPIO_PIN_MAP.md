# GPIO pin map, extracted from ARCHITECTURE.md
Source: ~/workspace/si-console-research-2/ARCHITECTURE.md
Extracted: 2026-11-22. Text below is copied verbatim, nothing edited or shortened.

## Section 7, GPIO map (lines 195-205)

GPIO: use gpiozero, not RPi.GPIO. RPi.GPIO does not work on Pi 5. That is VERIFIED from the previous blueprint. Debounce: gpiozero Button with bounce_time 0.05 seconds for green, red, and push to talk. Kill switch bounce_time 0.02 seconds. Test with 100 button presses, no double execution.
GPIO map, starting point from the brief, to be rechecked by the hardware worker against the ULN2003 change and the Pi 5 pinout:
Green approve, input, GPIO17, physical pin 11, to button switch terminal 1. Ground GND physical pin 14, to button switch terminal 2. Internal pull up, active low.
Red reject, input, GPIO27, physical pin 13, to button switch terminal 1. Ground GND physical pin 20, to button switch terminal 2. Internal pull up, active low.
Kill freeze, input, GPIO22, physical pin 15, to kill switch NC terminal 1. Ground GND physical pin 25, to kill switch NC terminal 2. Internal pull up. LOW means normal, HIGH means frozen.
Push to talk, input, GPIO23, physical pin 16. Internal pull up, active low.
Language toggle, input, GPIO24, physical pin 18. Toggle switch, not a button. Read on change, debounce 0.05 s. EN when open, ZH when closed, or the reverse, pick one at build time and label the switch.
LEDs, outputs to ULN2003 inputs, not direct to LEDs. See section 9. Signal LED input GPIO5, physical pin 29. Risk LED input GPIO6, physical pin 31. Execution LED input GPIO13, physical pin 33. Coordinator LED input GPIO19, physical pin 35. All through the ULN2003. Do not drive LEDs directly from these pins in the new design.
Do not use GPIO0 and GPIO1, physical 27 and 28, reserved for HAT ID. Do not use GPIO2 and GPIO3, physical 3 and 5, I2C. Do not use GPIO14 and GPIO15, physical 8 and 10, UART. Do not use GPIO7 to GPIO11, physical 19, 21, 23, 24, 26, SPI. That is VERIFIED from the previous blueprint.
LED behaviour: off means the agent has no task. Solid on means the agent is working. Slow blink means the agent is queued. Fast blink means the agent is blocked. All 4 agent LEDs off, plus the red button LED solid on, when kill is active. If the red button has no LED, all 4 agent LEDs off and KILL ACTIVE on both screens only. The bridge updates LEDs from state.json, not from a timer alone. If the bridge dies, LEDs must go to a safe state, all off, except the red button LED solid on if kill was active and the red button has an LED. A systemd stop script must set all GPIO outputs low on exit, ASSUMED, to be tested.
Button LEDs: the green button glows when an approval is pending. The red button glows when kill is active, if it has an LED. Button LEDs are driven through the ULN2003 from 5V, not from GPIO directly. See section 9. The ULN2003 has 7 channels. Four are used for status LEDs. Two are used for button LEDs. One is spare. That fits. If a seventh channel is needed, use the spare, do not add a second chip in v1.

## Section 9, ULN2003 wiring and resistor math (lines 261-286)

## 9. ULN2003 wiring and resistor math
The ULN2003 is a 7 channel Darlington array, DIP-16 or SO-16. Pinout, VERIFIED from the datasheet:
Inputs: pin 1 IN1, pin 2 IN2, pin 3 IN3, pin 4 IN4, pin 5 IN5, pin 6 IN6, pin 7 IN7.
GND: pin 8, common emitter, to GND.
COM: pin 9, common cathode of flyback diodes, to 5V load rail.
Outputs, reversed order: pin 16 OUT1, pin 15 OUT2, pin 14 OUT3, pin 13 OUT4, pin 12 OUT5, pin 11 OUT6, pin 10 OUT7.
IN1 drives OUT1. IN2 drives OUT2. And so on, down to IN7 driving OUT7. The output order is reversed against the input order on the chip body. Check the pin numbers, not the physical position.
Channel map for this build, ASSUMED as a plan, to be confirmed on the bench:
Channel 1: IN1 pin 1 from GPIO5, OUT1 pin 16 to signal LED cathode.
Channel 2: IN2 pin 2 from GPIO6, OUT2 pin 15 to risk LED cathode.
Channel 3: IN3 pin 3 from GPIO13, OUT3 pin 14 to execution LED cathode.
Channel 4: IN4 pin 4 from GPIO19, OUT4 pin 13 to coordinator LED cathode.
Channel 5: IN5 pin 5 from GPIO20, physical pin 38, for the green button LED, OUT5 pin 12 to green button LED cathode. Picked 2026-11-20 by lead decision. GPIO20 is free, not reserved. Record it in the wiring diagram. Do not use GPIO12 or GPIO16 for this LED.
Channel 6: IN6 pin 6 from GPIO21, physical pin 40, for the red button LED, OUT6 pin 11 to red button LED cathode. Picked 2026-11-20 by lead decision. GPIO21 is free, not reserved. Record it in the wiring diagram.
Channel 7: spare. Leave IN7 pin 7 unconnected, or tie it to GND through a resistor, ASSUMED. Do not leave it floating in the final build. Record the choice.
LED path per channel: 5V rail, then resistor, then LED anode, long leg, then LED cathode, short leg, then ULN2003 output pin, then chip GND pin 8 to system GND. The resistor is on the anode side, between 5V and the LED. The LED current flows through the chip to ground.
Resistor math: R equals (5V minus Vf minus Vce_sat) divided by I. Vce_sat is the chip drop, about 0.7 to 0.9V at 10 to 20 mA, ASSUMED, and about 0.9 to 1.1V at 100 mA, LIKELY. Use 0.8V for the calc, then test brightness on the bench.
Red LED, Vf about 2.0V, target 10 mA: R equals (5 minus 2.0 minus 0.8) divided by 0.010, equals 220 ohm. Use 220 ohm. Current about 10 mA. Power in resistor about 0.022W. A 1/4W resistor is fine.
Yellow LED, Vf about 2.1V, target 10 mA: R equals (5 minus 2.1 minus 0.8) divided by 0.010, equals 210 ohm. Use 220 ohm. Current about 9.5 mA.
Green LED, Vf about 2.2V, target 10 mA: R equals (5 minus 2.2 minus 0.8) divided by 0.010, equals 200 ohm. Use 200 ohm, or 220 ohm if 200 ohm is not in the kit. At 220 ohm the current is about 9.1 mA. That is bright enough in a booth, LIKELY. Test it.
Green Vf disagreement, not resolved: LEAD_CHECKS.md gives green Vf about 3.0V, which gives about 110 ohm at 10 mA, use 120 ohm. That disagrees with 2.2V and 200 ohm here. Both values are ASSUMED until the real LED part is measured on the bench with a multimeter. Do not change the resistor values in this file. Do not pick a winner. Measure Vf first, then recalculate with the formula in this section.
Blue LED, Vf about 3.2V, target 10 mA: R equals (5 minus 3.2 minus 0.8) divided by 0.010, equals 100 ohm. Use 100 ohm. Current about 10 mA.
Button LEDs, EG STARTS style, 5V LED with built in resistor, LIKELY, or a plain LED, UNVERIFIED for the exact part. If the button LED has a built in resistor, do not add another resistor. Check the part datasheet before wiring. If it is a plain LED, use the same math as above, with the LED colour Vf. Measure the current with a multimeter on the bench. Do not guess.
Total LED current: 4 status LEDs at about 10 mA each, plus 2 button LEDs at about 10 to 20 mA each, total about 60 to 80 mA, ASSUMED. The ULN2003 can sink 500 mA per channel, and about 2.5A total emitter current, LIKELY from the datasheet. That fits. The Pi 5V rail can supply it, but the LEDs must not be powered from a GPIO pin. They are powered from the 5V rail, through the ULN2003 to ground.
Heat: the ULN2003 at 80 mA total dissipates about 0.8V times 0.08A, equals about 0.064W, ASSUMED. That is cool. No heatsink is needed.
Common mistake to avoid: do not connect the LED anode to a GPIO pin and the cathode to the ULN2003. Do not connect the ULN2003 output to 5V. Do not connect COM to ground. Do not leave the ULN2003 GND unconnected. All four are wrong and will cause dim LEDs, a hot chip, or no light at all.

## Rev R4.1 update (2026-11-23), added after the verbatim extract above

The text above is unchanged. This section records the changes decided in R4.1.

- AGENT 1 LED is WHITE (was red in R2 and R3). Red is for reject and kill only.
- White LED resistor = 100 ohm (decided by Jayden). Same GPIO and channel as before: GPIO6, physical pin 31, ULN2003 IN2 pin 2, OUT2 pin 15.
- Check with the section 9 formula, Vf about 3.2 V (white LEDs are similar to blue) and Vce_sat 0.8 V, both ASSUMED: R = (5 - 3.2 - 0.8) / 0.010 = 100 ohm, current about 10 mA. If the real white LED has a Vf of 3.0 V the current is about 12 mA, still fine. Measure Vf on the bench as for the other colours.
- Final status LED map in the CAD: COORD green (GPIO5), AGENT 1 white (GPIO6, 100 ohm), AGENT 2 blue (GPIO13, 100 ohm), GUARD yellow (GPIO19). The other resistor values and the green Vf disagreement above are unchanged and still open.

