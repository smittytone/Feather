"""
Clock Segment ESP8266 - a very simple four-digit timepiece

Version:   1.1.1
Author:    smittytone
Copyright: 2020, Tony Smith
Licence:   MIT
"""

"""
Imports
"""
import usocket as socket
import ustruct as struct
import ujson as json
import network
from micropython import const
from machine import I2C, Pin, RTC
from utime import localtime, sleep


"""
Constants
(see http://docs.micropython.org/en/latest/reference/speed_python.html#the-const-declaration)
"""
_HT16K33_BLINK_CMD = const(0x80)
_HT16K33_BLINK_DISPLAY_ON = const(0x01)
_HT16K33_CMD_BRIGHTNESS = const(0xE0)
_HT16K33_SYSTEM_ON = const(0x21)
_HT16K33_COLON_ROW = const(0x04)
_HT16K33_MINUS_CHAR = const(0x10)
_HT16K33_DEGREE_CHAR = const(0x11)


class HT16K33:
    """
    A simple, generic driver for the I2C-connected Holtek HT16K33 controller chip.
    This release supports MicroPython and CircuitPython

    Version:    3.0.2
    Bus:        I2C
    Author:     Tony Smith (@smittytone)
    License:    MIT
    Copyright:  2020
    """

    # *********** CONSTANTS **********

    HT16K33_GENERIC_DISPLAY_ON = 0x81
    HT16K33_GENERIC_DISPLAY_OFF = 0x80
    HT16K33_GENERIC_SYSTEM_ON = 0x21
    HT16K33_GENERIC_SYSTEM_OFF = 0x20
    HT16K33_GENERIC_DISPLAY_ADDRESS = 0x00
    HT16K33_GENERIC_CMD_BRIGHTNESS = 0xE0
    HT16K33_GENERIC_CMD_BLINK = 0x81

    # *********** PRIVATE PROPERTIES **********

    i2c = None
    address = 0
    brightness = 15
    flash_rate = 0

    # *********** CONSTRUCTOR **********

    def __init__(self, i2c, i2c_address):
        assert 0x00 <= i2c_address < 0x80, "ERROR - Invalid I2C address in HT16K33()"
        self.i2c = i2c
        self.address = i2c_address
        self.power_on()

    # *********** PUBLIC METHODS **********

    def set_brightness(self, brightness=15):
        """
        Set the display's brightness (ie. duty cycle).

        Brightness values range from 0 (dim, but not off) to 15 (max. brightness).

        Args:
            brightness (int): The chosen flash rate. Default: 15 (100%).
        """
        if brightness < 0 or brightness > 15: brightness = 15
        self.brightness = brightness
        self._write_cmd(self.HT16K33_GENERIC_CMD_BRIGHTNESS | brightness)

    def draw(self):
        """
        Writes the current display buffer to the display itself.

        Call this method after updating the buffer to update
        the LED itself.
        """
        self._render()

    def clear(self):
        """
        Clear the buffer.

        Returns:
            The instance (self)
        """
        for i in range(0, len(self.buffer)): self.buffer[i] = 0x00
        return self

    def power_on(self):
        """
        Power on the controller and display.
        """
        self._write_cmd(self.HT16K33_GENERIC_SYSTEM_ON)
        self._write_cmd(self.HT16K33_GENERIC_DISPLAY_ON)

    def power_off(self):
        """
        Power on the controller and display.
        """
        self._write_cmd(self.HT16K33_GENERIC_DISPLAY_OFF)
        self._write_cmd(self.HT16K33_GENERIC_SYSTEM_OFF)

    # ********** PRIVATE METHODS **********

    def _render(self):
        """
        Write the display buffer out to I2C
        """
        buffer = bytearray(len(self.buffer) + 1)
        buffer[1:] = self.buffer
        buffer[0] = 0x00
        self.i2c.writeto(self.address, bytes(buffer))

    def _write_cmd(self, byte):
        """
        Writes a single command to the HT16K33. A private method.
        """
        self.i2c.writeto(self.address, bytes([byte]))


