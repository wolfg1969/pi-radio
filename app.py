# -*- coding: utf-8 -*-

import logging
import os
import sys
import subprocess
from ConfigParser import ConfigParser


logging.basicConfig(filename="/tmp/pi-radio.log", level=logging.DEBUG)


def start_pifm_proc(pi_fm_dir, frequency, sample_rate, play_stereo, audio_pipe_r):
    cmd = ["sudo", os.path.join(pi_fm_dir, "pifm"), "-", frequency, sample_rate]
    if play_stereo:
        cmd.append("stereo")
    fm_process = subprocess.Popen(cmd, stdin=audio_pipe_r, stdout=open(os.devnull, "w"))


def get_player_class(player_name):
    
    last_dot_index = player_name.rfind('.')
    player_mod_name = player_name[:last_dot_index]
    player_class_name = player_name[last_dot_index+1:]
    player_mod = __import__(player_mod_name, fromlist=[player_class_name])
    return getattr(player_mod, player_class_name)

def on_air():
    
    script_dir = os.path.dirname(os.path.abspath(__file__))

    config = ConfigParser()
    config.readfp(open(os.path.expanduser("~/.pi-radio/radio.conf")))
    
    frequency = config.get("PirateRadio", "frequency")  # in MHz, default is 76.6
    play_stereo = config.getboolean("PirateRadio", "stereo_playback")
    sample_rate = config.get("PirateRadio", "sample_rate")  # 22050 or 44100 Hz
    
    audio_pipe_r, audio_pipe_w = os.pipe()

    start_pifm_proc(script_dir, frequency, sample_rate, play_stereo, audio_pipe_r)
    
    player_class = get_player_class(config.get('PirateRadio', 'radio_player'))
    player = player_class(config, audio_pipe_w)
    player.play()


if __name__ == "__main__":
    
    fpid = os.fork()
    if fpid != 0:
        sys.exit(0)

    on_air()
