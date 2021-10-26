# Friedjof Noweck
# 02.09.2021 Do

from peewee import ModelSelect
import base64
import hashlib

from server.backend.utils.orMapper import *


class FrequentlyUsedQueries:
    def __init__(self):
        pass

    def get_user_by(
            self, user_id: str = None, login_id: str = None, token_id: str = None,
            chat_id: str = None, owner_id: str = None
    ) -> ModelSelect or None:
        if user_id is not None:
            return User.select().where(User.UserID == user_id)
        elif login_id is not None:
            return User.select().join(
                Login, on=(Login.LoginID == User.LoginID)
            ).where(Login.LoginID == login_id)
        elif token_id is not None:
            token = self.get_token_by(token_id=token_id).get()

            return User.select().join(
                Login, on=(Login.LoginID == User.LoginID)
            ).join(
                Token, on=(Token.TokenID == Login.TokenID)
            ).where(Token.TokenID == token.TokenID)
        elif chat_id is not None:
            return User.select().join(
                ChatToUser, on=(ChatToUser.UserID == User.UserID)
            ).join(
                Chat, on=(Chat.ChatID == ChatToUser.ChatID)
            ).where(
                Chat.ChatID == chat_id
            )
        elif owner_id is not None:
            return User.select().join(
                ChatToUser, on=(ChatToUser.UserID == User.UserID)
            ).join(
                Chat, on=(Chat.ChatID == ChatToUser.ChatID)
            ).where(Chat.ChatID.in_(
                (ChatToUser.select(ChatToUser.ChatID).where(ChatToUser.UserID == owner_id))
            ) & (User.UserID != owner_id)).distinct()

    def get_login_by(self, login_id: str = None, user_id: str = None, token_id: str = None) -> ModelSelect or None:
        if login_id is not None:
            return Login.select().where(Login.LoginID == login_id)
        elif user_id is not None:
            return Login.select().join(
                User, on=(User.LoginID == Login.LoginID)
            ).where(User.UserID == user_id)
        elif token_id is not None:
            token = self.get_token_by(token_id=token_id).get()

            return Login.select().join(
                Token, on=(Token.TokenID == Login.TokenID)
            ).where(Token.TokenID == token.TokenID)

    def get_token_by(
            self, token_id: str = None, token_id_hash: str = None,
            login_id: str = None, user_id: str = None
    ) -> ModelSelect or None:
        if token_id is not None:
            hashed_token_id = base64.b64encode(hashlib.sha256(token_id.encode('utf-8')).digest())
            return Token.select().where(Token.TokenID == hashed_token_id)
        elif token_id_hash is not None:
            return Token.select().where(Token.TokenID == token_id_hash)
        elif login_id is not None:
            return Token.select().join(
                Login, on=(Login.LoginID == Token.LoginID)
            ).where(Login.LoginID == login_id)
        elif user_id is not None:
            return Token.select().join(
                Login, on=(Login.TokenID == Token.TokenID)
            ).join(
                User, on=(User.LoginID == Login.LoginID)
            ).where(User.UserID == user_id)

    def get_chat_by(self, chat_id: str = None) -> ModelSelect or None:
        if chat_id is not None:
            return Chat.select().where(Chat.ChatID == chat_id)

    def get_messages_by(
            self, chat_id: str = None,
            author_id: str = None,
            message_id: str = None,
            sinceTimeStamp: int = 0.0,
            nrOfMessages: int = None
    ) -> ModelSelect or None:

        if message_id is not None:
            if author_id is not None:
                return TextMessage.select().where(
                    (TextMessage.TextMessageID == message_id) &
                    (TextMessage.AuthorID == author_id)
                )
            return TextMessage.select().where(TextMessage.TextMessageID == message_id)
        elif chat_id is not None and sinceTimeStamp is not None:
            if nrOfMessages is None:
                if author_id is not None:
                    return TextMessage.select().where(
                        (TextMessage.ChatID == chat_id) &
                        (TextMessage.Timestamp > sinceTimeStamp) &
                        (TextMessage.AuthorID.in_(self.get_user_by(chat_id=chat_id)))
                    )
                return TextMessage.select().where(
                    (TextMessage.ChatID == chat_id) &
                    (TextMessage.Timestamp > sinceTimeStamp)
                )
            else:
                if author_id is not None:
                    return TextMessage.select().where(
                        (TextMessage.ChatID == chat_id) &
                        (TextMessage.AuthorID.in_(self.get_user_by(chat_id=chat_id)))
                    ).order_by(TextMessage.Timestamp.desc()).limit(nrOfMessages)
                return TextMessage.select().where(
                    (TextMessage.ChatID == chat_id)
                ).order_by(TextMessage.Timestamp.desc()).limit(nrOfMessages)

    def get_organisation_by(self, organisation_id: str = None, user_id: str = None) -> ModelSelect:
        if organisation_id is not None:
            return Organisation.select().where(Organisation.OrganisationID == organisation_id)
        elif user_id is not None:
            return Organisation.select().join(
                User, on=(User.OrganisationID == Organisation.OrganisationID)
            ).where(User.UserID == user_id)

    def chat_exists(self, chat_id) -> bool:
        try:
            self.get_chat_by(chat_id=chat_id).get()
            return True
        except:
            return False
