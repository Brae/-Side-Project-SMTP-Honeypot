#!/usr/bin/env python

import socket
import sys
import time
import datetime

class Logger:

    logFile = None
    def __init__(self, fname):
        try:
            Logger.logfile = open(fname, 'w')
        except IOError:
            print "[!] Error opening log file. Quitting..."
            sys.exit(1)


    def write_to_log(self, data, id):
        self.ts = time.time()
        self.stamp = datetime.datetime.fromtimestamp(self.ts).strftime('%d-%m-%Y %H:%M:%S')
        Logger.logfile.write(self.stamp + " - " + id + ": " + data + "\n")

    def close_log(self):
        Logger.logfile.close()

class ConnectionHandler:

    _Client = None
    _Logger = None

    # initialise the handler
    def __init__(self, client, logger):
        ConnectionHandler._Client = client
        ConnectionHandler._Logger = logger
        self.stc = self.sendToClient("220 SMTP.BRAE.IO Simple Mail Transfer Service Ready\n")
        if not self.stc:
            return
        ConnectionHandler._Logger.write_to_log("220 SMTP.BRAE.IO Simple Mail Transfer Service Ready", "S")

        #Handle HELO
        self.response = ConnectionHandler._Client.recv(1024)
        ConnectionHandler._Logger.write_to_log(self.response, "C")
        while self.response[:4] != "HELO":
            self.stc = self.sendToClient("502 Use HELO/EHLO first\n")
            if not self.stc:
                return
            ConnectionHandler._Logger.write_to_log("502 Use HELO/EHLO first","S")
            self.response = ConnectionHandler._Client.recv(1024)

        while True:
            self.parseSuccess = self.parseHelo(self.response)
            if self.parseSuccess == 1:
                break
            else:
                self.response = ConnectionHandler._Client.recv(1024)
                ConnectionHandler._Logger.write_to_log(self.response, "C")


        #Handle MAIL FROM
        self.response = ConnectionHandler._Client.recv(1024)
        ConnectionHandler._Logger.write_to_log(self.response, "C")
        while self.response[:4] !=  "MAIL":
            self.stc = self.sendToClient("550 Invalid syntax. Syntax should be MAIL FROM:<userdomain>\n")
            if not self.stc:
                return
            ConnectionHandler._Logger.write_to_log("550 Invalid syntax. Syntax should be MAIL FROM:<userdomain>", "S")
            self.response = ConnectionHandler._Client.recv(1024)

        while True:
            self.parseSuccess = self.parseMailFrom(self.response)
            if self.parseSuccess == 1:
                break
            else:
                self.response = ConnectionHandler._Client.recv(1024)
                ConnectionHandler._Logger.write_to_log(self.response, "C")

        #Handle recipient(s)
        self.response = ConnectionHandler._Client.recv(1024)
        ConnectionHandler._Logger.write_to_log(self.response, "C")
        while self.response[:4] != "RCPT":
            self.stc = self.sendToClient("550 Invalid syntax. Syntax should be RCPT TO:<recipientaddress\n")
            if not self.stc:
                return
            ConnectionHandler._Logger.write_to_log("550 Invalid syntax. Syntax should be RCPT TO:<recipientaddress", "S")
            self.response = ConnectionHandler._Client.recv(1024)

        while self.response[:4] == "RCPT": #For multiple recipientaddress
            while True:
                self.parseSuccess = self.parseRcpt(self.response)
                if self.parseSuccess == 1:
                    break
                else:
                    self.response = ConnectionHandler._Client.recv(1024)
                    ConnectionHandler._Logger.write_to_log(self.response, "C")
            self.response = ConnectionHandler._Client.recv(1024)
            ConnectionHandler._Logger.write_to_log(self.response, "C")

        #Handle data
        while self.response[:4] != "DATA":
            self.stc = self.sendToClient("550 Unexpected command\n")
            if not self.stc:
                return
            ConnectionHandler._Logger.write_to_log("550 Unexpected command", "S")
            self.response = ConnectionHandler._Client.recv(1024)

        self.dataGet = self.getData()

        self.response = ConnectionHandler._Client.recv(1024)
        ConnectionHandler._Logger.write_to_log(self.response, "C")

        while self.response[:4] != "QUIT":
            self.stc = self.sendToClient("550 Unexpected command\n")
            if not self.stc:
                return
            ConnectionHandler._Logger.write_to_log("550 Unexpected command", "S")
            self.response = ConnectionHandler._Client.recv(1024)

        print "[!] Quit received"
        self.stc = self.sendToClient("221 SMTP.BRAE.IO Service closing transmission channel\n")
        if not self.stc:
            return
        ConnectionHandler._Logger.write_to_log("221 SMTP.BRAE.IO Service closing transmission channel", "S")
        ConnectionHandler._Logger.write_to_log("\n=========================================================\n", "S")
        ConnectionHandler._Client.close()

    def sendToClient(self, data):
        try:
            ConnectionHandler._Client.send(data)
        except socket.error, v:
            print "Connection lost"
            ConnectionHandler._Logger.write_to_log("Connection lost", "Error")
            return False
        return True


    def getData(self):
        self.stc = self.sendToClient("354 Start mail input; end with <CRLF>.<CRLF>\n")
        if not self.stc:
            return
        ConnectionHandler._Logger.write_to_log("354 Start mail input; end with <CRLF>.<CRLF>", "S")
        self.content = ""
        while True:
            self.line = ConnectionHandler._Client.recv(1024)
            if self.line and self.line[:1] == ".":
                print "[i] Message complete:", self.content
                self.stc = self.sendToClient("250 OK\n\n")
                if not self.stc:
                    return
                ConnectionHandler._Logger.write_to_log(self.content + "\n", "C")
                return 1
            else:
                self.content += self.line
                print self.line


    def parseHelo(self, data):
        if len(data) > 4:
            self.heloSplit = data.split(' ')
            if self.heloSplit[0] and self.heloSplit[0] == "HELO":
                if self.heloSplit[1] and self.heloSplit[1].rstrip() == "SMTP.BRAE.IO":
                    print "[i] HELO response OK"
                    self.stc = self.sendToClient("250 SMTP.BRAE.IO\n\n")
                    if not self.stc:
                        return
                    ConnectionHandler._Logger.write_to_log("250 SMTP.BRAE.IO\n", "S")
                    return 1
                else:
                    print "[i] HELO domain incorrect"
                    self.stc = self.sendToClient("501 HELO Invalid domain address\n")
                    if not self.stc:
                        return
                    ConnectionHandler._Logger.write_to_log("501 HELO Invalid domain address", "S")
                    return 0
            else:
                print "[i] Not a HELO response"
                self.stc = self.sendToClient("502 Use HELO/EHLO first\n")
                if not self.stc:
                    return
                ConnectionHandler._Logger.write_to_log("502 Use HELO/EHLO first", "S")
                return 0

    def parseMailFrom(self, data):
        self.mailSplit = data.split()
        if self.mailSplit[0] and self.mailSplit[1] and self.mailSplit[0] == "MAIL":
            self.mailSplitb = self.mailSplit[1].split(":")
            if self.mailSplitb[0] and self.mailSplitb[1] and self.mailSplitb[0] == "FROM":
                self.mailSplitc = self.mailSplitb[1].split("@")
                if self.mailSplitc[1] and self.mailSplitc[1] == "BRAE.IO>":
                    print "[i] Mail command OK"
                    self.stc = self.sendToClient("250 OK\n\n")
                    if not self.stc:
                        return
                    ConnectionHandler._Logger.write_to_log("S: 250 OK\n", "S")
                    return 1
                else:
                    print "[i] Invalid mail domain"
                    self.stc = self.sendToClient("550 The address is not valid\n")
                    if not self.stc:
                        return
                    ConnectionHandler._Logger.write_to_log("550 The address is not valid", "S")
                    return 0
            else:
                print "[i] Invalid mail syntax"
                self.stc = self.sendToClient("550 Invalid syntax. Syntax should be MAIL FROM:<userdomain>\n")
                if not self.stc:
                    return
                ConnectionHandler._Logger.write_to_log("550 Invalid syntax. Syntax should be MAIL FROM:<userdomain>", "S")
                return 0
        else:
            print "[i] Invalid mail command"
            self.stc = self.sendToClient("550 Invalid syntax. Syntax should be MAIL FROM:<userdomain>\n")
            if not self.stc:
                return
            ConnectionHandler._Logger.write_to_log("550 Invalid syntax. Syntax should be MAIL FROM:<userdomain>", "S")
            return 0

    def parseRcpt(self, data):
        self.rcptSplit = data.split()
        if self.rcptSplit[0] and self.rcptSplit[0] == "RCPT":
            self.rcptSplitb = self.rcptSplit[1].split(":")
            if self.rcptSplitb[0] and self.rcptSplitb[0] == "TO":
                print "[i] RCPT command OK"
                self.stc = self.sendToClient("250 OK\n\n")
                if not self.stc:
                    return
                ConnectionHandler._Logger.write_to_log("250 OK\n", "S")
                return 1
            else:
                print "[i] RCPT syntax incorrect"
                self.stc = self.sendToClient("550 Invalid syntax. Syntax should be RCPT TO:<recipientaddress>\n")
                if not self.stc:
                    return
                ConnectionHandler._Logger.write_to_log("550 Invalid syntax. Syntax should be RCPT TO:<recipientaddress>", "S")
                return 0
        else:
            print "[i] RCPT syntax incorrect"
            self.stc = self.sendToClient("550 Invalid syntax. Syntax should be RCPT TO:<recipientaddress\n")
            if not self.stc:
                return
            ConnectionHandler._Logger.write_to_log("550 Invalid syntax. Syntax should be RCPT TO:<recipientaddress>", "S")
            return 0





print "Launching SMTP Honeypot\n=======================\n\n"
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
print "[i] Socket initialised"
try:
    sock.bind(('172.16.0.201', 25))
except socket.error, v:
    print "[!] Socket binding failed. Exiting..."
    sys.exit(1)
print "[i] Socket bound"
honeyLog = Logger("robusthoney.log")
print "[i] Log file opened"
sock.listen(5)
print "[i] Listening on port 25..."
while True:
    c, addr = sock.accept()
    print "[i] Connection attempt received. Passing to handler..."
    clientH = ConnectionHandler(c, honeyLog)
    print "[i] Connection complete. Listening..."
