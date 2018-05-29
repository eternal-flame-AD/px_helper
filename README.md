# px_helper

## Usage
usage: main.py [-h] [-u USERNAME] [-p PASSWORD] [-s SESS_ID] url

1. Use with username and password:
  python main.py -u USERNAME -p PASSWORD url
 
2. Use with a valid PHPSESSID:
  python main.py -s SESS_ID url
  
## Supported urls:
  - https://www.pixiv.net/bookmark.php
  - https://www.pixiv.net/member_illust.php?mode=medium&illust_id=xxxxxx
  - https://www.pixiv.net/member_illust.php?mode=manga&illust_id=xxxxxx
  - https://www.pixiv.net/member_illust.php?id=xxxxxx
