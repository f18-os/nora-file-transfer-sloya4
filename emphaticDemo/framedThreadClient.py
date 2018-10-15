#! /usr/bin/env python3

# Echo client program
import socket, sys, re, os
import params
from framedSock import FramedStreamSock
from threading import Thread
import time

switchesVarDefaults = (
    (('-s', '--server'), 'server', "localhost:50001"),
    (('-d', '--debug'), "debug", False), # boolean (set if present)
    (('-?', '--usage'), "usage", False), # boolean (set if present)
    (('put', '--put'),"put", "fileName"),
    )


progname = "framedClient"
paramMap = params.parseParams(switchesVarDefaults)

server, usage, debug  = paramMap["server"], paramMap["usage"], paramMap["debug"]
fileName = paramMap["put"]

if usage:
    params.usage()


try:
    serverHost, serverPort = re.split(":", server)
    serverPort = int(serverPort)
except:
    print("Can't parse server:port from '%s'" % server)
    sys.exit(1)

class ClientThread(Thread):
    def __init__(self, serverHost, serverPort, debug):
        global fileName
        Thread.__init__(self, daemon=False)
        self.serverHost, self.serverPort, self.debug = serverHost, serverPort, debug
        self.start()
    def run(self):
       global fileName
       s = None
       for res in socket.getaddrinfo(serverHost, serverPort, socket.AF_UNSPEC, socket.SOCK_STREAM):
           af, socktype, proto, canonname, sa = res
           try:
               print("creating sock: af=%d, type=%d, proto=%d" % (af, socktype, proto))
               s = socket.socket(af, socktype, proto)
           except socket.error as msg:
               print(" error: %s" % msg)
               s = None
               continue
           try:
               print(" attempting to connect to %s" % repr(sa))
               s.connect(sa)
           except socket.error as msg:
               print(" error: %s" % msg)
               s.close()
               s = None
               continue
           break

       if s is None:
           print('could not open socket')
           sys.exit(1)

       fs = FramedStreamSock(s, debug=debug)


       print("sending hello world")
       fs.sendmsg(b"hello world")
       print("received:", fs.receivemsg())

       fs.sendmsg(b"hello world")
       print("received:", fs.receivemsg())
       
       if os.path.isfile(fileName):#Check if file exists
           fileR = open(fileName, "rb")
           fileName1 = "IFL$" +fileName # IFL$ To let the server know it is a file
           fs.sendmsg(fileName1.encode())# Send file name
           receiveP = fs.receivemsg()
           print("received: ", receiveP)
           if receiveP.decode() != "File already in server":
               read = fileR.read(100)
               while read:
                   read = read.decode().strip().encode()
                   fs.sendmsg(read)
                   print("received: ", fs.receivemsg())
                   read = fileR.read(100)
               fileR.close()

for i in range(100):
    ClientThread(serverHost, serverPort, debug)

