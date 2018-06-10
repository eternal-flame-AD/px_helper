import pytest
import os
import sys
import time
import threading

parentdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parentdir)

import main
import login
import config


@pytest.fixture(scope="function")
def clean_download_dir():
    import shutil
    shutil.rmtree("down", ignore_errors=True)
    try:
        os.remove("output-info.txt")
    except:
        pass

@pytest.fixture(scope="module", autouse=True)
def start_proxy():
    import proxy2
    proxy_server = threading.Thread(target=proxy2.test, args=())
    proxy_server.daemon = True
    proxy_server.start()
    time.sleep(3) # wait for proxy to start
    config.proxy = "http"
    config.proxy_host = "127.0.0.1"
    config.proxy_port = 8080

class TestCrawlProxy():
    @pytest.fixture(scope="class", autouse=True)
    def login(self):
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
            "https://www.pixiv.net/member_illust.php?mode=medium&illust_id=68686165"
        )
        assert os.path.getsize("down/村カルキ/色がケンカしない方法/1.jpg") > 20000
        assert os.path.getsize("down/村カルキ/色がケンカしない方法/2.jpg") > 20000
        assert os.path.getsize("down/村カルキ/色がケンカしない方法/3.jpg") > 20000
