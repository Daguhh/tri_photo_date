#!/usr/bin/env python3

from time import sleep


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
            f"\r\033[94m [{tags}{spaces}] {percents}\033[00m",
            " | ",
            f"\033[92m {text}\033[00m",
            " > ",
            f"\033[97m {text2}\033[00m",
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
    for i in range(101):
        progress(i)
        sleep(0.5)
