WATCHER_DATA = {}


class WatcherDataControl:
    @staticmethod
    def get_data_by_fid(fid: int) -> dict:

        ret_value = {}

        if WATCHER_DATA:
            if fid in WATCHER_DATA:
                ret_value = WATCHER_DATA.get(fid)

        return ret_value

    @staticmethod
    def get_all() -> dict:
        return WATCHER_DATA

    @staticmethod
    def update_data(fid, data: dict):
        global WATCHER_DATA

        WATCHER_DATA[fid] = data
