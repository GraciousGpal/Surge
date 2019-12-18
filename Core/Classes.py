import logging

import numpy as np
import pandas
from sqlalchemy import exists
from sqlalchemy.exc import SQLAlchemyError

from Core.sqlops import Inventory, session, Player

logg = logging.getLogger(__name__)


class Classloader():
    def __init__(self, role):
        self.c = role


def load_ProfData():  # Level-Location-Profession
    dt = pandas.read_csv('Game/Profession_Item_drop.csv', names=["Location", "Lumberjack", "Miner", "Herbalism"],
                         skiprows=1).T.to_dict()
    dt = {x: dt[x] for x in dt if dt[x]['Location'] is not np.nan}
    print()
    return dt


class Profession:
    def __init__(self, player):
        self.master = {}
        self.master["ProfData"] = load_ProfData()
        self.player = player

    @property
    def unlocked(self):
        area = []
        for lvl in self.master["ProfData"]:
            if lvl < self.player.level:
                area.append(self.master["ProfData"][lvl]['Location'])
        return area

    def gain(self, location):
        profdata = self.master["ProfData"]


class Location:
    def __init__(self, name):
        self.name = name
        self.resource = []


class Character:
    def __init__(self, user, store=None):
        self.bot = store.bot
        self.user = user
        self.has_chosen = False

        if self.user is None:
            raise BotVarNotPassed

        self.plyr = session.query(Player).filter(Player.id == self.user.id).first()

        if self.plyr is None:
            self.create_player()

        if self.plyr.profession is not None:
            self.has_chosen = True

    @property
    def profession(self):
        return self.plyr.profession

    @property
    def level(self):
        return self.plyr.level

    @level.setter
    def level(self, value):
        if value < 0:
            value = 0
        try:
            self.plyr.level = value
            session.commit()
        except SQLAlchemyError as e:
            session.rollback()
            logg.error("Level up error {} - {}".format(self.user.id, value))

    @property
    def moolah(self):
        return self.plyr.moolah

    @moolah.setter
    def moolah(self, value):
        try:
            transaction = abs(int(value))
        except ValueError:
            raise ValueError('Please Enter a Number')

        if transaction >= 2147483647:
            raise OverflownError('Cannot Exceed the transaction max limit ! [2147483647] ')

        if value < self.plyr.moolah:  # Detect subtraction
            if value < 0:
                raise InsufficientFunds(
                    "{} in balance, Transaction amount: {}".format(self.plyr.moolah, self.plyr.moolah + value * -1))

        if self.plyr.moolah < 0:
            self.plyr.moolah = 0

        try:
            self.plyr.moolah = value
            session.commit()
        except SQLAlchemyError as e:
            session.rollback()
            logg.error("Moolah transaction error {} - {}".format(self.user.id, value))

    @property
    def exp(self):
        if self.has_chosen is None:
            raise CharacterNotSetup("Your Character has not been setup!.")
        return self.plyr.exp

    @exp.setter
    def exp(self, value):
        if self.has_chosen is None:
            raise CharacterNotSetup("Your Character has not been setup!.")
        if value < 0:
            value = 0

        try:
            self.plyr.exp = value
            new_lvl = max([x for x in self.bot.master["ProfData"]["level_data"] if
                           self.plyr.exp >= self.bot.master["ProfData"]["level_data"][x]])
            old_c = new_lvl
            # Level Up logic
            if old_c != self.level:
                old_lvl = int(self.plyr.level)
                self.plyr.level = new_lvl
                logg.info("Leveled: {} - {} --> {}".format(self.user.name, old_lvl, self.plyr.level))

            session.commit()
        except SQLAlchemyError as e:
            session.rollback()
            logg.error(e)

    @property
    def inventory(self):
        if self.has_chosen is None:
            raise CharacterNotSetup("Your Character has not been setup!.")
        return self.plyr.inv

    @property
    def location(self):
        return self.plyr.location

    @location.setter
    def location(self, dest):
        try:
            self.plyr.location = dest
            session.commit()
        except SQLAlchemyError as e:
            logg.info("Error Setting Location Data {} - {} ".format(self.user.id, dest))
            session.rollback()

    def create_player(self):
        try:
            player = Player(id=self.user.id)
            session.add(player)
            session.commit()
        except SQLAlchemyError as e:
            session.rollback()
            logg.error(e)

    async def add_to_inv(self, id_item, quantity=1):
        """
        Adds an item to the player inventory
        :param id_item:
        :param quantity:
        :return:
        """
        s_r = session.query(exists().where(
            Inventory.player_id == self.user.id and Inventory.item_id == id_item)).scalar()  # Check if item exists
        if s_r:
            try:  # If item exists add to quantity
                inv_object = session.query(Inventory).filter(
                    Inventory.player_id == self.user.id).filter(
                    Inventory.item_id == id_item).first()
                inv_object.quantity += quantity
                session.commit()
            except SQLAlchemyError as e:
                logg.warning(e)
                session.rollback()
        else:  # If it does not exists create an entry and initialize it
            inv_entry = Inventory(player_id=self.user.id, item_id=id_item, quantity=1)
            try:
                session.add(inv_entry)
                session.commit()
            except SQLAlchemyError as e:
                logg.warning(e)
                session.rollback()

    async def take_from_inv(self, id_item, quantity=1):
        """
        Takes an item from the player inventory
        :param id_item:
        :param quantity:
        :return:
        """
        s_r = session.query(exists().where(
            Inventory.player_id == self.user.id and Inventory.item_id == id_item)).scalar()  # Check if item exists
        if s_r:
            try:  # If item exists take from quantity
                inv_object = session.query(Inventory).filter(
                    Inventory.player_id == self.user.id).filter(
                    Inventory.item_id == id_item).first()

                if quantity > inv_object.quantity:
                    raise InsufficientQuantity("You do not have enough of {}".format(id_item))
                inv_object.quantity -= quantity

                if inv_object.quantity <= 0:
                    session.delete(inv_object)

                session.commit()
                return inv_object.item.base_value, quantity
            except SQLAlchemyError as e:
                logg.warning(e)
                session.rollback()
        else:  # If it does not exists raise an itemNot found exception
            raise ItemNotFound("You do not have this item")


class CharacterNotSetup(Exception):
    pass


class ItemNotFound(Exception):
    pass


class InsufficientQuantity(Exception):
    pass


class OverflownError(Exception):
    pass


class BotVarNotPassed(Exception):
    pass


class InsufficientFunds(Exception):
    pass


if __name__ == "__main__":
    class UserX:
        def __init__(self):
            self.id = 89258994744430592


    chara = Character(UserX())
    chara.exp += 10
    print(chara.exp)
