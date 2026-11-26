# GPIO pin map

The written GPIO map for SI Console. `code/si_console/gpio_map.py` is the source of truth and this document must match it. Current values as decided by the owner (Jayden), 2026-11-24. First extracted from ARCHITECTURE.md on 2026-11-22; the earlier text is in git history. `blueprints/R5/wiring_diagram_R5.svg` must match too.

## Status LEDs and button LEDs (all through the ULN2003)

| LED | Colour | GPIO | Physical pin | ULN2003 input | ULN2003 output | Resistor |
| --- | --- | --- | --- | --- | --- | --- |
| COORD | green | GPIO5 | 29 | IN1 (pin 1) | OUT1 pin 16 | 150 ohm |
| AGENT 1 | white | GPIO6 | 31 | IN2 (pin 2) | OUT2 pin 15 | 100 ohm |
| AGENT 2 | blue | GPIO13 | 33 | IN3 (pin 3) | OUT3 pin 14 | 100 ohm |
| GUARD | yellow | GPIO19 | 35 | IN4 (pin 4) | OUT4 pin 13 | 220 ohm |
| Green button LED | green | GPIO20 | 38 | IN5 (pin 5) | OUT5 pin 12 | built into the button, no extra resistor |
| Red button LED | red | GPIO21 | 40 | IN6 (pin 6) | OUT6 pin 11 | built into the button, no extra resistor |
| Not used | none | none | none | IN7 (pin 7) tied to GND | OUT7 pin 10 unused | none |

## Buttons and switches (inputs)

| Control | GPIO | Physical pin | Ground | Notes |
| --- | --- | --- | --- | --- |
| Green button, approve | GPIO17 | 11 | Pi pin 14 | Internal pull-up, active low |
| Red button, reject | GPIO27 | 13 | Pi pin 20 | Internal pull-up, active low |
| Kill switch, NC | GPIO22 | 15 | common GND bus | Internal pull-up. LOW means normal, HIGH means frozen |
| Push to talk | GPIO23 | 16 | common GND bus | Internal pull-up, active low |
| EN/ZH toggle | GPIO24 | 18 | common GND bus | Toggle switch, read on change. EN when open, ZH when closed, or the reverse: pick one at build time and label the switch |

## Grounds

- The kill switch, push to talk and EN/ZH toggle grounds all go to the **common GND bus on the perfboard**.
- The bus is fed from Pi GND **pins 6, 9 and 14**.
- ULN2003 GND (pin 8) and IN7 (pin 7) connect to the same bus.
- The green button ground goes to Pi pin 14 and the red button ground to Pi pin 20.

## Software settings

GPIO: use gpiozero, not RPi.GPIO. RPi.GPIO does not work on Pi 5. That is confirmed from the previous blueprint. Debounce: gpiozero Button with bounce_time 0.05 seconds for green, red, and push to talk. Kill switch bounce_time 0.02 seconds. Test with 100 button presses, no double execution.

Do not use GPIO0 and GPIO1, physical 27 and 28, reserved for HAT ID. Do not use GPIO2 and GPIO3, physical 3 and 5, I2C. Do not use GPIO14 and GPIO15, physical 8 and 10, UART. Do not use GPIO7 to GPIO11, physical 19, 21, 23, 24, 26, SPI. That is confirmed from the previous blueprint. GPIO26, physical pin 37, is free and not wired.

## LED behaviour

Off means the agent has no task. Solid on means the agent is working. Slow blink means the agent is queued. Fast blink means the agent is blocked. When kill is active, all 4 status LEDs are off and the red button LED is solid on. The bridge updates LEDs from state.json, not from a timer alone. If the bridge dies, LEDs must go to a safe state: all off, except the red button LED solid on if kill was active. A systemd stop script must set all GPIO outputs low on exit, estimated, to be tested.

The green button LED glows when an approval is pending. The red button LED glows when kill is active.

## ULN2003 wiring

The ULN2003 is a 7 channel Darlington array, DIP-16. Pinout, confirmed from the datasheet: inputs pins 1 to 7 (IN1 to IN7), GND pin 8 (common emitter), COM pin 9 (common cathode of the flyback diodes, to the 5V rail), outputs in reverse order from pin 16 (OUT1) to pin 10 (OUT7). IN1 drives OUT1, IN2 drives OUT2, and so on. Check the pin numbers, not the physical position.

Status LED path: 5V rail, resistor, LED anode (long leg), LED cathode (short leg), ULN2003 output pin, chip GND pin 8, GND bus. The resistor is on the anode side.

Button LED path: 5V rail, button LED with its built-in resistor, ULN2003 output pin. No extra resistor. Check on the bench that the delivered buttons do have the built-in resistor, and measure the current, before leaving them powered.

The 5V rail comes from Pi pins 2 and 4. LEDs are never powered from a GPIO pin.

## Resistor check

R = (5 - Vf - Vce_sat) / I, so I = (5 - Vf - Vce_sat) / R. Vce_sat about 0.8V at 10 to 20 mA, estimated. Every forward voltage below is an estimate until measured on the bench with a multimeter.

| LED | Vf (not yet measured) | Resistor | Current |
| --- | --- | --- | --- |
| COORD green | 2.2 V | 150 ohm | 13.3 mA (8.0 mA if the real Vf is 3.0 V) |
| AGENT 1 white | 3.2 V | 100 ohm | 10.0 mA (12.0 mA if Vf is 3.0 V) |
| AGENT 2 blue | 3.2 V | 100 ohm | 10.0 mA |
| GUARD yellow | 2.1 V | 220 ohm | 9.5 mA |

Pass if each LED draws 5 to 20 mA, measured. A 1/4W resistor is fine.

Total LED current: about 43 mA for the 4 status LEDs plus 10 to 20 mA for each button LED, about 63 to 83 mA, estimated. The ULN2003 can sink 500 mA per channel, unconfirmed from the datasheet. Heat in the chip is about 0.07W, estimated. No heatsink is needed.

Common mistakes to avoid: do not connect an LED anode to a GPIO pin. Do not connect a ULN2003 output to 5V. Do not connect COM to ground. Do not leave the ULN2003 GND unconnected. Do not leave IN7 floating.
