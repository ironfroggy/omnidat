#!/usr/bin/env python3

import sys
import argparse
import json
import re


parser = argparse.ArgumentParser()
parser.add_argument('filename', metavar='FILE')
parser.add_argument('action', metavar='ACTION', default="LIST")


def print_datum(datum, keys):
    items = list(datum.items())
    if keys:
        items.sort(key=lambda _: keys.index(_[0]))
    print(', '.join(': '.join((k, v)) for (k, v) in items))

def main(argv):
    args, rest = parser.parse_known_args(argv[1:])
    return globals()["do_" + args.action.upper()](args, *rest) or 0

def do_LIST(args, *rest): 
    rest = list(rest)
    filters = None
    keys = []
    if rest:
        while rest and '=' not in rest[0]:
            keys.append(rest.pop(0))
        filters = dict(item.split('=', 1) for item in rest)
    with open(args.filename) as f:
        for line in f:
            linedata = json.loads(line)
            approved = False
            if filters:
                approved = True
                for fkey, fvalue in filters.items():
                    if linedata.get(fkey) != fvalue:
                        approved = False
            else:
                approved = True
            if approved:
                if keys:
                    linedata = dict((k, v) for (k, v) in linedata.items() if k in keys)
                print_datum(linedata, keys)

def do_ADD(args, *rest):
    with open(args.filename, 'a') as f:
        data = dict(item.split('=', 1) for item in rest)
        f.write(json.dumps(data))
        f.write('\n')


if __name__ == '__main__':
    sys.exit(main(sys.argv))
