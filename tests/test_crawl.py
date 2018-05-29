import pytest
import os
import sys

parentdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parentdir)

import main
import login
import config


class TestCrawl():
    @pytest.fixture(scope="class", autouse=True)
    def login(self):
        username = os.getenv("PX_USER")
        password = os.getenv("PX_PASS")
        config.sess_id = login.login(username, password)

    def test_crawl_one_page_illust(self):
        main.parse_pixlv(
            "https://www.pixiv.net/member_illust.php?mode=medium&illust_id=59259626"
        )
