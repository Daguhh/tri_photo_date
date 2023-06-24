#!/usr/bin/env python3

import os
from tri_photo_date.utils.small_tools import limited_string

if os.name == 'nt':
    W  = ''
    R  = ''
    G  = ''
    O  = ''
    B  = ''
    P  = ''
    BB = ''
    BG = ''
    BW = ''
else:
    W  = '\033[0m'  # white (normal)
    R  = '\033[31m' # red
    G  = '\033[32m' # green
    O  = '\033[33m' # orange
    B  = '\033[34m' # blue
    P  = '\033[35m' # purple
    BB = '\033[94m' # bright blue
    BG = '\033[92m' # bright green
    BW = '\033[97m' # bright white


table_color = lambda xs : (c + x + W for c, x in zip([R,G,B], xs))

class CliProgressBar:
    def __init__(self, width=40):
        self.width = width
        self.init(0)

    def init(self, n):
        n = n if n else 1
        self._progbar_nb_val = n

    def update(self, v, text="", text2=""):
        left = (self.width * v) // self._progbar_nb_val
        right = self.width - left

        tags = "#" * left
        spaces = "_" * right
        percents = f"{100*v//self._progbar_nb_val:.0f}%"

        print(
            f"\r{BB} [{tags}{spaces}] {percents}{W}",
            " | ",
            f"{BG} {limited_string(text,limit=30)}{W}",
            " > ",
            f"{BW} {limited_string(text2, limit=60)} {W}",
            12 * " ",
            sep="",
            end="",
            flush=True,
        )


cli_progbar = CliProgressBar()
# print(text_out, end='\n', flush=True)

# return text_out


if __name__ == "__main__":
    # Example run
    from time import sleep
    for i in range(101):
        progress(i)
        sleep(0.5)
