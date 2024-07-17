from microbit import i2c, sleep, running_time
import utime
import struct
import math

# Useful BME688 Register Addresses
CHIP_ADDRESS = 0x77
CTRL_MEAS = 0x74
RESET = 0xE0
CHIP_ID = 0xD0
CTRL_HUM = 0x72
CONFIG = 0x75
CTRL_GAS_0 = 0x70
CTRL_GAS_1 = 0x71

# Pressure Data
PRESS_MSB_0 = 0x1F
PRESS_LSB_0 = 0x20
PRESS_XLSB_0 = 0x21

# Temperature Data
TEMP_MSB_0 = 0x22
TEMP_LSB_0 = 0x23
TEMP_XLSB_0 = 0x24

# Humidity Data
HUMID_MSB_0 = 0x25
HUMID_LSB_0 = 0x26

# Gas Resistance Data
GAS_RES_MSB_0 = 0x2C
GAS_RES_LSB_0 = 0x2D

# Status
MEAS_STATUS_0 = 0x1D

# Oversampling rate constants
OSRS_1X = 0x01
OSRS_2X = 0x02
OSRS_4X = 0x03
OSRS_8X = 0x04
OSRS_16X = 0x05

# IIR filter coefficient values
IIR_0 = 0x00
IIR_1 = 0x01
IIR_3 = 0x02
IIR_7 = 0x03

def get_uint8(reg):
    i2c.write(CHIP_ADDRESS, bytearray([reg]))
    return i2c.read(CHIP_ADDRESS, 1)[0]

def get_int8(reg):
    i2c.write(CHIP_ADDRESS, bytearray([reg]))
    return struct.unpack('b', i2c.read(CHIP_ADDRESS, 1))[0]

def twos_comp(value, bits):
    if value & (1 << (bits - 1)):
        value -= 1 << bits
    return value

def i2c_write(reg, data):
    write_buf[0] = reg
    write_buf[1] = data
    i2c.write(CHIP_ADDRESS, write_buf)

PAR_T1 = twos_comp((get_uint8(0xEA) << 8) | get_uint8(0xE9), 16)
PAR_T2 = twos_comp((get_uint8(0x8B) << 8) | get_uint8(0x8A), 16)
PAR_T3 = get_int8(0x8C)

PAR_P1 = (get_uint8(0x8F) << 8) | get_uint8(0x8E)
PAR_P2 = twos_comp((get_uint8(0x91) << 8) | get_uint8(0x90), 16)
PAR_P3 = get_int8(0x92)
PAR_P4 = twos_comp((get_uint8(0x95) << 8) | get_uint8(0x94), 16)
PAR_P5 = twos_comp((get_uint8(0x97) << 8) | get_uint8(0x96), 16)
PAR_P6 = get_int8(0x99)
PAR_P7 = get_int8(0x98)
PAR_P8 = twos_comp((get_uint8(0x9D) << 8) | get_uint8(0x9C), 16)
PAR_P9 = twos_comp((get_uint8(0x9F) << 8) | get_uint8(0x9E), 16)
PAR_P10 = get_int8(0xA0)

parH1_LSB_parH2_LSB = get_uint8(0xE2)
PAR_H1 = (get_uint8(0xE3) << 4) | (parH1_LSB_parH2_LSB & 0x0F)
PAR_H2 = (get_uint8(0xE1) << 4) | (parH1_LSB_parH2_LSB >> 4)
PAR_H3 = get_int8(0xE4)
PAR_H4 = get_int8(0xE5)
PAR_H5 = get_int8(0xE6)
PAR_H6 = get_int8(0xE7)
PAR_H7 = get_int8(0xE8)

PAR_G1 = get_int8(0xED)
PAR_G2 = twos_comp((get_uint8(0xEC) << 8) | get_uint8(0xEB), 16)
PAR_G3 = get_uint8(0xEE)
RES_HEAT_RANGE = (get_uint8(0x02) >> 4) & 0x03
RES_HEAT_VAL = twos_comp(get_uint8(0x00), 8)

baseLinesSet = False
write_buf = bytearray(2)

tempRaw = 0
pressureRaw = 0
humidityRaw = 0
gasResRaw = 0
gasRange = 0


def calc_t_fine():
    var1 = (tempRaw >> 3) - (PAR_T1 << 1)
    var2 = (var1 * PAR_T2) >> 11
    var3 = (((var1 >> 1) * (var1 >> 1)) >> 12) * (PAR_T3 << 4) >> 14
    t_fine = var2 + var3

    return t_fine

# temperature in degrees C
def calc_temperature():
    t_fine = calc_t_fine()
    temp = ((t_fine * 5) + 128) >> 8
    temp = temp / 100 # Converting to floating point with 2 dp

    return temp

