"""Tests for dashboard configuration feature."""
import pytest
import time
from unittest.mock import MagicMock, patch
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
def base_config():
    """Create a minimal base config for testing."""
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


def create_config_file(config_dict):
    """Helper to create a temporary config file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(config_dict, f)
        return f.name


class TestDashboardConfigLoading:
    """Test dashboard configuration loading."""
    
    def test_default_dashboard_when_not_configured(self, base_config, mock_hardware):
        """Test that default dashboard is used when not configured."""
        from lcd_picommander.main import MenuController
        
        config_file = create_config_file(base_config)
        try:
            controller = MenuController(config_file)
            
            # Should have default 2-page dashboard
            assert len(controller.dashboard_config) == 2
            assert controller.dashboard_config[0] == [
                ("IP", "stat:get_ip"),
                ("H", "stat:get_hostname")
            ]
            assert controller.dashboard_config[1] == [
                ("Temp", "stat:get_cpu_temp"),
                ("Net", "stat:check_internet")
            ]
        finally:
            os.unlink(config_file)
    
    def test_custom_dashboard_single_page(self, base_config, mock_hardware):
        """Test loading custom single-page dashboard."""
        from lcd_picommander.main import MenuController
        
        base_config['dashboard'] = {
            'pages': [
                [
                    {'label': 'CPU', 'stat': 'stat:get_cpu_temp'},
                    {'label': 'Mem', 'stat': 'stat:get_memory_usage'}
                ]
            ]
        }
        
        config_file = create_config_file(base_config)
        try:
            controller = MenuController(config_file)
            
            assert len(controller.dashboard_config) == 1
            assert controller.dashboard_config[0] == [
                ("CPU", "stat:get_cpu_temp"),
                ("Mem", "stat:get_memory_usage")
            ]
        finally:
            os.unlink(config_file)
    
    def test_custom_dashboard_multiple_pages(self, base_config, mock_hardware):
        """Test loading custom multi-page dashboard."""
        from lcd_picommander.main import MenuController
        
        base_config['dashboard'] = {
            'pages': [
                [
                    {'label': 'IP', 'stat': 'stat:get_ip'},
                    {'label': 'Host', 'stat': 'stat:get_hostname'}
                ],
                [
                    {'label': 'CPU', 'stat': 'stat:get_cpu_temp'},
                    {'label': 'Load', 'stat': 'stat:get_cpu_load'}
                ],
                [
                    {'label': 'Mem', 'stat': 'stat:get_memory_usage'},
                    {'label': 'Disk', 'stat': 'stat:get_disk_usage'}
                ]
            ]
        }
        
        config_file = create_config_file(base_config)
        try:
            controller = MenuController(config_file)
            
            assert len(controller.dashboard_config) == 3
            assert controller.dashboard_config[0][0] == ("IP", "stat:get_ip")
            assert controller.dashboard_config[1][0] == ("CPU", "stat:get_cpu_temp")
            assert controller.dashboard_config[2][0] == ("Mem", "stat:get_memory_usage")
        finally:
            os.unlink(config_file)
    
    def test_empty_dashboard_config_uses_default(self, base_config, mock_hardware):
        """Test that empty dashboard config falls back to default."""
        from lcd_picommander.main import MenuController
        
        base_config['dashboard'] = {}
        
        config_file = create_config_file(base_config)
        try:
            controller = MenuController(config_file)
            
            # Should use default dashboard
            assert len(controller.dashboard_config) == 2
        finally:
            os.unlink(config_file)
    
    def test_dashboard_with_empty_pages_uses_default(self, base_config, mock_hardware):
        """Test that dashboard with only empty pages falls back to default."""
        from lcd_picommander.main import MenuController
        
        base_config['dashboard'] = {
            'pages': [[], [], []]  # All empty pages
        }
        
        config_file = create_config_file(base_config)
        try:
            controller = MenuController(config_file)
            
            # Should fall back to default dashboard
            assert len(controller.dashboard_config) == 2
            assert controller.dashboard_config[0] == [
                ("IP", "stat:get_ip"),
                ("H", "stat:get_hostname")
            ]
        finally:
            os.unlink(config_file)


class TestDashboardCycleWithConfig:
    """Test dashboard cycle behavior with custom configuration."""
    
    @patch('lcd_picommander.main.SystemStats')
    def test_dashboard_displays_custom_stats(self, mock_stats, base_config, mock_hardware):
        """Test that custom dashboard stats are displayed correctly."""
        from lcd_picommander.main import MenuController
        
        # Configure custom dashboard
        base_config['dashboard'] = {
            'pages': [
                [
                    {'label': 'CPU', 'stat': 'stat:get_cpu_temp'},
                    {'label': 'Mem', 'stat': 'stat:get_memory_usage'}
                ]
            ]
        }
        
        # Mock stat methods
        mock_stats.get_cpu_temp.return_value = "45.0C"
        mock_stats.get_memory_usage.return_value = "65.2%"
        
        config_file = create_config_file(base_config)
        try:
            controller = MenuController(config_file)
            controller.is_idle = True
            controller.last_input_time = time.time() - 20
            
            # Run dashboard cycle
            with patch('time.time', return_value=100.0):
                controller.last_input_time = 80.0
                controller.run_dashboard_cycle()
            
            # Verify LCD was updated with custom stats
            mock_lcd = mock_hardware['lcd']
            assert mock_lcd.write_string.called
            
            # Check that our custom stats were used
            calls = [str(call) for call in mock_lcd.write_string.call_args_list]
            assert any('CPU:45.0C' in str(call) for call in calls)
            assert any('Mem:65.2%' in str(call) for call in calls)
        finally:
            os.unlink(config_file)
    
    @patch('lcd_picommander.main.SystemStats')
    def test_dashboard_cycles_through_custom_pages(self, mock_stats, base_config, mock_hardware):
        """Test that dashboard cycles through custom pages."""
        from lcd_picommander.main import MenuController
        
        # Configure multi-page dashboard
        base_config['dashboard'] = {
            'pages': [
                [
                    {'label': 'P1A', 'stat': 'stat:get_ip'},
                    {'label': 'P1B', 'stat': 'stat:get_hostname'}
                ],
                [
                    {'label': 'P2A', 'stat': 'stat:get_cpu_temp'},
                    {'label': 'P2B', 'stat': 'stat:get_cpu_usage'}
                ]
            ]
        }
        
        # Mock stat methods
        mock_stats.get_ip.return_value = "192.168.1.1"
        mock_stats.get_hostname.return_value = "pi"
        mock_stats.get_cpu_temp.return_value = "50C"
        mock_stats.get_cpu_usage.return_value = "25%"
        
        config_file = create_config_file(base_config)
        try:
            controller = MenuController(config_file)
            controller.is_idle = True
            controller.dashboard_cycle_time = 1.0
            
            base_idle_time = 80.0
            controller.last_input_time = base_idle_time
            
            # First page (page 0)
            with patch('time.time', return_value=base_idle_time + controller.idle_timeout + 0.5):
                controller.run_dashboard_cycle()
                assert controller.current_dashboard_page == 0
            
            # Second page (page 1)
            with patch('time.time', return_value=base_idle_time + controller.idle_timeout + 1.5):
                controller.run_dashboard_cycle()
                assert controller.current_dashboard_page == 1
            
            # Back to first page (page 0)
            with patch('time.time', return_value=base_idle_time + controller.idle_timeout + 2.5):
                controller.run_dashboard_cycle()
                assert controller.current_dashboard_page == 0
        finally:
            os.unlink(config_file)


class TestDashboardPageFormats:
    """Test various dashboard page formats."""
    
    def test_dashboard_with_missing_label(self, base_config, mock_hardware):
        """Test that missing labels default to 'N/A'."""
        from lcd_picommander.main import MenuController
        
        base_config['dashboard'] = {
            'pages': [
                [
                    {'stat': 'stat:get_ip'},  # Missing label
                ]
            ]
        }
        
        config_file = create_config_file(base_config)
        try:
            controller = MenuController(config_file)
            assert controller.dashboard_config[0][0][0] == "N/A"
        finally:
            os.unlink(config_file)
    
    def test_dashboard_with_missing_stat(self, base_config, mock_hardware):
        """Test that missing stats default to hostname stat."""
        from lcd_picommander.main import MenuController
        
        base_config['dashboard'] = {
            'pages': [
                [
                    {'label': 'Test'},  # Missing stat
                ]
            ]
        }
        
        config_file = create_config_file(base_config)
        try:
            controller = MenuController(config_file)
            assert controller.dashboard_config[0][0][1] == "stat:get_hostname"
        finally:
            os.unlink(config_file)
