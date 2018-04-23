import socket
import sys
# Using UDP
client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

print '-------------- Welcome to Pokemon World ! ------------------\n'
send_addr = "localhost"
send_port = 9001
username = str(sys.argv[1])
data = "Connect-" + username 
client_socket.sendto(data,(send_addr,send_port))
while 1:

	recvData, address = client_socket.recvfrom(1024)

	if recvData.lower() == 'q':
		print "End the current session Pokecat game"
		print "Thank you for playing"
		break

	print recvData