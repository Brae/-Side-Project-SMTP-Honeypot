#!/usr/bin/env python

import socket
import sys

def parseHelo(data, logfile):
    logfile.write("C: " + data + "\n")
    heloSplit = data.split()
    if heloSplit[0] == "HELO":
        if heloSplit[1] == "SMTP.BRAE.IO":
            print "HELO response OK"
            client.send("250 SMTP.BRAE.IO\n\n")
            logfile.write("S: 250 SMTP.BRAE.IO\n\n")
            return 1
        else:
            print "HELO response incorrect"
            client.send("501 HELO Invalid domain address\n")
            logfile.write("S: 501 HELO Invalid domain address\n")
            return 0
    else:
        print "Not a HELO response"
        client.send("502 Use HELO/EHLO first\n")
        logfile.write("S: 502 Use HELO/EHLO first\n")
        return 0

def parseMailFrom(data, logfile):
    logfile.write("C: " + data + "\n")
    mailSplit = data.split()
    if mailSplit[0] == "MAIL":
        mailSplitb = mailSplit[1].split(":")
        if mailSplitb[0] == "FROM":
            mailSplitc = mailSplitb[1].split("@")
            if mailSplitc[1] == "BRAE.IO>":
                print "Mail command OK"
                client.send("250 OK\n\n")
                logfile.write("S: 250 OK\n\n")
                return 1
            else:
                print mailSplitc[1], "\n"
                print "Invalid mail domain"
                client.send("550 The address is not valid\n")
                logfile.write("S: 550 The address is not valid\n")
                return 0
        else:
            print "Invalid syntax"
            client.send("550 Invalid syntax. Syntax should be MAIL FROM:<userdomain>\n")
            logfile.write("S: 550 Invalid syntax. Syntax should be MAIL FROM:<userdomain>\n")
            return 0
    else:
        print "Invalid command"
        client.send("550 Invalid syntax. Syntax should be MAIL FROM:<userdomain>\n")
        logfile.write("S: 550 Invalid syntax. Syntax should be MAIL FROM:<userdomain>\n")
        return 0

def parseRcpt(data, logfile):
    logfile.write("C: " + data + "\n")
    rcptSplit = data.split()
    if rcptSplit[0] == "RCPT":
        rcptSplitb = rcptSplit[1].split(":")
        if rcptSplitb[0] == "TO":
            print "RCPT command OK"
            client.send("250 OK\n\n")
            logfile.write("S: 250 OK\n\n")
            return 1
        else:
            print "RCPT syntax incorrect"
            client.send("550 Invalid syntax. Syntax should be RCPT TO:<recipientaddress>\n")
            logfile.write("S: 550 Invalid syntax. Syntax should be RCPT TO:<recipientaddress>\n")
            return 0
    else:
        print "RCPT syntax incorrect"
        client.send("550 Invalid syntax. Syntax should be RCPT TO:<recipientaddress\n")
        logfile.write("S: 550 Invalid syntax. Syntax should be RCPT TO:<recipientaddress>\n")
        return 0

def getData(logfile):
    client.send("354 Start mail input; end with <CRLF>.<CRLF>\n")
    logfile.write("S: 354 Start mail input; end with <CRLF>.<CRLF>\n")
    content = ""
    while True:
        line = client.recv(1024)
        if line[:1] == ".":
            print "Message complete:", content
            client.send("250 OK\n\n")
            logfile.write("C: " + content + "\n\n")
            return content
        else:
            content += line
            print line




def clientHandler(client, logfile):
    client.send("220 SMTP.BRAE.IO Simple Mail Transfer Service Ready\n")
    logfile.write("S: 220 SMTP.BRAE.IO Simple Mail Transfer Service Ready\n")
    response = client.recv(1024)

    #Loop until correct input given i.e. HELO SMTP.BRAE.IO
    while True:
        success = parseHelo(response, logfile)
        if success == 0:
            response = client.recv(1024)
        else:
            break

    #Check the MAIL FROM command that should come next
    response = client.recv(1024)
    while True:
        success = parseMailFrom(response, logfile)
        if success == 0:
            response = client.recv(1024)
        else:
            break

    #Handle RCPT command(s)
    response = client.recv(1024)
    while True:
        success = parseRcpt(response, logfile)
        if success == 0:
            response = client.recv(1024)
        else:
            response = client.recv(1024)
            if response[:4] != "RCPT":
                break

    #Handle data
    while True:
        if response[:4] == "DATA":
            logfile.write("C: DATA\n")
            data = getData(logfile)
            break
        else:
            client.send("550 Unexpected command\n")
            response = client.recv(1024)

    #Handle quit
    while True:
        response = client.recv(1024)
        if response[:4] == "QUIT":
            print "QUIT received"
            logfile.write("C: QUIT\n")
            client.send("221 SMTP.BRAE.IO Service closing transmission channel\n")
            logfile.write("S: 221 SMTP.BRAE.IO Service closing transmission channel\n")
            break
        else:
            client.send("550 Unexpected command\n")
            logfile.write("S: 550 Unexpected command\n")
    client.close()
    logfile.write("\n\n---------------------------------------------------------------------\n\n")

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
print "Creating socket..."
print "Binding..."
sock.bind(('127.0.0.1', 25))
print "Opening log file"
logFile = open("honey.log", 'a')
sock.listen(5)
print "Listening on port 25"
while True:
    client, addr = sock.accept()
    print "Received connection"
    clientHandler(client,logFile)
