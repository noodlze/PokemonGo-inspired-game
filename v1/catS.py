import socket
import time
import random, sys
from threading import Thread, Timer
from DataObjects.player import *

# The constant parameters of the PokeCat module
pokeNum = 150
worldSz = 5
maxPokeNum = 5  # number of pokemon you will spawn
moveDuration = 1
turnDuration = 10
spawning_time = 10
despawning_time = 11
replenish_time = 8
disappear_time = 6


# Binding Server #todo: randomize the port and send the port number to the authentication server
server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_socket.bind(("", 9001))

# Initialize pokeworld - to generate Pokemon
poke_world = [[0 for x in range(worldSz)] for y in range(worldSz)]
# Initialize playerworld - to move around
player_world = [[0 for x in range(worldSz)] for y in range(worldSz)]

# Get all Pokemons Data
file = open('data/pokedexv3.json').read()
pokeData = json.loads(file)
pokestops = []
with open("data/pokestops5.txt",'r') as f: # pokestops5 == generate 5 random coor on a 5x5 grid, if you want to 50 pokestops on a 50x50 grid change to pokestop50.txt stored in the unused file
    for line in f:
        line = line.rstrip("\n\r")
        (x,y) = line.split(' ')
        pokestops.append((x,y))

playerData = []

# New Player List
new_player_list = []

print "Pokecat game server is waiting for connection ..."



def displayPoke():
    global poke_world
    print("Poke world")
    for x in range(worldSz):
        for y in range(worldSz):
            sys.stdout.write("{:<4}".format(poke_world[x][y]))
        print "\n"


def displayPlayer():
    global player_world
    print(" Player's world")
    for x in range(worldSz):
        for y in range(worldSz):
            sys.stdout.write("{:<4}".format(player_world[x][y]))
        print "\n"

def generate_pos():
    x = random.randint(0, worldSz - 1)
    y = random.randint(0, worldSz - 1)
    return (x, y)


def myRandom(a,
             b):  # generate a point between the numbers a-b, including b!, i.e 0-1.0, including 0 and 1.0 ([0, 1.0]).
    candidate = random.uniform(a, b + sys.float_info.epsilon)
    while candidate > b:
        candidate = random.uniform(a, b + sys.float_info.epsilon)
    return candidate


def generate_pokemon():
    global player_world
    global poke_world

    Timer(spawning_time, generate_pokemon).start()  # start the timer after interval = spawning_time
    batch_loc = []  # stores the coordinates of recently spawned pokemon

    print 'Spawning Pokemon.............!!!'
    count = 0
    while count < maxPokeNum:
        pokeIDlst = pokedexDAO().getallPokeID()
        pokemonID = random.choice(pokeIDlst)
        while 1:
            (x, y) = generate_pos()
            try:
                pokestops.index((x,y))
            except ValueError:
                if poke_world[x][y] == 0:
                    batch_loc.append((x, y))
                    poke_world[x][y] = pokemonID
                    count += 1
                    break
            else:
                pass
    print 'Complete Spawning !!!'
    displayPoke()
    time.sleep(despawning_time)  # Wait for 5 mins
    for loc in batch_loc:
        x = loc[0]
        y = loc[1]
        # Search for current spawn batch and despawn them
        if poke_world[x][y] != 0:
            poke_world[x][y] = 0
    print 'Despawned Pokemon............!!!'
    displayPoke()
    return  # A class to handle the connection of each player

def replenish_pokestops():
    global player_world
    global poke_world
    Timer(replenish_time, replenish_pokestops).start()  # start the timer after interval = spawning_time
    print 'Replenishing goodies at all pokestops.............!!!'
    for i in range(len(pokestops)):
        (x,y) = pokestops[i]
        x = int(x)
        y = int(y)
        poke_world[x][y] = random.choice(['-2','-3'])
    print 'Completed replenishing pokestops !!!'
    displayPoke()
    time.sleep(disappear_time)  # Wait for 5 mins
    for i in range(len(pokestops)):
        (x, y) = pokestops[i]
        x = int(x)
        y = int(y)
        if poke_world[x][y] != 0: # the goodie has been collected
            poke_world[x][y] = 0
    print 'The goodies at all pokestops are disappearing.....!!!'
    displayPoke()
    return

