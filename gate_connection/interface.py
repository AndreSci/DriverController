import asyncio
from gate_connection.models import CommandsCMD, ReserveSection, AnswerState, ReadDataFromHex, Packet, DeviceData
from gate_connection.connection import DeviceConnection

from misc.logger import Logger

logger = Logger()

# Повторные Сообщения по ошибке соединения
REPEAT_WARNING = dict()

# В модуле реле присутствует 2 реле (новые данные уже до 15 реле)
DICT_GATES_OPEN = {0: b"#01000100", 1: b"#01000101"}

# STR_GATE_OPEN_FIRST = b"#01000100"
# STR_GATE_OPEN_SECOND = b"#01000101"

# Мануал по байт-коду
# 1. GetInputState  (Получить статус контролера)
# 2. Pulse          (Отправить сигнал на реле)
# 3. SetRelay       (Назначить настройки)
# Расшифровка
# b" 00 (тип команды) 00 (резерв) 00 (размер следующих данных) 00 (номер реле)"


def card_for_packet(card_number) -> list:
    """ Функция преобразовывает номер карты в массив бит представленных в виде строки """

    if len(card_number) % 2 == 0:
        n = 2
        split_string = [card_number[i:i + n] for i in range(0, len(card_number), n)]
        res_list = list()

        for hex_string in split_string:
            res_list.append(int(hex_string, 16))
    else:
        raise ValueError(f"Входные данные карты содержат нечетную длину: {len(card_number)}")

    return res_list


def repeat_warning(address, port, bool_it: bool = False) -> bool:
    """ Если True разрешить сообщение """
    global REPEAT_WARNING
    id_device = f"{address}{port}"

    if id_device in REPEAT_WARNING:
        ret_value = REPEAT_WARNING[id_device]
    else:
        ret_value = True

    REPEAT_WARNING[id_device] = bool_it

    return ret_value


class DeviceInterface:
    """ Класс управления контроллерами """
    def __init__(self):
        pass

    @staticmethod
    async def pulse(device_data: DeviceData, relay_num: int) -> dict:
        """ Функция принимает данные устройства из БД и номер реле которым нужно отработать. """
        packet = Packet(CommandsCMD.ACTION, ReserveSection.NOT_DEFINE, [relay_num,])

        data_res = await DeviceConnection().send_packet(device_data, packet)
        data_res['decode_data'] = ReadDataFromHex(data_res.get('bytes')).decode_answer()

        return data_res

    @staticmethod
    async def state(device_data: DeviceData) -> dict:
        """ Функция принимает данные устройства из БД """
        packet = Packet(CommandsCMD.STATUS, ReserveSection.NOT_DEFINE, [0,])

        data_res = await DeviceConnection().send_packet(device_data, packet)

        hex_res = ReadDataFromHex(data_res.get('bytes'))

        data_res['decode_topic'] = hex_res.decode_answer()
        data_res['decode_data'] = hex_res.get_read_data_list()

        return data_res

    # Additional Functions ----------------------------------------------------------
    @staticmethod
    async def send_bytes(device: DeviceData, byte_code: str = None) -> dict:
        """ Функция запрашиваем данные у удаленного устройства через сокет """

        ret_value = {"RESULT": "ERROR", "DESC": '', "DATA": dict()}

        address = device.address
        port = device.port

        try:
            if byte_code:
                byte_code = byte_code.encode()
            else:
                byte_code = b'#000000'

            res = await DeviceConnection().force_request(address, port, byte_code)

            ret_value['DATA'] = res
            ret_value['RESULT'] = 'SUCCESS'
            repeat_warning(address, port, True)

        except ConnectionError as cex:
            ret_value['DESC'] = f"Ошибка связи с контролером: {cex} ({address}:{port})"
            logger.warning(ret_value['DESC'])
        except TimeoutError as tex:
            ret_value['DESC'] = f"Превышено время ожидания контролером: {tex} ({address}:{port})"

            if repeat_warning(address, port, False):
                logger.warning(ret_value['DESC'])
        except Exception as ex:
            ret_value['DESC'] = f"Общая ошибка: {ex} ({address}:{port})"
            logger.exception(ret_value['DESC'])

        return ret_value

    @staticmethod
    async def send_with_params(address: str, port: int, byte_code: bytes) -> dict:
        """ Функция запрашиваем данные у удаленного устройства через сокет
            на данный момент работает только для Watcher """

        ret_value = {"RESULT": "ERROR", "DESC": '', "DATA": dict()}

        try:
            ret_value['DATA'] = await DeviceConnection().force_request(address, port, byte_code)

            ret_value['RESULT'] = "SUCCESS"
            if not repeat_warning(address, port):
                logger.event(f"Установленна связь с устройством: {address}:{port}")
            repeat_warning(address, port, True)

        except ConnectionError as cex:
            ret_value['DESC'] = f"Ошибка связи с контролером: {cex} ({address}:{port})"
            if repeat_warning(address, port, False):
                logger.warning(ret_value['DESC'])
        except TimeoutError as tex:
            ret_value['DESC'] = f"Превышено время ожидания контролером: {tex} ({address}:{port})"
            if repeat_warning(address, port, False):
                logger.warning(ret_value['DESC'])
        except asyncio.exceptions.TimeoutError as tex:
            ret_value['DESC'] = f"Превышено время ожидания контролером: {tex} ({address}:{port})"
            if repeat_warning(address, port, False):
                logger.warning(ret_value['DESC'])
        except Exception as ex:
            ret_value['DESC'] = f"Общая ошибка: {ex} ({address}:{port})"
            logger.exception(ret_value['DESC'])

        return ret_value

    @staticmethod
    def send_add_card(address: str, port: int, card_number: str) -> dict:
        """ Функция запрашиваем данные у удаленного устройства через сокет """

        ret_value = {"RESULT": "ERROR", "DESC": '', "DATA": dict()}

        try:
            card_list = card_for_packet(card_number)
            byte_code = Packet(CommandsCMD.ADD_CARD, ReserveSection.NOT_DEFINE, card_list).get()
            ret_value['DATA'] = DeviceConnection().force_request(address, port, byte_code)

            ret_value['RESULT'] = "SUCCESS"

            repeat_warning(address, port, True)

        except ConnectionError as cex:
            ret_value['DESC'] = f"Ошибка связи с контролером: {cex} ({address}:{port})"
            logger.warning(ret_value['DESC'])
        except TimeoutError as tex:
            ret_value['DESC'] = f"Превышено время ожидания контролером: {tex} ({address}:{port})"
            if repeat_warning(address, port, False):
                logger.warning(ret_value['DESC'])
        except Exception as ex:
            ret_value['DESC'] = f"Общая ошибка: {ex} ({address}:{port})"
            logger.exception(ret_value['DESC'])

        return ret_value
