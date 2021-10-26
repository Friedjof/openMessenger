# Friedjof Noweck
# 18.08.2021 Mi

from server.backend.utils.orMapper import *


# Create all DB-Tables...
if __name__ == "__main__":
    db.Connect()
    db.create_tables(
        [
            Organisation,
            Token,
            Login, User,
            Chat, TextMessage,
            Reaction,
            Reaction2TextMessage,
            ChatToUser,
            UserRole, UserRole2ChatToUser
        ]
    )
