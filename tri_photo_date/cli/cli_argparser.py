#!/usr/bin/env python3

import argparse
from pathlib import Path

CLI_DUMP = 1
CLI_DUMP_DEFAULT = 2
CLI_LOAD = 3
CLI_RUN = 4


class StorePath(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        if values is None:
            setattr(namespace, self.dest, "./tri_photo_date.ini")
        else:
            setattr(namespace, self.dest, values)


def parse_arguments():
    """Parse command line arguments"""

    parser = argparse.ArgumentParser(
        prog="tri_photo_date", description="""Sort image using metadata placeholder """
    )

    parser.add_argument('mode', nargs='?', default='gui',help='shell/gui, chose interface to run, gui will be run by default')

    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "-d",
        "--dump",
        help="save actual config to path and exit",
        const="./tri_photo_date.toml",
        nargs="?",
        action=StorePath,
        dest="dump",
    )
    group.add_argument(
        "-D",
        "--dump-default",
        help="save default config to path and exit",
        nargs="?",
        action=StorePath,
        dest="dump_default",
        const="./tri_photo_date.toml",
    )
    group.add_argument(
        "-l",
        "--load",
        help="run the program with given config",
        nargs="?",
        action=StorePath,
        dest="load",
        const="./tri_photo_date.toml",
    )

    return parser.parse_known_args()

def cli_arguments():

    args, *_ = parse_arguments()

    if args.dump is not None:
        return CLI_DUMP, Path(args.dump).resolve()
    elif args.dump_default is not None:
        return CLI_DUMP_DEFAULT, Path(args.dump_default).resolve()
    elif args.load is not None:
        return CLI_LOAD, Path(args.load).resolve()
    else:
        return CLI_RUN, None


if __name__ == "__main__":
    print(cli_arguments())
