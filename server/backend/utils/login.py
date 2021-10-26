# Friedjof Noweck
# 19.08.2021 Do

from core.utils.backend.request import Request, RequestTypes, RequestStatus
from core.utils.backend.otp import Totp
from core.utils.backend.password import Password, PasswordType

from server.backend.utils.token import ServerToken
from server.backend.utils.frequentlyUsedQueries import FrequentlyUsedQueries as FUQ
from server.backend.utils.orMapper import *


class ServerLogin:
    def __init__(self, configuration: Configuration, requestMsg: Request):
        self._config = configuration
        self.requestMsg = requestMsg

        self.fuq = FUQ()

        self.user = None
        self.login = None

        self._responsePayload: dict = {}
        self._responseStatus: RequestStatus.__dict__ = None

        if self.requestMsg.get_requestType() in (RequestTypes.ChangePassword, RequestTypes.ChangeTotpKey):
            rows = tuple(self.fuq.get_user_by(token_id=self.requestMsg.token["tokenId"]))
        else:
            rows = tuple(self.fuq.get_user_by(user_id=self.requestMsg.msg.payload.userid))
        if len(rows) == 1:
            self._config.log.log(self._config.logStatus.INFO, f"Result: {tuple(rows)}", ignore=True)
            self.user: User = rows[0]

            self.password = Password(
                configuration=self._config,
                passwordType=PasswordType.UserPassword
            )

            self.password.load_password(self.requestMsg.msg.payload.password)

            self._config.log.log(self._config.logStatus.DEBUG,
                                 f"User id >> {self.user.UserID}", ignore=True)

            login = tuple(self.fuq.get_login_by(user_id=self.user.UserID))

            if len(login) >= 1:
                self.login: Login = login[0]

                self.totp = Totp(
                    configuration=self._config,
                    userID=self.user.UserID,
                    totpKey=self.login.TOTP
                )
            else:
                self.login = None
                self.totp = None

    def verify(self) -> bool:
        if self.user is None:
            self._config.log.log(self._config.logStatus.WARNING,
                                 f"No client with this id ({self.requestMsg.msg.payload.userid}) known.")
            return False

        if self.totp is None or self.login is None:
            self._config.log.log(self._config.logStatus.WARNING,
                                 f"This user is not qualified for login.")
            return False

        self._config.log.log(
            self._config.logStatus.DEBUG,
            msg=f"Payload >> {self.requestMsg.msg.payload}",
            ignore=True
        )

        totp: bool = self.totp.verify(self.requestMsg.msg.payload.totpCode)
        passwd: bool = self.password.verify(passwordHash=self.login.PasswordHash)

        self._config.log.log(self._config.logStatus.INFO,
                             msg=f"totp is correct: {totp}; password is correct: {passwd}")

        return totp and passwd

    def response(self) -> Request:
        if self.verify():
            self._config.log.log(self._config.logStatus.DEBUG,
                                 f"-> Client token config: {self.requestMsg.payload['token']}", ignore=True)
            token = ServerToken(configuration=self._config, user=self.user, tokenConfig=self.requestMsg.payload["token"])
            token.save()
            self._responsePayload = token.client_payload()
            self._responseStatus = RequestStatus.Validated
            self._config.log.log(self._config.logStatus.DEBUG,
                                 f"> Client payload: {token.client_payload()}", ignore=True)
            self._config.log.log(self._config.logStatus.SUCCESSFUL,
                                 f"Client login data are correct")
        else:
            self._responseStatus = RequestStatus.LoginError
            self._config.log.log(self._config.logStatus.WARNING,
                                 f"Client login data is incorrect")

        self._config.log.log(self._config.logStatus.INFO, f"Login Status: {self._responseStatus.Msg}")

        return Request(
            payload=self._responsePayload,
            requestType=RequestTypes.Response,
            requestStatus=self._responseStatus
        )


class ServerLogout:
    def __init__(self, request: Request):
        self._request = request
        self._fuq = FUQ()

    def response(self) -> Request:
        login = self._fuq.get_login_by(token_id=self._request.token["tokenId"]).get()
        login.update({Login.TokenID: None}).execute()
        return Request(
            payload={},
            requestStatus=RequestStatus.Successful,
            requestType=RequestTypes.Logout
        )


class ChangePassword:
    def __init__(self, configuration: Configuration, request: Request):
        self._config = configuration
        self.request = request

        self.fuq = FUQ()

        self.password = None
        self.totpCode = None
        self.newPassword = None

        self.login = self.fuq.get_login_by(token_id=self.request.token["tokenId"]).get()

        self.foundAllImportantItems, self.payloadResponse = self.request.get(
            payload_items={"password": True, "totpCode": True, "newPassword": True}
        )
        
        self.serverLogin = ServerLogin(configuration=self._config, requestMsg=self.request)

    def _set_new_password(self) -> bool:
        self.newPassword = Password(
            configuration=self._config,
            password=self.newPassword,
            passwordType=PasswordType.UserPassword
        )

        if not self.newPassword.passwordRegulationsAreObserved(
                similarityComparison=self.password, maximumOverTuning=45.0
        ):
            return False

        self.login.PasswordHash = self.newPassword.get_hash()
        self.login.save()
        return True

    def response(self) -> Request:
        if self.foundAllImportantItems:
            self.password = self.payloadResponse["password"]
            self.totpCode = self.payloadResponse["totpCode"]
            self.newPassword = self.payloadResponse["newPassword"]

            if not self.serverLogin.verify():
                return Request(
                    payload={},
                    requestStatus=RequestStatus.LoginError,
                    requestType=RequestTypes.ChangePassword
                )

            if not self._set_new_password():
                return Request(
                    payload={"error": "Your password may not have special characters, numbers, upper and lower case letters, and a minimum character length of 12 characters. Also, the new password might be too similar to the old one."},
                    requestStatus=RequestStatus.PasswordFormatError,
                    requestType=RequestTypes.ChangePassword
                )

            return Request(
                payload={},
                requestStatus=RequestStatus.Successful,
                requestType=RequestTypes.ChangePassword
            )
        else:
            return Request(
                payload={},
                requestStatus=RequestStatus.RequestFormatError,
                requestType=RequestTypes.ChangePassword
            )


class ChangeTotp:
    def __init__(self, configuration: Configuration, request: Request):
        self._config = configuration
        self.request = request

        self.fuq = FUQ()
        self.user = self.fuq.get_user_by(token_id=self.request.token["tokenId"]).get()

        self.password = None
        self.totpCode = None

        self.serverLogin = ServerLogin(configuration=self._config, requestMsg=self.request)
        self.totp = Totp(
            configuration=self._config,
            userID=self.user
        )
        self.foundAllImportantItems, _ = self.request.get(
            payload_items={"password": True, "totpCode": True}
        )

    def _set_new_totpKey(self) -> bool:
        if not self.foundAllImportantItems:
            return False

        if not self.serverLogin.verify():
            return False

        Login.update({Login.TOTP: self.totp.totpKey, Login.TokenID: None}).where(
            Login.LoginID == self.fuq.get_login_by(user_id=self.user.UserID)
        ).execute()

        return True

    def response(self) -> Request:
        if not self._set_new_totpKey():
            return Request(
                payload={"totpKey": None},
                requestStatus=RequestStatus.ClientError,
                requestType=RequestTypes.Response
            )
        return Request(
            payload={"totpKey": self.totp.totpKey},
            requestStatus=RequestStatus.Successful,
            requestType=RequestTypes.Response
        )
