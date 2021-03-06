# FeatherClock 1.1.0 #

This repo contains code written for the [Adafruit Feather HUZZAH ESP8266](https://www.adafruit.com/product/2821) running [MicroPython](http://docs.micropython.org/en/latest/index.html). It now includes a version for the [Adafruit Feather HUZZAH ESP32](https://www.adafruit.com/product/3405) too.

It is an initial attempt to replicate my [Electric Imp clock project](https://github.com/smittytone/Clock). It uses the [Adafruit FeatherWing](https://learn.adafruit.com/adafruit-7-segment-led-featherwings/overview) four-digit, seven-segment LED add-on.

Currently, the clock has no remote control, which the Electric Imp Platform makes very easy to implement, but is rather less so here. You can [set preferences](#clock-settings), though. Adding a web UI, served locally or remotely, lies in a future phase of the project.

### Installation ###

#### Pre-requisites ####

1. `pip3 install adafruit-ampy`
1. `pip3 install esptool`
1. Running macOS Big Sur? You also need:
    1. `nano /usr/local/bin/esptool.py`
    1. Comment out lines 56 to 61 inclusive
    1. Save the file
1. Connect your assembled Feather Clock (Feather plus LED add-on).
1. `ls /dev/cu*`
    1. Note the Feather’s device file path.
1. Update MicroPython:
    1. `esptool.py --port <FEATHER_DEVICE_PATH> erase_flash`
    1. `esptool.py --port <FEATHER_DEVICE_PATH> --baud 460800 write_flash --flash_size=detect 0 esp8266-20200911-v1.13.bin`
1. Run `./install-app.sh <FEATHER_DEVICE_PATH>`
1. Press `Enter` to continue or `Q` to quit.
1. Enter your WiFi SSID.
1. Enter your WiFi password.
1. After the code has copied, power-cycle your Feather Clock or press the RESET button.

### Clock Settings ###

For now, the clock’s prefs are set by sending over a `prefs.json` file with the following values:

```
{ "mode":   <true/false>,   # 24-hour (true) or 12-hour (false)
  "colon":  <true/false>,   # Show a colon between the hours and minutes readouts
  "flash":  <true/false>,   # Flash the colon symbol, if it's shown
  "bright": 10,             # Display brightness from 1 (dim) to 15 (bright)
  "bst":    <true/false> }  # Auto-adjust for Daylight Saving Time
```

Having installed `ampy` as above, you send over prefs file using:

```
ampy --port <FEATHER_DEVICE_PATH> put prefs.json
```

### To Do ###

- Web UI for clock settings control.

### Release History ###

- 1.1.0 *3 December 2020*
    - Revised code.
    - Matrix display version.
- 1.0.10 *19 November 2020*
    - Adds Feather Huzzah 32 version.
- 1.0.9 *29 September 2020*
    - Improve RTC time checks.
    - Improve installation script.
- 1.0.8 *6 September 2019*
    - Add installation script.
- 1.0.7 *25 April 2019*
    - Add optional on-device JSON prefs (`prefs.json`) loading.
- 1.0.6 *13 April 2019*
    - Add app preferences structure.
- 1.0.5 *10 April 2019*
    - Correct the months used for BST checking.
- 1.0.4 *9 April 2019*
    - Various linting-suggested code improvements.
- 1.0.3 *8 April 2019*
    - Improve RTC updates by making NTP checks.
- 1.0.2 &mdash; *5 April 2019*
    - Add regular RTC updates.
- 1.0.1 *4 April 2019*
    - Add disconnection indicator to display.
    - Correct constant usage.
- 1.0.0 *3 April 2019*
    - Initial release.

### Licence ###

FeatherClock is copyright 2020, Tony Smith. It is released under the MIT licence.