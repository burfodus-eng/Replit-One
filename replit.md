# Reef Controller

A sophisticated web-based reef aquarium controller with real-time monitoring and control capabilities.

## Overview

Reef Controller is a FastAPI-based application designed to monitor and control reef aquarium equipment including LED lighting arrays, battery backup systems, and wave pumps. The application features a beautiful web interface with real-time telemetry updates and interactive controls.

## Recent Changes (November 8, 2025)

### Enhanced UI and Features
- **Beautiful Ocean-Themed Design**: Gradient backgrounds, professional spacing, and clean card layout
- **Live Time Display**: Real-time clock showing current date and time
- **Interactive LED Control**: Sliders for controlling light intensity (0-100%) with live updates
- **Dynamic Sensor Simulation**: Realistic voltage and current readings that respond to duty cycle changes
- **Automation Dashboard**: Displays completed and upcoming tasks
- **Wave Mode Control**: Dropdown selector for various pump patterns (Reef Pulse, Left Swirl, etc.)
- **System Health Monitoring**: Color-coded health card showing warnings and errors

### Architecture

#### Backend (FastAPI)
- **Services**:
  - `StageManager`: Manages LED arrays and battery stages
  - `AutomationService`: Handles task scheduling and wave modes
  - `SystemHealthService`: Monitors system health and generates alerts
  - `JobScheduler`: Runs periodic telemetry sampling
  - `Store`: Persists telemetry data to SQLite database

- **API Endpoints**:
  - `/api/status` - Current stage status
  - `/api/snapshot` - Latest telemetry readings
  - `/api/control` - Update stage settings (mode, duty, enable)
  - `/api/automation/tasks/*` - Completed and upcoming tasks
  - `/api/automation/wave-modes` - Get/set wave modes
  - `/api/system/health` - System health status

#### Frontend
- Vanilla JavaScript (no frameworks)
- Real-time updates via polling
- Interactive sliders with immediate visual feedback
- Responsive grid layout

#### Simulation
All sensors use simulated data with realistic behavior:
- Current scales 0-2A based on duty cycle (0-100%)
- Voltage drops up to 10% under full load
- 90% efficiency factor for current conversion
- Random variations for realism

## Project Structure

```
app/
├── config.py              # Configuration and environment variables
├── main.py                # FastAPI application and startup
├── models.py              # Pydantic models
├── drivers/               # Hardware simulation drivers
│   └── sensors_sim.py     # Simulated sensor readings
├── routers/               # API route handlers
│   ├── automation.py      # Automation and wave mode endpoints
│   ├── config_api.py      # Status and snapshot endpoints
│   ├── control.py         # Control endpoint
│   └── telemetry.py       # Health check
├── services/              # Business logic
│   ├── automation.py      # Task and wave mode management
│   ├── scheduler.py       # Periodic job scheduling
│   ├── stage_manager.py   # Stage lifecycle management
│   ├── storage.py         # Database persistence
│   └── system_health.py   # Health monitoring
├── stages/                # Stage implementations
│   ├── base.py            # Base stage class
│   ├── battery_stage.py   # Battery management
│   └── led_stage.py       # LED array control
└── web/                   # Frontend
    └── index.html         # Single-page application
```

## Configuration

### Environment Variables
- `APP_PORT`: Server port (default: 5000)
- `DB_URL`: Database connection string (default: sqlite:///./reef.db)
- `SENSOR_DRIVER`: Sensor implementation (default: sensors_sim)
- `GPIO_DRIVER`: GPIO implementation (default: gpio)

### config.yaml
Defines LED array timers, battery settings, telemetry intervals, and alert thresholds.

## Development

The application runs in simulation mode by default, making it perfect for development and testing without hardware.

### Running Locally
```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 5000
```

### Dependencies
- FastAPI: Web framework
- Uvicorn: ASGI server
- SQLModel: Database ORM
- APScheduler: Job scheduling
- PyYAML: Configuration parsing

## Deployment

Configured for Replit's autoscale deployment:
- Stateless design suitable for automatic scaling
- SQLite database for telemetry storage
- Environment-based configuration
- Port 5000 for public access

## User Preferences

None specified yet.

## Future Enhancements

- Hardware integration (INA219 sensors, GPIO control)
- User authentication
- Historical data visualization
- Mobile app
- Advanced scheduling with sunrise/sunset timing
- Multi-tank support
