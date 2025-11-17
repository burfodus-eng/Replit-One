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
from .routers import telemetry, control, config_api, automation, arrays, history, wavemakers

logger = logging.getLogger("uvicorn.error")


app = FastAPI(title=CONFIG['site']['name'])
app.mount('/ui', StaticFiles(directory='app/web', html=True), name='ui')


@app.get('/')
async def root():
    return FileResponse('app/web/index.html')


app.include_router(telemetry.router, prefix='/api')
app.include_router(control.router, prefix='/api')
app.include_router(config_api.router, prefix='/api')
app.include_router(automation.router, prefix='/api')
app.include_router(arrays.router, prefix='/api')
app.include_router(history.router)
app.include_router(wavemakers.router, prefix='/api')


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
        
        logger.info("Initializing automation service...")
        app.state.automation = AutomationService()
        
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
        
        logger.info("Creating initial snapshot...")
        app.state.latest = app.state.stage_manager.snapshot()
        
        logger.info("Starting job scheduler...")
        JobScheduler(
            app.state.stage_manager,
            persist_cb=app.state.store.persist,
            interval_s=CONFIG['telemetry']['sample_interval_ms']/1000,
            power_allocator=app.state.power_allocator,
            wavemaker_manager=app.state.wavemaker_manager
        ).start(app)
        
        logger.info("Reef Controller startup complete!")
        
    except Exception as e:
        logger.error(f"Failed to initialize Reef Controller: {e}", exc_info=True)
        raise