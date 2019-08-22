import datetime

from peewee import SqliteDatabase, Model
from peewee import CharField, ForeignKeyField, DateTimeField, IntegerField, FloatField

# from local_settings import DB_LOCATION

db = SqliteDatabase("here.db", {
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
    lantitude = CharField(default="")
    longtitude = CharField(default="")


class Route(BaseModel):
    start = ForeignKeyField(Address, backref="as_starts", null=False, on_delete="CASCADE")
    stop = ForeignKeyField(Address, backref="as_stops", null=False, on_delete="CASCADE")
    method = IntegerField(choices=method_choices, null=False)
    cron = CharField(default="")

    @property
    def method_readable(self):
        return dict(method_choices)[self.method]

    # @shared_task
    def check_and_trace():
        # from models import Route
        # query = Route.select()
        # for route in query:
        #     if route.cron:
        #         if not route.traces:
        #             pass
        #         last_trace = route.Traces[-1]
        #         min, hour, dow, dom, moy = route.cron.split(" ")
        #         schedule = crontab(min, hour, dow, dom, moy)
        pass


class Trace(BaseModel):
    route = ForeignKeyField(Route, backref="traces", null=False, on_delete="CASCADE")
    source = IntegerField(choices=source_choices)
    # unit: km
    duration = FloatField(null=False)
    # unit: min
    distance = FloatField(null=False)

    def get_source(self):
        return dict(source_choices)[self.status]


if __name__ == "__main__":
    with db:
        db.drop_tables([Address, Route, Trace])
        db.create_tables([Address, Route, Trace])
        a = Address.create(address="60 stanhope road auckland")
        b = Address.create(address="188 carrington road auckland")
        c = Route.create(start=a, stop=b, method=0)