class HT16K33Segment(HT16K33):
    """
    Micro/Circuit Python class for the Adafruit 0.56-in 4-digit,
    7-segment LED matrix backpack and equivalent Featherwing.

    Version:    3.0.2
    Bus:        I2C
    Author:     Tony Smith (@smittytone)
    License:    MIT
    Copyright:  2020
    """

    # *********** CONSTANTS **********

    HT16K33_SEGMENT_COLON_ROW = 0x04
    HT16K33_SEGMENT_MINUS_CHAR = 0x10
    HT16K33_SEGMENT_DEGREE_CHAR = 0x11
    HT16K33_SEGMENT_SPACE_CHAR = 0x00

    # The positions of the segments within the buffer
    POS = (0, 2, 6, 8)

    # Bytearray of the key alphanumeric characters we can show:
    # 0-9, A-F, minus, degree
    CHARSET = b'\x3F\x06\x5B\x4F\x66\x6D\x7D\x07\x7F\x6F\x5F\x7C\x58\x5E\x7B\x71\x40\x63'

    # *********** CONSTRUCTOR **********

    def __init__(self, i2c, i2c_address=0x70):
        self.buffer = bytearray(16)
        super(HT16K33Segment, self).__init__(i2c, i2c_address)

    # *********** PUBLIC METHODS **********

    def set_colon(self, is_set=True):
        """
        Set or unset the display's central colon symbol.

        This method updates the display buffer, but does not send the buffer to the display itself.
        Call 'draw()' to render the buffer on the display.

        Args:
            isSet (bool): Whether the colon is lit (True) or not (False). Default: True.

        Returns:
            The instance (self)
        """
        self.buffer[self.HT16K33_SEGMENT_COLON_ROW] = 0x02 if is_set is True else 0x00
        return self

    def set_glyph(self, glyph, digit=0, has_dot=False):
        """
        Present a user-defined character glyph at the specified digit.

        Glyph values are 8-bit integers representing a pattern of set LED segments.
        The value is calculated by setting the bit(s) representing the segment(s) you want illuminated.
        Bit-to-segment mapping runs clockwise from the top around the outside of the matrix; the inner segment is bit 6:

                0
                _
            5 |   | 1
              |   |
                - <----- 6
            4 |   | 2
              | _ |
                3

        This method updates the display buffer, but does not send the buffer to the display itself.
        Call 'draw()' to render the buffer on the display.

        Args:
            glyph (int):   The glyph pattern.
            digit (int):   The digit to show the glyph. Default: 0 (leftmost digit).
            has_dot (bool): Whether the decimal point to the right of the digit should be lit. Default: False.

        Returns:
            The instance (self)
        """
        assert 0 <= digit < 4, "ERROR - Invalid digit (0-3) set in set_glyph()"
        assert 0 <= glyph < 0xFF, "ERROR - Invalid glyph (0x00-0xFF) set in set_glyph()"
        self.buffer[self.POS[digit]] = glyph
        if has_dot is True: self.buffer[self.POS[digit]] |= 0x80
        return self

    def set_number(self, number, digit=0, has_dot=False):
        """
        Present single decimal value (0-9) at the specified digit.

        This method updates the display buffer, but does not send the buffer to the display itself.
        Call 'draw()' to render the buffer on the display.

        Args:
            number (int):  The number to show.
            digit (int):   The digit to show the number. Default: 0 (leftmost digit).
            has_dot (bool): Whether the decimal point to the right of the digit should be lit. Default: False.

        Returns:
            The instance (self)
        """
        assert 0 <= digit < 4, "ERROR - Invalid digit (0-3) set in set_number()"
        assert 0 <= number < 10, "ERROR - Invalid value (0-9) set in set_number()"
        return self.set_character(str(number), digit, has_dot)

    def set_character(self, char, digit=0, has_dot=False):
        """
        Present single alphanumeric character at the specified digit.

        Only characters from the class' character set are available:
        0, 1, 2, 3, 4, 5, 6, 7, 8, 9, a, b, c, d ,e, f, -.
        Other characters can be defined and presented using 'set_glyph()'.

        This method updates the display buffer, but does not send the buffer to the display itself.
        Call 'draw()' to render the buffer on the display.

        Args:
            char (string):  The character to show.
            digit (int):    The digit to show the number. Default: 0 (leftmost digit).
            has_dot (bool): Whether the decimal point to the right of the digit should be lit. Default: False.

        Returns:
            The instance (self)
        """
        assert 0 <= digit < 4, "ERROR - Invalid digit set in set_character()"
        char = char.lower()
        char_val = 0xFF
        if char == "deg":
            char_val = HT16K33_SEGMENT_DEGREE_CHAR
        elif char == '-':
            char_val = self.HT16K33_SEGMENT_MINUS_CHAR
        elif char == ' ':
            char_val = self.HT16K33_SEGMENT_SPACE_CHAR
        elif char in 'abcdef':
            char_val = ord(char) - 87
        elif char in '0123456789':
            char_val = ord(char) - 48
        assert char_val != 0xFF, "ERROR - Invalid char string set in set_character()"
        self.buffer[self.POS[digit]] = self.CHARSET[char_val]
        if has_dot is True: self.buffer[self.POS[digit]] |= 0x80
        return self


