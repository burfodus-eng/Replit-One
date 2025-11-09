# Reef Controller

A sophisticated web-based reef aquarium controller with real-time monitoring and control capabilities.

## Overview

Reef Controller is a FastAPI-based application designed to monitor and control reef aquarium equipment including LED lighting arrays, battery backup systems, and wave pumps. The application features a beautiful web interface with real-time telemetry updates and interactive controls.

## Recent Changes

### November 9, 2025: LED Control Enhancements

#### Individual LED Enable/Disable Controls
- **Per-LED toggles in settings modal**: Each LED can now be individually enabled or disabled
- **Visual feedback**: Disabled LEDs show as off (gray) on array cards
- **Settings persist during session**: LED enable/disable state maintained until server restart

#### Array-Level Enable/Disable
- **Quick array control**: Toggle switch added to array card header for fast enable/disable
- **Master control**: Entire array can be turned on/off without adjusting individual LEDs

#### Corrected LED Display
- **Fixed percentage display**: Array cards now show configured intensity limits (intensity_limit_pct) instead of current scaled values
- **Master slider behavior**: Duty slider correctly scales all enabled LEDs proportionally based on their individual limits
- **Clear settings**: LED percentages in settings modal match what's displayed on cards

#### Wide Chart Modals (16:10 Display Optimization)
- **90% viewport width**: History and power charts now use 90vw for maximum data visibility
- **Canvas expansion**: Chart canvases fill the modal width (1664px on 1920×1200 displays)
- **Compact layout**: Tightened spacing throughout to fit 1920×1200 without scrolling
- **6-item telemetry grid**: 2×3 layout showing Input V/I, Output V/I, Power, and Mode

#### Control Persistence Improvements
- **Extended slider local state**: Intensity slider now holds value for 5 seconds (up from 2s) to survive multiple page refresh cycles
- **Array toggle local state**: Added localToggleState tracking so array enable/disable doesn't reset during refreshes
- **Consistent UX**: Both slider and toggle maintain user input through background polling without flickering

#### Technical Updates
- Added `is_on` field to LEDSettingsUpdate model
- Updated /arrays/{id}/settings endpoint to handle LED enable/disable state
- Added toggle switch CSS components
- LED settings modal expanded to 4-column grid (ID, Label, Limit%, Toggle)
- Implemented local state persistence with 5-second timeout for slider and toggle controls

**Known Limitation**: LED is_on state does not persist across server restarts (stored in memory only). Settings must be reapplied after restart. Future enhancement will add config file or database persistence.

### November 8, 2025: Professional Touch-Enabled Interface with Intelligent Power Management

#### Per-LED Granular Control
- **3 Renamed Arrays**: Acropora SPS Lights (A1), LPS Lights (A2), Center Lights (A3)
- **6 Individual LEDs per array**: Each LED has configurable name, intensity limit (0-100%), and priority (1-18)
- **Real-time LED telemetry**: Voltage, current, power, and state tracking for each LED
- **Interactive settings modals**: Touch-optimized dialogs for configuring LED parameters and reordering priorities

#### Intelligent Power Management
- **Priority-based power shedding**: Automatically reduces load by turning off lowest-priority LEDs when power budget is exceeded
- **Hysteresis-controlled restoration**: 20% headroom band prevents LED flapping during marginal power conditions
- **Real-time power allocation**: Runs every second, responding to PV generation and battery availability
- **Event tracking**: Complete audit log of all shed/restore/alert events with timestamps

#### Touch-Optimized UI (1920×1080)
- **Weather-app styling**: Ocean gradient backgrounds, clean card layout, professional spacing
- **Large touch targets**: All interactive elements sized for finger input (48×48px minimum)
- **Array cards**: Individual cards for each LED array showing status, power, and per-LED controls
- **System monitoring**: Real-time PV input, battery flow, and net power display with color-coded indicators
- **Sparkline graphs**: Miniature trend visualizations on array cards
- **Event feed**: Live display of recent shed/restore events
- **Responsive modals**: Full-screen settings dialogs with drag-to-reorder priority lists

#### Enhanced Simulation
- **Diurnal PV curve**: Realistic solar power generation following time-of-day (0W at night, peak at solar noon)
- **Per-LED load calculation**: Accurate power consumption based on individual LED states
- **Battery flow simulation**: Realistic charge/discharge behavior with voltage sag under load
- **Configurable power budget**: Easy testing of deficit scenarios by adjusting target_watts in config

### Architecture

#### Backend (FastAPI)
- **Services**:
  - `StageManager`: Manages LED arrays and battery stages with per-LED state tracking
  - `PowerAllocator`: Intelligent load shedding and restoration with hysteresis logic
  - `EventsService`: Tracks and persists shed/restore/alert events
  - `AutomationService`: Handles task scheduling and wave modes
  - `SystemHealthService`: Monitors system health and generates alerts
  - `JobScheduler`: Runs periodic telemetry sampling and power allocation (1Hz)
  - `Store`: Persists telemetry and events to SQLite database

- **API Endpoints**:
  - `/api/arrays` - Array status with per-LED telemetry
  - `/api/arrays/{id}/settings` - Update array/LED configuration
  - `/api/system/load` - Current PV, battery, and net power
  - `/api/events` - Recent shed/restore/alert events
  - `/api/history/array/{id}` - Historical telemetry for sparklines
  - `/api/automation/tasks/*` - Task management
  - `/api/automation/wave-modes` - Wave pump patterns
  - `/api/system/health` - System health status

#### Frontend
- Vanilla JavaScript (no frameworks)
- Touch-optimized for 14" FHD displays (1920×1080)
- Real-time updates via polling (2s intervals)
- Modal dialogs for settings and history
- Sparkline rendering with HTML5 Canvas
- Drag-to-reorder priority lists

#### Simulation
Realistic sensor simulation with:
- Diurnal PV power curve (time-of-day based generation)
- Per-LED current/voltage/power calculation
- Battery voltage sag under discharge
- Configurable array limits and priorities
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
