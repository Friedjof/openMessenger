# Friedjof Noweck
# 24.08.2021 Di
import time
from peewee import ModelSelect

from server.backend.utils.orMapper import *
from server.backend.utils.frequentlyUsedQueries import FrequentlyUsedQueries as FUQ

from core.utils.backend.request import Request, RequestTypes, RequestStatus
from core.utils.backend.chat import ChatHistory


class MessageMetaData:
    def __init__(self, request: Request = None):
        if request is not None:
            self.request = request
            self.payload = request.payload

            self.orgChatId = None
            self.chat = None
            self.fuq = FUQ()

            self._keys = tuple(request.payload.keys())

            if "text" in self._keys:
                self.text: str = self.request.payload["text"]
            else:
                self.text = None

            if "chatId" in self._keys:
                if self.fuq.chat_exists(chat_id=self.request.payload["chatId"]):
                    self.orgChatId = self.request.payload["chatId"]
                    # Determination of the recipient chat by means of the chat id.
                    self.chat: Chat = self.fuq.get_chat_by(chat_id=self.request.payload["chatId"]).get()

            # Determine sender using the token id.
        self.transmitter: User = self.fuq.get_user_by(token_id=self.request.token["tokenId"]).get()


class ReceiveTextMessage:
    def __init__(self, configuration: Configuration, request: Request):

        self._config = configuration
        self._request = request

        self.metaData = MessageMetaData(request=request)

    def deliver(self) -> Request:

        if self.metaData.chat is None:
            self._config.log.log(
                self._config.logStatus.WARNING,
                msg=f"The given chat id {self.metaData.orgChatId} does not exists."
            )

            return Request(
                payload={"error": f"The chat with this ID does not exist."},
                requestStatus=RequestStatus.ClientError,
                requestType=RequestTypes.Response
            )

        user: ModelSelect = FUQ().get_user_by(chat_id=self.metaData.chat.ChatID)

        self._config.log.log(
            self._config.logStatus.DEBUG,
            msg=f"Chat participants: {', '.join(u.Nickname for u in user)}",
            ignore=True
        )

        TextMessage.create(
            ChatID=self.metaData.chat.ChatID,
            AuthorID=self.metaData.transmitter.UserID,
            TimeStamp=time.time(),
            Text=self._request.payload["text"]
        )

        return Request(
            payload={}, requestType=RequestTypes.sendMessage,
            requestStatus=RequestStatus.Successful
        )


class MessageRequest:
    def __init__(self, request: Request):
        self._request = request
        self.chat: ChatHistory = ChatHistory().from_payload(payload=request)

        self.fuq = FUQ()

        self.author: User = self.fuq.get_user_by(token_id=self._request.token["tokenId"]).get()

        self.formatCorrect = True

        try:
            self.messages: tuple = (self.fuq.get_messages_by(
                chat_id=self.chat.chatId, author_id=self.author.UserID, nrOfMessages=self.chat.nr_of_messages
            ).dicts())
        except AttributeError:
            self.formatCorrect = False

    def response(self) -> Request:
        if self.formatCorrect:
            return Request(payload={"messages": [message for message in self.messages]})
        else:
            return Request(
                payload={},
                requestStatus=RequestStatus.RequestFormatError,
                requestType=RequestTypes.Response
            )
