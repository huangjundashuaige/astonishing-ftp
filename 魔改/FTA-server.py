DEBUG = True

def log(message):
	if DEBUG:
		print message

import sys
import struct
import socket
import crpSocket2
import os

def checkArgs():
	if len(sys.argv) == 2 or len(sys.argv) == 3 :
		print "Valid arguments"
	else:
		print "Invalid arguments"
		sys.exit(1)

def usage():
	print "Invalid arguments\n"
	print "FTA-server Usage: \n"
	print "FTA-server X \n"
	print "X: port number to which FTA server's UDP socker should bind \n"
	print "Example: FTA-server 5000"
	sys.exit(1)

def runServer():
    global sock
    global state

    log("Top of the server, state: " + state)

    if(state != "CONNECTED"):
        try:
            log("Listening...")
            try:
                sock.listen()
            except Exception as e:
                log("Exception: " + str(e))
                sys.exit(0)
            log("Setting state to CONNECTED.\n")
            state = "CONNECTED"
        except Exception as e:
            log("Connection Failed: " + str(e))
            return

    log("Waiting for message from client")
    message = recv_msg(sock)
    log("Message: " + str(message))
    

def recv_msg(asocket):
    # Read message length and unpack it into an integer
    raw_msglen = recvall(asocket, 4)
    if not raw_msglen:
        return None
    return raw_msglen

####????
def recvall(asocket, n):
    recvCallsMode = 0
    packet = asocket.recv()

    if not packet:
        return None
    return packet

    


# ----------------Program Run-------------------------#
checkArgs()

serverCRPport = int(sys.argv[1])
debugFlag = False

if len(sys.argv) == 3:
    if sys.argv[2] != None:
        log("Flag set to True")
        debugFlag = True

sock = crpSocket2.CRPSocket2(serverCRPport, debugFlag)
state = 'DISCONNECTED'

try:
    sock.bind("127.0.0.1", serverCRPport)

except Exception as e:
    print "Error: could not bind to port " + str(serverCRPport) + " on local host.\n"
    log("Exception: " + str(e))
    sys.exit(1)

while True:
    runServer()



