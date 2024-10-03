from enum import Enum, unique
from pprint import pprint


@unique
class AnswerEHS(Enum):
    """ Команда определяет действие для устройства """
    SUCCESS = 0


@unique
class CommandsCMD(Enum):
    """ Команда определяет действие для устройства """
    STATUS = 0
    ACTION = 1
    ADD_CARD = 2


@unique
class ReserveSection(Enum):
    """ Зарезервированная область разработчиком """
    NOT_DEFINE = 0


@unique
class AnswerData(Enum):
    CLOSE = 7
    OPEN = 6
    IC = 5
    LOOP_A = 4
    LOOP_B = 3
    RESERVE_A = 2
    RESERVE_B = 1
    POWER_ON = 0


@unique
class StateDevice(Enum):
    CAR_EMPTY = 0           # Машин и других объектов нет в зоне шлагбаума
    CAR_IN_CENTER = 1       # Машина в центре
    CAR_ENTRY_CENTER = 2    # Машина на въезде + часть в центре
    CAR_EXIT_CENTER = 3     # Машина на выезде + часть в центре
    CAR_OBJECT_CENTER = 4   # Посторонний объект в центре
    CAR_EXIT = 5            # Машина со стороны выезда
    CAR_ENTRY = 6           # Машина со стороны въезда

    GATE_POS_ERROR = 7      # Ошибка позиции шлагбаума
    GATE_POS_OPEN = 8       # Шлагбаум открыт
    GATE_POS_CLOSE = 9      # Шлагбаум закрыт
    GATE_POS_NEUTRAL = 10   # Шлагбаум в нейтральном положении


class ResAnswerData:
    """ Класс распределения данных из ответа от устройства """
    def __init__(self, fid, name, type_device, address, desc, port, online_status, answer, pak_res):
        self.fid = fid
        self.name = name
        self.type_device = type_device
        self.address = address
        self.desc = desc
        self.port = port
        self.online_status = online_status
        self.answer = answer
        self.pak_res = pak_res

        if answer:
            # Случай когда может быть ответ без данных
            hex_res = ReadDataFromHex(str(answer))
            decode_topic = hex_res.decode_answer()
            decode_data = hex_res.get_read_data_list()
        else:
            decode_topic = []
            decode_data = []

        self.decode_topic = decode_topic
        self.decode_data = decode_data

    def json(self):
        """ {'FID': self.fid,\n
            'FName': self.name,\n
            'FTypeDeviceID': self.type_device,\n
            'FAddress': self.address,\n
            'FDescription': self.desc,\n
            'FPort': self.port,\n
            'FOnlineStatus': self.online_status,\n
            'bytes': str(self.answer),  # str нужен для request json\n
            'Packet': self.pak_res,\n
            'decode_topic': self.decode_topic,\n
            'decode_data': self.decode_data} """
        return {'FID': self.fid,
                   'FName': self.name,
                   'FTypeDeviceID': self.type_device,
                   'FAddress': self.address,
                   'FDescription': self.desc,
                   'FPort': self.port,
                   'FOnlineStatus': self.online_status,
                   'bytes': str(self.answer),  # преобразование в str нужно для request json
                   'Packet': self.pak_res,
                'decode_topic': self.decode_topic,
                'decode_data': self.decode_data}


class ReadDataFromHex:
    """ Класс отвечает за парсинг ответа от контроллера """
    def __init__(self, byte_code: bytes):
        """ Принимает байт-код стиля b'#01000100' или же такой же стиль только в строке '#01000100' """
        # Проверяем на тип
        if type(byte_code) is bytes:
            self.str_data = byte_code.decode()[1:]  # Декодируем данные в строку и убираем # в начале строки
        else:
            self.str_data = byte_code[1:]

        self.data_list = [self.str_data[i:i + 2] for i in range(0, len(self.str_data), 2)]
        self.hex_list = list()

    def get_results(self) -> dict:
        self.hex_list = list()
        for_iter = self.data_list[3:]

        for it in for_iter:
            # Шаг: Преобразование из hex в decimal
            decimal_number = int(it, 16)
            str_data = format(decimal_number, '08b')

            self.hex_list.append(str_data)

        ret_value = {'CMD': self.data_list[0],
                     'EHS': self.data_list[1],
                     'SIZE': self.data_list[2],
                     'HEX_TO_BIN': self.hex_list}

        return ret_value

    def get_read_data_list(self) -> list:
        hex_res = self.get_results()
        ret_value = list()

        for it in hex_res.get('HEX_TO_BIN'):
            ret_value.append(AnswerState(it).complete())

        return ret_value

    def decode_answer(self):
        data = self.get_results()

        return {'CMD': int(data['CMD'], 16),
                'EHS': int(data['EHS'], 16),
                'SIZE': int(data['SIZE'], 16)}


