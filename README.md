# 📟 LCD PiCommander
LCD PiCommander is a lightweight, highly configurable Python-based menu system for Raspberry Pi. It allows you to control your headless server (Docker, system services, power management) using a standard I2C Character LCD, a rotary encoder, and physical buttons.

Perfect for homelabs, media centers, or IoT gateways where you need quick physical access to system commands without a monitor or SSH.

## ✨ Features
+ 📂 Dynamic Menu: Define your menu structure in a simple config.yaml file.
+ 🐚 Shell Integration: Link menu items to any bash command or script (Restart Docker, Shutdown, etc.).
+ 📊 Configurable Idle Dashboard: Automatically cycles through customizable system stats when not in use.
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
pipx install git+https://github.com/GameOver94/LCD-PiCommander.git
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

### Dashboard Configuration
The `dashboard` section allows you to customize what stats are displayed when the system is idle. You can define multiple pages that will cycle automatically.

```yaml
dashboard:
  pages:
    - - label: "IP:   "
        stat: "stat:get_ip"
      - label: "Host: "
        stat: "stat:get_hostname"
    - - label: "Temp: "
        stat: "stat:get_cpu_temp"
      - label: "Net:  "
        stat: "stat:check_internet"
```

Each page can display up to 2 stats on a 16x2 display or 4 stats on a 20x4 display. The dashboard will automatically cycle through all configured pages based on the `dashboard_cycle_time` setting (default: 5 seconds).

If no dashboard configuration is provided, the system uses a default dashboard showing IP/Hostname and CPU Temp/Internet status.

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

## 🔄 Run as a Service (Auto-Start)
 To have LCD PiCommander start automatically on boot, set it up as a systemd service.

 1. **Create the service file:**
   ```bash
   sudo nano /etc/systemd/system/lcd-picommander.service
    ```

 2. **Paste the following configuration** (Adjust usage of `/home/pi/` if your user is different):
    ```ini
    [Unit]
    Description=LCD PiCommander Service
    After=network.target

    [Service]
    Type=simple
    # Replace 'pi' with your username
    User=pi
    WorkingDirectory=/home/pi
    # Ensure this path matches where pipx installed the binary
    ExecStart=/home/pi/.local/bin/pi-commander --config /home/pi/config.yaml
    Restart=always
    RestartSec=5
    Environment=PYTHONUNBUFFERED=1

    [Install]
    WantedBy=multi-user.target
    ```

 3. **Enable and Start the Service:**
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable lcd-picommander.service
   sudo systemctl start lcd-picommander.service
    ```

 4. **Check Status:**
   ```bash
   systemctl status lcd-picommander.service
    ```

## 🧪 Testing

The project includes a comprehensive pytest test suite covering all system stats and wildcard functionality.

### Run Tests

```bash
# Install test dependencies
pip install -e ".[test]"

# Run all tests
pytest

# Run with verbose output
pytest -v

# Run with coverage
pytest --cov=lcd_picommander --cov-report=html
```

See `tests/README.md` for more details on the test suite.

## 📝 Development

The test suite is designed to work without hardware dependencies, so you can develop and test on any platform without requiring a Raspberry Pi or hardware components.
