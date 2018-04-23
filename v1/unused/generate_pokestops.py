import random
from projectFilesPath import *
amount = 5
worldSz = 5
x = worldSz
y = worldSz

# pokestops = []
#
# def gen_pokestops():
#     count = 1
#     while( count <= amount):
#         x = random.randint(0, worldSz - 1)
#         y = random.randint(0, worldSz - 1)
#         try:
#             i = pokestops.index((x,y))
#         except ValueError:
#             pokestops.append((x,y))
#             count += 1
#         else:
#             pass
#
# gen_pokestops()
# print(pokestops)
#
# with open(dataFile_path + "/pokestops5.txt", 'w+') as f:
#     for i in range(len(pokestops)):
#         f.write(str(pokestops[i][0]) + " " + str(pokestops[i][1]) + "\n")

def addPokestops():
    lst = []
    with open("data/pokestops5.txt",'r') as f:
        for line in f:
            line = line.rstrip("\n\r")
            (x,y) = line.split(' ')
            lst.append((x,y))
    return lst

pokestops = addPokestops()
print(pokestops)

