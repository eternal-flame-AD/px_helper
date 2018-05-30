import bs4
import time
import threading
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
        def get_info(content):
            res = {}
            res['work_type'] = "manga"
            res['work_title'] = content.find("title").get_text()
            profile_module = content.find("footer").find(
                "div", class_="profile-module").find("div")
            res['work_id'] = profile_module['data-illust-id']
            res['author_id'] = profile_module['data-user-id']
            res['referer'] = self.url.geturl()
            res = {**res, **PixlvAuthors().query(res['author_id'])}
            return res

        res = PixlvParserResult()
        seq = 0
        for img in self.content.find_all(
                "img", attrs={"data-filter": "manga-image"}):
            seq += 1
            res.add_img(
                img['data-src'],
                info={
                    **self.url.info,
                    **get_info(self.content), "manga_seq": seq
                })
        return res

    def img_from_member_illust_medium(self):
        def get_info(content, url):
            def find_tag(content):
                res = []
                tags = content.find_all(
                    "a",
                    attrs={
                        "data-click-category":
                        "illust-tag-on-member-illust-medium"
                    })
                if not tags:
                    return []
                for tag in tags:
                    res.append(tag.get_text())
                return res

            res = {}
            res['work_type'] = "illust"
            res['work_title'] = content.find(
                "section", class_="work-info").find(
                    "h1", class_="title").get_text()
            try:
                res['work_subtitle'] = content.find(
                    "section", class_="work-info").find(
                        "p", class_="caption").get_text()
            except AttributeError:
                res['work_subtitle'] = ""
            work_meta = content.find(
                "section", class_="work-info").find(
                    "ul", class_="meta").find_all("li")
            res['work_time'] = work_meta[0].get_text()
            res['work_resolution'] = work_meta[1].get_text()
            res['work_id'] = url.getquerydict()['illust_id'][0]
            res['author_id'] = content.find(
                "div", attrs={"data-click-label": "follow"})['data-user-id']
            res['tags'] = find_tag(content)
            res['view-count'] = content.find(
                "dd", class_="view-count").get_text()
            res['rated-count'] = content.find(
                "dd", class_="rated-count").get_text()
            if content.find(class_="bookmarked"):
                res['bookmarked'] = True
            else:
                res['bookmarked'] = False
            res['referer'] = self.url.geturl()
            res = {**res, **PixlvAuthors().query(res['author_id'])}
            return res

        def one_pic_work(content, info={}):
            res = PixlvParserResult()
            res.add_img(
                content.find("div",
                             class_="_illust_modal").find("img")['data-src'],
                info=info)
            return res

        def mult_pic_work(work, info={}):
            nexturi = work.find("a", class_="_work")['href']
            res = PixlvParserResult()
            res.add_url(nexturi, base=self.url.geturl(), info=info)
            return res

        work = self.content.find(class_="works_display")
        if work.find(class_="multiple"):
            return mult_pic_work(work, info=get_info(self.content, self.url))
        else:
            return one_pic_work(
                self.content, info=get_info(self.content, self.url))

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
            res = PixlvParser(newurl).parse()
            getimgcallback(res.imgs)
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
        comp = False
        while (not self.urlqueue.empty()) or (not comp) or (
                self.downloader.check_busy()):
            comp = True
            for wkr in self.workers:
                if not wkr.idle:
                    comp = False
            time.sleep(1)
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
    parser.add_argument("--proxy", dest="proxy", help="specify a http proxy (format: http://127.0.0.1:8080)")
    args = parser.parse_args()
    if args.proxy:
        proxy_url=PixlvUrl(args.proxy, use_sessid=False, use_english=False)
        scheme=proxy_url.getscheme()
        if scheme=="http":
            config.proxy="http"
            config.proxy_host=proxy_url.gethost()
            config.proxy_port=proxy_url.getport()
        else:
            raise NotImplementedError("Unsupported proxy")
    else:
        config.proxy=None
    if args.sess_id:
        config.sess_id = args.sess_id
    elif (args.username) and (args.password):
        config.sess_id = login(args.username, args.password)
    else:
        raise ValueError("Provide credentials please")
    parse_pixlv(args.url)


if __name__ == "__main__":
    main()
