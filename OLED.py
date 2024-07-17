from microbit import i2c, sleep

# ASCII font table
font = [
    0x0022d422, 0x0022d422, 0x0022d422, 0x0022d422, 0x0022d422, 0x0022d422, 0x0022d422, 0x0022d422,
    0x0022d422, 0x0022d422, 0x0022d422, 0x0022d422, 0x0022d422, 0x0022d422, 0x0022d422, 0x0022d422,
    0x0022d422, 0x0022d422, 0x0022d422, 0x0022d422, 0x0022d422, 0x0022d422, 0x0022d422, 0x0022d422,
    0x0022d422, 0x0022d422, 0x0022d422, 0x0022d422, 0x0022d422, 0x0022d422, 0x0022d422, 0x0022d422,
    0x00000000, 0x000002e0, 0x00018060, 0x00afabea, 0x00aed6ea, 0x01991133, 0x010556aa, 0x00000060,
    0x000045c0, 0x00003a20, 0x00051140, 0x00023880, 0x00002200, 0x00021080, 0x00000100, 0x00111110,
    0x0007462e, 0x00087e40, 0x000956b9, 0x0005d629, 0x008fa54c, 0x009ad6b7, 0x008ada88, 0x00119531,
    0x00aad6aa, 0x0022b6a2, 0x00000140, 0x00002a00, 0x0008a880, 0x00052940, 0x00022a20, 0x0022d422,
    0x00e4d62e, 0x000f14be, 0x000556bf, 0x0008c62e, 0x0007463f, 0x0008d6bf, 0x000094bf, 0x00cac62e,
    0x000f909f, 0x000047f1, 0x0017c629, 0x0008a89f, 0x0008421f, 0x01f1105f, 0x01f4105f, 0x0007462e,
    0x000114bf, 0x000b6526, 0x010514bf, 0x0004d6b2, 0x0010fc21, 0x0007c20f, 0x00744107, 0x01f4111f,
    0x000d909b, 0x00117041, 0x0008ceb9, 0x0008c7e0, 0x01041041, 0x000fc620, 0x00010440, 0x01084210,
    0x00000820, 0x010f4a4c, 0x0004529f, 0x00094a4c, 0x000fd288, 0x000956ae, 0x000097c4, 0x0007d6a2,
    0x000c109f, 0x000003a0, 0x0006c200, 0x0008289f, 0x000841e0, 0x01e1105e, 0x000e085e, 0x00064a4c,
    0x0002295e, 0x000f2944, 0x0001085c, 0x00012a90, 0x010a51e0, 0x010f420e, 0x00644106, 0x01e8221e,
    0x00093192, 0x00222292, 0x00095b52, 0x0008fc80, 0x000003e0, 0x000013f1, 0x00841080, 0x0022d422
]

# Constants
NUMBER_OF_CHAR_PER_LINE = 26
DISPLAY_ADDR_1 = 0x3C
DISPLAY_ADDR_2 = 0x0A
displayAddress = DISPLAY_ADDR_1

pageBuf = bytearray(129)
ackBuf = bytearray(2)
writeOneByteBuf = bytearray(2)
writeTwoByteBuf = bytearray(3)
writeThreeByteBuf = bytearray(4)

initialised = 0

def write_one_byte(regValue):
    writeOneByteBuf[0] = 0
    writeOneByteBuf[1] = regValue
    i2c.write(displayAddress, writeOneByteBuf)

def write_two_byte(regValue1, regValue2):
    writeTwoByteBuf[0] = 0
    writeTwoByteBuf[1] = regValue1
    writeTwoByteBuf[2] = regValue2
    i2c.write(displayAddress, writeTwoByteBuf)

def write_three_byte(regValue1, regValue2, regValue3):
    writeThreeByteBuf[0] = 0
    writeThreeByteBuf[1] = regValue1
    writeThreeByteBuf[2] = regValue2
    writeThreeByteBuf[3] = regValue3
    i2c.write(displayAddress, writeThreeByteBuf)

def set_pos(col=0, page=0):
    write_one_byte(0xb0 | page)  # page number
    write_one_byte(0x00 | (col % 16))  # lower start column address
    write_one_byte(0x10 | (col >> 4))  # upper start column address

def clear_bit(d, b):
    if d & (1 << b):
        d -= (1 << b)
    return d

