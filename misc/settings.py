import os
import unittest
import configparser
from dataclasses import dataclass


@dataclass
class SettingsStruct:
    host: str
    port: int
    log_path: str
    term_name: str

    db_host: str
    db_user: str
    db_password: str
    db_charset: str


class SettingsIni:

    def __init__(self, file_url: str = "settings.ini"):
        self.class_settings: SettingsStruct = None
        self.file_url = file_url

    def create_settings(self) -> dict:
        """ Функция получения настройки из файла settings.ini. """
        error_mess = 'Успешная загрузка данных из settings.ini'
        ret_value = dict()
        ret_value["result"] = False
        parser_file = configparser.ConfigParser()

        # проверяем файл settings.ini
        if os.path.isfile(self.file_url):
            try:
                parser_file.read(self.file_url, encoding="utf-8")

                # Заполняем структуру данными
                self.class_settings = SettingsStruct(
                    host=parser_file.get('GEN', 'HOST'),
                    port=int(parser_file.get('GEN', 'PORT')),
                    log_path=parser_file.get('GEN', 'LOG_PATH'),
                    term_name=parser_file.get('GEN', 'TERMINAL_NAME'),

                    db_host=parser_file.get('BASE', 'HOST'),
                    db_user=parser_file.get('BASE', 'USER'),
                    db_password=parser_file.get('BASE', 'PASSWORD'),
                    db_charset=parser_file.get('BASE', 'CHARSET'),
                )

                ret_value["result"] = True

            except KeyError as ex:
                error_mess = f"Ошибка ключа - {ex}"

            except Exception as ex:
                error_mess = f"Общая ошибка - {ex}"
        else:
            error_mess = "Файл settings.ini не найден"

        ret_value["desc"] = error_mess

        return ret_value


class TestSettingsIni(unittest.TestCase):

    def setUp(self):
        # Создаем временный файл конфигурации для тестов
        self.config_content = """
        [GEN]
        HOST = localhost
        PORT = 8080
        LOG_PATH = /var/log/app.log

        [BASE]
        HOST = db.example.com
        USER = user
        PASSWORD = password
        CHARSET = utf8

        [READER]
        USER = reader_user
        PASSWORD = reader_password
        HOST = reader.example.com
        PORT = 1234

        [APACS]
        HOST = apacs.example.com
        PORT = 9000
        USER = apacs_user
        PASSWORD = apacs_password
        FOLDER = folder_apacs
        """
        self.config_file = 'test_settings.ini'
        with open(self.config_file, 'w') as f:
            f.write(self.config_content)

    def tearDown(self):
        # Удаляем временный файл после тестов
        if os.path.exists(self.config_file):
            os.remove(self.config_file)

    def test_create_settings_success(self):
        # Тест успешного создания настроек из файла
        settings = SettingsIni(self.config_file)
        result = settings.create_settings()
        self.assertTrue(result['result'])
        self.assertEqual(result['desc'], 'Успешная загрузка данных из settings.ini')

        # Проверяем, что объект Settings был корректно создан
        self.assertIsInstance(settings.class_settings, SettingsStruct)
        self.assertEqual(settings.class_settings.host, 'localhost')
        self.assertEqual(settings.class_settings.port, 8080)
        self.assertEqual(settings.class_settings.log_path, '/var/log/app.log')
        self.assertEqual(settings.class_settings.db_host, 'db.example.com')
        self.assertEqual(settings.class_settings.db_user, 'user')
        self.assertEqual(settings.class_settings.db_password, 'password')
        self.assertEqual(settings.class_settings.db_charset, 'utf8')

    def test_create_settings_file_not_found(self):
        # Тест обработки ошибки, если файл settings.ini не найден
        settings = SettingsIni('non_existing_file.ini')
        result = settings.create_settings()
        self.assertFalse(result['result'])
        self.assertEqual(result['desc'], 'Файл settings.ini не найден')

    def test_create_settings_key_error(self):
        # Тест обработки ошибки KeyError при отсутствии ключа в файле settings.ini
        invalid_config_content = """
        [GEN]
        HOST = localhost
        """
        invalid_config_file = 'invalid_settings.ini'
        with open(invalid_config_file, 'w') as f:
            f.write(invalid_config_content)

        settings = SettingsIni(invalid_config_file)
        result = settings.create_settings()
        self.assertFalse(result['result'])
        self.assertTrue('Ошибка ключа' in result['desc'])

        # Удаляем временный файл после тестов
        if os.path.exists(invalid_config_file):
            os.remove(invalid_config_file)

#
# if __name__ == "__main__":
#     set_ini = SettingsIni('..\\settings.ini')
#     print(set_ini.create_settings())
