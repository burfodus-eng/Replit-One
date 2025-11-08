from apscheduler.schedulers.asyncio import AsyncIOScheduler


class JobScheduler:
    def __init__(self, mgr, persist_cb=None, interval_s=1.0):
        self.mgr = mgr
        self.persist_cb = persist_cb
        self.interval_s = interval_s
        self.sched = AsyncIOScheduler()


    def start(self, app):
        @self.sched.scheduled_job("interval", seconds=self.interval_s)
        def sample_job():
            snap = self.mgr.snapshot()
            if self.persist_cb:
                self.persist_cb(snap)
            app.state.latest = snap # cheap cache for GUI
        self.sched.start()
