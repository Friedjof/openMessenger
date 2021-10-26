# Friedjof Noweck
# 09.09.2021 Do

from core.utils.backend.request import Request, RequestTypes, RequestStatus

from server.backend.utils.frequentlyUsedQueries import FrequentlyUsedQueries as FUQ
from server.backend.utils.orMapper import *


class UserRequests:
    def __init__(self, request: Request):
        self.request = request
        self.fuq = FUQ()

    def response(self) -> Request:
        keys = self.request.payload.keys()
        if self.request.payload == {}:
            return self.getStatus()
        elif "status" in keys:
            return self.setStatus(status=self.request.payload["status"])
        else:
            return Request(
                payload={},
                requestType=RequestTypes.Status,
                requestStatus=RequestStatus.RequestFormatError
            )

    def getStatus(self):
        user: User = self.fuq.get_user_by(token_id=self.request.token["tokenId"]).get()
        return Request(
            payload={"status": user.Status},
            requestStatus=RequestStatus.Successful,
            requestType=RequestTypes.Response
        )

    def setStatus(self, status) -> Request:
        user: User = self.fuq.get_user_by(token_id=self.request.token["tokenId"]).get()
        user.Status = status
        user.save()

        return Request(
            payload={"status": status},
            requestStatus=RequestStatus.Successful,
            requestType=RequestTypes.Response
        )
