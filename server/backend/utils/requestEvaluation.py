# Friedjof Noweck
# 19.08.2021 Do

from server.backend.utils.login import ServerLogin, ServerLogout, ChangePassword, ChangeTotp
from server.backend.utils.token import TokenLogin
from server.backend.utils.message import ReceiveTextMessage, MessageRequest
from server.backend.utils.contact import OwnContacts
from server.backend.utils.user import UserRequests
from server.backend.utils.chat import CreateChat

from core.utils.backend.request import Request, RequestTypes, RequestStatus
from core.utils.backend.configuration import Configuration


class Evaluation:
    def __init__(self, configuration: Configuration):
        self.config: Configuration = configuration

        self.tokenLogin = TokenLogin(configuration=self.config)

    def load(self, request: Request) -> Request:
        requestType = request.get_requestType()

        self.tokenLogin.set_request(request=request)
        if self.tokenLogin.token_is_true() or requestType == RequestTypes.Login:
            if requestType == RequestTypes.Login:
                return ServerLogin(configuration=self.config, requestMsg=request).response()
            elif requestType == RequestTypes.Logout:
                return ServerLogout(request=request).response()
            elif requestType == RequestTypes.checkToken:
                return self.tokenLogin.request_validation(request=request)
            elif requestType == RequestTypes.sendMessage:
                return ReceiveTextMessage(configuration=self.config, request=request).deliver()
            elif requestType == RequestTypes.chatHistory:
                return MessageRequest(request=request).response()
            elif requestType == RequestTypes.getOwnContacts:
                return OwnContacts(request=request).response()
            elif requestType in (RequestTypes.Status,):
                return UserRequests(request=request).response()
            elif requestType == RequestTypes.CreateChat:
                return CreateChat(request=request).response()
            elif requestType == RequestTypes.ChangePassword:
                return ChangePassword(configuration=self.config, request=request).response()
            elif requestType == RequestTypes.ChangeTotpKey:
                return ChangeTotp(configuration=self.config, request=request).response()
        else:
            self.config.log.log(
                self.config.logStatus.WARNING,
                msg='The login process was not successful.'
            )
            return Request(
                payload={"error": "The login process was not successful."},
                requestStatus=RequestStatus.LoginError,
                requestType=RequestTypes.Response
            )

        self.config.log.log(
            self.config.logStatus.WARNING,
            msg=f'"{request.get_requestType()}" as request type is undefined.'
        )
        return Request(
            payload={"error": f"This request type is undefined ({request.get_requestType()})."},
            requestStatus=RequestStatus.ClientError,
            requestType=RequestTypes.Response
        )
