import sys
import socket
import random

if len(sys.argv) != 5:
    print('ERROR! usage: server.py PORT_NUMBER qname qtype timeout')
    sys.exit()

# taken from https://docs.python.org/3/library/random.html
qid = random.getrandbits(16)
server_port = int(sys.argv[1])
qname = sys.argv[2]
qtype = sys.argv[3]
timeout = int(sys.argv[4])

if timeout == 0:
    timeout = 0.001

# client/server socket programming recieve and sending taken from https://stackoverflow.com/questions/60624252/python-udp-server-client and https://webcms3.cse.unsw.edu.au/COMP3331/24T2/resources/98569
client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
client_socket.settimeout(timeout)

message = f'{qname} {qtype} {qid}'
try:
    client_socket.sendto(message.encode(), ('127.0.0.1', server_port))
    response, server_address = client_socket.recvfrom(2048)
    print(response.decode())
except socket.timeout:
    print('timed out')
except Exception as e:
    print('There was an error: ', e)
finally:
    client_socket.close()