# pressure in pascals (int)
# needs t_fine
def calc_pressure():
    t_fine = calc_t_fine()

    var1 = (t_fine >> 1) - 64000
    var2 = ((((var1 >> 2) * (var1 >> 2)) >> 11) * PAR_P6) >> 2
    var2 = var2 + ((var1 * PAR_P5) << 1)
    var2 = (var2 >> 2) + (PAR_P4 << 16)
    var1 = (((((var1 >> 2) * (var1 >> 2)) >> 13) * (PAR_P3 << 5)) >> 3) + ((PAR_P2 * var1) >> 1)
    var1 = var1 >> 18
    var1 = ((32768 + var1) * PAR_P1) >> 15
    pRead = 1048576 - pressureRaw
    pRead = ((pRead - (var2 >> 12)) * 3125)

    if (pRead >= (1 << 30)):
        pRead = math.floor(pRead / var1) << 1

    else:
        pRead = math.floor((pRead << 1) / var1)

    var1 = (PAR_P9 * (((pRead >> 3) * (pRead >> 3)) >> 13)) >> 12
    var2 = ((pRead >> 2) * PAR_P8) >> 13
    var3 = ((pRead >> 8) * (pRead >> 8) * (pRead >> 8) * PAR_P10) >> 17
    pRead = pRead + ((var1 + var2 + var3 + (PAR_P7 << 7)) >> 4)

    return pRead


def calc_humidity():
    temp = calc_temperature()

    var1 = humidityRaw - (PAR_H1 << 4) - (math.floor((temp * PAR_H3) / 100) >> 1)
    var2 = (PAR_H2 * (math.floor((temp * PAR_H4) / 100) + math.floor((math.floor(temp * (math.floor((temp * PAR_H5) / 100))) >> 6) / 100) + ((1 << 14)))) >> 10
    var3 = var1 * var2
    var4 = ((PAR_H6 << 7) + (math.floor((temp * PAR_H7) / 100))) >> 4
    var5 = ((var3 >> 14) * (var3 >> 14)) >> 10
    var6 = (var4 * var5) >> 1
    hRead = (var3 + var6) >> 12
    hRead = (((var3 + var6) >> 10) * (1000)) >> 12
    hRead = math.floor(hRead / 1000)

    return hRead


def convert_gas_target_temp(targetTemp):
    temp = calc_temperature()

    var1 = math.floor((temp * PAR_G3) / 10) << 8
    var2 = (PAR_G1 + 784) * math.floor((math.floor(((PAR_G2 + 154009) * targetTemp * 5) / 100) + 3276800) / 10)
    var3 = var1 + (var2 >> 1)
    var4 = math.floor(var3 / (RES_HEAT_RANGE + 4))
    var5 = (131 * RES_HEAT_VAL) + 65536                 # Target heater resistance in Ohms
    resHeatX100 = ((math.floor(var4 / var5) - 250) * 34)
    resHeat = math.floor((resHeatX100 + 50) / 100)

    return resHeat


def calc_gas_resistance():
    var1 = 262144 >> gasRange
    var2 = 4096 + ((gasResRaw - 512) * 3)
    calcGasRes = math.floor((10000 * var1) / var2)

    gRes = calcGasRes * 100

    return gRes


def init_gas_sensor():
    # Define the target heater resistance from temperature (Heater Step 0)
    i2c_write(0x5A, convert_gas_target_temp(300))     # Write the target temperature (300°C) to res_wait_0 register - heater step 0

    # Define the heater on time, converting ms to register code (Heater Step 0) - cannot be greater than 4032ms
    # Bits <7:6> are a multiplier (1, 4, 16 or 64 times)    Bits <5:0> are 1ms steps (0 to 63ms)
    # i2cWrite(0x64, 101)        # Write the coded duration (101) of 150ms to gas_wait_0 register - heater step 0
    i2c_write(0x64, 109)        # Write the coded duration (109) of 180ms to gas_wait_0 register - heater step 0

    # Select index of heater step (0 to 9): CTRL_GAS_1 reg <3:0>    (Make sure to combine with gas enable setting already there)
    gasEnable = (get_uint8(write_buf[0]) & 0x20)
    i2c_write(CTRL_GAS_1, (0x00 | gasEnable))          # Select heater step 0


