import logging

import numpy as np
import pandas

from Core.sqlops import session, Player

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
        except Exception as e:
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

        if value < 0:
            value = 0

        if self.plyr.moolah < value:
            raise InsufficientFunds("{} in Balance, transaction {}".format(self.plyr.moolah, value))
        try:
            self.plyr.moolah = value
            session.commit()
        except Exception as e:
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
        except Exception as e:
            logg.error(e)

    @property
    def inventory(self):
        if self.has_chosen is None:
            raise CharacterNotSetup("Your Character has not been setup!.")
        return self.plyr.inv

    def create_player(self):
        try:

            player = Player(id=self.user.id)
            session.add(player)
            session.commit()
        except Exception as e:
            logg.error(e)


class CharacterNotSetup(Exception):
    pass


class OverflownError(Exception):
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
