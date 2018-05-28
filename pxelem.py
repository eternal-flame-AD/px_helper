import urllib.parse as urlparser
import downloader
import bs4

author_cache = {}


class PixlvAuthors():
    def query(self, id):
        if id in author_cache:
            return author_cache[id]
        url = PixlvUrl("https://www.pixiv.net/member.php?id=" + id)
        content = url.toBs4()
        res = {}
        res['author_nick'] = content.find(
            "table", class_="profile").find(
                "td", text="Nickname").parent.find(
                    "td", class_="td2").get_text()
        author_cache[id] = res
        return res


class PixlvImage():
    def __init__(self, url, info={}):
        self.url = url
        info['url'] = url
        self.info = info

    def __str__(self):
        return str(self.info)


class PixlvUrl():
    def __init__(self, url, base=None, info={}):
        self.info = info
        if base:
            self.url = urlparser.urlparse(urlparser.urljoin(base, url))
        else:
            self.url = urlparser.urlparse(url)

    def addinfo(self, key, elem):
        self.info[key] = elem

    def toBs4(self):
        content = downloader.download_html(self.gethost(), self.geturi())
        return bs4.BeautifulSoup(content, "html5lib")

    def gethost(self):
        return self.url.hostname

    def getscheme(self):
        return self.url.scheme

    def getport(self):
        if self.url.port:
            return self.url.port
        else:
            if self.getscheme == ("http"):
                return 80
            elif self.getscheme == ("https"):
                return 443
            else:
                raise ValueError("Unknown port: " + self.url.geturl())

    def geturl(self):
        return self.url.geturl()

    def geturi(self):
        if self.url.query != "":
            return self.url.path + "?" + self.url.query
        else:
            return self.url.path

    def getquerydict(self):
        return urlparser.parse_qs(self.url.query)
