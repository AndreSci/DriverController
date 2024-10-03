from sqlalchemy import Table, Column, Integer, String, DateTime, ForeignKey
from database.database import METADATA

DATABASE_NAME_SENDER = "vig_sender"


t_camera = Table(
    "tcamera",
    METADATA,
    Column("FID", Integer, primary_key=True, index=True),
    Column("FName", String(255), index=True),
    Column("FDateCreate", DateTime),
    Column("FRTSP", String(255)),
    Column("FDesc", String(255)),
    Column("FDateLastModify", DateTime),
    Column("isPlateRecEnable", Integer)
)

t_camera_groups = Table(
    "tcameragroups",
    METADATA,
    Column("FID", Integer, primary_key=True, index=True),
    Column("FCameraID", Integer, ForeignKey("tcamera.FID")),
    Column("FAsteriskCallerID", Integer, ForeignKey("tasteriskcaller.FID"))
)

t_asterisk_caller = Table(
    "tasteriskcaller",
    METADATA,
    Column("FID", Integer, primary_key=True, index=True),
    Column("FName", String(255))
)

t_event = Table(
    "tevent",
    METADATA,
    Column("FID", Integer, primary_key=True, index=True),
    Column("FEventTypeID", Integer),
    Column("FDateEvent", DateTime),
    Column("FDateRegistration", DateTime),
    Column("FOwnerName", String(45)),
    Column("FEventMessage", String(256)),
    Column("FEventDescription", String(512)),
    Column("FProcessed", Integer)
)
