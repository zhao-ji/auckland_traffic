from celery import Celery
from requests import get

from local_settings import GOOGLE_URL, GOOGLE_API_KEY

app = Celery("auckland_traffic")
app.conf.update(
    celery_timezone="Pacific/Auckland",
    BROKER_URL="redis://localhost",
    celery_task_serializer="json",
    celery_accept_content=["json"],
    celerybeat_schedule={
        "fetch_duration": {
            "task": "auckland_traffic.fetch_duration",
            "schedule": 60.0,
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
