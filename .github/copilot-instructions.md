# Copilot Instructions for LCD PiCommander

This is a casual pet project designed for a Raspberry Pi. It creates a physical menu system on a character LCD (16x2 or 20x4).

## Project Guidelines

### Coding Style
- **Casual & Clear**: Functionality comes first. Keep code readable and simple.
- **Python**: We use Python 3.13+. Follow standard PEP 8, but don't stress too much about strict type hinting unless it helps clarity.
- **No Over-Engineering**: Avoid complex design patterns if a simple function or class will do.

### Hardware Context
- **Platform**: Raspberry Pi (Latest Raspberry Pi OS based on Debian Trixie).
- **Display**: PCF8574 I2C LCD (User `RPLCD` library).
- **Input**:
  - Rotary Encoder (CLK, DT, SW) used for navigation.
  - Physical Buttons (Back, Home, Custom) used for actions.
  - We use `gpiozero` for all input handling.

### Libraries
- Use `gpiozero` for buttons and rotary encoders.
- Use `RPLCD` for the I2C LCD.
- Use `subprocess` for executing system commands (Docker, shell scripts).

### Deployment
- **Tool**: `pipx`.
- **Strategy**: The tool is intended to be installed via `pipx` on the Pi. Ensure the structure (`pyproject.toml`) supports this.

### Development Tips
- Since I might be coding on a PC (not the Pi itself), code should ideally handle `ImportError` for hardware libraries gracefully (e.g., using mocks or dummy classes if `RPi.GPIO` is missing) so I can test logic locally.
- Logging is preferred over `print` statements.

### Goal
Have fun building a cool physical interface for my homelab server!
