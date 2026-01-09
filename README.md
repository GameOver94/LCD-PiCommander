# 📟 LCD PiCommander
LCD PiCommander is a lightweight, highly configurable Python-based menu system for Raspberry Pi. It allows you to control your headless server (Docker, system services, power management) using a standard I2C Character LCD, a rotary encoder, and physical buttons.

Perfect for homelabs, media centers, or IoT gateways where you need quick physical access to system commands without a monitor or SSH.

## ✨ Features
+ 📂 Dynamic Menu: Define your menu structure in a simple config.yaml file.
+ ⚡ Wildcard System Stats: Use `${stats.method_name}` syntax for easy access to common system statistics (CPU, memory, disk, uptime, etc.).
+ 🐚 Shell Integration: Link menu items to any bash command or script for advanced stats and custom actions.
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
|Button 3   |8        |Quick Launch       |

## 🚀 Installation
### 1. Enable I2C
Use `sudo raspi-config` to enable the I2C interface under Interface Options.

### 2. Install Build Dependencies
Some libraries (like `lgpio`) need to be compiled from source. Install these build tools first:

```bash
sudo apt update
sudo apt install swig python3-dev liblgpio-dev
```

### 3. Install via pipx
The cleanest way to install on modern Pi OS is using `pipx`:

```
# Install pipx if you haven't already
sudo apt update && sudo apt install pipx
pipx ensurepath

# Install LCD PiCommander
pipx install githttps://github.com/GameOver94/LCD-PiCommander.git
```

## ⚙️ Configuration

Create a `config.yaml` to define your menu. You can use two types of actions:

### 1. Wildcard System Stats (Recommended for Common Stats)
Use `${stats.method_name}` syntax to call built-in system statistics methods. This is faster and easier to configure than shell commands:

```yaml
menu:
  - label: "System Info"
    items:
      - label: "IP Address"
        action: "${stats.get_ip}"
        wait_for_key: true
      - label: "CPU Temp"
        action: "${stats.get_cpu_temp}"
        wait_for_key: true
      - label: "Memory"
        action: "${stats.get_memory}"
        wait_for_key: true
      - label: "Disk Usage"
        action: "${stats.get_disk_percent}"
        wait_for_key: true
```

**Available Wildcard Methods:**
- `${stats.get_ip}` - Primary IP address
- `${stats.get_hostname}` - Device hostname
- `${stats.get_cpu_temp}` - CPU temperature (Raspberry Pi)
- `${stats.get_cpu_usage}` - CPU usage percentage
- `${stats.get_memory}` - Memory usage (e.g., "512M/2048M")
- `${stats.get_memory_percent}` - Memory usage percentage
- `${stats.get_disk_usage}` - Disk usage (e.g., "12.5G/32.0G")
- `${stats.get_disk_percent}` - Disk usage percentage
- `${stats.get_uptime}` - System uptime
- `${stats.get_kernel}` - Kernel version
- `${stats.get_os}` - OS information
- `${stats.check_internet}` - Internet connectivity status

### 2. Custom Shell Commands (For Advanced Stats)
For more advanced or custom statistics, you can still use any bash command or script:

```yaml
menu:
  - label: "Advanced Stats"
    items:
      - label: "Load Average"
        action: "uptime | awk -F'load average:' '{print $2}'"
        wait_for_key: true
      - label: "Top Process"
        action: "ps aux --sort=-%cpu | head -2 | tail -1 | awk '{print $11}'"
        wait_for_key: true
  - label: "Docker"
    items:
      - label: "Restart All"
        action: "docker-compose restart"
```

### Quick Launch Button
The `quick_launch` section configures Button 3 to execute a specific command regardless of which menu item is currently selected. This is useful for frequently accessed commands.

```yaml
quick_launch:
  command: "docker ps --format '{{.Names}}'"
  wait_for_key: true
```

Run the commander with your config:
```bash
pi-commander --config my_config.yaml
```
