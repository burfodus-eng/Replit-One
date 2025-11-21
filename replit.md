# Reef Controller

## Overview
Reef Controller is a sophisticated web-based application built with FastAPI, designed for real-time monitoring and control of reef aquarium equipment. Its primary purpose is to manage LED lighting arrays, battery backup systems, and wave pumps through an intuitive web interface. The project aims to provide comprehensive control over an aquarium environment, featuring real-time telemetry, interactive controls, and intelligent power management capabilities. Key ambitions include offering production-ready wave pump control with various patterns, granular per-LED control with intelligent power shedding, and a touch-optimized user interface for easy interaction.

## User Preferences
None specified yet.

## System Architecture
The Reef Controller is built upon a FastAPI backend and a vanilla JavaScript frontend, emphasizing a touch-optimized user experience.

### UI/UX Decisions
- **Touch-Optimized Interface**: Designed for 1920x1080 displays with large touch targets and "weather-app" styling with ocean gradient backgrounds and clean card layouts.
- **Real-time Updates**: UI polls backend every 2 seconds for synchronized telemetry and control states.
- **Interactive Modals**: Full-screen modals for settings, history, and a dedicated Schedule Calendar (95vw×90vh) with weekly grid display.
- **Visual Feedback**: Disabled LEDs are gray, array cards show intensity limits, and disabled scheduled tasks are grayed out.
- **Chart Modals**: History and power charts use 90% viewport width.
- **Preset Editor**: Full-screen modal with sidebar, Canvas-based graphical curve editor for 6 wavemakers, and interactive keyframe manipulation.
- **Scheduler Calendar View**: Weekly grid (24 hours x 7 days) with visual task placement, clickable cells for new tasks, and clickable task badges for editing.
- **Toast Notifications**: Non-blocking success/error/info toasts replace `alert()` calls.
- **Clean Interactions**: Removed button hover bounce effects. Feed Mode button toggles states.

### Technical Implementations
- **Backend (FastAPI)**:
    - **Services**: `StageManager`, `PowerAllocator`, `EventsService`, `AutomationService`, `SystemHealthService`, `JobScheduler`, `Store` (SQLite persistence).
    - **API Endpoints**: Comprehensive RESTful API for controlling arrays, wavemakers, telemetry, events, and historical data, supporting partial updates.
    - **Wavemaker Control**: 6 independent channels with various patterns, 20Hz control loop, 1Hz telemetry loop.
    - **LED Control**: Individual and array-level enable/disable, proportional scaling based on intensity limits.
    - **Intelligent Power Management**: Priority-based power shedding with hysteresis, running every second.
    - **Timezone Support**: Frontend detects browser timezone, backend uses `USER_TZ_OFFSET` for scheduler and ETA calculations.
- **Frontend (Vanilla JavaScript)**:
    - No external frameworks.
    - Uses HTML5 Canvas for sparklines and visual flow pattern displays, with `getBoundingClientRect()` for accurate mouse interaction.
    - Implements local state persistence for sliders/toggles.
    - Smart preset selector updates only on state changes to prevent visual jumping.

### Feature Specifications
- **Wavemaker Preset System**: Coordinated flow control across 6 wavemakers using presets (Gentle Flow, Pulse, Gyre, Feed Mode, Random Reef) with custom flow curves. Features a graphical Canvas-based editor with interactive keyframe editing and automated scheduler integration.
- **Feed Mode**: Manual button activation pauses all wavemakers for 10 minutes using a dedicated "Feed Mode" preset, then automatically restores the previous preset. Includes real-time countdown and scheduler integration.
- **Automation Scheduler UI**: Full-screen modal for managing scheduled preset activations with sidebar task list, form editor (time picker, preset selector, day-of-week filtering, enabled toggle), and full CRUD operations.
- **Automation Scheduler Backend**: Fully automated 24/7 preset activation system with 30-second precision, ±30 second time window matching, and automatic startup resume (up to 7 days backward search). Supports day-of-week filtering and timezone-aware execution.
- **Wavemaker Subsystem**: Supports 6 independent channels with patterns (Off, Constant, Pulse, Gyre Left/Right, Random Reef), API for status, control, and 15-minute history.
- **LED Control**: Granular control over 3 arrays, each with 6 individual LEDs, configurable name, intensity limit, and priority.
- **Intelligent Power Management**: Automatic shedding of lowest-priority loads when power budget is exceeded, with hysteresis.
- **System Monitoring**: Real-time display of PV input, battery flow, and net power.
- **Simulation Mode**: Comprehensive software simulation for development, including diurnal PV curves, LED load calculation, battery flow, and configurable power budgets.

### System Design Choices
- **Hardware Abstraction Layer (HAL)**: Unifies control for simulated and real Raspberry Pi hardware (PCA9685 PWM, INA219 sensors) via `HARDWARE_MODE`.
- **Database**: SQLite for telemetry and event persistence.
- **Configuration**: Environment variables (`APP_PORT`, `DB_URL`, `SENSOR_DRIVER`, `GPIO_DRIVER`) and `config.yaml`.
- **Deployment**: Designed for Replit's autoscale deployment, emphasizing statelessness and environment-based configuration.

## External Dependencies
- **FastAPI**: Web framework.
- **Uvicorn**: ASGI server.
- **SQLModel**: ORM for SQLite.
- **APScheduler**: Python library for scheduling tasks.
- **PyYAML**: For parsing YAML configuration files.
- **PCA9685 PWM Controller**: Hardware for pump control (I2C).
- **INA219 Power Sensors**: Hardware for monitoring current/voltage (I2C).