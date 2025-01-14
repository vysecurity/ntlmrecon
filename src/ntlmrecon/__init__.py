import argparse
import json
import requests
import csv
import sys
import os

from colorama import init as init_colorama
from multiprocessing.dummy import Pool as ThreadPool
from ntlmrecon.ntlmutil import gather_ntlm_info
from ntlmrecon.misc import print_banner, wordlist
from ntlmrecon.inpututils import readfile_and_gen_input, read_input_and_gen_list
from termcolor import colored
from urllib.parse import urlsplit, urlunsplit

# Initialize colors in Windows - Because I like Windows too!
init_colorama()

# make the Pool of workers
# TODO: Make this an argument

FOUND_DOMAINS = []


def in_found_domains(url):
    split_url = urlsplit(url)
    if split_url.hostname in FOUND_DOMAINS:
        return True
    else:
        return False


def write_records_to_csv(records, filename):
    if os.path.exists(filename):
        with open(filename, 'a') as file:
            writer = csv.writer(file)
            for record in records:
                csv_record = list()
                url = list(record.keys())[0]
                csv_record.append(url)
                csv_record.extend(list(record[url]['data'].values()))
                writer.writerow(csv_record)
    else:
        with open(filename, 'w+') as file:
            writer = csv.writer(file)
            writer.writerow(['URL', 'AD Domain Name', 'Server Name', 'DNS Domain Name', 'FQDN', 'Parent DNS Domain'])
            for record in records:
                csv_record = list()
                url = list(record.keys())[0]
                csv_record.append(url)
                csv_record.extend(list(record[url]['data'].values()))
                writer.writerow(csv_record)


def main():

    # Init arg parser
    parser = argparse.ArgumentParser(description=print_banner())
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--input', help='Pass input as an IP address, URL or CIDR to enumerate NTLM endpoints')
    group.add_argument('--infile', help='Pass input from a local file')
    # TODO
    # parser.add_argument('--wordlist', help='Override the internal wordlist with a custom wordlist', required=False)
    parser.add_argument('--threads', help="Set number of threads (Default: 10)", required=False, default=10)
    parser.add_argument('--output-type', '-o', help='Set output type. JSON (TODO) and CSV supported (Default: CSV)',
                        required=False, default='csv', action="store_true")
    parser.add_argument('--outfile', help='Set output file name (Default: ntlmrecon.csv)', required=True)
    parser.add_argument('--random-user-agent', help="TODO: Randomize user agents when sending requests (Default: False)",
                        default=False, action="store_true")
    parser.add_argument('--force-all', help="Force enumerate all endpoints even if a valid endpoint is found for a URL "
                                            "(Default : False)", default=False, action="store_true")
    parser.add_argument('--shuffle', help="Break order of the input files", default=False, action="store_true")
    args = parser.parse_args()

    if os.path.isdir(args.outfile):
        print(colored("[!] Invalid filename. Please enter a valid filename!", "red"))
        sys.exit()
    elif os.path.exists(args.outfile):
        print(colored("[!] File already exists. Please choose a different file name", "red"))
        sys.exit()

    pool = ThreadPool(args.threads)

    if args.input:
        if args.shuffle:
            records = read_input_and_gen_list(args.input, shuffle=True)
        else:
            records = read_input_and_gen_list(args.input, shuffle=False)
    elif args.infile:
        if args.shuffle:
            records = readfile_and_gen_input(args.infile, shuffle=True)
        else:
            records = readfile_and_gen_input(args.infile, shuffle=False)

    for record in records:
        all_combos = []
        for word in wordlist:
            # TODO : Dirty now, do sanity checks
            all_combos.append(record+word)
        results = pool.map(gather_ntlm_info, all_combos)
        results = [x for x in results if x]
        write_records_to_csv(results, args.outfile)

    print(colored('[+] All done! Output saved to {}. Happy hacking!'.format(args.outfile), 'green'))




