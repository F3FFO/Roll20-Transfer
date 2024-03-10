import os
import sys

is_ci = "CI" in os.environ and os.environ["CI"] == "true"


def error(str):
    if is_ci:
        print(f"\n ! {str}\n")
    else:
        print(f"\n\033[41m{str}\033[0m\n")
    sys.exit(1)


def vprint(args, str):
    if args.verbose:
        print(str)
