import sqlite3
import math
import io
import time
from PIL import Image, ImageDraw, ImageFont
from st7796 import ST7796
import serial
import pynmea2

# Constants
MBTILES_PATH = "/home/pi/GPS/maps/samplemap.mbtiles"
ZOOM = 15
TILE_SIZE = 256
SCREEN_WIDTH = 480
SCREEN_HEIGHT = 320
GPS_PORT = "/dev/ttyAMA0"
GPS_BAUDRATE = 115200

# Init display
display = ST7796(width=SCREEN_WIDTH, height=SCREEN_HEIGHT, rotation=270, port=0, cs=0, dc=24, rst=25)

# Tile cache
tile_cache = {}

def deg2num(lat, lon, zoom):
    lat_rad = math.radians(lat)
    n = 2.0 ** zoom
    xtile = int((lon + 180.0) / 360.0 * n)
    ytile = int((1.0 - math.log(math.tan(lat_rad) + (1 / math.cos(lat_rad))) / math.pi) / 2.0 * n)
    return xtile, ytile

def get_tile(z, x, y):
    key = (z, x, y)
    if key in tile_cache:
        return tile_cache[key]

    conn = sqlite3.connect(MBTILES_PATH)
    cursor = conn.cursor()
    y_tms = (2 ** z - 1) - y  # Convert to TMS tile scheme
    cursor.execute("SELECT tile_data FROM tiles WHERE zoom_level=? AND tile_column=? AND tile_row=?", (z, x, y_tms))
    row = cursor.fetchone()
    conn.close()

    if row:
        img = Image.open(io.BytesIO(row[0])).convert("RGB")
    else:
        img = Image.new("RGB", (TILE_SIZE, TILE_SIZE), "gray")

    tile_cache[key] = img
    return img

def get_composite_tile(lat, lon, zoom):
    cx, cy = deg2num(lat, lon, zoom)
    composite = Image.new("RGB", (TILE_SIZE * 5, TILE_SIZE * 5), "black")

    for dx in range(-2, 3):
        for dy in range(-2, 3):
            tx, ty = cx + dx, cy + dy
            tile = get_tile(zoom, tx, ty)
            px = (dx + 2) * TILE_SIZE
            py = (dy + 2) * TILE_SIZE
            composite.paste(tile, (px, py))

    crop_x = (TILE_SIZE * 5 - SCREEN_WIDTH) // 2
    crop_y = (TILE_SIZE * 5 - SCREEN_HEIGHT) // 2
    return composite.crop((crop_x, crop_y, crop_x + SCREEN_WIDTH, crop_y + SCREEN_HEIGHT))

def draw_overlay(image, lat, lon, heading):
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()

    cx, cy = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2
    draw.ellipse((cx - 4, cy - 4, cx + 4, cy + 4), fill="red")

    # Heading arrow
    arrow_len = 15
    arrow_x = cx + arrow_len * math.cos(math.radians(heading))
    arrow_y = cy - arrow_len * math.sin(math.radians(heading))
    draw.line((cx, cy, arrow_x, arrow_y), fill="blue", width=2)

    # Coordinates
    draw.text((5, 5), f"{lat:.5f}, {lon:.5f}", fill="red", font=font)

    # Compass label
    label = f"N {int(heading)}°"
    bbox = draw.textbbox((0, 0), label, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    draw.text((SCREEN_WIDTH - tw - 5, SCREEN_HEIGHT - th - 5), label, fill="red", font=font)

    return image

def get_gps_data(ser, max_lines=30):
    """Try to read up to `max_lines` lines from GPS and return lat/lon/heading.>
    for _ in range(max_lines):
        try:
            line = ser.readline().decode("ascii", errors="ignore").strip()
            if not line:
                continue

            if line.startswith("$GNRMC") or line.startswith("$GPRMC"):
                msg = pynmea2.parse(line)
                if getattr(msg, "status", "V") == "A":
                    heading = float(msg.true_course or 0)
                    return msg.latitude, msg.longitude, heading

            elif line.startswith("$GNGGA") or line.startswith("$GPGGA"):
                msg = pynmea2.parse(line)
                return msg.latitude, msg.longitude, 0
        except pynmea2.ParseError:
            continue
        except Exception as e:
            print(f"[GPS Parse Error]: {e}")
            continue

    # If no valid line is found after max_lines, raise an error or return fallb>
    raise TimeoutError("No valid GPS data received.")
    
def main():
    print("Starting GPS map viewer...")
    ser = serial.Serial(GPS_PORT, GPS_BAUDRATE, timeout=1)

    while True:
        try:
            print("Reading GPS data...")
            lat, lon, heading = get_gps_data(ser)
            print(f"Got GPS: {lat}, {lon} heading: {heading}")

            print("Generating map tile...")
            map_img = get_composite_tile(lat, lon, ZOOM)

            print("Drawing overlay...")
            display_img = draw_overlay(map_img, lat, lon, heading)

            print("Updating display...")
            display.display(display_img)

            time.sleep(3)
            
if __name__ == "__main__":
    main()

