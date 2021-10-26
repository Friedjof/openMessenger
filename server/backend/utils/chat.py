# Friedjof Noweck
# 07.09.2021 Di

from core.utils.backend.request import Request, RequestTypes, RequestStatus

from server.backend.utils.orMapper import *
from server.backend.utils.frequentlyUsedQueries import FrequentlyUsedQueries as FUQ


class CreateChat:
    def __init__(self, request: Request):
        self.request: Request = request

        self.fuq = FUQ()

        self.chatMembers = None
        self.chatName = None
        self.chatDescription = None

        self.requestAuthor = self.fuq.get_user_by(token_id=self.request.token["tokenId"]).get()

        self._load()

    def _load(self):
        foundAllImportantItems, response = self.request.get(payload_items={
            "chatMembers": True, "chatName": True, "chatDescription": True
        })

        if foundAllImportantItems:
            self.chatMembers: list = response["chatMembers"]
            self.chatName: str = response["chatName"]
            self.chatDescription: str = response["chatDescription"]

    def response(self) -> Request:
        if None in (self.chatMembers, self.chatName, self.chatDescription):
            return Request(
                payload={},
                requestType=RequestTypes.Response,
                requestStatus=RequestStatus.RequestFormatError
            )

        chat = Chat.create(
            Name=self.chatName,
            Description=self.chatDescription
        )

        for member in self.chatMembers:
            user = self.fuq.get_user_by(user_id=member).get()

            if user == self.requestAuthor:
                ChatToUser.create(
                    ChatID=chat.ChatID,
                    UserID=user.UserID,
                    Admin=1
                )
            else:
                ChatToUser.create(
                    ChatID=chat.ChatID,
                    UserID=user.UserID
                )

        return Request(
            payload={
                "chatId": chat.ChatID, "members": tuple(self.fuq.get_user_by(chat_id=chat.ChatID).dicts())
            },
            requestStatus=RequestStatus.ServerResponse,
            requestType=RequestTypes.Response
        )
