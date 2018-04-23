# no option to choose your opponent -> easier to code
from functools import partial
from twisted.internet import protocol, stdio
from twisted.protocols import basic
def load_src(name, fpath): # used to access a .py file not located in current directory or lower directory
    import os, imp
    p = fpath if os.path.isabs(fpath) \
        else os.path.join(os.path.dirname(__file__), fpath)
    return imp.load_source(name, p)


load_src("pokemon", "../DataObjects/pokemon.py")
from pokemon import pokedexDAO # --> needs to be in upper directory
load_src("protocol", "../protocol.py")
from protocol import JsonReceiver
import re
import os
from twisted.internet import reactor
from clint.textui import colored
import sys


Token_Path = 'data/access_token.txt'
username = ''
# if it does not exist -> redirect user to validation C ?
pokedex = pokedexDAO()


class UserInputProtocol(basic.LineReceiver):
    from os import linesep
    delimiter = linesep

    def __init__(self, callback):
        self.callback = callback

    def lineReceived(self, line):
        self.callback(line)


class BattleClientProtocol(JsonReceiver):
    STATE_JOINING_BATTLE = 1
    STATE_PRE_BATTLE = 2
    STATE_CHOOSE_POKEMON = 3
    STATE_BATTLE = 4
    STATE_POST_BATTLE = 5

    def __init__(self):
        self.playerData = {}
        self._pokeBag = []
        self._activePokemon_name = None
        self._activePokemon_ID = None

        self._opp_name = None
        self._opp_pokemon = None  # A DICT containing opponent's pokemon info
        self._state = None
        self._makingMove = None

        self.debug_enabled = False

    def out(self, *messages):
        for message in messages:
            print(message)

    def debug(self, *messages):
        if self.debug_enabled:
            self.out(*messages)

    def connectionMade(self):
        stdio.StandardIO(UserInputProtocol(self.userInputReceived))
        self.out(colored.blue("Connected to the battle server..."))
        if os.path.exists(Token_Path): # attempting to read access_token.txt
            global username
            file = open(Token_Path, 'r')
            username = file.readline()
            username = username.rstrip("\n\r")
            file.close()
            self.out("Atttempting to connect as " + colored.green(username))
            self.sendCommand(command="identification", val=username)
        else:
            self.out(colored.red("Looks like you have no user data; cannot locate access_token.txt. Please login through the authentication server"))
            self.transport.loseConnection()

    def userInputReceived(self, string):
        commands = {
            '?': self._printHelp,
            'h': self._printHelp,
            'help': self._printHelp,
            'open': self._viewPlayerData,
            'info': self._viewPokemon,
            'add': self._addToBag,
            'remove': self._removeFromBag,
            'transfer': self._transferExp,
            'view': self._viewBagContents,
            'confirm': self._sendChosenPokemon,
            "attack": self._makeAttack,
            "pick": self._whenPokeFaints,
            "switch": self._makeSwitch,
            "surrender": self._makeSurrender,
            'revive': self._revivePokemon,
            'q': self._exitGame,
            'quit': self._exitGame,
            'exit': self._exitGame,

        }
        if string == '':  # empty string
            return

        params = filter(len, string.split(' ', 1))
        command, params = params[0], params[1:]

        # TODO: cleanup regex code below --> MESSY
        # check if match 'info' command
        r = re.compile('\s*info\s*([0-9]+)\s*')
        res = r.match(string)
        if res:
            command = 'info'
            params = res.groups()
        # check if match 'add' command
        r = re.compile('\s*add\s*([0-9]+)\s*')
        res = r.match(string)
        if res:
            command = 'add'
            params = res.groups()
        # check if match 'remove' command
        r = re.compile('\s*remove\s*([0-9]+)\s*')
        res = r.match(string)
        if res:
            command = 'remove'
            params = res.groups()
        # check if match 'switch' command
        r = re.compile('\s*switch\s*([0-9]+)\s*')
        res = r.match(string)
        if res:
            command = 'switch'
            params = res.groups()
        # check if match 'pick <id> attack' command
        r = re.compile('\s*pick\s*([0-9]+)\s*attack')
        res = r.match(string)
        if res:
            command = 'pick'
            params = res.groups()
        # check if match 'from <id> to <id>' command
        r = re.compile('\s*from\s*([0-9]+)\s*to\s*([0-9]+)\s*')
        res = r.match(string)
        if res:
            command = 'transfer'
            params = res.groups()
        # check if match 'revive' command
        r = re.compile('\s*revive\s*([0-9]+)\s*')
        res = r.match(string)
        if res:
            command = 'revive'
            params = res.groups()


        if not command:
            return

        if command not in commands:
            self.out(colored.red("Invalid command"))
            return

        try:
            commands[command](*params)
        except TypeError as e:
            self.out(colored.red("Invalid command parameters: {0}".format(e)))

    def _revivePokemon(self, id):
        if id in self.playerData['fainted'].keys():
            try:
                i = self.playerData['berries']
            except KeyError:
                self.out(colored.red("You do not have any berries\n"))
                return
            else:
                if i == 0:
                    self.out(colored.red("You do not have any berries\n"))
                    return

                if self._state != BattleClientProtocol.STATE_BATTLE:
                    self.sendCommand("revive",pokemonID = id)
                else:
                    self.out(colored.magenta("Command is not currently available\n"))
        else:
            self.out(colored.red("Pokemon is healthy. Berries can only be used on fainted pokemon\n"))

    def _transferExp(self,giverID, receiverID):
        if self._state != BattleClientProtocol.STATE_BATTLE:
            if giverID in self.playerData['alive'] and receiverID in self.playerData['alive']:
                self.sendCommand('transfer', giver = giverID, receiver = receiverID) #update playerData stored on server
            else:
                self.out(colored.red("Cannot transfer experience points when there is one or more fainted pokemon"))
        else:
            self.out(colored.magenta("Command is not currently available\n"))

    def _exitGame(self):
        self.transport.loseConnection()

    def _makeAttack(self):
        if self._state != BattleClientProtocol.STATE_BATTLE:
            self.out(colored.magenta("Command is not currently available\n"))
        elif self._makingMove != username:
            self.out(colored.red("It's not your turn. Can't attack"))
        else:
            self.sendCommand("attack")

    def _makeSwitch(self, id):
        if self._state != BattleClientProtocol.STATE_BATTLE:
            self.out(colored.magenta("Command is not currently available\n"))
        elif self._makingMove != username:
            self.out(colored.red("It's not your turn. Can't switch pokemon"))
        else:
            self._activePokemon_ID = id
            self._activePokemon_name = pokedex.getName(self.playerData['alive'][self._activePokemon_ID][
                                                           '_id'])  # TODO: error checking mechanism, when the server rejects switch
            self.sendCommand("switch", pokemonID=id)

    def _makeSurrender(self):
        if self._state != BattleClientProtocol.STATE_BATTLE:
            self.out(colored.magenta("Command is not currently available\n"))
        else:
            self.out(colored.red("You forfeited the battle"))
            self.sendCommand("surrender", madeBy = username)

    def _removeFromBag(self, id):
        if self._state == BattleClientProtocol.STATE_CHOOSE_POKEMON:
            if id in self._pokeBag:
                self._pokeBag.remove(id)
                self.out(colored.blue('Removed pokemon with id = ' + id + ' from pokemon battle bag'))
            else:
                self.out(colored.red('pokemon with id = ' + id + ' not in pokemon battle bag'))
        else:
            self.out(colored.magenta("Command is not currently available\n"))

    def _viewBagContents(self):
        if self._state != BattleClientProtocol.STATE_JOINING_BATTLE and self._state != BattleClientProtocol.STATE_PRE_BATTLE :
            if self._activePokemon_name != None and self._activePokemon_ID != None:
                self.out(colored.blue("\nActive pokemon id: ") + colored.green(str(self._activePokemon_ID)),
                     colored.blue("Active pokemon name: ") + colored.green(self._activePokemon_name))
            if len(self._pokeBag) == 0:
                self.out(colored.red("No pokemon selected for battle\n"))
            for id in self._pokeBag:
                self._viewPokemon(id)
        else:
            self.out(colored.magenta("Command is not currently available\n"))

    def _addToBag(self, id):
        if self._state == BattleClientProtocol.STATE_CHOOSE_POKEMON:
            if len(self._pokeBag) >= 3:
                self.out(colored.red("You cannot select more than 3 pokemon to join the upcoming battle\n"))
            elif id not in self._pokeBag and id not in self.playerData['fainted'] and id in self.playerData['alive']:
                self._pokeBag.append(id)
                self.out(colored.blue('pokemon with id = ' + id + ' added to selection for the upcoming battle\n'))
            else:
                self.out(colored.red('Cannot use pokemon with id = ' + id + " in the upcoming battle\n"))
        else:
            self.out(colored.magenta("Command is not currently available\n"))

    def _sendChosenPokemon(self):
        if self._state == BattleClientProtocol.STATE_CHOOSE_POKEMON:
            if len(self._pokeBag) >= 1:
                self.sendCommand('pokemon_chosen', data=self._pokeBag)
                self._activePokemon_ID = self._pokeBag[0]
                self._activePokemon_name = pokedex.getName(self.playerData['alive'][self._activePokemon_ID]['_id'])  # first pokemon to be sent out

                self._state = BattleClientProtocol.STATE_PRE_BATTLE
            else:
                self.out("You must choose at least 1 pokemon for the battle")
        else:
            self.out(colored.magenta("Command is not currently available\n"))

    def sendCommand(self, command, **params):
        self.sendObject(command=command, params=params)

    def objectReceived(self, obj):
        self.debug("Data received: {0}".format(obj))
        if obj.has_key('command'):
            command = obj['command']
            params = obj.get('params', {})
            self.receiveCommand(command, **params)

    def invalidJsonReceived(self, data):
        self.debug("Invalid JSON data received: {0}".format(data))

    def receiveCommand(self, command, **params):
        commands = {
            'awaiting_opponent': partial(self.serverMessage, "Waiting for an opponent to join the battle..."),
            'opponent_name': self._updateOpp_name,
            'choose_pokemon': self._choosePokemon,
            'opponent_disconnected': partial(self.serverMessage, "The opponent left before the battle started"),
            'pokemon_data': self._savePokeData,
            'error': self.serverError,
            'battleInfo': self._battleInfo,
            'start': self._battleStarted,
            'attack_made': self._processAttack,
            'battlePokemon_changed': self._processSwitch,
            'exp_change': self._displayExpInfo,
            'revive_success': self._processRevive,
            'revive_failure': partial(self.serverError, "Pokemon could not be revived. Please check you have at least 1 berry"),
            'battle_end': self._battleEnd
        }

        if command not in commands:
            self.debug("Invalid command received: {0}".format(command))
            return

        try:
            commands[command](**params)
        except TypeError as e:
            self.debug("Invalid command parameters received: {0}".format(e))

    def _processRevive(self, pokemon, hp):
        self.out("Pokemon with id " + colored.green(str(pokemon))  + " was successfully revived to full health: " + colored.green(str(hp) + "/" + str(hp)) + " HP\n")

        self.playerData['berries'] -= 1
        self.playerData['fainted'][pokemon]['_hp'] = hp
        self.playerData['alive'][pokemon] = self.playerData['fainted'][pokemon]
        del self.playerData['fainted'][pokemon]

    def _battleEnd(self,verdict, reward = None, data = None):
        if verdict == 'win':
            self.out("You won! Each of your pokemon gained " + str(reward) + " experience points")
            self._displayExpInfo(data)
        else:
            self.out("Unfortunately, you lost!")
        self._exitGame()

    def _displayExpInfo(self, data, new_Exp = None, pokemonID = None ):
        if new_Exp != None and pokemonID != None: #pokemon destroyed
            self.out("Pokemon with id " + colored.green(str(pokemonID)) +" now has " + colored.blue(str(new_Exp)) + " EXPERIENCE POINTS")
        if not data:
            return
        if isinstance(data, dict): # sent at the end of the battle
            for id, data in data.iteritems():
                if len(data) > 0:
                    self.out("", "Pokemon id: " + str(id))
                    for update in data:
                        self.out(update)
                    self.out("")
        else:
            self.out("", "Pokemon id: " + str(pokemonID))
            for update in data:
                self.out(update)
            self.out("")

    def _processAttack(self, madeBy, damage, hp):
        if madeBy == username:
            self.out("Your " + colored.green(self._activePokemon_name) + " attacked")
            self.out(colored.red(self._opp_name) + "'s " + self._opp_pokemon['name'] + " was hit for " + colored.magenta(str(damage)) + " hp")
            self.out("It's hp is now at " + colored.magenta(str(hp)) + " hp")
            if hp == 0:
                self.out(colored.red(self._opp_pokemon['name']) + " fainted" + "\n")
            self._makingMove = self._opp_name
        else:
            self._updatePokeInfo(hp)
            self.out(colored.red(self._opp_pokemon['name']) + " attacked your pokemon")
            self.out("Your " + colored.green(self._activePokemon_name) + " was hit for " + colored.magenta(str(damage)) + " hp")
            self.out("Your pokemon's hp is now at " + colored.magenta(str(hp)) + " hp")
            if hp == 0:
                self.out(colored.green(self._activePokemon_name) + " has " + colored.red("fainted") + "\n")
                self.out(
                    colored.red("You need to choose another pokemon to send out. Please use the command: " + colored.green('pick <id> attack') + ", where id is the id of the pokemon you want to send out"))
                self._activePokemon_ID = None  # allows you to acess the command pick <id> attack
                self._activePokemon_name = None
            self._makingMove = username

        self._printNextTurnMessage(self._makingMove)

    def _updatePokeInfo(self, hp):
        self.playerData['alive'][self._activePokemon_ID]['_hp'] = hp
        if hp == 0:
            # move to 'fainted'
            self.playerData['fainted'][self._activePokemon_ID] = self.playerData['alive'][self._activePokemon_ID]
            del self.playerData['alive'][self._activePokemon_ID]

    def _whenPokeFaints(self, id):
        if self._state == BattleClientProtocol.STATE_BATTLE and self._activePokemon_name == None:
            if id in self._pokeBag and id in self.playerData['alive']:
                self.sendCommand('switch_attack', pokemonID=id)
                self._activePokemon_ID = id
            else:
                self.out(colored.red("Invalid choice.") + "This pokemon either has not been chosen for this battle/has fainted",
                         colored.blue("Please choose again"))
        else:
            self.out(colored.magenta("Command is not currently available\n"))

    def _processSwitch(self, madeBy, switched_Poke, doubleMove):

        if madeBy == username:  # you switched pokemon
            if doubleMove == False:
                self._makingMove = self._opp_name
            else:
                self._activePokemon_name = switched_Poke['name'] # update your pokemon name from None!!

            if self._state != BattleClientProtocol.STATE_CHOOSE_POKEMON and self._state != BattleClientProtocol.STATE_PRE_BATTLE:
                self.out(colored.blue("\nYou switched pokemon."))
                self._activePokemon_name = str(switched_Poke['name'])
            self.out("You send out " + colored.green(self._activePokemon_name) + ".\n")

        else:
            if doubleMove == False:
                self._makingMove = username
            if self._state != BattleClientProtocol.STATE_CHOOSE_POKEMON and self._state != BattleClientProtocol.STATE_PRE_BATTLE:
                self.out("\n" + colored.red(self._opp_name) + " switched pokemon.")
                self.out("Your opponent sent out " + colored.blue(str(switched_Poke['name'])) + "; hp = " + str(switched_Poke['hp']) + "; level = " + str(switched_Poke['level']))

        if doubleMove == False and self._state == BattleClientProtocol.STATE_BATTLE:
            self._printNextTurnMessage(self._makingMove)

    def _battleInfo(self, yourPokeID, oppInfo):
        self._opp_pokemon = oppInfo
        self.out(colored.red(self._opp_name) + " sent out " + colored.blue(oppInfo['name']) + "; hp = " + str(oppInfo['hp']) + " ; level = " + str(oppInfo[
            'level']))

    def _battleStarted(self, turn):
        self.out(colored.blue("\nLet the battle commence!!!\n"))
        self._state = BattleClientProtocol.STATE_BATTLE
        self._printNextTurnMessage(turn)

    def _printNextTurnMessage(self, turn):
        self._makingMove = turn  # player making next turn

        if username == turn:
            self.out(colored.green("It's your turn\n"))
        else:
            self.out("It's " + colored.red(self._opp_name) + "'s turn\n")

    def _choosePokemon(self):
        self._state = BattleClientProtocol.STATE_CHOOSE_POKEMON
        self.serverMessage("Please choose 1-3 active pokemon to join the battle\n")

    def _updateOpp_name(self, name):
        self._opp_name = name
        self.out(colored.red(name) + colored.blue(" is your opponent\n"))

    def _savePokeData(self, data):
        self.playerData = data
        if self._state == None:
            self._printHelp()
        self._state = BattleClientProtocol.STATE_JOINING_BATTLE

    def _printHelp(self):
        # print commands that are available to the user currently
        # have received pokemon_data -> allow the user to browse their poke_bag to view poke_data
        self.out(
            "",
            "Available commands:",
            "[The following commands can be used" + colored.red(' ANYTIME')+"]",
            "  ?, h, help          - Print list of commands",
            "  open                - View the contents of your bag",
            "  info <id>           - View more detailed info about the pokemon with this name",
            "  q, quit,exit        - Exit the program; NOTE: quitting after a battle has started is considered equivalent to surrendering",
            "[The following commands are only available" +colored.red(" BEFORE THE BATTLE HAS STARTED") + "]",
            "  from <id1> to <id2> - Destroy pokemon id1 and transfer its experience points to pokemon id2",
            "  revive <id>         - Revive fainted pokemon using a berry",
            "[The following commands are avaliable when you" + colored.red(" CHOOSE THE POKEMON USED IN BATTLE + when the BATTLE HAS BEGUN") + "]",
            "  view                - View the pokemon you have chosen to join the upcoming battle",
            "[The following commands are only available when you are" + colored.red(" PROMPTED TO CHOOSE THE POKEMON USED IN BATTLE")+ "]",
            "  add <id>            - Use this pokemon in the upcoming battle",
            "  remove <id>         - Withdraw this pokemon from the upcoming battle",
            "  confirm             - Confirm the selected pokemon for battle",
            "[The following commands are only available" + colored.red(" ONCE THE BATTLE HAS STARTED") +"]",
            "  attack              - Attack the opponent's pokemon",
            "  switch <id>         - Switch the pokemon used to fight",
            "  surrender           - Concede defeat:(",
            "")

    def _viewPlayerData(self):
        self.out("\n" + colored.green("POKEMON:"))
        self.out(colored.cyan("{:<8} {:<5} {:<20} {:<30} {:<3}".format('Status', 'ID', 'Name', 'HP', 'Level')))
        for status, v in self.playerData.iteritems():
            if status == 'alive' or status == 'fainted':
                for id, poke in v.iteritems():
                    self.out("{:<8} {:<5} {:<20} {:<30} {:<3}".format(status, id, pokedex.getName(poke['_id']),
                                                                   str(poke['_hp']) + "/" + str(poke['_max_hp']),
                                                                   poke['_cur_lvl']))
        self.out("\n" +colored.green("OTHER ITEMS:") )
        self.out(colored.cyan("{:<10} {:<10}".format("Item","Quantity")))
        for item, quantity in self.playerData.iteritems():
            if item != 'alive' and item != 'fainted':
                self.out("{:<10} {:<10}".format(item,quantity))
        self.out("\n")

    def _viewPokemon(self, id):
        for status, v in self.playerData.iteritems():
            if status == 'alive' or status == 'fainted':
                for pokeid, poke in v.iteritems():
                    if str(id) == pokeid:
                        pokeData = self.playerData[status][str(id)]
                        self.out("",
                                 "ID: " + colored.green(str(id)),
                                 "Name: " + colored.green(pokedex.getName(pokeData['_id'])),
                                 "Hp: " + str(pokeData['_hp']) + "/" + str(pokeData['_max_hp']),
                                 "Current experience points(exp): " + str(pokeData["_cur_exp"]),
                                 "Current level: " + str(pokeData['_cur_lvl']),
                                 "Required exp to level up: " + str(pokeData['_req_exp']),
                                 "Defense: " + str(pokeData['_def']),
                                 "Attack: " + str(pokeData['_attk']),
                                 "Special defense: " + str(pokeData['_sp_def']),
                                 "Special attack: " + str(pokeData['_sp_attk']),
                                 "Speed: " + str(pokedex.getSpeed(pokeData['_id'])),
                                 "Type: " + ",".join(str(x) for x in pokedex.getType(pokeData['_id'])),
                                 "Effort Value: " + str(pokeData['_ev']),
                                 "")
                        return
        self.out(colored.red("No pokemon with that ID\n"))


    def serverError(self, message):
        self.out(colored.red("Server error: {0}".format(message)))

    def serverMessage(self, message):
        self.out(colored.blue(message))


class BattleClientFactory(protocol.ClientFactory):
    protocol = BattleClientProtocol

    def startedConnecting(self, connector):
        destination = connector.getDestination()
        print("Connecting to server {0}:{1}, please wait...".format(destination.host, destination.port))

    def clientConnectionFailed(self, connector, reason):
        print (colored.red(reason.getErrorMessage()))
        from twisted.internet import reactor
        reactor.stop()  # @UndefinedVariable

    def clientConnectionLost(self, connector, reason):
        print (colored.blue(reason.getErrorMessage()))
        from twisted.internet import reactor, error
        try:
            reactor.stop()  # @UndefinedVariable
        except error.ReactorNotRunning:
            pass


host, port = ('127.0.0.1', 21123)
factory = BattleClientFactory()
connection = reactor.connectTCP(host, port, factory)
reactor.run()
