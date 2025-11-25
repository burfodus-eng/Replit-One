# Reef Controller

## Overview
Reef Controller is a sophisticated web-based application built with FastAPI, designed for real-time monitoring and control of reef aquarium equipment.

## Recent Changes
- **v2.2.2** (2025-11-25): Header readability fix - Title and clock now use brighter colors (#4fc3f7 cyan, #9575cd violet, #f06292 magenta gradient) with stronger glow effects for better visibility. Background now scrolls with page content (position: absolute instead of fixed).
- **v2.2.1** (2025-11-25): Color refinement - Reduced saturation of primary neon colors by ~20% (cyan #5cb8e2, violet #8a5fd6, magenta #d76fa1) for better blending with background. Dark Theme now uses grey overlay (rgba 51,51,51,0.28 for cards, 0.20 for inner) instead of pure black for more natural look.
- **v2.2.0** (2025-11-25): Theme system with Light/Dark modes - Background now scrolls with page (full width, no fixed), removed ALL backdrop blur from cards for clearer background visibility. Light Theme uses very subtle white overlay (rgba 255,255,255,0.03 for cards, 0.02 for inner elements), Dark Theme uses subtle dark overlay (rgba 0,0,0,0.25 for cards, 0.15 for inner elements). Theme persists in localStorage. Settings page has theme selector dropdown.
- **v2.1.0** (2025-11-25): Static background and UX polish - Replaced animated gradient with generated deep-ocean bioluminescent background image (coral silhouettes, glowing particles), removed ALL hover transform animations (no more flash/shimmer/bounce effects), UI is now completely static on mouseover except for color/shadow changes. Improves performance and visual stability.
- **v2.0.0** (2025-11-25): MAJOR VISUAL OVERHAUL - Transformed from monochrome to vibrant neon dashboard with aurora gradient background (#0b1026→#1a1446→#35105f), neon color palette (cyan #38bdf8, violet #7c3aed, magenta #ec4899), glowing interactive elements with text-shadow effects, gradient rainbow sliders (violet→cyan→magenta), enhanced glassmorphism cards with gradient borders, glow/bloom effects on all controls, radial lighting overlays, and comprehensive theming matching modern dashboard aesthetics. Fixed white-text readability on modal/table backgrounds.
- **v1.8.2** (2025-11-25): Added GPIO conflict detection for config import - rejects imports with duplicate GPIO assignments before any changes are made, preventing hardware conflicts. Also added registry-level guards to prevent registering devices on already-claimed GPIO pins.
- **v1.8.1** (2025-11-25): Fixed config import hot-reload bug - imported device configurations now immediately apply to hardware registry without requiring restart. This resolves LED jitter issues when importing configs with different GPIO mappings.

Its primary purpose is to manage LED lighting arrays, battery backup systems, and wave pumps through an intuitive web interface. The project aims to provide comprehensive control over an aquarium environment, featuring real-time telemetry, interactive controls, and intelligent power management capabilities. Key ambitions include offering production-ready wave pump control with various patterns, granular per-LED control with intelligent power shedding, and a touch-optimized user interface for easy interaction.

## User Preferences
None specified yet.

## System Architecture
The Reef Controller is built upon a FastAPI backend and a vanilla JavaScript frontend, emphasizing a touch-optimized user experience.

### UI/UX Decisions
- **Touch-Optimized Interface**: Designed for 1920x1080 displays with large touch targets and "weather-app" styling with ocean gradient backgrounds and clean card layouts.
- **Real-time Updates**: UI polls backend every 2 seconds for synchronized telemetry and control states.
- **Navigation Menu**: Hamburger menu in header provides access to Dashboard, Logs, and Hardware Settings pages with smooth page transitions.
- **Interactive Modals**: Full-screen modals for settings, history, and a dedicated Schedule Calendar (95vw×90vh) with weekly grid display.
- **Visual Feedback**: Disabled LEDs are gray, array cards show intensity limits, and disabled scheduled tasks are grayed out.
- **Chart Modals**: History and power charts use 90% viewport width.
- **Preset Editor**: Full-screen modal with sidebar, Canvas-based graphical curve editor for 12 wavemakers, and interactive keyframe manipulation.
- **Scheduler Calendar View**: Weekly grid (24 hours x 7 days) with visual task placement, clickable cells for new tasks, and clickable task badges for editing.
- **Toast Notifications**: Non-blocking success/error/info toasts replace `alert()` calls.
- **Clean Interactions**: Removed button hover bounce effects. Feed Mode button toggles states.
- **Logs Viewer**: Full-page log viewer with auto-refresh, log level filtering (INFO/WARNING/ERROR), and real-time workflow output display.
- **Hardware Settings Page**: Compact 8-column grid layout for GPIO device management. Shows device ID with type as subtitle, editable channel names, GPIO pin assignments (with optional monitor pin), PWM frequency, intensity range, and voltage limits. Devices are sorted by type (wavemakers first) then channel number. Compact action buttons (Test/Save/Del) without emoji. Tabs for Wavemakers, LEDs, and All Devices views.

### Technical Implementations
- **Backend (FastAPI)**:
    - **Services**: `StageManager`, `PowerAllocator`, `EventsService`, `AutomationService`, `SystemHealthService`, `JobScheduler`, `Store` (SQLite persistence).
    - **API Endpoints**: Comprehensive RESTful API for controlling arrays, wavemakers, telemetry, events, and historical data, supporting partial updates.
    - **Hardware Settings API**: Full CRUD operations for device configurations via `/api/settings/hardware/*` endpoints with GPIO pin conflict validation and LED follow relationship management.
    - **Logs API**: Real-time workflow log streaming via `/api/settings/logs` endpoint.
    - **Wavemaker Control**: 12 independent channels with various patterns, 20Hz control loop, 1Hz telemetry loop.
    - **LED Control**: Individual and array-level enable/disable, proportional scaling based on intensity limits.
    - **Intelligent Power Management**: Priority-based power shedding with hysteresis, running every second.
    - **Timezone Support**: Frontend detects browser timezone, backend uses `USER_TZ_OFFSET` for scheduler and ETA calculations.
    - **Database-Driven Configuration**: Device configurations (GPIO pins, PWM frequency, voltage limits, follow relationships) persisted in SQLite `device_configs` table, loaded automatically on startup with default device seeding.
- **Frontend (Vanilla JavaScript)**:
    - No external frameworks.
    - Uses HTML5 Canvas for sparklines and visual flow pattern displays, with `getBoundingClientRect()` for accurate mouse interaction.
    - Implements local state persistence for sliders/toggles.
    - Smart preset selector updates only on state changes to prevent visual jumping.

### Feature Specifications
- **Wavemaker Preset System**: Coordinated flow control across 12 wavemakers using 9 built-in presets with custom flow curves. Presets include: Gentle Flow, Pulse, Gyre Clockwise/Counter-Clockwise, Feed Mode, Random Reef, Sequential Walk (single channel 1-12), Knight Rider (bouncing 1-12-1), and Paired Police (oscillating pairs). Features a graphical Canvas-based editor with interactive keyframe editing and automated scheduler integration.
- **Feed Mode**: Manual button activation pauses all wavemakers for 10 minutes using a dedicated "Feed Mode" preset, then automatically restores the previous preset. Includes real-time countdown and scheduler integration.
- **Automation Scheduler UI**: Full-screen modal for managing scheduled preset activations with sidebar task list, form editor (time picker, preset selector, day-of-week filtering, enabled toggle), and full CRUD operations.
- **Automation Scheduler Backend**: Fully automated 24/7 preset activation system with 30-second precision, ±30 second time window matching, and automatic startup resume (up to 7 days backward search). Supports day-of-week filtering and timezone-aware execution.
- **Hardware Configuration System**: Database-driven device management with web-based configuration UI for GPIO pin assignments, PWM frequencies (wavemakers: 200Hz, LEDs: 800Hz), voltage limits (wavemakers: 0-0.6V, LEDs: 0-5V), and LED mirror relationships. Supports dynamic device addition/removal with automatic conflict detection and startup device seeding (default: WM1 on GPIO18, LED1 on GPIO19 following WM1). Device deletion properly unregisters from HAL, stopping output and cleaning up hardware resources.
- **Logs Viewer**: Real-time workflow log monitoring with auto-refresh, log level filtering, and search capabilities for troubleshooting and system health monitoring.
- **Wavemaker Subsystem**: Supports 12 independent channels with patterns (Off, Constant, Pulse, Gyre Left/Right, Random Reef), API for status, control, and 15-minute history. Channel names: Front Left/Right, Mid Left/Right, Back Left/Right, Side Left/Right Top/Bottom, Rear Left/Right.
- **LED Control**: Granular control over 3 arrays, each with 6 individual LEDs, configurable name, intensity limit, and priority.
- **Intelligent Power Management**: Automatic shedding of lowest-priority loads when power budget is exceeded, with hysteresis.
- **System Monitoring**: Real-time display of PV input, battery flow, and net power.
- **Simulation Mode**: Comprehensive software simulation for development, including diurnal PV curves, LED load calculation, battery flow, and configurable power budgets.

### System Design Choices
- **Hardware Abstraction Layer (HAL)**: Unifies control for simulated, Raspberry Pi (pigpio), and ESP32 serial USB adapter hardware via `HARDWARE_MODE` environment variable.
  - `HARDWARE_MODE=mock`: Software simulation (default)
  - `HARDWARE_MODE=pigpio` or `pi` or `real`: Raspberry Pi with pigpio daemon
  - `HARDWARE_MODE=esp32`: ESP32 USB-to-GPIO adapter with serial communication
- **ESP32 Serial Driver**: Supports USB-connected ESP32 boards (e.g., Keyestudio KS0413) using pyserial for PWM control. Protocol: `PIN:VALUE\n` format (VALUE: 0-255). Configurable via `ESP32_SERIAL_PORT` (default: COM4) and `ESP32_SERIAL_BAUD` (default: 115200).
- **Database**: SQLite for telemetry, event persistence, and device configuration storage (`device_configs` table).
- **Configuration**: Environment variables (`APP_PORT`, `DB_URL`, `HARDWARE_MODE`, `ESP32_SERIAL_PORT`, `ESP32_SERIAL_BAUD`, `USER_TZ_OFFSET`) and `config.yaml`, with runtime device configuration persisted in database.
- **Platform-Agnostic GPIO**: USB-to-GPIO adapter support (ESP32, Raspberry Pi) for PC-style boards (Linux/Windows compatible), abstracting hardware control from specific board requirements.
- **Deployment**: Designed for Replit's autoscale deployment, emphasizing statelessness and environment-based configuration.

## External Dependencies
- **FastAPI**: Web framework.
- **Uvicorn**: ASGI server.
- **SQLModel**: ORM for SQLite.
- **APScheduler**: Python library for scheduling tasks.
- **PyYAML**: For parsing YAML configuration files.
- **PySerial**: Serial communication library for ESP32 USB adapter.
- **PCA9685 PWM Controller**: Hardware for pump control (I2C).
- **INA219 Power Sensors**: Hardware for monitoring current/voltage (I2C).