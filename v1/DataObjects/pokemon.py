import simplejson as json
import math


def load_src(name, fpath):
    import os, imp
    p = fpath if os.path.isabs(fpath) \
        else os.path.join(os.path.dirname(__file__), fpath)
    return imp.load_source(name, p)


load_src("projectFilesPath", "../projectFilesPath.py")
from projectFilesPath import *  # load python script from parent directory

class Singleton(type): #todo: implement with Rlock on resources for thread safety
    """ This is a Singleton metaclass. All classes affected by this metaclass 
    have the property that only one instance is created for each set of arguments 
    passed to the class constructor."""
    def __init__(cls, name, bases, dict):
        super(Singleton, cls).__init__(cls, bases, dict)
        cls._instanceDict = {}

    def __call__(cls, *args, **kwargs):
        argdict = {'args': args}
        argdict.update(kwargs)
        argset = frozenset(argdict)
        if argset not in cls._instanceDict:
            cls._instanceDict[argset] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instanceDict[argset]


class pokedexDAO(object):
    __metaclass__ = Singleton

    def __init__(self):
        self.database = {}
        self.createPokedexDatabase()

    def getName(self, pokemonID):  # returns a string
        return self.database[str(pokemonID)]['name']

    def getSpeed(self, pokemonID):  # returns an int
        return self.database[str(pokemonID)]['base_speed']

    def getType(self, pokemonID):  # returns a list
        return self.database[str(pokemonID)]['type']

    def getDmgWhenAttk(self,pokemonID): #returns a dictionary
        return self.database[str(pokemonID)]['dmg_when_atked']

    def getEvolveLevel(self, pokemonID):  # returns an int
        return self.database[str(pokemonID)]['evolve_level']

    def getEvolveID(self, pokemonID):  # returns an int
        return self.database[str(pokemonID)]['evolve_id']

    def getPokemon(self, pokemonID):  # returns a dict
        return self.database[str(pokemonID)]

    def getallPokeID(self):
        return self.database.keys()

    # def findEvolvePattern(self): # link between pokemon in evolution, stored in evolve_data.txt
    #     used2 = {}
    #     lst2 = []
    #     for i in range(1,151):
    #         if i not in used2 and str(i) in self.database:
    #             used2[str(i)] = None
    #             sub_lst2 = []
    #             sub_lst2.append(i)
    #             poke = self.database[str(i)]
    #             while poke['evolve_id'] != 0:
    #                 used2[poke['evolve_id']] = None
    #                 sub_lst2.append(poke['evolve_id'])
    #                 poke = self.database[str(poke['evolve_id'])]
    #             lst2.append(sub_lst2)
    #     file = 'evolve_data.txt'
    #     with open(file,'w+') as f:
    #         for i in range(len(lst2)):
    #             f.write(",".join(str(x) for x in lst2[i]))
    #             f.write("\n")

    # def findEvolvePattern2(self): #prints the corresponding evolve_level for the evolve_id in evolve_data.txt,-> data stored in evolve_data2.txt
    #     used = {}
    #     lst = []
    #     for i in range(1,151):
    #         if i not in used and str(i) in self.database:
    #             used[str(i)] = None
    #             sub_lst = []
    #             sub_lst.append(self.database[str(i)]['evolve_level'])
    #             poke = self.database[str(i)]
    #             while poke['evolve_id'] != 0:
    #                 used[poke['evolve_id']] = None
    #                 poke = self.database[str(poke['evolve_id'])]
    #                 sub_lst.append(poke['evolve_level'])
    #             lst.append(sub_lst)
    #     file = 'evolve_data2.txt'
    #     with open(file,'w+') as f:
    #         for i in range(len(lst)):
    #             f.write(",".join(str(x) for x in lst[i]))
    #             f.write("\n")

    # def add_base_level(self): #modifies the pokedex.json, adds base_level -> creates pokedexv3.json
    #     used2 = {}
    #     lst2 = []
    #     for i in range(1, 151):
    #         if i not in used2 and str(i) in self.database:
    #             used2[str(i)] = None
    #             sub_lst2 = []
    #             sub_lst2.append(i)
    #             poke = self.database[str(i)]
    #             while poke['evolve_id'] != 0:
    #                 used2[poke['evolve_id']] = None
    #                 sub_lst2.append(poke['evolve_id'])
    #                 poke = self.database[str(poke['evolve_id'])]
    #             lst2.append(sub_lst2)
    #
    #     used = {}
    #     lst = []
    #     for i in range(1,151):
    #         if i not in used and str(i) in self.database:
    #             used[str(i)] = None
    #             sub_lst = []
    #             sub_lst.append(self.database[str(i)]['evolve_level'])
    #             poke = self.database[str(i)]
    #             while poke['evolve_id'] != 0:
    #                 used[poke['evolve_id']] = None
    #                 poke = self.database[str(poke['evolve_id'])]
    #                 sub_lst.append(poke['evolve_level'])
    #             lst.append(sub_lst)
    #
    #     for i in range(len(lst2)):
    #         for j in range(len(lst2[i])):
    #             if j == 0:
    #                 self.database[str(lst2[i][j])]['base_level'] = 1
    #             else:
    #                 self.database[str(lst2[i][j])]['base_level'] = lst[i][j - 1]
    #     file = 'pokedexv3.json'
    #     with open(file,'w') as f:
    #         f.write(json.dumps(self.database, indent = 4, sort_keys = True))

    def createPokemon(self,pokemonID, random_ev):
        val = self.database[str(pokemonID)]

        aPokemon = pokemon(int(pokemonID), val['base_experience'], val['base_experience']*2, val['base_def'], val['base_atk'],
                           val['base_hp'], val['base_hp'],
                           val['base_level'], val['base_special_atk'], val['base_special_def'],random_ev)
        return aPokemon

    def createPokedexDatabase(self):
        self.database.update(json.loads(open(pokedexJSON_path).read()))


