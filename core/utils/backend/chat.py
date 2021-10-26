# Friedjof Noweck
# 07.09.2021 Di

from core.utils.backend.request import Request


class ChatHistory:
    def __init__(self, chat_id: str = None, since: int or float = 0.0, **kwargs):
        self.chatId: str = chat_id
        self.since = since
        self.nr_of_messages = None
        self.args: dict = kwargs

        self._updateArgs()

    def as_payload(self) -> dict:
        return self.args

    def _updateArgs(self) -> dict:
        self.args.update({"chatId": self.chatId, "since": self.since})
        return self.args

    def from_payload(self, payload: Request) -> any:
        keys = payload.payload.keys()

        if "chatId" in keys:
            self.chatId = payload.payload["chatId"]

        if "since" in keys:
            self.since: int = payload.payload["since"]

        if "nr_of_messages" in keys:
            self.nr_of_messages = payload.payload["nr_of_messages"]

        self._updateArgs()
        return self

    def __str__(self) -> str:
        return str(self.args)
