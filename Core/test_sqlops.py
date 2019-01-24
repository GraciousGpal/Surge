import random
import unittest

from faker import Faker

from Core.sqlops import *

Fake = Faker()
Fake.random.seed(8889)


# Fake Test Data Server
class Server:
    def __init__(self):
        self.guilds = [guild() for x in range(0, 2)]


class Rolez:
    def __init__(self, name, guild_id):
        self.id = int("".join([str(random.randint(0, 9)) for x in range(0, 10)]))
        self.name = name
        self.guild_id = guild_id


class Userz:
    def __init__(self, name, moolah):
        self.id = int("".join([str(random.randint(0, 9)) for x in range(0, 11)]))
        self.name = name
        self.moolah = moolah


class guild:
    def __init__(self):
        self.id = Fake.random_number()
        self.name = Fake.name()
        self.members = [Userz(name=Fake.name(), moolah=0) for x in range(0, 1000)]
        self.roles = [Rolez(name=Fake.state(), guild_id=self.id)]


class Testing(unittest.TestCase):
    def setUp(self):
        self.fake = Faker()
        self.guilds = Server().guilds
        self.server = create_full_table(self)

    def test1_initalCheck(self):
        # Check Number of Guilds in database and class structure is the same
        self.assertEqual(len([a for a in Query(types='guild').get('all')]), len(self.guilds))

    def test2_querycheck(self):
        # Query Users
        num = random.randint(0, 10)
        self.user = self.guilds[0].members[num]
        self.user_b = Query(types='user', obj=self.user).get()

        # Check if the model is not None and the queried is not None
        self.assertIsNotNone(self.user.moolah)
        self.assertIsNotNone(self.user_b.moolah)

        # Check if the Db value is the same as the model
        self.assertEqual(self.user.moolah, self.user_b.moolah)

    def test3_S_trans(self):
        # Simple addition check
        guild_no = random.randint(0, len(self.guilds) - 1)
        member_no = len(self.guilds[guild_no].members) - 1

        user_t = transaction(bot=self, usr=self.guilds[guild_no].members[member_no])
        user_t.add(1000)
        user_b_m = Query(types='user', obj=self.guilds[guild_no].members[member_no]).get().moolah
        self.assertGreater(user_b_m, self.guilds[guild_no].members[member_no].moolah)

    def test4_S_overflow(self):
        guild_no = random.randint(0, len(self.guilds) - 1)
        member_no = len(self.guilds[guild_no].members) - 1

        # Overflow Check
        user_t = transaction(bot=self, usr=self.guilds[guild_no].members[member_no])
        with self.assertRaises(OverflownError):
            user_t.add(10000000000)

    def test4_Randominput(self):
        guild_no = random.randint(0, len(self.guilds) - 1)
        member_no = len(self.guilds[guild_no].members) - 1

        user_t = transaction(bot=self, usr=self.guilds[guild_no].members[member_no])
        with self.assertRaises(ValueError):
            user_t.add('234')
            user_t.add('234s')

    def test5_overSub(self):
        guild_no = random.randint(0, len(self.guilds) - 1)
        member_no = len(self.guilds[guild_no].members) - 1
        user_t = transaction(bot=self, usr=self.guilds[guild_no].members[member_no])
        user_t.add(5634534)
        user_t.remove(100000000)
        self.assertEqual(0, Query(types='user', obj=self.guilds[guild_no].members[member_no]).get().moolah)

    def test6_overSub(self):
        pass


if __name__ == '__main__':
    unittest.main()
