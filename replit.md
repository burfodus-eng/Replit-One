# Reef Controller

**Current Version: v1.1.0**

## Version History
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

### Technical Implementations
- **Backend (FastAPI)**:
    - **Services**: `StageManager` (LEDs, battery), `PowerAllocator` (load shedding), `EventsService` (event logging), `AutomationService` (scheduling, wave modes), `SystemHealthService`, `JobScheduler` (1Hz telemetry/power allocation), `Store` (SQLite persistence).
    - **API Endpoints**: Comprehensive RESTful API for controlling arrays, managing wavemakers, retrieving system telemetry, events, and historical data. Supports partial updates for flexible control.
    - **Wavemaker Control**: Implements 6 independent channels with various patterns (Off, Constant, Pulse, Gyre Left/Right, Random Reef), a 20Hz control loop for smooth operation, and a 1Hz telemetry loop.
    - **LED Control**: Individual LED enable/disable, array-level enable/disable, and proportional scaling of LEDs based on intensity limits.
    - **Intelligent Power Management**: Priority-based power shedding with hysteresis, running every second to respond to power budget changes.
- **Frontend (Vanilla JavaScript)**:
    - No external frameworks are used.
    - Utilizes HTML5 Canvas for sparkline rendering.
    - Implements local state persistence for sliders and toggles (e.g., 5-second timeout for intensity sliders) to maintain user input during UI refreshes.

### Feature Specifications
- **Wavemaker Preset System**: Coordinated flow pattern control across all 6 wavemakers using preset-based management. Features 6 built-in presets (Gentle Flow, Pulse, Gyre Clockwise/Counter-Clockwise, Feed Mode, Random Reef) with custom flow curves per wavemaker. PresetManager interpolates power values from keyframe-based curves every 20Hz for smooth transitions. REST API supports preset CRUD operations, activation, and real-time status. Frontend includes preset selector dropdown and design interface.
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