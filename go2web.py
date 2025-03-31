#!/usr/bin/env python3
import sys
import argparse

def main():
    parser = argparse.ArgumentParser(description='go2web - HTTP client and search utility')
    parser.add_argument('-u', '--url', help='make an HTTP request to the specified URL')
    parser.add_argument('-s', '--search', nargs='+', help='search the term using a search engine')
    args = parser.parse_args()

    if not any(vars(args).values()):
        parser.print_help()
        return

    if args.url:
        print(f"Would make request to: {args.url}")
    elif args.search:
        search_term = ' '.join(args.search)
        print(f"Would search for: {search_term}")

if __name__ == '__main__':
    main()