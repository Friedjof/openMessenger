# Friedjof Noweck
# 18.08.2021 Mi
import time
import socket
import binascii
import pyotp
import ssl

from client.backend.utils.token import Token

from core.utils.backend.logging import LoggingStatus, Logging
from core.utils.backend.request import Request, RequestTypes, RequestStatus
from core.utils.backend.configuration import Configuration, ConfigPaths
from core.utils.backend.message import Message
from core.utils.backend.chat import ChatHistory


class Client:
    def __init__(self, configuration: Configuration, host: str, port: int, token: Token = None):
        self.context = ssl.create_default_context()
        self._config = configuration
        self._connection: bool = False

        self.logging: Logging = Logging(logLevel=LoggingStatus.DEBUG)
        self.logging.log(LoggingStatus.INFO, msg="Client is started", line=True)

        self.host = host
        self.port = port

        if token is None:
            self.token: Token = Token(configuration=self._config)
        else:
            self.token: Token = token

    def _sendAll(self, data: bytes) -> Request:
        try:
            with socket.create_connection((self.host, self.port)) as sock:
                with self.context.wrap_socket(sock, server_hostname=self.host) as ssock:
                    ssock.send(data)
                    data = ssock.recv(10240)
                    response = Request(payload=data)
                    self.logging.log(LoggingStatus.DEBUG, f"Response: {response.as_dict()}", ignore=True)
            time.sleep(0.1)
            return response
        except ConnectionRefusedError:
            self.logging.log(LoggingStatus.CRITICAL, f"Can not connect to the given host or port.")
            self.logging.log(LoggingStatus.CRITICAL, f"EXIT", line=True, lineString="~")
            exit()

    def _sendRequest(self, request: Request) -> Request:
        self.logging.log(
            LoggingStatus.INFO, msg=f'--> Sending "RequestTypes" >> "{request.get_requestType()}"'
        )

        response = self._sendAll(request.as_pickle())

        if response.get_requestStatus() == RequestStatus.LoginError:
            self._config.log.log(self._config.logStatus.ERROR, msg="Verification error")

        return response

    def _login(self, login) -> Request:
        login["token"] = {"PeriodOfValidity": self._config.load().conf.token["PeriodOfValidity"],
                          "StayRegistered": self._config.load().conf.token["StayRegistered"]}
        self.logging.log(LoggingStatus.DEBUG, f"Token specification: {login['token']}", ignore=True)
        new_request = Request(
            payload=login,
            requestType=RequestTypes.Login,
            requestStatus=RequestStatus.Unvalidated
        )
        return self._sendRequest(new_request)

    def Connect(self, **login):
        self.token: Token = Token(configuration=self._config)
        self.logging.log(LoggingStatus.INFO, f"Connect to {self.host}")
        self.logging.log(LoggingStatus.INFO, f"Start the login process...")

        if self.token.is_cached():
            self.logging.log(LoggingStatus.INFO, "Loading Token from cache...")
            try:
                request = Request(
                    payload={}, requestType=RequestTypes.checkToken,
                    requestStatus=RequestStatus.Unvalidated,
                    token=self.token.as_login_dict()
                )
                response = self._sendRequest(request=request)

                self.logging.log(LoggingStatus.DEBUG, f"Response: {response}", ignore=True)
                self.logging.log(LoggingStatus.DEBUG, f"Token: {self.token.as_login_dict()}", ignore=True)

                if response.get_requestStatus() == RequestStatus.Validated:
                    self._connection = True
                    self.logging.log(LoggingStatus.SUCCESSFUL, f"Your saved login data is still correct.")
                else:
                    self._connection = False
                    self.logging.log(LoggingStatus.WARNING, f"Login failed. You have to log in again.")
                    self.token.clear()
            except binascii.Error:
                self._connection = False
                self.logging.log(LoggingStatus.WARNING, f"Login failed. You have to log in again.")
                self.token.clear()
        if not self._connection:
            response = self._login(login=login)
            if response.as_dict()["requestStatus"] is RequestStatus.Validated:
                self.logging.log(LoggingStatus.SUCCESSFUL, f"Successfully logged in.")
                self._connection = True
                self.token.set_payload(payload=response.payload)
                self.token.save()
            elif response.as_dict()["requestStatus"] is RequestStatus.LoginError:
                self._connection = False
                self.logging.log(LoggingStatus.ERROR, f"Login failed. Check your login details.")

    def Message(self, text: str, chatId: str):
        self._config.log.log(self._config.logStatus.DEBUG,
                             msg=f"text: {text} | contact id: {chatId}")

        request: Request = Request(
            requestType=RequestTypes.sendMessage,
            requestStatus=RequestStatus.ClientRequest,
            payload=Message(text=text, chat_id=chatId).as_payload(),
            token=self.token.as_login_dict()
        )

        self._sendRequest(request=request)

    def ChatHistory(self, chat_id: str, since: float = 0.0, nr_of_messages: int = None) -> tuple or list:
        request: Request = Request(
            requestType=RequestTypes.chatHistory,
            requestStatus=RequestStatus.ClientRequest,
            payload=ChatHistory(chat_id=chat_id, since=since, nr_of_messages=nr_of_messages).as_payload(),
            token=self.token.as_login_dict()
        )

        response: Request = self._sendRequest(request=request)
        
        if "messages" in response.payload.keys():
            messages: list = response.payload["messages"]
            self._config.log.log(self._config.logStatus.DEBUG, msg=messages, ignore=False)
            return messages
        else:
            self._config.log.log(self._config.logStatus.WARNING, msg=response)

    def CreateChat(self, members: list or tuple, chatName: str, chatDescription: str = None) -> dict:
        if chatDescription is None:
            chatDescription = chatName
            
        request: Request = Request(
            requestType=RequestTypes.CreateChat,
            requestStatus=RequestStatus.ClientRequest,
            payload={"chatMembers": members, "chatName": chatName, "chatDescription": chatDescription},
            token=self.token.as_login_dict()
        )
        return self._sendRequest(request=request).payload

    def Contacts(self) -> list:
        request: Request = Request(
            requestType=RequestTypes.getOwnContacts,
            requestStatus=RequestStatus.ClientRequest,
            payload={},
            token=self.token.as_login_dict()
        )

        response: Request = self._sendRequest(request=request)
        contactsExists, resp = response.get(payload_items={"contacts": True})

        self._config.log.log(self._config.logStatus.DEBUG, msg=f"{contactsExists} >> {resp}", ignore=True)

        if contactsExists:
            Contact: list = resp["contacts"]
            self._config.log.log(self._config.logStatus.DEBUG, msg=Contact, ignore=True)
            return Contact
        else:
            self._config.log.log(self._config.logStatus.WARNING, msg=response)
            return []

    def Status(self, new: str = None) -> Request:
        if new is None:
            return self._getStatus()
        else:
            return self.SetStatus(new=new)

    def SetStatus(self, new: str) -> Request:
        request: Request = Request(
            requestType=RequestTypes.Status,
            requestStatus=RequestStatus.ClientRequest,
            payload={"status": new},
            token=self.token.as_login_dict()
        )

        return self._sendRequest(request=request)

    def _getStatus(self) -> Request:
        return self._sendRequest(request=Request(
            requestType=RequestTypes.Status,
            requestStatus=RequestStatus.ClientRequest,
            payload={},
            token=self.token.as_login_dict()
        ))

    def ChangePassword(self, password: str, totpCode: str, newPassword: str):
        return self._sendRequest(request=Request(
            requestType=RequestTypes.ChangePassword,
            requestStatus=RequestStatus.ClientRequest,
            payload={"password": password, "totpCode": totpCode, "newPassword": newPassword},
            token=self.token.as_login_dict()
        ))

    def ChangeTotp(self, password: str, totpCode: str):
        return self._sendRequest(request=Request(
            requestType=RequestTypes.ChangeTotpKey,
            requestStatus=RequestStatus.ClientRequest,
            payload={"password": password, "totpCode": totpCode},
            token=self.token.as_login_dict()
        ))

    def Logout(self) -> Request:
        response: Request = self._sendRequest(request=Request(
            requestType=RequestTypes.Logout,
            requestStatus=RequestStatus.ClientRequest,
            payload={},
            token=self.token.as_login_dict()
        ))

        if response.get_requestStatus() == RequestStatus.Successful:
            self.token.reset_token_cache()
            self._config.log.log(self._config.logStatus.SUCCESSFUL, msg="Successfully logged out.")
        else:
            self._config.log.log(self._config.logStatus.WARNING, msg="No logout possible...")
        return response


