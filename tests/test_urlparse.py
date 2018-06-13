import os
import sys

parentdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parentdir)

from pxelem import PixivUrl


class TestUrlParse():
    def test_simple_url(self):
        url = PixivUrl("https://www.example.com", use_english=False)
        assert url.getscheme() == "https"
        assert url.gethost() == "www.example.com"
        assert url.getquerydict() == {}
        assert url.geturi() == "/"

    def test_query_string(self):
        url = PixivUrl(
            "https://www.example.com/query.php?param1=abc&param2=123",
            use_english=False)
        assert url.getquerydict()["param1"][0] == "abc"
        url.addquerystring("param3", "456")
        assert url.getquerydict()["param3"][0] == "456"
        url.addquerystring("param3", "789")
        assert url.getquerydict()["param3"][0] == "789"
        assert url.geturl(
        ) == "https://www.example.com/query.php?param1=abc&param2=123&param3=789"

    def test_port_detection(self):
        url = PixivUrl("https://www.example.com")
        assert url.getport() == 443
        url = PixivUrl("http://www.example.com")
        assert url.getport() == 80
        url = PixivUrl("https://www.example.com:444")
        assert url.getport() == 444
