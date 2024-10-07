from fastapi import APIRouter, Response, Request
from fastapi.responses import JSONResponse
from typing import Dict

from database.gate_db import GatesDB
from misc.logger import Logger

from gate_connection.interface import DeviceInterface
from gate_connection.cash_data import DeviceControlData
from gate_connection.watcher_data import WatcherDataControl
from datetime import datetime

logger = Logger()

# регистрируем схему `Blueprint`
gates_router = APIRouter(tags=['gates_router_blue'])


@gates_router.get('/PulseDeviceByReader')
async def open_gate_by_reader(fid: int, request: Request) -> Dict:
    """ Функция принимает fid прохода (считывателя)\n
    Таблица связи: vig_access.treader"""

    logger.info(f"Запрос на открытие через считыватель: IP: {request.client.host}:{request.client.port}",
                print_it=False)
    ret_value = {"RESULT": "ERROR", "DESC": '', "DATA": dict()}

    try:
        # Получаем данные считывателя из буфера
        reader_fid = fid
        reader_data = DeviceControlData.get_reader_by_fid(reader_fid)

        if reader_data:
            # Получаем данные контроллера и буфера
            device_fid = reader_data.get('FDeviceID')
            device_data = DeviceControlData.get_device_by_fid(device_fid)

            if device_data:
                # Отправляем запрос на открытие проезда
                device_res = await DeviceInterface.pulse(device_data, int(reader_data.get('FNumberOnDevice')))

                ret_value['RESULT'] = "SUCCESS"
                ret_value['DESC'] = f"Предоставлен доступ {reader_fid}: {device_res}"
            else:
                ret_value['RESULT'] = "WARNING"
                ret_value['DESC'] = f"Не удалось найти связь с контроллером: {device_fid}"
        else:
            ret_value['RESULT'] = "WARNING"
            ret_value['DESC'] = f"Не удалось найти считыватель: {reader_fid}"

        logger.warning(ret_value['DESC'])

    except Exception as ex:
        msg = f"Exception in: {ex}"
        ret_value['DESC'] = msg
        logger.exception(msg)

    return JSONResponse(ret_value)


@gates_router.get('/PulseByCameraID')
async def pulse_by_camera(fid: int, request: Request, relay_num: int = None) -> Dict:
    """Отправить запрос на действие с реле на контроллере по FID камеры.\n
    Таблица связи: vig_access.tdevicecameragroups"""

    logger.info(f"Запрос на открытие через считыватель: IP: {request.client.host}:{request.client.port}",
                print_it=False)
    ret_value = {"RESULT": "NOTDEFINE", "DESC": "", "DATA": {}}

    # Получаем данные контроллера из буфера
    device_data = DeviceControlData.get_device_by_camera(fid)

    if device_data:
        try:
            start_time = datetime.now()
            if relay_num:
                device_answer = await DeviceInterface.pulse(device_data, relay_num)
            else:
                device_answer = await DeviceInterface.pulse(device_data, 0)
            total_sec = (datetime.now() - start_time).total_seconds()

            device_answer['req_time_speed'] = total_sec

            ret_value['RESULT'] = "SUCCESS"
            ret_value['DATA'] = device_answer
        except Exception as ex:
            ret_value['RESULT'] = "ERROR"
            ret_value['DESC'] = "При попытке отправить запрос на открытие проезда возникла ошибка"
            logger.warning(f"Exception in router.pulse_by_camera(): {ex}")

    else:
        ret_value['RESULT'] = "WARNING"
        ret_value['DESC'] = "Для данной камеры нет устройства управления проездом"

    return JSONResponse(ret_value)


# Метод создан для Asterisk скрипта
@gates_router.get('/PulseByCallerID')
async def pulse_by_caller(caller_name: str, request: Request, relay_num: int = None) -> Dict:
    """Отправить запрос на действие с реле на контроллере по имени 'FName' абонента.\n
    Таблицы связей: vig_sender.tasteriskcaller -> vig_sender.tcamera -> vig_sender.tcameragroups"""

    logger.info(f"Запрос на открытие через считыватель: IP: {request.client.host}:{request.client.port}",
                print_it=False)
    ret_value = {"RESULT": "NOTDEFINE", "DESC": "", "DATA": {}}

    # Получаем данные контроллера из буфера
    # получаем fid абонента по имени
    caller_id = DeviceControlData.get_asterisk_callers_id(caller_name)
    # получаем fid камеры по fid абонента
    camera_id = DeviceControlData.get_fid_camera_by_caller(caller_id)
    # получаем данные устройства по fid камеры
    device_data = DeviceControlData.get_device_by_camera(camera_id)

    if device_data:
        try:
            if relay_num:
                device_answer = await DeviceInterface.pulse(device_data, relay_num)
            else:
                device_answer = await DeviceInterface.pulse(device_data, 0)

            ret_value['RESULT'] = "SUCCESS"
            ret_value['DATA'] = device_answer
        except Exception as ex:
            ret_value['RESULT'] = "ERROR"
            ret_value['DESC'] = (f"При попытке отправить запрос на открытие "
                                 f"проезда возникла ошибка {caller_id} {camera_id} {device_data}")
            logger.warning(f"Exception in router.pulse_by_caller(): {ex}")

    else:
        ret_value['RESULT'] = "WARNING"
        ret_value['DESC'] = "Для данной камеры нет устройства управления проездом"

    logger.info(ret_value)

    return JSONResponse(ret_value)


