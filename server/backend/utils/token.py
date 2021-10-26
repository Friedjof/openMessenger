# Friedjof Noweck
# 20.08.2021 Fr
import time
import pyotp
import base64
import bcrypt
import hashlib

from core.utils.backend.otp import Totp, TotpType
from core.utils.backend.request import Request, RequestTypes, RequestStatus

from server.backend.utils.orMapper import *
from server.backend.utils.frequentlyUsedQueries import FrequentlyUsedQueries as FUQ


class TokenLogin:
    def __init__(self, configuration: Configuration, request: Request = None):
        self._config = configuration
        self._request = request

    def request_validation(self, request: Request = None) -> Request:
        self._config.log.log(self._config.logStatus.DEBUG, f"Token validation...", ignore=True)
        if request is None:
            clientToken: dict = self._request.token
        else:
            clientToken: dict = request.token

        if clientToken is None:
            return self._get_token_validation_error_response()

        serverToken = ServerToken(configuration=self._config)
        token_exists = serverToken.token_exists(clientToken["tokenId"])
        self._config.log.log(self._config.logStatus.DEBUG,
                             f"Client tokenTOTP Code: {clientToken['tokenTOTP']}", ignore=True)
        self._config.log.log(self._config.logStatus.DEBUG,
                             f"Server tokenTOTP Code: {pyotp.TOTP(serverToken.tokenTOTP.totpKey).now()}", ignore=True)
        self._config.log.log(self._config.logStatus.DEBUG,
                             f"Server tokenTOTP: {serverToken.tokenTOTP.totpKey}", ignore=True)

        if token_exists and pyotp.TOTP(serverToken.tokenTOTP.totpKey).verify(clientToken["tokenTOTP"]):
            self._config.log.log(self._config.logStatus.SUCCESSFUL, f"Token validation successful")
            return Request(
                payload={}, requestType=RequestTypes.checkToken,
                requestStatus=RequestStatus.Validated
            )
        else:
            self._config.log.log(self._config.logStatus.WARNING, f"Token validation failed")
            return self._get_token_validation_error_response()

    def _get_token_validation_error_response(self) -> Request:
        return Request(
                payload=ServerToken(configuration=self._config).client_payload(),
                requestType=RequestTypes.checkToken,
                requestStatus=RequestStatus.LoginError
            )

    def token_is_true(self) -> bool:
        if self._request is None:
            return False
        else:
            return self.request_validation().get_requestStatus() == RequestStatus.Validated

    def set_request(self, request: Request):
        self._request: Request = request


class TokenConfig:
    def __init__(self, configuration: Configuration, tokenConfig: dict = None):
        self._config = configuration

        if tokenConfig is None:
            self.PeriodOfValidity: int = self._config.conf.token["PeriodOfValidity"]["min"]
            self.StayRegistered: bool or None = None
        else:
            if "PeriodOfValidity" in tuple(tokenConfig.keys()):
                if self._config.conf.token["PeriodOfValidity"]["min"] <= int(tokenConfig["PeriodOfValidity"]) <= self._config.conf.token["PeriodOfValidity"]["max"]:
                    self.PeriodOfValidity: int = int(tokenConfig["PeriodOfValidity"])
                else:
                    self.PeriodOfValidity: int = self._config.conf.token["PeriodOfValidity"]["min"]
            else:
                self.PeriodOfValidity: int = self._config.conf.token["PeriodOfValidity"]["min"]
            if "StayRegistered" in tuple(tokenConfig.keys()):
                if type(tokenConfig["StayRegistered"]) is bool or type(tokenConfig["StayRegistered"]) is None:
                    self.StayRegistered: bool = tokenConfig["StayRegistered"]
                else:
                    self.StayRegistered: bool or None = None
            else:
                self.StayRegistered: bool or None = None

    def as_dict(self) -> dict:
        self._config.log.log(self._config.logStatus.DEBUG, msg=f"PeriodOfValidity: {self.PeriodOfValidity}")
        return {"PeriodOfValidity": self.PeriodOfValidity, "StayRegistered": self.StayRegistered}


