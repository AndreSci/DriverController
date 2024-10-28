from typing import Union, Any


class StatusType:
    SUCCESS = "SUCCESS"
    ERROR = "ERROR"
    WARNING = "WARNING"
    EXCEPTION = "EXCEPTION"
    NOT_DEFINE = "NOTDEFINE"


class UnionType:
    """ Для определения типа данных в разделе data """
    dict = "dict"
    list = "list"
    not_def = "not_defined"


class RetValue:
    def __init__(self):
        self.status = StatusType.NOT_DEFINE
        self.desc = ''
        self.data_type = UnionType.not_def
        self.data = {}
        self.details = None

    def __update_data(self, status: str, desc: Any = None, data: Union[dict, list] = None):
        try:
            self.status = status

            if desc:
                self.desc += f"{desc}"

            if data:
                if type(data) is dict:
                    self.data_type = UnionType.dict
                elif type(data) is list:
                    self.data_type = UnionType.list
                else:
                    self.data_type = UnionType.not_def

                self.data = data

            else:
                self.data_type = UnionType.not_def
                self.data = {}

        except Exception as ex:
            print(f"Exception in: {ex}")

    def change_desc(self, desc: Any):
        self.desc = f"{desc}"

    def add_details(self, details: Any):
        """ Дополнительные данные не входящие в self.data """
        self.details = details

    def success(self, desc:str = None, data: Union[dict, list] = None):
        self.__update_data(StatusType.SUCCESS, desc, data)

    def error(self, desc:str = None, data: Union[dict, list] = None):
        self.__update_data(StatusType.ERROR, desc, data)

    def warning(self, desc:str = None, data: Union[dict, list] = None):
        self.__update_data(StatusType.WARNING, desc, data)

    def exception(self, desc:str = None, data: Union[dict, list] = None):
        self.__update_data(StatusType.EXCEPTION, desc, data)

    def respond(self) -> dict:
        """ Функция возвращает подготовленный словарь для http ответа json """
        no_desc = ""

        ret_value = {"RESULT": self.status,
                        "DESC": (lambda x, y: x if x else y)(self.desc, no_desc),
                        "TYPE_DATA": self.data_type,
                        "DATA": self.data}

        if self.details:
            ret_value['details'] = self.details

        return ret_value


if __name__ == "__main__":

    res = RetValue()

    res.success("some_text_success", {"a": 1})
    print(res.respond())

    res = RetValue()

    res.error("some_text_error", {"a": 1})
    print(res.respond())

    res = RetValue()

    res.exception("some_text_exception", [1,2,3])
    print(res.respond())

    res = RetValue()

    res.exception("some_text_exception", [])
    print(res.respond())

    res = RetValue()

    res.exception()
    print(res.respond())
