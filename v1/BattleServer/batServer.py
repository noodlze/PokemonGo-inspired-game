from collections import deque
from twisted.python import log
from twisted.internet import protocol
from twisted.application import service
from DataObjects.battle import Battle
from DataObjects.player import *
from verifyProtocol import *

class BattleProtocol(JsonReceiver):
    STATE_AWAITING_OPPONENT = 1
    STATE_CHOOSING_POKEMON = 2
    STATE_AWAITING_BATTLE_START = 3  # the player have already picked their 1-3 pokemon
    STATE_MAKING_MOVE = 4
    STATE_AWAITING_MOVE = 5
    STATE_FINISHED = 6

    def __init__(self):
        self.battle = None
        self.opponent = None
        self._username = None  # player has not sent their username for identification purposes
        self._playerData = None  # is a player object instance
        self._state = None

    def getUsername(self):
        return self._username

    username = property(getUsername)

    def getState(self):
        return self._state

    state = property(getState)

    def connectionMade(self):
        peer = self.transport.getPeer()
        log.msg("Connection made from {0}:{1}".format(peer.host, peer.port))

    def connectionLost(self, reason):
        peer = self.transport.getPeer()
        log.msg("Connection lost from {0}:{1}".format(peer.host, peer.port))
        self.factory.playerDisconnected(self)

        if self._state != None:
            self._playerData.savePlayerData()

        if (self._state == None or self._state == BattleProtocol.STATE_AWAITING_OPPONENT or self._state == BattleProtocol.STATE_CHOOSING_POKEMON or self._state == BattleProtocol.STATE_AWAITING_BATTLE_START) and self.opponent is not None :# player disconnects before sending their username
            self.opponent.sendResponse('opponent_disconnected')
            self.opponent.transport.loseConnection()
        elif self._state != BattleProtocol.STATE_FINISHED and self.opponent is not None:  # when one person disconnects unexpectedly
            self._processSurrender(self._username)

    def objectReceived(self, data):
        """Decodes and runs a command from the received data"""
        log.msg('Data received: {0}'.format(data))

        if not data.has_key('command'):
            self.sendError("Empty command")
            return

        command = data['command']
        params = data.get('params', {})

        self.runCommand(command, **params)

    def invalidJsonReceived(self, data):
        log.msg("Invalid JSON data received:\n" + data)
        self.sendError("Invalid JSON data")

    def sendError(self, message):
        self.sendResponse('error', message=message)

    def sendResponse(self, command, **params):
        self.sendObject(command=command, params=params)
        log.msg("Data sent: {0}({1})".format(command, params))

    def runCommand(self, command, **params):
        commands = {
            'identification': self._setUsername,
            'pokemon_chosen': self._updatePokeBag,
            'attack': self._attack,
            'switch': self._switch,
            'switch_attack': self._pickActivePoke,
            'transfer': self._transferExp,
            'revive': self._revivePokemon,
            'surrender': self._processSurrender
        }

        if not commands.has_key(command):
            self.sendError("Invalid command: \"{0}\"".format(command))
            return

        try:
            print (params)
            commands[command](**params)
        except (ValueError, TypeError) as e:
            self.sendError("Error executing command \"{0}\": {1}".format(command, e))

    def _revivePokemon(self, pokemonID):
        (result, new_hp) = self._playerData.revivePoke(pokemonID)
        if result == True:
            self.sendResponse("revive_success", pokemon = pokemonID, hp = new_hp)
        else:
            self.sendResponse("revive_failure")

    def _processSurrender(self, madeBy):
        self._state = BattleProtocol.STATE_FINISHED
        self._playerData.savePlayerData()
        you = self._username
        self.opponent.endBattle(loser = you)
        self.transport.loseConnection()

    def _transferExp(self,giver, receiver):
        (updates_log, new_Exp ) = self._playerData.transferExp(giverID = giver, receiverID= receiver)
        if updates_log == None and new_Exp == None:
            self.sendError("Two pokemon are not of the same type. Transfer of experience points failed")
        else:
            self._sendPlayerData()
            self.sendResponse('exp_change', data=updates_log , new_Exp = new_Exp, pokemonID= receiver)

    def _sendPlayerData(self):
        allData = self._playerData.getAllItems()
        new_dict = {}
        for kind, value in allData.iteritems():  # TODO: rewrite ?? ->duplicate with player code -> CRUDE code writing
            if kind == 'alive' or kind == 'fainted':
                new_dict[kind] = {}
                for key, data in value.iteritems():
                    new_dict[kind][key] = data.__dict__  # converts pokemon object to dictionary
            else:
                new_dict[kind] = value
        self.sendResponse("pokemon_data", data=new_dict)

    def _setUsername(self,
                     val):  # after establishing a connection, the user sends their username so the server can identify the player's data
        if val in validClients:
            self._username = val
            self._playerData = player(val)

            if self._playerData.getAlivePokemon() == 0:
                self.sendError("You have 0 healthy pokemon that can battle")
                self.factory.playerDisconnected(self)
                self.transport.loseConnection()  # disconnect from the battle server

            else:
                self._state = BattleProtocol.STATE_AWAITING_OPPONENT  # tells us the player has joined the battle
                self.sendResponse("awaiting_opponent")
                self._sendPlayerData()
                self.factory.findOpponent(self)  # find an opponent to join the battle
        else:
            self.sendError("You have not logged in through the authentication server. Please do so before attempting another connection to the battle server")
            self.transport.loseConnection()

    def choosePokemon(self, Battle_game, opponent):
        self.battle = Battle_game
        self.opponent = opponent
        self.battle.addPlayer(self._username)
        self.opponent.sendResponse("opponent_name", name = self._username)
        self._state = BattleProtocol.STATE_CHOOSING_POKEMON

        self.sendResponse('choose_pokemon')  # already sent the player's pokemon data in _setUsername method

    def _updatePokeBag(self,
                       data):  # data is a LIST containing the id of the chosen pokemon, range for len(data) is [1,3]
        self._state = BattleProtocol.STATE_AWAITING_BATTLE_START

        pokeBag = {}
        for id in data:
            pokeBag[id] = self._playerData.getPokemon(id)
        self.battle.updatePokeBag(self._username, pokeBag)

        self._changeBattlePoke(data[0])

        if self.opponent.state == BattleProtocol.STATE_AWAITING_BATTLE_START:  # both players have picked 1-3 poke
            self.battle.battleStarted = True  # changing the value of battleStarted from False -> True will trigger the battle instance to determine and set the first player to go (i.e. set the value of current_player)
        # set the pokemon used for battle at the beginning of the battle

            self.opponent.startBattle()
            self.startBattle()


    def _changeBattlePoke(self, pokemonID, doubleMove = False):
        self.battle.setActivePokemon(self._username, pokemonID)

        new_Poke = self.battle.pokeInfo(self._username)

        self.sendResponse('battlePokemon_changed', madeBy=self._username,
                          switched_Poke=new_Poke, doubleMove = doubleMove)  # notify players that battle pokemon has changed
        self.opponent.sendResponse('battlePokemon_changed', madeBy=self._username, switched_Poke=new_Poke,doubleMove = doubleMove)

    def startBattle(self):
        self.battle.setOppReward(self._username, self._playerData.getAccumExp())

        if self.battle.currentPlayer == self._username:
            self._state = BattleProtocol.STATE_MAKING_MOVE
        else:
            self._state = BattleProtocol.STATE_AWAITING_MOVE

        (yourID, opponent_poke_info) = self.battle.getBattleInfo(self._username)
        self.sendResponse('battleInfo', yourPokeID=yourID, oppInfo=opponent_poke_info)
        self.sendResponse("start", turn=self.battle.currentPlayer)

    def _attack(self):
        if self._state == BattleProtocol.STATE_MAKING_MOVE:
            (dmg, new_hp, isFinished) = self.battle.attack_from(self._username)  # username of player making the attack

            if new_hp == 0:
                opp_poke_id = self.battle.removeOpponentActivePokemon(self._username)
                self.opponent.moveToFainted(opp_poke_id)
            attacker = self._username  # side making the move
            self.sendResponse('attack_made', madeBy=attacker, damage=dmg, hp=new_hp)
            self.opponent.sendResponse('attack_made', madeBy=attacker, damage=dmg, hp=new_hp)
            if isFinished:
                self.endBattle(winner=self._username)
                self.opponent.endBattle(winner=self._username)
            else:
                self._moveMade(BattleProtocol.STATE_AWAITING_MOVE)
                self.opponent.makeMoveFromOpponent()
        else:
            self.sendError("Not your turn.Your pokemon can't attack right now")

    def moveToFainted(self, pokemonID):  # update self._playerData
        print(self.username + " moving pokemon id " + pokemonID + " to fainted")

        self._playerData.getFaintedPokemon()[pokemonID] = self._playerData.getAlivePokemon()[pokemonID]
        del self._playerData.getAlivePokemon()[pokemonID]

    def makeMoveFromOpponent(self):
        if self._state == BattleProtocol.STATE_AWAITING_MOVE:
            self._moveMade(BattleProtocol.STATE_MAKING_MOVE)
        else:
            # TODO: handle "Unexpected move from opponent"
            raise Exception("Opponent sent us a move but we weren't expecting that")

    def _moveMade(self, new_state):
        if self.battle.isFinished:
            self._state = BattleProtocol.STATE_FINISHED
        else:
            self._state = new_state

    def _pickActivePoke(self, pokemonID):
        if self._state == BattleProtocol.STATE_MAKING_MOVE and self.battle.battleStarted and self.battle.hasActivePoke(
                self._username) is False:
            self._changeBattlePoke(pokemonID, True)  # TODO: catch exception if you cannot change to that pokemon
            self._attack()
        else:
            self.sendError("Unable to switch pokemon and an attack in one turn")

    def _switch(self, pokemonID):
        if self._state == BattleProtocol.STATE_MAKING_MOVE:
            self._changeBattlePoke(pokemonID)

            self._moveMade(BattleProtocol.STATE_AWAITING_MOVE)
            self.opponent.makeMoveFromOpponent()
        else:
            self.sendError("Not your turn. Can't switch your pokemon right now")

    def endBattle(self, winner= None, loser = None):
        self._state = BattleProtocol.STATE_FINISHED
        if winner is not None:
            if self._username == winner:
                self._youWon()
            else:
                self._youLost()
        else:
            if self._username == loser:
                self._youLost()
            else:
                self._youWon()

        self.transport.loseConnection()  # disconnect from the client

    def _youWon(self):
        # up to the client server to update their copy of the _playerData and inform the user whether the pokemon has leveled and what level they are at
        # fainted pokemon still get exp points
        amount = self.battle.getWinReward(self._username)
        updates_log = self._playerData.expAwarded(amount)

        self._playerData.savePlayerData()
        self.sendResponse('battle_end', verdict='win', reward=amount, data = updates_log)

    def _youLost(self):
        self._playerData.savePlayerData()
        self.sendResponse('battle_end', verdict='lost')


class BattleFactory(protocol.ServerFactory):
    protocol = BattleProtocol
    queue = deque()

    def __init__(self, service):
        self.service = service
        from twisted.internet import reactor
        reactor.connectTCP('127.0.0.1',21000,verifyClientFactory())

    def findOpponent(self, player):
        try:
            opponent = self.queue.popleft()
        except IndexError:
            self.queue.append(player)
        else:
            game = Battle()
            player.choosePokemon(game, opponent)
            opponent.choosePokemon(game, player)

    def playerDisconnected(self, player):
        try:
            self.queue.remove(player)
        except ValueError:
            pass

class GameService(service.Service):
    pass