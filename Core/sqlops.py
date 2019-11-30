import logging
import os
from datetime import datetime

from sqlalchemy import Column, ForeignKey, Integer, String, DateTime, CheckConstraint, Boolean, create_engine, \
    BigInteger
from sqlalchemy import exists
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.orm import sessionmaker

logg = logging.getLogger(__name__)

Base = declarative_base()

# Create an engine that stores data in the local directory's
# sqlalchemy_example.db file.
# engine = create_engine('sqlite:///data/data.db')
engine = create_engine(os.environ['DB_CON_STRING'])

# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
Base.metadata.bind = engine

# A DBSession() instance establishes all conversations with the database
# and represents a "staging zone" for all the objects loaded into the
# database session object. Any change made against the objects in the
# session won't be persisted into the database until you call
# session.commit(). If you're not happy about the changes, you can
# revert all of them back to the last commit by calling
# session.rollback()
session = sessionmaker(bind=engine)()


# SQL Models
class Guild(Base):
    __tablename__ = 'Guilds'
    id = Column(BigInteger, primary_key=True)
    name = Column(String(250), nullable=False)
    prefix = Column(String(2), default='+')
    roles = relationship("Role")
    modules = relationship("Module")


class Player(Base):
    __tablename__ = 'player'
    id = Column(BigInteger, primary_key=True)
    name = Column(String(32), nullable=False)
    moolah = Column(BigInteger, CheckConstraint('moolah >= 0'), nullable=False)
    updated_on = Column(DateTime, nullable=False, default=datetime.now(), onupdate=datetime.now())
    # ----------BASE----------#
    profession = Column(String(32))
    level = Column(Integer, default=0)
    exp = Column(Integer, default=0)
    location = Column(String(32))
    # --------STATS-------- #
    resource = Column(Integer, default=1)
    craft = Column(Integer, default=1)
    capacity = Column(Integer, default=10)
    luck = Column(Integer, default=1)
    # ----------COMBAT---------- #
    atk = Column(Integer, default=1)
    defence = Column(Integer, default=1)
    inv = relationship("Inventory", back_populates="user")


class Module(Base):
    __tablename__ = 'Modules'
    id = Column(Integer, primary_key=True)
    guild_id = Column(BigInteger, ForeignKey('Guilds.id'))
    modules = relationship("Guild", back_populates="modules")
    name = Column(String(32), nullable=False)
    state = Column(Boolean, default=False)


class Role(Base):
    __tablename__ = 'Roles'
    id = Column(BigInteger, primary_key=True)
    guild_id = Column(BigInteger, ForeignKey('Guilds.id'))
    price = Column(Integer, CheckConstraint('price >= 0'))


class Inventory(Base):
    __tablename__ = 'inventory'
    player_id = Column(BigInteger, ForeignKey('player.id'), primary_key=True)
    item_id = Column(Integer, ForeignKey('item.id'), primary_key=True)
    quantity = Column(Integer)
    # ------------------------- #
    user = relationship("Player", back_populates="inv")
    item = relationship("Item", back_populates="owners")


class Item(Base):
    __tablename__ = 'item'
    id = Column(Integer, primary_key=True)
    # ----------BASE----------#
    name = Column(String(32), nullable=False)
    types = Column(String(32), nullable=False)
    description = Column(String(64))
    base_value = Column(Integer, default=0)
    atk = Column(Integer, default=0)
    life = Column(Integer, default=0)
    # --------STATS-------- #
    resource = Column(Integer, default=0)
    craft = Column(Integer, default=0)
    capacity = Column(Integer, default=0)
    luck = Column(Integer, default=0)
    # ------------------------- #
    owners = relationship("Inventory", back_populates="item")


class Auction(Base):
    __tablename__ = 'auction'
    id = Column(Integer, primary_key=True)
    player_id = Column(BigInteger, ForeignKey('player.id'))
    item_id = Column(Integer, ForeignKey('item.id'))
    # ------------------------- #
    quantity = Column(Integer)
    price = Column(Integer, CheckConstraint('price >= 0'), default=0)
    # ------------------------- #
    player = relationship("Player")
    item = relationship("Item")


