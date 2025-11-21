import os
import logging
from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from .config import CONFIG, DB_URL, APP_PORT
from .services.stage_manager import StageManager
from .services.scheduler import JobScheduler
from .services.storage import make_db, Store
from .services.automation import AutomationService
from .services.system_health import SystemHealthService
from .services.events import EventsService
from .services.power_allocator import PowerAllocator
from .services.wavemaker_manager import WavemakerManager
from .services.preset_manager import PresetManager
from .routers import telemetry, control, config_api, automation, arrays, history, wavemakers, presets, hardware

logger = logging.getLogger("uvicorn.error")


app = FastAPI(title=CONFIG['site']['name'])
app.mount('/ui', StaticFiles(directory='app/web', html=True), name='ui')


@app.get('/')
async def root():
    return FileResponse(
        'app/web/index.html',
        headers={
            'Cache-Control': 'no-cache, no-store, must-revalidate',
            'Pragma': 'no-cache',
            'Expires': '0'
        }
    )


app.include_router(telemetry.router, prefix='/api')
app.include_router(control.router, prefix='/api')
app.include_router(config_api.router, prefix='/api')
app.include_router(automation.router, prefix='/api')
app.include_router(arrays.router, prefix='/api')
app.include_router(history.router)
app.include_router(wavemakers.router, prefix='/api')
app.include_router(presets.router, prefix='/api')
app.include_router(hardware.router, prefix='/api')


@app.on_event('startup')
async def startup():
    try:
        logger.info("Starting Reef Controller initialization...")
        
        db_path = DB_URL.replace('sqlite:///', '')
        db_dir = os.path.dirname(db_path)
        if db_dir and not os.path.exists(db_dir):
            logger.info(f"Creating database directory: {db_dir}")
            Path(db_dir).mkdir(parents=True, exist_ok=True)
        
        logger.info("Loading configuration...")
        app.state.config = CONFIG
        
        logger.info("Initializing stage manager...")
        app.state.stage_manager = StageManager(CONFIG)
        app.state.mgr = app.state.stage_manager
        
        logger.info("Initializing system health service...")
        app.state.health = SystemHealthService()
        
        logger.info("Initializing events service...")
        app.state.events = EventsService(max_events=200)
        
        logger.info("Initializing power allocator...")
        app.state.power_allocator = PowerAllocator(CONFIG, app.state.events)
        
        logger.info("Initializing wavemaker manager...")
        app.state.wavemaker_manager = WavemakerManager()
        
        logger.info(f"Initializing database at {DB_URL}...")
        engine = make_db(DB_URL)
        app.state.store = Store(engine)
        
        logger.info("Initializing preset manager...")
        app.state.preset_manager = PresetManager(app.state.store)
        
        logger.info("Connecting preset manager to wavemaker manager...")
        app.state.wavemaker_manager.set_preset_manager(app.state.preset_manager)
        
        logger.info("Initializing automation service...")
        # Get timezone offset from environment (should match browser's detected timezone)
        user_tz_offset = int(os.getenv('USER_TZ_OFFSET', '0'))
        logger.info(f"User timezone offset: {user_tz_offset} minutes (UTC{'+' if user_tz_offset >= 0 else ''}{user_tz_offset//60})")
        app.state.automation = AutomationService(
            store=app.state.store,
            preset_manager=app.state.preset_manager,
            timezone_offset_minutes=user_tz_offset
        )
        
        logger.info("Creating initial snapshot...")
        app.state.latest = app.state.stage_manager.snapshot()
        
        logger.info("Starting job scheduler...")
        scheduler = JobScheduler(
            app.state.stage_manager,
            persist_cb=app.state.store.persist,
            interval_s=CONFIG['telemetry']['sample_interval_ms']/1000,
            power_allocator=app.state.power_allocator,
            wavemaker_manager=app.state.wavemaker_manager,
            automation=app.state.automation
        )
        scheduler.start(app)
        
        logger.info("Initializing hardware control system...")
        from .services.hw_devices import registry as hw_registry, DeviceConfig
        from .services.hw_patterns import pattern_registry, PatternConfig
        from .hw_scheduler.realtime_loop import start_hw_scheduler, set_led_follow, set_preset_manager
        
        # Initialize WM1 (Wavemaker Channel 1) on GPIO18
        wm1_config = DeviceConfig(
            name="Wavemaker CH1",
            gpio_pin=18,
            pwm_freq_hz=200,
            min_intensity=0.05,  # Avoid full stop
            max_intensity=1.0,
            volts_min=0.0,
            volts_max=0.6
        )
        hw_registry.register_wavemaker("WM1", wm1_config)
        
        # Initialize LED1 on GPIO19 to mirror WM1
        led1_config = DeviceConfig(
            name="LED CH1",
            gpio_pin=19,
            pwm_freq_hz=800,
            min_intensity=0.0,
            max_intensity=1.0,
            volts_min=0.0,
            volts_max=5.0
        )
        hw_registry.register_led("LED1", led1_config)
        
        # Configure LED1 to follow WM1
        set_led_follow("LED1", "WM1")
        
        # Create default PULSE pattern for WM1 (fallback when no preset active)
        default_pattern = PatternConfig(
            mode="PULSE",
            period_s=6.0,
            on_ratio=0.5,
            phase_deg=0.0,
            min_intensity=0.0,
            max_intensity=1.0
        )
        pattern_registry.create_pattern("WM1", default_pattern)
        
        # Link PresetManager to hardware control - presets drive GPIO output
        set_preset_manager(app.state.preset_manager)
        
        # Start hardware scheduler (20Hz real-time loop)
        start_hw_scheduler()
        logger.info(f"Hardware control started ({hw_registry.mode} mode)")
        
        # Auto-resume wavemakers based on current schedule
        logger.info("Auto-resuming wavemakers from schedule...")
        app.state.automation.auto_resume_from_schedule()
        
        logger.info("Reef Controller startup complete!")
        
    except Exception as e:
        logger.error(f"Failed to initialize Reef Controller: {e}", exc_info=True)
        raise