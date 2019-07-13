import numpy as np
import pandas

hand_types = ['Pickaxe', 'Axe', 'Sewing Kit']
gear_types = ['Hat', 'Chest', 'Legs']
series = [('Makeshift', 0), ('Scuffed', 10), ('Quality', 20), ('Unique', 40), ('Superior', 60)]


def is_even(no):
    return True if no % 2 == 0 else False


def load_ProfData():  # Level-Location-Profession
    dt = pandas.read_csv('Core/Game/Profession_Item_drop.csv', names=["Location", "Lumberjack", "Miner", "Herbalism"],
                         skiprows=1).T.to_dict()

    lvl_dt = pandas.read_csv('Core/Game/Profession_xp.csv', names=["Level", "Xp Requirement"],
                             skiprows=1).T.to_dict()
    lvl_data = {x: lvl_dt[x]['Xp Requirement'] for x in lvl_dt if lvl_dt[x]['Xp Requirement'] is not np.nan}
    dt = {x: dt[x] for x in dt if dt[x]['Location'] is not np.nan}
    # dt['level_data'] = lvl_data
    return dt


data = load_ProfData()

for level in data:
    print(level, data[level])
