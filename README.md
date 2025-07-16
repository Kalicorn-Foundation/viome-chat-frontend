# SM UI Main

A transparent chat application with global hotkey support.

## Recent Changes

### Global Hotkey Fix

- **Issue**: The `keyboard` module was causing hotkey binding to become unreliable over time
- **Solution**: Replaced `keyboard` module with `pynput` for more stable global hotkey support
- **Benefits**:
  - More reliable hotkey detection
  - Better cross-platform compatibility
  - Proper resource cleanup

## Installation

### Prerequisites

- Python 3.7+
- Node.js (for Hangul composition)

### Install Dependencies

#### Option 1: Using the install script

```bash
python install_dependencies.py
```

#### Option 2: Manual installation

```bash
pip install -r requirements.txt
npm install
```

## Usage

### Global Hotkeys

- `Ctrl+Shift+Z`: Toggle window visibility
- `Ctrl+Alt+=`: Increase transparency
- `Ctrl+Alt+-`: Decrease transparency
- `Alt(right)`: Navigate between languages
- `Ctrl+Shift+R`: Mark messages as read

### Configuration

Create a `config.json` file based on `config_example.json` with your settings.

## Features

- Transparent overlay window
- Global hotkey support
- Korean/English input method switching
- WebSocket communication
- Message encryption
- Notification system with icon changes

## Troubleshooting

### Hotkey Issues

If hotkeys stop working:

1. Restart the application
2. Check if other applications are using the same hotkeys
3. Ensure the application has proper permissions

### Permission Issues (Windows)

On Windows, you may need to run the application as administrator for global hotkeys to work properly.
