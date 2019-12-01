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

    def mine(self, location):
        profdata = self.master["ProfData"]


class Location:
    def __init__(self, name):
        self.name = name
        self.resource = []


class Character:
    def __init__(self, user):
        self.user = user
        self.has_chosen = False
        self.plyr = session.query(Player).filter(Player.id == self.user.id).first()
        if self.plyr.profession is not None:
            self.has_chosen = True

    @property
    def profession(self):
        return self.plyr.profession

    @property
    def moolah(self):
        return self.plyr.moolah

    @moolah.setter
    def moolah(self, value):
        if value < 0:
            value = 0
        self.plyr.moolah = value
        session.commit()

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
        self.plyr.exp = value
        session.commit()

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
            logg.info(e)


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
