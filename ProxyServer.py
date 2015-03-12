#!/usr/bin/env python3
import re, os, sys
from socket import *

BYTES_TO_RECEIVE = 1024
SCRIPT_LOCATION = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
RELATIVE_CACHE_DIR = "cache"
ABSOLUTE_CACHE_DIR = os.path.join(SCRIPT_LOCATION, RELATIVE_CACHE_DIR)
SERVER_HOST = "0.0.0.0"
SERVER_PORT = 12000

print("Absolute cache dir: " + ABSOLUTE_CACHE_DIR)

try:
    # Handle arguments
    SERVER_HOST = sys.argv[1]
    SERVER_PORT = int(sys.argv[2])
    serverSocket = socket(AF_INET, SOCK_STREAM)
    # Reuse local addresses
    serverSocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    # Bind to all interfaces (for now)
    serverSocket.bind(('0.0.0.0', SERVER_PORT))
    # Maximum 10 clients
    serverSocket.listen(10)
except:
    print("""Wrong arguments. Usage:
    python ProxyServer.py proxyserverIP proxyserverPort""")
    sys.exit();

print("Server is listening...")

# Form the HTTP header response to be sent to the client
def formHeaderResponse():
    response = ("HTTP/1.1 200 TRUE\r\n\r\n")
    print("Sending header response 200: " + repr(response))
    return response.encode('utf-8')

# Form the binary response to be sent to the client
def formBinaryResponse(bfLength, bfName):
    # HTTP protocol uses CRLF type endlines
    response = ("HTTP/1.1 200 OK\r\n"
                "Accept-Ranges: bytes\r\n"
                "Keep-Alive: timeout=10, max=100\r\n"
                "Connection: Keep-Alive\r\n"
                # Set content-length, content-type, disposition to faciliate binary download
                "Content-Length: " + str(bfLength) + "\r\n"
                "Content-Type: application/octet-stream\r\n"
                # HTTP protocol expects two endlines as header termination
                "Content-Disposition: attachment; filename=" + bfName + "\r\n\r\n")
    print("Sending content-header response 200: " + repr(response))
    return response.encode('utf-8')

# Form the HTTP 404 response to be sent to the client
def form404Response(rf, isGetRequest):
    html = ("<center>Error 404: File not found!<br>"
            "You have requested for a non existing file: <b>" + rf + "</b><br><br>"
            "Please try another file</center>")
    response = ("HTTP/1.1 404 Not Found\r\n"
                "Keep-Alive: timeout=10, max=100\r\n"
                "Content-Length: " + str(len(html)) + "\r\n"
                "Content-Type: text/html\r\n\r\n")
    if isGetRequest:
        print("Sending content-header response 404: " + repr(response + html))
        return (response + html).encode('utf-8')
    else:
        print("Sending header response 404: " + repr(response))
        return response.encode('utf-8')

# Form the HTTP homepage response to be sent to the client
def formHomePageResponse():
    html = ("<center><b>Welcome!</b><br>"
            "You have reached Steven Huang's web cache server<br><br>"
            "Use me!</center>")
    response = ("HTTP/1.1 200 OK\r\n"
                "Keep-Alive: timeout=10, max=100\r\n"
                "Content-Length: " + str(len(html)) + "\r\n"
                "Content-Type: text/html\r\n\r\n")
    print("Sending content-header homepage response: " + repr(response + html))
    return (response + html).encode('utf-8')

try:
    # Main listen loop
    while True:
        connectionSocket, addr = serverSocket.accept()
        request = connectionSocket.recv(BYTES_TO_RECEIVE).decode('utf-8')
        if not request:
            continue

        # Get the request type and file
        try:
            requestType = request.split()[0]
            requestedFile = request.split()[1]
            # Only handle GET and HEAD request types
            if requestType != 'GET' and requestType != 'HEAD':
                raise Exception;
            print("\nIncoming request: " + repr(request))
        except:
            print("Malformed HTTP request; ignoring..")
            continue

        # Client requests the cache homepage, how curious!
        if requestedFile == "/":
            connectionSocket.send(formHomePageResponse())
            continue

        print("Cache for page: " + repr(requestedFile))
        try:
            # Open file in read-only, binary mode, trim /, in our cache at ABSOLUTE_CACHE_DIR
            binaryFile = open(os.path.join(ABSOLUTE_CACHE_DIR, requestedFile[1:]), 'rb')
            print(" FOUND AT " + ABSOLUTE_CACHE_DIR)
            # If this is a GET request, try to send the contents of the file
            if requestType == 'GET':
                data = binaryFile.read().decode('utf-8')
                connectionSocket.send(formBinaryResponse(len(data), requestedFile))
                for i in range(0, len(data)):
                    connectionSocket.sendall(data[i].encode('utf-8'))
                    print("Sending byte " + str(i + 1) + ": " + repr(data[i]))

                contentLenStr = str(len(data))
                print("Finished sending " + contentLenStr + "/" + contentLenStr + " bytes of ." + requestedFile + " to client")
            else:
                # Otherwise, send the header only
                connectionSocket.send(formHeaderResponse())
            binaryFile.close()
        except ConnectionError as e:
            # Ignore if client crashes
            print(str(e) + ": Client probably exploded, RIP")
        except IOError:
            # The file could not be found. Send 404 response
            print(" NOT FOUND AT " + ABSOLUTE_CACHE_DIR)
            connectionSocket.send(form404Response(requestedFile, requestType == 'GET'))
        finally:
            connectionSocket.close()
except KeyboardInterrupt:
    print("\n^C Detected: Terminating gracefully")
finally:
    print("Server socket closed")
    serverSocket.close()
