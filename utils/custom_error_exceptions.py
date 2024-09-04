from rest_framework.exceptions import APIException

class UserNotStaffException(APIException):
    status_code = 400
    default_detail = "L'utilisateur doit être un staff."
    default_code = "USER_NOT_STAFF"


class UserInvalidGroupException(APIException):
    status_code = 400
    default_detail = "Présence d'un groupe d'utilisateur invalide."
    default_code = "USER_INVALID_GROUP"