class ServerToken:
    def __init__(self, configuration: Configuration, user: User = None, tokenConfig: dict = None):
        self._config = configuration
        self.user = user

        self.tokenConfig = TokenConfig(configuration=self._config, tokenConfig=tokenConfig)

        self._timeStamp = time.time()
        self.tokenId: str = self._config.uuid.generate()

        self.tokenTOTP = Totp(
            configuration=self._config,
            userID=self.tokenId,
            totpType=TotpType.Token
        )

    def client_payload(self) -> dict:
        return {"tokenId": self.tokenId, "tokenTOTP": self.tokenTOTP.totpKey}

    def token_exists(self, tokenId: str) -> bool:
        self._config.log.log(self._config.logStatus.DEBUG, f"Token ID: {tokenId}", ignore=True)

        token: Token = FUQ().get_token_by(token_id=tokenId)

        if token is not None and len(tuple(token)) >= 1:
            token = tuple(token)[0]

            self._config.log.log(self._config.logStatus.INFO, f"Server token status: {token.TokenStatus}")
            self._config.log.log(self._config.logStatus.INFO,
                                 f"Time since generated: {int(time.time() - token.TokenTimeStamp.timestamp())}sec")
            self._config.log.log(self._config.logStatus.INFO,
                                 f"PeriodOfValidity: {token.PeriodOfValidity.timestamp()}")
            if token.TokenStatus is False:
                self._config.log.log(self._config.logStatus.WARNING, f"This token is marked as invalid.")
                return False
            elif time.time() - token.TokenTimeStamp.timestamp() > token.PeriodOfValidity.timestamp() and token.TokenStatus is not True:
                self._config.log.log(self._config.logStatus.WARNING, f"This token has expired and must be renewed.")
                token.TokenStatus = False
                token.save()
                self._config.log.log(self._config.logStatus.DEBUG, f"The token was marked as invalid.", ignore=True)
                return False

            self.user = tuple(FUQ().get_user_by(token_id=tokenId))

            if len(self.user) > 0:
                self.user = self.user[0]
                self._config.log.log(
                    self._config.logStatus.INFO, f"user response form DB: {self.user}",
                    ignore=True
                )

                self.tokenTOTP = Totp(
                    configuration=self._config,
                    userID=self.user.UserID,
                    totpType=TotpType.Token,
                    totpKey=token.TOTP
                )
                return True
            else:
                return False
        else:
            return False

    def _get_hash_from_tokenId(self, tokenId: str = None) -> bytes:
        if tokenId is None:
            tokenId = self.tokenId

        return base64.b64encode(hashlib.sha256(tokenId.encode('utf-8')).digest())

    def save(self) -> None:
        self._config.log.log(self._config.logStatus.INFO, f"> User ID: {self.user}", ignore=True)

        for t in Token.select(Token.TokenStatus).join(
            Login, on=(Login.TokenID == Token.TokenID),
        ).join(
            User, on=(User.LoginID == Login.LoginID)
        ).where((User.UserID == self.user.UserID) & (
                Token.TokenStatus.is_null() | (Token.TokenStatus != 0)
        )):
            self._config.log.log(self._config.logStatus.DEBUG,
                                 f"Valid token {t.TokenID}; {t.TokenStatus}", ignore=False)
            t.TokenStatus = 0
            t.save()

        self._config.log.log(self._config.logStatus.DEBUG,
                             f"Token ID: {self.tokenId}", ignore=True)

        newToken: Token = Token.get_or_create(
            TokenID=self._get_hash_from_tokenId(),
            TOTP=self.tokenTOTP.totpKey,
            TokenTimeStamp=self._timeStamp,
            PeriodOfValidity=self.tokenConfig.PeriodOfValidity,
            TokenStatus=self.tokenConfig.StayRegistered
        )[0]

        currentUser: User = User.select().where(
            User.UserID == self.user.UserID
        ).get()

        currentLogin: Login = Login.select().where(
            Login.LoginID == currentUser.LoginID
        ).get()

        currentLogin.TokenID = newToken.TokenID
        currentLogin.save()

        self._config.log.log(self._config.logStatus.DEBUG, f"Token successfully saved.", ignore=True)

    def verify(self, totpCode: str, totpId: str = None) -> bool:
        if totpId is not None:
            token = list(Token.select(Token.TOTP).where(Token.TokenID == totpId))[0]
            if len(token) > 0:
                totp = Totp(configuration=self._config, userID=self.tokenId, totpKey=token[0], totpType=TotpType.Token)
                return totp.verify(totpCode)
            return False
        else:
            self._config.log.log(self._config.logStatus.DEBUG, f"tokenTOTP: {self.tokenTOTP.totpKey}; totpCode: {totpCode}")
            return self.tokenTOTP.verify(totpCode)
