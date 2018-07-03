import gevent.monkey
gevent.monkey.patch_all()

import bs4
import time
import threading
import json
import re
import queue
import sys
import argparse
import codecs

from . import imgfilter
from . import downloader
from .pxelem import PixivUrl, PixivImage, PixivAuthors
from . import config
from .login import login

url_queue = queue.Queue()


class PixivParserResult():
    def __init__(self):
        self.urls = []
        self.imgs = []

    def add_img(self, img, info={}):
        self.imgs.append(PixivImage(img, info=info))

    def add_url(self, url, base=None, info={}):
        newurl = PixivUrl(url, base=base, info=info)
        self.urls.append(newurl)
        url_queue.put(newurl)

    def __str__(self):
        urls = []
        for url in self.urls:
            urls.append(url.geturl())
        imgs = []
        for img in self.imgs:
            imgs.append(str(img))
        return str(urls) + '\r\n' + str(imgs)


class PixivParser():
    def __init__(self, url):
        if type(url) == str:
            url = PixivUrl(url)
        self.url = url
        self.content = self.url.toBs4()

    def img_from_member_illust_manga(self):

        if self.url.info:
            res = PixivParserResult()
            for seq in range(self.url.info['work_imgcount']):
                res.add_img(
                    re.search(r'(?<=pixiv\.context\.images\[' +
                              str(seq) + r'\]\s=\s")(.*?)(?=")',
                              self.content.prettify()).group(0).replace(
                                  r"\/", "/"),
                    info={
                        **self.url.info, "manga_seq": seq + 1
                    })
        else:
            res = PixivParserResult()
            res.add_url(self.url.geturl().replace("mode=manga", "mode=medium"))
        return res

    def img_from_member_illust_medium(self):
        def get_info(json_data):
            res = {}
            if json_data['illustType'] < 2:
                if json_data['pageCount'] == 1:
                    res['work_type'] = "illust"
                else:
                    res['work_type'] = "manga"
            else:
                res['work_type'] = "ugoira"
            res['work_imgcount'] = json_data['pageCount']
            res['work_title'] = json_data['illustTitle']
            res['work_subtitle'] = json_data['illustComment']
            res['work_time'] = json_data['createDate']
            res['work_id'] = json_data['illustId']
            res['work_resolution'] = "x".join((str(json_data['width']),
                                               str(json_data['height'])))
            res['height'] = json_data['height']
            res['width'] = json_data['width']
            res['author_id'] = json_data['userId']
            res = {**res, **PixivAuthors().query(res['author_id'])}
            res['view-count'] = json_data['viewCount']
            res['like-count'] = json_data['likeCount']
            res['bookmark-count'] = json_data['bookmarkCount']
            res['bookmarked'] = bool(json_data['bookmarkData'])
            res['cover_url'] = json_data['urls']['original']
            res['referer'] = self.url.geturl()

            res['tags'] = []
            for tag in json_data['tags']['tags']:
                res['tags'].append(tag["tag"])

            return res

        def illust_work(info):
            res = PixivParserResult()
            res.add_img(info['cover_url'], info=info)
            return res

        def manga_work(info):
            res = PixivParserResult()
            res.add_img(info['cover_url'], info={**info, "manga_seq": "cover"})
            res.add_url(
                self.url.geturl().replace("mode=medium", "mode=manga"),
                info=info)
            return res

        def ugoira_work(info):
            url = PixivUrl(
                "https://www.pixiv.net/ajax/illust/{}/ugoira_meta".format(
                    info['work_id']))
            res = PixivParserResult()
            ugoira_def = url.toJsonDict()['body']
            res.add_img(ugoira_def['originalSrc'], info={**info,"frames":ugoira_def['frames']})
            return res

        json_data = re.search(r"(?<=\()\{token:.*\}(?=\);)",
                              self.content.prettify()).group(0)
        json_data, _ = re.subn(r"(\{\s*|,\s*)(\w+):", r'\1"\2":', json_data)
        json_data, _ = re.subn(r",\s*\}", r'}', json_data)
        json_data = json.loads(json_data)['preload']['illust'][
            self.url.getquerydict()['illust_id'][0]]
        info = get_info(json_data)
        if info['work_type'] == "manga":
            return manga_work(info)
        elif info['work_type'] == "illust":
            return illust_work(info)
        elif info['work_type'] == "ugoira":
            return ugoira_work(info)

    def img_from_member_illust_no_p(self):
        res = PixivParserResult()
        res.add_url(
            self.url.geturl() +
            ("?" if not self.url.getquerydict() else "&") + "p=1",
            base=self.url.geturl())
        return res

    def img_from_member_illust(self):
        res = PixivParserResult()
        works = self.content.find_all("li", class_="image-item")
        if len(works) != 0:
            for work in works:
                res.add_url(
                    work.find("a", class_="work")['href'],
                    base=self.url.geturl())
            p = int(self.url.getquerydict()['p'][0])
            res.add_url(
                self.url.geturl().replace("p=" + str(p), "p=" + str(p + 1)),
                base=self.url.geturl())
        return res

    def img_from_bookmark_list_no_p(self):
        return self.img_from_member_illust_no_p()

    def img_from_bookmark_list(self):
        return self.img_from_member_illust()

    def img_from_search_no_p(self):
        return self.img_from_member_illust_no_p()

    def img_from_search(self):
        res = PixivParserResult()
        search_data = self.content.find(
            "input", id="js-mount-point-search-result-list")['data-items']
        search_result = json.loads(search_data)
        for work in search_result:
            res.add_url(
                "https://www.pixiv.net/member_illust.php?mode=medium&illust_id="
                + work['illustId'])
        p = int(self.url.getquerydict()['p'][0])
        res.add_url(
            self.url.geturl().replace("p=" + str(p), "p=" + str(p + 1)),
            base=self.url.geturl())
        return res

    def img_from_showcase_article(self):
        article_id = re.search(r"/a/(\d+)/", self.url.geturi()).group(1)
        article_api_uri = "https://www.pixiv.net/ajax/showcase/article?article_id={}".format(
            article_id)
        article_api_response = PixivUrl(article_api_uri).toJsonDict()
        result = PixivParserResult()
        for illust in article_api_response['body'][0]['illusts']:
            result.add_url(
                "https://www.pixiv.net/member_illust.php?mode=medium&illust_id="
                + str(illust['illust_id']))
        return result

    def parse(self):
        loc = self.url.geturi()
        if not imgfilter.filter_url(self.url):
            # filter url
            return PixivParserResult()
        if loc.startswith("/member_illust.php"):
            query = self.url.getquerydict()
            mode = query['mode'][0] if "mode" in query else None
            if mode == "medium":
                return self.img_from_member_illust_medium()
            elif mode == "manga":
                return self.img_from_member_illust_manga()
            elif "id" in query:
                if "p" in query:
                    return self.img_from_member_illust()
                else:
                    return self.img_from_member_illust_no_p()
            else:
                raise ValueError
        elif loc.startswith("/bookmark.php"):
            query = self.url.getquerydict()
            if "p" in query:
                return self.img_from_bookmark_list()
            else:
                return self.img_from_bookmark_list_no_p()
        elif loc.startswith("/search.php"):
            query = self.url.getquerydict()
            if "p" in query:
                return self.img_from_search()
            else:
                return self.img_from_search_no_p()
        elif loc.startswith("/showcase/a"):
            return self.img_from_showcase_article()
        else:
            raise NotImplementedError


