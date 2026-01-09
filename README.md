# 📟 LCD PiCommander
LCD PiCommander is a lightweight, highly configurable Python-based menu system for Raspberry Pi. It allows you to control your headless server (Docker, system services, power management) using a standard I2C Character LCD, a rotary encoder, and physical buttons.

Perfect for homelabs, media centers, or IoT gateways where you need quick physical access to system commands without a monitor or SSH.

## ✨ Features
+ 📂 Dynamic Menu: Define your menu structure in a simple config.yaml file.
+ 🐚 Shell Integration: Link menu items to any bash command or script (Restart Docker, Shutdown, etc.).
+ 📊 Idle Dashboard: Automatically cycles through system stats (IP, Hostname, CPU Temp, Internet Status) when not in use.
+ 🎡 Intuitive Navigation: Uses a rotary encoder for scrolling and buttons for Enter/Back/Home.

## 🛠️ Hardware Requirements
+ Raspberry Pi (Running Pi OS 64-bit / Debian Trixie)
+ LCD Display: 16x2 or 20x4 Character LCD with a PCF8574 I2C adapter.
+ Input: 1x Rotary Encoder, 2x Momentary Push Buttons.

## Wiring Diagram (Default Config)

|Component  |Pin (BCM)|Function           |
|-----------|---------|-------------------|
|LCD        |SDA/SCL  |I2C Communication  |
|Rotary A   |12       |Scroll Up/Down     |
|Rotary B   |6        |Scroll Up/Down     |
|Rotary SW  |13       |Enter / Select     |
|Button 1   |25       |Back / Exit        |
|Button 2   |11       |Home               |
|Button 3   |8        |Quck lauch command |

## 🚀 Installation
### 1. Enable I2C
Use `sudo raspi-config` to enable the I2C interface under Interface Options.

### 2. Install via pipx
The cleanest way to install on modern Pi OS is using `pipx`:

```
# Install pipx if you haven't already
sudo apt update && sudo apt install pipx
pipx ensurepath

# Install LCD PiCommander
pipx install git+[https://github.com/GameOver94/LCD-PiCommander.git](https://github.com/GameOver94/LCD-PiCommander.git)
```

## ⚙️ ConfigurationCreate a config.yaml to define your menu. Example:
```
menu:
  - label: "Docker"
    items:
      - label: "Restart All"
        action: "docker-compose restart"
  - label: "System"
    items:
      - label: "IP Address"
        action: "hostname -I"
        wait_for_key: true
```

Run the commander with your config:
```
pi-menu --config my_config.yaml
```
