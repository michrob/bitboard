import base64
import json
import logging as log
import sys
import time
import traceback
import xmlrpclib
from threading import Thread

from sortedcontainers import SortedListWithKey as sortedlist

import config
from chan_objects import ChanBoard
from chan_objects import ChanPost


def getBitmessageEndpoint():
    username = config.getBMConfig("apiusername")
    password = config.getBMConfig("apipassword")
    host = config.getBMConfig("apiinterface")
    port = config.getBMConfig("apiport")
    return "http://"+username+":"+password+"@"+host+":"+port+"/"


class BitMessageGateway(Thread):
    def __init__(self):
        super(BitMessageGateway, self).__init__()
        self._postsById = {}
        self._boardByChan = {}
        self._chanDict = {}
        self._killed = False
        self._refresh = True
        self._api = xmlrpclib.ServerProxy(getBitmessageEndpoint())

    def run(self):
        while not self._killed:
            try:
                print "Updating bitmessage info."
                self.updateChans()
                self.updateChanThreads()

                print `len(self._postsById)` + " total messages " + `len(self._chanDict)` + " total chans."

                for i in range(0, config.bm_refresh_interval):
                    time.sleep(i)
                    if self._killed:
                        sys.exit(0)
                    if self._refresh:
                        self._refresh = False
                        break
            except Exception as e:
                log.error("Exception in gateway thread: " + `e`)
                time.sleep(config.bm_refresh_interval)
                
    def getChans(self):
        return self._chanDict

    def deleteMessage(self, chan, messageid):
        try:
            board = self._boardByChan[chan]
            post = self._postsById[messageid]
            board.deletePost(post)
            del self._postsById[messageid]
        except Exception as e:
            print "Exception deleting post: " + `e`
            traceback.print_exc()
        return self._api.trashMessage(messageid)

    def deleteThread(self, chan, threadid):
        try:
            board = self._boardByChan[chan]
            thread = board.getThread(threadid)
            if thread:
                threadposts = thread.getPosts()
                for post in threadposts:
                    self.deleteMessage(chan, post.msgid)
            board.deleteThread(threadid)
        except Exception as e:
            print "Exception deleting thread: " + repr(e)
            traceback.print_exc()
        return "Thread [" + repr(threadid) + "] deleted."

    def updateChans(self):
        chans = {}
        try:
            straddr = self._api.listAddresses()
            addresses = json.loads(straddr)['addresses']
            for jaddr in addresses:
                if jaddr['chan'] and jaddr['enabled']:
                    chan_name = jaddr['label']
                    chans[chan_name] = jaddr['address']
        except Exception as e:
            log.error("Exception getting channels: " + `e`)
            traceback.print_exc()

        self._chanDict = dict(self._chanDict.items() + chans.items())

    def getChanName(self, chan):
        for label, addr in self._chanDict.iteritems():
            if addr == chan:
                return label

    def getImage(self, imageid):
        return self._postsById[imageid].image

    def updateChanThreads(self):
        strmessages = self._api.getAllInboxMessageIDs()
        messages = json.loads(strmessages)['inboxMessageIds']
        for message in messages:
            messageid = message["msgid"]

            if messageid in self._postsById:
                continue

            strmessage = self._api.getInboxMessageByID(messageid)
            jsonmessages = json.loads(strmessage)['inboxMessage']

            if len(jsonmessages) <= 0:
                continue

            chan = jsonmessages[0]['toAddress']
            post = ChanPost(chan, jsonmessages[0])

            if chan not in self._boardByChan:
                self._boardByChan[chan] = ChanBoard(chan)

            self._postsById[messageid] = post
            chanboard = self._boardByChan[chan]
            chanboard.addPost(post)

    def getThreadCount(self, chan):
        if chan not in self._boardByChan:
            return 0
        return self._boardByChan[chan].getThreadCount()

    def getChanThreads(self, chan, page=1):
        if chan not in self._boardByChan:
            return []
        board = self._boardByChan[chan]

        thread_start = int((int(page) - 1) * config.threads_per_page)
        thread_end = int(int(page) * config.threads_per_page)

        return board.getThreads(thread_start, thread_end)

    def getChanThread(self, chan, thread_id):
        if chan not in self._boardByChan:
            return None

        board = self._boardByChan[chan]

        return board.getThread(thread_id)

    def submitPost(self, chan, subject, body, image):
        subject = subject.encode('utf-8').strip()
        subjectdata = base64.b64encode(subject)

        print body

        msgdata = body.encode('utf-8').strip()

        if image:
            imagedata = base64.b64encode(image)
            msgdata += "\n\n<img src=\"data:image/jpg;base64," + imagedata + "\">"

        print msgdata

        msg = base64.b64encode(msgdata)

        self._refresh = True
        return self._api.sendMessage(chan, chan, subjectdata, msg)

    def joinChan(self, passphrase):
        self._refresh = True

        try:
            result = self._api.createChan(base64.b64encode(passphrase))
        except Exception as e:
            result = repr(e)

        return result

    def getAPIStatus(self):
        try:
            result = self._api.add(2, 2)
        except Exception as e:
            return repr(e)
        if result == 4:
            return True
        return result

gateway_instance = BitMessageGateway()
gateway_instance.start()