class AnswerState:
    """ Класс отвечает за структурирование и расшифровку ответа от устройства """
    def __init__(self, str_data: str):
        """ Принимает готовую строку BIN из раздела HEX:
        '10000001' в данном примере power_on = 1 и gate_position = close """

        self.close = int(str_data[AnswerData.CLOSE.value])
        self.open = int(str_data[AnswerData.OPEN.value])
        self.ic = int(str_data[AnswerData.IC.value])
        self.loop_a = int(str_data[AnswerData.LOOP_A.value])
        self.loop_b = int(str_data[AnswerData.LOOP_B.value])
        self.reserve_a = int(str_data[AnswerData.RESERVE_A.value])
        self.reserve_b = int(str_data[AnswerData.RESERVE_B.value])
        self.power_on = int(str_data[AnswerData.POWER_ON.value])

    def complete(self) -> dict:
        """ Функция отвечает за подготовку данных полученных от устройства '01000001' """
        if self.close and self.open:
            # Два датчика замкнуты Ошибка
            gate_position = StateDevice.GATE_POS_ERROR
        elif self.open:
            # Позиция вверх иди открыт
            gate_position = StateDevice.GATE_POS_OPEN
        elif self.close:
            # Позиция внизу или закрыта
            gate_position = StateDevice.GATE_POS_CLOSE
        else:
            # Нейтральное положение
            gate_position = StateDevice.GATE_POS_NEUTRAL

        object_in = StateDevice.CAR_EMPTY

        if self.ic and self.loop_a and self.loop_b:
            # В центре машина
            object_in = StateDevice.CAR_IN_CENTER
        elif self.ic and self.loop_a:
            # Въезд центр
            object_in = StateDevice.CAR_ENTRY_CENTER
        elif self.ic and self.loop_b:
            # Выезд центр
            object_in = StateDevice.CAR_EXIT_CENTER
        elif self.ic:
            # Объект в центре
            object_in = StateDevice.CAR_OBJECT_CENTER
        elif self.loop_b:
            # Машина выезд
            object_in = StateDevice.CAR_EXIT
        elif self.loop_a:
            # Машина въезд
            object_in = StateDevice.CAR_ENTRY

        ret_value = {"gate_position": gate_position.value,
                     "object_in": object_in.value,
                     "power": self.power_on,
                     "reserve_a": self.reserve_a,
                     "reserve_b": self.reserve_b}

        return ret_value


class ByteGen:
    """ Класс преобразования данных из числа в десятеричные данные"""
    @staticmethod
    def gen_hex(number: int) -> str:
        """ Преобразует число в хекс значение и переводит в строку для дальнейшей обработки """
        nod_str = str(hex(number).split('x')[-1]).upper()
        if len(nod_str) < 2:
            nod_str = '0' + nod_str

        return nod_str


class Packet:
    """ Класс создания пакета запроса (если нет данных указывать пустой список [])"""

    def __init__(self, command: CommandsCMD, reserve: ReserveSection, data: list):
        self.command: str = ByteGen.gen_hex(command.value)
        self.reserve: str = ByteGen.gen_hex(reserve.value)
        self.size: str = ByteGen.gen_hex(len(data))

        self.data_list = list()

        for it in data:
            self.data_list.append(ByteGen.gen_hex(it))

    def get(self) -> bytes:
        """ Возвращает подготовленные данные для отправки в сокет """
        ret_data = f"#{self.command}{self.reserve}{self.size}"

        for it in self.data_list:
            ret_data = ret_data + it

        return ret_data.encode()

    def __str__(self) -> str:
        """ Если нужно распечатать в терминал или получить строку """
        ret_str = f"{self.command}x{self.reserve}x{self.size}"

        for it in self.data_list:
            ret_str = ret_str + f"x{it}"

        return ret_str


if __name__ == "__main__":
    # res = AnswerComplete(b'#00000110')
    #
    # pprint(res.complete())

    pprint(ReadDataFromHex(b'#010003010255').get_results())
