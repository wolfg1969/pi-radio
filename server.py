# -*- coding: utf-8 -*-

import logging
import os
import signal
import socket
import sys
import subprocess
import thread
import threading
import time
import SocketServer

from daemon import Daemon
from player import Player

logging.basicConfig(filename="/tmp/douban-fmd.log", level=logging.DEBUG)

server_logger = logging.getLogger('douban-fmd.server')

music_pipe_r,music_pipe_w = os.pipe()
fm_process = None
play_stereo = True
with open(os.devnull, "w") as dev_null:
    fm_process = subprocess.Popen(["sudo", "/home/pi/piFm/new/pifm","-","76.6","44100", ], stdin=music_pipe_r, stdout=dev_null)

class CmdHandler(SocketServer.StreamRequestHandler):

    def handle(self):
        # self.request is the TCP socket connected to the client
        self.data = self.rfile.readline().strip()

        server_logger.debug("cmd=%s" % self.data)

        if not self.data:
            return

        cmd = self.data.split()
        arg = None

        if len(cmd) == 2:
            arg = cmd[1]

        cmd = cmd[0]

        if cmd == "play":

            self.request.sendall(self.server.player.play())

        elif cmd == "stop":

            self.server.player.stop()

        elif cmd == "pause":

            self.request.sendall(self.server.player.pause())

        elif cmd == "toggle":

            self.request.sendall(self.server.player.toggle())

        elif cmd == "skip":

            self.request.sendall(self.server.player.skip())

        elif cmd == "ban":

            self.request.sendall(self.server.player.ban())


        elif cmd == "rate":

            self.request.sendall(self.server.player.rate())

        elif cmd == "unrate":

            self.request.sendall(self.server.player.unrate())

        elif cmd == "info":

            self.request.sendall(self.server.player.info())

        elif cmd == "setch":

            if arg:
                self.request.sendall(self.server.player.setch(int(arg)))

            else:
                self.request.sendall("invalid channel id")

        #elif cmd == "end":
        #    self.server.player.stop()
        #    self.server.player.close()
        #    self.server.running = False
            
        else:
            server_logger.info("invalid command")


class PlayerSocketServer(SocketServer.TCPServer):
    address_family = socket.AF_INET
    allow_reuse_address = True


def init_player_server():

    import ConfigParser, os

    config = ConfigParser.ConfigParser()
    config.readfp(open(os.path.expanduser("~/.fmd/fmd.conf")))

    player = Player(
        long(config.get("DoubanFM", "uid")),
        config.get("DoubanFM", "uname"),
        config.get("DoubanFM", "token"),
        long(config.get("DoubanFM", "expire")),
        music_pipe_w
    )
    player.play()

    signal.signal(signal.SIGUSR1, player.playNextSong)

    HOST, PORT = "localhost", 8888

    # Create the server, binding to localhost on port 8888
    server = PlayerSocketServer((HOST, PORT), CmdHandler)
    server.player = player

    # Activate the server; this will keep running until you
    # interrupt the program with Ctrl-C
    #server.serve_forever()

    server.running = True

    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.start()

    while server.running:
        time.sleep(1)
    
    server_thread.join()



class ServerDaemon(Daemon):

    def run(self):
        init_player_server()



if __name__ == "__main__":

    daemon = ServerDaemon("/tmp/douban-fmd.pid")
    daemon.start()







