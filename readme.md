# UDP DNS Server (Python)

## Overview

A simplified DNS server and client built using UDP sockets. The server resolves queries using a local cache (`master.txt`) and supports A, CNAME, and NS records.

## Files

- `server.py` – multi-threaded UDP server
- `client.py` – sends queries to the server
- `master.txt` – DNS records used as cache

## Run

Start server:

python server.py <PORT>

Run client:

python client.py <PORT> <qname> <qtype> <timeout>

Example:

python client.py 8080 foo.example.com. A 1

## Features

- UDP communication
- Multi-threaded request handling
- CNAME recursion
- Authority and additional sections for referrals
- Simulated network delay

## How it works

- Server loads `master.txt` into a dictionary
- Each request is handled in a new thread (can accept multiple requests concurrently)
- Queries are resolved via cache lookup and recursion
- Responses are returned as formatted strings

## Limitations

- Not a full DNS implementation
- Uses string-based messages (not real DNS packets)
- Basic error handling
- Requires correct file paths (`master.txt` must be present)

## Summary

Demonstrates socket programming, concurrency, and basic DNS resolution logic using Python.
