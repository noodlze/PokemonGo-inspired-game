from protocol import JsonReceiver
from twisted.internet import reactor
from twisted.internet import protocol, stdio
validClients = []

class verifyClientProtocol(JsonReceiver):
    def __init__(self):
        self.debug_enabled = False

    def out(self, *messages):
        for message in messages:
            print(message)

    def debug(self, *messages):
        if self.debug_enabled:
            self.out(*messages)

    def connectionMade(self):
        self.sendCommand("battle_server")
        self.out("Battle server connected to the authentication server...")

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
            'validPlayer': self.verifiedPlayer,
            'invalidatePlayer': self.logoutPlayer
        }
        if command not in commands:
            self.debug("Invalid command received: {0}".format(command))
            return

        try:
            commands[command](**params)
        except TypeError as e:
            self.debug("Invalid command parameters received: {0}".format(e))

    def logoutPlayer(self, username):
        try:
            i = validClients.index(username)
        except ValueError:
            pass
        else:
            del validClients[i]

    def verifiedPlayer(self,username):
        global validClients
        validClients.append(username)
        # print(validClients)

    def serverError(self, message):
        self.out("Server error: {0}".format(message))

    def serverMessage(self, message):
        self.out(message)

class verifyClientFactory(protocol.ClientFactory):
    protocol = verifyClientProtocol

    def startedConnecting(self, connector):
        destination = connector.getDestination()
        print
        "Connecting to server {0}:{1}, please wait...".format(destination.host, destination.port)

    def clientConnectionFailed(self, connector, reason):
        print
        'Could not connect to authentication server at port ' + str(connector.getDestination().port)

    def clientConnectionLost(self, connector, reason):
        print
        'Connection to authentication server severed'
        reactor.stop()