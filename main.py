import ctypes
import logging
import uvicorn
import setproctitle
from fastapi import FastAPI
from flask import Flask
from config import SettingsInitial
from gate_connection.watcher import WatcherDevice
from misc.logger import Logger
from misc.settings import SettingsIni

from routes.gates import gates_router

watcher_app = WatcherDevice()
watcher_app.start()

data_from_settings = SettingsIni()
data_from_settings.create_settings()

app = FastAPI()

# Устанавливаем уровень логирования для всех логгеров uvicorn
logging.getLogger("uvicorn").setLevel(logging.WARNING)
logging.getLogger("uvicorn.error").setLevel(logging.WARNING)
logging.getLogger("uvicorn.access").setLevel(logging.WARNING)

f_app = Flask(__name__)

# регистрируем в фласк новые router
app.include_router(gates_router)

logger = Logger()


if __name__ == '__main__':
    # Требуется пред загрузка настроек из файла settings.ini
    cls_settings = data_from_settings.class_settings

    SettingsInitial.load_config(f_app, cls_settings, watcher_app)

    setproctitle.setproctitle("Device Driver FastAPI")
    # Меняем имя терминала
    ctypes.windll.kernel32.SetConsoleTitleW(f"Device Driver (port: {cls_settings.port}) - "
                                            f"API отвечает за доступ к контроллерам")

    logger.event(f"Start work API Host: {cls_settings.host} Port: {cls_settings.port}")
    # app.run(host=cls_settings.host, port=cls_settings.port)

    uvicorn.run(app, host=str(cls_settings.host), port=int(cls_settings.port), reload=False, log_level="warning")
