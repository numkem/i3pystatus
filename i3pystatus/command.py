#!/usr/bin/env python
# -*- coding: utf-8 -*-

import subprocess

from i3pystatus import IntervalModule


class Command(IntervalModule):
    """
    Show the output of the given command
    """

    settings = (
        "format",
        "executable",
        "color"
    )
    required = ("executable")
    format = "{output}"
    color = "#FFFFFF"
    executable = ""
    interval = 5

    def run(self):
        output = subprocess.check_output(self.executable.split(' '))

        self.output = {
            "full_text": output,
            "color": self.color
        }