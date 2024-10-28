from fastapi import APIRouter, Response, Request
from fastapi.responses import JSONResponse
from typing import Dict

from database.gate_db import GatesDB
from misc.logger import Logger
from misc.ret_value import RetValue

from gate_connection.models import DeviceData
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
    Таблица связи: vig_access.treader """

    logger.info(f"Запрос на открытие через считыватель: "
                f"IP: {request.client.host}:{request.client.port} - fid: {fid}",
                print_it=False)

    # ret_value = {"RESULT": "ERROR", "DESC": '', "DATA": dict()}
    ret_value = RetValue()

    try:
        # Получаем данные считывателя из буфера
        reader_fid = fid
        reader_data = DeviceControlData.get_reader_by_fid(reader_fid)

        if reader_data:
            # Получаем данные контроллера и буфера
            device_fid = reader_data.get('FDeviceID')
            device_data = DeviceControlData.get_device_by_fid(device_fid)

            if device_data.address:
                device_data.reader_name = reader_data.get("FName")
                # Отправляем запрос на открытие проезда
                device_res = await DeviceInterface.pulse(device_data, int(reader_data.get('FNumberOnDevice')))

                # ret_value['RESULT'] = "SUCCESS"
                # ret_value['DESC'] = f"Предоставлен доступ {reader_fid}: {device_res}"
                # ret_value['DATA'] = device_res
                ret_value.success(desc=f"Предоставлен доступ {reader_fid}: {device_res}", data=device_res)
            else:
                # ret_value['RESULT'] = "WARNING"
                # ret_value['DESC'] = f"Не удалось найти связь с контроллером: {device_fid}"
                ret_value.warning(desc=f"Не удалось найти связь с контроллером: {device_fid}")
        else:
            # ret_value['RESULT'] = "WARNING"
            # ret_value['DESC'] = f"Не удалось найти считыватель: {reader_fid}"
            ret_value.warning(desc=f"Не удалось найти считыватель: {reader_fid}")

        logger.event(ret_value.respond())

    except Exception as ex:
        msg = f"Exception in: {ex}"
        # ret_value['DESC'] = "Не удалось получить данные от контроллера. При запросе возникла ошибка в драйвере."
        ret_value.exception(desc="Не удалось получить данные от контроллера. При запросе возникла ошибка в драйвере.")
        logger.exception(msg)

    return JSONResponse(ret_value.respond())


@gates_router.get('/PulseByCameraID')
async def pulse_by_camera(fid: int, request: Request, relay_num: int = None) -> Dict:
    """Отправить запрос на действие с реле на контроллере по FID камеры.\n
    Таблица связи: vig_access.tdevicecameragroups """

    logger.info(f"Запрос на открытие через считыватель: "
                f"IP: {request.client.host}:{request.client.port} - fid: {fid} relay_num: {relay_num}",
                print_it=False)

    ret_value = RetValue()

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

            ret_value.success(data=device_answer)
        except Exception as ex:
            ret_value.exception(desc="При попытке отправить запрос на открытие проезда возникла ошибка")
            logger.warning(f"Exception in router.pulse_by_camera(): {ex}")

    else:
        ret_value.warning(desc="Для данной камеры нет устройства управления проездом")

    logger.event(ret_value.respond())

    return JSONResponse(ret_value.respond())


# Метод создан для Asterisk скрипта
@gates_router.get('/PulseByCallerID')
async def pulse_by_caller(caller_name: str, request: Request, relay_num: int = None) -> Dict:
    """Отправить запрос на действие с реле на контроллере по имени 'FName' абонента.\n
    Таблицы связей: vig_sender.tasteriskcaller -> vig_sender.tcamera -> vig_sender.tcameragroups """

    logger.info(f"Запрос на открытие через считыватель: IP: {request.client.host}:{request.client.port}",
                print_it=False)

    ret_value = RetValue()

    device_data = DeviceData()
    caller_id = None
    camera_id = None

    # Получаем данные контроллера из буфера
    try:
        # получаем fid абонента по имени
        caller_id = DeviceControlData.get_asterisk_callers_id(caller_name)
        # получаем fid камеры по fid абонента
        camera_id = DeviceControlData.get_fid_camera_by_caller(caller_id)
        # получаем данные устройства по fid камеры
        device_data = DeviceControlData.get_device_by_camera(camera_id)
    except Exception as ex:
        msg = f"Не удалось получить данные для абонента: {caller_name} - {ex}"
        logger.warning(msg)

    if device_data.address:
        try:
            if relay_num:
                device_answer = await DeviceInterface.pulse(device_data, relay_num)
            else:
                device_answer = await DeviceInterface.pulse(device_data, 0)

            ret_value.success(data=device_answer)
        except Exception as ex:
            ret_value.exception(desc=(f"При попытке отправить запрос на открытие "
                                        f"проезда возникла ошибка {caller_id} {camera_id} {device_data}"))
            logger.warning(f"Exception in router.pulse_by_caller(): {ex}")

    else:
        ret_value.warning(desc="Для данного абонента нет устройства управления проездом")

    logger.event(ret_value.respond())

    return JSONResponse(ret_value.respond())


@gates_router.get('/StateByCameraID')
async def get_by_camera(fid: int) -> Dict:
    """ Запрос возвращает состояние контроллера который связан с камерой.\n
    Таблица связи камеры и контроллера: vig_access.tdevicecameragroups """

    ret_value = RetValue()

    device_data = DeviceData()

    try:
        device_data = DeviceControlData.get_device_by_camera(fid)
    except Exception:
        # Пропускаем из-за множественных запросов к этому методу
        pass

    if device_data.address:
        try:
            # device_answer = await DeviceInterface.state(device_data)

            device_answer = WatcherDataControl.get_data_by_fid(device_data.fid)

            ret_value.success(data=device_answer)
        except Exception as ex:
            ret_value.exception(desc="При попытке отправить запрос на открытие проезда возникла ошибка")
            logger.exception(f"Exception in router.StateByCameraID(): {ex}")

    else:
        ret_value.warning(desc="Для данной камеры нет устройства управления проездом")

    return JSONResponse(ret_value.respond())


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

    logger.info(f"Запрос для ручного управления: IP: {request.client.host}:{request.client.port}")

    ret_value = RetValue()

    logger.info(f"Request данные: fid:{fid}, host:{host}, port:{port}, byte_code:{byte_code}", print_it=False)

    try:
        if fid:
            device_data = DeviceControlData.get_device_by_fid(fid)
        elif host and port:
            device_dict = {'FAddress': host, 'FPort': port, "FID": -1}
            device_data = DeviceData()
            device_data.update_from(device_dict)
        else:
            ret_value.warning(desc=f"Не удалось получить данные из запроса: fid:{fid} или host:{host} - port:{port}")
            return JSONResponse(ret_value.respond())

        ret_device = await DeviceInterface.send_bytes(device_data, byte_code)

        ret_value.success(desc=ret_device.get('DESC'), data=ret_device.get('DATA'))
        ret_value.add_details(device_data.get_dict())

    except Exception as ex:
        ret_value.exception(desc=f"Не удалось обработать данные запроса: {ex}")
        logger.exception(f"Исключение в запросе: {ex}")

    return JSONResponse(ret_value.respond())


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
    # В ТЕСТЕ
    """ Функция принимает JSON, где содержится список новых карт (GUID).
    Можно вручную указать устройство где требуется определить (FAddress = 127.0.0.1 и FPort = 177).
    Если не указывать данные, будет получен полный список контроллеров из БД
    и карты будут добавлены во все контроллеры. """

    ret_value = {"RESULT": "ERROR", "DESC": '', "DATA": list()}

    json_req = await request.json()

    try:
        # Получаем список устройств
        if json_req.get('FAddress'):
            device_data_list = dict()
            device_data_list['DATA'] = [{'FName': 'Без имени',
                                          'FDescription': 'Ручной ввод адреса контроллера',
                                          'FAddress': f"{json_req.get('FAddress')}",
                                          'FPort': json_req.get('FPort')}
                                        ]
        else:
            device_data_list = GatesDB.get_devices()

        logger.info(device_data_list)

        for card_guid in json_req.get('cards'):
            for controller in device_data_list['DATA']:
                ret_value['DATA'].append(DeviceInterface.send_add_card(controller.get('FAddress'),
                                                                       controller.get('FPort'),
                                                                       card_guid))

    except Exception as ex:
        msg = f"Exception in: {ex}"
        ret_value['DESC'] = msg
        logger.exception(msg)

    return JSONResponse(ret_value)
