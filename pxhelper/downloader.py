import gevent.monkey

gevent.monkey.patch_all()

import queue
import hashlib
import time
import random
import gevent.pool
import os
from http import client as httpconn

from . import config

from . import remuxer


def get_ready_to_write(path):
    os.makedirs(path, exist_ok=True)


def sanitize_name(fn):
    return fn.replace("?", "？").replace("..", "").replace("/", "").replace(
        "\\", "").replace("|", "").replace("*", "").replace(":", "：").replace(
            '"', "“").replace("<", "").replace(">", "")


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
    def __init__(self, uri, fn, ref="", finishcallback=None):
        self.uri = uri
        self.fn = fn
        self.ref = ref
        self.finishcallback = finishcallback


class DownloadDispatcher():
    def __init__(self, count, host):
        self.taskqueue = queue.Queue()
        self.pool = gevent.pool.Pool(count)
        for _ in range(count):
            wkr = DownloadWorker(host)
            self.pool.apply_async(wkr.monitor, args=(self.taskqueue, ))

    def join(self):
        self.taskqueue.join()

    def dispatch(self, img):
        ext = img.url[img.url.rindex("."):]
        fn = config.download_prefix + "/" + sanitize_name(
            img.info['author_nick']) + "/"
        if img.info['work_type'] == "illust":
            fn += sanitize_name(img.info['work_title']) + ext
        elif img.info['work_type'] == "manga":
            fn += sanitize_name(img.info['work_title']) + "/"
            fn += str(img.info['manga_seq']) + ext
        else:
            fn += sanitize_name(img.info['work_title']) + "/" + sanitize_name(
                img.info['work_title']) + ext
        task = DownloadTask(
            img.url.replace("https://i.pximg.net", ""),
            fn,
            img.info['referer'],
            finishcallback=remuxer.UgoiraRemuxer(
                fn, img.info['frames'], img.info['work_resolution']).remux
            if (img.info['work_type'] == "ugoira" and config.remux_ugoira) else
            None)
        self.taskqueue.put((task, config.down_retry_count))


class DownloadWorker():
    def __init__(self, host):
        self.host = host
        self.reset_connnection()
        self.is_busy = False

    def reset_connnection(self):
        if config.proxy == "http":
            self.conn = httpconn.HTTPSConnection(config.proxy_host,
                                                 config.proxy_port)
            self.conn.set_tunnel(self.host)
        elif config.proxy == None:
            self.conn = httpconn.HTTPSConnection(self.host)

    def monitor(self, queue):
        while True:
            self.is_busy = False
            task, retry_count = queue.get()
            self.is_busy = True
            try:
                if os.path.exists(task.fn) and os.path.getsize(task.fn) > 1024:
                    print("Skipped:", task.fn)
                elif retry_count == 0:
                    print(
                        "Failed to download", task.fn,
                        ". Giving up. Maybe you should set a lower down_thread."
                    )
                else:
                    print("Download:", task.fn)
                    self.download(task.uri, task.fn, task.ref)
                    if task.finishcallback:
                        task.finishcallback()
            except OSError as e:
                print("Failed to create file", task.fn,
                      ". Remaining attempts:", retry_count)
                print(e)
                m = hashlib.md5()
                m.update(task.fn[task.fn.rindex("/") + 1:].encode("utf-8-sig"))
                task.fn = task.fn[:task.fn.rindex("/") + 1] + m.hexdigest()
                queue.put((task, retry_count - 1))
            except Exception as e:
                print("Failed to download", task.fn, ". Remaining attempts:",
                      retry_count)
                print(e)
                self.reset_connnection()
                queue.put((task, retry_count - 1))
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