def is_bst(now=None):
    """
    Convenience function for 'bstCheck()'.

    Args:
        n (tuple): An 8-tuple indicating the request date
            (see http://docs.micropython.org/en/latest/library/utime.html?highlight=localtime#utime.localtime).

    Returns:
        bool: Whether the specified date is within the BST period (true), or not (false).
    """
    return bst_check(now)


def bst_check(now=None):
    """
    Determine whether the specified date lies within the British Summer Time period.

    Args:
        n (tuple): An 8-tuple indicating the request date
            (see http://docs.micropython.org/en/latest/library/utime.html?highlight=localtime#utime.localtime).

    Returns:
        bool: Whether the specified date is within the BST period (true), or not (false).
    """
    if now is None: now = localtime()

    if now[1] > 3 and now[1] < 10: return True

    if now[1] == 3:
        # BST starts on the last Sunday of March
        for index in range(31, 24, -1):
            if day_of_week(index, 3, now[0]) == 0 and now[2] >= index: return True

    if now[1] == 10:
        # BST ends on the last Sunday of October
        for index in range(31, 24, -1):
            if day_of_week(index, 10, now[0]) == 0 and now[2] < index: return True

    return False


def day_of_week(day, month, year):
    """
    Determine the day of the week for a given day, month and year, using
    Zeller's Rule (see http://mathforum.org/dr.math/faq/faq.calendar.html).

    Args:
        d (int): The specified day of the month (1-31).
        m (int): The specified month (1-12).
        y (int): The specified year (including the century, ie. '2019' not '19').

    Returns:
        int: The day of the week: 0 (Monday) to 6 (Sunday).
    """
    month -= 2
    if month < 1: month += 12
    century = int(str(year)[:2])
    year = int(str(year)[2:])
    year = year - 1 if month > 10 else year
    dow = day + int((13 * month - 1) / 5) + year + int(year / 4) + int(century / 4) - (2 * century)
    dow = dow % 7
    if dow < 0: dow += 7
    return dow


def is_leap_year(year):
    """
    Is the current year a leap year?

    Args:
        y (int): The year you wish to check.

    Returns:
        bool: Whether the year is a leap year (True) or not (False).
    """
    if year % 4 == 0 and (year % 100 > 0 or year % 400 == 0): return True
    return False


def get_time(timeout=10):
    # https://github.com/micropython/micropython/blob/master/ports/esp8266/modules/ntptime.py
    # Modify the standard code to extend the timeout, and catch OSErrors triggered when the
    # socket operation times out
    log("Getting time")
    ntp_query = bytearray(48)
    ntp_query[0] = 0x1b
    address = socket.getaddrinfo("pool.ntp.org", 123)[0][-1]
    # Create DGRAM UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(timeout)
    return_value = None
    err = 0
    try:
        err = 1
        log("Getting NTP data ")
        _ = sock.sendto(ntp_query, address)
        err = 2
        msg = sock.recv(48)
        log("Got NTP data ")
        err = 3
        val = struct.unpack("!I", msg[40:44])[0]
        return_value = val - 3155673600
    except:
        show_error(err)
    sock.close()
    return return_value


def set_rtc(timeout=10):
    now_time = get_time(timeout)
    if now_time is not None:
        time_data = localtime(now_time)
        time_data = time_data[0:3] + (0,) + time_data[3:6] + (0,)
        RTC().datetime(time_data)
        log("RTC set")
        return True
    log("RTC not set")
    return False


def load_prefs():
    file_data = None
    try:
        with open("prefs.json", "r") as file:
            file_data = file.read()
    except:
        print("Whoops: no prefs file")
        return

    if file_data != None:
        try:
            data = json.loads(file_data)
            set_prefs(data)
        except ValueError:
            print("Whoops: JSON decode error")


def set_prefs(prefs_data):
    """
    Set the clock's preferences to reflect the specified object's contents.
    """
    global prefs
    if "mode" in prefs_data: prefs["mode"] = prefs_data["mode"]
    if "colon" in prefs_data: prefs["colon"] = prefs_data["colon"]
    if "flash" in prefs_data: prefs["flash"] = prefs_data["flash"]
    if "bright" in prefs_data: prefs["bright"] = prefs_data["bright"]
    if "on" in prefs_data: prefs["on"] = prefs_data["on"]


def default_prefs():
    """
    Set the clock's default preferences.
    """
    global prefs
    prefs = {}
    prefs["mode"] = True
    prefs["colon"] = True
    prefs["flash"] = True
    prefs["bright"] = 10
    prefs["bst"] = True
    prefs["on"] = True
    prefs["url"] = "@AGENT"


