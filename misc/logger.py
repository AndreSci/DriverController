# Author AndreSci
import threading
import os
import datetime
import inspect
import traceback

# Данные для logger
LOGGER_PATH = os.path.join(os.getcwd(), "logs/")


class BColors:
    """ Класс вариантов цвета для текста в консоли """
    col_header = '\033[95m'
    col_okblue = '\033[94m'
    col_okcyan = '\033[96m'
    col_okgreen = '\033[92m'
    col_warning = '\033[93m'
    col_fail = '\033[91m'
    col_endc = '\033[0m'
    col_bold = '\033[1m'
    col_underline = '\033[4m'


def test_dir(log_path) -> bool:
    """ Функция проверки папки куда сохраняются логи """
    ret_value = True

    try:
        if not os.path.exists(log_path):  # Если нет директории log_path пробуем её создать.
            os.makedirs(log_path)
            print(f"{BColors.col_warning}Была создана директория для лог-фалов:{BColors.col_endc} {log_path}")
    except Exception as ex:
        print(f"Ошибка при проверка/создании директории лог файлов: {ex}")
        ret_value = False

    return ret_value


class SingletonBaseClass(type):
    """ Шаблон синглетом (объяви один раз и пользуйся во всей программе одним экземпляром)"""
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(SingletonBaseClass, cls).__call__(*args, **kwargs)

        return cls._instances[cls]


class Logger(metaclass=SingletonBaseClass):
    """ Класс вывода данных в консоль и запись в файл """
    def __init__(self, log_path: str = None):
        self.font_color = False
        self.log_guard = threading.Lock()
        if log_path:
            global LOGGER_PATH
            LOGGER_PATH = log_path

    def add_log(self, text: str, print_it=True):
        """ Обшивает текст датой, табуляцией и переходом на новую строку """
        ret_value = False
        try:

            if type(text) is not str():
                text = str(text)

            today = datetime.datetime.today()

            for_file_name = str(today.strftime("%Y-%m-%d"))

            date_time = str(today.strftime("%Y-%m-%d %H:%M:%S"))
            # Создаем лог
            mess = date_time + "\t" + text + "\n"

            if test_dir(LOGGER_PATH):

                # if LOGGER_PATH[-1] == '\\' or LOGGER_PATH[-1] == '/':
                #     pass
                # else:
                #     log_path = LOGGER_PATH + '/'

                with self.log_guard:  # Защищаем поток

                    if print_it:
                        if 'ERROR' == text[:5]:
                            print(f"{BColors.col_fail}{date_time}\t{text}{BColors.col_endc}")
                        elif 'WARNING' == text[:7]:
                            print(f"{BColors.col_warning}{date_time}\t{text}{BColors.col_endc}")
                        else:
                            print(date_time + "\t" + text)

                    # Открываем и записываем логи в файл отчета.
                    with open(f'{LOGGER_PATH}{for_file_name}.log', 'a', encoding='utf-8') as file:
                        file.write(mess)
                        ret_value = True
        except Exception as ex:
            print(f"{BColors.col_warning}"
                  f"EXCEPTION\tLOGGER.add_log\tИсключение в работе регистрации события в файл: {ex}"
                  f"{BColors.col_endc}")

        return ret_value

    def __rebuild_msg(self, text: str, print_it=True, type_mess="INFO", current_frame=inspect.currentframe()):
        """ Метод изменяет текст в стандартный стиль """

        # получи фрейм объект, который его вызвал
        caller_frame = current_frame.f_back

        # возьми у вызвавшего фрейма исполняемый в нём объект типа "код" (code object)
        code_obj = caller_frame.f_code

        # и получи его имя
        code_obj_name = code_obj.co_name

        return self.add_log(f"{type_mess}\t{code_obj_name}\t{text}", print_it)

    def info(self, text: str, print_it=True):
        """ Метод изменяет текст в стандартный стиль """
        # возьми текущий фрейм объект (frame object)
        current_frame = inspect.currentframe()
        return self.__rebuild_msg(text, print_it, "INFO", current_frame)

    def event(self, text: str, print_it=True):
        """ Метод изменяет текст в стандартный стиль """
        # возьми текущий фрейм объект (frame object)
        current_frame = inspect.currentframe()
        return self.__rebuild_msg(text, print_it, "EVENT", current_frame)

    def warning(self, text: str, print_it=True):
        """ Метод изменяет текст в стандартный стиль """
        # возьми текущий фрейм объект (frame object)
        current_frame = inspect.currentframe()
        return self.__rebuild_msg(text, print_it, "WARNING", current_frame)

    def error(self, text: str, print_it=True):
        """ Метод изменяет текст в стандартный стиль """
        # возьми текущий фрейм объект (frame object)
        current_frame = inspect.currentframe()
        return self.__rebuild_msg(text, print_it, "ERROR", current_frame)

    def exception(self, text: str, print_it=True):
        """ Метод изменяет текст и указывает где была вызвана ошибка(traceback) """
        # возьми текущий фрейм объект (frame object)
        current_frame = inspect.currentframe()

        # получи фрейм объект, который его вызвал
        caller_frame = current_frame.f_back

        # возьми у вызвавшего фрейма исполняемый в нём объект типа "код" (code object)
        code_obj = caller_frame.f_code

        # и получи его имя
        code_obj_name = code_obj.co_name

        return self.add_log(f"EXCEPTION\t{code_obj_name}\t{text} - {traceback.format_exc()}", print_it)
