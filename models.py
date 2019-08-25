import datetime
from pprint import pprint

from celery.schedules import crontab
from peewee import SqliteDatabase, Model
from peewee import CharField, ForeignKeyField, DateTimeField, IntegerField, FloatField

from apis import google_trace, bing_trace

# from local_settings import DB_LOCATION

db = SqliteDatabase("./backup/here.db", {
    # allow readers and writers to co-exist
    'journal_mode': 'wal',
    # page-cache size in KiB  64MB
    'cache_size': -1 * 64000,
    # foreign-key constraints
    'foreign_keys': 1,
    # check constraints
    'ignore_check_constraints': 1,
    'synchronous': 0,
})


method_choices = [
    (0, "driving"),
    (1, "walking"),
    (2, "bicycling"),
    (3, "transite"),
]

source_choices = [
    (0, "google"),
    (1, "bing"),
]


class BaseModel(Model):
    class Meta:
        database = db

    created_at = DateTimeField(default=datetime.datetime.now)


class Address(BaseModel):
    address = CharField(unique=True, null=False, index=True)
    alias = CharField(default="")
    latitude = CharField(default="")
    longitude = CharField(default="")

    def serialize(self):
        return {
            "id": self.id,
            "address": self.address,
            "alias": self.alias,
            "latitude ": self.latitude,
            "longitude": self.longitude,
        }


class Route(BaseModel):
    start = ForeignKeyField(Address, backref="as_starts", null=False, on_delete="CASCADE")
    stop = ForeignKeyField(Address, backref="as_stops", null=False, on_delete="CASCADE")
    method = IntegerField(choices=method_choices, null=False)
    cron = CharField(default="")

    @property
    def method_readable(self):
        return dict(method_choices)[self.method]

    def check_and_trace(self):
        if not self.cron:
            return
        if not self.traces:
            return self.trace()

        last_trace = self.traces[-1]
        min, hour, dom, moy, dow = self.cron.split(" ")
        schedule = crontab(
            minute=min, hour=hour, day_of_week=dow,
            day_of_month=dom, month_of_year=moy,
        )
        if schedule.is_due(last_trace.created_at):
            self.trace()

    def trace(self):
        try:
            result = google_trace(self.start, self.stop, self.method)
            Trace.create(
                route=self.id, source=0,
                duration=result["duration"],
                distance=result["distance"],
            )
        except Exception as e:
            pprint(e)

        try:
            result = bing_trace(self.start, self.stop, self.method_readable)
            Trace.create(
                route=self.id, source=1,
                duration=result["duration"],
                distance=result["distance"],
            )
        except Exception as e:
            pprint(e)

    def serialize(self):
        return {
            "id": self.id,
            "start": self.start.serialize(),
            "stop": self.stop.serialize(),
            "method": self.method_readable,
            "cron": self.cron,
        }


class Trace(BaseModel):
    route = ForeignKeyField(Route, backref="traces", null=False, on_delete="CASCADE")  # noqa
    source = IntegerField(choices=source_choices)
    # unit: m
    duration = FloatField(null=False)
    # unit: second
    distance = FloatField(null=False)

    @property
    def source_readable(self):
        return dict(source_choices)[self.status]

    def serialize(self):
        return {
            "id": self.id,
            "route": self.route.serialize(),
            "source": self.source_readable,
            "duration": self.duration,
            "distance": self.distance,
        }


if __name__ == "__main__":
    with db:
        db.drop_tables([Address, Route, Trace])
        db.create_tables([Address, Route, Trace])
        a = Address.create(address="60 stanhope road auckland")
        b = Address.create(address="188 carrington road auckland")
        c = Route.create(start=a, stop=b, method=0)
        c.trace()