def init_display():
    global initialised

    # Load the ackBuffer to check if there is a display there before starting initialisation
    ackBuf[0] = 0
    ackBuf[1] = 0xAF
    try:
        i2c.write(displayAddress, ackBuf)
    except OSError:
        display_error()
        return

    # Start initializing the display
    write_one_byte(0xAE)  # SSD1306_DISPLAYOFF
    write_one_byte(0xA4)  # SSD1306_DISPLAYALLON_RESUME
    write_two_byte(0xD5, 0xF0)  # SSD1306_SETDISPLAYCLOCKDIV
    write_two_byte(0xA8, 0x3F)  # SSD1306_SETMULTIPLEX
    write_two_byte(0xD3, 0x00)  # SSD1306_SETDISPLAYOFFSET
    write_one_byte(0 | 0x0)  # line #SSD1306_SETSTARTLINE
    write_two_byte(0x8D, 0x14)  # SSD1306_CHARGEPUMP
    write_two_byte(0x20, 0x00)  # SSD1306_MEMORYMODE
    write_three_byte(0x21, 0, 127)  # SSD1306_COLUMNADDR
    write_three_byte(0x22, 0, 63)  # SSD1306_PAGEADDR
    write_one_byte(0xa0 | 0x1)  # SSD1306_SEGREMAP
    write_one_byte(0xc8)  # SSD1306_COMSCANDEC
    write_two_byte(0xDA, 0x12)  # SSD1306_SETCOMPINS
    write_two_byte(0x81, 0xCF)  # SSD1306_SETCONTRAST
    write_two_byte(0xd9, 0xF1)  # SSD1306_SETPRECHARGE
    write_two_byte(0xDB, 0x40)  # SSD1306_SETVCOMDETECT
    write_one_byte(0xA6)  # SSD1306_NORMALDISPLAY
    write_two_byte(0xD6, 0)  # Zoom is set to off
    write_one_byte(0xAF)  # SSD1306_DISPLAYON
    initialised = 1

    clear_display()


def clear_display():
    # Fill buffer with all 0's
    pageBuf = bytearray([0] * 128)
    pageBuf[0] = 0x40
    for y in range(8):
        set_pos(0, y)  # Set position to the start of the screen
        i2c.write(displayAddress, pageBuf)


# Function to convert any input data to a string
def convert_to_text(input_data):
    return str(input_data)

# Function to show text on the OLED display
def show(input_data, line=0):
    global pageBuf
    pageBuf = bytearray([0] * 128)
    input_string = convert_to_text(input_data) + " "

    if not initialised:
        init_display()

    y = line

    # Break input_string into lines
    string_array = []
    start_of_string = 0
    previous_space_point = 0

    for space_finder in range(len(input_string)):
        if input_string[space_finder] == " ":
            space_point = space_finder
            if (space_point - start_of_string) < NUMBER_OF_CHAR_PER_LINE:
                previous_space_point = space_point
                if space_finder == len(input_string) - 1:
                    string_array.append(input_string[start_of_string:space_point])
            elif (space_point - start_of_string) > NUMBER_OF_CHAR_PER_LINE:
                string_array.append(input_string[start_of_string:previous_space_point])
                start_of_string = previous_space_point + 1
            elif (space_point - start_of_string) == NUMBER_OF_CHAR_PER_LINE:
                string_array.append(input_string[start_of_string:space_point])
                start_of_string = space_point + 1
                previous_space_point = space_point

    if start_of_string < len(input_string):
        string_array.append(input_string[start_of_string:])

    # Write the text to the buffer and display it
    for text_line in range(len(string_array) - 1):
        display_string = string_array[text_line]

        for char_of_string in range(len(display_string)):
            char_display_bytes = font[ord(display_string[char_of_string])]
            for k in range(5):
                col = 0
                for l in range(5):
                    if char_display_bytes & (1 << (5 * k + l)):
                        col |= (1 << (l + 1))

                ind = (char_of_string * 5) + k + 1
                pageBuf[ind] = col

        set_pos(0, y)
        pageBuf[0] = 0x40
        i2c.write(displayAddress, pageBuf)
        y += 1

# Function to set the position on the display
def set_pos(x, y):
    i2c.write(displayAddress, bytearray([0x00, 0xB0 + y, 0x00 | (x & 0x0F), 0x10 | (x >> 4)]))

# Initialize the display variable
initialised = False