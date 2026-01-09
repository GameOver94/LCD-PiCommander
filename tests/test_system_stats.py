"""Tests for SystemStats class."""
import sys
import os
import pytest
from unittest.mock import mock_open, patch, MagicMock
from importlib.util import spec_from_file_location, module_from_spec

# Import SystemStats module directly without going through __init__.py
spec = spec_from_file_location(
    "system_stats",
    os.path.join(os.path.dirname(__file__), "..", "src", "lcd_picommander", "system_stats.py")
)
system_stats = module_from_spec(spec)
spec.loader.exec_module(system_stats)
SystemStats = system_stats.SystemStats


class TestSystemStats:
    """Test SystemStats methods."""
    
    def test_get_hostname(self):
        """Test get_hostname returns a string."""
        result = SystemStats.get_hostname()
        assert isinstance(result, str)
        assert len(result) > 0
    
    def test_get_ip_success(self):
        """Test get_ip returns IP address on success."""
        with patch('socket.socket') as mock_socket:
            mock_instance = MagicMock()
            mock_instance.getsockname.return_value = ['192.168.1.100', 0]
            mock_socket.return_value = mock_instance
            
            result = SystemStats.get_ip()
            assert result == '192.168.1.100'
    
    def test_get_ip_failure(self):
        """Test get_ip returns 'No IP' on failure."""
        with patch('socket.socket', side_effect=Exception("Network error")):
            result = SystemStats.get_ip()
            assert result == "No IP"
    
    def test_get_cpu_temp_success(self):
        """Test get_cpu_temp reads temperature successfully."""
        mock_data = "45000\n"
        with patch('builtins.open', mock_open(read_data=mock_data)):
            result = SystemStats.get_cpu_temp()
            assert result == "45.0C"
    
    def test_get_cpu_temp_failure(self):
        """Test get_cpu_temp returns N/A on failure."""
        with patch('builtins.open', side_effect=FileNotFoundError()):
            result = SystemStats.get_cpu_temp()
            assert result == "N/A"
    
    def test_check_internet_online(self):
        """Test check_internet returns Online when connected."""
        with patch('socket.create_connection'):
            result = SystemStats.check_internet()
            assert result == "Online"
    
    def test_check_internet_offline(self):
        """Test check_internet returns Offline when not connected."""
        with patch('socket.create_connection', side_effect=OSError()):
            result = SystemStats.check_internet()
            assert result == "Offline"
    
    def test_get_cpu_usage(self):
        """Test get_cpu_usage returns percentage."""
        with patch('os.getloadavg', return_value=(0.5, 0.3, 0.2)):
            with patch('os.cpu_count', return_value=4):
                result = SystemStats.get_cpu_usage()
                assert result == "12.5%"
    
    def test_get_cpu_usage_capped(self):
        """Test get_cpu_usage caps at 100%."""
        with patch('os.getloadavg', return_value=(8.0, 4.0, 2.0)):
            with patch('os.cpu_count', return_value=4):
                result = SystemStats.get_cpu_usage()
                assert result == "100.0%"
    
    def test_get_cpu_load(self):
        """Test get_cpu_load returns load average."""
        with patch('os.getloadavg', return_value=(1.25, 0.75, 0.50)):
            result = SystemStats.get_cpu_load()
            assert result == "1.25"
    
    def test_get_cpu_load_failure(self):
        """Test get_cpu_load returns N/A on failure."""
        with patch('os.getloadavg', side_effect=OSError()):
            result = SystemStats.get_cpu_load()
            assert result == "N/A"
    
    def test_parse_memory_info_success(self):
        """Test _parse_memory_info parses /proc/meminfo correctly."""
        mock_data = """MemTotal:       16000000 kB
MemFree:         8000000 kB
MemAvailable:   12000000 kB
Buffers:          500000 kB
"""
        with patch('builtins.open', mock_open(read_data=mock_data)):
            total, available = SystemStats._parse_memory_info()
            assert total == 16000000
            assert available == 12000000
    
    def test_parse_memory_info_failure(self):
        """Test _parse_memory_info returns (0, 0) on failure."""
        with patch('builtins.open', side_effect=FileNotFoundError()):
            total, available = SystemStats._parse_memory_info()
            assert total == 0
            assert available == 0
    
    def test_get_memory_usage_success(self):
        """Test get_memory_usage calculates percentage correctly."""
        with patch.object(SystemStats, '_parse_memory_info', return_value=(16000000, 12000000)):
            result = SystemStats.get_memory_usage()
            # (16000000 - 12000000) / 16000000 * 100 = 25.0%
            assert result == "25.0%"
    
    def test_get_memory_usage_zero_total(self):
        """Test get_memory_usage returns N/A when total is 0."""
        with patch.object(SystemStats, '_parse_memory_info', return_value=(0, 0)):
            result = SystemStats.get_memory_usage()
            assert result == "N/A"
    
    def test_get_memory_info_success(self):
        """Test get_memory_info formats MB correctly."""
        with patch.object(SystemStats, '_parse_memory_info', return_value=(16000000, 12000000)):
            result = SystemStats.get_memory_info()
            # used = (16000000 - 12000000) / 1024 = 3906.25 MB
            # total = 16000000 / 1024 = 15625 MB
            assert result == "3906/15625MB"
    
    def test_get_disk_usage_success(self):
        """Test get_disk_usage calculates percentage correctly."""
        class MockStatVFS:
            f_blocks = 100000
            f_frsize = 4096
            f_bfree = 30000
        
        with patch('os.statvfs', return_value=MockStatVFS()):
            result = SystemStats.get_disk_usage()
            # total = 100000 * 4096 = 409600000
            # free = 30000 * 4096 = 122880000
            # used = 286720000
            # percent = 286720000 / 409600000 * 100 = 70.0%
            assert result == "70.0%"
    
    def test_get_disk_usage_failure(self):
        """Test get_disk_usage returns N/A on failure."""
        with patch('os.statvfs', side_effect=OSError()):
            result = SystemStats.get_disk_usage()
            assert result == "N/A"
    
    def test_get_disk_info_success(self):
        """Test get_disk_info formats GB correctly."""
        class MockStatVFS:
            f_blocks = 100000000
            f_frsize = 4096
            f_bfree = 30000000
        
        with patch('os.statvfs', return_value=MockStatVFS()):
            result = SystemStats.get_disk_info()
            # total = 100000000 * 4096 / (1024^3) ≈ 381.5 GB
            # free = 30000000 * 4096 / (1024^3) ≈ 114.4 GB
            # used ≈ 267.0 GB
            assert "GB" in result
            parts = result.replace("GB", "").split("/")
            assert len(parts) == 2
            assert float(parts[0]) > 0
            assert float(parts[1]) > 0
    
    def test_get_uptime_success(self):
        """Test get_uptime formats time correctly."""
        # Test with days
        with patch('builtins.open', mock_open(read_data="200000.00 150000.00\n")):
            result = SystemStats.get_uptime()
            assert "d" in result or "h" in result or "m" in result
        
        # Test with hours only
        with patch('builtins.open', mock_open(read_data="7200.00 3600.00\n")):
            result = SystemStats.get_uptime()
            assert result == "2h 0m"
        
        # Test with minutes only
        with patch('builtins.open', mock_open(read_data="300.00 150.00\n")):
            result = SystemStats.get_uptime()
            assert result == "5m"
    
    def test_get_uptime_failure(self):
        """Test get_uptime returns N/A on failure."""
        with patch('builtins.open', side_effect=FileNotFoundError()):
            result = SystemStats.get_uptime()
            assert result == "N/A"
    
    def test_get_os_info_success(self):
        """Test get_os_info parses OS release correctly."""
        mock_data = """NAME="Ubuntu"
VERSION="22.04.1 LTS (Jammy Jellyfish)"
ID=ubuntu
ID_LIKE=debian
PRETTY_NAME="Ubuntu 22.04.1 LTS"
VERSION_ID="22.04"
"""
        with patch('builtins.open', mock_open(read_data=mock_data)):
            result = SystemStats.get_os_info()
            assert result == "Ubuntu 22.04.1 LTS"
    
    def test_get_os_info_pi_os(self):
        """Test get_os_info shortens Raspberry Pi OS name."""
        mock_data = 'PRETTY_NAME="Raspberry Pi OS 11 (Bullseye)"\n'
        with patch('builtins.open', mock_open(read_data=mock_data)):
            result = SystemStats.get_os_info()
            assert result == "Pi OS 11 (Bullseye)"
    
    def test_get_os_info_failure(self):
        """Test get_os_info returns Linux on failure."""
        with patch('builtins.open', side_effect=FileNotFoundError()):
            result = SystemStats.get_os_info()
            assert result == "Linux"
    
    def test_get_kernel_success(self):
        """Test get_kernel parses kernel version correctly."""
        mock_data = "Linux version 5.15.0-1234-generic (buildd@lcy02-amd64-001) (gcc version 11.3.0)\n"
        with patch('builtins.open', mock_open(read_data=mock_data)):
            result = SystemStats.get_kernel()
            assert result == "5.15.0-1234-generic"
    
    def test_get_kernel_failure(self):
        """Test get_kernel returns N/A on failure."""
        with patch('builtins.open', side_effect=FileNotFoundError()):
            result = SystemStats.get_kernel()
            assert result == "N/A"
    
    def test_get_kernel_malformed(self):
        """Test get_kernel returns N/A on malformed data."""
        mock_data = "Not a valid kernel version line\n"
        with patch('builtins.open', mock_open(read_data=mock_data)):
            result = SystemStats.get_kernel()
            assert result == "N/A"
