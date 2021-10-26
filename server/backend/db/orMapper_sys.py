# Friedjof Noweck
# 19.08.2021 Do

from peewee import *
from core.utils.backend.configuration import Configuration

db = MySQLDatabase(**Configuration().load().conf.db_connections["system"])


class BaseModel(Model):
    class Meta:
        database = db


class Sessions(BaseModel):
    SessionID = CharField()
    TOTP = CharField()
    SessionTimeStamp = TimestampField()
    Status = CharField(null=True)


if __name__ == "__main__":
    db.connect()
    db.create_tables([Sessions])