async def create_player(ctx, class_m):
    if class_m is None:
        await ctx.send(
            "Select a class <e.g +create Miner>\n```Class List:{}```".format(["Miner", "Lumberjack", "Gatherer"]))
    try:
        plyr = Player(id=ctx.author.id, profession=class_m, level=0, exp=0, atk=0, defence=0)
        session.add(plyr)
        session.commit()
    except IntegrityError as e:
        await ctx.send("You have already created a character!.")
        # logg.error(e)
        session.rollback()


def dataCheck(self):
    logg.info('Checking Database entries..')
    for server in self.guilds:
        if not session.query(exists().where(Guild.id == server.id)).scalar():
            logg.error('Missing Data Detected!')
            try:
                guild = Guild(id=server.id, name=server.name)
                session.add(guild)
                session.commit()
            except IntegrityError as e:
                logg.error('Guild Entry Error')
                session.rollback()
        for member in server.members:
            # print(member.name,session.query(exists().where(User.id == member.id)).scalar())
            if not session.query(exists().where(Player.id == member.id)).scalar():
                try:
                    user = Player(id=member.id, name=member.name, moolah=0)
                    session.add(user)
                except IntegrityError as e:
                    logg.error('User Entry Error')
                    session.rollback()
        for roles in server.roles:
            if not session.query(exists().where(Role.id == roles.id)).scalar():
                try:
                    channelz = Role(id=roles.id, guild_id=server.id)
                    session.add(channelz)
                except IntegrityError as e:
                    logg.error('Role Entry Error')
                    session.rollback()
        try:
            serverd = self.master[server.id]
        except KeyError:
            self.master[server.id] = {}

        for module in [f for f in self.cogs]:
            try:
                modules = self.master[server.id]['modules']
            except  KeyError:
                self.master[server.id]['modules'] = {}
            try:
                if session.query(Module).filter_by(guild_id=server.id, name=module).first() is None:
                    session.add(Module(guild_id=server.id, name=module, state=False))
            except Exception as e:
                raise (e)

    session.commit()

    # Load Settings into Master Index
    for server in self.guilds:
        for module in [f for f in self.cogs]:
            self.master[server.id]['modules'][module] = session.query(Module).filter_by(guild_id=server.id,
                                                                                        name=module).first().state
        self.master[server.id]["prefix"] = [session.query(Guild).filter_by(id=server.id).first().prefix]


def create_full_table(self):
    #Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    logg.info("Filling Tables ...")
    for server in self.guilds:
        if session.query(Guild).filter_by(id=server.id).first() is None:
            try:
                guildz = Guild(id=server.id, name=server.name)
                session.add(guildz)
                # session.commit()
            except IntegrityError as e:
                logg.error(e)

        for member in server.members:
            if session.query(Player).filter_by(id=member.id).first() is None:
                try:
                    # logg.info(member.id)
                    user = Player(id=member.id, name=str(member.name), moolah=0)
                    session.add(user)
                    # session.commit()
                except IntegrityError as e:
                    logg.error(e)
                    session.rollback()

        for roles in server.roles:
            if session.query(Role).filter_by(id=roles.id).first() is None:
                try:
                    channelz = Role(id=roles.id, guild_id=server.id)
                    session.add(channelz)
                except IntegrityError as e:
                    logg.error(e)
                    session.rollback()

        for item in [self.master["ProfData"][level] for level in self.master["ProfData"]]:
            for key in item:
                if key == 'Location' or str(key).isdigit() or key == 'Level':
                    continue
                if session.query(Item).filter_by(name=item[key]).first() is None:
                    try:
                        itemz = Item(name=item[key], types='Resource', description='needs work',
                                     base_value=item['Level'] * 100)
                        session.add(itemz)
                    except IntegrityError as e:
                        logg.error(e)
                        session.rollback()

        '''
        self.master["ProfData"]['Itemlist'] = []
        for item in self.master["ProfData"].copy():
            try:
                lol = self.master["ProfData"]['Itemlist']
                #print(self.master["ProfData"][item]['Lumberjack'])
                lumberjack = {'name': self.master["ProfData"][item]['Lumberjack'], 'type': 'Resource'}
                miner = {'name': self.master["ProfData"][item]['Miner'], 'type': 'Resource'}
                herb = {'name': self.master["ProfData"][item]['Herbalism'], 'type': 'Resource'}
                lol.append(lumberjack)
                lol.append(miner)
                lol.append(herb)
            except Exception as e:
                logg.error(e)
                pass
        #print(self.master["ProfData"]['Itemlist'])
        for item in self.master["ProfData"]['Itemlist']:
            if session.query(Item).filter_by(name=item).first() is None:
                print(str(item['name']))
                try:
                    Itemz = Item(name=str(item['name']), types=str(item['type']), description='need work')
                    session.add(Itemz)
                except IntegrityError as e:
                    logg.error(e)
                    session.rollback()'''

    logg.info("Table Creation finished!")
    session.commit()


