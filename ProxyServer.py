#!/usr/bin/env python3
import re, os, sys, time
from socket import *
import colorama.colorama as CLR

CLR.init()

# START CLIENT CODE FROM HTTPWEBSERVER project1
CONTENT_LENGTH_HEADER = "Content-Length: "
CRLF = '\r\n'
FILE_NAME_PREPEND = "DL_"
TIME_OUT_LIMIT = 3
# END CLIENT CODE FROM HTTPWEBSERVER project1
BYTES_TO_RECEIVE = 1024
SCRIPT_LOCATION = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
RELATIVE_CACHE_DIR = "cache"
ABSOLUTE_CACHE_DIR = os.path.join(SCRIPT_LOCATION, RELATIVE_CACHE_DIR)
SERVER_HOST = "0.0.0.0"
SERVER_PORT = 12000

desiredHost = "localhost"

print("Absolute cache dir: " + ABSOLUTE_CACHE_DIR)
# create the cache directory
if not os.path.exists(RELATIVE_CACHE_DIR):
    os.makedirs(RELATIVE_CACHE_DIR)

# text, color, text, color, ...
def p(*args):
    arglen = len(args)
    if arglen % 2 != 0:
        raise ValueError
    elif arglen < 2:
        print('')
        return
    else:
        txt = args[0]
        color = args[1].upper()
        if color == "GREEN":
            print(CLR.Fore.GREEN + txt + CLR.Fore.RESET, end = '')
        elif color == "BLUE":
            print(CLR.Fore.BLUE + txt + CLR.Fore.RESET, end = '')
        elif color == "RED":
            print(CLR.Fore.RED + txt + CLR.Fore.RESET, end = '')
        elif color == "YELLOW":
            print(CLR.Fore.YELLOW + txt + CLR.Fore.RESET, end = '')
        elif color == "RESET":
            print(CLR.Fore.RESET + txt, end = '')
        else:
            print(txt)
        p(*args[2:])

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
    python3 ProxyServer.py proxyserverIP proxyserverPort""")
    sys.exit();

p("Server is listening...", "GREEN")

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

def parseFileOrHost(requestedSite):
    lastSlashIndex = requestedSite.rfind("/")
    parsedHost = ""
    parsedFile = ""
    # if last slash exists and is not first slash
    if lastSlashIndex != -1 and lastSlashIndex != 0:
        parsedFile = requestedSite[lastSlashIndex:]
        parsedHost = requestedSite[:lastSlashIndex]
    else:
        parsedHost = requestedSite
    return parsedHost, parsedFile

def cacheExists(parsedHost, parsedFile):

def cacheDoesNotExist(parsedHost, parsedFile):

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
            requestedSite = request.split()[1]
            # Only handle GET and HEAD request types
            if requestType != 'GET' and requestType != 'HEAD':
                raise Exception;
            p("\nIncoming request: ", "BLUE", repr(request), "YELLOW")
        except:
            p("Malformed HTTP request; ignoring..", "RED")
            continue

        # Client requests the cache's homepage; how curious!
        if requestedSite == "/":
            connectionSocket.send(formHomePageResponse())
            continue

        p("Client requests cache of object: ", "BLUE", repr(requestedSite), "YELLOW")
        parsedHost, parsedFile = parseFileOrHost(requestedSite)
        p("Requested host: ", "BLUE", parsedHost, "YELLOW")
        p("Requested file: ", "BLUE", parsedFile, "YELLOW")
        try:
            # lstrip to assure python this is a relative dir
            desiredCacheDir = os.path.join(RELATIVE_CACHE_DIR, parsedHost.lstrip('/'))
            p("Requested cache dir: /", "BLUE", desiredCacheDir, "YELLOW")
            if not os.path.exists(desiredCacheDir):
                p("Does not exist in our cache; creating it now..", "RED")
                os.makedirs(desiredCacheDir)
                cacheDoesNotExist()
            else:
                p("Exists in our cache...", "GREEN")
                cacheExists()
            # Open file in read-only, binary mode, trim /, in our cache at ABSOLUTE_CACHE_DIR
            binaryFile = open(os.path.join(ABSOLUTE_CACHE_DIR, requestedSite[1:]), 'rb')
            print(" FOUND AT " + ABSOLUTE_CACHE_DIR)
            # If this is a GET request, try to send the contents of the file
            if requestType == 'GET':
                data = binaryFile.read().decode('utf-8')
                connectionSocket.send(formBinaryResponse(len(data), requestedSite))
                for i in range(0, len(data)):
                    connectionSocket.sendall(data[i].encode('utf-8'))
                    print("Sending byte " + str(i + 1) + ": " + repr(data[i]))

                contentLenStr = str(len(data))
                print("Finished sending " + contentLenStr + "/" + contentLenStr + " bytes of ." + requestedSite + " to client")
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
            connectionSocket.send(form404Response(requestedSite, requestType == 'GET'))
        finally:
            connectionSocket.close()
except KeyboardInterrupt:
    print("\n^C Detected: Terminating gracefully")
finally:
    print("Server socket closed")
    serverSocket.close()

# START CLIENT CODE FROM HTTPWEBSERVER project1

# Form the HTTP request to be sent to the server
def formRequest(req_type, req_name):
    response = (req_type + " /" + req_name + " HTTP/1.1"+2*CRLF)
    print("Sending request: " + repr(response))
    return (response).encode('utf-8')

# Parse content length from headers
def getContentLength(headers):
    leftIndex = headers.find(CONTENT_LENGTH_HEADER)
    if leftIndex == -1:
        return -1
    else:
        leftIndex += len(CONTENT_LENGTH_HEADER)
    rightIndex = headers.find(CRLF, leftIndex)
    return int(headers[leftIndex:rightIndex])

# Listen for and only return HTTP headers from server
def getHeaders():
    rcvBuffer = ""
    httpHeaders = ""
    while True:
        response = clientSocket.recv(BYTES_TO_RECEIVE).decode('utf-8')
        if not response:
            continue
        rcvBuffer += response;
        lastCRLFindex = rcvBuffer.rfind(CRLF)
        if lastCRLFindex != -1:
            # We assume valid HTTP responses (2 CRLFs as header termination)
            for line in rcvBuffer[:lastCRLFindex + 2].splitlines(True):
                httpHeaders += line
                if line == CRLF and httpHeaders[-2:] == CRLF:
                    return httpHeaders, rcvBuffer[2 + lastCRLFindex:]
            rcvBuffer = rcvBuffer[2 + lastCRLFindex:]

# Listen for and only return content from server
def getContent(rcvBuffer, cl):
    contentBuffer = rcvBuffer
    if len(contentBuffer) >= cl:
        return contentBuffer
    while True:
        content = clientSocket.recv(BYTES_TO_RECEIVE).decode('utf-8')
        if not content:
            continue
        contentBuffer += content
        if len(contentBuffer) >= cl:
            return contentBuffer

def s2sTo(_host, _port):
    try:
        # Create a socket of our own to retrieve and cache files from webservers for clients
        clientSocket = socket(AF_INET, SOCK_STREAM)
        # Gracefully handle timeouts
        clientSocket.settimeout(TIME_OUT_LIMIT)
        clientSocket.connect((_host, server_port))
    except timeout:
        print("Timed out. Is " + _host + " reachable?")
    except ConnectionRefusedError:
        print("Connection refused. Is " + _host + " reachable?")
    except:
        print("Failed to connect to " + _host)
    finally:
        return

    print("Connected to " + _host + " on port 80\n")
    clientSocket.send(formRequest(request_type, file_name))
    print("Client's request has been forwarded. Awaiting response...\n")

    try:
        headers, rcvBuffer = getHeaders()
        responseCode = headers.split()[1]

        if responseCode == '200':
            if request_type == 'GET':
                info = ""
                try:
                    print("Response code 200 received: " + repr(headers)  + "\nDownloading file...")
                    content = getContent(rcvBuffer, getContentLength(headers))
                    info = "File successfully downloaded to "
                except timeout:
                    # Timing out shouldn't happen, but if it does, continue anyways
                    info = "File partially downloaded due to timeout; writing file anyways to "
                finally:
                    # Write the received content to file
                    with open(os.path.join(SCRIPT_LOCATION, FILE_NAME_PREPEND + file_name), 'wb') as binaryFile:
                        binaryFile.write(content.encode('utf-8'))
                        print(info + FILE_NAME_PREPEND + file_name + ": " + repr(content) + '\n')
            elif request_type == 'HEAD':
                print("Response code 200 (TRUE) received: " + repr(headers) + "\n")
        elif responseCode == '404':
            if request_type == 'GET':
                print("Response code 404 received: " + repr(headers + getContent(rcvBuffer, getContentLength(headers)) + "\n"))
            elif request_type == 'HEAD':
                print("Response code 404 received: " + repr(headers) + "\n")
    except timeout:
        print("\nTimed out. Exiting")
    except (ValueError, IndexError):
        print("\nReceived malformed headers. Exiting")
    except KeyboardInterrupt:
        print("\n^C Detected. Terminating gracefully")
    finally:
        print("Client socket closed")
        clientSocket.close()

# END CLIENT CODE FROM HTTPWEBSERVER project1
