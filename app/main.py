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
from .routers import telemetry, control, config_api, automation, arrays, history


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


@app.on_event('startup')
async def startup():
    app.state.config = CONFIG
    app.state.stage_manager = StageManager(CONFIG)
    app.state.mgr = app.state.stage_manager
    app.state.automation = AutomationService()
    app.state.health = SystemHealthService()
    app.state.events = EventsService(max_events=200)
    app.state.power_allocator = PowerAllocator(CONFIG, app.state.events)
    engine = make_db(DB_URL)
    app.state.store = Store(engine)
    app.state.latest = app.state.stage_manager.snapshot()
    JobScheduler(
        app.state.stage_manager,
        persist_cb=app.state.store.persist,
        interval_s=CONFIG['telemetry']['sample_interval_ms']/1000,
        power_allocator=app.state.power_allocator
    ).start(app)