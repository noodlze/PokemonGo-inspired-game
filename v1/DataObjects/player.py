from pokemon import *

class playerDataDAO(object):
    __metaclass__ = Singleton
    def getPlayerData(self, username):  # read data from <username>.json file, returns dictionary of pokemon objects
        playerPokeBag = json.loads(open(getPlayerDataJSON_path(username)).read())
        pokeDict = {}
        for kind, value in playerPokeBag.iteritems():
            if kind == 'alive' or kind == 'fainted':
                pokeDict[kind] = {}
                for key, val in value.iteritems():
                    aPokemon = pokemon(val['_id'], val['_cur_exp'], val['_req_exp'], val['_def'], val['_attk'],
                                   val['_max_hp'], val['_hp'],
                                   val['_cur_lvl'], val['_sp_attk'], val['_sp_def'], val['_ev'])
                    pokeDict[kind][key] = aPokemon
            else:
                pokeDict[kind] = value
        return pokeDict

    def savePlayerData(self, username,
                       data):  # data is a dictionary, where key = player's pokemon id, val = pokemon object
        PlayerDataJSON_path = getPlayerDataJSON_path(username)
        new_dict = {}

        with open(PlayerDataJSON_path, 'w') as f:
            for kind, value in data.iteritems():
                if kind == 'alive' or kind == 'fainted':
                    new_dict[kind] = {}
                    for key, val in value.iteritems():
                        new_dict[kind][key] = val.__dict__  # converts pokemon object to dictionary
                else:
                    new_dict[kind] = value
            f.write(json.dumps(new_dict, indent=4, sort_keys=True))
        # print(new_dict)
        print("{0}\'s data was successfully updated".format(username))

class player(object):
    def __init__(self, username):
        # bag to store pokemon
        self._username = username
        self._bag = playerDataDAO().getPlayerData(username)

    def revivePoke(self, pokemonID):
        if pokemonID in self._bag['fainted'].keys() and 'berries' in self._bag.keys() and self._bag['berries'] > 0:
            new_hp = self._bag['fainted'][pokemonID].max_hp
            self._bag['fainted'][pokemonID].hp = new_hp
            self._bag['alive'][pokemonID] = self._bag['fainted'][pokemonID]
            del self._bag['fainted'][pokemonID]
            self._bag['berries'] -= 1
            return (True, new_hp)
        else:
            return False

    def addPokemon(self, pokemon):
        # pokemon == pokemon object instance
        # find the first free  player key in the dict
        currentNo = len(self._bag['alive']) + len(self._bag['fainted'])
        if currentNo >= 200:
            return False
        else:
            self._bag['pokeballs'] -= 1 # used up one pokeball to catch the pokemon
            index = 1
            while 1:
                if str(index) not in self._bag['alive'].keys() and str(index) not in self._bag['fainted'].keys():
                    self._bag['alive'][str(index)] = pokemon
                    # print("adding pokemon " + str(index))
                    # self.printBagContents()
                    break
                else:
                    index += 1
            return True

    def printBagContents(self):
        for kind, val in self._bag.iteritems():
            print(kind)
            if kind == 'alive' or kind == 'fainted':
                for id, obj in val.iteritems():
                    print (id)
                    print(obj.__dict__)
            else:
                print(kind,val)

    def hasPokeBalls(self):
        if 'pokeballs' not in self._bag.keys():
            return False
        elif self._bag['pokeballs'] > 0:
            return True
        else:
            return False

    def getAllItems(self):
        return self._bag

    def getPokemon(self,pokemonID):
        for kind in ['alive','fainted']:
            if pokemonID in self._bag[kind]:
                return self._bag[kind][pokemonID]

    def getAlivePokemon(self):
        return self._bag['alive']

    def addItem(self, type):
        if type not in self._bag.keys():
            self._bag[type] = 1
        else:
            self._bag[type] += 1

    def getFaintedPokemon(self):
        return self._bag['fainted']

    def getAccumExp(self):
        accumExp = 0
        for poke_dict in self._bag.values(): # is a dictionary of poke
            if isinstance(poke_dict, dict):
                for poke_info in poke_dict.values():
                    accumExp += poke_info.curExp
        return int(math.ceil(float(accumExp)/3))

    def transferExp(self, giverID , receiverID):
        if self._bag['alive'][giverID].sameType(receiverID):
            giveAmount = self._bag['alive'][giverID].curExp
            del self._bag['alive'][giverID] # delete pokemon from player's bag

            receiverPoke = self._bag['alive'][receiverID]
            exp_log = receiverPoke.updateCurExp(giveAmount)
            return (exp_log,receiverPoke.curExp) # level up/evolve info after adding exp
        else:
            return (None, None)

    def expAwarded(self, add_amount):
        poke_log = {}
        for poke_dict in self._bag.values():
            if isinstance(poke_dict,dict):
                for poke_info in poke_dict.values():
                    poke_log[poke_info.pokemonID] = poke_info.updateCurExp(add_amount) # NOTE you pass in add_amount to setter function, this amount is added to cur_Exp
        # self.printBagContents()
        return poke_log # level up/evolve info after adding exp for all pokemon in bag

    def savePlayerData(self):
        # self.printBagContents()
        playerDataDAO().savePlayerData(self._username, self._bag)

# t1 = playerDataDAO()
# t2 = playerDataDAO()
# print(t1)
# print(t2)
# assert(id(t1) == id(t2))
# a = t1.getPlayerData('thuypham')
# a['2'].curExp = 0
# print (a['2'].__dict__)
# print(a['2'].curExp)
# print(a['2'].isAlive())
# print (a['1'].__dict__)
# t1.savePlayerData('thuypham', a)