import urllib.parse as urlparser
import bs4
import re
import json

from . import downloader
from . import config

author_cache = {}


class PixivAuthors():
    def query(self, id):
        if id in author_cache:
            return author_cache[id]
        url = PixivUrl("https://www.pixiv.net/member.php?lang=en&id=" + id)
        content = url.toBs4()
        res = {}
        detail_info = {}
        for row in content.find("table", class_="profile").find_all("tr"):
            detail_info[row.find("td", class_="td1").get_text()] = row.find(
                "td", class_="td2").get_text()
        res['author_nick'] = detail_info['Nickname']
        res['author_info'] = detail_info
        author_cache[id] = res
        return res


class PixivImage():
    def __init__(self, url, info={}):
        self.url = url
        info['url'] = url
        self.info = info

    def __str__(self):
        return str(self.info)


class PixivUrl():
    def __init__(self,
                 url,
                 base=None,
                 info={},
                 use_sessid=True,
                 use_english=True):
        self.info = info
        self.use_sessid = use_sessid
        if base:
            self.url = urlparser.urlparse(urlparser.urljoin(base, url))
        else:
            self.url = urlparser.urlparse(url)
        if use_english:
            self.addquerystring("lang", "en")

    def addinfo(self, key, elem):
        self.info[key] = elem

    def _download(self):
        content = downloader.download_html(
            self.gethost(),
            self.geturi(),
            sessid=(config.sess_id if self.use_sessid else None))
        return content

    def toJsonDict(self):
        content = self._download()
        return json.loads(content)

    def toBs4(self):
        content = self._download()
        return bs4.BeautifulSoup(content, "html5lib")

    def gethost(self):
        return self.url.hostname

    def getscheme(self):
        return self.url.scheme

    def getport(self):
        if self.url.port:
            return self.url.port
        else:
            if self.getscheme() == "http":
                return 80
            elif self.getscheme() == "https":
                return 443
            else:
                raise ValueError("Unknown port: " + self.url.geturl())

    def geturl(self):
        return self.url.geturl()

    def geturi(self):
        path = self.url.path
        if path == "":
            path = "/"
        if self.url.query != "":
            return path + "?" + self.url.query
        else:
            return path

    def getquerydict(self):
        return urlparser.parse_qs(self.url.query)

    def addquerystring(self, key, elem):
        url = self.geturl()
        if key in self.getquerydict():
            url += "&"
            orig_query_string = re.search(key + "=(.*?)&", url).group(0)
            url = url.replace(orig_query_string, key + "=" + elem + "&")[:-1]
        else:
            url = url + ("?" if "?" not in url else "&") + key + "=" + elem
        self.url = urlparser.urlparse(url)
