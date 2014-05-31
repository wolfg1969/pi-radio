# -*- coding: utf-8 -*-

import logging
import os
import sys
import subprocess
from player import Player

logging.basicConfig(filename="/tmp/douban-fmd.log", level=logging.DEBUG)


def radio_on():

    import ConfigParser, os
    
    script_dir = os.path.dirname(os.path.abspath(__file__))

    config = ConfigParser.ConfigParser()
    config.readfp(open(os.path.join(script_dir, "radio.conf")))
    
    frequency = config.get("PirateRadio", "frequency")  # in MHz, default is 76.6
    play_stereo = config.getboolean("PirateRadio", "stereo_playback")
    sample_rate = config.get("PirateRadio", "sample_rate")  # 22050 or 44100 Hz
    
    audio_pipe_r, audio_pipe_w = os.pipe()

    fm_process = subprocess.Popen(["sudo", os.path.join(script_dir, "pifm"), "-", frequency, sample_rate, "stereo" if play_stereo else ""],
                                  stdin=audio_pipe_r, stdout=open(os.devnull, "w"))

    player = Player(
        channel=config.get("DoubanFM", "channel"),
        uid=long(config.get("DoubanFM", "uid")),
        uname=config.get("DoubanFM", "uname"),
        token=config.get("DoubanFM", "token"),
        expire=long(config.get("DoubanFM", "expire")),
        kbps=config.get("DoubanFM", "kbps"),
        play_stereo=play_stereo,
        sample_rate=sample_rate,
        audio_pipe=audio_pipe_w
    )
    player.play()


if __name__ == "__main__":
    
    fpid = os.fork()
    if fpid != 0:
        sys.exit(0)

    radio_on()
