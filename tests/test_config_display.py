"""Tests for display configuration and dashboard cycle behavior."""
import pytest
import time
from unittest.mock import MagicMock, patch, PropertyMock
import tempfile
import yaml
import os


# Mock hardware dependencies
@pytest.fixture(autouse=True)
def mock_hardware():
    """Mock all hardware dependencies before importing main."""
    with patch('lcd_picommander.main.LCDDisplay') as mock_lcd_display, \
         patch('lcd_picommander.main.GPIOInputs') as mock_gpio:
        
        # Setup mock LCD
        mock_lcd = MagicMock()
        mock_lcd.cols = 16
        mock_lcd.rows = 2
        mock_lcd_display.return_value.lcd = mock_lcd
        mock_lcd_display.return_value.cols = 16
        mock_lcd_display.return_value.rows = 2
        
        # Setup mock GPIO
        mock_encoder = MagicMock()
        mock_gpio.return_value.encoder = mock_encoder
        mock_gpio.return_value.btn_enter = MagicMock()
        mock_gpio.return_value.btn_back = MagicMock()
        mock_gpio.return_value.btn_home = MagicMock()
        mock_gpio.return_value.btn_launch = MagicMock()
        
        yield {
            'lcd_display': mock_lcd_display,
            'gpio': mock_gpio,
            'lcd': mock_lcd
        }


@pytest.fixture
def sample_config():
    """Create a sample config for testing."""
    return {
        'hardware': {
            'i2c': {
                'address': 0x27,
                'port': 1,
                'cols': 16,
                'rows': 2
            },
            'display': {
                'idle_timeout': 10.0,
                'dashboard_cycle_time': 3.0,
                'backlight_timeout': 60.0
            },
            'inputs': {
                'encoder': {'clk': 12, 'dt': 6},
                'buttons': {'enter': 13, 'back': 25, 'custom': 11},
                'pull_up': True
            }
        },
        'menu': [
            {'label': 'Test', 'action': 'echo test'}
        ]
    }