class PlayerHandler(Thread):
    def __init__(self, username, address):
        Thread.__init__(self)

        self.username = username
        self.adr = address
        # location coordinates
        self.coor_x = None
        self.coor_y = None

        # Create a class player to store their info for later use (e.g., save to Json)
        self.player = player(self.username)

    # Has to be set order like this to work correctly !!!!! DONT change anything HERE

        (x, y) = self.generate_player()
        self.x = x
        self.y = y

        self.done = False

    def run(self):
        global server_socket
        global playerData

        print "Start moving"

    # Automove the player to catch pokemon
    #     displayPlayer()
        self.automove(0)

    # End the current session of the client after 120 seconds
        while not self.done:
            pass

        print "End moving"

        self.player.savePlayerData()
        server_socket.sendto("q", self.adr)

        return

    def automove(self, sec):
        global player_world
        global server_socket
        global worldSz

        if sec == turnDuration:
            self.done = True
            return

    # Repeat the automove function every 1 second until 120 seconds
        Timer(moveDuration, self.automove, (sec + 1,)).start()

    # Old position of the player
        oldX = self.x
        oldY = self.y

    # New position of the player
        newX = self.x
        newY = self.y

        status = "You "
        direction = ""

        while player_world[newX][newY] != 0:
            newX = self.x
            newY = self.y

            # Options: clockwise
            # 1: Move up
            # 2: Move right
            # 3: Move down
            # 4: Move left
            option = random.randint(1, 4)

            if option == 1:
                newX -= 1
                direction = "moved up "
            elif option == 2:
                newY += 1
                direction = "moved right "
            elif option == 3:
                newX += 1
                direction = "moved down "
            elif option == 4:
                newY -= 1
                direction = "moved left "

            if newX < 0:
                newX = worldSz - 1

            if newY < 0:
                newY = worldSz - 1

            newX %= worldSz
            newY %= worldSz

        # print option
        status += direction + "to (" + str(newX) +"," + str(newY) + ")."
        # print status
    # Send the moving information back to the current client
        server_socket.sendto(status, self.adr)

        self.x = newX
        self.y = newY

    # Reset the position of the player on the field
        player_world[oldX][oldY] = 0
        player_world[self.x][self.y] = 1

        # displayPlayer()

    # Found a pokemon/pokeball/berries
        if poke_world[self.x][self.y] != 0:
            if poke_world[self.x][self.y] == '-2' or poke_world[self.x][self.y] == '-3':
                # print("berries or pokeball")
                self.addItem(poke_world[self.x][self.y])
                poke_world[self.x][self.y] = 0
            else:
                # print("pokemon")
                if self.player.hasPokeBalls() == False:
                    server_socket.sendto("You encountered a wild pokemon but have no pokeballs to catch it :(", self.adr)
                else:
                    pokemonID = poke_world[self.x][self.y]
                    self.catch_pokemon(pokemonID)
                    poke_world[self.x][self.y] = 0

    def generate_player(self):
        global player_world
        global poke_world

        x, y = generate_pos()
        while player_world[x][y] == 1:
            x, y = generate_pos()

        if poke_world[x][y] != 0:
            if poke_world[x][y] == '-2' or poke_world[x][y] == '-3':
                self.addItem(poke_world[x][y])
            else:
                if self.player.hasPokeBalls() == False:
                    server_socket.sendto("You encountered a wild pokemon but have no pokeballs to catch it :(",
                                         self.adr)
                else:
                    pokemonID = poke_world[x][y]
                    self.catch_pokemon(pokemonID)
                    poke_world[x][y] = 0

        player_world[x][y] = 1

        return (x, y)  # Return location for new Player

    def addItem(self,id):
        item = ''
        if id == '-2': # item is a pokeball
            item = 'pokeballs'
        else: # item is a berry
            item = 'berries'
        self.player.addItem(item)

        status = "You just collected " + item + " at a pokestop"
        server_socket.sendto(status, self.adr)

    def catch_pokemon(self, pokemonID):

        global pokeData
        global server_socket

        ev = myRandom(0.5, 1.0)
        poke = pokedexDAO().createPokemon(pokemonID, round(ev,1))

        # print "Pokemon id:", poke_a.id

        status = "You just caught " + poke.getName()
        #print status
        verdict = self.player.addPokemon(poke)
        if verdict == False:
            status = "You have 200 pokemon; there's no room left in your pokebag so you had to release the caught " + poke.getName()
# Send the name of caught pokemon to client
        server_socket.sendto(status, self.adr)


playerThreads = []
pokemonGeneratorThread = Thread(target=generate_pokemon).start()
pokestopsGeneratorThread = Thread(target=replenish_pokestops).start()
# MAIN GAME
while 1:
    data, address = server_socket.recvfrom(256)

    # Get all Player Data
    file = open('data/players.json').read()
    playerData = json.loads(file)

    # print playerData

    temp = data.split('-')
    username = None

    # print "Player bag", playerbag
    if 'Connect' in data:
        username = temp[1]

    player_thread = PlayerHandler(username, address)
    player_thread.start()
    # playerThreads.append(player_thread)
    # print adr_list.keys()
    print "(", address[0], " ", address[1], ") said: ", data

for t in playerThreads:
    t.join()
pokemonGeneratorThread.join()
pokestopsGeneratorThread.join()
server_socket.close()
