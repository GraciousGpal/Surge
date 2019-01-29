import json
import logging
import os
import time

from sqlalchemy import Column, String, BIGINT, Integer, Boolean
from sqlalchemy import create_engine
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.schema import CreateColumn


def write(location, data):
    with open(location, 'w') as outfile:
        json.dump(data, outfile)


def load(location):
    with open(location, 'r') as data_file:
        data = json.load(data_file)
        return data


def check_files():
    f = "data/member_logger/settings.json"
    try:
        load(f)
    except Exception:
        logging.info("Creating default member_logger settings.json...")
        write(f, {})


def check_folders():
    if not os.path.exists("data/member_logger"):
        logging.info("Creating data/member_logger folder...")
        os.makedirs("data/member_logger")


@compiles(CreateColumn, 'postgresql')
def use_identity(element, compiler, **kw):
    text = compiler.visit_create_column(element, **kw)
    text = text.replace("SERIAL", "INT GENERATED BY DEFAULT AS IDENTITY")
    return text


Base = declarative_base()


class MapDataVoice(Base):
    __tablename__ = 'MapData_Voice'
    id = Column(Integer, primary_key=True)
    time = Column(Integer)
    member = Column(BIGINT)
    present = Column(String, default="")
    type = Column(Boolean, default=True)


class MemberLogger:
    """ Gathers information on when users interact with each other. Can be used for later statistical analysis """

    def __init__(self, bot):
        self.bot = bot
        self.settings_path = "data/member_logger/settings.json"
        self.settings = load(self.settings_path)

        # Ensure path is set. Use default path if not.
        if "database" not in self.settings.keys():
            self.settings["database"] = "sqlite:///data/member_logger/data.db"

        self.engine = None
        self.task = None
        if self.settings["database"]:
            logging.info("MemberLogDatabase info found...")
            self.engine = create_engine(self.settings["database"])
            Base.metadata.bind = self.engine
            self.session = sessionmaker(bind=self.engine)()
            Base.metadata.create_all(self.engine)

    async def on_message(self, message):
        if message.author.bot or not message.mentions or message.mention_everyone:
            return
        mentions = [m.id for m in message.mentions if not m.bot and m.id != message.author.id]
        if len(mentions) == 0:
            return
        data = MapDataVoice(time=int(time.time()), member=message.author.id,
                            present=str(mentions),
                            type=False)
        self.session.add(data)
        self.session.commit()

    async def on_voice_state_update(self, member, before, after):
        if member.bot:
            return

        bvchan = before.channel
        avchan = after.channel

        if bvchan != avchan:
            # went from no channel to a channel
            if bvchan is None and avchan is not None:
                # came online
                members = [m.id for m in avchan.members if not m.bot and m.id != member.id]
                if len(members) == 0:
                    return
                data = MapDataVoice(time=int(time.time()), member=member.id,
                                    present=str(members))
                self.session.add(data)
                self.session.commit()


def setup(bot):
    check_folders()
    check_files()
    bot.add_cog(MemberLogger(bot))
