# Friedjof Noweck
# 23.08.2021 Mo


class Message:
    def __init__(self, text: str, chat_id: str):
        self.text = text
        self.chat_id = chat_id

    def as_payload(self) -> dict:
        return {"text": self.text, "chatId": self.chat_id}
