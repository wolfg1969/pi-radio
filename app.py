# -*- coding: utf-8 -*-

import logging
import os
import sys
import subprocess


logging.basicConfig(filename="/tmp/pi-radio.log", level=logging.DEBUG)


def start_pifm_proc(frequency, sample_rate, play_stereo, audio_pipe_r):
    fm_process = subprocess.Popen([
                                      "sudo",
                                      os.path.join(script_dir, "pifm"),
                                      "-",
                                      frequency,
                                      sample_rate,
                                      "stereo" if play_stereo else ""
                                  ],
                                  stdin=audio_pipe_r, stdout=open(os.devnull, "w"))


def get_player_class(player_name):
    
    last_dot_index = player_name.rfind('.')
    player_mod_name = player_name[:last_dot_index]
    player_class_name = player_name[last_dot_index+1:]
    player_mod = __import__(player_mod_name, fromlist=[player_class_name])
    return getattr(player_mod, player_class_name)

def radio_on():

    import ConfigParser, os
    
    script_dir = os.path.dirname(os.path.abspath(__file__))

    config = ConfigParser.ConfigParser()
    config.readfp(open(os.path.join(script_dir, "radio.conf")))
    
    frequency = config.get("PirateRadio", "frequency")  # in MHz, default is 76.6
    play_stereo = config.getboolean("PirateRadio", "stereo_playback")
    sample_rate = config.get("PirateRadio", "sample_rate")  # 22050 or 44100 Hz
    
    audio_pipe_r, audio_pipe_w = os.pipe()

    #start_pifm_proc(frequency, sample_rate, play_stereo, audio_pipe_r)
    
    player_class = get_player_class(config.get('PirateRadio', 'radio_player'))
    player = player_class(config, audio_pipe_w)
    player.play()


if __name__ == "__main__":
    
    fpid = os.fork()
    if fpid != 0:
        sys.exit(0)

    radio_on()
