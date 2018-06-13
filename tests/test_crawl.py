import pytest
import os
import sys
import time

parentdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parentdir)

import main
import login
import config
import imgfilter


@pytest.fixture(scope="function")
def clean_download_dir():
    import shutil
    shutil.rmtree("down", ignore_errors=True)
    try:
        os.remove("output-info.txt")
    except:
        pass


def get_output_info():
    res = []
    import codecs
    with codecs.open("output-info.txt", mode="r", encoding="utf-8") as f:
        for line in f.readlines():
            if type(eval(line)) == dict:
                res.append(eval(line))
    return res


class TestCrawl():
    @pytest.fixture(scope="class", autouse=True)
    def login(self):
        config.proxy = None
        username = os.getenv("PX_USER")
        password = os.getenv("PX_PASS")
        config.sess_id = login.login(username, password)

    def test_crawl_one_pic_illust(self):
        main.parse_pixlv(
            "https://www.pixiv.net/member_illust.php?mode=medium&illust_id=59259626"
        )
        assert os.path.getsize("down/ツバサ/『　』.jpg") > 20000

    def test_crawl_mult_pic_illust(self):
        main.parse_pixlv(
            "https://www.pixiv.net/showcase/a/3517/"
        )
        assert os.path.getsize("down/アガハリ/徹はんと緒花はん/1.jpg") > 20000
        assert len(get_output_info()) > 5

    def test_crawl_showcase(self):
        main.parse_pixlv(
            "https://www.pixiv.net/member_illust.php?mode=medium&illust_id=68686165"
        )
        assert os.path.getsize("down/村カルキ/色がケンカしない方法/1.jpg") > 20000
        assert os.path.getsize("down/村カルキ/色がケンカしない方法/2.jpg") > 20000
        assert os.path.getsize("down/村カルキ/色がケンカしない方法/3.jpg") > 20000

    def test_crawl_author_page(self):
        # inject filter function
        def filter_url(url):
            try:
                p = int(url.getquerydict()['p'][0])
                return p == 5
            except KeyError:
                return True

        imgfilter.filter_url = filter_url
        main.parse_pixlv(
            "https://www.pixiv.net/member_illust.php?id=811927&type=all&p=5")
        assert len(get_output_info()) >= 20

    def test_crawl_search_page(self):
        # inject filter function
        def filter_url(url):
            try:
                p = int(url.getquerydict()['p'][0])
                return p == 5
            except KeyError:
                return True

        imgfilter.filter_url = filter_url
        main.parse_pixlv(
            "https://www.pixiv.net/search.php?word=test&order=date_d&p=5")
        assert len(get_output_info()) >= 20
