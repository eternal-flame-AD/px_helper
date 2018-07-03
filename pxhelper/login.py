import http.client as httpconn
import urllib.parse
import re
import bs4
import json

from . import config
from .pxelem import PixivUrl


def login(username, password):
    host = "accounts.pixiv.net"
    if config.proxy == "http":
        conn = httpconn.HTTPSConnection(config.proxy_host, config.proxy_port)
        conn.set_tunnel(host)
    elif config.proxy == None:
        conn = httpconn.HTTPSConnection(host)
    conn.request(
        "GET",
        "/login?lang=en&source=pc&view_type=page&ref=wwwtop_accounts_index")
    res = conn.getresponse()
    login_cookie = res.getheader("set-cookie")
    post_key = bs4.BeautifulSoup(res.read(), "html5lib").find(
        "input", attrs={"name": "post_key"})['value']
    login_sess_id = re.search(r"(?<=PHPSESSID=)(\w)*(?=;)",
                              login_cookie).group(0)

    params = urllib.parse.urlencode({
        "pixiv_id": username,
        "captcha": "",
        "g_recaptcha_response": "",
        "password": password,
        "post_key": post_key,
        "lang": "en",
        "source": "accounts",
        "ref": "",
        "return_to": "https://www.pixiv.net",
    })

    conn.request(
        "POST",
        "/api/login?lang=en",
        body=params,
        headers={
            "origin":
            "https://accounts.pixiv.net",
            "referer":
            "https://accounts.pixiv.net/login?lang=en&source=pc&view_type=page&ref=wwwtop_accounts_index",
            "content-type":
            "application/x-www-form-urlencoded",
            "accept":
            "application/json",
            "cookie":
            "show_welcome_modal=1; p_ab_id=7; p_ab_id_2=9; login_bc=1; PHPSESSID="
            + login_sess_id,
            "user-agent":
            "Mozilla/5.0"
        })
    res = conn.getresponse()
    result = json.loads(res.read())
    if result['error'] or ("success" not in result['body']):
        print("login fail:" + str(result))
        raise ValueError
    return re.search(r"(?<=PHPSESSID=)[\w_]*(?=;)",
                     res.getheader("set-cookie")).group(0)
