# Tests for LCD PiCommander

This directory contains the pytest test suite for LCD PiCommander.

## Running Tests

### Install Test Dependencies

```bash
pip install -e ".[test]"
```

Or install pytest and pytest-cov directly:

```bash
pip install pytest pytest-cov
```

### Run All Tests

```bash
pytest
```

### Run with Verbose Output

```bash
pytest -v
```

### Run Specific Test File

```bash
pytest tests/test_system_stats.py -v
pytest tests/test_wildcard.py -v
```

### Run with Coverage Report

```bash
pytest --cov=lcd_picommander --cov-report=html
```

This will generate an HTML coverage report in the `htmlcov/` directory.

## Test Structure

### test_system_stats.py

Tests for the `SystemStats` class covering all stat methods:
- Network stats (IP, hostname, internet connectivity)
- CPU stats (temperature, usage, load)
- Memory stats (usage percentage and MB format)
- Disk stats (usage percentage and GB format)
- System info (uptime, OS info, kernel version)

### test_wildcard.py

Tests for the wildcard functionality:
- Wildcard detection (`stat:method_name` format)
- Wildcard execution (calling SystemStats methods)
- Security controls (method whitelisting)
- Integration tests (all stat methods via wildcards)
- MenuNode class tests

## Notes

Tests are designed to work without hardware dependencies (no Raspberry Pi required). They use mocks and direct module imports to avoid requiring `gpiozero`, `RPLCD`, and other hardware-specific libraries.
