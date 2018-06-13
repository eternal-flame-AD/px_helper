import threading
import queue
import time
import random
import os
from http import client as httpconn
import config

prefix = config.download_prefix


def get_ready_to_write(path):
    os.makedirs(path, exist_ok=True)


def sanitize_name(fn):
    return fn.replace("?", "？").replace("..", "").replace("/", "")


def download_html(host, uri, sessid=None):
    if config.proxy == "http":
        conn = httpconn.HTTPSConnection(config.proxy_host, config.proxy_port)
        print(config.proxy_host, config.proxy_port)
        print(host, uri, sessid)
        conn.set_tunnel(host)
    elif config.proxy == None:
        conn = httpconn.HTTPSConnection(host)
    if not sessid:
        conn.request("GET", uri)
    else:
        conn.request("GET", uri, headers={"cookie": "PHPSESSID=" + sessid})
    return conn.getresponse().read()


class DownloadTask():
    def __init__(self, uri, fn, ref=""):
        self.uri = uri
        self.fn = fn
        self.ref = ref


class DownloadDispatcher():
    def __init__(self, count, host):
        self.taskqueue = queue.Queue()
        self.worker = []
        for _ in range(count):
            wkr = DownloadWorker(host)
            wkr_thread = threading.Thread(
                target=wkr.monitor, args=(self.taskqueue, ))
            wkr_thread.daemon = True
            wkr_thread.start()
            self.worker.append((wkr, wkr_thread))

    def join(self):
        self.taskqueue.join()

    def dispatch(self, img):
        fn = prefix + sanitize_name(img.info['author_nick']) + "/"
        if img.info['work_type'] == "manga":
            fn += sanitize_name(img.info['work_title']) + "/"
            fn += str(img.info['manga_seq']) + ".jpg"
        elif img.info['work_type'] == "illust":
            fn += sanitize_name(img.info['work_title']) + ".jpg"
        task = DownloadTask(
            img.url.replace("https://i.pximg.net", ""), fn,
            img.info['referer'])
        self.taskqueue.put(task)


class DownloadWorker():
    def __init__(self, host):
        if config.proxy == "http":
            self.conn = httpconn.HTTPSConnection(config.proxy_host,
                                                 config.proxy_port)
            self.conn.set_tunnel(host)
        elif config.proxy == None:
            self.conn = httpconn.HTTPSConnection(host)
        self.is_busy = False

    def monitor(self, queue):
        while True:
            self.is_busy = False
            task = queue.get()
            self.is_busy = True
            try:
                self.download(task.uri, task.fn, task.ref)
            finally:
                queue.task_done()

    def download(self, uri, fn, ref=""):
        get_ready_to_write(fn[:fn.rindex("/")])
        self.conn.request("GET", uri, headers={"Referer": ref})
        with open(fn, "wb") as f:
            resp = self.conn.getresponse()
            if resp.status != 200:
                print("Req failed:" + str(resp.status) + " " + uri)
            f.write(resp.read())
