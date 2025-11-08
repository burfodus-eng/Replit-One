# Reef Controller - Professional Aquarium Automation System

A sophisticated touch-enabled web application for controlling and monitoring reef aquarium equipment with intelligent power management and beautiful visualizations.

## 🌊 Features

### Per-LED Array Control
- **3 LED Arrays**: Acropora (SPS), LPS, and Center Lights
- **6 Individual LEDs per array** with configurable:
  - Display names
  - Intensity limits (0-100%)
  - Priority levels for power shedding
- Real-time intensity sliders with live telemetry feedback

### Intelligent Power Management
- **Automatic LED Shedding**: When power budget is exceeded, LEDs are automatically disabled in priority order (lowest priority first)
- **Hysteresis-Controlled Restoration**: LEDs restore when surplus power is available for a sustained period (configurable delay)
- **Event Logging**: All shedding and restoration events are tracked and displayed
- **Configurable Budget**: Set target watts and restoration parameters in config.yaml

### Touch-Optimized UI (1920×1080)
- **Weather-App Aesthetic**: Soft gradients, frosted glass cards, professional spacing
- **Touch Targets**: All interactive elements ≥48×48px (primary buttons ≥56×56px)
- **Responsive Layout**: Header with live clock, 3-column array grid, right sidebar
- **Real-Time Updates**: All data refreshes every 2 seconds

### System Monitoring
- **Live Telemetry**: Voltage, current, and power for each array
- **System Load Dashboard**: PV input, total load, battery flow, power budget
- **System Health**: Color-coded status (green/yellow/red) with detailed alerts
- **Event Feed**: Recent shed/restore/warning/alert events
- **Task Scheduling**: View completed and upcoming automation tasks

### Data Visualization
- **Sparklines**: Mini power graphs on each array card (last 15 minutes)
- **History Charts**: Click any array to view detailed voltage/current/power history
- **Load Sparkline**: System-wide PV input visualization

## 🚀 Quick Start

### Running Locally
```bash
# Install dependencies (automatic on Replit)
# Start the server
python -m uvicorn app.main:app --host 0.0.0.0 --port 5000
```

Visit `http://localhost:5000` in your browser (optimized for 1920×1080 displays).

### Configuration

Edit `config.yaml` to customize:

```yaml
stages:
  arrays:
    - id: "A1"
      name: "Acropora (SPS) Lights"
      max_current_a: 4.0
      nominal_voltage_v: 36.0
      leds:
        - id: "L1"
          label: "Front Blue"
          intensity_limit_pct: 100
          priority: 1  # Highest priority (shed last)

power_budget:
  target_watts: 400          # Maximum allowed system load
  restore_hysteresis_pct: 10 # Require 10% surplus before restore
  restore_delay_s: 10        # Wait 10s with surplus before restore
```

## 🧪 Testing Power Shedding

### Method 1: Lower the Power Budget
1. Edit `config.yaml` and set `power_budget.target_watts: 50`
2. Restart the application
3. Set all arrays to 100% intensity
4. Watch LEDs shed automatically in priority order
5. Lower array intensity to create surplus
6. Watch LEDs restore after 10 seconds

### Method 2: Simulate Low PV Input
The PV simulator uses time-of-day to generate realistic solar curves:
- **6 AM - 8 AM**: Sunrise (0% → 100%)
- **8 AM - 6 PM**: Full sun (100% with cloud variation ±30%)
- **6 PM - 8 PM**: Sunset (100% → 0%)
- **8 PM - 6 AM**: Night (0%)

Run the app during simulated "night" hours or modify the simulator's time calculation.

### Method 3: Manual API Testing
```bash
# Get current system load
curl http://localhost:5000/api/system/load

# Set all arrays to maximum
curl -X POST http://localhost:5000/api/control \
  -H "Content-Type: application/json" \
  -d '{"stage_id": "A1", "mode": "MANUAL", "duty": 1.0}'

# Watch events feed
curl http://localhost:5000/api/events?limit=20
```

## 📱 Using the Touch Interface

### Main Controls
- **Array Intensity Sliders**: Drag to adjust 0-100% duty cycle
- **Settings Button** (⚙): Click to modify LED names, limits, and priorities
- **Array Cards**: Click to view detailed power history charts

### LED Indicators
Each LED shows:
- **Status Dot**: Green (on) or gray (off)
- **Current Intensity**: Actual output percentage
- **Priority Number**: P1-P6 (P1 = highest priority, sheds last)

### Settings Modal
- Edit LED display names
- Adjust intensity limits (0-100%)
- Priority is shown but reordering not yet implemented

### System Monitoring
- **System Load**: Real-time PV, load, battery, and budget
- **Upcoming Tasks**: Next scheduled automation events
- **Completed Tasks**: Recent task history
- **Recent Events**: Shed/restore/alert timeline

## 🏗️ Architecture

