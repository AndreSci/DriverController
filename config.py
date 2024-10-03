from flask import Flask
from misc.settings import SettingsStruct
from database.database import GlobControlDatabase
from database.models import DATABASE_NAME_SENDER
from gate_connection.watcher import WatcherDevice


class SettingsInitial:
    @staticmethod
    def load_config(flask_app: Flask, set_data: SettingsStruct, watcher: WatcherDevice):

        GlobControlDatabase.set_url(set_data.db_user,
                                    set_data.db_password,
                                    set_data.db_host,
                                    3306,
                                    DATABASE_NAME_SENDER,
                                    set_data.db_charset)

        flask_app.config['host'] = set_data.host
        flask_app.config['port'] = set_data.port
        flask_app.config['term_name'] = set_data.term_name

        flask_app.config['db_host'] = set_data.db_host
        flask_app.config['db_user'] = set_data.db_user
        flask_app.config['db_password'] = set_data.db_password
        flask_app.config['db_charset'] = set_data.db_charset

        flask_app.config['class_settings'] = set_data

        flask_app.config['watcher_app'] = watcher
