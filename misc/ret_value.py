

class StatusType:
    SUCCESS = "SUCCESS"
    ERROR = "ERROR"
    WARNING = "WARNING"
    EXCEPTION = "EXCEPTION"
    NOT_DEFINE = "NOT DEFINE"


class RetValue:
    def __init__(self):
        self.status = StatusType.NOT_DEFINE
        self.desc = ''
        self.data = {}

    def __update_data(self, status: str, desc:str, data:str):
        try:
            self.status = status

            if desc:
                if type(desc) is str:
                    self.desc = desc
                else:
                    self.desc = "Ошибка типа данных для создания описания"

            if data:
                if type(data) is dict:
                    self.data = data
                else:
                    self.

        except Exception as ex:
            print(f"Exception in: {ex}")

    def success(self, desc:str = None, data:dict = None):
        self.__update_data(StatusType.SUCCESS, desc, data)
