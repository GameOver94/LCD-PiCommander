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

Create a config.yaml to define your menu. The menu system supports two types of actions:

### 1. System Stats Wildcards (Recommended for Common Stats)
Use the `stat:method_name` syntax to call built-in SystemStats methods:

```yaml
menu:
  - label: "System Info"
    items:
      - label: "IP Address"
        action: "stat:get_ip"
        wait_for_key: true
      - label: "CPU Temp"
        action: "stat:get_cpu_temp"
        wait_for_key: true
      - label: "Memory Usage"
        action: "stat:get_memory_usage"
        wait_for_key: true
      - label: "Disk Usage"
        action: "stat:get_disk_usage"
        wait_for_key: true
```

#### Available System Stats Methods:
- `stat:get_ip` - Local IP address
- `stat:get_hostname` - System hostname
- `stat:get_cpu_temp` - CPU temperature
- `stat:get_cpu_usage` - CPU usage % (based on load average)
- `stat:get_cpu_load` - CPU load average (1 min)
- `stat:get_memory_usage` - Memory usage %
- `stat:get_memory_info` - Memory usage in MB (used/total)
- `stat:get_disk_usage` - Root filesystem usage %
- `stat:get_disk_info` - Disk usage in GB (used/total)
- `stat:get_uptime` - System uptime
- `stat:get_os_info` - OS name and version
- `stat:get_kernel` - Kernel version
- `stat:check_internet` - Internet connectivity status

### 2. Shell Commands (For Advanced/Custom Stats)
For advanced stats or custom commands, use regular shell commands:

```yaml
menu:
  - label: "Docker"
    items:
      - label: "List Containers"
        action: "docker ps --format '{{.Names}}'"
        wait_for_key: true
  - label: "Advanced"
    items:
      - label: "GPU Temp"
        action: "vcgencmd measure_temp"
        wait_for_key: true
```

### Quick Launch Configuration
The `quick_launch` section configures Button 3 to execute a specific command regardless of which menu item is currently selected:

```yaml
quick_launch:
  command: "docker ps --format '{{.Names}}'"
  wait_for_key: true
```

### Full Example

See `config.yaml` in the repository for a complete example showing both stat wildcards and shell commands.

Run the commander with your config:
```bash
pi-commander --config my_config.yaml
```
