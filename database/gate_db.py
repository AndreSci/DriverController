import threading
import time

import pymysql
from datetime import datetime

from database.connect_db import DBCon


# Номер типа для шлагбаума
TYPE_DEVICE = 3

# Номер в словаре соответствует FID в БД
exemple_data = {1: {'FID': 1, 'FName': 'Тестовый вход', 'FDescription': '',
                    'FDeviceID': 1, 'FNumberOnDevice': 0, 'FEntranceID': 1, 'FDirectionReaderID': 1,
                    'tdevice.FID': 1,
                    'tdevice.FName': 'Тестовый контроллер 1', 'tdevice.FDescription': 'Создан для тестов',
                    'FTypeDeviceID': 1,
                    'FAddress': '192.168.48.177', 'FPort': 177}}


class GatesDB:
    """ Получает из БД данные всех рэле и связи с домофонами (gate_id)"""
    @staticmethod
    def get_readers() -> dict:
        """ Получить полный список всех считывателей """
        ret_value = {"RESULT": "ERROR", "DESC": "", "DATA": list()}

        db_con = DBCon()
        ret_value = db_con.connect()

        if ret_value["RESULT"] == "SUCCESS":
            connection = ret_value['DATA']['pool']

            try:
                with connection.cursor() as cur:
                    cur.execute(f"SELECT * FROM vig_access.treader")
                    res = cur.fetchall()

                    ret_value['RESULT'] = "SUCCESS"
                    ret_value['DATA'] = res

            except pymysql.Error as pex:
                ret_value['DESC'] = f"Pymysql exception: {pex}"
            except Exception as ex:
                ret_value["DESC"] = f"Исключение вызвало: {ex}"

        return ret_value

    @staticmethod
    def get_devices() -> dict:
        """ Получить список все устройств/контроллеров из БД по типу """
        ret_value = {"RESULT": "ERROR", "DESC": "", "DATA": list()}

        db_con = DBCon()
        ret_value = db_con.connect()

        if ret_value["RESULT"] == "SUCCESS":
            connection = ret_value['DATA']['pool']

            try:
                with connection.cursor() as cur:
                    cur.execute(f"SELECT * FROM vig_access.tdevice where FTypeDeviceID = {TYPE_DEVICE}")
                    res = cur.fetchall()

                    ret_value['RESULT'] = "SUCCESS"
                    ret_value['DATA'] = res

            except pymysql.Error as pex:
                ret_value['DESC'] = f"Pymysql exception: {pex}"
            except Exception as ex:
                ret_value["DESC"] = f"Исключение вызвало: {ex}"

        return ret_value

    @staticmethod
    def get_camera_device_groups() -> dict:
        """ Получить полный список всех групп камера/контроллер """

        ret_value = {"RESULT": "ERROR", "DESC": "", "DATA": {}}

        db_con = DBCon()
        ret_value = db_con.connect()

        if ret_value["RESULT"] == "SUCCESS":
            connection = ret_value['DATA']['pool']

            try:
                with connection.cursor() as cur:
                    cur.execute(f"SELECT * FROM vig_access.tdevicecameragroups")
                    res = cur.fetchall()

                    ret_value['RESULT'] = "SUCCESS"
                    ret_value['DATA'] = res

            except pymysql.Error as pex:
                ret_value['DESC'] = f"Pymysql exception: {pex}"
            except Exception as ex:
                ret_value["DESC"] = f"Исключение вызвало: {ex}"

        return ret_value

    # Additional functions ---------------------------------
    @staticmethod
    def get_by_reader(fid: int) -> dict:
        """ Принимает fid считывателя и ищет связанный с ним контроллер """

        ret_value = {"RESULT": "ERROR", "DESC": "", "DATA": {}}

        db_con = DBCon()
        ret_value = db_con.connect()

        if ret_value["RESULT"] == "SUCCESS":
            connection = ret_value['DATA']['pool']

            try:
                with connection.cursor() as cur:
                    cur.execute(f"SELECT * FROM vig_access.treader, vig_access.tdevice "
                                f"WHERE vig_access.treader.FID = {fid} AND vig_access.tdevice.FID = FDeviceID")
                    res = cur.fetchone()

                    ret_value['RESULT'] = "SUCCESS"
                    ret_value['DATA'] = res

            except pymysql.Error as pex:
                ret_value['DESC'] = f"Pymysql exception: {pex}"
            except Exception as ex:
                ret_value["DESC"] = f"Исключение вызвало: {ex}"

        return ret_value

    @staticmethod
    def get_device(fid: int) -> dict:
        """ Получить устройство/контроллер по FID """
        ret_value = {"RESULT": "ERROR", "DESC": "", "DATA": list()}

        db_con = DBCon()
        ret_value = db_con.connect()

        if ret_value["RESULT"] == "SUCCESS":
            connection = ret_value['DATA']['pool']

            try:
                with connection.cursor() as cur:
                    cur.execute(f"SELECT * FROM vig_access.tdevice where FID = {fid}")
                    res = cur.fetchall()

                    if res:
                        ret_value['RESULT'] = "SUCCESS"
                        ret_value['DATA'] = res

            except pymysql.Error as pex:
                ret_value['DESC'] = f"Pymysql exception: {pex}"
            except Exception as ex:
                ret_value["DESC"] = f"Исключение вызвало: {ex}"

        return ret_value

    @staticmethod
    def get_by_camera(fid: int) -> dict:
        """ Принимает fid камеры """

        ret_value = {"RESULT": "ERROR", "DESC": "", "DATA": {}}

        db_con = DBCon()
        ret_value = db_con.connect()

        if ret_value["RESULT"] == "SUCCESS":
            connection = ret_value['DATA']['pool']

            try:
                with connection.cursor() as cur:
                    cur.execute(f"SELECT FDeviceID FROM vig_access.tdevicecameragroups WHERE FCameraID = {fid}")
                    res = cur.fetchall()

                    ret_value['RESULT'] = "SUCCESS"
                    ret_value['DATA'] = res

            except pymysql.Error as pex:
                ret_value['DESC'] = f"Pymysql exception: {pex}"
            except Exception as ex:
                ret_value["DESC"] = f"Исключение вызвало: {ex}"

        return ret_value

    @staticmethod
    def get_asterisk_callers() -> dict:
        """ Получить полный список всех в виде словаря абонентов Астериск """

        ret_value = {"RESULT": "ERROR", "DESC": "", "DATA": {}}

        db_con = DBCon()
        ret_value = db_con.connect()

        if ret_value["RESULT"] == "SUCCESS":
            connection = ret_value['DATA']['pool']

            try:
                with connection.cursor() as cur:
                    cur.execute(f"SELECT * FROM vig_sender.tasteriskcaller")
                    res = cur.fetchall()

                    result = dict()

                    for item in res:
                        result[item.get("FName")] = item.get("FID")

                    ret_value['RESULT'] = "SUCCESS"
                    ret_value['DATA'] = result

            except pymysql.Error as pex:
                ret_value['DESC'] = f"Pymysql exception: {pex}"
            except Exception as ex:
                ret_value["DESC"] = f"Исключение вызвало: {ex}"

        return ret_value

    @staticmethod
    def get_asterisk_camera_group() -> dict:
        """ Получить полный список в виде словаря для связи камер и абонентов астериск """

        ret_value = {"RESULT": "ERROR", "DESC": "", "DATA": {}}

        db_con = DBCon()
        ret_value = db_con.connect()

        if ret_value["RESULT"] == "SUCCESS":
            connection = ret_value['DATA']['pool']

            try:
                with connection.cursor() as cur:
                    cur.execute(f"SELECT * FROM vig_sender.tcameragroups")
                    res = cur.fetchall()

                    result = dict()

                    for item in res:
                        result[item.get("FAsteriskCallerID")] = item.get("FCameraID")

                    ret_value['RESULT'] = "SUCCESS"
                    ret_value['DATA'] = result

            except pymysql.Error as pex:
                ret_value['DESC'] = f"Pymysql exception: {pex}"
            except Exception as ex:
                ret_value["DESC"] = f"Исключение вызвало: {ex}"

        return ret_value


if __name__ == "__main__":
    print(GatesDB.get_by_reader(1))
    time.sleep(1)
    print(GatesDB.get_by_reader(1))
    time.sleep(1)
    print(GatesDB.get_devices())
