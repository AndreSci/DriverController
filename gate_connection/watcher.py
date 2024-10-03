import threading
import time
import asyncio

from datetime import datetime
from threading import Thread, Lock
from database.events import EventDB, TYPE_EVENT_NO_SIG, TYPE_EVENT_ONLINE
from misc.logger import Logger
from gate_connection.interface import DeviceInterface
from gate_connection.connection import TIME_OUT_REQUEST
from gate_connection.watcher_data import WatcherDataControl
from gate_connection.models import ReadDataFromHex, ResAnswerData
from gate_connection.cash_data import UpdaterDataBaseCash, DeviceControlData

logger = Logger()

TIME_FOR_UPDATE = 60
TIMEOUT_ASYNC = (1 + TIME_OUT_REQUEST)
DB_UPDATE_LOCK = Lock()
GET_INPUT_STATUS = b'#000000'

FOR_TEST = [{'FID': 1,
             'FName': 'Тестовый контроллер 1',
             'FDescription': 'Создан для тестов (из тестового буфера)',
             'FTypeDeviceID': 1,
             'FAddress': '192.168.48.177',
             'FPort': 177
             }]


class WatcherDeviceState:
    """ Наблюдает за временем последнего удачного конекта устройства """
    def __init__(self):
        self.device_state = {}
        self.device_desc = {}
        self.device_name = {}
        self.msg_sent = {}
        self.last_event_no_sig = {}

        self.thread = threading.Thread(target=self.__event_creator)

    def start_thread(self):
        self.thread.start()

    def update_time(self, fid: int, address: str, port: int, name: str, desc: str):
        self.device_state[fid] = datetime.now()
        self.device_name[fid] = name
        self.device_desc[fid] = f"Url:{address}:{port} Name: {name} Desc: {desc}"
        self.msg_sent[fid] = False

    def first_update_offline(self, fid: int, address: str, port: int, name: str, desc: str):
        """ Заглушка для первого определения """
        if fid not in self.device_state:
            self.device_state[fid] = datetime.now()
            self.device_name[fid] = name
            self.device_desc[fid] = f"Url:{address}:{port} Name: {name} Desc: {desc}"
            self.msg_sent[fid] = False

    def __event_creator(self):

        while True:
            time.sleep(1)
            for_read = self.device_state.copy()  # словарь без вложений хватит внешнего копирования

            if for_read:
                for fid, last_time in for_read.items():
                    try:
                        # Проверяем существует ли данный контроллер в триггере для восстановления связи
                        if fid not in self.last_event_no_sig:
                            self.last_event_no_sig[fid] = False

                        current_time = int((datetime.now() - last_time).total_seconds())

                        if current_time > (TIMEOUT_ASYNC + 2) and not self.msg_sent[fid]:
                            # Отправляем событие, что связь с контроллером потеряна
                            self.set_event(fid, last_time.strftime("%Y-%m-%d %H:%M:%S"),
                                           self.device_desc[fid],
                                           TYPE_EVENT_NO_SIG)
                            self.last_event_no_sig[fid] = True
                        elif current_time < (TIMEOUT_ASYNC + 2):
                            self.msg_sent[fid] = False
                            # Далее проверяем восстановлена связь или же это повторная проверка.
                            if self.last_event_no_sig[fid]:
                                self.last_event_no_sig[fid] = False
                                # Отправляем событие, что контроллер вернулся на связь
                                self.set_event(fid, last_time.strftime("%Y-%m-%d %H:%M:%S"),
                                               self.device_desc[fid],
                                               TYPE_EVENT_ONLINE)
                    except Exception as ex:
                        logger.exception(f"Exception in WatcherDeviceState.__event_creator(): {ex}")

    def set_event(self, fid: int, last_time: str, desc: str, event_type: int) -> dict:
        """ Метод предназначен для добавления события 'нес связи' в БД """
        res_db = EventDB.insert(self.device_name[fid], last_time, desc, event_type)
        self.msg_sent[fid] = True
        return res_db


