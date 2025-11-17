# Reef Controller

**Current Version: v1.5.0**

## Version History
- **v1.5.0** (Nov 17, 2025): Created dedicated full-screen Schedule Calendar modal (95vw×90vh) accessible via new "Schedule Calendar" button, featuring weekly grid display (24 hours x 7 days) with visual task placement, clickable cells to create tasks with pre-filled time/day, and clickable task badges to edit existing tasks - calendar opens/closes independently while scheduler modal remains simple list-based editor
- **v1.4.0** (Nov 17, 2025): Added calendar view to scheduler modal with weekly grid display (24 hours x 7 days), visual task placement at scheduled times, clickable cells to create new tasks with pre-filled time/day, and clickable task badges to edit existing tasks using proper selectTaskForEditing() integration
- **v1.3.1** (Nov 17, 2025): UX polish - implemented toast notification system to replace iframe-blocking alert() calls with non-blocking success/error/info toasts, updated Feed Mode button to toggle functionality (click to start, click again to cancel), removed button hover bounce effects for cleaner interaction
- **v1.3.0** (Nov 17, 2025): Added feed mode system with manual button that pauses all wavemakers for 10 minutes and automatically restores previous preset, built complete scheduler UI modal for creating/editing/deleting scheduled preset activations with time picker and day-of-week filtering, integrated feed mode with scheduler (pauses scheduled changes during feeding), improved feed mode robustness with name-based preset lookup and proper HTTP error handling
- **v1.2.3** (Nov 17, 2025): UX improvements - changed wavemaker channel display from 0-5 to user-friendly 1-6 numbering, added individual "Clear" buttons to each wavemaker curve editor for resetting curves without deleting presets
- **v1.2.2** (Nov 17, 2025): Enhanced preset selector stability with comprehensive hash-based change detection (ID, name, description) and fixed flow pattern canvas updates to refresh on every polling cycle
- **v1.2.1** (Nov 17, 2025): UI polish - fixed Canvas keyframe editor coordinate mapping for accurate mouse interaction, removed individual wavemaker controls and added visual flow pattern displays, fixed preset selector jumping on refresh
- **v1.2.0** (Nov 17, 2025): Added graphical preset editor with Canvas-based curve design, interactive keyframe editing, and automated scheduler for time-based preset switching
- **v1.1.0** (Nov 17, 2025): Added preset-based wavemaker control system with 6 built-in flow patterns, interpolated power curves, REST API, and frontend preset selector
- **v1.0.0**: Initial release with LED control, battery management, individual wavemaker control, and power allocation

## Overview
Reef Controller is a sophisticated web-based application built with FastAPI, designed for real-time monitoring and control of reef aquarium equipment. Its primary purpose is to manage LED lighting arrays, battery backup systems, and wave pumps through an intuitive web interface. The project aims to provide comprehensive control over an aquarium environment, featuring real-time telemetry, interactive controls, and intelligent power management capabilities. Key ambitions include offering production-ready wave pump control with various patterns, granular per-LED control with intelligent power shedding, and a touch-optimized user interface for easy interaction.

## User Preferences
None specified yet.

## System Architecture
The Reef Controller is built upon a FastAPI backend and a vanilla JavaScript frontend, emphasizing a touch-optimized user experience.

### UI/UX Decisions
- **Touch-Optimized Interface**: Designed for 1920x1080 displays with large touch targets (minimum 48x48px) and a "weather-app" styling featuring ocean gradient backgrounds and clean card layouts.
- **Real-time Updates**: The UI polls the backend every 2 seconds to ensure synchronized display of telemetry and control states.
- **Interactive Modals**: Settings and history are managed through full-screen modal dialogs, including drag-to-reorder priority lists.
- **Visual Feedback**: Disabled LEDs are visually represented as off (gray), and array cards display configured intensity limits.
- **Chart Modals**: History and power charts utilize 90% viewport width for maximum data visibility.
- **Preset Editor**: Full-screen modal with sidebar preset list, Canvas-based graphical curve editor for all 6 wavemakers, and interactive keyframe manipulation (click to add, drag to move, Shift+click to delete).
- **Scheduler Calendar View**: Toggle between list and calendar views in scheduler modal. Calendar displays weekly grid (24 hours x 7 days) with scheduled tasks visually placed at their times. Click calendar cells to create new tasks with pre-filled time/day. Click task badges to edit. Disabled tasks shown in gray.
- **Toast Notifications**: Non-blocking notification system replaces all alert() calls to prevent iframe blocking, with success (green), error (red), and info (blue) variants that auto-dismiss after 3 seconds.
- **Clean Interactions**: Removed button hover bounce effects for smoother, more professional feel. Feed Mode button toggles between start/cancel states with clear visual feedback.

