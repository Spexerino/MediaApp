# scheduler_runner.py
from apscheduler.schedulers.blocking import BlockingScheduler
from app import create_app
from app.startup import scan_and_insert_folders_and_files

app = create_app()
scheduler = BlockingScheduler()

@scheduler.scheduled_job('cron', hour=6)
def scheduled_job():
    with app.app_context():
        scan_and_insert_folders_and_files(app)

if __name__ == '__main__':
    scheduler.start()
