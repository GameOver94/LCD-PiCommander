"""Hardware initialization and management for LCD and GPIO."""
import sys
import logging
from gpiozero import Button, RotaryEncoder
from RPLCD.i2c import CharLCD

logger = logging.getLogger(__name__)


class LCDDisplay:
    """Manages the I2C LCD display."""
    
    def __init__(self, hw_config):
        """Initialize LCD with hardware configuration.
        
        Args:
            hw_config: Dictionary containing i2c configuration
        """
        i2c = hw_config['i2c']
        try:
            self.lcd = CharLCD(
                i2c_expander='PCF8574',
                address=i2c['address'],
                port=i2c['port'],
                cols=i2c['cols'],
                rows=i2c['rows'],
                dotsize=8
            )
            self.lcd.clear()
            self.lcd.write_string("LCD PiCommander")
            self.cols = i2c['cols']
            self.rows = i2c['rows']
        except Exception as e:
            logger.error(f"LCD Init failed: {e}")
            sys.exit(1)


class GPIOInputs:
    """Manages GPIO inputs including encoder and buttons."""
    
    def __init__(self, hw_config):
        """Initialize GPIO inputs with hardware configuration.
        
        Args:
            hw_config: Dictionary containing inputs configuration
        """
        inputs = hw_config['inputs']
        pull_up = inputs.get('pull_up', True)
        
        # Encoder
        self.encoder = RotaryEncoder(
            inputs['encoder']['clk'], 
            inputs['encoder']['dt'], 
            wrap=False
        )

        # Buttons (Debounced)
        self.btn_enter = Button(inputs['buttons']['enter'], pull_up=pull_up, bounce_time=0.1)
        self.btn_back = Button(inputs['buttons']['back'], pull_up=pull_up, bounce_time=0.1)
        self.btn_home = Button(inputs['buttons']['custom'], pull_up=pull_up, bounce_time=0.1)
        
        # New Button 3 (Pin 8) mapped to Launch Command
        self.btn_launch = Button(8, pull_up=pull_up, bounce_time=0.1)
