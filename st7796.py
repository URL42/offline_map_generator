from PIL import Image
import spidev
import RPi.GPIO as GPIO
import time

class ST7796:
    def __init__(self, width, height, rotation, port, cs, dc, rst, spi_speed_hz=40000000):
        self.width = width
        self.height = height
        self.rotation = rotation
        self.cs = cs
        self.dc = dc
        self.rst = rst

        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(self.cs, GPIO.OUT)
        GPIO.setup(self.dc, GPIO.OUT)
        GPIO.setup(self.rst, GPIO.OUT)

        self.spi = spidev.SpiDev()
        # Respect the chip select pin provided by the caller
        self.spi.open(port, cs)
        self.spi.max_speed_hz = spi_speed_hz
        self.spi.mode = 0

        self.reset()
        self.init_display()

    def reset(self):
        GPIO.output(self.rst, GPIO.HIGH)
        time.sleep(0.1)
        GPIO.output(self.rst, GPIO.LOW)
        time.sleep(0.1)
        GPIO.output(self.rst, GPIO.HIGH)
        time.sleep(0.1)

    def write_cmd(self, cmd):
        GPIO.output(self.dc, GPIO.LOW)
        GPIO.output(self.cs, GPIO.LOW)
        self.spi.writebytes([cmd])
        GPIO.output(self.cs, GPIO.HIGH)

    def write_data(self, data):
        GPIO.output(self.dc, GPIO.HIGH)
        GPIO.output(self.cs, GPIO.LOW)
        if isinstance(data, int):
            self.spi.writebytes([data])
        else:
            self.spi.writebytes(data)
        GPIO.output(self.cs, GPIO.HIGH)

    def init_display(self):
        self.write_cmd(0x11)  # Sleep Out
        time.sleep(0.1)
        self.write_cmd(0x36)
        self.write_data(0x48)  # MADCTL
        self.write_cmd(0x3A)
        self.write_data(0x55)  # COLMOD: 16-bit/pixel
        self.write_cmd(0x29)  # Display On
        time.sleep(0.1)

    def display(self, image):
        if image.mode != "RGB":
            image = image.convert("RGB")

        # Convert the RGB888 PIL image data to RGB565 expected by the display
        rgb = image.tobytes()
        pixelbytes = bytearray(len(rgb) // 3 * 2)
        j = 0
        for i in range(0, len(rgb), 3):
            r = rgb[i] & 0xF8
            g = rgb[i + 1] & 0xFC
            b = rgb[i + 2] & 0xF8
            value = (r << 8) | (g << 3) | (b >> 3)
            pixelbytes[j] = (value >> 8) & 0xFF
            pixelbytes[j + 1] = value & 0xFF
            j += 2

        self.write_cmd(0x2A)
        self.write_data([0x00, 0x00, (self.width-1) >> 8, (self.width-1) & 0xFF])
        self.write_cmd(0x2B)
        self.write_data([0x00, 0x00, (self.height-1) >> 8, (self.height-1) & 0xFF])
        self.write_cmd(0x2C)

        GPIO.output(self.dc, GPIO.HIGH)
        GPIO.output(self.cs, GPIO.LOW)
        self.spi.writebytes(pixelbytes)
        GPIO.output(self.cs, GPIO.HIGH)

