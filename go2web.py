#!/usr/bin/env python3
import sys
import argparse
import socket
from urllib.parse import urlparse, quote_plus
import html2text
import ssl
from bs4 import BeautifulSoup

def http_request(url, headers=None):
    try:
        parsed = urlparse(url)
        if not parsed.scheme:
            url = 'http://' + url
            parsed = urlparse(url)
            
        host = parsed.netloc
        path = parsed.path if parsed.path else '/'
        if parsed.query:
            path += '?' + parsed.query
        
        # Set default headers
        default_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
            'Accept': 'text/html',
            'Connection': 'close'
        }
        if headers:
            default_headers.update(headers)
            
        headers_str = '\r\n'.join(f'{k}: {v}' for k, v in default_headers.items())
        request = f"GET {path} HTTP/1.1\r\nHost: {host}\r\n{headers_str}\r\n\r\n"
        
        # Create appropriate socket connection
        context = ssl.create_default_context()
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if parsed.scheme == 'https':
                s = context.wrap_socket(s, server_hostname=host)
            port = 443 if parsed.scheme == 'https' else 80
            s.connect((host, port))
            s.sendall(request.encode())
            
            response = b''
            while True:
                data = s.recv(4096)
                if not data:
                    break
                response += data
        
        headers, _, body = response.partition(b'\r\n\r\n')
        return body.decode('utf-8', errors='ignore')
    
    except Exception as e:
        print(f"Request failed: {str(e)}")
        return None

def make_human_readable(html):
    h = html2text.HTML2Text()
    h.ignore_links = False
    h.ignore_images = True
    return h.handle(html)

def search_bing(query):
    try:
        search_url = f"http://www.bing.com/search?q={quote_plus(query)}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept-Language': 'en-US,en;q=0.9'
        }
        
        html = http_request(search_url, headers)
        if not html:
            return []
            
        soup = BeautifulSoup(html, 'html.parser')
        results = []
        
        # Find all result blocks in Bing
        for result in soup.find_all('li', class_='b_algo'):
            link = result.find('a')
            if link:
                title = link.get_text(strip=True)
                href = link['href']
                results.append({
                    'title': title,
                    'link': href
                })
                if len(results) >= 10:
                    break
        
        return results
            
    except Exception as e:
        print(f"Search error: {str(e)}")
        return []

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
        if response:
            clean_response = make_human_readable(response)
            print(clean_response)
    elif args.search:
        search_term = ' '.join(args.search)
        results = search_bing(search_term)
        
        if results:
            print(f"Top {len(results)} results for '{search_term}':\n")
            for i, result in enumerate(results, 1):
                print(f"{i}. {result['title']}")
                print(f"   {result['link']}\n")
        else:
            print("No results found. Please try a different search term.")

if __name__ == '__main__':
    main()