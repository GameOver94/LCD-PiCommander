"""Tests for wildcard functionality in MenuController."""
import sys
import os
import pytest
from unittest.mock import MagicMock, patch, mock_open
from importlib.util import spec_from_file_location, module_from_spec

# Import menu module directly without going through __init__.py
spec = spec_from_file_location(
    "menu",
    os.path.join(os.path.dirname(__file__), "..", "src", "lcd_picommander", "menu.py")
)
menu_module = module_from_spec(spec)
spec.loader.exec_module(menu_module)
MenuNode = menu_module.MenuNode

# Import SystemStats for tests
spec2 = spec_from_file_location(
    "system_stats",
    os.path.join(os.path.dirname(__file__), "..", "src", "lcd_picommander", "system_stats.py")
)
system_stats_module = module_from_spec(spec2)
spec2.loader.exec_module(system_stats_module)
SystemStats = system_stats_module.SystemStats


class MockMenuController:
    """Mock MenuController with wildcard methods for testing."""
    
    def _is_stat_wildcard(self, action):
        """Check if action is a stat wildcard."""
        return isinstance(action, str) and action.startswith('stat:')
    
    def _execute_stat_wildcard(self, action):
        """Execute a SystemStats method based on wildcard syntax."""
        try:
            # Extract method name from 'stat:method_name'
            parts = action.split(':', 1)
            if len(parts) != 2 or not parts[1]:
                return "Invalid format"
            
            method_name = parts[1]
            
            # Security: Only allow public getter methods
            if not (method_name.startswith('get_') or method_name.startswith('check_')):
                return f"Not allowed: {method_name}"
            
            # Check if method exists in SystemStats
            if hasattr(SystemStats, method_name):
                method = getattr(SystemStats, method_name)
                if callable(method):
                    return method()
                else:
                    return "Not callable"
            else:
                return f"Unknown: {method_name}"
        except Exception as e:
            return f"Err: {str(e)[:15]}"


class TestWildcardDetection:
    """Test wildcard detection logic."""
    
    def test_is_stat_wildcard_valid(self):
        """Test valid wildcard format is detected."""
        controller = MockMenuController()
        assert controller._is_stat_wildcard("stat:get_ip") is True
        assert controller._is_stat_wildcard("stat:get_hostname") is True
        assert controller._is_stat_wildcard("stat:check_internet") is True
    
    def test_is_stat_wildcard_invalid(self):
        """Test invalid formats are not detected as wildcards."""
        controller = MockMenuController()
        assert controller._is_stat_wildcard("hostname -I") is False
        assert controller._is_stat_wildcard("vcgencmd measure_temp") is False
        assert controller._is_stat_wildcard("stats:get_ip") is False
        assert controller._is_stat_wildcard("") is False
    
    def test_is_stat_wildcard_none(self):
        """Test None is not detected as wildcard."""
        controller = MockMenuController()
        assert controller._is_stat_wildcard(None) is False
    
    def test_is_stat_wildcard_number(self):
        """Test number is not detected as wildcard."""
        controller = MockMenuController()
        assert controller._is_stat_wildcard(123) is False


class TestWildcardExecution:
    """Test wildcard execution logic."""
    
    def test_execute_valid_wildcard(self, monkeypatch):
        """Test executing a valid wildcard."""
        controller = MockMenuController()
        
        monkeypatch.setattr(SystemStats, 'get_hostname', lambda: "test-pi")
        result = controller._execute_stat_wildcard("stat:get_hostname")
        assert result == "test-pi"
    
    def test_execute_empty_method_name(self):
        """Test executing wildcard with empty method name."""
        controller = MockMenuController()
        result = controller._execute_stat_wildcard("stat:")
        assert result == "Invalid format"
    
    def test_execute_unknown_method(self):
        """Test executing wildcard with unknown method."""
        controller = MockMenuController()
        result = controller._execute_stat_wildcard("stat:get_unknown_stat")
        assert "Unknown" in result
    
    def test_execute_private_method_blocked(self):
        """Test private methods are blocked."""
        controller = MockMenuController()
        result = controller._execute_stat_wildcard("stat:_parse_memory_info")
        assert "Not allowed" in result
    
    def test_execute_magic_method_blocked(self):
        """Test magic methods are blocked."""
        controller = MockMenuController()
        result = controller._execute_stat_wildcard("stat:__init__")
        assert "Not allowed" in result
    
    def test_execute_check_method_allowed(self, monkeypatch):
        """Test check_ prefix methods are allowed."""
        controller = MockMenuController()
        
        monkeypatch.setattr(SystemStats, 'check_internet', lambda: "Online")
        result = controller._execute_stat_wildcard("stat:check_internet")
        assert result == "Online"
    
    def test_execute_get_method_allowed(self, monkeypatch):
        """Test get_ prefix methods are allowed."""
        controller = MockMenuController()
        
        monkeypatch.setattr(SystemStats, 'get_ip', lambda: "192.168.1.100")
        result = controller._execute_stat_wildcard("stat:get_ip")
        assert result == "192.168.1.100"
    
    def test_execute_arbitrary_method_blocked(self):
        """Test arbitrary method names are blocked."""
        controller = MockMenuController()
        result = controller._execute_stat_wildcard("stat:some_random_method")
        assert "Not allowed" in result