### Backend (FastAPI)
```
app/
├── main.py                    # Application entry point
├── config.py                  # Configuration loader
├── models.py                  # Pydantic data models
├── drivers/
│   └── sensors_sim.py         # Simulated sensors (PV diurnal curve)
├── services/
│   ├── stage_manager.py       # LED array lifecycle
│   ├── power_allocator.py     # Shedding/restoration logic
│   ├── events.py              # Event tracking
│   ├── automation.py          # Task scheduling
│   ├── system_health.py       # Health monitoring
│   ├── scheduler.py           # Periodic jobs
│   └── storage.py             # SQLite persistence
├── routers/
│   ├── arrays.py              # New LED array endpoints
│   ├── automation.py          # Tasks and wave modes
│   ├── control.py             # Manual control
│   ├── config_api.py          # Status and snapshot
│   └── telemetry.py           # Health check
└── stages/
    ├── led_stage.py           # LED array implementation
    └── battery_stage.py       # Battery management
```

### Key Services

#### Power Allocator
Implements intelligent load management:
- Calculates total load from all arrays
- Sheds LEDs when load > available power
- Restores LEDs with hysteresis and delay
- Logs all events for auditing

#### Events Service
Tracks system events in memory:
- Shed/restore operations
- System warnings and alerts
- Ring buffer (200 events max)
- Queryable via API

#### PV Simulator
Realistic solar panel behavior:
- Diurnal curve (sunrise/sunset)
- Cloud variation (±30%)
- Time-of-day dependent output
- Deterministic mode for testing

### API Endpoints

#### Array Management
- `GET /api/arrays` - List all arrays with LED status
- `POST /api/arrays/{id}/settings` - Update LED configuration
- `GET /api/history/array/{id}?range_hours=1` - Array power history

#### System Monitoring
- `GET /api/system/load` - PV, load, battery, budget
- `GET /api/system/health` - System status and alerts
- `GET /api/events?limit=50` - Recent events

#### Legacy Endpoints (Maintained)
- `GET /api/status` - Stage status
- `GET /api/snapshot` - Latest telemetry
- `POST /api/control` - Manual control
- `GET /api/automation/*` - Tasks and wave modes

## 🔧 Simulation Mode

All features work in simulation mode without hardware:

### Simulated Behavior
- **PV Output**: 0-600W based on time of day
- **Array Current**: Scales with duty cycle (0-100% = 0-max_current_a)
- **Voltage Droop**: Up to 8% drop at full load
- **LED Intensity**: Respects individual LED limits
- **Power Shedding**: Realistic budget enforcement

### Deterministic Testing
Set `simulator.deterministic_seed` in config.yaml for repeatable tests.

## 🎨 Design Philosophy

### Touch-First
- All controls sized for finger interaction
- Generous spacing (8-12px gaps)
- Large touch targets (48×48px minimum)
- Immediate visual feedback

### Weather-App Aesthetic
- Soft gradient background
- Frosted glass cards with subtle shadows
- Rounded corners (16-20px)
- Professional color palette
- Minimal, clean typography

### Performance
- Vanilla JavaScript (no frameworks)
- Efficient 2-second polling
- Lightweight assets
- Single-page application

## 📊 Configuration Reference

### Array Settings
```yaml
stages:
  arrays:
    - id: "A1"              # Unique identifier
      name: "Display Name"  # Shown in UI
      description: "Info"   # Card subtitle
      max_current_a: 4.0    # Maximum current draw
      nominal_voltage_v: 36 # Nominal output voltage
      leds: [...]           # 6 LED configurations
```

### LED Configuration
```yaml
leds:
  - id: "L1"                    # L1-L6
    label: "Front Blue"         # Display name
    intensity_limit_pct: 100    # 0-100% cap
    priority: 1                 # 1-6 (1=highest)
```

### Power Budget
```yaml
power_budget:
  target_watts: 400              # Maximum system load
  restore_hysteresis_pct: 10     # Surplus margin for restore
  restore_delay_s: 10            # Delay before restore
  pv_max_w: 600                  # Simulator PV capacity
```

## 🚢 Deployment

Configured for Replit autoscale deployment:
- Stateless design
- SQLite persistence
- Environment-based config
- Port 5000 public access

Click **Deploy** in Replit to publish!

## 📝 Future Enhancements

- [ ] Drag-to-reorder LED priorities in settings
- [ ] Real hardware integration (INA219, GPIO)
- [ ] User authentication
- [ ] Multi-tank support
- [ ] Mobile responsive design
- [ ] Advanced scheduling (sunrise/sunset sync)
- [ ] Historical data export
- [ ] Custom alert webhooks

## 🤝 Contributing

This is a demonstration project. For production use, consider:
- Adding authentication/authorization
- Implementing database migrations
- Adding comprehensive testing
- Hardware safety interlocks
- Backup power monitoring

## 📄 License

MIT License - Free for personal and commercial use.

---

**Built with ❤️ for reef aquarium hobbyists**