class transaction:
    def __init__(self, bot, usr=None):
        self.bot = bot
        self.usr = usr
        self.transaction = 0

    def add(self, amount):
        self.inputSanitation(amount)
        try:
            user = session.query(Player).filter(Player.id == self.usr.id).first()
            user.moolah += self.transaction
            session.commit()
        except SQLAlchemyError as e:
            logg.error(e)
        finally:
            session.close()

    def remove(self, amount):
        self.inputSanitation(amount)
        self.hasenough(self.transaction)
        try:
            user = session.query(Player).filter(Player.id == self.usr.id).first()

            if user.moolah < self.transaction:
                user.moolah = 0
            else:
                user.moolah -= self.transaction

            session.commit()
        except SQLAlchemyError as e:
            logg.error(e)
        finally:
            session.close()

    def set(self, amount):
        self.inputSanitation(amount)
        try:
            user = session.query(Player).filter(Player.id == self.usr.id).first()
            user.moolah = self.transaction
            session.commit()
        except SQLAlchemyError as e:
            logg.error(e)
        finally:
            session.close()

    def hasenough(self, amount):
        class InsufficientFunds(Exception):
            pass

        user = session.query(Player).filter(Player.id == self.usr.id).first()
        if user.moolah < amount:
            raise InsufficientFunds("{} in Balance, transaction {}".format(user.moolah, amount))
        else:
            return True

    def inputSanitation(self, amount):
        try:
            self.transaction = abs(int(amount))
        except ValueError:
            raise ValueError('Please Enter a Number')

        if self.transaction >= 2147483647:
            raise OverflownError('Cannot Exceed the transaction max limit ! [2147483647] ')


class OverflownError(Exception):
    pass


class Query:
    def __init__(self, types='player', obj=None):
        if types == 'player':
            self.type = Player
        elif types == 'guild':
            self.type = Guild
        elif types == 'role':
            self.type = Role
        elif types == 'auction':
            self.type = Auction
        else:
            self.type = None
        self.obj = obj

    def get(self, number=None, orderby=None, order='desc'):
        """
        Gets Value
        :param number:
        :param order:
        :return:
        """

        if number is 'all':
            number = self.count()
        elif number is None:
            return session.query(self.type).filter_by(id=self.obj.id).first()

        if orderby is None:
            col_a = self.type.name
        elif orderby == 'moolah':
            col_a = self.type.moolah
        elif orderby == 'name':
            col_a = self.type.name
        elif orderby == 'id':
            col_a = self.type.id
        elif orderby == 'price':
            col_a = self.type.price

        if order == "desc" and number == "special":
            colum_q = session.query(self.type).order_by(col_a.desc())
            return colum_q
        elif order == 'desc':
            if self.obj is None:
                colum_q = session.query(self.type).order_by(col_a.desc()).limit(number)
            return colum_q

        elif order == 'asc':

            colum_q = session.query(self.type).order_by(col_a.asc()).limit(number)
            return colum_q

    def exists(self):
        """
        Check if it exists
        :return:
        """
        return session.query(exists().where(self.type.id == self.obj.id)).scalar()

    def count(self):
        """
        Return the total number of item
        :return:
        """
        return session.query(self.type).count()
