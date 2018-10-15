#! /usr/bin/env python3
import sys, os, socket, params, time, threading
from threading import Thread
from framedSock import FramedStreamSock

switchesVarDefaults = (
    (('-l', '--listenPort') ,'listenPort', 50001),
    (('-d', '--debug'), "debug", False), # boolean (set if present)
    (('-?', '--usage'), "usage", False), # boolean (set if present)
    )

progname = "echoserver"
paramMap = params.parseParams(switchesVarDefaults)

debug, listenPort = paramMap['debug'], paramMap['listenPort']
secure = threading.Lock()

if paramMap['usage']:
    params.usage()

lsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # listener socket
bindAddr = ("127.0.0.1", listenPort)
lsock.bind(bindAddr)
lsock.listen(5)
print("listening on:", bindAddr)

class ServerThread(Thread):
    requestCount = 0            # one instance / class
    def __init__(self, sock, debug): 
        Thread.__init__(self, daemon=True)
        self.fsock, self.debug = FramedStreamSock(sock, debug), debug
        self.start()
    def run(self):
        while True:#While the client keeps sending messages
            msg = self.fsock.receivemsg()
            if not msg: #If empty, stop
                if self.debug: print(self.fsock, "server thread done")
                return
            requestNum = ServerThread.requestCount
            time.sleep(0.001)
            ServerThread.requestCount = requestNum + 1
            isAFile = msg.decode().split("$")
            if len(isAFile) > 1: #If it has a file name
                fileName = isAFile[1].encode()
            else:
                fileName = msg
            self.fsock.sendmsg(fileName)
            if isAFile[0] == "IFL":
                if os.path.isfile("serverFolder/"+fileName.decode()):#Check if fileName is in server
                   self.fsock.send(b"File already in server")#File Already in Server
                else:
                    secure.acquire()
                    fileW = open("serverFolder/"+fileName.decode(), "wb")
                    while True:
                        msg = self.fsock.receivemsg()
                        if not msg:
                            break
                        fileW.write(msg)
                        self.fsock.sendmsg(msg)
                    fileW.close()
                    secure.release()
 
            msg = ("%s! (%d)" % (msg, requestNum)).encode()
            self.fsock.sendmsg(msg)


while True: #Keeps the server open
    sock, addr = lsock.accept() #Waits for a client
    ServerThread(sock, debug)
