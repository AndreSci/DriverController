from pydantic import BaseModel
from typing import Optional


class ManualControl(BaseModel):
    byte_code:  Optional[str] = '#000000'

    fid: Optional[int] = None

    host: Optional[str] = None
    port: Optional[int] = None

    class Config:
        json_schema_extra = {
            "example1": {
                "byte_code": "#000000",
                "fid": 4
            },
            "example2": {
                "byte_code": "#000000",
                "host": "192.168.15.177",
                "port": 177
            }
        }
