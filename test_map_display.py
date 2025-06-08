import sqlite3
import math
import io
from PIL import Image
from st7796 import ST7796

# Configuration
MBTILES_PATH = "maps/oakpark.mbtiles"
LAT = 38.55107
LON = -121.46074
ZOOM = 15
TILE_SIZE = 256
SCREEN_WIDTH = 480
SCREEN_HEIGHT = 320

# Initialize display
display = ST7796(
    width=SCREEN_WIDTH,
    height=SCREEN_HEIGHT,
    rotation=270,
    port=0,
    cs=0,
    dc=24,
    rst=25
)

def deg2num(lat, lon, zoom):
    """Convert latitude and longitude to XYZ tile numbers."""
    lat_rad = math.radians(lat)
    n = 2.0 ** zoom
    xtile = int((lon + 180.0) / 360.0 * n)
    ytile = int((1.0 - math.log(math.tan(lat_rad) + (1 / math.cos(lat_rad))) / math.pi) / 2.0 * n)
    return xtile, ytile

def get_tile(z, x, y):
    """Fetch a tile image from the MBTiles database."""
    conn = sqlite3.connect(MBTILES_PATH)
    cursor = conn.cursor()
    y_tms = (2 ** z - 1) - y  # TMS flip
    cursor.execute("SELECT tile_data FROM tiles WHERE zoom_level=? AND tile_column=? AND tile_row=?", (z, x, y_tms))
    row = cursor.fetchone()
    conn.close()
    if row:
        return Image.open(io.BytesIO(row[0])).convert("RGB")
    else:
        return Image.new("RGB", (TILE_SIZE, TILE_SIZE), "gray")

def get_composite_tile(center_lat, center_lon, zoom):
    """Build a composite image of tiles centered around the given location."""
    center_x, center_y = deg2num(center_lat, center_lon, zoom)
    composite = Image.new("RGB", (TILE_SIZE * 3, TILE_SIZE * 2), "black")
    
    for dx in range(-1, 2):
        for dy in range(-1, 1):
            tx = center_x + dx
            ty = center_y + dy
            tile = get_tile(zoom, tx, ty)
            px = (dx + 1) * TILE_SIZE
            py = (dy + 1) * TILE_SIZE
            composite.paste(tile, (px, py))
    
    crop_x = (composite.width - SCREEN_WIDTH) // 2
    crop_y = (composite.height - SCREEN_HEIGHT) // 2
    cropped = composite.crop((crop_x, crop_y, crop_x + SCREEN_WIDTH, crop_y + SCREEN_HEIGHT))
    return cropped

def main():
    print("Rendering tile map preview...")
    image = get_composite_tile(LAT, LON, ZOOM)
    display.display(image)

if __name__ == "__main__":
    main()
