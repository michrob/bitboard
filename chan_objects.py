import base64
import datetime
import hashlib
import json
import traceback

import bleach
from sortedcontainers import SortedListWithKey as sortedlist

import config

ID_LENGTH = 9


def getThreadId(subject):
    sha256 = hashlib.sha256()
    sha256.update(subject)
    threadId = sha256.hexdigest()
    return threadId


class ChanPost:
    def __init__(self, chan, jsonObj):
        self.chan = chan
        self.subject = bleach.clean(base64.decodestring(jsonObj['subject'])).encode('utf-8').strip()

        if self.subject.startswith("Re: "):
            self.subject = self.subject[4:]

        self.threadid = getThreadId(self.subject)

        self.msgid = bleach.clean(jsonObj['msgid'])
        self.postid = self.msgid[-ID_LENGTH:].upper()

        self.timestamp = int(jsonObj['receivedTime'])
        self.date = datetime.datetime.fromtimestamp(self.timestamp).strftime('%Y/%m/%d(%a)%H:%M:%S')

        self.toaddr = bleach.clean(jsonObj['toAddress'])
        self.fromaddr = bleach.clean(jsonObj['fromAddress'])

        self.username = "Anonymous"
        if self.toaddr != self.fromaddr:
            self.username = self.fromaddr[-ID_LENGTH:]

        self.image = None
        self.body = None

        # set of postId's this post references.
        self.targetposts = set([])

        message = base64.decodestring(jsonObj['message'])
        try:
            self.parseJsonBody(message)
        except Exception as e:
            if self.subject == "test subject":
                print "Exception parsing JSON: " + message + " Exception: " + `e`
            self.parsePlaintextBody(message)

        self.markup()

    def parseJsonBody(self, msgdata):
        try:
            message = json.loads(msgdata)
            if 'text' in message:
                self.body = bleach.clean(message['text'])
            if 'image' in message:
                self.image = base64.decodestring(message['image'])
        except Exception as e:
            raise Exception("parseJsonBody failed. " + `e`)

    def parsePlaintextBody(self, msgdata):
        if config.bm_integration:
            self.body = msgdata.split("\n" + 54 * "-")[0]
            if "data:image" in self.body:
                try:
                    self.image = bleach.clean(self.body.split(",")[1])
                    if "\"" in self.image:
                        self.image = self.image.split("\"")[0]
                    self.image = base64.decodestring(self.image)
                except Exception as e:
                    print "Exception decoding image: " + `e`
                    print self.image
                    traceback.print_exc()
                self.body = self.body.split("<img")[0]
            else:
                self.body = bleach.clean(self.body)

    def isPostidReply(self, text):
        if not text.startswith("&gt;&gt;"):
            return False

        targetpostid = text.split(" ")[0][8:]
        if not len(targetpostid) == ID_LENGTH:
            return False

        postid = 0
        try:
            postid = int(targetpostid, 16)
        except Exception as e:
            print "Not a post reply: " + text + " Exception: " + `e`
            traceback.print_exc()

        return postid != 0

    def markup(self):
        # add greentext
        if not self.body:
            return
        lines = self.body.split("\n")
        for line in range(0, len(lines)):
            if self.isPostidReply(lines[line]):
                targetpostid = lines[line].split(" ")[0][8:]
                self.targetposts.add(targetpostid)
                lines[line] = "<a class=\"underlined link\" href=\"#" + targetpostid + "\">" + lines[line] + "</a>"
            elif lines[line].startswith("&gt;"):
                lines[line] = "<span class=\"greentext\">" + lines[line] + "</span>"
        self.body = "\n".join(lines)


class ChanThread:
    def __init__(self, chan, subject):
        self.posts = sortedlist(key=lambda post: post.timestamp)
        # postid -> set(replies)
        self.repliesByPostId = {}
        self.subject = subject
        self.timestamp = 0
        self.threadid = getThreadId(subject)
        self.chan = chan

    def getPosts(self):
        return self.posts

    def deletePost(self, post):
        try:
            self.posts.remove(post)
        except Exception as e:
            print "Exception removing post: " + `e`
            traceback.print_exc()

    def addPost(self, post):
        self.posts.add(post)
        self.updatePostLinks(post)
        if post.timestamp > self.timestamp:
            self.timestamp = post.timestamp

    def updatePostLinks(self, post):
        for postId in post.targetposts:
            if postId not in self.repliesByPostId:
                self.repliesByPostId[postId] = set([])
            self.repliesByPostId[postId].add(post.postid)

    def getPostReplies(self, postid):
        if postid not in self.repliesByPostId:
            return set([])
        return self.repliesByPostId[postid]


class ChanBoard:
    def __init__(self, chan):
        self._threads = sortedlist(key=lambda thread: -thread.timestamp)
        self._threadsById = {}
        self.chan = chan

    def getThreadCount(self):
        return len(self._threadsById)

    def getThreads(self, start_index, end_index):
        return self._threads[start_index:end_index]

    def getThread(self, threadid):
        if threadid in self._threadsById:
            return self._threadsById[threadid]
        return None

    def deletePost(self, post):
        threadid = getThreadId(post.subject)
        thread = self.getThread(threadid)
        if thread:
            thread.deletePost(post)

    def deleteThread(self, threadid):
        if threadid in self._threadsById:
            thread = self._threadsById[threadid]
            self._threads.remove(thread)

    def addPost(self, post):
        threadid = getThreadId(post.subject)
        thread = self.getThread(threadid)

        if not thread:
            thread = ChanThread(self.chan, post.subject)
            self._threadsById[thread.threadid] = thread
        else:
            # Remove it because we need to
            # re-insert it in sorted order.
            self._threads.remove(thread)

        # print "Updating thread: " + `thread.subject`

        thread.addPost(post)
        self._threads.add(thread)
