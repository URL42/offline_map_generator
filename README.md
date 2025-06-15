# 🗺️ Raspberry Pi GPS Map Tracker with Offline Tiles

A Raspberry Pi-based GPS tracker that displays your current location and heading on an offline map using `.mbtiles`, rendered in real time on an ST7796 480x320 display. Built for field use with battery packs and real-time location updates.

## 📦 Features

- Real-time GPS location tracking using `/dev/ttyAMA0`
- Displays on 480x320 ST7796 TFT screen (SPI)
- Supports `.mbtiles` format (offline map tiles)
- Auto-centering with red dot marker and heading arrow
- On-screen compass and lat/lon coordinates
- Caching for improved tile load performance
- Designed for low-power operation (battery pack compatible)

---

## 🧰 Hardware Requirements

- Raspberry Pi Zero 2W or similar
- ST7796 480x320 TFT SPI display
- GPS Module (tested with 115200 baud rate on `/dev/ttyAMA0`)
- Battery pack (e.g., INIU 10,000mAh with USB-C → Micro USB cable)
- MicroSD with Raspbian OS
- Optional: enclosure for field use

---

## 🧰 Software Requirements

- Raspberry Pi OS (Lite or Full)
- Python 3
- Required Python libraries:
  ```bash
  sudo apt update && sudo apt install -y python3-pip sqlite3
  pip3 install pillow pyserial pynmea2
  ```
- mbtiles map file (use tools like [OfflineMapDownloader](https://github.com/0015/OfflineMapDownloader))

---

## 🔌 Wiring Overview

### GPS Module Wiring

| GPS Pin | Pi GPIO | Description       |
|---------|---------|-------------------|
| TX      | GPIO 15 | Pi RX (data in)   |
| RX      | GPIO 14 | Pi TX (data out)  |
| VCC     | 3.3V/5V | Power from Pi     |
| GND     | GND     | Ground reference  |
| Other   | —       | Leave wired per module spec (e.g. PPS, but unused) |

### ST7796 TFT Screen Wiring (SPI)

| Screen Pin | Pi GPIO               | Function                          |
|---------------|-----------------------|--------------------------------|
| VCC           | 5V (pin 2/4)          | Power                          |
| GND           | GND (pin 6)           | Ground                         |
| CS            | GPIO 8 (CE0)          | Chip Select for SPI            |
| DC            | GPIO 24               | Data/Command select            |
| RST           | GPIO 25               | Hardware reset                 |
| CLK (SCLK)    | SPI0 SCLK (GPIO 11)   | SPI Clock                      |
| MOSI          | SPI0 MOSI (GPIO 10)   | SPI Data Output                |
| MISO          | Not used              | (Screen doesn’t send data)     |
| LED Backlight | GPIO 18 (optional)    | Pin for backlight control: Connect through resistor or wire to +5V always on |

---

## 📂 Project Structure

- `GPS/`
  - `main.py` – Main tracker script with real-time GPS and map display
  - `st7796.py` – Custom driver for the ST7796 TFT display
  - `maps/`
    - `samplemap.mbtiles` – Offline tile map database (MBTiles format)
  - `test_map_display.py` – Standalone tile rendering test script
  - `README.md` – This documentation file

---

## 🚀 Setup Instructions

### 1. 📁 Map File

Download `.mbtiles` for your region using [OfflineMapDownloader](https://github.com/0015/OfflineMapDownloader) or other tools, and place it in the `/home/pi/GPS/maps/` directory:

```bash
scp ~/Downloads/samplemap.mbtiles pi@<raspberrypi_ip>:/home/pi/GPS/maps/
```
Replace <raspberrypi_ip> with the actual IP address of your Raspberry Pi. Do this from your main computer, not from the pi via ssh.

### 2. ⚙️ Run the Map Viewer

Once the map tiles are in place and the GPS module is connected:

```bash
cd ~/GPS
python3 main.py
```

You should see the following on the display:
- A centered red dot showing your current GPS position
- A blue arrow indicating your heading (currently static or zero unless compass integrated)
- Red text at the top left showing latitude and longitude
- A red compass label at the bottom right showing heading in degrees

## 3. 🧪 Testing Without GPS

If you want to verify that your `.mbtiles` file and screen rendering are working without needing the GPS module:

```bash
python3 test_map_display.py
```

This will render a test location at a predefined latitude/longitude and zoom level to verify that:
- Your .mbtiles file loads correctly
- The display is connected and rendering
- Map centering logic works as expected
- You can modify the lat/lon values in test_map_display.py to test different areas.

## 4. 🔧 Customization Options
Edit variables at the top of main.py to fine-tune the behavior for your setup:

Variable	Description
MBTILES_PATH	Path to your .mbtiles file
ZOOM	Zoom level (must match the zoom level in your downloaded tiles)
SCREEN_WIDTH	Width of your screen in pixels (default is 480)
SCREEN_HEIGHT	Height of your screen in pixels (default is 320)
GPS_PORT	Serial port for GPS module (default: /dev/ttyAMA0)
GPS_BAUDRATE	Baud rate for GPS serial communication (default: 115200)

To adjust the map detail level, change the ZOOM level and redownload tiles accordingly.

## 5. 🔋 Power Supply Suggestions
This project is optimized for portable use. Here’s what works well:
- Battery pack: INIU 10,000mAh USB-C power bank
- Cable: USB-C to Micro-USB (high-quality braided cable recommended)
- Runtime: ~4–6 hours depending on update rate and GPS activity
- Make sure the battery pack supports output while charging (pass-through) if you want to hot-swap.

## 6. 🔁 Auto-Start on Boot with systemd
To ensure your GPS map viewer launches automatically at boot, you can create a systemd service.
- Create a new service file:
  ```
  sudo nano /etc/systemd/system/gpsmap.service
  ```
- Paste the following contents:
  ```
  [Unit]
  Description=GPS Map Viewer
  After=network.target
  
  [Service]
  ExecStartPre=/bin/sleep 10
  ExecStart=/usr/bin/python3 /home/pi/GPS/main.py
  Restart=always
  User=pi
  WorkingDirectory=/home/pi/GPS
  StandardOutput=journal
  StandardError=journal
  
  [Install]
  WantedBy=multi-user.target
  ```

-- ExecStartPre=/bin/sleep 10 ensures the system initializes SPI and serial devices before your script runs.

-- Restart=always will keep the service alive if it crashes.

-- StandardOutput=journal logs output so you can inspect it with journalctl.

- Enable the service:
```
sudo systemctl daemon-reexec
sudo systemctl daemon-reload
sudo systemctl enable gpsmap.service
```

- Check the status:
```
sudo systemctl status gpsmap.service
```

- To view logs:
```
journalctl -u gpsmap.service
```

### 🛡️ License
MIT License
Feel free to copy, modify, and build on this project for personal use only, not for commercial use.

### 🙌 Acknowledgments
Built with 💻 Python, 🧭 GPS, and 🗺️ OpenStreetMap data.
Thanks to the open-source community, 0015 for his [offline map viewer idea](https://github.com/0015/Offline-Map-Viewer-for-E-Paper) and his [OfflineMapDownloader software](https://github.com/0015/OfflineMapDownloader) for tile generation tools.
