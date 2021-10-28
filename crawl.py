import math
import json
import csv
from urllib import request
from pathlib import Path
from collections import Counter
import bs4
from bs4 import BeautifulSoup, NavigableString

PAGES_FILE = Path("pages.json")


def network_get(url):
    req = request.Request(url)
    response = request.urlopen(req)
    return response.read().decode()


def get_text(bs):
    if isinstance(bs, bs4.element.NavigableString):
        return str(bs)
    return " ".join([get_text(content) for content in bs.contents])


class Page:
    def __init__(self, url):
        self.url = url
        raw_text = network_get(self.url)
        self.words = dict(
            Counter(list(filter(lambda x: len(x) < 10, raw_text.split(" "))))
        )
        soup = BeautifulSoup(raw_text, features="html.parser")
        self.links = [str(link["href"]) for link in soup.find_all("a")]
        text = get_text(soup)
        self.rank = 1

    def value(self):
        return {
            "url": self.url,
            "links": self.links,
            "rank": self.rank,
            "words": self.words,
        }

    def __str__(self):
        return f"Page: {self.url}"

    def __repr__(self):
        return str(self)


# Dict url(str) -> Page.value()
pages = dict()


def crawl(url, depth=1, jump_domains=True):
    print(
        "crawl_domain", f"url={url}", f"depth={depth}", f"jump_domains={jump_domains}"
    )
    if str(url) in pages.values():
        return list()
    try:
        page = Page(url)
    except:
        return list()
    pages[str(url)] = page
    to_return = [page]
    if depth > 0:
        for link in page.links:
            try:
                if (not jump_domains) and link.domain != page.url.domain:
                    continue
                to_return += crawl(link, depth - 1, jump_domains)
            except:
                pass
    return to_return


if PAGES_FILE.exists():
    pages = json.load(open(PAGES_FILE))
else:
    whitelist = list()
    with open("whitelists.csv") as whitelist_file:
        reader = csv.reader(whitelist_file)
        for row in reader:
            whitelist += row

    for whitelisted in whitelist:
        crawl(whitelisted)

    pages_object = dict()
    for url, page in pages.items():
        pages_object[url] = page.value()

    pages_json = json.dumps(pages_object)

    with open(PAGES_FILE, "w") as pages_file:
        pages_file.write(pages_json)
        print(f"wrote to {str(PAGES_FILE)}")

    pages = pages_object

# Calculate page rank
for i in range(3):
    for url, page in pages.items():
        links = page["links"]
        value_per_link = float(page["rank"]) / len(links)
        for link in links:
            linked_page = pages.get(link)
            if linked_page != None:
                linked_page["rank"] += value_per_link

    for page in pages.values():
        print(page["rank"])
        page["rank"] = abs(math.log(page["rank"]))


class RankedPage:
    def __init__(self, url, score):
        self.url = url
        self.score = score


class Word:
    def __init__(self, word):
        self.word = word
        self.ranked_pages = list()

    def add(self, ranked_page):
        worst_page_index = -1
        for current_page in self.ranked_pages:
            if (
                worst_page_index == -1
                or current_pages.score < self.ranked_pages[worst_page_index].score
            ):
                pass

        if len(self.ranked_pages) < 10:
            pass


print(pages)
