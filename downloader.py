import threading
import time
import random
import os
from http import client as httpconn
import config

prefix = config.download_prefix


def get_ready_to_write(path):
    os.makedirs(path, exist_ok=True)

def sanitize_name(fn):
    return fn.replace("?","？").replace("..","").replace("/","")

def download_html(host, uri, sessid=None):
    conn = httpconn.HTTPSConnection(host)
    if not sessid:
        conn.request("GET", uri)
    else:
        conn.request("GET", uri, headers={"cookie": "PHPSESSID=" + sessid})
    return conn.getresponse().read()


class DownloadDispatcher():
    def __init__(self, count, host):
        self.worker = []
        for _ in range(count):
            self.worker.append(DownloadWorker(host))

    def get_worker(self):
        while True:
            for worker in self.worker:
                if not worker.is_busy:
                    return worker
            time.sleep(1)

    def dispatch(self, img):
        fn = prefix + sanitize_name(img.info['author_nick']) + "/"
        if img.info['work_type'] == "manga":
            fn += sanitize_name(img.info['work_title']) + "/"
            fn += str(img.info['manga_seq']) + ".jpg"
        elif img.info['work_type'] == "illust":
            fn += sanitize_name(img.info['work_title']) + ".jpg"
        threading.Thread(
            target=self.get_worker().download,
            args=(img.url.replace("https://i.pximg.net", ""), fn,
                  img.info['referer'])).start()


class DownloadWorker():
    def __init__(self, host):
        self.conn = httpconn.HTTPSConnection(host)
        self.is_busy = False

    def download(self, uri, fn, ref=""):
        self.is_busy = True
        get_ready_to_write(fn[:fn.rindex("/")])
        self.conn.request("GET", uri, headers={"Referer": ref})
        with open(fn, "wb") as f:
            resp = self.conn.getresponse()
            if resp.status != 200:
                print("Req failed:" + str(resp.status) + " " + uri)
            f.write(resp.read())
        self.is_busy = False
