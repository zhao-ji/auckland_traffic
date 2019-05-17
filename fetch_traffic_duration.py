from celery import Celery
from celery.schedules import crontab
from requests import get

from local_settings import GOOGLE_URL, GOOGLE_API_KEY

app = Celery("auckland_traffic")
app.conf.update(
    CELERY_TIMEZONE="Pacific/Auckland",
    BROKER_URL="redis://localhost",
    CELERY_TASK_SERIALIZER="json",
    CELERY_ACCEPT_CONTENT=["json"],
    CELERYBEAT_SCHEDULE={
        "fetch_duration": {
            "task": "auckland_traffic.fetch_duration",
            "schedule": crontab(minute="*"),
            "options": {
                "expires": 30,
                "priority": 0,
            }
        }
    }
)


@app.task(name="auckland_traffic.fetch_duration")
def fetch_duration():
    params = {
        "key": GOOGLE_API_KEY,
        "mode": "driving",
        "region": "nz",
        "units": "metric",
        "origins": "60 stanhope road, auckland",
        "destinations": "victoria street car park",
    }
    ret = get(GOOGLE_URL, params=params)
    if ret.ok:
        data = ret.json()
        for row in data["rows"]:
            for element in row["elements"]:
                print element["duration"]["text"]
                print element["distance"]["text"]


if __name__ == "__main__":
    fetch_duration()
