import urllib.parse as urlparser
import downloader
import bs4
import config

author_cache = {}


class PixlvAuthors():
    def query(self, id):
        if id in author_cache:
            return author_cache[id]
        url = PixlvUrl("https://www.pixiv.net/member.php?lang=en&id=" + id)
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


class PixlvImage():
    def __init__(self, url, info={}):
        self.url = url
        info['url'] = url
        self.info = info

    def __str__(self):
        return str(self.info)


class PixlvUrl():
    def __init__(self, url, base=None, info={}, use_sessid=True):
        self.info = info
        self.use_sessid = use_sessid
        if base:
            self.url = urlparser.urlparse(urlparser.urljoin(base, url))
        else:
            self.url = urlparser.urlparse(url)

    def addinfo(self, key, elem):
        self.info[key] = elem

    def toBs4(self):
        content = downloader.download_html(
            self.gethost(),
            self.geturi(),
            sessid=(config.sess_id if self.use_sessid else None))
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
