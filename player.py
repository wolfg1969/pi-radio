# -*- coding: utf-8 -*-

import logging
import os
import subprocess
import time
from api import RadioAPI, ReportType


class PlayerStatus:
    INIT = 0
    PLAY = 1
    PAUSE = 2
    STOP = 3


class Player:

    def __init__(self, uid, uname, token, expire, play_stereo, sample_rate, audio_pipe):
    
        self.logger = logging.getLogger('douban-pi-radio.player')

        self.channel = 0

        self.radioAPI = RadioAPI(uid, uname, token, expire)

        self.play_stereo = play_stereo
        self.audio_pipe = audio_pipe
        self.sample_rate = sample_rate

        self.play_list = []
        self.play_history = []
        self.current_song_index = -1

        self.status = PlayerStatus.INIT

    def close(self):
        pass

    def __login(self):
        pass
        
    def __play(self):                  
        
        if self.current_song_index in range(len(self.play_list)):

            song_url = self.play_list[self.current_song_index]['url'].replace('\\','')
            
            self.logger.debug("streaming radio from %s", song_url)
            try:
                subprocess.call(
                    [
                        "/usr/bin/ffmpeg", "-i", song_url, 
                        "-f", "s16le",
                        "-acodec", "pcm_s16le",
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

    def __stop(self):
        self.logger.debug("stop at index: %d" % self.current_song_index)        

    def __pause(self):
        pass

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
              
    def playNextSong(self, signum, frame):
    
        self.__opCurrentSong(ReportType.END)
        self.__get_next_song()
        self.__play()  

    def play(self):
        self.logger.info("play")

        if self.status == PlayerStatus.INIT:
            while (True):  # TODO play forever now
                self.__get_next_song()
                self.__play()
                time.sleep(1)
            
        #elif self.status == PlayerStatus.STOP:        
        #    self.__play()

        #elif self.status == PlayerStatus.PAUSE:
        #    try:
        #        os.kill(self.mpg321_pid, signal.SIGCONT)
        #    except OSError:
        #        pass

        self.status = PlayerStatus.PLAY
        return self.__current_song_info()

    def stop(self):
        self.logger.info("stop")

        if self.status == PlayerStatus.PLAY or self.status == PlayerStatus.PAUSE:            
            self.__stop()
            self.status = PlayerStatus.STOP

    def pause(self):
        self.logger.info("pause")
        
        self.__pause()
        self.status = PlayerStatus.PAUSE

    def toggle(self):
        self.logger.info("toggle")

        if self.status == PlayerStatus.PLAY:
            self.pause()
        else:
            self.play()

    def skip(self):
        self.logger.info("skip")

        self.__opCurrentSong(ReportType.SKIP)

        self.__stop()
        self.__get_next_song()
        self.__play()
        
        return self.__current_song_info()

    def ban(self):
        self.logger.info("ban")

        self.__opCurrentSong(ReportType.BAN)

        self.__stop()
        self.__get_next_song()
        self.__play()
        
        return self.__current_song_info()

    def rate(self):
        self.logger.info("rate")

        self.__opCurrentSong(ReportType.RATE)
        
        return self.__current_song_info()

    def unrate(self):
        self.logger.info("unrate")

        self.__opCurrentSong(ReportType.UNRATE)
        
        return self.__current_song_info()

    def info(self):
        self.logger.info("info")
        
        return self.__current_song_info()

    def setch(self, ch):
        self.logger.info("setch %d" % ch)

        self.channel = ch

        self.current_song_index = -1
        del self.play_list[:]

        if self.status != PlayerStatus.STOP:
            self.__stop()

        self.__get_next_song()
        self.__play()
        
        return self.__current_song_info()

    def __current_song_info(self):
        
        if self.current_song_index in range(len(self.play_list)):
                        
            song = self.play_list[self.current_song_index]
                        
            return (u"Album: %s\nTitle: %s\nArtist: %s\nLike:%s\n" % (
                    song['albumtitle'], 
                    song['title'], 
                    song['artist'], 
                    song['like'],
                )
            ).encode('utf-8')
            
        return ""

    def __maintainPlayHistory(self, songId, op):

        self.play_history.append({
                'sid': songId,
                'type': op
            })

        if len(self.play_history) > 20:
            del self.play_history[0]

    def __opCurrentSong(self, op):

        if self.current_song_index in range(len(self.play_list)):

            songId = self.play_list[self.current_song_index]['sid']

            self.radioAPI.sendShortReport(
                    self.channel,
                    songId,
                    op
            )

            if op in [ReportType.END, ReportType.SKIP, ReportType.BAN]:
                self.__maintainPlayHistory(songId, op)
                
            if op in [ReportType.RATE, ReportType.UNRATE]:
                if op == ReportType.RATE:
                    self.play_list[self.current_song_index]['like'] = '1'
                else:
                    self.play_list[self.current_song_index]['like'] = '0'
