import sys
import yaml
import time
import subprocess
import argparse
import logging
from pathlib import Path
from collections import deque
from threading import Lock

# Local imports
from .system_stats import SystemStats
from .menu import MenuNode
from .hardware import LCDDisplay, GPIOInputs

# Setup Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MenuController:
    def __init__(self, config_path):
        self.config = self._load_config(config_path)
        self.hw_conf = self.config['hardware']
        self.lcd_lock = Lock()
        
        # State
        self.current_menu_list = [] 
        self.parent_stack = deque() 
        self.cursor_pos = 0         
        self.list_offset = 0        
        self.in_action_view = False 
        
        # Idle State
        self.last_input_time = time.time()
        display_config = self.hw_conf.get('display', {})
        self.idle_timeout = display_config.get('idle_timeout', 15.0)
        self.dashboard_cycle_time = display_config.get('dashboard_cycle_time', 5.0)
        self.backlight_timeout = display_config.get('backlight_timeout', 0.0)
        self.is_idle = False
        self.backlight_on = True
        self.last_dashboard_update = 0
        self.current_dashboard_page = 0
        
        # Quick Launch Configuration
        self.quick_launch_config = self.config.get('quick_launch', {})
        
        # Initialize Hardware
        self.lcd_display = LCDDisplay(self.hw_conf)
        self.lcd = self.lcd_display.lcd
        self.cols = self.lcd_display.cols
        self.rows = self.lcd_display.rows
        
        self.gpio_inputs = GPIOInputs(self.hw_conf)
        self._setup_gpio_callbacks()
        
        # Load Menu Tree
        self.root_nodes = self._parse_menu(self.config['menu'])
        self.current_menu_list = self.root_nodes
        
        self.update_display()

    def _load_config(self, path):
        try:
            with open(path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            sys.exit(1)

    def _parse_menu(self, raw_items):
        nodes = []
        for item in raw_items:
            children = self._parse_menu(item.get('items', []))
            nodes.append(MenuNode(
                label=item.get('label', 'Unknown'),
                action=item.get('action'),
                children=children,
                wait_for_key=item.get('wait_for_key', False)
            ))
        return nodes

    def _setup_gpio_callbacks(self):
        """Setup callbacks for GPIO inputs."""
        self.gpio_inputs.encoder.when_rotated_clockwise = self._on_scroll_down
        self.gpio_inputs.encoder.when_rotated_counter_clockwise = self._on_scroll_up
        
        self.gpio_inputs.btn_enter.when_pressed = self._on_enter
        self.gpio_inputs.btn_back.when_pressed = self._on_back
        self.gpio_inputs.btn_home.when_pressed = self._on_home
        self.gpio_inputs.btn_launch.when_pressed = self._on_launch

    def _wake_up(self):
        self.last_input_time = time.time()
        if self.is_idle:
            self.is_idle = False
            self.update_display()
            return True
        if not self.backlight_on:
            self.backlight_on = True
            self.lcd.backlight_enabled = True
        return False

    def _on_scroll_down(self):
        if self._wake_up(): return
        if self.in_action_view: return
        
        max_idx = len(self.current_menu_list) - 1
        if (self.list_offset + self.cursor_pos) < max_idx:
            if self.cursor_pos < (self.rows - 1):
                self.cursor_pos += 1
            else:
                self.list_offset += 1
            self.update_display()

    def _on_scroll_up(self):
        if self._wake_up(): return
        if self.in_action_view: return

        if self.cursor_pos > 0:
            self.cursor_pos -= 1
            self.update_display()
        elif self.list_offset > 0:
            self.list_offset -= 1
            self.update_display()

    def _on_enter(self):
        if self._wake_up(): return
        if self.in_action_view:
            self.in_action_view = False
            self.update_display()
            return

        selected_node = self.current_menu_list[self.list_offset + self.cursor_pos]
        if selected_node.is_submenu:
            self.parent_stack.append((self.current_menu_list, self.list_offset, self.cursor_pos))
            self.current_menu_list = selected_node.children
            self.list_offset = 0
            self.cursor_pos = 0
            self.update_display()
        elif selected_node.action:
            self._execute_action(selected_node)

    def _on_back(self):
        if self._wake_up(): return
        if self.in_action_view:
            self.in_action_view = False
            self.update_display()
            return

        if self.parent_stack:
            prev_list, prev_offset, prev_cursor = self.parent_stack.pop()
            self.current_menu_list = prev_list
            self.list_offset = prev_offset
            self.cursor_pos = prev_cursor
            self.update_display()

    def _on_home(self):
        if self._wake_up(): return
        if self.parent_stack:
            self.current_menu_list = self.root_nodes
            self.parent_stack.clear()
            self.list_offset = 0
            self.cursor_pos = 0
            self.in_action_view = False
            self.update_display()

    def _on_launch(self):
        """Specifically handles Button 3 logic: Execute configured quick launch command."""
        if self._wake_up(): return
        
        # Execute the quick launch command from config if available
        command = self.quick_launch_config.get('command')
        if not command:
            logger.warning("No quick_launch command configured")
            return
        
        # Create a temporary MenuNode to execute the configured command
        quick_launch_node = MenuNode(
            label="Quick Launch",
            action=command,
            wait_for_key=self.quick_launch_config.get('wait_for_key', False)
        )
        self._execute_action(quick_launch_node)

    def _is_stat_wildcard(self, action):
        """Check if action is a stat wildcard (e.g., 'stat:get_cpu_temp')."""
        return isinstance(action, str) and action.startswith('stat:')
    
    def _execute_stat_wildcard(self, action):
        """Execute a SystemStats method based on wildcard syntax.
        
        Args:
            action: String in format 'stat:method_name'
            
        Returns:
            Output string from the stat method
        """
        try:
            # Extract method name from 'stat:method_name'
            parts = action.split(':', 1)
            if len(parts) != 2 or not parts[1]:
                return "Invalid format"
            
            method_name = parts[1]
            
            # Security: Only allow public getter methods (start with 'get_' or 'check_')
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
    
    def _execute_action(self, node):
        with self.lcd_lock:
            self.lcd.clear()
            self.lcd.write_string("Executing...")
        
        # Check if this is a stat wildcard or a shell command
        if self._is_stat_wildcard(node.action):
            output = self._execute_stat_wildcard(node.action)
        else:
            # Execute as shell command
            try:
                result = subprocess.run(
                    node.action, shell=True, capture_output=True, text=True, timeout=30
                )
                output = result.stdout.strip() if result.stdout else result.stderr.strip()
                if not output:
                    output = "Done." if result.returncode == 0 else "Error"
            except Exception as e:
                output = f"Err: {str(e)[:15]}"

        if node.wait_for_key:
            self.in_action_view = True
            with self.lcd_lock:
                self.lcd.clear()
                lines = [output[i:i+self.cols] for i in range(0, len(output), self.cols)]
                for i, line in enumerate(lines[:self.rows]):
                    self.lcd.cursor_pos = (i, 0)
                    self.lcd.write_string(line)
        else:
            with self.lcd_lock:
                self.lcd.clear()
                self.lcd.write_string(output[:self.cols])
            time.sleep(2)
            self.update_display()

    def update_display(self):
        with self.lcd_lock:
            self.lcd.clear()
            visible_items = self.current_menu_list[self.list_offset : self.list_offset + self.rows]
            for row, node in enumerate(visible_items):
                self.lcd.cursor_pos = (row, 0)
                prefix = ">" if row == self.cursor_pos else " "
                self.lcd.write_string(f"{prefix}{node.label[:self.cols-1]}")

    def run_dashboard_cycle(self):
        """Display dashboard with cycling pages.
        
        Stats are only refreshed when:
        1. The page changes (to reduce flickering)
        2. There is only one page (refresh with cycle time)
        """
        pages = [
            ("IP", "get_ip", "H", "get_hostname"),
            ("Temp", "get_cpu_temp", "Net", "check_internet")
        ]
        
        current_time = time.time()
        
        # Calculate which page we should be on
        time_since_idle = current_time - (self.last_input_time + self.idle_timeout)
        target_page = int(time_since_idle / self.dashboard_cycle_time) % len(pages)
        
        # Only update if page changed or if single page and cycle time elapsed
        should_update = False
        if len(pages) == 1:
            # Single page: refresh with cycle time
            if current_time - self.last_dashboard_update >= self.dashboard_cycle_time:
                should_update = True
        else:
            # Multiple pages: only update when page changes
            if target_page != self.current_dashboard_page:
                should_update = True
        
        if should_update:
            self.current_dashboard_page = target_page
            self.last_dashboard_update = current_time
            
            # Get stats for current page
            try:
                label1, stat1, label2, stat2 = pages[self.current_dashboard_page]
                stat1_value = getattr(SystemStats, stat1)()
                stat2_value = getattr(SystemStats, stat2)()
                
                line1 = f"{label1}:{stat1_value}"
                line2 = f"{label2}:{stat2_value}"

                with self.lcd_lock:
                    self.lcd.clear()
                    self.lcd.cursor_pos = (0, 0)
                    self.lcd.write_string(line1[:self.cols])
                    self.lcd.cursor_pos = (1, 0)
                    self.lcd.write_string(line2[:self.cols])
            except (AttributeError, Exception) as e:
                logger.error(f"Dashboard cycle error: {e}")
                with self.lcd_lock:
                    self.lcd.clear()
                    self.lcd.write_string("Dashboard Error")

    def run(self):
        try:
            while True:
                time.sleep(1)
                current_time = time.time()
                
                # Check for idle timeout (start dashboard)
                if not self.is_idle and (current_time - self.last_input_time) > self.idle_timeout:
                    self.is_idle = True
                    
                # Check for backlight timeout (turn off backlight)
                if (self.backlight_timeout > 0 and 
                    self.backlight_on and 
                    (current_time - self.last_input_time) > self.backlight_timeout):
                    self.backlight_on = False
                    with self.lcd_lock:
                        self.lcd.backlight_enabled = False
                
                # Run dashboard if idle
                if self.is_idle:
                    self.run_dashboard_cycle()
        except KeyboardInterrupt:
            with self.lcd_lock:
                self.lcd.clear()
                self.lcd.write_string("Shutdown")
                self.lcd.close()

def main():
    parser = argparse.ArgumentParser(description="LCD PiCommander")
    parser.add_argument("--config", default="config.yaml", help="Path to config file")
    args = parser.parse_args()
    app = MenuController(Path(args.config))
    app.run()

if __name__ == "__main__":
    main()