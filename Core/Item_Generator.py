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


lvl_unlock = [x for x in range(104) if x % 4 is 0]
lvl_res = [(str(x) + 'A', str(x) + 'B', str(x) + 'C') for x in lvl_unlock]
randloc = [str(x) + 'L' for x in lvl_unlock]
gprof = ['Miner', 'Lumberjack', 'Gatherer']
cprof = ['Smith', 'Outfitter', 'Chef']
craft_ratios = [(5, 3, 2), (3, 5, 2), (2, 3, 5)]
gear = ['Hat', 'Chest', 'tool', 'Legging', ' Food']
tier = ['T' + str(x) for x in range(10)]


def is_even(no):
    return True if no % 2 == 0 else False


no = 1
t = 0
for level in lvl_unlock:
    ind = lvl_unlock.index(level)
    # print('At Level {}, you can : '.format(level))
    # print('G: Miner: {} Lumberjack: {} Gatherer: {}'.format(lvl_res[ind][0], lvl_res[ind][1], lvl_res[ind][2]))
    # print('Can Craft :')
    if no == 5:
        no = 1
    # food-tool hat chest legging
    if no == 1:
        rr = craft_ratios[2]
        print(
            '{} - recipe ({}x {}, {}x {}, {}x {})'.format((tier[t] + ' Food'), 1 * rr[0] * (t + 1) * 4, lvl_res[ind][0],
                                                          1 * rr[1] * (t + 1) * 4, lvl_res[ind][1],
                                                          1 * rr[2] * (t + 1) * 4, lvl_res[ind][2]))

        rr = craft_ratios[0]
        print(
            '{} - recipe ({}x {}, {}x {}, {}x {})'.format((tier[t] + ' Tool'), 1 * rr[0] * (t + 1) * 4, lvl_res[ind][0],
                                                          1 * rr[1] * (t + 1) * 4, lvl_res[ind][1],
                                                          1 * rr[2] * (t + 1) * 4, lvl_res[ind][2]))

    elif no == 2:
        rr = craft_ratios[1]
        print(
            '{} - recipe ({}x {}, {}x {}, {}x {})'.format((tier[t] + ' Hat'), 1 * rr[0] * (t + 1) * 4, lvl_res[ind][0],
                                                          1 * rr[1] * (t + 1) * 4, lvl_res[ind][1],
                                                          1 * rr[2] * (t + 1) * 4, lvl_res[ind][2]))

    elif no == 3:
        rr = craft_ratios[0]
        print('{} - recipe ({}x {}, {}x {}, {}x {})'.format((tier[t] + ' Chest'), 1 * rr[0] * (t + 1) * 4,
                                                            lvl_res[ind][0], 1 * rr[1] * (t + 1) * 4, lvl_res[ind][1],
                                                            1 * rr[2] * (t + 1) * 4, lvl_res[ind][2]))

    elif no == 4:
        rr = craft_ratios[1]
        print('{} - recipe ({}x {}, {}x {}, {}x {})'.format((tier[t] + ' Leggings'), 1 * rr[0] * (t + 1) * 4,
                                                            lvl_res[ind][0], 1 * rr[1] * (t + 1) * 4, lvl_res[ind][1],
                                                            1 * rr[2] * (t + 1) * 4, lvl_res[ind][2]))

    if no == 4:
        print('<<<<<<<<<<<{}>>>>>>>>>>>'.format(tier[t]))
        t += 1
    no += 1

data = load_ProfData()

for level in data:
    print(level, data[level])
