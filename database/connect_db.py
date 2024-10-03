import threading
import datetime
import pymysql
import os
import configparser
from misc.logger import Logger

logger = Logger()


LOCK_TH_INI = threading.Lock()


class DBCon:

    def __init__(self):
        self.host = ''
        self.user = ''
        self.password = ''
        self.charset = ''

    def take_settings(self):
        """ Функция загружает данные из settings.ini """

        ret_value = {"RESULT": "ERROR", "DESC": "", "DATA": ""}

        settings_file = configparser.ConfigParser()

        if os.path.isfile("./settings.ini"):
            try:
                with LOCK_TH_INI:  # Блокируем потоки
                    settings_file.read("settings.ini", encoding="utf-8")

                self.host = str(settings_file["BASE"]["HOST"])
                self.user = str(settings_file["BASE"]["USER"])
                self.password = str(settings_file["BASE"]["PASSWORD"])
                self.charset = str(settings_file["BASE"]["CHARSET"])

                ret_value['RESULT'] = "SUCCESS"

            except Exception as ex:
                ret_value['DESC'] = f"{datetime.datetime.now()}\tERROR\tDBCon.take_db_settings\t{ex}"
        else:
            ret_value['DESC'] = f"{datetime.datetime.now()}\tERROR\t" \
                                f"DBCon.take_db_settings\tФайл settings.ini не найден."

        return ret_value

    def connect(self) -> dict:
        """ Возвращает pool в словаре ( ret_value['DATA']['pool'] ) """

        ret_value = {"RESULT": "ERROR", "DESC": "", "DATA": dict()}

        ret_settings = self.take_settings()

        try:
            if ret_settings.get("RESULT") == "SUCCESS":
                ret_value['DATA']['pool'] = pymysql.connect(host=self.host,
                                                              user=self.user,
                                                              password=self.password,
                                                              charset=self.charset,
                                                              cursorclass=pymysql.cursors.DictCursor)
                ret_value['RESULT'] = 'SUCCESS'
            else:
                ret_value = ret_settings
        except Exception as ex:
            msg = f"Исключение в попытке создать подключение к БД: {ex}"
            logger.warning(msg)
            ret_value['DESC'] = msg

        return ret_value