def connect():
    """
    Attempt to connect to the Internet as a station, and flash the decimal
    point at the right-side of the display while the connection is in
    progress. Upon connection, set the RTC then start the clock.
    NOTE Replace '@SSID' and '@PASS' with your own WiFi credentials.
         The 'install-app.sh' script does this for you
    """
    global wout

    err = 0
    con_count = 0
    state = True
    glyph = 0x39
    if wout is None: wout = network.WLAN(network.STA_IF)
    if not wout.active(): wout.active(True)
    log("Connecting")
    if not wout.isconnected():
        # Attempt to connect
        wout.connect("@SSID", "@PASS")
        while not wout.isconnected():
            # Flash char 4's decimal point during connection
            sleep(0.5)
            matrix.set_glyph(glyph, 3, state).draw()
            state = not state
            con_count += 1
            if con_count > 40: break
    log("Connected")


def initial_connect():
    # Connect and get the time
    connect()
    timecheck = False
    if wout.isconnected(): timecheck = set_rtc(59)

    # Clear the display and start the clock loop
    matrix.clear()
    clock(timecheck)


def bcd(bin_value):
    for i in range(0, 8):
        bin_value = bin_value << 1
        if i == 7: break
        if (bin_value & 0xF00) > 0x4FF: bin_value += 0x300
        if (bin_value & 0xF000) > 0x4FFF: bin_value += 0x3000
    return (bin_value >> 8) & 0xFF


def clock(timecheck=False):
    """
    The primary clock routine: in infinite loop that displays the time
    from the UTC every pass and flips the display's central colon every
    second.
    NOTE The code calls 'isBST()' to determine if we are in British Summer Time.
         You will need to alter that call if you use some other form of daylight
         savings calculation.
    """

    mode = prefs["mode"]

    while True:
        now = localtime()
        now_hour = now[3]
        now_min = now[4]
        now_sec = now[5]

        if prefs["bst"] is True and is_bst() is True:
            now_hour += 1
        if now_hour > 23: now_hour -= 23

        is_pm = False
        if now_hour > 11: is_pm = True

        # Calculate and set the hours digits
        hour = now_hour
        if mode is False:
            if is_pm is True: hour -= 12
            if hour == 0: hour = 12

        # Display the hour
        # The decimal point by the first digit is used to indicate connection status
        # (lit if the clock is disconnected)
        decimal = bcd(hour)
        if mode is False and hour < 10:
            matrix.set_character(" ", 0, not wout.isconnected())
        else:
            matrix.set_number(decimal >> 4, 0, not wout.isconnected())
        matrix.set_number(decimal & 0x0F, 1, False)

        # Display the minute
        # The decimal point by the last digit is used to indicate AM/PM,
        # but only for the 12-hour clock mode (mode == False)
        decimal = bcd(now_min)
        matrix.set_number(decimal >> 4, 2, False)
        matrix.set_number(decimal & 0x0F, 3, is_pm if mode is False else False)

        # Set the colon and present the display
        matrix.set_colon(prefs["colon"])
        if prefs["colon"] is True and prefs["flash"] is True:
            matrix.set_colon(now_sec % 2 == 0)
        matrix.draw()

        # Every two hours re-sync the RTC
        # (which is poor, see http://docs.micropython.org/en/latest/esp8266/general.html#real-time-clock)
        if now_hour % 2 == 0 and (1 < now_min < 8) and timecheck is False:
            if not wout.isconnected(): connect()
            if wout.isconnected(): timecheck = set_rtc(59)

        # Reset the 'do check' flag every other hour
        if now_hour % 2 > 0: timecheck = False


def show_error(error_code):
    """
    Present a simple error message on the LED.
    """
    log("Error {}".format(error_code))
    matrix.clear()
    err_text = b'\x39\x50\x50'
    for i in range(0, 3): matrix.set_glyph(err_text[i], i)
    matrix.set_number(error_code, 3)
    matrix.draw()


def log(msg):
    now = localtime()
    with open("log.txt", "a") as file:
        file.write("{}-{}-{} {}:{}:{} - {}\n".format(now[0], now[1], now[2], now[3], now[4], now[5], msg))


def sync_text():
    """
    This function displays the text 'SYNC' on the display while the
    newly booted clock is connecting to the Internet and getting the
    current time.
    """
    matrix.clear()
    sync = b'\x6D\x6E\x37\x39'
    for i in range(0, 4): matrix.set_glyph(sync[i], i)
    matrix.draw()


"""
This is the simple runtime start point.
Set up the display on I2C
"""
prefs = None
wout = None

# Set default prefs
default_prefs()

# Load non-default prefs, if any
load_prefs()

# Initialize hardware
i2c = I2C(scl=Pin(5), sda=Pin(4))
matrix = HT16K33Segment(i2c)
matrix.set_brightness(prefs["bright"])

# Display 'sync' on the display while connecting,
# and attempt to connect
sync_text()
initial_connect()
