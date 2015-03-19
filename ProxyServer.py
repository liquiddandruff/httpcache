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
    # lstrip to assure python that these are a relative dirs
    return parsedHost.lstrip("/"), parsedFile.lstrip("/")

def cacheExists(clientSocket, cacheDir, parsedFile):
    try:
        # Open file in read-only, binary mode, trim /, in the cache 
        path = os.path.join(cacheDir, parsedFile)
        p("The path: " + path, "RED")
        binaryFile = open(os.path.join(cacheDir, parsedFile), 'rb')
        # If this is a GET request, try to send the contents of the file
        if requestType == 'GET':
            data = binaryFile.read().decode('utf-8')
            clientSocket.send(formBinaryResponse(len(data), requestedSite))
            for i in range(0, len(data)):
                clientSocket.sendall(data[i].encode('utf-8'))
                print("Sending byte " + str(i + 1) + ": " + repr(data[i]))

            contentLenStr = str(len(data))
            print("Finished sending " + contentLenStr + "/" + contentLenStr + " bytes of ." + requestedSite + " to client")
        else:
            # Otherwise, send the header only
            clientSocket.send(formHeaderResponse())
        binaryFile.close()
    except ConnectionError as e:
        # Ignore if client crashes
        print(str(e) + ": Client probably exploded, RIP")
    except IOError:
        # The file could not be found. Send 404 response
        print(" NOT FOUND AT " + ABSOLUTE_CACHE_DIR)
        clientSocket.send(form404Response(requestedSite, requestType == 'GET'))
    finally:
        clientSocket.close()
    return ""

def cacheObjDoesNotExist(parsedHost, parsedFile, cacheDir):
    p("Requested cache dir exists but cache object does not exist; requesting it now from origin..", "RED")
    server2server(parsedHost, 80, "GET", parsedFile, cacheDir)
    return ""

def run():
    print("Absolute cache dir: " + ABSOLUTE_CACHE_DIR)
    # create the cache directory
    if not os.path.exists(RELATIVE_CACHE_DIR):
        os.makedirs(RELATIVE_CACHE_DIR)

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

            p("Client requests cache of object: ", "BLUE", requestedSite, "YELLOW")
            parsedHost, parsedFile = parseFileOrHost(requestedSite)
            desiredCacheDir = os.path.join(RELATIVE_CACHE_DIR, parsedHost)
            desiredCacheObj = os.path.join(desiredCacheDir, parsedFile)
            p("Requested host: ", "BLUE", parsedHost, "YELLOW")
            p("Requested file: ", "BLUE", parsedFile, "YELLOW")
            p("Requested cache dir: ", "BLUE", desiredCacheDir, "YELLOW")
            p("Requested cache file: ", "BLUE", os.path.join(desiredCacheDir, parsedFile), "YELLOW")
            if not os.path.exists(desiredCacheDir):
                p("Requested cache dir does not exist; creating it now...", "RED")
                os.makedirs(desiredCacheDir)
                if os.path.exists(desiredCacheObj):
                    p("This shouldn't happen, LOL", "RED")
                else:
                    cacheObjDoesNotExist(parsedHost, parsedFile, desiredCacheDir)
            else:
                p("Requested cache dir exists; looking around...", "GREEN")
                if os.path.exists(desiredCacheObj):
                    p("Requested object exists in our cache; fetching it now...", "GREEN")
                    cacheExists(connectionSocket, desiredCacheDir, parsedFile)
                else:
                    cacheObjDoesNotExist(parsedHost, parsedFile, desiredCacheDir)

    except KeyboardInterrupt:
        print("\n^C Detected: Terminating gracefully")
    finally:
        print("Server socket closed")
        serverSocket.close()

# START CLIENT CODE FROM HTTPWEBSERVER project1

# Form the HTTP request to be sent to the server
def formRequest(req_type, req_host, req_file):
    response = (req_type + " /" + req_file + " HTTP/1.1"+2*CRLF
                + "Host: " + req_host + 2*CRLF)
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
def getHeaders(clientSocket):
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
def getContent(clientSocket, rcvBuffer, cl):
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

def server2server(_host, _port, request_type, _file, destCacheFolder):
    # format _host properly
    _host = "www." + _host if _host.find("www.") == -1 else _host
    p(_host + " " + str(_port) + " " + request_type + " " + destCacheFolder, "GREEN")
    clientSocket = ""
    try:
        # Create a socket of our own to retrieve and cache files from webservers for clients
        clientSocket = socket(AF_INET, SOCK_STREAM)
        # Gracefully handle timeouts
        clientSocket.settimeout(TIME_OUT_LIMIT)
        clientSocket.connect((_host, _port))
        print("Connected to " + _host + " on port 80")
        clientSocket.send(formRequest(request_type, _host, _file))
        print("Client's request has been forwarded. Awaiting response...")

        try:
            headers, rcvBuffer = getHeaders(clientSocket)
            responseCode = headers.split()[1]

            p("server2server headers: " + headers, "RED")
            p("server2server content: " + getContent(clientSocket, rcvBuffer, getContentLength(headers)), "BLUE")

            if responseCode == '404':
                print("Response code 404 received: " + repr(headers + getContent(clientSocket, rcvBuffer, getContentLength(headers)) + "\n"))
            #elif responseCode == '404':
            else:
                info = ""
                try:
                    print("Response code " + responseCode + " received: " + repr(headers)  + "\nDownloading file...")
                    content = getContent(clientSocket, rcvBuffer, getContentLength(headers))
                    info = "File successfully downloaded to "
                except timeout:
                    # Timing out shouldn't happen, but if it does, continue anyways
                    info = "File partially downloaded due to timeout; writing file anyways to "
                finally:
                    # Write the received contents to file
                    target = os.path.join(destCacheFolder, _file)
                    with open(target, 'wb') as binaryFile:
                        binaryFile.write(content.encode('utf-8'))
                        print(info + target + ": " + repr(content) + '\n')
        except timeout:
            print("\nTimed out. Exiting")
        except (ValueError, IndexError):
            print("\nReceived malformed headers. Exiting")
        except KeyboardInterrupt:
            print("\n^C Detected. Terminating gracefully")
        except Exception as e:
            print("Final exception: " + str(e))
        finally:
            print("Client socket closed")
            clientSocket.close()
    except timeout:
        print("Timed out. Is " + _host + " reachable?")
    except ConnectionRefusedError:
        print("Connection refused. Is " + _host + " reachable?")
    except Exception as e:
        print("Failed to connect to " + _host + ": " + str(e))
    finally:
        p("return?", "RED")
        return


# END CLIENT CODE FROM HTTPWEBSERVER project1

if __name__ == "__main__":
    run()

