from twisted.application import internet, service
from AuthenticationServer.authServer import AuthenticationProtocol,AuthenticationFactory, GameService
from BattleServer.batServer import BattleFactory,BattleProtocol


auth_port = 21000
bat_port = 21123
interface = 'localhost'


top_service = service.MultiService()

game_service = GameService()
game_service.setServiceParent(top_service)

#authentication server
factory = AuthenticationFactory(game_service)
tcp_service = internet.TCPServer(auth_port, factory, interface=interface)
tcp_service.setServiceParent(top_service)

#battle server
bat_factory = BattleFactory(game_service)
tcp_service1 = internet.TCPServer(bat_port, bat_factory, interface=interface)
tcp_service1.setServiceParent(top_service)

application = service.Application("twisted-game-server")

top_service.setServiceParent(application)
