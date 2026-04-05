import sys
import socket
import random
from datetime import datetime
import time
import threading


def generate_response(response, answer_section, authority_section, additional_section, qname, qtype, qid):
    response += f'ID: {qid}\n\n'
    response += 'QUESTION SECTION\n'
    response += f'{qname:<21} {qtype:<5}\n\n'
    if len(answer_section) > 0:
        response += 'ANSWER SECTION\n'
        # two loops are needed in case there are >1 'A' records or >1 NS records associated with one qname
        for key, records in answer_section.items():
            for record in records:
                response += f"{key:<21} {record[0]:<5} {record[1]}\n"
        response += '\n'
    if len(authority_section) > 0:
        response += 'AUTHORITY SECTION\n'
        for key, records in authority_section.items():
            for record in records:
                response += f"{key:<21} {record[0]:<5} {record[1]}\n"
        response += '\n'
    if len(additional_section) > 0:
        response += 'ADDITIONAL SECTION\n'
    for key, records in additional_section.items():
        for record in records:
            response += f"{key:<21} {record[0]:<5} {record[1]}\n"
    return response


def process_query(qname, qtype, cache, answer_section=None, authority_section=None, additional_section=None):
    # in the case of recursive call, this is to make sure any data is not overwritten with an empty object
    if answer_section is None:
        answer_section = {}
    if authority_section is None:
        authority_section = {}
    if additional_section is None:
        additional_section = {}
    if qname in cache:
        for qtype_cache, qvalue_cache in cache[qname]:
            # if client is looking for CNAME, then the function ends here, result can be sent.
            if qtype_cache == "CNAME" and qtype == "CNAME":
                answer_section[qname] = cache[qname]
                return answer_section, authority_section, additional_section
            elif qtype_cache == "CNAME" and qtype != "CNAME":
                answer_section[qname] = cache[qname]
            # Change qname to the CNAME found in the record (masterfile.txt) and call function again with the new qname
                new_qname = qvalue_cache
                return process_query(new_qname, qtype, cache, answer_section,
                                     authority_section, additional_section)
            else:
                if qtype == qtype_cache:
                    if qname in answer_section:
                        answer_section[qname].append(
                            (qtype_cache, qvalue_cache))
                    else:
                        answer_section[qname] = []
                        answer_section[qname].append(
                            (qtype_cache, qvalue_cache))
                elif qtype_cache == "A" and qtype == "CNAME":
                    if qname in answer_section:
                        answer_section[qname].append(
                            (qtype_cache, qvalue_cache))
                    else:
                        answer_section[qname] = []
                        answer_section[qname].append(
                            (qtype_cache, qvalue_cache))
        if len(answer_section) > 0:
            last_key = list(answer_section.keys())[-1]
            last_qtype_answer_section = answer_section[last_key][-1][0]

            if len(answer_section) > 0 and last_qtype_answer_section != 'CNAME':
                return answer_section, authority_section, additional_section

    # if qname not in master.txt then we try to find the closest match to refer the client to another server
    qname_split = qname.split('.')

    authority_string = ''
    for i in range(len(qname_split)):
        # if authority string in cache, closest match is found so we test to see if it is an NS record and add it to the authority section dictionary
        authority_string = '.'.join(qname_split[i:])
        if not authority_string:
            authority_string = '.'
        if authority_string in cache:
            authority_section[authority_string] = []
            for qtype_cache, qvalue_cache in cache[authority_string]:
                if qtype_cache == 'NS':
                    authority_section[authority_string].append(
                        (qtype_cache, qvalue_cache))
            if len(authority_section[authority_string]) > 0:
                break
            else:
                del authority_section[authority_string]
                # loop through all the tuples associated with this record to see if we can find an 'A' record for the additonal section of the response

    for tuple in authority_section[authority_string]:
        if tuple[1] in cache:
            additional_section[tuple[1]] = []
            for qtype_cache, qvalue_cache in cache[tuple[1]]:
                if qtype_cache == 'A':
                    additional_section[tuple[1]].append(
                        (qtype_cache, qvalue_cache))
            if len(additional_section[tuple[1]]) == 0:
                del additional_section[tuple[1]]
    return answer_section, authority_section, additional_section


def handle_client(message, client_address, server_socket, cache):
    # timestamp rounding to 3 decimal places taken from https://stackoverflow.com/questions/11040177/datetime-round-trim-number-of-digits-in-microseconds
    rcv_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
    split_message = message.decode().split(' ')
    qname = split_message[0]
    if not qname.endswith('.'):
        qname += '.'
    split_message[0] = qname
    random_delay = random.choice([0, 1, 2, 3, 4])
    print(
        f"{rcv_timestamp} rcv {client_address[1]:<5}: {split_message[2]:<5} {split_message[0]} {split_message[1]:<5} (delay: {random_delay}s)")
    time.sleep(random_delay)
    answer_section, authority_section, additional_section = process_query(
        split_message[0], split_message[1], cache)
    response = generate_response('', answer_section, authority_section,
                                 additional_section,  split_message[0], split_message[1], split_message[2])
    server_socket.sendto(response.encode(), client_address)
    send_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
    print(
        f"{send_timestamp} snd {client_address[1]:<5}: {split_message[2]:<5} {split_message[0]} {split_message[1]}")


if len(sys.argv) != 2:
    print('ERROR! usage: server.py PORT_NUMBER')
    sys.exit()

server_port = int(sys.argv[1])

cache = {}

# can access record type and value using the cache dictionary EG: cache['foo.example.com.'][0][0 for Record type, 1 for value]
with open("master.txt") as file:
    for line in file:
        split_line = line.split()
        if split_line[0] in cache:
            cache[split_line[0]].append((split_line[1], split_line[2]))
        else:
            cache[split_line[0]] = [(split_line[1], split_line[2])]


# basic UDP socket code  taken from https://webcms3.cse.unsw.edu.au/COMP3331/24T2/resources/98572
server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_socket.bind(('127.0.0.1', server_port))

while True:
    message, client_address = server_socket.recvfrom(2048)
    # threading in python tutorial and sample code taken from https://www.geeksforgeeks.org/multithreading-python-set-1/amp/
    threading.Thread(target=handle_client, args=(
        message, client_address, server_socket, cache)).start()
