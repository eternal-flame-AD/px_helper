import bs4
import time
import threading
import downloader
from pxelem import PixlvUrl, PixlvImage, PixlvAuthors
import queue
import sys
import argparse
import codecs
import imgfilter
import config
from login import login


class PixlvParserResult():
    def __init__(self):
        self.urls = []
        self.imgs = []

    def add_img(self, img, info={}):
        self.imgs.append(PixlvImage(img, info=info))

    def add_url(self, url, base=None, info={}):
        self.urls.append(PixlvUrl(url, base=base, info=info))

    def merge(self, res2):
        self.urls = [*self.urls, *res2.urls]
        self.imgs = [*self.imgs, *res2.urls]

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

    def parse(self):
        loc = self.url.geturi()
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
        else:
            raise NotImplementedError


class PixlvMTWorker():
    def __init__(self, urlqueue, getimgcallback):
        self.worker = threading.Thread(
            target=PixlvMTWorker.work,
            group=None,
            args=(self, urlqueue, getimgcallback))
        self.worker.daemon = True
        self.worker.start()
        self.idle = False

    def work(self, urlqueue, getimgcallback):
        while True:
            self.idle = False
            try:
                newurl = urlqueue.get(timeout=8)
            except:
                self.idle = True
                newurl = urlqueue.get()
            res = PixlvParser(newurl).parse()
            getimgcallback(res.imgs)
            for url in res.urls:
                urlqueue.put(url)


class PixlvMTMain():
    def __init__(self, num):
        self.num = num
        self.infooutput = codecs.open(
            "output-info.txt", mode="w", encoding="utf-8")
        self.workers = []
        self.urlqueue = queue.Queue()
        self.writeLock = threading.Lock()
        self.downloader = downloader.DownloadDispatcher(
            config.down_thread, "i.pximg.net")
        for _ in range(num):
            self.workers.append(PixlvMTWorker(self.urlqueue, self.getimg))

    def start(self, url):
        self.urlqueue.put(url)
        comp = False
        while (not self.urlqueue.empty) or (not comp):
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
    args = parser.parse_args()
    if args.sess_id:
        config.sess_id = args.sess_id
    elif (args.username) and (args.password):
        config.sess_id = login(args.username, args.password)
    parse_pixlv(args.url)


if __name__ == "__main__":
    main()