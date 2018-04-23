import simplejson as json
import uuid
from twisted.python import log
from twisted.internet import protocol
from twisted.application import service
from protocol import JsonReceiver
from projectFilesPath import * # stores value of playersListJSON_path
playerData = {}


class AuthenticationProtocol(JsonReceiver):  # TODO: improve code implementation by using deferrals and callbacks -> would make debugging a lot easier
    def connectionMade(self):
        peer = self.transport.getPeer()
        log.msg("Connection made from {0}:{1}".format(peer.host, peer.port))
        # log.msg("Total active connections: {0}/{1}".format(self.factory.clients + 1, self.factory.clients_max))
        # self.factory.clients += 1
        # if self.factory.clients > self.factory.clients_max:
        #     self.sendError("overloaded server")
        #     self.transport.loseConnection()

    def connectionLost(self, reason):
        peer = self.transport.getPeer()
        log.msg("Connection lost from {0}:{1}".format(peer.host, peer.port))

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

    def sendResponse(self, command, **params):
        self.sendObject(command=command, params=params)
        log.msg("Data sent: {0}({1})".format(command, params))

    def runCommand(self, command, **params):
        # params is a dictionary
        commands = {
            'signup':self.signup,
            'login': self.validateLogin,
            'logout': self.logoutClient,
            'authenticate': self.verifyToken,
            'battle_server': self.addBattleServer
        }
        if not command in commands:
            self.sendError("Invalid command: \"{0}\"".format(command))
            return
        try:
            commands[command](**params)
        except (ValueError, TypeError) as e:
            self.sendError("Error executing command \"{0}\": {1}".format(command, e))

    def signup(self,username,password):
        if username in playerData.keys():
            self.sendError("Username already taken. Please choose another")
        else:
            playerData[username] = {}
            playerData[username]['password'] = password

            emptyDict = {}
            emptyDict['alive'] = {}
            emptyDict['fainted'] = {}
            with open(dataFile_path+"/" + username + ".json", 'w+') as f:
                f.write(json.dumps(emptyDict, indent=4, sort_keys=True))
            self.factory.updatePlayersJSON()

            self.sendResponse("signup_sucess")


    def logoutClient(self, username):
        try:
            i = self.factory.loggedInClients.index(username)
        except ValueError:
            self.sendError(username + " has not logged on")
        else:
            del self.factory.loggedInClients[i]
            self.factory.battleServer.sendResponse('invalidatePlayer', username=username)
            self.sendResponse("logout_success")

    def addBattleServer(self):
        self.factory.battleServer = self

    def validateLogin(self, username, password):
        if username in playerData and playerData[username]['password'] == password:
            token = str(uuid.uuid4())  # automatically create access token for player
            # >>> str(uuid.uuid4())  'f50ec0b7-f960-400d-91f0-c42a6d44e3d0'
            playerData[username]['access_token'] = token
            self.sendResponse('login_success', access_token=token)
            self.factory.updatePlayersJSON()

            try:
                self.factory.loggedInClients.index(username)
            except ValueError:
                self.factory.loggedInClients.append(username)
            else:
                pass

            self.factory.battleServer.sendResponse("validPlayer", username = username)
        else:
            self.sendError("Login failure")

    def verifyToken(self, username, token):
        if username in playerData and 'access_token' in playerData[username] and playerData[username][
            'access_token'] == token:
            self.sendResponse('authentication_success')

            try:
                self.factory.loggedInClients.index(username)
            except ValueError:
                self.factory.loggedInClients.append(username)
            else:
                pass

            self.factory.battleServer.sendResponse("validPlayer", username=username)
        else:  # the user's token and the server's token don't match/the server has no stored token for the user
            if 'access_token' in playerData[username]:
                del playerData[username]['access_token']
            self.sendResponse('authentication_failure')


    def sendError(self, message):
        self.sendResponse('error', message=message)


class AuthenticationFactory(protocol.ServerFactory):
    protocol = AuthenticationProtocol
    loggedInClients = []
    battleServer = None

    def __init__(self, service):
        self.service = service
        self.getPlayerData()

    def updatePlayersJSON(self):
        if os.path.exists(playersListJSON_path):
            with open(playersListJSON_path, 'w') as f:
                f.write(json.dumps(playerData, indent=4, sort_keys=True))
        else:
            log.msg("players.json file cannot be located in the /data file")
            from twisted.internet import reactor
            reactor.stop()

    def getPlayerData(self):  # checks whether you can read from players.json file
        if os.path.exists(playersListJSON_path):
            file = open(playersListJSON_path).read()
            global playerData
            playerData.update(json.loads(file))  # playerData is a dictionary
            return True
        else:
            log.msg("Cannot locate players.json file")
            return False


class GameService(service.Service):
    pass
