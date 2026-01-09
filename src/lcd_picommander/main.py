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
        self.idle_timeout = 15.0
        self.is_idle = False
        
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

    def _execute_action(self, node):
        with self.lcd_lock:
            self.lcd.clear()
            self.lcd.write_string("Executing...")
        
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
        pages = [
            (f"IP:{SystemStats.get_ip()}", f"H:{SystemStats.get_hostname()}"),
            (f"Temp:{SystemStats.get_cpu_temp()}", f"Net:{SystemStats.check_internet()}")
        ]
        page_idx = (int(time.time()) // 3) % len(pages)
        line1, line2 = pages[page_idx]

        with self.lcd_lock:
            self.lcd.clear()
            self.lcd.cursor_pos = (0, 0)
            self.lcd.write_string(line1[:self.cols])
            self.lcd.cursor_pos = (1, 0)
            self.lcd.write_string(line2[:self.cols])

    def run(self):
        try:
            while True:
                time.sleep(1)
                if not self.is_idle and (time.time() - self.last_input_time) > self.idle_timeout:
                    self.is_idle = True
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