import bs4
import time
import threading
import json
import re
import downloader
from pxelem import PixlvUrl, PixlvImage, PixlvAuthors
import queue
import sys
import argparse
import codecs
import imgfilter
import config
from login import login

url_queue = queue.Queue()


class PixlvParserResult():
    def __init__(self):
        self.urls = []
        self.imgs = []

    def add_img(self, img, info={}):
        self.imgs.append(PixlvImage(img, info=info))

    def add_url(self, url, base=None, info={}):
        newurl = PixlvUrl(url, base=base, info=info)
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


class PixlvParser():
    def __init__(self, url):
        if type(url) == str:
            url = PixlvUrl(url)
        self.url = url
        self.content = self.url.toBs4()

    def img_from_member_illust_manga(self):

        if self.url.info:
            res = PixlvParserResult()
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
            res = PixlvParserResult()
            res.add_url(self.url.geturl().replace("mode=manga", "mode=medium"))
        return res

    def img_from_member_illust_medium(self):
        def get_info(json_data):
            res = {}
            if json_data['pageCount'] > 1:
                res['work_type'] = "manga"
            else:
                res['work_type'] = "illust"
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
            res = {**res, **PixlvAuthors().query(res['author_id'])}
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

        def one_pic_work(info):
            res = PixlvParserResult()
            res.add_img(info['cover_url'], info=info)
            return res

        def mult_pic_work(info):
            res = PixlvParserResult()
            res.add_img(info['cover_url'], info={**info, "manga_seq": "cover"})
            res.add_url(
                self.url.geturl().replace("mode=medium", "mode=manga"),
                info=info)
            return res

        json_data = re.search(r"(?<=\()\{token:.*\}(?=\);)",
                              self.content.prettify()).group(0)
        json_data, _ = re.subn(r"(\{\s*|,\s*)(\w+):", r'\1"\2":', json_data)
        json_data, _ = re.subn(r",\s*\}", r'}', json_data)
        json_data = json.loads(json_data)['preload']['illust'][
            self.url.getquerydict()['illust_id'][0]]
        info = get_info(json_data)
        if info['work_type'] == "manga":
            return mult_pic_work(info)
        else:
            return one_pic_work(info)

    def img_from_member_illust_no_p(self):
        res = PixlvParserResult()
        res.add_url(
            self.url.geturl() +
            ("?" if not self.url.getquerydict() else "&") + "p=1",
            base=self.url.geturl())
        return res

    def img_from_member_illust(self):
        res = PixlvParserResult()
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
        res = PixlvParserResult()
        search_data = self.content.find(
            "input", id="js-mount-point-search-result-list")['data-items']
        search_result = eval(
            eval("u'" + search_data + "'").replace("\/", "/").replace(
                ":true", ":True").replace(":false", ":False")
        )  # evaluate unicode string & replace true/false for True/False
        for work in search_result:
            res.add_url(
                "https://www.pixiv.net/member_illust.php?mode=medium&illust_id="
                + work['illustId'])
        p = int(self.url.getquerydict()['p'][0])
        res.add_url(
            self.url.geturl().replace("p=" + str(p), "p=" + str(p + 1)),
            base=self.url.geturl())
        return res

    def parse(self):
        loc = self.url.geturi()
        if not imgfilter.filter_url(self.url):
            # filter url
            return PixlvParserResult()
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
        else:
            raise NotImplementedError


class PixlvMTWorker():
    def __init__(self, urlqueue, getimgcallback):
        self.worker = threading.Thread(
            target=PixlvMTWorker.work,
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
                res = PixlvParser(newurl).parse()
                getimgcallback(res.imgs)
            finally:
                url_queue.task_done()
        
        self.idle = True


class PixlvMTMain():
    def __init__(self, num):
        self.num = num
        self.infooutput = codecs.open(
            "output-info.txt", mode="w", encoding="utf-8")
        self.workers = []
        self.urlqueue = url_queue
        self.writeLock = threading.Lock()
        self.downloader = downloader.DownloadDispatcher(
            config.down_thread, "i.pximg.net")
        for _ in range(num):
            self.workers.append(PixlvMTWorker(self.urlqueue, self.getimg))

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


def parse_pixlv(url):
    PixlvMTMain(config.crawl_thread).start(url)


def main():
    parser = argparse.ArgumentParser(description="Pixlv downloader")
    parser.add_argument(
        "url",
        type=str,
        help="Pixlv URL, either bookmark, member_illust or illust")
    parser.add_argument("-u", dest="username", help="username", type=str)
    parser.add_argument("-p", dest="password", help="password", type=str)
    parser.add_argument("-s", dest="sess_id", help="sessid", type=str)
    parser.add_argument(
        "--proxy",
        dest="proxy",
        help="specify a http proxy (format: http://127.0.0.1:8080)")
    args = parser.parse_args()
    if args.proxy:
        proxy_url = PixlvUrl(args.proxy, use_sessid=False, use_english=False)
        scheme = proxy_url.getscheme()
        if scheme == "http":
            config.proxy = "http"
            config.proxy_host = proxy_url.gethost()
            config.proxy_port = proxy_url.getport()
        else:
            raise NotImplementedError("Unsupported proxy")
    else:
        config.proxy = None
    if args.sess_id:
        config.sess_id = args.sess_id
    elif (args.username) and (args.password):
        config.sess_id = login(args.username, args.password)
    else:
        raise ValueError("Provide credentials please")
    parse_pixlv(args.url)


if __name__ == "__main__":
    main()
