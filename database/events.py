import pymysql
from datetime import datetime

from database.connect_db import DBCon


TYPE_EVENT_NO_SIG = 38
TYPE_EVENT_ONLINE = 39

# Номер в словаре соответствует FID в БД
exemple_data = {1: {'FID': 1, 'FName': 'Тестовый вход', 'FDescription': '',
                    'FDeviceID': 1, 'FNumberOnDevice': 0, 'FEntranceID': 1, 'FDirectionReaderID': 1,
                    'tdevice.FID': 1,
                    'tdevice.FName': 'Тестовый контроллер 1', 'tdevice.FDescription': 'Создан для тестов',
                    'FTypeDeviceID': 1,
                    'FAddress': '192.168.48.177', 'FPort': 177}}


class EventDB:
    """ Получает из БД данные всех рэле и связи с домофонами (gate_id)"""
    @staticmethod
    def insert(name: str, last_time: str, desc: str, event_type: int) -> dict:
        """ Получить полный список всех считывателей """
        ret_value = {"RESULT": "ERROR", "DESC": "", "DATA": {}}

        db_con = DBCon()
        ret_value = db_con.connect()

        if event_type == TYPE_EVENT_NO_SIG:
            event_msg = f"Контроллер {name} не в сети с {last_time}"
        elif event_type == TYPE_EVENT_ONLINE:
            event_msg = f"Контроллер {name} снова в сети с {last_time}"
        else:
            event_msg = f"Неучтённое событие для контроллера {name} время {last_time}"

        if ret_value["RESULT"] == "SUCCESS":
            connection = ret_value['DATA']['pool']

            try:
                with connection.cursor() as cur:
                    cur.execute(f"insert into vig_sender.tevent (FEventTypeID, FDateEvent, "
                                f"FDateRegistration, FOwnerName, FEventMessage, FEventDescription, FProcessed) "
                                f"values ({event_type}, "
                                f"'{datetime.now()}', "
                                f"'{datetime.now()}', "
                                f"'DeviceDriver.Watcher', "
                                f"'{event_msg}', "
                                f"'{desc}', "
                                f"0)")

                    connection.commit()

                    ret_value['RESULT'] = "SUCCESS"
                    ret_value['DATA'] = {}

            except pymysql.Error as pex:
                ret_value['RESULT'] = "ERROR"
                ret_value['DESC'] = f"Pymysql exception: {pex}"
            except Exception as ex:
                ret_value['RESULT'] = "ERROR"
                ret_value["DESC"] = f"Исключение вызвало: {ex}"

        return ret_value