def read_air_quality():
    hWeight = 0.25
    # base humidity - average is around 40%
    hBase = 40

    # current temp
    currentTemp = calc_temperature()

    # using baselines if they have been set
    if baseLinesSet:
        ambTemp = tempBase
        gBase = gasBase
    else:
        ambTemp = currentTemp
        gBase = 0

    gRes = calc_gas_resistance()

    hRead = calc_humidity()
    humidityScore = 0
    gasScore = 0
    humidityOffset = hRead - hBase         # Calculate the humidity offset from the baseline setting


    temperatureOffset = currentTemp - ambTemp     # Calculate the temperature offset from the ambient temperature
    humidityRatio = ((humidityOffset / hBase) + 1)
    temperatureRatio = (temperatureOffset / ambTemp)


    # IAQ Calculations
    if (humidityOffset > 0):                                    # Different paths for calculating the humidity score depending on whether the offset is greater than 0
        humidityScore = (100 - hRead) / (100 - hBase)

    else:
        humidityScore = hRead / hBase

    humidityScore = humidityScore * hWeight * 100

    # for stopping division by 0 error
    if gBase == 0:
        # cant set to infinity like in TypeScript, python maths different
        gasRatio = 1e37
    else:
        gasRatio = (gRes / gBase)

    #gas score
    if ((gBase - gRes) > 0):                                            # Different paths for calculating the gas score depending on whether the offset is greater than 0
        gasScore = gasRatio * (100 * (1 - hWeight))

    else:
        # Make sure that when the gas offset and humidityOffset are 0, iaqPercent is 95% - leaves room for cleaner air to be identified
        gasScore = round(70 + (5 * (gasRatio - 1)))
        if (gasScore > 75):
            gasScore = 75

    iaqPercent = math.trunc(humidityScore + gasScore)               # Air quality percentage is the sum of the humidity (25% weighting) and gas (75% weighting) scores
    iaqScore = (100 - iaqPercent) * 5                               # Final air quality score is in range 0 - 500 (see BME688 datasheet page 11 for details)
    # here its off from the Typescript, but seems to be correct value
    eCO2Value = 250 * math.pow(math.e, (0.012 * iaqScore))      # Exponential curve equation to calculate the eCO2 from an iaqScore input

    # Adjust eCO2Value for humidity and/or temperature greater than the baseline values
    if (humidityOffset > 0):
        if (temperatureOffset > 0):
            eCO2Value = eCO2Value * (humidityRatio + temperatureRatio)

        else:
            eCO2Value = eCO2Value * humidityRatio

    elif (temperatureOffset > 0):
        eCO2Value = eCO2Value * (temperatureRatio + 1)

    eCO2Value = math.trunc(eCO2Value)

    # look at datasheet for meanings
    # eCO2 in ppm
    return iaqScore, iaqPercent, eCO2Value


# A baseline gas resistance is required for the IAQ calculation - it should be taken in a well ventilated area without obvious air pollutants
# Take 60 readings over a ~5min period and find the mean
def establish_baselines():
    global gasBase, tempBase, baseLinesSet
    count = 0
    gasResTotal = 0
    tempTotal = 0
    while (count < 60):               # Measure data and continue summing gas resistance until 60 readings have been taken
        read_data_registers()
        tempTotal += calc_temperature()
        gasResTotal += calc_gas_resistance()
        count += 1
        sleep(5000)
        print("Progress {}/60".format(count))

    gasBase = math.trunc(gasResTotal / 60)             # Find the mean gas resistance during the period to form the baseline
    tempBase = math.trunc(tempTotal / 60)    # Calculate the ambient temperature as the mean of the 60 initial readings

    baseLinesSet = True


def init_sensor():
    write_buf[0] = CHIP_ID
    chip_id = get_uint8(write_buf[0])
    while chip_id != 0x61:
        chip_id = get_uint8(write_buf[0])
    i2c_write(RESET, 0xB6)
    sleep(1000)
    i2c_write(CTRL_MEAS, 0x00)
    i2c_write(CTRL_HUM, OSRS_2X)
    i2c_write(CTRL_MEAS, (OSRS_2X << 5) | (OSRS_16X << 2))
    i2c_write(CONFIG, IIR_3 << 2)
    i2c_write(CTRL_GAS_1, 0x20)


def read_data_registers():
    global tempRaw, pressureRaw, humidityRaw, gasResRaw, gasRange, measTime

    o_sample_tp = get_uint8(write_buf[0])
    i2c_write(CTRL_MEAS, 0x01 | o_sample_tp)
    write_buf[0] = MEAS_STATUS_0
    new_data = (get_uint8(write_buf[0]) & 0x80) >> 7
    while new_data != 1:
        new_data = (get_uint8(write_buf[0]) & 0x80) >> 7
    write_buf[0] = GAS_RES_LSB_0
    heater_stable = (get_uint8(write_buf[0]) & 0x10) >> 4
    tempRaw = (get_uint8(TEMP_MSB_0) << 12) | (get_uint8(TEMP_LSB_0) << 4) | (get_uint8(TEMP_XLSB_0) >> 4)
    pressureRaw = (get_uint8(PRESS_MSB_0) << 12) | (get_uint8(PRESS_LSB_0) << 4) | (get_uint8(PRESS_XLSB_0) >> 4)
    humidityRaw = (get_uint8(HUMID_MSB_0) << 8) | get_uint8(HUMID_LSB_0)
    gasResRaw = (get_uint8(GAS_RES_MSB_0) << 2) | (get_uint8(GAS_RES_LSB_0) >> 6)
    gasRange = get_uint8(GAS_RES_LSB_0) & 0x0F
    measTime = running_time()

# initialise()
# init_gas_sensor()
# read_data_registers()

# #establish_baselines()

# while True:
#     read_data_registers()
#     temp = calc_temperature()
#     print("temp:", temp)
#     humidity = calc_humidity()
#     print("hum:", humidity)
#     pressure = calc_pressure()
#     print("press:", pressure)


#     iaqScore, iaqPercent, eCO2Value = read_air_quality()
#     print("air stuff:", iaqScore, iaqPercent, eCO2Value)

#     sleep(500)


