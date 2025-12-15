# ViewFinder

A lightweight quality-of-life utility for **Blackhawk Rescue Mission 5** on Roblox.

**ViewFinder** provides an on-screen **crosshair overlay** and a **magnifier window** to improve visibility when operating mainly helicopter-mounted weapons — addressing the lack of a built-in crosshair and limited zoom options.

This tool is fully **external**, **non-intrusive**, and safe to use.

***The tool is still in developement***

---

## Why This Tool Was Created

BRM5's helicopter door guns offer no native crosshair and no meaningful zoom for long-range engagement.

This utility adds:
- A reliable, centered, and fully customizable crosshair
- A magnified view of the selected area on your screen with adjustable zoom levels
- Individual overlay toggles for maximum flexibility

Together, they make aiming and target identification far easier during air support operations.

---

## Main Features

### ✓ Customizable Crosshair Overlay
- Multiple styles: cross, dot, and circle
- Adjustable size, thickness, gap, and opacity
- Custom colors for crosshair and outline
- Optional center dot and T-style (no top line)
- Real-time preview in configuration menu

### ✓ Adjustable Magnifier Window
- Variable zoom levels (0.1x - 10x)
- Configurable capture radius and window size
- Adjustable refresh rate (10-60 FPS)
- Draggable magnified view window
- Smooth interpolation for quality scaling

 # ViewFinder — Quick Start

A lightweight external overlay that provides a customizable crosshair and a magnifier window for Blackhawk Rescue Mission 5 (BRM5) on Roblox.

Quick, copy-paste steps for day-to-day use:

- Prerequisites: `Python 3.9+`
- Install dependencies:

```bash
pip install -r requirements.txt
```

If `pip install` fails, run the included installer instead:

```bash
python Info/req_installer.py
```

- Run the configuration menu (optional, recommended once):

```bash
python ViewFinder_Config_Menu.pyw
```

- Run the application:

```bash
python ViewFinder_0.9.pyw
```

You can also double-click the `.pyw` files to run without a console window.

---

**Controls (defaults — configurable in `ViewFinder_Config_Menu.pyw`):**

- `Up Arrow`: Toggle auto-detection
- `Down Arrow`: Exit program
- `Right Arrow`: Hide/show all overlays
- `M`: Toggle magnifier overlay
- `C`: Toggle crosshair overlay

---

## Common Troubleshooting (fast checks)

 - Note: this project is under active development and will most definitely have bugs; please report issues when you find them.


## Configuration (short)

1. Run `ViewFinder_Config_Menu.pyw` to change the settings.

2. Save configuration (The settings are written to `viewfinder_config.json`).

3. Run the application

If you prefer standalone executables, run the compiler in `Info/compiler.py` (for automatic detection, move the compiler up by one directory) to produce `.exe` files — the compiled executables do not require Python or installed dependencies. If you need to remove installed dependencies later, use:

```bash
python Info/req_uninstaller.py
```

---

## Technical / Development Notes

This section is for maintainers and contributors.

### Project layout

```
ViewFinder/
├── ViewFinder_0.9.pyw              # Main application
├── ViewFinder_Config_Menu.pyw      # Configuration GUI
├── crosshair_overlay.py            # Crosshair overlay logic
├── crosshair_config_widget.py      # Crosshair settings UI
├── crosshair_preview.py            # Crosshair preview widget
├── magnifier_overlay.py            # Magnifier overlay logic
├── magnifier_config_widget.py      # Magnifier settings UI
├── instructions_menu.py            # On-screen instructions display
├── overlay_toggles.py              # Overlay toggle management
├── Info/                           # Helper scripts and installers
│   ├── compiler.py                 # Compiles everything into three .exe files
│   ├── req_installer.py            # Alternative dependency installer
│   ├── req_uninstaller.py          # Dependency uninstaller
│   ├── requirements.txt            # Python dependencies
├── viewfinder_config.json          # Saved configuration (generated)
└── README.md                       # This file
```

### Dependencies

See `requirements.txt`. The project targets Python 3.9+. If platform-specific permission or environment issues prevent `pip` usage, `Info/req_installer.py` attempts a more guided install.

### Known limitations

- High magnification (8x+) with large radii may drop frames.
- Auto-detection requires manual calibration for non-1080p displays.
- This tool is an external overlay and does not interface with Roblox internals.

### Roadmap / TODO

- Auto-detection: add a calibration wizard and presets to simplify setup. Current manual workaround: open `ViewFinder_Config_Menu.pyw` and re-calibrate X/Y for your resolution.

### Contributing

- Fork the repo and open a PR. Keep changes focused and test on Windows (primary target).
- If adding dependencies, update `requirements.txt` and provide rationale in the PR.

---

## Credits & License

Developed for the BRM5 community.

MIT License — see `LICENSE` for details.

---