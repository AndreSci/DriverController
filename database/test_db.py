""" Функции интерфейса в разработке или в плане """

import pymysql
from database.connect_db import DBCon


class DataReader:
    @staticmethod
    def gen_data(sql_data: dict):
        pass


class PassPeriod:
    @staticmethod
    def get_by_fid(fid: int, start_date: str, end_date: str) -> dict:
        """ Ищет проходы по персоне за период в таблице tpasses """
        ret_value = {"RESULT": "ERROR", "DESC": "", "DATA": {}}

        db_con = DBCon()
        ret_value = db_con.connect()

        if ret_value["RESULT"] == "SUCCESS":
            connection = ret_value['DATA']['pool']

            try:
                with connection.cursor() as cur:
                    cur.execute(f"select * from vig_face.tpasses where "
                                f"FPersonID = {fid} and FDateTimePass between '{start_date}' and '{end_date}'")
                    res = cur.fetchall()

                    ret_value['RESULT'] = "SUCCESS"
                    ret_value['DATA'] = res

            except pymysql.Error as pex:
                ret_value['DESC'] = f"Pymysql exception: {pex}"
            except Exception as ex:
                ret_value["DESC"] = f"Исключение вызвало: {ex}"

        return ret_value


if __name__ == "__main__":
    print(PassPeriod.get_by_fid(154, '2022-05-12', '2022-05-23'))
