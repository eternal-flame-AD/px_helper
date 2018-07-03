# px_helper [![Build Status](https://travis-ci.org/eternal-flame-AD/px_helper.svg?branch=master)](https://travis-ci.org/eternal-flame-AD/px_helper) [![Coverage Status](https://coveralls.io/repos/github/eternal-flame-AD/px_helper/badge.svg?branch=master)](https://coveralls.io/github/eternal-flame-AD/px_helper?branch=master)

2018-6-16 Ugoira现在会使用ffmpeg自动转为视频

## Installation

 `git clone https://github.com/eternal-flame-AD/px_helper.git`

 `cd ./px_helper && pip install ./`

## Usage
<pre>
usage: pxdown [-h] [-u USERNAME] [-p PASSWORD] [-s SESS_ID] [--proxy PROXY]
              [-o OUTPUT] [--max-page PAGE] [--newer-than NEW] [--remux REMUX]
              [--remux-ext REMUX_EXT]
              url

Pixiv downloader

positional arguments:
  url                   Pixiv URL, either bookmark, member_illust or illust

optional arguments:
  -h, --help            show this help message and exit
  -u USERNAME           username
  -p PASSWORD           password
  -s SESS_ID            sessid
  --proxy PROXY         specify a http proxy (format: http://127.0.0.1:8080)
  -o OUTPUT             output folder
  --max-page PAGE       specify max page number (only useful when downloading
                        illust_member or search page) Example: --max-page 10
  --newer-than NEW      Only download works newer than the specified date.
                        Format:YYYY-MM-DD Example: --newer-than 2018-07-03
  --remux REMUX         Whether to remux ugoira with ffmpeg(y/n). Default: y
  --remux-ext REMUX_EXT Output format of remuxed ugoira. Example: --remux-ext
                        mp4
</pre>
1. Use with username and password (This may cause your SESSID in your browser to be revoked):
  
  **REMINDER: Make sure to backslash characters in password when necessary**
  
  `pxdown -u USERNAME -p PASSWORD url`

2. Use with a valid PHPSESSID copied from your browser (31897178_xxxxxxxxxxxx):
  
  `pxdown -s SESS_ID url`

3. To Use With a HTTP proxy, add the --proxy param:
  
  `pxdown -s SESS_ID --proxy http://127.0.0.1:8080 url`

## Supported urls:
  - https://www.pixiv.net/bookmark.php (crawl all bookmarks)
  - https://www.pixiv.net/bookmark.php?p=x (start from this page)
  - https://www.pixiv.net/member_illust.php?mode=medium&illust_id=xxxxxx
  - https://www.pixiv.net/member_illust.php?mode=manga&illust_id=xxxxxx
  - https://www.pixiv.net/member_illust.php?id=xxxxxx (crawl all works)
  - https://www.pixiv.net/member_illust.php?id=xxxxxx&p=x (start from this page)
  - https://www.pixiv.net/search.php?word=xxx&order=xxx (iter over pages)
  - https://www.pixiv.net/search.php?word=xxx&order=xxx&p=x (start from this page)
  - https://www.pixiv.net/showcase/a/xxxx/

## Custom filter:
  you can edit the filter function in imgfilter.py to customize which image to download:
  
  <pre># example img filter
  def filter(img):
      # only download manga work(multi pics)
      return img.info['work_type']=="manga"
  </pre>
  sample info data for https://www.pixiv.net/member_illust.php?mode=medium&illust_id=68686165:
  <pre>
{'work_type': 'manga', 'work_imgcount': 3, 'work_title': '色がケンカしない方法', 'work_subtitle': '色がケンカしない方法をご質問をいただいたので、自己流ではありますが、解説しました。', 'work_time': '2018-05-10T16:07:35+00:00', 'work_id': '68686165', 'work_resolution': '900x635', 'height': 635, 'width': 900, 'author_id': '811927', 'author_nick': '村カルキ', 'author_info': {'Nickname': '村カルキ', 'Website': 'http://mura73424033.jimdo.com/', 'Gender': 'Female', 'Location': 'Chiba, Japan    ', 'Occupation': 'Seeking employment', 'Twitter': '\n                                            murakaruki\n                                    ', 'Self introduction': '■絵のお仕事募集しております。ご依頼、御用の際はHPに記載されているメールアドレスからお気軽にご連絡ください。（HP）http://mura73424033.jimdo.com/■絵を描くのと寝るのとゲームが好きです。創作とか企画物（PF）中心にその時好きな版権作品などのイラストを描いてます。好きなものを好きなだけ描いてますので固定ジャンルはありません。■イラストの転載許可に関しまして自分で管理できなくなる可能性がございますので、お問い合わせいただきましても許可はできないです。また、転載に関してのメッセージにもお答えはできません。■コメントやブックマーク、評価本当にありがとうございます！とても励みになります。全て大切に拝見させていただいております。コメントに関してはお返事できないことが多く申し訳ございません。■特に今後もマイピク限定公開にする予定の絵などもないのでマイピクは募集しておりません。基本的には友人、知人のみとさせていただいております。よろしくお願いします！◇仕事履歴◇【書籍】◆「シャバの『普通』は難しい」（エンターブレイン様）【中村颯希先生著】◆「銃魔大戦－怠謀連理－」（ＫＡＤＯＫＡＷＡ様）【カルロ・ゼン先生著】◆「無能と呼ばれた俺、４つの力を得る１～２」（オーバーラップ様）【松村道彦先生著】◆「クロの戦記」（オーバーラップ様）【サイトウアユム先生著】◆「異世界に転生したので日本式城郭をつくってみた。」（一二三書房様）【リューク先生著】◆「塗り事典BOYS」（NextCreator編集部様）CLIPSTUDIOPROメイキングイラスト＋解説◆「和装・洋装の描き方」（朝日新聞出版様）洋装の描き方のイラストカットを一部担当【TCG】◆「Lecee Overture Ver.Fate/Grannd Order 2.0」（TYPE-MOON様）３点◆「ラクエンロジック」（ブシロード様）３点【ソーシャルゲーム】◆「PSO2es」（株式会社セガ様）キャラクターイラスト7点◆「エンドライド」（株式会社サイバーエージェント様）イメージボード２点、背景６点◆「OZ Chrono Chronicle」（DMM GAMES様）キャラクターイラスト２セット◆「グランスフィア」（シリコンスタジオ様）カードイラスト多数◆「Ｒｅｖｏｌｖｅ」（株式会社ysy様）カードイラスト2点【その他】◆「Drawimg with Wacom」（株式会社ワコム様）イラスト制作動画＋インタビュー◆「BoCO株式会社2018年カレンダー」（BoCo株式会社様）カレンダーイラスト３、４月担当'}, 'view-count': 15040, 'like-count': 1057, 'bookmark-count': 1527, 'bookmarked': True, 'cover_url': 'https://i.pximg.net/img-original/img/2018/05/11/01/07/35/68686165_p0.jpg', 'referer': 'https://www.pixiv.net/member_illust.php?mode=medium&illust_id=68686165&lang=en', 'tags': ['メイキング'], 'manga_seq': 1, 'url': 'https://i.pximg.net/img-master/img/2018/05/11/01/07/35/68686165_p0_master1200.jpg'}
</pre>
  
  You can also limit urls to crawl by modifying the filter_url function (see imgfilter.py for an example for limiting pages to crawl)

## More about info output:
  - "work_type": "manga"/"illust"/"ugoira"
  - "work_imgcount": total count of images in this work
  - "work_title": title of this work
  - "work_subtitle": subtitle or comment of this work
  - "work_resolution": $"{width}x{height}"
  - "work_time": submission time of this work
  - "manga_seq": Only in manga work. The sequence number of this image in the work, 'cover' for the cover image.
  - "bookmarked": whether you have bookmarked this work
  - "referer": referer needed to download this image
  - "url": url of the image
  
## Notice
This software uses <a href=http://ffmpeg.org>FFmpeg</a> licensed under the <a href=http://www.gnu.org/licenses/old-licenses/lgpl-2.1.html>LGPLv2.1</a>.
