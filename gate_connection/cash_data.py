import pprint
import threading
import time
from datetime import datetime
from database.gate_db import GatesDB
from misc.logger import Logger

from gate_connection.models import DeviceData

logger = Logger()

UPDATE_TIME_DATA_CASH = 120


class CashGroupCameraDevice:
    """ Класс служить для кэширования данных из БД для таблицы tdevicecameragroups """

    def __init__(self):
        self.data = dict()
        self.time_update = datetime.now()

    def add(self, camera_fid: int, device_fid: int):
        self.data[camera_fid] = device_fid

    def add_all(self, groups: list):
        data = dict()
        for it in groups:
            camera_fid = it.get('FCameraID')
            device_fid = it.get('FDeviceID')
            data[camera_fid] = device_fid

        self.data = data

    def get_by_camera(self, camera_fid: int) -> int:
        return self.data.get(camera_fid)

    def get_by_device(self, device_fid: int) -> int:
        return self.data.get(device_fid)


class CashDevice:
    """ Класс служит для кэширования данных из БД для таблицы tdevice """

    def __init__(self):
        self.data = dict()
        self.data_list = list()
        self.time_update = datetime.now()

    def add(self, device_data: dict):
        fid = device_data.get('FID')
        self.data[fid] = device_data

    def add_all(self, devices_data: list):
        self.data_list = devices_data
        data = dict()

        for it in devices_data:
            device_fid = it.get('FID')
            data[device_fid] = it

        self.data = data

    def get(self, device_fid: int) -> dict:
        return self.data.get(device_fid)

    def get_list(self) -> list:
        return self.data_list


class CashReader:
    """ Класс отвечает за кэширование данных из БД для таблицы treader """
    def __init__(self):
        self.data = dict()
        self.data_list = list()

    def add_all(self, readers_data: list):
        self.data_list = readers_data
        data = dict()

        for it in readers_data:
            device_fid = it.get('FID')
            data[device_fid] = it

        self.data = data

    def get(self, reader_fid: int) -> dict:
        return self.data.get(reader_fid)

    def get_list(self) -> list:
        return self.data_list


class CashAsteriskCallers:
    def __init__(self):
        self.data = dict()

    def add_all(self, callers_data: dict):
        self.data = callers_data

    def get(self, caller_name: str) -> int:
        return self.data.get(caller_name)


class CashAsteriskCameraGroup:
    def __init__(self):
        self.data = dict()

    def add_all(self, group_data: dict):
        self.data = group_data

    def get(self, caller_id: int) -> int:
        return self.data.get(caller_id)


CASH_GROUPS = CashGroupCameraDevice()
CASH_DEVICES = CashDevice()
CASH_READER = CashReader()
CASH_ASTERISK = CashAsteriskCallers()
CASH_CAM_AST_GROUP = CashAsteriskCameraGroup()


class UpdaterDataBaseCash:
    """ Класс служит для обновления данных из БД и кэширования их в Глобальные переменные """

    def __init__(self):
        self.time_update = datetime.now()
        self.first_time = True

        tr = threading.Thread(target=self.update_while, daemon=True)
        tr.start()

    def update_while(self):
        global CASH_GROUPS
        global CASH_DEVICES
        global CASH_READER
        global CASH_ASTERISK
        global CASH_CAM_AST_GROUP

        while True:
            time.sleep(5)

            if int((datetime.now() - self.time_update).total_seconds()) > UPDATE_TIME_DATA_CASH or self.first_time:
                self.first_time = False

                try:

                    # Получаем данные для связи камер и устройств
                    groups_res = GatesDB.get_camera_device_groups()

                    if groups_res.get('RESULT') == "SUCCESS":
                        CASH_GROUPS.add_all(groups_res.get('DATA'))
                    else:
                        logger.warning(f"Не удалось обновить данные: {groups_res}")

                    # Получаем список всех устройств
                    devices_res = GatesDB.get_devices()

                    if devices_res.get('RESULT') == "SUCCESS":
                        CASH_DEVICES.add_all(devices_res.get('DATA'))
                    else:
                        logger.warning(f"Не удалось обновить данные: {devices_res}")

                    # Получаем список всех считывателей
                    reader_res = GatesDB.get_readers()

                    if reader_res.get('RESULT') == "SUCCESS":
                        CASH_READER.add_all(reader_res.get('DATA'))
                    else:
                        logger.warning(f"Не удалось обновить данные: {reader_res}")

                    # Получаем список всех абонентов Астериск
                    callers_res = GatesDB.get_asterisk_callers()

                    if callers_res.get('RESULT') == "SUCCESS":
                        CASH_ASTERISK.add_all(callers_res.get('DATA'))
                    else:
                        logger.warning(f"Не удалось обновить данные: {callers_res}")

                    # Получаем список групп связывающие абонентов Астериск с камерами
                    cam_ast_group_res = GatesDB.get_asterisk_camera_group()

                    if cam_ast_group_res.get('RESULT') == "SUCCESS":
                        CASH_CAM_AST_GROUP.add_all(cam_ast_group_res.get('DATA'))
                    else:
                        logger.warning(f"Не удалось обновить данные: {cam_ast_group_res}")

                    self.time_update = datetime.now()
                except Exception as ex:
                    logger.exception(f"Exception in UpdaterCash.watcher: {ex}")


class DeviceControlData:
    @staticmethod
    def get_device_by_camera(camera_fid: int) -> DeviceData:
        """ Данные контроллера: поиск по FID камеры. """
        device_fid = CASH_GROUPS.get_by_camera(camera_fid)

        ret_value = DeviceData()
        ret_value.update_from(CASH_DEVICES.get(device_fid))

        return ret_value

    @staticmethod
    def get_device_by_fid(device_fid: int) -> DeviceData:
        """ Данные контроллера: поиск по FID контроллера. """
        ret_value = DeviceData()
        ret_value.update_from(CASH_DEVICES.get(device_fid))

        return ret_value

    @staticmethod
    def get_reader_by_fid(reader_fid: int) -> dict:
        """ Данные считывателя: поиск по FID считывателя. """
        return CASH_READER.get(reader_fid)

    @staticmethod
    def get_device_list() -> list:
        """ Полный список всех контроллеров из БД. """
        return CASH_DEVICES.get_list()

    @staticmethod
    def get_asterisk_callers_id(caller_name: str) -> int:
        """ Возвращает FID абонента астериск. """
        return CASH_ASTERISK.get(caller_name)

    @staticmethod
    def get_fid_camera_by_caller(caller_fid: int) -> int:
        """ Возвращает FID камеры связанной с абонентом по FID """
        return CASH_CAM_AST_GROUP.get(caller_fid)

    @staticmethod
    def print_all():
        print(CASH_DEVICES.data)
        print(CASH_GROUPS.data)
        print(CASH_READER.data)
        print(CASH_ASTERISK.data)
        print(CASH_CAM_AST_GROUP.data)
