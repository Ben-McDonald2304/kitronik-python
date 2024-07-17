from microbit import i2c, sleep

# Useful Constants
CHIP_ADDRESS = 0x6F
RTC_SECONDS_REG = 0x00
RTC_MINUTES_REG = 0x01
RTC_HOURS_REG = 0x02
RTC_WEEKDAY_REG = 0x03
RTC_DAY_REG = 0x04
RTC_MONTH_REG = 0x05
RTC_YEAR_REG = 0x06
RTC_CONTROL_REG = 0x07
RTC_OSCILLATOR_REG = 0x08
RTC_PWR_UP_MINUTE_REG = 0x1C

RTC_ALM0_SEC_REG = 0x0A
RTC_ALM0_MIN_REG = 0x0B
RTC_ALM0_HOUR_REG = 0x0C
RTC_ALM0_WEEKDAY_REG = 0x0D
RTC_ALM0_DATE_REG = 0x0E
RTC_ALM0_MONTH_REG = 0x0F

RTC_ALM1_SEC_REG = 0x11
RTC_ALM1_MIN_REG = 0x12
RTC_ALM1_HOUR_REG = 0x13
RTC_ALM1_WEEKDAY_REG = 0x14
RTC_ALM1_DATE_REG = 0x15
RTC_ALM1_MONTH_REG = 0x16

START_RTC = 0x80
STOP_RTC = 0x00

ENABLE_BATTERY_BACKUP = 0x08

# Global Variables
currentSeconds = 0
currentMinutes = 0
currentHours = 0
currentWeekDay = 0
currentDay = 0
currentMonth = 0
currentYear = 0

# Convert a decimal number to BCD
def dec_to_bcd(value):
    tens = value // 10
    units = value % 10
    bcd_number = (tens << 4) | units
    return bcd_number

# Convert a BCD to decimal number
def bcd_to_dec(value, read_reg):
    mask = 0
    if read_reg in (RTC_SECONDS_REG, RTC_MINUTES_REG):
        mask = 0x70
    elif read_reg in (RTC_HOURS_REG, RTC_DAY_REG):
        mask = 0x30
    elif read_reg == RTC_MONTH_REG:
        mask = 0x10
    elif read_reg == RTC_YEAR_REG:
        mask = 0xF0

    units = value & 0x0F
    tens = (value & mask) >> 4
    dec_number = (tens * 10) + units
    return dec_number

# Initialize the MCP7940-N RTC
def init_RTC():
    # First set the external oscillator
    i2c.write(CHIP_ADDRESS, bytearray([RTC_CONTROL_REG, 0x00]))

    # Reading weekday register to set the Battery backup supply
    i2c.write(CHIP_ADDRESS, bytearray([RTC_WEEKDAY_REG]))
    read_buf = i2c.read(CHIP_ADDRESS, 1)
    read_weekday_reg = read_buf[0]
    if (read_weekday_reg & ENABLE_BATTERY_BACKUP) == 0:
        i2c.write(CHIP_ADDRESS, bytearray([RTC_WEEKDAY_REG, ENABLE_BATTERY_BACKUP | read_weekday_reg]))

    # Read current seconds for masking start RTC bit
    i2c.write(CHIP_ADDRESS, bytearray([RTC_SECONDS_REG]))
    read_buf = i2c.read(CHIP_ADDRESS, 1)
    read_current_seconds = read_buf[0]

    # Start the oscillator
    i2c.write(CHIP_ADDRESS, bytearray([RTC_SECONDS_REG, START_RTC | read_current_seconds]))

# Read all the time and date registers
def read_value():
    global currentSeconds, currentMinutes, currentHours, currentWeekDay, currentDay, currentMonth, currentYear

    # Set read from seconds register to receive all the information to global variables
    i2c.write(CHIP_ADDRESS, bytearray([RTC_SECONDS_REG]))
    read_buf = i2c.read(CHIP_ADDRESS, 7)
    currentSeconds = read_buf[0]
    currentMinutes = read_buf[1]
    currentHours = read_buf[2]
    currentWeekDay = read_buf[3]
    currentDay = read_buf[4]
    currentMonth = read_buf[5]
    currentYear = read_buf[6]

