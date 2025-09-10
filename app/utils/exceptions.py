class RESTCONFError(Exception):
    """Базовое исключение для RESTCONF"""
    def __init__(self, error_type, error_tag, error_message, status_code=500):
        self.error_type = error_type
        self.error_tag = error_tag 
        self.error_message = error_message
        self.status_code = status_code
        super().__init__(error_message)

class BadRequestError(RESTCONFError):
    """Ошибка 400 - неправильный запрос"""
    def __init__(self, error_tag="invalid-value", error_message="Bad request"):
        super().__init__("application", error_tag, error_message, 400)

class NotFoundError(RESTCONFError):  
    """Ошибка 404 - ресурс не найден"""
    def __init__(self, error_tag="invalid-value", error_message="Resource not found"):
        super().__init__("application", error_tag, error_message, 404)

class ValidationError(RESTCONFError):
    """Ошибка валидации данных"""
    def __init__(self, error_message="Data validation failed"):
        super().__init__("application", "invalid-value", error_message, 400)

class InternalServerError(RESTCONFError):
    """Внутренняя ошибка сервера"""
    def __init__(self, error_message="Internal server error"):
        super().__init__("application", "operation-failed", error_message, 500)