class PixivMTWorker():
    def __init__(self, urlqueue, getimgcallback):
        self.worker = threading.Thread(
            target=PixivMTWorker.work,
            group=None,
            args=(self, urlqueue, getimgcallback))
        self.worker.daemon = True
        self.completed = False
        self.worker.start()
        self.idle = False

    def work(self, urlqueue, getimgcallback):
        while True:

            while True:
                if self.completed:
                    break
                try:
                    newurl = urlqueue.get(timeout=4)
                    break
                except:
                    self.idle = True
            if self.completed:
                break

            self.idle = False

            try:
                res = PixivParser(newurl).parse()
                getimgcallback(res.imgs)
            finally:
                url_queue.task_done()

        self.idle = True


class PixivMTMain():
    def __init__(self, num):
        self.num = num
        self.infooutput = codecs.open(
            "./output-info.txt", mode="w", encoding="utf-8")
        self.workers = []
        self.urlqueue = url_queue
        self.writeLock = threading.Lock()
        self.downloader = downloader.DownloadDispatcher(
            config.down_thread, "i.pximg.net")
        for _ in range(num):
            self.workers.append(PixivMTWorker(self.urlqueue, self.getimg))

    def start(self, url):
        self.urlqueue.put(url)
        self.urlqueue.join()
        self.downloader.join()
        self.close()

    def getimg(self, imgs):
        self.writeLock.acquire()
        for img in imgs:
            if not imgfilter.filter(img):
                continue
            self.downloader.dispatch(img)
            self.infooutput.write(str(img))
            self.infooutput.write("\n")
        self.writeLock.release()

    def close(self):
        for wkr in self.workers:
            wkr.completed = True
        for wkr in self.workers:
            wkr.worker.join()
        self.infooutput.close()


def parse_pixiv(url):
    PixivMTMain(config.crawl_thread).start(url)