### Technical Implementations
- **Backend (FastAPI)**:
    - **Services**: `StageManager` (LEDs, battery), `PowerAllocator` (load shedding), `EventsService` (event logging), `AutomationService` (scheduling, wave modes), `SystemHealthService`, `JobScheduler` (1Hz telemetry/power allocation), `Store` (SQLite persistence).
    - **API Endpoints**: Comprehensive RESTful API for controlling arrays, managing wavemakers, retrieving system telemetry, events, and historical data. Supports partial updates for flexible control.
    - **Wavemaker Control**: Implements 6 independent channels with various patterns (Off, Constant, Pulse, Gyre Left/Right, Random Reef), a 20Hz control loop for smooth operation, and a 1Hz telemetry loop.
    - **LED Control**: Individual LED enable/disable, array-level enable/disable, and proportional scaling of LEDs based on intensity limits.
    - **Intelligent Power Management**: Priority-based power shedding with hysteresis, running every second to respond to power budget changes.
- **Frontend (Vanilla JavaScript)**:
    - No external frameworks are used.
    - Utilizes HTML5 Canvas for sparkline rendering and visual flow pattern displays.
    - Canvas coordinate mapping uses `getBoundingClientRect()` for accurate mouse interaction in scaled layouts.
    - Implements local state persistence for sliders and toggles (e.g., 5-second timeout for intensity sliders) to maintain user input during UI refreshes.
    - Smart preset selector updates only when state actually changes to prevent visual jumping.

### Feature Specifications
- **Wavemaker Preset System**: Coordinated flow pattern control across all 6 wavemakers using preset-based management. Features 6 built-in presets (Gentle Flow, Pulse, Gyre Clockwise/Counter-Clockwise, Feed Mode, Random Reef) with custom flow curves per wavemaker. PresetManager interpolates power values from keyframe-based curves every 20Hz for smooth transitions. REST API supports preset CRUD operations, activation, and real-time status. Frontend includes preset selector dropdown, graphical curve editor with Canvas-based interactive keyframe editing (click to add, drag to move, Shift+click to delete), and automated scheduler for time-based preset switching.
- **Feed Mode**: Manual feeding assistance with one-button activation that pauses all wavemakers for 10 minutes using built-in "Feed Mode" preset, then automatically restores the previous preset. Features real-time countdown display, feed mode status indicator, and integration with scheduler (pauses scheduled changes during feeding). Backend uses name-based preset lookup for robustness, proper HTTP error handling, and 1-second timeout checking via JobScheduler. API endpoints: POST /api/feed/start, GET /api/feed/status, POST /api/feed/stop.
- **Automation Scheduler UI**: Full-screen modal interface for managing scheduled preset activations. Features sidebar showing all scheduled tasks with enabled/disabled badges, form editor with time picker (24-hour format), preset selector, day-of-week filtering (optional), and enabled toggle. Complete CRUD operations with create/edit/delete functionality, coordinated with feed mode to pause automated changes during feeding. Integrated with existing scheduler backend (/api/automation/scheduled endpoints).
- **Automation Scheduler Backend**: Time-based preset activation system with minute-precision execution. Supports scheduled tasks with optional day-of-week filtering, database persistence (ScheduledTaskRow), and automatic execution via JobScheduler. REST API provides CRUD operations for scheduled tasks (/api/automation/scheduled) and upcoming task queries. Integrated with PresetManager for seamless automated preset switching throughout the day.
- **Wavemaker Subsystem**: Supports 6 independent channels with patterns like Off, Constant, Pulse (configurable duty ratio and intensity), Gyre Left/Right (synchronized sinusoidal waves), and Random Reef (smooth random transitions). Includes API endpoints for status, control, and 15-minute history.
- **LED Control**: Granular control over 3 arrays, each with 6 individual LEDs. Each LED has configurable name, intensity limit, and priority. Real-time telemetry for each LED.
- **Intelligent Power Management**: Automatically sheds lowest-priority loads when the power budget is exceeded, with hysteresis for stable operation. Tracks all shedding/restoration events.
- **System Monitoring**: Real-time display of PV input, battery flow, and net power with color-coded indicators.
- **Simulation Mode**: Comprehensive software simulation for development and testing, including diurnal PV curves, per-LED load calculation, battery flow simulation, and configurable power budgets.

### System Design Choices
- **Hardware Abstraction Layer (HAL)**: Unifies control for both simulated and real Raspberry Pi hardware (PCA9685 PWM, INA219 sensors) via a `HARDWARE_MODE` environment variable.
- **Database**: SQLite for telemetry and event persistence.
- **Configuration**: Environment variables (`APP_PORT`, `DB_URL`, `SENSOR_DRIVER`, `GPIO_DRIVER`) and `config.yaml` for detailed settings.
- **Deployment**: Designed for Replit's autoscale deployment, emphasizing statelessness and environment-based configuration.

## External Dependencies
- **FastAPI**: Web framework for building APIs.
- **Uvicorn**: ASGI server for running the FastAPI application.
- **SQLModel**: ORM for interacting with the SQLite database.
- **APScheduler**: Python library for scheduling periodic tasks.
- **PyYAML**: For parsing YAML configuration files.
- **PCA9685 PWM Controller**: Hardware for precise pump control (I2C address 0x40, 1000Hz PWM frequency, 12-bit resolution).
- **INA219 Power Sensors**: Hardware for monitoring current/voltage (I2C addresses 0x40-0x45, 0-26V, 0-3.2A).