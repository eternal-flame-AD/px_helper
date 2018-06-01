# px_helper [![Build Status](https://travis-ci.org/eternal-flame-AD/px_helper.svg?branch=master)](https://travis-ci.org/eternal-flame-AD/px_helper) [![Coverage Status](https://coveralls.io/repos/github/eternal-flame-AD/px_helper/badge.svg?branch=master)](https://coveralls.io/github/eternal-flame-AD/px_helper?branch=master)

## Usage
usage: main.py [-h] [-u USERNAME] [-p PASSWORD] [-s SESS_ID] [--proxy PROXY] url

1. Use with username and password (This may cause your SESSID in your browser to be revoked):
  
  **REMINDER: Make sure to backslash characters in password when necessary**
  
  `python main.py -u USERNAME -p PASSWORD url`

2. Use with a valid PHPSESSID copied from your browser (31897178_xxxxxxxxxxxx):
  
  `python main.py -s SESS_ID url`

3. To Use With a HTTP proxy, add the --proxy param:
  
  `python main.py -s SESS_ID --proxy http://127.0.0.1:8080 url`

## Supported urls:
  - https://www.pixiv.net/bookmark.php (crawl all bookmarks)
  - https://www.pixiv.net/bookmark.php?p=x (start from this page)
  - https://www.pixiv.net/member_illust.php?mode=medium&illust_id=xxxxxx
  - https://www.pixiv.net/member_illust.php?mode=manga&illust_id=xxxxxx
  - https://www.pixiv.net/member_illust.php?id=xxxxxx (crawl all works)
  - https://www.pixiv.net/member_illust.php?id=xxxxxx&p=x (start from this page)
  - https://www.pixiv.net/search.php?word=xxx&order=xxx (iter over pages)
  - https://www.pixiv.net/search.php?word=xxx&order=xxx&p=x (start from this page)

## Custom filter:
  you can edit the filter function in imgfilter.py to customize which image to download:
  
  <pre># example img filter
  def filter(img):
      # only download manga work(multi pics)
      return img.info['work_type']=="manga"
  </pre>
  sample info data for https://www.pixiv.net/member_illust.php?mode=medium&illust_id=68768651:
  <pre>
  {'work_type': 'illust', 'work_title': '死してなお囚われる', 'work_subtitle': '', 'work_time': '5/16/2018 02:28', 'work_resolution': '650×612', 'work_id': '68768651', 'author_id': '811927', 'tags': ['オリジナルoriginal', '創作creation', 'オリジナル1000users入りoriginal 1000+ bookmarks', '昆虫標本', '標本hyouhonn'], 'view-count': '16084', 'rated-count': '1901', 'bookmarked': False, 'referer': 'https://www.pixiv.net/member_illust.php?mode=medium&illust_id=68768651', 'author_nick': '村カルキ', 'author_info': {'Nickname': '村カルキ', 'Website': 'http://mura73424033.jimdo.com/', 'Gender': 'Female', 'Location': 'Chiba, Japan    ', 'Occupation': 'Seeking employment', 'Twitter': '\n                                            murakaruki\n                                    ', 'Self introduction': '■絵のお仕事募集しております。ご依頼、御用の際はHPに記載されているメールアドレスからお気軽にご連絡ください。（HP）http://mura73424033.jimdo.com/■絵を描くのと寝るのとゲームが好きです。創作とか企画物（PF）中心にその時好きな版権作品などのイラストを描いてます。好きなものを好きなだけ描いてますので固定ジャンルはありません。■イラストの転載許可に関しまして自分で管理できなくなる可能性がございますので、お問い合わせいただきましても許可はできないです。また、転載に関してのメッセージにもお答えはできません。■コメントやブックマーク、評価本当にありがとうございます！とても励みになります。全て大切に拝見させていただいております。コメントに関してはお返事できないことが多く申し訳ございません。■特に今後もマイピク限定公開にする予定の絵などもないのでマイピクは募集しておりません。基本的には友人、知人のみとさせていただいております。よろしくお願いします！◇仕事履歴◇【書籍】◆「シャバの『普通』は難しい」（エンターブレイン様）【中村颯希先生著】◆「銃魔大戦－怠謀連理－」（ＫＡＤＯＫＡＷＡ様）【カルロ・ゼン先生著】◆「無能と呼ばれた俺、４つの力を得る１～２」（オーバーラップ様）【松村道彦先生著】◆「クロの戦記」（オーバーラップ様）【サイトウアユム先生著】◆「異世界に転生したので日本式城郭をつくってみた。」（一二三書房様）【リューク先生著】◆「塗り事典BOYS」（NextCreator編集部様）CLIPSTUDIOPROメイキングイラスト＋解説◆「和装・洋装の描き方」（朝日新聞出版様）洋装の描き方のイラストカットを一部担当【TCG】◆「Lecee Overture Ver.Fate/Grannd Order 2.0」（TYPE-MOON様）３点◆「ラクエンロジック」（ブシロード様）３点【ソーシャルゲーム】◆「PSO2es」（株式会社セガ様）キャラクターイラスト7点◆「エンドライド」（株式会社サイバーエージェント様）イメージボード２点、背景６点◆「OZ Chrono Chronicle」（DMM GAMES様）キャラクターイラスト２セット◆「グランスフィア」（シリコンスタジオ様）カードイラスト多数◆「Ｒｅｖｏｌｖｅ」（株式会社ysy様）カードイラスト2点【その他】◆「Drawimg with Wacom」（株式会社ワコム様）イラスト制作動画＋インタビュー◆「BoCO株式会社2018年カレンダー」（BoCo株式会社様）カレンダーイラスト３、４月担当'}, 'url': 'https://i.pximg.net/img-original/img/2018/05/16/02/28/49/68768651_p0.jpg'}
</pre>
  
  You can also limit urls to crawl by modifying the filter_url function (see imgfilter.py for an example for limiting pages to crawl)
