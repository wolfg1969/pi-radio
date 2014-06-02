# -*- coding: utf-8 -*-

import logging
import os
import subprocess
import time
from radio_player import RadioPlayer
from .api import DoubanFmAPI, ReportType


class DoubanFmPlayer(RadioPlayer):

    def __init__(self, config, audio_pipe):
    
        super(self.__class__, self).__init__(config, audio_pipe)
        self.logger = logging.getLogger('douban-fm.player')

        self.channel = self.config.get("DoubanFM", "channel")
        
        uid = self.config.get("DoubanFM", "uid")
        uname = self.config.get("DoubanFM", "uname")
        token = self.config.get("DoubanFM", "token")
        expire = self.config.get("DoubanFM", "expire")
        kbps = self.config.get("DoubanFM", "kbps")

        self.radioAPI = DoubanFmAPI(uid, uname, token, expire, kbps)

        self.play_stereo = self.config.getboolean("PirateRadio", "stereo_playback")
        self.sample_rate = self.config.get("PirateRadio", "sample_rate")

        self.play_list = []
        self.play_history = []
        self.current_song_index = -1

    def play_next(self):
        
        self.__get_next_song()
        
        if self.current_song_index in range(len(self.play_list)):

            song_url = self.play_list[self.current_song_index]['url'].replace('\\','')
            
            self.logger.debug("streaming radio from %s", song_url)
            try:
                subprocess.call(
                    [
                        "/usr/bin/avconv", "-i", song_url, 
                        "-f", "wav",
                        # "-b", "128k",
                        "-ac", "2" if self.play_stereo else "1",
                        "-ar", self.sample_rate, "-"
                    ],
                    stdout=self.audio_pipe, 
                    stderr=open(os.devnull, "w")
                )
            except Exception, e:
                self.logger.debug(e)
        else:
            self.logger.debug("invalid song index %d" % self.current_song_index)        

    def __get_next_song(self):

        self.logger.debug("playlist's len %d, current %d" % (len(self.play_list), self.current_song_index))

        if self.current_song_index == -1:

            self.logger.debug("no playlist, request new")
            
            self.play_list = self.radioAPI.sendLongReport(
                self.channel,
                0,
                ReportType.NEW,
                self.play_history
            )
            self.current_song_index = 0

        elif self.current_song_index >= len(self.play_list)-1:

            self.logger.debug("playlist end, request new")
            
            self.play_list = self.radioAPI.sendLongReport(
                self.channel,
                self.play_list[-2:-1][0]['sid'],
                ReportType.PLAY,
                self.play_history
            )
            self.current_song_index = 0
        else:
            
            self.logger.debug("playlist playing, no need to request")
            self.current_song_index = self.current_song_index + 1 
            
        self.logger.debug("playlist's len %d, next %d" % (len(self.play_list), self.current_song_index))

