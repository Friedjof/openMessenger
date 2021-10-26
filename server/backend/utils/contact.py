# Friedjof Noweck
# 08.09.2021

from core.utils.backend.request import Request

from server.backend.utils.orMapper import *
from server.backend.utils.frequentlyUsedQueries import FrequentlyUsedQueries as FUQ


class OwnContacts:
    def __init__(self, request: Request):
        self.request = request
        self.fuq: FUQ = FUQ()

    def response(self) -> Request:
        owner = self.fuq.get_user_by(token_id=self.request.token["tokenId"]).get()
        contacts = self.fuq.get_user_by(owner_id=owner.UserID)

        request = Request(payload={"contacts": [Contact(user=contact).as_dict() for contact in contacts]})

        return request


class Contact:
    def __init__(self, user: User):
        self._user = user
        self._fuq = FUQ()

        if self._user.OrganisationID is not None:
            self._organisation: Organisation = self._fuq.get_organisation_by(user_id=self._user.UserID).get()
            self._org: dict = {
                "Name": self._organisation.Name,
                "Host": self._organisation.Host,
                "Port": self._organisation.Port
            }
        else:
            self._org = None

    def as_dict(self) -> dict:
        return {
            "UserID": self._user.UserID,
            "Nickname": self._user.Nickname,
            "FirstName": self._user.FirstName,
            "LastName": self._user.LastName,
            "Status": self._user.Status,
            "EMailAddress": self._user.EMailAddress,
            "Organisation": self._org
        }
