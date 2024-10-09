import asyncio
import pprint
from datetime import datetime
from misc.logger import Logger
from gate_connection.models import Packet, DeviceData

logger = Logger()

TIME_OUT_REQUEST = 4  # sec.

# В модуле реле присутствует 2 реле (новые данные уже до 15 реле)
SUCCESS_ANSWER = b"#010000"  # возвращает тип команды которую он получил в запросе и остальное нули (#01 тип команды)


class DeviceConnection:

    def __init__(self):
        pass

    @classmethod
    async def __socket_request(cls, host: str, port: int, byte_code: bytes) -> bytes:
        """ Базовый метод связи с устройством """
        # start = datetime.now()
        data = b''
        start_time = datetime.now()
        reader, writer = await asyncio.wait_for(asyncio.open_connection(host, port), TIME_OUT_REQUEST)
        # reader, writer = await asyncio.open_connection(host, port)

        if writer:

            try:
                writer.write(byte_code)
                await writer.drain()

                data = await reader.read(1024)

            except Exception as ex:
                print("TEST")
            finally:
                writer.close()
                await writer.wait_closed()

        total_sec = (datetime.now() - start_time).total_seconds()

        if total_sec > 1:
            logger.info(f"Время запроса к контроллеру {host}:{port} - {total_sec} сек.")

        # print(f"Время на запрос к сокету {host}:{port} - {(datetime.now() - start).total_seconds()}")

        return data

    @classmethod
    async def send_packet(cls, device_data: DeviceData, packet: Packet) -> dict:
        """ Функция принимает подготовленный пакет данных, и отвечает словарём,
        где содержится имя устройства, результат запроса и сообщение об возникших ошибках """

        res = await cls.__socket_request(device_data.address, device_data.port, packet.get())

        bytes_str = str(res.decode())

        data_res = {"bytes": bytes_str,
                    "device.FName": device_data.f_name,
                    "reader.FName": device_data.reader_name}

        return data_res

    @classmethod
    async def force_request(cls, host: str, port: int, byte_code: bytes) -> dict:
        """ Функция отправляет байт-код на устройство по сокет """

        ret_value = {}

        res = await cls.__socket_request(host, port, byte_code)

        if res:
            ret_value = {'bytes': str(res.decode())}

        return ret_value
