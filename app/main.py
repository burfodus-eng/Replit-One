from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from .config import CONFIG, DB_URL, APP_PORT
from .services.stage_manager import StageManager
from .services.scheduler import JobScheduler
from .services.storage import make_db, Store
from .routers import telemetry, control, config_api


app = FastAPI(title=CONFIG['site']['name'])
app.mount('/ui', StaticFiles(directory='app/web', html=True), name='ui')


@app.get('/')
async def root():
return FileResponse('app/web/index.html')


app.include_router(telemetry.router, prefix='/api')
app.include_router(control.router, prefix='/api')
app.include_router(config_api.router, prefix='/api')


@app.on_event('startup')
async def startup():
app.state.mgr = StageManager(CONFIG)
engine = make_db(DB_URL)
store = Store(engine)
app.state.latest = app.state.mgr.snapshot()
JobScheduler(app.state.mgr, persist_cb=store.persist, interval_s=CONFIG['telemetry']['sample_interval_ms']/1000).start(app)