"""System statistics helper module."""
import socket


class SystemStats:
    """Helper class to gather system information efficiently."""
    
    @staticmethod
    def get_ip():
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
        return socket.gethostname()

    @staticmethod
    def get_cpu_temp():
        try:
            with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
                temp = int(f.read()) / 1000.0
            return f"{temp:.1f}C"
        except Exception:
            return "N/A"

    @staticmethod
    def check_internet():
        try:
            socket.create_connection(("1.1.1.1", 53), timeout=2)
            return "Online"
        except OSError:
            return "Offline"
