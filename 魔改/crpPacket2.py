# -*- coding: UTF-8 -*-
import sys
import socket
import struct
import ctypes
import math

DEBUG = False

def log(messgae):
    if DEBUG:
        print messgae

class CRPPacket2:
    global uint16
    global uint32
    global uint8

    uint16 = ctypes.c_uint16
    uint32 = ctypes.c_uint32
    uint8 = ctypes.c_uint8

    global MAX_SEQUENCE_NUM
    global MAX_ACK_NUM
    global MAX_WINDOW_SIZE
    global HEADER_LENGTH
    global DATA_LEN

    MAX_SEQUENCE_NUM = int(math.pow(2, 32) - 1) # 32bits 4 bytes
    MAX_ACK_NUM = int(math.pow(2, 32) - 1) # 32bits 4 bytes
    MAX_WINDOW_SIZE = int(math.pow(2, 16) - 1) # 16bits 2 bytes
    HEADER_LENGTH = 20  # 16 BYTES  一般urgent data pointer不会使用
    DATA_LEN = 1004 #?????
   

    global HEADER_FIELDS

    HEADER_FIELDS = (  # 20 bytes
                    ('srcPort', uint16, 2),
                    ('desPort', uint16, 2),
                    ('seqNum', uint32, 4),
                    ('ackNum', uint32, 4),
                    ('flagList', uint16, 2),
                    ('winSize', uint16, 2),
                    ('checksum', uint16, 2),
                    ('urgptr', uint16, 2)
                    ) 

    @staticmethod
    def maxSeqNum():
        return MAX_SEQUENCE_NUM

    @staticmethod
    def maxAckNum():
        return MAX_ACK_NUM

    @staticmethod
    def maxWindowSize():
        return MAX_WINDOW_SIZE

    @staticmethod
    def getHeaderLeangth():
        return HEADER_LENGTH

    @staticmethod
    def getDataLength():
        return DATA_LEN

    # 输入byteArray 返回出来一个包
    @staticmethod
    def fromByteArray(byteArray):
        p = CRPPacket2()  # 初始化一个包
        p.__unpack(byteArray)  ##??
        return p

    # 将byteArray放入到包中
    # 前面放在header 后面放在data
    def __unpack(self, byteArray):
        if byteArray:
            log("HEADER_LENGTH is " + str(HEADER_LENGTH))
            # 把byteArray的0-HEADER_LENGTH的内容放到headerBytes里面
            # 相当于放头部信息
            headerBytes = byteArray[0:HEADER_LENGTH]
           
            log("headerBytes size: " + str(len(headerBytes)))

            ##########################
            self.__unpackHeader(headerBytes)

            if(len(byteArray) != HEADER_LENGTH):
                # 把剩下的东西放到dataBytes里面
                dataBytes = byteArray[HEADER_LENGTH : ]
            else:
                dataBytes = None

            self.data = dataBytes

    # 放进header
    # 前面的
    def __unpackHeader(self, headerBytes):
        base = 0 # ????

        # for each header field, get values
        for (fieldName, dataType, size) in HEADER_FIELDS:
            # get the bytes from byteArray, convert to int
            bytes = headerBytes[base : base + size]
            # 其实就是index一直加上去
            #log("base: " + str(base) + " size: " + str(size))
            value = dataType.from_buffer(bytes).value
            #log("Unpacked " + fieldName + " Value is " + str(value))

            # 当fieldType是flagList 弄一个更细的函数
            if (fieldName == 'flagList'):
                value = self.__unpackFlags(value)

            # 把相应值放在头部
            self.header[fieldName] = value

            # 增加base
            base = base + size

    # 解析每一位 返回
    def __unpackFlags(self, value):
        log("Unpack Flags")

        # 检查每一位
        # isREQ = ((value & 0x1) == 1)
        # isSYNC = (((value & 0x2) >> 1) == 1)
        # isAck = (((value & 0x4) >> 2) == 1)
        # isFin = (((value & 0x8) >> 3) == 1)
        # 这句是不是写错了呀
        # isLast = (((value & 0x16) >> 4) == 1)

        # textbook p234
        #################################
        ##  U | A | P | R | S | F |
        ##  R | C | S | S | Y | I |
        ##  G | K | H | T | N | N |
        #################################
        isFIN = ((value & 0x1) == 1)
        isSYN = (((value & 0x2) >> 1) == 1)
        isRST = (((value & 0x4) >> 2) == 1)
        isPSH = (((value & 0x8) >> 3) == 1) # 一般不会用到
        isACK = (((value & 0x10) >> 4) == 1)
        isURG = (((value & 0x20) >> 5) == 1) # 一般不会用到


        #log("REQ: " + str(isREQ) + " SYNC: " + str(isSYNC) + " ACK: " + str(isAck)) + " FIN: " + str(isFin) + " LAST: " + str(isLast) + " isSent")

        return (isURG, isACK, isPSH, isRST, isSYN, isFIN)

    # 产生二进制数组  ????????
    def toByteArray(self):
        #log("converting to ByteArray") 
        # 二进制数组
        packet = bytearray()
        
        packet.extend(self.__packHeader()) #放入头部
        #log("Header added to Packet")
        if self.data != 0:
            if self.data != None:
                packet.extend(self.data)
                #log("Header added to Packet")
        while True:
            if (len(packet) % 2 != 0): ### ????
                #log("Packet extended to keep it even")
                packet.extend(' ')
            else:
                #log("Packet is even")
                break
        return packet

    
    # converts the header to a length 20 bytearray
    def __packHeader(self):
        log("---------------------------------------------------------------")
        log("Packing header to the packet")
        byteArray = bytearray()

        for (fieldName, dataType, size) in HEADER_FIELDS:
            #print("crpPacket __packHeader: fieldName " + fieldName)
            value = self.header[fieldName]
            #print(value)

            if (fieldName != 'flagList'):
                byteArray.extend(bytearray(dataType(value)))
            else:
                # __packFlags -> 把flag变成byte
                byteArray.extend(self.__packFlags())
            log("After Packet " + fieldName + " length is " + str(len(byteArray)))
        log("---------------------------------------------------------------")
        return byteArray


    # 把flag变成byte
    #################################
    ##  U | A | P | R | S | F |
    ##  R | C | S | S | Y | I |
    ##  G | K | H | T | N | N |
    #################################
    #(isURG, isACK, isPSH, isRST, isSYN, isFIN)
    def __packFlags(self):
        value = 0
        flags = self.header['flagList']   #####
        if flags[5] == True:              # isFIN
            value = value | 0x1
        if flags[4] == True:              # isSYN
            value = value | 0x2
        if flags[3] == True:              # isRST
            value = value | 0x4
        if flags[2] == True:              # isPSH
            value = value | 0x8
        if flags[1] == True:              # isACK
            value = value | 0x10
        if flags[0] == True:              # isURG
            value = value | 0x20
            
        # if flags[4] == True:
        #     value = value | 0x1
        # if flags[3] == True:
        #     value = value | (0x1 << 1)
        # if flags[2] == True:
        #     value == value | (0x1 << 2)
        # if flags[1] == True:
        #     value = value | (0x1 << 3)
        # if flags[0] == True:
        #     value = value | (0x1 << 4)
        # return bytearray(uint32(value)) # 扩展到32位
        return bytearray(uint16(value))


    
    #(isURG, isACK, isPSH, isRST, isSYN, isFIN)
    
    ###########################这里可能要重新想一下
    # Returns a simple FIN packet.   之前的REQ代表的是什么啊
    @staticmethod
    def getFIN(srcPort, desPort, seqNum, ackNum, winSize, urgptr = 0):
        return CRPPacket2(srcPort, desPort, seqNum, ackNum, (False, False, False, False, False, True), winSize, urgptr = 0)

    # Returns a simple ACK packet
    @staticmethod
    def getACK(srcPort, desPort, seqNum, ackNum, winSize, urgptr = 0):  # 之后可能要考虑一下ACK + SYN
        return CRPPacket2(srcPort, desPort, seqNum, ackNum, (False, True, False, False, False, False), winSize, urgptr = 0)

    # Returns a simple SYN packet.
    @staticmethod
    def getSYN(srcPort, desPort, seqNum, ackNum, winSize, urgptr = 0):
        
        return CRPPacket2(srcPort, desPort, seqNum, ackNum,(False, False, False, False, True, False), winSize, urgptr = 0)
    
    def isFIN(self):
        return self.header['flagList'][5]

    def isSYN(self):
        return self.header['flagList'][4]

    def isRST(self):
        return self.header['flagList'][3]

    def isPSH(self):
        return self.header['flagList'][2]

    def isACK(self):
        return self.header['flagList'][1]

    def isURG(self):
        return self.header['flagList'][0]



    # def isREQ(self):
    #     return self.header['flagList'][4]

    # def isSYNC(self):
    #     return self.header['flagList'][3]

    # def isAck(self):
    #     return self.header['flagList'][2]

    # def isFin(self):
    #     return self.header['flagList'][1]

    # def isLastPacket(self):
    #     return self.header['flagList'][0]

    
    def __init__(self, srcPort = 99, desPort = 99, seqNum = 0, ackNum = 0, flagList = (False, False, False, False, False, False), winSize = MAX_WINDOW_SIZE, urgptr = 0, data = None):
        self.header = {}

        if srcPort:
            self.header['srcPort'] = srcPort
        if desPort:
            self.header['desPort'] = desPort
        # RESTART THE SEQUENCE NUMBER(?????)
        if seqNum > MAX_SEQUENCE_NUM:
            self.header['seqNum'] = seqNum - MAX_SEQUENCE_NUM
        else:
            self.header['seqNum'] = seqNum
        
        if ackNum > MAX_ACK_NUM:
            self.header['ackNum'] = ackNum - MAX_ACK_NUM
        else:
            self.header['ackNum'] = ackNum

        if flagList:
            self.header['flagList'] = flagList

        if winSize > MAX_SEQUENCE_NUM:
            self.header['winSize'] = MAX_WINDOW_SIZE
        else:
            self.header['winSize'] = winSize

        # 不知道对不对
        
        self.header['urgptr'] = urgptr

        if data:
            self.data = bytearray(data)
        else:
            self.data = 0

        
        self.header['checksum'] = self._computeChecksum()
        

    def _computeChecksum(self): ##这个看不太懂
        log("Computing checksum...\n")

        self.header['checksum'] = 0

        log("Converting packet to byteArray...\n")

        # 为什么是赋值str
        packet = str(self.toByteArray())

        log("Packet converted to byteArray...\n")
        log("Length of the packet is " + str(len(packet)))

        sum = 0
        for i in range(0, len(packet), 2):
            log(str(i) + '\n')
            #16 bit carry-around addition
            value = ord(packet[i]) + (ord(packet[i + 1]) << 8)
            temp = sum + value
            # 取16位 再看看用不用进位
            sum = (temp & 0xffff) + (temp >> 16)

        return ~sum & 0xffff #16-bit one's complement 反码 



    






    


    