class WatcherDevice:
    """ Наблюдатель за состоянием контролеров (шлагбаумов)"""

    def __init__(self):

        self.updater_db_cash = UpdaterDataBaseCash()    # Запускаем авто-обновление данных из БД

        self.is_alive = True
        self.device_data_list = []
        self.last_update_data = datetime.now()
        self.first_start = True

        self.result_asking = {}
        self.result_time_asking = {}    # тут записывается последнее время удавшегося запроса
        self.accept_request = {}

        self.watcher_state = WatcherDeviceState()
        self.watcher_state.start_thread()

        self.thread = Thread(target=self.__while_live, daemon=True)

    def start(self) -> bool:
        self.thread.start()

        return True

    def stop(self) -> bool:
        self.is_alive = False

        return True

    def __while_live(self):
        """ Цикл жизни наблюдателя, каждый раз спрашиваем в БД новый список контролеров,
        так же продолжает свою жизнь если нет связи с БД, но были уже ранее получены данные """
        time.sleep(1)

        logger.event(f"Watcher: Начинаю опрос оборудования")
        while self.is_alive:
            time.sleep(0.1)

            thread_list = []

            with DB_UPDATE_LOCK:
                for gate_params in DeviceControlData.get_device_list():
                    if type(gate_params) is dict:
                        fid = gate_params.get('FID')  # передаем дальше этот fid для уменьшения нагрузки
                        # Не пускает выполнять функцию дальше есть та занята на данный момент и завершает поток.
                        if fid in self.accept_request:
                            if self.accept_request[fid]:
                                thread_list.append(Thread(target=self.run_async_ask,
                                                          args=[gate_params, fid], daemon=True))
                        else:
                            # Ничего не теряем если на первой итерации пропустим запрос
                            self.accept_request[fid] = True
                    else:
                        logger.warning(f"ValueType error: "
                                       f"'gate_param' type != dict (current type = {type(gate_params)})")

            for thr in thread_list:
                thr.start()

    def run_async_ask(self, params: dict, fid: int):
        """ Промежуточное звено для запуска асинхронной функции из потока """
        # Блокируем создание нового потока для данного FID
        self.accept_request[fid] = False
        asyncio.run(self.__ask_device_timeout(params))
        # Ожидаем завершение работы функции и открываем доступ для новых потоков по данному FID
        self.accept_request[fid] = True

    async def __ask_device_timeout(self, params: dict):
        """ Добавлено после потери контроля над переменной self.accept_request[fid]
            Убрало коллизию зависания связи """
        try:
            # В процессе тестирования было замечено зависание сокета на бесконечный коннект
            # (timeout должен решить проблему)
            await asyncio.wait_for(self.__ask_device(params), timeout=TIMEOUT_ASYNC)
        except asyncio.TimeoutError:
            print(f"Ошибка выполнения async функции по timeout: __ask_device_timeout({params}) "
                  f"Данная ошибка вызывается когда зависает запрос к устройству.")
        except Exception as ex:
            print(f"Исключение в __ask_device_timeout: {ex}")

    async def __ask_device(self, params: dict):
        """ Функция служит связью с устройством """

        answer = ''
        online_status = 0
        pak_res = {}

        try:
            fid = params.get('FID')

            name = params.get('FName')
            desc = params.get('FDescription')
            type_device = params.get('FTypeDeviceID')
            address = params.get('FAddress')
            port = int(params.get('FPort'))

            res_ask = await DeviceInterface.send_with_params(address, port, GET_INPUT_STATUS)

            if res_ask.get('RESULT') == 'SUCCESS':
                answer = res_ask['DATA'].get('bytes')
                online_status = 1
                pak_res = {}
                self.watcher_state.update_time(fid, address, port, name, desc)
            else:
                self.watcher_state.first_update_offline(fid, address, port, name, desc)

            class_data = ResAnswerData(fid, name, type_device, address, desc, port, online_status, answer, pak_res)

            self.result_asking[fid] = class_data.json()
            WatcherDataControl.update_data(fid, class_data.json())

        except Exception as ex:
            logger.exception(f"Exception in __ask_device: {ex} answer: {answer}")
