#!/usr/bin/env python
import os
from functools import partial
from twisted.protocols import basic
from twisted.internet import protocol, stdio
from twisted.python import util
from twisted.internet import reactor
def load_src(name, fpath): # used to access a .py file not located in current directory or lower directory
    import os, imp
    p = fpath if os.path.isabs(fpath) \
        else os.path.join(os.path.dirname(__file__), fpath)
    return imp.load_source(name, p)

load_src("protocol", "../protocol.py")
from protocol import JsonReceiver


Token_Path = 'data/access_token.txt'
username = None

class UserInputProtocol(basic.LineReceiver):
    from os import linesep
    delimiter = linesep

    def __init__(self, callback):
        self.callback = callback

    def lineReceived(self, line):
        self.callback(line)


class AuthenticationClientProtocol(JsonReceiver):
    def __init__(self):
        self.debug_enabled = False

    def out(self, *messages):
        for message in messages:
            print(message)

    def debug(self, *messages):
        if self.debug_enabled:
            self.out(*messages)

    def connectionMade(self):
        stdio.StandardIO(UserInputProtocol(self.userInputReceived))
        self.out("Connected to the authentication server...")
        if self.openAuth():
            self.out("Welcome back " + username + " .Please wait while we log you in...")
        self.printHelp()

    def userInputReceived(self, string):
        """
        """
        commands = {
            '?': self.printHelp,
            'h': self.printHelp,
            'help': self.printHelp,
            'login': self.login,
            'logout': self.logout,
            'signup': self.signup,
            'q': self.exitGame,
            'quit': self.exitGame,
            'exit': self.exitGame,
        }
        if string == '':  # empty string
            return

        params = filter(len, string.split(' ', 1))
        command, params = params[0], params[1:]

        if not command:
            return

        if command not in commands:
            self.out("Invalid command")
            return

        try:
            commands[command](*params)
        except TypeError as e:
            self.out("Invalid command parameters: {0}".format(e))

    def printHelp(self):
        self.out(
            "",
            "Available commands:",
            "  ?, h, help          - Print list of commands",
            "  login <username>    - Login into your account",
            "  signup <username>   - Sign up for an account using this username",
            "  logout              - Logout of your account",
            "  q, quit, exit       - Exit the program",
            "")

    def signup(self, uname):
        username = uname
        password = util.getPassword('Password: ')
        self.sendCommand(command='signup', username=uname, password=password)

    def openAuth(self):
        global username
        token = ''
        if os.path.exists(Token_Path):
            file = open(Token_Path, 'r')
            username = file.readline()
            username = username.rstrip("\n\r")
            token = file.readline()
            token = token.rstrip("\n\r")
            file.close()
            self.sendCommand(command='authenticate', username=username, token=token)
            return True
        else:
            return False

    def logout(self):
        if username != None:
            self.sendCommand("logout", username = username)
        else:
            self.out('You are not logged in as any user')

    def login(self, uname): #TODO: find a better way to get the login details
        global username
        username = uname
        password = util.getPassword('Password: ')
        self.sendCommand(command='login', username=username, password=password)

    def exitGame(self):
        self.out("Disconnecting...")
        self.transport.loseConnection() # disconnects from the authentication server

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
            'error': self.serverError,
            'login_success': self.saveToken,
            'authentication_success': partial(self.serverMessage,
                                              'Welcome ' + str(username) + ".You have successfully logged in"),
            'authentication_failure': self.deleteOldToken,
            'logout_success': self.logoutAccount,
            'signup_sucess': partial(self.serverMessage, "You have successfully signed up for a new account.")
        }

        if command not in commands:
            self.debug("Invalid command received: {0}".format(command))
            return

        try:
            commands[command](**params)
        except TypeError as e:
            self.debug("Invalid command parameters received: {0}".format(e))

    def logoutAccount(self):
        global username
        self.out("You have logged out of the account " + username)
        username = None

    def deleteOldToken(self):
        if os.path.exists(Token_Path):
            os.remove(Token_Path)
            self.serverMessage('Authentication failed for the user ' + username + '. Please try to login again')

    def saveToken(self, access_token):
        self.serverMessage('Welcome ' + username + ".You have successfully logged in")
        file = open(Token_Path, 'w+')
        file.write(username + "\n")
        file.write(access_token)
        file.close()

    def serverError(self, message):
        self.out("Server error: {0}".format(message))

    def serverMessage(self, message):
        self.out(message)

class AuthenticationClientFactory(protocol.ClientFactory):
    protocol = AuthenticationClientProtocol

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


host, port = ('127.0.0.1', 21000)
factory = AuthenticationClientFactory()
connection = reactor.connectTCP(host, port, factory)
reactor.run()
