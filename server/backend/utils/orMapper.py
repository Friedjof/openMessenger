# Friedjof Noweck
# 18.08.2021 Mi

from peewee import *
import uuid

from core.utils.backend.configuration import Configuration

db = MySQLDatabase(**Configuration().load().conf.db_connections["user"])


class BaseModel(Model):
    class Meta:
        database = db


class Organisation(BaseModel):
    OrganisationID = AutoField(primary_key=True)
    Name = CharField(null=True)
    Host = CharField(null=False, unique=True)
    Port = IntegerField(null=False)


class Token(BaseModel):
    TokenID = CharField(null=False, primary_key=True)
    TOTP = CharField(null=False)
    TokenTimeStamp = TimestampField(null=False)
    PeriodOfValidity = TimestampField(null=False)
    TokenStatus = BooleanField(null=True)


class Login(BaseModel):
    LoginID = AutoField(primary_key=True)
    TokenID = ForeignKeyField(Token, backref="Login", null=True)
    PasswordHash = CharField(null=False)
    TOTP = CharField(null=False)


class User(BaseModel):
    UserID = UUIDField(primary_key=True, default=uuid.uuid4)
    LoginID = ForeignKeyField(Login, backref="User", null=True)
    OrganisationID = ForeignKeyField(
        Organisation, backref="User",
        null=True
    )
    Nickname = CharField(null=False)
    FirstName = CharField(null=True)
    LastName = CharField(null=True)
    Status = CharField(null=True)
    EMailAddress = CharField(null=True)


class Chat(BaseModel):
    ChatID = UUIDField(primary_key=True, default=uuid.uuid4)
    Name = CharField(null=False)
    Description = CharField()


class UserRole(BaseModel):
    RoleID = UUIDField(primary_key=True, default=uuid.uuid4)
    Name = CharField(null=False)
    Description = CharField(null=True)


class ChatToUser(BaseModel):
    ChatToUserID = UUIDField(primary_key=True, default=uuid.uuid4)
    ChatID = ForeignKeyField(Chat, backref="ChatToUser")
    UserID = ForeignKeyField(User, backref="ChatToUser")
    Admin = BooleanField(null=False, default=False)


class UserRole2ChatToUser(BaseModel):
    RoleID = ForeignKeyField(UserRole, backref="Role2ChatToUser")
    ChatToUserID = ForeignKeyField(ChatToUser, backref="Role2ChatToUser")

    class Meta:
        """
        Creating a combination key
        - (source: http://docs.peewee-orm.com/en/latest/peewee/models.html#indexes-and-constraints)
        """
        indexes = (
            (("RoleID", "ChatToUserID"), True),
        )


class Reaction(BaseModel):
    ReactionID = UUIDField(primary_key=True, default=uuid.uuid4)
    Name = CharField()
    Description = CharField(null=True)


class TextMessage(BaseModel):
    TextMessageID = UUIDField(primary_key=True, default=uuid.uuid4)
    ChatID = ForeignKeyField(Chat, backref="TextMessage")
    AuthorID = ForeignKeyField(User, backref="TextMessage")
    Timestamp = TimestampField()
    Text = TextField(null=False)


class Reaction2TextMessage(BaseModel):
    ReactionID = ForeignKeyField(Reaction, backref="Reaction2TextMessage")
    TextMessageID = ForeignKeyField(TextMessage, backref="Reaction2TextMessage")
    UserID = ForeignKeyField(User, backref="user")

    class Meta:
        """
        Creating a combination key
        - (source: http://docs.peewee-orm.com/en/latest/peewee/models.html#indexes-and-constraints)
        """
        indexes = (
            (("ReactionID", "TextMessageID", "UserID"), True),
        )


if __name__ == "__main__":
    db.connect()
    db.create_tables([
        Organisation,
        Login, User,
        Chat,
        Reaction, Reaction2TextMessage,
        TextMessage,
        ChatToUser,
        Token
    ])
