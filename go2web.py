#!/usr/bin/env python3
import sys
import argparse
import socket
from urllib.parse import urlparse

def http_request(url):
    # Parse URL
    parsed = urlparse(url)
    host = parsed.netloc
    path = parsed.path if parsed.path else '/'
    
    # Create socket connection
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((host, 80))
        request = f"GET {path} HTTP/1.1\r\nHost: {host}\r\nConnection: close\r\n\r\n"
        s.sendall(request.encode())
        
        response = b''
        while True:
            data = s.recv(1024)
            if not data:
                break
            response += data
    
    # Parse response
    headers, _, body = response.partition(b'\r\n\r\n')
    return body.decode('utf-8', errors='ignore')

def main():
    parser = argparse.ArgumentParser(description='go2web - HTTP client and search utility')
    parser.add_argument('-u', '--url', help='make an HTTP request to the specified URL')
    parser.add_argument('-s', '--search', nargs='+', help='search the term using a search engine')
    args = parser.parse_args()

    if not any(vars(args).values()):
        parser.print_help()
        return

    if args.url:
        response = http_request(args.url)
        print(response)
    elif args.search:
        search_term = ' '.join(args.search)
        print(f"Would search for: {search_term}")

if __name__ == '__main__':
    main()