class pokemon(object):
    pokemonDatabase = pokedexDAO() # TODO: is this the best way to link up to pokemonDAO??

    def __init__(self, pokemonID, cur_experience, required_experience, defense, attack, max_hp, cur_hp, cur_level,
                 special_attack,
                 special_defense, effort_value):  # data is a dictionary containing the pokemon details
        self._id = pokemonID
        self._cur_exp = cur_experience
        self._req_exp = required_experience
        self._def = defense
        self._attk = attack
        self._max_hp = max_hp
        self._hp = cur_hp
        self._cur_lvl = cur_level
        self._sp_attk = special_attack
        self._sp_def = special_defense
        self._ev = effort_value

    def getpokemonID(self):
        return self._id

    pokemonID = property(getpokemonID)

    def getCurExp(self):
        return self._cur_exp

    def updateCurExp(self,
                  add_amount):  # TODO: faster way to calculate the new pokemon stats,do just once instead of having  many iterations
        progress = []
        while self._req_exp - self._cur_exp <= add_amount:
            add_amount -= self._req_exp - self._cur_exp
            self._cur_exp = self._req_exp
            if pokemon.pokemonDatabase.getEvolveLevel(self._id) == self._cur_lvl + 1:
                info = self._evolve()
                progress.append(info)
                # print ('evolved')
            else:
                info = self._levelUp()
                progress.append(info)
                # print ('level up')
        self._cur_exp += add_amount
        return progress

    curExp = property(getCurExp)

    def _levelUp(self):
        # cur_exp remains unchanged
        self._req_exp *= 2
        self._cur_lvl += 1
        self._max_hp = self._recal(self._max_hp)
        if self._hp != 0:
            self._hp = self._max_hp  # the pokemon's current hp level gets bumped up to max_hp
        self._attk = self._recal(self._attk)
        self._def = self._recal(self._def)
        self._sp_attk = self._recal(self._sp_attk)
        self._sp_def = self._recal(self._sp_def)
        return "Levelled up to LVL " + str(self._cur_lvl) + "."

    def _evolve(self):
        evolve_id = pokemon.pokemonDatabase.getEvolveID(self._id)
        evolve_into = pokemon.pokemonDatabase.getPokemon(evolve_id)
        self._id = evolve_id
        # cur_exp remains unchanged, val is >= evolve_id['base_experience']
        self._req_exp *= 2
        self._def = evolve_into['base_def']
        self._attk = evolve_into['base_atk']
        self._max_hp = evolve_into['base_hp']
        if self._hp != 0:
            self._hp = self._max_hp
        self._cur_lvl += 1
        self._sp_attk = evolve_into['base_special_atk']
        self._sp_def = evolve_into['base_special_def']
        return "Levelled up to LVL " + str(self._cur_lvl) + ".Evolved to " + pokemon.pokemonDatabase.getName(evolve_id)

    def getHP(self):
        return self._hp

    def setHP(self, val):
        self._hp = val

    hp = property(getHP, setHP)

    def getmaxHp(self):
        return self._max_hp

    max_hp = property(getmaxHp)

    def isAlive(self):
        if self._hp == 0:
            return False
        else:
            return True

    def getAttk(self):
        return self._attk
    attk = property(getAttk)

    def getDef(self):
        return self._def
    deff = property(getDef)

    def getSpAttk(self):
        return self._sp_attk
    sp_attk = property(getSpAttk)

    def getSpDef(self):
        return self._sp_def
    sp_def = property(getSpDef)

    def getCurLevel(self):
        return self._cur_lvl
    level = property(getCurLevel)

    def getSpeed(self):
        return pokemon.pokemonDatabase.getSpeed(self._id)

    def getName(self):
        return pokemon.pokemonDatabase.getName(self._id)

    def getElemental_Multiply(self,opponentID):
        my_Type = pokemon.pokemonDatabase.getType(self._id)
        opp_dmg_when_attk = pokemon.pokemonDatabase.getDmgWhenAttk(opponentID)
        max_multiply = 0
        for key, val in opp_dmg_when_attk.iteritems():
            if key in my_Type and  val > max_multiply:
                max_multiply = val

        return max_multiply

    def sameType(self, otherID):
        my_type = pokemon.pokemonDatabase.getType(self._id)
        other_type = pokemon.pokemonDatabase.getType(otherID)

        if bool(set(my_type) & set(other_type)):# check if two lists have shared elements
            return True
        else:
            return False

    def _recal(self, val):
        return int(math.ceil(val * (1.0 + self._ev)))




