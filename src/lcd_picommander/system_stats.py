"""System statistics helper module."""
import socket
import os
import subprocess


class SystemStats:
    """Helper class to gather system information efficiently."""
    
    @staticmethod
    def get_ip():
        """Get the local IP address."""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.settimeout(0)
            s.connect(('1.1.1.1', 1))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "No IP"

    @staticmethod
    def get_hostname():
        """Get the system hostname."""
        return socket.gethostname()

    @staticmethod
    def get_cpu_temp():
        """Get CPU temperature in Celsius."""
        try:
            with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
                temp = int(f.read()) / 1000.0
            return f"{temp:.1f}C"
        except Exception:
            return "N/A"

    @staticmethod
    def check_internet():
        """Check internet connectivity."""
        try:
            socket.create_connection(("1.1.1.1", 53), timeout=2)
            return "Online"
        except OSError:
            return "Offline"
    
    @staticmethod
    def get_cpu_usage():
        """Get current CPU usage percentage."""
        try:
            # Use top to get CPU usage (1 iteration, batch mode)
            result = subprocess.run(
                ["top", "-bn1"], 
                capture_output=True, 
                text=True, 
                timeout=2
            )
            # Parse the %Cpu(s) line
            for line in result.stdout.split('\n'):
                if '%Cpu(s)' in line or 'CPU:' in line:
                    # Extract idle percentage and calculate usage
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if 'id' in part or 'idle' in part:
                            try:
                                idle = float(parts[i-1].replace(',', '.'))
                                usage = 100.0 - idle
                                return f"{usage:.1f}%"
                            except (ValueError, IndexError):
                                pass
            return "N/A"
        except Exception:
            return "N/A"
    
    @staticmethod
    def get_cpu_load():
        """Get CPU load average (1 min)."""
        try:
            load1, _, _ = os.getloadavg()
            return f"{load1:.2f}"
        except Exception:
            return "N/A"
    
    @staticmethod
    def get_memory_usage():
        """Get memory usage percentage."""
        try:
            with open("/proc/meminfo", "r") as f:
                lines = f.readlines()
            
            mem_info = {}
            for line in lines[:3]:  # First 3 lines have what we need
                parts = line.split()
                mem_info[parts[0].rstrip(':')] = int(parts[1])
            
            total = mem_info.get('MemTotal', 0)
            available = mem_info.get('MemAvailable', 0)
            
            if total > 0:
                used_percent = ((total - available) / total) * 100
                return f"{used_percent:.1f}%"
            return "N/A"
        except Exception:
            return "N/A"
    
    @staticmethod
    def get_memory_info():
        """Get memory usage in MB format (used/total)."""
        try:
            with open("/proc/meminfo", "r") as f:
                lines = f.readlines()
            
            mem_info = {}
            for line in lines[:3]:
                parts = line.split()
                mem_info[parts[0].rstrip(':')] = int(parts[1])
            
            total = mem_info.get('MemTotal', 0) / 1024  # Convert to MB
            available = mem_info.get('MemAvailable', 0) / 1024
            used = total - available
            
            return f"{used:.0f}/{total:.0f}MB"
        except Exception:
            return "N/A"
    
    @staticmethod
    def get_disk_usage():
        """Get root filesystem usage percentage."""
        try:
            stat = os.statvfs('/')
            total = stat.f_blocks * stat.f_frsize
            free = stat.f_bfree * stat.f_frsize
            used = total - free
            percent = (used / total) * 100
            return f"{percent:.1f}%"
        except Exception:
            return "N/A"
    
    @staticmethod
    def get_disk_info():
        """Get root filesystem usage in GB format (used/total)."""
        try:
            stat = os.statvfs('/')
            total = (stat.f_blocks * stat.f_frsize) / (1024**3)  # Convert to GB
            free = (stat.f_bfree * stat.f_frsize) / (1024**3)
            used = total - free
            return f"{used:.1f}/{total:.1f}GB"
        except Exception:
            return "N/A"
    
    @staticmethod
    def get_uptime():
        """Get system uptime."""
        try:
            with open("/proc/uptime", "r") as f:
                uptime_seconds = float(f.read().split()[0])
            
            days = int(uptime_seconds // 86400)
            hours = int((uptime_seconds % 86400) // 3600)
            minutes = int((uptime_seconds % 3600) // 60)
            
            if days > 0:
                return f"{days}d {hours}h {minutes}m"
            elif hours > 0:
                return f"{hours}h {minutes}m"
            else:
                return f"{minutes}m"
        except Exception:
            return "N/A"
    
    @staticmethod
    def get_os_info():
        """Get OS name and version."""
        try:
            with open("/etc/os-release", "r") as f:
                lines = f.readlines()
            
            for line in lines:
                if line.startswith("PRETTY_NAME="):
                    # Extract the value, remove quotes
                    os_name = line.split('=', 1)[1].strip().strip('"')
                    # Shorten common long names
                    os_name = os_name.replace("Raspbian GNU/Linux", "Raspbian")
                    os_name = os_name.replace("Raspberry Pi OS", "Pi OS")
                    return os_name
            return "Linux"
        except Exception:
            return "Linux"
    
    @staticmethod
    def get_kernel():
        """Get kernel version."""
        try:
            result = subprocess.run(
                ["uname", "-r"], 
                capture_output=True, 
                text=True, 
                timeout=1
            )
            return result.stdout.strip()
        except Exception:
            return "N/A"
