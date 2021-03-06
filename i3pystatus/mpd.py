import socket

from i3pystatus import IntervalModule, formatp
from i3pystatus.core.util import TimeWrapper


def format_time(seconds):
    return "{}:{:02}".format(*divmod(int(seconds), 60)) if seconds else ""


class MPD(IntervalModule):
    """
    Displays various information from MPD (the music player daemon)

    Available formatters (uses `formatp`_)

    * `{title}` — (the title of the current song)
    * `{album}` — (the album of the current song, can be an empty string (e.g. for online streams))
    * `{artist}` — (can be empty, too)
    * `{song_elapsed}` — (Position in the currently playing song, uses `TimeWrapper`_, default is `%m:%S`)
    * `{song_length}` — (Length of the current song, same as song_elapsed)
    * `{pos}` — (Position of current song in playlist, one-based)
    * `{len}` — (Songs in playlist)
    * `{status}` — (play, pause, stop mapped through the `status` dictionary)
    * `{bitrate}` — (Current bitrate in kilobit/s)
    * `{volume}` — (Volume set in MPD)

    Left click on the module play/pauses, right click (un)mutes.
    """

    interval = 1

    settings = (
        ("host"),
        ("port", "MPD port"),
        ("format", "formatp string"),
        ("status", "Dictionary mapping pause, play and stop to output")
    )

    host = "localhost"
    port = 6600
    s = None
    format = "{title} {status}"
    format_sparse = None
    status = {
        "pause": "▷",
        "play": "▶",
        "stop": "◾",
    }

    vol = 100

    def _mpd_command(self, sock, command):
        try:
            sock.send((command + "\n").encode("utf-8"))
        except Exception as e:
            self.s = socket.create_connection((self.host, self.port))
            sock = self.s
            sock.recv(8192)
            sock.send((command + "\n").encode("utf-8"))
        try:
            reply = sock.recv(16384).decode("utf-8")
            replylines = reply.split("\n")[:-2]

            return dict(
                (line.split(": ", 1)) for line in replylines
            )
        except Exception as e:
            return None

    def init(self):
        if not self.format_sparse:
            self.format_sparse = self.format

    def run(self):
        try:
            status = self._mpd_command(self.s, "status")
            currentsong = self._mpd_command(self.s, "currentsong")
            fdict = {
                "pos": int(status.get("song", 0)) + 1,
                "len": int(status["playlistlength"]),
                "status": self.status[status["state"]],
                "volume": int(status["volume"]),

                "title": currentsong.get("Title", ""),
                "album": currentsong.get("Album", ""),
                "artist": currentsong.get("Artist", ""),
                "song_length": TimeWrapper(currentsong.get("Time", 0)),
                "song_elapsed": TimeWrapper(float(status.get("elapsed", 0))),
                "bitrate": int(status.get("bitrate", 0)),

            }
            self.output = {
                "full_text": formatp(self.format, **fdict).strip(),
            }
        except Exception as e:
            self.output = {"full_text": "error connecting MPD"}

    def on_leftclick(self):
        try:
            self._mpd_command(self.s, "pause %i" %
                                      (0 if self._mpd_command(self.s, "status")["state"] == "pause" else 1))
        except Exception as e:
            pass

    def on_rightclick(self):
        try:
            vol = int(self._mpd_command(self.s, "status")["volume"])
            if vol == 0:
                self._mpd_command(self.s, "setvol %i" % self.vol)
            else:
                self.vol = vol
                self._mpd_command(self.s, "setvol 0")
        except Exception as e:
            pass
