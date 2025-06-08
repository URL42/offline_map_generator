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
        self.spi.open(port, 0)
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
        pixelbytes = image.tobytes()

        self.write_cmd(0x2A)
        self.write_data([0x00, 0x00, (self.width-1) >> 8, (self.width-1) & 0xFF])
        self.write_cmd(0x2B)
        self.write_data([0x00, 0x00, (self.height-1) >> 8, (self.height-1) & 0xFF])
        self.write_cmd(0x2C)

        GPIO.output(self.dc, GPIO.HIGH)
        GPIO.output(self.cs, GPIO.LOW)
        self.spi.writebytes(list(pixelbytes))
        GPIO.output(self.cs, GPIO.HIGH)

