import logging
import time


class RadioPlayer(object):
    
    def __init__(self, config, audio_pipe):
        self.logger = logging.getLogger('pi-radio.player')
        self.config = config
        self.audio_pipe = audio_pipe
        
    def play_next(self):
        pass
        
    def play(self):
        self.logger.info("play")
        while (True):  # TODO play forever now
            self.play_next()
            time.sleep(1)
