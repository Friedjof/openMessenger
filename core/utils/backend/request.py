# Friedjof Noweck
# 19.08.2021 Do
import pickle
from collections import namedtuple

from core.utils.backend.logging import LoggingStatus, Logging


class RequestTypes:
    Login: str = "Login"
    Logout: str = "Logout"
    ChangePassword: str = "Change password"
    ChangeTotpKey: str = "Change totp key"
    CreateChat: str = "Create chat"
    Status: str = "Status"
    checkToken: str = "Check token"
    sendMessage: str = "Send message"
    chatHistory: str = "Get chat history"
    getOwnContacts: str = "Get own contacts"
    Response: str = "response"
    Null: str = None


class RequestStatus:
    class Undefined:
        Status: int = 0
        Msg: str = "Undefined"

    class Info:
        Status: int = 100
        Msg: str = "Info"

    class Created:
        Status: int = 101
        Msg: str = "Created"

    class Unvalidated:
        Status: int = 102
        Msg: str = "Unvalidated"

    class Validated:
        Status: int = 103
        Msg: str = "Validated"

    class ClientRequest:
        Status: int = 104
        Msg: str = "ClientRequest"

    class ServerResponse:
        Status: int = 105
        Msg: str = "ServerResponse"

    class Successful:
        Status: int = 200
        Msg: str = "Successful"

    class ClientError:
        Status: int = 400
        Msg: str = "ClientError"

    class LoginError:
        Status: int = 401
        Msg: str = "LoginError"

    class RequestFormatError:
        Status: int = 402
        Msg: str = "RequestFormatError"
        
    class PasswordFormatError:
        Status: int = 403
        Msg: str = "PasswordFormatError"

    class ServerError:
        Status: int = 500
        Msg: str = "ServerError"

    class Null:
        Status: int = None
        Msg: str = "Null"


class RequestStatusManagement(RequestStatus):
    def find(self, msg: str = None, status: int = None) -> RequestStatus.__dict__:
        for requestStatus in (
                self.Undefined, self.Info, self.Created, self.Undefined, self.Validated,
                self.Successful, self.ClientError, self.LoginError, self.ServerError, self.Null):
            if msg is not None:
                if requestStatus.Msg == msg:
                    return requestStatus
            elif status is not None:
                if requestStatus.Status == status:
                    return requestStatus


class Request:
    def __init__(
            self, payload: bytes or dict,
            requestType: RequestTypes or str = None,
            requestStatus: RequestStatus.__dict__ = RequestStatus.Undefined,
            token: dict = None
    ):
        self._row_data = payload
        self.token = token
        self._requestType: RequestTypes = requestType
        self._requestStatus = requestStatus

        self._logging = Logging()

        if type(self._row_data) is bytes:
            try:
                dict_data = pickle.loads(payload)
            except EOFError:
                self._logging.log(LoggingStatus.ERROR, msg=f">> Lost connection <<")
                raise ConnectionError("Lost connection")
            self.payload: dict = dict_data["payload"]
            self._requestType: RequestTypes = dict_data["requestType"]
            self._requestStatus: RequestStatus.__dict__ = dict_data["requestStatus"]
            self.token: dict = dict_data["token"]
        else:
            self.payload: dict = self._row_data

        self.msg = self._load_msg()

        self._logging.log(LoggingStatus.DEBUG, msg=f">> Request Type: {self._requestType}", ignore=True)
        self._logging.log(LoggingStatus.DEBUG, msg=f">> Request Status: {self._requestStatus.Msg}", ignore=True)

    def _payload_keys(self) -> tuple:
        return tuple(self.payload.keys())

    def get(self, payload_items: dict) -> tuple:
        """
        :param payload_items: {<name of payload key>:<important? [True or False]>, ...}
        :return: (<found all important payload keys? [True or False]>, response)
        Example:
        >> foundAllImportantItems, response = request.get(payload_items={"XXX": True, "CCC": True, "VVV": False})
        """

        keys = self._payload_keys()

        response: dict = {}

        for k in keys:
            if k in payload_items.keys():
                response[k] = self.payload[k]

        for k, v in payload_items.items():
            if k not in response.keys() and v:
                return False, response

        return True, response

    def _load_msg(self) -> namedtuple:
        return namedtuple('Configuration', ["requestType", "requestStatus", "payload"])(
            requestType=self._requestType,
            requestStatus=self._requestStatus,
            payload=namedtuple('payload', self.payload.keys())(**self.payload))

    def set_token(self, token: dict):
        self.token = token

    def set_requestStatus(self, status: RequestStatus or int) -> None:
        self._requestStatus = status
        self.msg = self._load_msg()

    def set_requestType(self, typ: RequestTypes or str) -> None:
        self._requestType = typ
        self.msg = self._load_msg()

    def get_requestStatus(self) -> RequestStatus.__dict__:
        return self._requestStatus

    def get_requestType(self) -> RequestTypes:
        return self._requestType

    def as_dict(self) -> dict:
        return {"requestType": self.msg.requestType, "requestStatus": self.msg.requestStatus,
                "payload": self.payload, "token": self.token}

    def as_pickle(self) -> bytes:
        return pickle.dumps(self.as_dict())

    def __str__(self) -> str:
        return str(self.as_dict())
