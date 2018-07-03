import argparse
import re

from . import config
from .parser import parse_pixiv
from .pxelem import PixivUrl
from .login import login
from . import imgfilter


def main():
    parser = argparse.ArgumentParser(description="Pixiv downloader")
    parser.add_argument(
        "url",
        type=str,
        help="Pixiv URL, either bookmark, member_illust or illust")
    parser.add_argument("-u", dest="username", help="username", type=str)
    parser.add_argument("-p", dest="password", help="password", type=str)
    parser.add_argument("-s", dest="sess_id", help="sessid", type=str)
    parser.add_argument(
        "--proxy",
        dest="proxy",
        help="specify a http proxy (format: http://127.0.0.1:8080)")
    parser.add_argument("-o", dest="output", help="output folder", type=str)
    parser.add_argument(
        "--max-page",
        dest="page",
        help=
        "specify max page number (only useful when downloading illust_member or search page) Example: --max-page 10",
        type=int)
    parser.add_argument(
        "--newer-than",
        dest="new",
        help=
        "Only download works newer than the specified date. Format:YYYY-MM-DD Example: --newer-than 2018-07-03",
        type=str)
    parser.add_argument(
        "--remux",
        dest="remux",
        help="Whether to remux ugoira with ffmpeg(y/n). Default: y",
        type=str)
    parser.add_argument(
        "--remux-ext",
        dest="remux_ext",
        help="Output format of remuxed ugoira. Example: --remux-ext mp4",
        type=str)
    args = parser.parse_args()

    if args.proxy:
        proxy_url = PixivUrl(args.proxy, use_sessid=False, use_english=False)
        scheme = proxy_url.getscheme()
        if scheme == "http":
            config.proxy = "http"
            config.proxy_host = proxy_url.gethost()
            config.proxy_port = proxy_url.getport()
        else:
            raise NotImplementedError("Unsupported proxy")
    else:
        config.proxy = None

    if args.page:

        def filter_url(url):
            try:
                p = int(url.getquerydict()['p'][0])
                return p <= args.page
            except KeyError:
                return True

        imgfilter.filter_url = filter_url

    if args.remux:
        args.remux = args.remux.lower()
        if "y" in args.remux:
            config.remux_ugoira = True
        if "n" in args.remux:
            config.remux_ugoira = False
    if args.remux_ext:
        config.remux_ext = args.remux_ext

    if args.new:
        assert re.match(r"\d{4}-\d{2}-\d{2}",
                        args.new), "Invalid date format. YYYY-MM-DD"
        imgfilter.filter = lambda img: img.info['work_time'] >= args.new

    if args.output:
        if args.output.endswith("/") or args.output.endswith("\\"):
            args.output = args.output[:-1]
        config.download_prefix = args.output

    if args.sess_id:
        config.sess_id = args.sess_id
    elif (args.username) and (args.password):
        config.sess_id = login(args.username, args.password)
    else:
        raise ValueError("Provide credentials please")

    parse_pixiv(args.url)


if __name__ == "__main__":
    main()
