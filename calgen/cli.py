import argparse
import calgen
import logging

logging.basicConfig(level=logging.DEBUG)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('calendar', nargs='+', help='Calendar config')
    args = parser.parse_args()
    cal = calgen.Calendar(args.calendar)
    print cal.format()
    return 0
