import os

ROOT_DIR = os.path.dirname(os.path.abspath(__file__)) # absolute file path to the project folder
dataFile_path = ROOT_DIR + '/data/playerData'
pokedexJSON_path = ROOT_DIR + '/data/pokedexv3.json'
playersListJSON_path = ROOT_DIR + '/data/players.json'
def getPlayerDataJSON_path(username):
    return ROOT_DIR + '/data/playerData/'+ username +'.json'
