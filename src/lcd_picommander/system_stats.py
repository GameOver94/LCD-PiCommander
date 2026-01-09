"""System statistics helper module."""
import socket
import os
import platform


class SystemStats:
    """Helper class to gather system information efficiently."""
    
    @staticmethod
    def get_ip():
        """Get the primary IP address of the device."""
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
        """Get the hostname of the device."""
        return socket.gethostname()

    @staticmethod
    def get_cpu_temp():
        """Get CPU temperature (Raspberry Pi specific)."""
        try:
            with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
                temp = int(f.read()) / 1000.0
            return f"{temp:.1f}C"
        except Exception:
            return "N/A"

    @staticmethod
    def check_internet():
        """Check if internet connection is available."""
        try:
            socket.create_connection(("1.1.1.1", 53), timeout=2)
            return "Online"
        except OSError:
            return "Offline"

    @staticmethod
    def get_cpu_usage():
        """Get current CPU usage percentage."""
        try:
            with open("/proc/stat", "r") as f:
                line = f.readline()
                fields = line.split()
                idle = int(fields[4])
                total = sum(int(x) for x in fields[1:])
                
            # Store previous values for next calculation
            if not hasattr(SystemStats.get_cpu_usage, 'prev_idle'):
                SystemStats.get_cpu_usage.prev_idle = idle
                SystemStats.get_cpu_usage.prev_total = total
                return "0%"
            
            idle_delta = idle - SystemStats.get_cpu_usage.prev_idle
            total_delta = total - SystemStats.get_cpu_usage.prev_total
            
            SystemStats.get_cpu_usage.prev_idle = idle
            SystemStats.get_cpu_usage.prev_total = total
            
            if total_delta == 0:
                return "0%"
            
            usage = 100.0 * (1.0 - idle_delta / total_delta)
            return f"{usage:.1f}%"
        except Exception:
            return "N/A"

    @staticmethod
    def get_memory():
        """Get memory usage information."""
        try:
            with open("/proc/meminfo", "r") as f:
                lines = f.readlines()
            
            mem_total = 0
            mem_available = 0
            
            for line in lines:
                if line.startswith("MemTotal:"):
                    mem_total = int(line.split()[1])
                elif line.startswith("MemAvailable:"):
                    mem_available = int(line.split()[1])
            
            mem_used = mem_total - mem_available
            mem_used_mb = mem_used // 1024
            mem_total_mb = mem_total // 1024
            
            return f"{mem_used_mb}M/{mem_total_mb}M"
        except Exception:
            return "N/A"

    @staticmethod
    def get_memory_percent():
        """Get memory usage as a percentage."""
        try:
            with open("/proc/meminfo", "r") as f:
                lines = f.readlines()
            
            mem_total = 0
            mem_available = 0
            
            for line in lines:
                if line.startswith("MemTotal:"):
                    mem_total = int(line.split()[1])
                elif line.startswith("MemAvailable:"):
                    mem_available = int(line.split()[1])
            
            mem_used = mem_total - mem_available
            percent = (mem_used / mem_total) * 100
            
            return f"{percent:.1f}%"
        except Exception:
            return "N/A"

    @staticmethod
    def get_disk_usage():
        """Get disk usage for root partition."""
        try:
            stat = os.statvfs('/')
            total = stat.f_blocks * stat.f_frsize
            free = stat.f_bfree * stat.f_frsize
            used = total - free
            
            total_gb = total / (1024**3)
            used_gb = used / (1024**3)
            
            return f"{used_gb:.1f}G/{total_gb:.1f}G"
        except Exception:
            return "N/A"

    @staticmethod
    def get_disk_percent():
        """Get disk usage as a percentage."""
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
    def get_uptime():
        """Get system uptime."""
        try:
            with open("/proc/uptime", "r") as f:
                uptime_seconds = float(f.read().split()[0])
            
            days = int(uptime_seconds // 86400)
            hours = int((uptime_seconds % 86400) // 3600)
            minutes = int((uptime_seconds % 3600) // 60)
            
            if days > 0:
                return f"{days}d {hours}h"
            elif hours > 0:
                return f"{hours}h {minutes}m"
            else:
                return f"{minutes}m"
        except Exception:
            return "N/A"

    @staticmethod
    def get_kernel():
        """Get kernel version."""
        try:
            return platform.release()
        except Exception:
            return "N/A"

    @staticmethod
    def get_os():
        """Get OS information."""
        try:
            # Try to read from /etc/os-release
            if os.path.exists("/etc/os-release"):
                with open("/etc/os-release", "r") as f:
                    for line in f:
                        if line.startswith("PRETTY_NAME="):
                            name = line.split("=", 1)[1].strip().strip('"')
                            # Shorten for LCD display
                            name = name.replace("Raspbian", "RPi")
                            name = name.replace("Raspberry Pi OS", "RPi OS")
                            return name
            return platform.system()
        except Exception:
            return "N/A"