if __name__ == "__main__":
    friedjof = Client(
        configuration=Configuration(
                configPaths=ConfigPaths(path="paths-friedjof.yaml")
            ),
        host="127.0.0.1",
        port=34911
    )

    """Login Details"""
    totpC = pyotp.TOTP('ZINLJVQMLMZCJ6QVPYZ5G4Z3UEF4YWFZ').now()
    passwd = "QU#Rc8%9rB6q3c99"
    userId = "719b147bed674b17ae4eee5f57ec2d65"

    """Connecting to the server"""
    friedjof.Connect(
        userid=userId,
        password=passwd,
        totpCode=totpC
    )

    """Logging out"""
    # friedjof.Logout()

    """Get my status"""
    friedjof.Status()

    """Change Totp Key"""
    # friedjof.ChangeTotp(
    #     password=password, totpCode=totpCode
    # )

    """Create new Chat"""
    chat: dict = friedjof.CreateChat(
        members=("ad1f5fdf10574f008c2ee64e4e6d56a0", "719b147bed674b17ae4eee5f57ec2d65"),
        chatName="New Chat", chatDescription="A new DEV chat!"
    )
    print("New chat ID:", chat)

    """Read Chat history"""
    # messages = friedjof.ChatHistory(chat_id="aeaa437990954fc595fad3958c49badb", since=0.0)
    # for m in messages:
    #     print(m)

    """Get all own contacts"""
    # contacts: list = friedjof.contacts()
    # for contact in contacts:
    #     print(f'{contact["UserID"].hex}; {contact["Nickname"]}')

    """Send messages"""
    # for i in range(10):
    #     friedjof.message(text=f"Hey, wie geht es euch? {i}", chatId="aeaa437990954fc595fad3958c49badb")

    """Connect client"""
    # bernhard = Client(configuration=Configuration(configPaths=ConfigPaths(path="paths-bernhard.yaml")),
    #                   host="127.0.0.1", port=34911)

    """Login to the server"""
    # bernhard.connect(
    #     userid="fe87b4dec3404217b46f22c947635d25", password="393G7k2&",
    #     totpCode=pyotp.TOTP('2YDIWT4MZQZN5WJOVKDV5WMFAQCZ4O46').now()
    # )

    """Send message 'Hey!'"""
    # bernhard.message(text="Hey!", chatId="aeaa437990954fc595fad3958c49badb")