# Calculate which day of the week a particular date is
def calc_weekday(date, month, year):
    day_offset = [0, 3, 2, 5, 0, 3, 5, 1, 4, 6, 2, 4]
    if month < 3:
        year -= 1
    weekday = (year + year // 4 - year // 100 + year // 400 + day_offset[month - 1] + date) % 7
    return weekday + 1  # Add 1 so range is 1-7 which matches the RTC chip setup


# Function to set time on the RTC
def set_time(set_hours, set_minutes, set_seconds):
    bcd_hours = dec_to_bcd(set_hours)
    bcd_minutes = dec_to_bcd(set_minutes)
    bcd_seconds = dec_to_bcd(set_seconds)

    # Disable Oscillator
    i2c.write(CHIP_ADDRESS, bytearray([RTC_SECONDS_REG, STOP_RTC]))

    # Send new Hours value
    i2c.write(CHIP_ADDRESS, bytearray([RTC_HOURS_REG, bcd_hours]))

    # Send new Minutes value
    i2c.write(CHIP_ADDRESS, bytearray([RTC_MINUTES_REG, bcd_minutes]))

    # Send new Seconds value masked with the Enable Oscillator
    i2c.write(CHIP_ADDRESS, bytearray([RTC_SECONDS_REG, START_RTC | bcd_seconds]))


def read_time():
    # Read Values
    read_value()

    # Convert number to Decimal
    dec_seconds = bcd_to_dec(currentSeconds, RTC_SECONDS_REG)
    dec_minutes = bcd_to_dec(currentMinutes, RTC_MINUTES_REG)
    dec_hours = bcd_to_dec(currentHours, RTC_HOURS_REG)

    # Combine hours, minutes, and seconds into one string
    str_time = "{:02}:{:02}:{:02}".format(dec_hours, dec_minutes, dec_seconds)

    return str_time


# Function to set the date on the RTC
def set_date(set_day, set_month, set_year):
    leap_year_check = 0
    bcd_day = 0
    bcd_months = 0
    bcd_years = 0
    read_current_seconds = 0

    # Check day entered does not exceed month that has 30 days in
    if set_month in [4, 6, 9, 11]:
        if set_day == 31:
            set_day = 30

    # Leap year check and does not exceed 30 days
    if set_month == 2 and set_day >= 29:
        leap_year_check = set_year % 4
        if leap_year_check == 0:
            set_day = 29
        else:
            set_day = 28

    weekday = calc_weekday(set_day, set_month, set_year + 2000)

    bcd_day = dec_to_bcd(set_day)  # Convert number to binary coded decimal
    bcd_months = dec_to_bcd(set_month)  # Convert number to binary coded decimal
    bcd_years = dec_to_bcd(set_year)  # Convert number to binary coded decimal

    # Read current seconds for masking start RTC bit
    i2c.write(CHIP_ADDRESS, bytearray([RTC_SECONDS_REG]))
    read_buf = i2c.read(CHIP_ADDRESS, 1)
    read_current_seconds = read_buf[0]

    # Disable Oscillator
    i2c.write(CHIP_ADDRESS, bytearray([RTC_SECONDS_REG, STOP_RTC]))

    # Send new Weekday value
    i2c.write(CHIP_ADDRESS, bytearray([RTC_WEEKDAY_REG, weekday]))

    # Send new Day value
    i2c.write(CHIP_ADDRESS, bytearray([RTC_DAY_REG, bcd_day]))

    # Send new Months value
    i2c.write(CHIP_ADDRESS, bytearray([RTC_MONTH_REG, bcd_months]))

    # Send new Year value
    i2c.write(CHIP_ADDRESS, bytearray([RTC_YEAR_REG, bcd_years]))

    # Enable Oscillator
    i2c.write(CHIP_ADDRESS, bytearray([RTC_SECONDS_REG, START_RTC | read_current_seconds]))

def read_date():
    global currentDay, currentMonth, currentYear

    # Read Values
    read_value()

    # Convert number to Decimal
    dec_day = bcd_to_dec(currentDay, RTC_DAY_REG)
    dec_months = bcd_to_dec(currentMonth, RTC_MONTH_REG)
    dec_years = bcd_to_dec(currentYear, RTC_YEAR_REG)

    # Combine day, month, and year into one string
    str_date = "{:02}/{:02}/{:02}".format(dec_day, dec_months, dec_years)

    return str_date

