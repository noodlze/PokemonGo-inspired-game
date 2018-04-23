from DataObjects.player import *
import random, math


class Battle(object):
    def __init__(self):
        self.info = {}
        self.players = []

        self._current_Player = None
        self._battleStarted = False
        self._isFinished = False

    def addPlayer(self, username):
        self.players.append(username)

        self.info[username] = {}
        self.info[username][
            'bag'] = None  # contains a dictionary where key = id and value = reference to a pokemon object instance
        self.info[username]['activePokemon_id'] = None  # id of the active pokemon
        self.info[username]['norm_attk'] = None
        self.info[username]['sp_attk'] = None
        self.info[username]['win_reward'] = None  # stores 1/3 of the accumulated xp of all pokemon of the opponent of the the player = username

    def updatePokeBag(self, username, data):
        # print('pokebag contents')
        # print(data)
        self.info[username]['bag'] = data
        # print(self.info[username]['bag'])

    def setOppReward(self, username, accumExp):
        opponent = self.players[abs(self.players.index(username) - 1)]
        self.info[opponent]['win_reward'] = accumExp

    def getWinReward(self, username):
        return self.info[username]['win_reward']

    def setActivePokemon(self, username, pokemonID):
        self.info[username]['activePokemon_id'] = pokemonID
        # print(self.info[username]['activePokemon_id'] )
        self.calculateAttkDmg()  # for both players since one of the active pokemon has been changed

    def calculateAttkDmg(self):
        if self.info[self.players[0]]['activePokemon_id'] is not None and self.info[self.players[1]][
            'activePokemon_id'] is not None:
            for i in range(len(self.players)):
                your_poke_id = self.info[self.players[i]]['activePokemon_id']
                your_poke = self.info[self.players[i]]['bag'][your_poke_id]
                opp_poke_id = self.info[self.players[abs(i - 1)]]['activePokemon_id']
                opp_poke = self.info[self.players[abs(i - 1)]]['bag'][opp_poke_id]
                # print (your_poke.attk)
                # print (opp_poke.deff)
                # print(your_poke.attk - opp_poke.deff)
                self.info[self.players[i]]['norm_attk'] = max(your_poke.attk - opp_poke.deff, 0)
                # print(self.info[self.players[i]]['norm_attk'])
                self.info[self.players[i]]['sp_attk'] = max(int(math.ceil(
                    your_poke.sp_attk * your_poke.getElemental_Multiply(opp_poke.pokemonID) - opp_poke.sp_def)), 0)
                # print(your_poke.sp_attk * your_poke.getElemental_Multiply(opp_poke.pokemonID) - opp_poke.sp_def)


    def removeOpponentActivePokemon(self, username):
        # returns the activePokemon_id for the removed activePokemon
        opponent = self.players[abs(self.players.index(username) - 1)]
        activePokemon_id = self.info[opponent]['activePokemon_id']

        self.info[opponent]['activePokemon_id'] = None

        return activePokemon_id

    def getFinished(self):
        return self._isFinished

    isFinished = property(getFinished)

    def getCurrentPlayer(self):
        return self._current_Player

    currentPlayer = property(getCurrentPlayer)

    def getBattleStarted(self):
        return self._battleStarted

    def setBattleStarted(self, bool):
        self._battleStarted = bool
        if self._battleStarted:  # changed from False to True
            self._setFirstPlayer()

    battleStarted = property(getBattleStarted, setBattleStarted)

    def hasActivePoke(self, username):
        if self.info[username]['activePokemon_id'] == None:
            return False
        else:
            return True

    def _setFirstPlayer(self):  # changes the value of _current_Player from None to 'A' or 'B'
        speed = []
        for username in self.players:
            poke_id = self.info[username]['activePokemon_id']
            speed.append(self.info[username]['bag'][poke_id].getSpeed())

        if speed[0] == speed[1]:
            self._current_Player = random.choice(self.players)
        elif speed[0] > speed[1]:
            self._current_Player = self.players[0]
        else:
            self._current_Player = self.players[1]

    def getBattleInfo(self, username):
        yourActivePokeID = self.info[username]['activePokemon_id']
        opponent = self.players[abs(self.players.index(username) - 1)]

        return (yourActivePokeID, self.pokeInfo(opponent))

    def pokeInfo(self, username):
        pokeInfo = {}
        poke_id = self.info[username]['activePokemon_id']
        pokemon = self.info[username]['bag'][poke_id]
        pokeInfo['name'] = pokemon.getName()
        pokeInfo['hp'] = pokemon.hp
        pokeInfo['level'] = pokemon.level
        return pokeInfo

    def attack_from(self, username):

        attk_type = 'norm_attk'
        val = random.random()
        if val >= 0.8:
            attk_type = 'sp_attk'
            # print("special attack used")
        dmgToOpp = self.info[username][attk_type]
        # print("damage was " + str(dmgToOpp))
        opponent = self.players[abs(self.players.index(username) - 1)]
        # print(opponent)
        opp_poke_id = self.info[opponent]['activePokemon_id']
        opp_poke = self.info[opponent]['bag'][str(opp_poke_id)]
        opp_poke.hp = max(opp_poke.hp - dmgToOpp, 0)
        # print(opp_poke.__dict__)
        isFinished = False
        if opp_poke.hp == 0:
            self._removePoke(opponent, opp_poke_id)  # remove from the bag in self.info
            if len(self.info[opponent]['bag']) == 0:
                self._battleEnded()
                isFinished = True

        return (dmgToOpp, opp_poke.hp, isFinished)

    def _removePoke(self, username, pokemonID):
        if pokemonID in self.info[username]['bag']:
            del self.info[username]['bag'][str(pokemonID)]

    def _battleEnded(self):
        self._isFinished = True
