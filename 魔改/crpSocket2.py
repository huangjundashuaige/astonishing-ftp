# -*- coding: UTF-8 -*-
import socket
import crpPacket2
from collections import deque
from crpPacket2 import CRPPacket2
import math

global DEBUG
DEBUG = True

def log(message):
    if DEBUG:
        print message

def ilog(message):
    if True:
        print message


class CRPSocket2:
    def __init__(self, sourceCRPPort, flag):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.settimeout(1)
        self.receivingWindowSize = CRPPacket2.maxWindowSize()
        self.recievingWindowSizeInt = 6
        self.destAddr = None
        self.srcAddr = None
        self.sendWindowSize = 6
        self.udpDestPort = None
        self.udpSrcPort = sourceCRPPort
        self.seqNum = 1
        self.ackNum = 1

        self.state = 'CLOSED'
        # ????
        self.maxReset = 100

        global DEBUG
        DEBUG = flag
    def _reconstructPacket(self, data, checkAckNum = False):
        # 用recvfrom收到的是一串东西
        # 需要用写在packet里面的函数把它复原出来
        packet = CRPPacket2.fromByteArray(data)

        # 检查包是否发生位错
        if checkAckNum:
            givenChecksum = packet.header['checksum']
            calculateChecksum = packet._computeChecksum()

            if givenChecksum != calculateChecksum:
                log("###### Corrupted Packet  #####")
                return None

            ## 下面看不太懂 感觉不是这样？？？
            # 应该是的
            # 就是有多少个seq过来我就ack了多少次
            # 如果两者一样就说明有一样的顺序？？？
            packetAckNum = packet.header['seqNum']
            if packetAckNum != checkAckNum:  
                log("### ACK is mismatch ###")
                return None

        return packet


    def bind(self, addr, portNum):
        self.socket.bind((addr, portNum))

    
    # server
    def listen(self):
        log("listen()")
        self.state = 'LISTENING'

        # Receive SYN from client
        # 等待从客户端来的SYN包
        while True:
            try:
                synData, synAddress = self.recvfrom(self.receivingWindowSize)
                synPacket = self._reconstructPacket(bytearray(synData), self.ackNum)
            
            except:
                log("Socket Time out")
                continue

            if synPacket != None:
                log("Received SYN")
                self.ackNum = synPacket.header['seqNum'] + 1
                break

        self.udpDestPort = int(synPacket.header['desPort'])
        self.destAddr = synAddress[0]
        self.udpDestPort = synAddress[1]

        log("Sending back ACK")
        # Send ACK
        ackPacket = CRPPacket2.getACK(self.udpSrcPort, self.udpDestPort, self.seqNum, self.ackNum, self.receivingWindowSize)
        self.socket.sendto(ackPacket.toByteArray(), (self.destAddr, self.udpDestPort))
        self.seqNum = self.seqNum + 1
        self.state = 'SYN-RCVD'
        log("ACK Packet Sent")

        timeoutCount = 0
        # 等待发过来的ACK包
        while True:
            try:
                ackData, ackAddress = self.recvfrom(self.receivingWindowSize)
                ackPacket2 = self._reconstructPacket(bytearray(ackData), self.ackNum)
            except:
                log("Socket Timed out")
                timeoutCount += 1
                if timeoutCount >= 3:
                    log("Send ACK again")
                    self.socket.sendto(ackPacket.toByteArray(), (self.destAddr, self.udpDestPort))
                    log("ACK Packet Sent")
                    timeoutCount = 0
                continue

            if ackPacket2 != None:
                log("Received ACK")
                self.ackNum = ackPacket2.header['seqNum'] + 1
                break 
        
        log("Connection Established")
        self.state = 'Established'



    # client
    def connect(self, ipAdress, portNum):
        log("Client connect()")
        self.destAddr = ipAdress
        self.udpDestPort = portNum

        # THREE WAY HANDSHAKE 
        # FIRST:
        # SEND A SYN PACKET (SYN BIT SET TO 1)
        # THE CLIENT RANDOMLY CHOOSE A SEQUENCE NUMBER
        log('Creating SYN Packet')
        # 先忽略随机数了吧...还是从1开始
        synPacket = CRPPacket2.getSYN(self.udpSrcPort, self.udpDestPort, self.seqNum, self.ackNum, self.receivingWindowSize)
        self.socket.sendto(synPacket.toByteArray(), (self.destAddr, self.udpDestPort))
        self.seqNum = self.seqNum + 1  # Increment sequence number

        log("SYN Packet Sent")
        self.state = 'SYN-SENT'

        timeoutCount = 0

        # SECOND:
        # WAITING FOR THE ACK FROM THE SERVER
        # 之后再改成SYN ACK包
        log("Waitin to receive ACK...")
        while True:
            try:
                ackData, ackAddress = self.recvfrom(self.receivingWindowSize)
                ackPacket = self._reconstructPacket(bytearray(ackData), self.ackNum)
            except:
                log("Timed out, listening again for ACK in connect()")
                timeoutCount += 1
                ### timeoutCount这部分之后可以再修改    
                if timeoutCount >= 3:
                    log("SEND SYN AGAIN")
                    self.socket.sendto(synPacket.toByteArray(), (self.destAddr, self.udpDestPort))
                    log("SYN PACKET SENT")
                    timeoutCount = 0

                continue

            if ackPacket != None:
                self.ackNum = ackPacket.header['seqNum'] + 1
                break    # 如果收到了ACK包就退出循环

        log("self.seqNum is " + str(self.seqNum))

        # 根据ACK和ack num判断收到的ACK包是否正确
        # ackNum = seqNum + 1
        # 但是之前seqNum就已经加过1了，所以直接判断ackNum和seqNum
        if ackPacket.isACK() and ackPacket.header['ackNum'] == self.seqNum:
            log("Correct ACK Received")

        # THIRD:
        # 客户端发送ACK包给服务端
        log("Creating ACK Packet")
        ackPacket2 = CRPPacket2.getACK(self.udpSrcPort, self.udpDestPort, self.seqNum, self.ackNum, self.receivingWindowSize)

        self.seqNum = self.seqNum + 1 # Increment sequence number
        self.socket.sendto(ackPacket2.toByteArray(),(self.destAddr, self.udpDestPort))
        log("ACK is sent")

        # ESTABLISHED
        self.state = 'ESTABLISHED'

        log("Increment Seq Num")

   
    # 其实这个函数也就是把socket里面的东西又再写了一遍
    def recvfrom(self, recvWindow):
        while True:
            try:
                packet = self.socket.recvfrom(recvWindow)
                log("Received message from " + str(packet[1]) + "\n")
            except socket.error as error:
                if error.errno is 35:
                    continue
                else:
                    raise error

            return packet

    # def recv(self):
        # 这下面两个是啥玩意
        receiveOrder = ""
        firstReceive = True
        log("recv() entered")

        if self.udpSrcPort is None:
            log("Socket already closed")
        if self.state != 'ESTABLISHED':
            log("Socket already closed")

        #????
        message = bytes()

        redoLeft = self.maxReset
        isLast = False
        while redoLeft and not isLast:
            justSendAck = False




        redo
    








    def recv(self):
		recieveOrder = ""
		firstReceving = True
		log("recv() entered")
		if self.udpSrcPort is None:
			log("Socket already closed")
		if self.state != 'ESTABLISHED':
			log("Socket already closed")

		message = bytes()

		redoLeft = self.maxReset
		isLast = False
		while redoLeft and not isLast:
			justSendAck = False
			windowCount = self.recievingWindowSizeInt
			log("Receiving Window Size: " + str(windowCount))
			packet = None
			while windowCount:
				try:
					log("==============Waiting to recieve a packet==============")
					data, address = self.recvfrom(self.receivingWindowSize)
				except socket.timeout:
					log("Timed out, just send ACK")
					redoLeft -= 1
					justSendAck = True
					break

				packetP = self._reconstructPacket(bytearray(data))
				log("Recevied Packet SeqNum: " + str(packetP.header['seqNum']) + " ackNum: " + str(self.ackNum))
				packet = self._reconstructPacket(bytearray(data), self.ackNum)

				if not packet:
					log("*******************Receive out of order or irrelevant packet, ignore****************")
					justSendAck = True
					windowCount -= 1
					break

				if packet.data != None:
					log("Recieved Packet, is First? " + str(firstReceving))
					recieveOrder = recieveOrder + ", " + str(packet.header['seqNum'])
					firstReceving = False
					message += packet.data
					self.ackNum = packet.header['seqNum'] + 1
					if self.ackNum > CRPPacket.maxAckNum():
						self.ackNum = 0
					windowCount -= 1

				if (packet.isLastPacket()):
					log("Last Packet")
					isLast = True
					break

				if (packet.isFin()):
					log("Finish Packet received")
					flags = (False, False, True, False, False)
					ackPacket = CRPPacket(
								srcPort = self.udpSrcPort,
								desPort = self.udpDestPort,
								seqNum = self.seqNum,
								ackNum = self.ackNum,
								flagList = flags,
								winSize = self.receivingWindowSize,
								)
					self.socket.sendto(ackPacket.toByteArray(), (self.destAddr, self.udpDestPort))
					break

			#log("Data received: " + str(packet.data))
			if (firstReceving == False and justSendAck == True) or packet != None and packet.data != None:
				if justSendAck:
					log("Send due to socket time out")
				flags = (False, False, True, False, False)
				ackPacket = CRPPacket(
							srcPort = self.udpSrcPort,
							desPort = self.udpDestPort,
							seqNum = self.seqNum,
							ackNum = self.ackNum,
							flagList = flags,
							winSize = self.receivingWindowSize,
							)
				self.socket.sendto(ackPacket.toByteArray(), (self.destAddr, self.udpDestPort))
				log("Ack Packet sent: #" + str(self.ackNum))
			log(" self.seq: " + str(self.seqNum) + " self.ack: " + str(self.ackNum))
		if not redoLeft:
			raise Exception('Socket timeout')

		#log("Order: " + recieveOrder)
		return message
		
	
	
	
        	