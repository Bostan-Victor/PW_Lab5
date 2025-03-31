#!/usr/bin/env python3
import sys
import argparse
import socket
from urllib.parse import urlparse, quote_plus
import html2text
import ssl
from bs4 import BeautifulSoup
import os
import hashlib
import pickle
from pathlib import Path

# Cache directory setup
CACHE_DIR = Path.home() / '.go2web_cache'
CACHE_DIR.mkdir(exist_ok=True)

def get_cache_key(url: str) -> str:
    """Generate a unique filename for each URL using MD5 hash."""
    return hashlib.md5(url.encode()).hexdigest()

def get_cached_response(url: str) -> str | None:
    """Retrieve cached response if it exists."""
    cache_key = get_cache_key(url)
    cache_file = CACHE_DIR / cache_key
    if cache_file.exists():
        with open(cache_file, 'rb') as f:
            return pickle.load(f)
    return None

def cache_response(url: str, response: str) -> None:
    """Save a response to the cache."""
    cache_key = get_cache_key(url)
    cache_file = CACHE_DIR / cache_key
    with open(cache_file, 'wb') as f:
        pickle.dump(response, f)

def http_request(url, accept='text/html', max_redirects=5):
    """
    Make an HTTP/HTTPS request with:
    - Caching
    - HTTPS support
    - Redirect handling
    - Content negotiation
    """
    if max_redirects <= 0:
        return None, "Too many redirects"

    # Check cache first
    cache_key = get_cache_key(url)
    cached = get_cached_response(cache_key)
    if cached:
        return cached['content_type'], cached['body']

    try:
        parsed = urlparse(url)
        if not parsed.scheme:
            url = 'http://' + url
            parsed = urlparse(url)

        host = parsed.netloc
        path = parsed.path or '/'
        if parsed.query:
            path += '?' + parsed.query

        # Prepare headers
        headers = {
            'User-Agent': 'Mozilla/5.0',
            'Accept': accept,
            'Connection': 'close',
            'Host': host
        }

        # Build request
        request = f"GET {path} HTTP/1.1\r\n"
        request += '\r\n'.join(f'{k}: {v}' for k, v in headers.items())
        request += '\r\n\r\n'

        # Create connection
        context = ssl.create_default_context()
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            if parsed.scheme == 'https':
                sock = context.wrap_socket(sock, server_hostname=host)
            port = 443 if parsed.scheme == 'https' else 80
            sock.connect((host, port))
            sock.sendall(request.encode())

            # Receive response
            response = b''
            while True:
                data = sock.recv(4096)
                if not data:
                    break
                response += data

        # Parse response
        headers_part, _, body = response.partition(b'\r\n\r\n')
        headers = headers_part.decode('utf-8', errors='ignore')

        # Check for redirects (301, 302)
        status_line = headers.split('\r\n')[0]
        if '301' in status_line or '302' in status_line:
            for line in headers.split('\r\n'):
                if line.lower().startswith('location:'):
                    new_url = line.split(':', 1)[1].strip()
                    if not new_url.startswith('http'):
                        new_url = f"{parsed.scheme}://{host}{new_url}"
                    return http_request(new_url, accept, max_redirects-1)

        # Get content type
        content_type = 'text/html'  # default
        for line in headers.split('\r\n'):
            if line.lower().startswith('content-type:'):
                content_type = line.split(':', 1)[1].strip()
                break

        decoded_body = body.decode('utf-8', errors='ignore')

        # Cache the response (with content type)
        cache_response(cache_key, {
            'content_type': content_type,
            'body': decoded_body
        })

        return content_type, decoded_body

    except Exception as e:
        print(f"Request failed: {str(e)}")
        return None, None
    
def format_response(content_type, body):
    """Convert response to human-readable format"""
    if 'application/json' in content_type:
        try:
            import json
            parsed = json.loads(body)
            return json.dumps(parsed, indent=2)
        except:
            return body  # Fallback to raw if invalid JSON
    else:
        return make_human_readable(body)

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
    parser = argparse.ArgumentParser(description='go2web - HTTP client')
    parser.add_argument('-u', '--url', help='URL to fetch')
    parser.add_argument('-s', '--search', nargs='+', help='Search term')
    parser.add_argument('--json', action='store_true', help='Prefer JSON response')
    args = parser.parse_args()

    if not any(vars(args).values()):
        parser.print_help()
        return

    if args.url:
        accept = 'application/json' if args.json else 'text/html'
        content_type, response = http_request(args.url, accept)
        if response:
            print(format_response(content_type, response))
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