class TestWildcardIntegration:
    """Integration tests for wildcard functionality."""
    
    def test_wildcard_with_all_stat_methods(self, monkeypatch):
        """Test all public stat methods can be called via wildcard."""
        controller = MockMenuController()
        
        methods_to_test = [
            ('stat:get_ip', '192.168.1.100'),
            ('stat:get_hostname', 'test-host'),
            ('stat:get_cpu_temp', '45.0C'),
            ('stat:get_cpu_usage', '25.5%'),
            ('stat:get_cpu_load', '1.25'),
            ('stat:get_memory_usage', '50.0%'),
            ('stat:get_memory_info', '4000/8000MB'),
            ('stat:get_disk_usage', '75.0%'),
            ('stat:get_disk_info', '50.0/100.0GB'),
            ('stat:get_uptime', '2h 30m'),
            ('stat:get_os_info', 'Pi OS 11'),
            ('stat:get_kernel', '5.15.0'),
            ('stat:check_internet', 'Online'),
        ]
        
        for wildcard, expected_value in methods_to_test:
            method_name = wildcard.split(':', 1)[1]
            monkeypatch.setattr(SystemStats, method_name, lambda v=expected_value: v)
            result = controller._execute_stat_wildcard(wildcard)
            assert result == expected_value, f"Failed for {wildcard}"


class TestMenuNode:
    """Test MenuNode class."""
    
    def test_menu_node_creation(self):
        """Test creating a MenuNode."""
        node = MenuNode(label="Test", action="stat:get_ip", wait_for_key=True)
        assert node.label == "Test"
        assert node.action == "stat:get_ip"
        assert node.wait_for_key is True
        assert node.children == []
    
    def test_menu_node_is_submenu_false(self):
        """Test is_submenu returns False for action nodes."""
        node = MenuNode(label="Test", action="stat:get_ip")
        assert node.is_submenu is False
    
    def test_menu_node_is_submenu_true(self):
        """Test is_submenu returns True for nodes with children."""
        child = MenuNode(label="Child", action="stat:get_ip")
        parent = MenuNode(label="Parent", children=[child])
        assert parent.is_submenu is True
    
    def test_menu_node_defaults(self):
        """Test MenuNode default values."""
        node = MenuNode(label="Test")
        assert node.action is None
        assert node.children == []
        assert node.wait_for_key is False


class TestSecurityControls:
    """Test security controls for wildcard execution."""
    
    def test_no_access_to_private_attributes(self):
        """Test private attributes cannot be accessed."""
        controller = MockMenuController()
        
        private_methods = [
            "stat:_parse_memory_info",
            "stat:__class__",
            "stat:__dict__",
            "stat:__module__",
        ]
        
        for method in private_methods:
            result = controller._execute_stat_wildcard(method)
            assert "Not allowed" in result, f"Private method {method} should be blocked"
    
    def test_only_whitelisted_prefixes_allowed(self):
        """Test only get_ and check_ prefixes are allowed."""
        controller = MockMenuController()
        
        # These should be blocked even if they exist
        blocked_methods = [
            "stat:calculate_something",
            "stat:run_command",
            "stat:execute_action",
            "stat:do_something",
        ]
        
        for method in blocked_methods:
            result = controller._execute_stat_wildcard(method)
            assert "Not allowed" in result, f"Method {method} should be blocked"
    
    def test_malformed_wildcards_handled(self):
        """Test malformed wildcards are handled gracefully."""
        controller = MockMenuController()
        
        malformed = [
            "stat:",
            "stat",
            ":get_ip",
            "stat::get_ip",
        ]
        
        for wildcard in malformed:
            result = controller._execute_stat_wildcard(wildcard)
            # Should return error, not crash
            assert isinstance(result, str)
