def filter(img):
    return True


def filter_url(url):
    # filter by pages
    try:
        p = int(url.getquerydict()['p'][0])
        return p < 99999
    except KeyError:
        return True
