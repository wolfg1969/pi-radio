# -*- coding: utf-8 -*-

import cjson
import logging
import pycurl
import cStringIO


APP_NAME        = "radio_desktop_win"
VERSION         = 100
LOGIN_API_URL   = "http://www.douban.com/j/app/login"
CHANNEL_API_URL = "http://www.douban.com/j/app/radio/channels"
RADIO_API_URL   = "http://www.douban.com/j/app/radio/people"


class ReportType:

    BAN     = 'b'   # 不再播放当前歌曲  [短报告]
    END     = 'e'   # 当前歌曲播放完毕，播放列表非空  [短报告]
    NEW     = 'n'   # 当前不在播放，播放列表为空 [长报告]
    PLAY    = 'p'   # 正在播放，播放列表为空，需要新的播放列表  [长报告]
    SKIP    = 's'   # 跳过当前播放的歌曲，播放列表非空  [短报告]
    RATE    = 'r'   # 为当前播放歌曲加红心    [短报告]
    UNRATE  = 'u'   # 取消当前歌曲的红心     [短报告]


class RadioAPI:

    def __init__(self, uid, uname, token, expire, kbps):
    
        self.logger = logging.getLogger('douban-pi-radio.api')

        self.uid = uid
        self.uname = uname
        self.token = token
        self.expire = expire
        self.kbps = kbps

        self.curl = pycurl.Curl()
        self.curl.setopt(pycurl.USERAGENT,
            'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:8.0) Gecko/20100101 Firefox/8.0')
        self.curl.setopt(pycurl.ENCODING, "utf-8")
        self.curl.setopt(pycurl.CONNECTTIMEOUT, 30)
        self.curl.setopt(pycurl.TIMEOUT, 30)
        self.curl.setopt(pycurl.VERBOSE, True)

    def sendLongReport(self, channel, songId, reportType, playHistory):

        buf = cStringIO.StringIO()

        url = "%s?app_name=%s&version=%s&user_id=%d&expire=%d&token=%s&channel=%d&sid=%s&type=%c&h=%s&kbps=%s" % (
            RADIO_API_URL,
            APP_NAME,
            VERSION,
            self.uid,
            self.expire,
            self.token,
            channel,
            songId,
            reportType,
            self.__populateHistory(playHistory),
            self.kbps,
        )
        
        self.logger.debug("api request url is %s" % url)

        self.curl.setopt(pycurl.URL, url)
        self.curl.setopt(pycurl.WRITEFUNCTION, buf.write)
        self.curl.perform()

        json_str = buf.getvalue().decode('utf8')
        self.logger.debug("return json_str is %s" % json_str)
        
        json_obj = cjson.decode(json_str)
        self.logger.info("sendLongReport.ret=%s" % json_obj['r'])

        buf.close()

        if json_obj['r'] == 0:
            return json_obj['song']
        else:
            return []

    def sendShortReport(self, channel, songId, reportType):

        url = "%s?app_name=%s&version=%s&user_id=%d&expire=%d&token=%s&channel=%d&sid=%s&type=%c" % (
            RADIO_API_URL,
            APP_NAME,
            VERSION,
            self.uid,
            self.expire,
            self.token,
            channel,
            songId,
            reportType,
        )
        
        self.logger.debug("api request url is %s" % url)

        buf = cStringIO.StringIO()

        self.curl.setopt(pycurl.URL, url)
        self.curl.setopt(pycurl.WRITEFUNCTION, buf.write)
        self.curl.perform()

        json_str = buf.getvalue().decode('utf8')
        self.logger.debug("return json_str is %s" % json_str) 
        
        buf.close()
        
    def __populateHistory(self, hisList):

        ret = []
        for his in hisList:
            ret.append("|%s:%s" % (his['sid'], his['type']))

        return "".join(ret)