@gates_router.get('/StateByCameraID')
async def get_by_camera(fid: int) -> Dict:
    """ Запрос возвращает состояние контроллера который связан с камерой.\n
    Таблица связи камеры и контроллера: vig_access.tdevicecameragroups"""

    ret_value = {"RESULT": "NOTDEFINE", "DESC": "", "DATA": {}}

    device_data = DeviceControlData.get_device_by_camera(fid)

    if device_data:
        try:
            # device_answer = await DeviceInterface.state(device_data)

            device_answer = WatcherDataControl.get_data_by_fid(device_data.get('FID'))

            ret_value['RESULT'] = "SUCCESS"
            ret_value['DATA'] = device_answer
        except Exception as ex:
            ret_value['RESULT'] = "ERROR"
            ret_value['DESC'] = "При попытке отправить запрос на открытие проезда возникла ошибка"
            logger.exception(f"Exception in router.StateByCameraID(): {ex}")

    else:
        ret_value['RESULT'] = "WARNING"
        ret_value['DESC'] = "Для данной камеры нет устройства управления проездом"

    return JSONResponse(ret_value)


# ADDITION FUNCTIONS ----------------------------------------------
@gates_router.get('/ManualControlDevice')
async def manual_control_device(request: Request,
                                fid: int = None,
                                host: str = None, port: str = None,
                                byte_code: str = '#000000') -> Dict:

    """ Случай когда нужно обратиться к контроллеру напрямую.\n
    Если не указать byte_code ответом будет статус устройства.\n
    1. Данные для запроса по FID: fid=4 и byte_code = '#000000'\n
    2. Данные для запроса по IP: host=192.168.15.177 port=177 byte_code = '#000000'\n
    '#000000' = команда на получение статуса контроллера. """

    logger.info(f"Запрос для ручного управления: IP: {request.client.host}:{request.client.port}", print_it=False)
    ret_value = {"RESULT": "NOTDEFINE", "DESC": "", "DATA": {}}

    logger.info(f"Request данные: fid:{fid}, host:{host}, port:{port}, byte_code:{byte_code}", print_it=False)

    try:
        if fid:
            device = DeviceControlData.get_device_by_fid(fid)
        elif host and port:
            device = {'FAddress': host, 'FPort': port}
        else:
            ret_value['RESULT'] = 'WARNING'
            ret_value['DESC'] = "В json не удалось найти данные устройства"
            return JSONResponse(ret_value)

        ret_value = await DeviceInterface.send_bytes(device, byte_code)

        ret_value['details'] = device

    except Exception as ex:
        ret_value['RESULT'] = "EXCEPTION"
        ret_value['DESC'] = f"Не удалось обработать данные запроса: {ex}"
        logger.exception(f"Исключение в запросе: {ex}")

    return JSONResponse(ret_value)


# ----------------------------------------------------------------

@gates_router.get('/GetBarrierState')
async def get_state_barrier(fid: int) -> Dict:
    """ Функция принимает FID Barrier,
    так же есть возможность получить статус всех Barrier одновременно
    если указать fid -1 или любой другой меньше нуля."""

    ret_value = {"RESULT": "ERROR", "DESC": '', "DATA": dict()}

    try:
        if fid >= 0:
            ret_value['DATA'] = {fid: WatcherDataControl.get_data_by_fid(fid)}
        else:
            ret_value['DATA'] = WatcherDataControl.get_all()

        ret_value['RESULT'] = "SUCCESS"

    except Exception as ex:
        msg = f"Exception in: {ex}"
        ret_value['DESC'] = msg
        logger.exception(msg)

    return JSONResponse(ret_value)


@gates_router.post('/ActionAddCards')
async def add_cards(request: Request) -> Dict:
    """ Функция принимает fid прохода (считывателя) и дополнительно JSON, где содержится список карт """

    ret_value = {"RESULT": "ERROR", "DESC": '', "DATA": list()}

    cards_guid = await request.json()

    try:
        # Получаем список устройств
        if cards_guid.get('FAddress'):
            device_data_list = dict()
            device_data_list['DATA'] = [{'FName': 'Без имени',
                                          'FDescription': 'Ручной ввод адреса контроллера',
                                          'FAddress': f"{cards_guid.get('FAddress')}",
                                          'FPort': cards_guid.get('FPort')}
                                        ]
        else:
            device_data_list = GatesDB.get_devices()

        logger.info(device_data_list)

        for card_guid in cards_guid.get('cards'):
            for controller in device_data_list['DATA']:
                ret_value['DATA'].append(DeviceInterface.send_add_card(controller.get('FAddress'),
                                                                       controller.get('FPort'),
                                                                       card_guid))

    except Exception as ex:
        msg = f"Exception in: {ex}"
        ret_value['DESC'] = msg
        logger.exception(msg)

    return JSONResponse(ret_value)