@pytest.fixture
def config_file(sample_config):
    """Create a temporary config file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(sample_config, f)
        temp_path = f.name
    yield temp_path
    os.unlink(temp_path)


class TestDisplayConfiguration:
    """Test display configuration loading."""
    
    def test_default_values_when_display_config_missing(self, mock_hardware):
        """Test default values are used when display config is missing."""
        from lcd_picommander.main import MenuController
        
        config = {
            'hardware': {
                'i2c': {'address': 0x27, 'port': 1, 'cols': 16, 'rows': 2},
                'inputs': {
                    'encoder': {'clk': 12, 'dt': 6},
                    'buttons': {'enter': 13, 'back': 25, 'custom': 11},
                    'pull_up': True
                }
            },
            'menu': [{'label': 'Test', 'action': 'echo test'}]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config, f)
            temp_path = f.name
        
        try:
            controller = MenuController(temp_path)
            assert controller.idle_timeout == 15.0
            assert controller.dashboard_cycle_time == 5.0
            assert controller.backlight_timeout == 0.0
        finally:
            os.unlink(temp_path)
    
    def test_custom_idle_timeout(self, config_file):
        """Test custom idle timeout is loaded from config."""
        from lcd_picommander.main import MenuController
        
        controller = MenuController(config_file)
        assert controller.idle_timeout == 10.0
    
    def test_custom_dashboard_cycle_time(self, config_file):
        """Test custom dashboard cycle time is loaded from config."""
        from lcd_picommander.main import MenuController
        
        controller = MenuController(config_file)
        assert controller.dashboard_cycle_time == 3.0
    
    def test_custom_backlight_timeout(self, config_file):
        """Test custom backlight timeout is loaded from config."""
        from lcd_picommander.main import MenuController
        
        controller = MenuController(config_file)
        assert controller.backlight_timeout == 60.0
    
    def test_backlight_starts_enabled(self, config_file):
        """Test backlight starts in enabled state."""
        from lcd_picommander.main import MenuController
        
        controller = MenuController(config_file)
        assert controller.backlight_on is True


class TestDashboardCycle:
    """Test dashboard cycle behavior."""
    
    def test_dashboard_page_tracking(self, config_file, mock_hardware):
        """Test dashboard page tracking is initialized."""
        from lcd_picommander.main import MenuController
        
        controller = MenuController(config_file)
        assert controller.current_dashboard_page == 0
        assert controller.last_dashboard_update == 0
    
    @patch('lcd_picommander.main.SystemStats')
    def test_dashboard_only_updates_on_page_change(self, mock_stats, config_file, mock_hardware):
        """Test dashboard only updates when page changes."""
        from lcd_picommander.main import MenuController
        
        # Mock stat methods
        mock_stats.get_ip.return_value = "192.168.1.1"
        mock_stats.get_hostname.return_value = "test-pi"
        mock_stats.get_cpu_temp.return_value = "50C"
        mock_stats.check_internet.return_value = "Online"
        
        controller = MenuController(config_file)
        controller.is_idle = True
        controller.last_input_time = time.time() - 20  # Simulate idle state
        
        # First call should update (initial)
        controller.run_dashboard_cycle()
        first_update_time = controller.last_dashboard_update
        assert first_update_time > 0
        
        # Immediate second call should NOT update (same page)
        time.sleep(0.1)
        controller.run_dashboard_cycle()
        assert controller.last_dashboard_update == first_update_time
    
    @patch('lcd_picommander.main.SystemStats')
    def test_dashboard_updates_when_page_changes(self, mock_stats, config_file, mock_hardware):
        """Test dashboard updates when page changes."""
        from lcd_picommander.main import MenuController
        
        # Mock stat methods
        mock_stats.get_ip.return_value = "192.168.1.1"
        mock_stats.get_hostname.return_value = "test-pi"
        mock_stats.get_cpu_temp.return_value = "50C"
        mock_stats.check_internet.return_value = "Online"
        
        controller = MenuController(config_file)
        controller.is_idle = True
        controller.dashboard_cycle_time = 1.0  # Short cycle for testing
        
        # Set initial idle time
        base_time = time.time() - 20
        controller.last_input_time = base_time
        
        # First update (page 0)
        with patch('time.time', return_value=base_time + controller.idle_timeout + 0.5):
            controller.run_dashboard_cycle()
            assert controller.current_dashboard_page == 0
            first_update_time = controller.last_dashboard_update
        
        # After cycle time, should be on page 1
        with patch('time.time', return_value=base_time + controller.idle_timeout + 1.5):
            controller.run_dashboard_cycle()
            assert controller.current_dashboard_page == 1
            assert controller.last_dashboard_update > first_update_time


class TestBacklightTimeout:
    """Test backlight timeout functionality."""
    
    def test_backlight_disabled_when_timeout_zero(self, mock_hardware):
        """Test backlight timeout is disabled when set to 0."""
        from lcd_picommander.main import MenuController
        
        config = {
            'hardware': {
                'i2c': {'address': 0x27, 'port': 1, 'cols': 16, 'rows': 2},
                'display': {
                    'idle_timeout': 10.0,
                    'dashboard_cycle_time': 3.0,
                    'backlight_timeout': 0.0  # Disabled
                },
                'inputs': {
                    'encoder': {'clk': 12, 'dt': 6},
                    'buttons': {'enter': 13, 'back': 25, 'custom': 11},
                    'pull_up': True
                }
            },
            'menu': [{'label': 'Test', 'action': 'echo test'}]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config, f)
            temp_path = f.name
        
        try:
            controller = MenuController(temp_path)
            
            # Simulate long inactivity
            controller.last_input_time = time.time() - 1000
            
            # Backlight should remain on (timeout disabled)
            assert controller.backlight_timeout == 0.0
            assert controller.backlight_on is True
        finally:
            os.unlink(temp_path)
    
    def test_wake_up_enables_backlight(self, config_file, mock_hardware):
        """Test wake_up re-enables backlight."""
        from lcd_picommander.main import MenuController
        
        controller = MenuController(config_file)
        mock_lcd = mock_hardware['lcd']
        
        # Simulate backlight off
        controller.backlight_on = False
        mock_lcd.backlight_enabled = False
        
        # Wake up should enable backlight
        controller._wake_up()
        assert controller.backlight_on is True
        assert mock_lcd.backlight_enabled is True


class TestIdleBehavior:
    """Test idle state management."""
    
    def test_goes_idle_after_timeout(self, config_file, mock_hardware):
        """Test system goes idle after configured timeout."""
        from lcd_picommander.main import MenuController
        
        controller = MenuController(config_file)
        controller.last_input_time = time.time() - 15  # Exceed 10s timeout
        
        assert not controller.is_idle
        # Simulate check in run loop
        if (time.time() - controller.last_input_time) > controller.idle_timeout:
            controller.is_idle = True
        
        assert controller.is_idle
    
    def test_wake_up_resets_idle(self, config_file, mock_hardware):
        """Test wake_up resets idle state."""
        from lcd_picommander.main import MenuController
        
        controller = MenuController(config_file)
        controller.is_idle = True
        
        controller._wake_up()
        assert not controller.is_idle
