import sys
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
        page["rank"] = abs(math.log(page["rank"]))


class RankedPage:
    def __init__(self, url, score):
        self.url = url
        self.score = score

class Word:
    RANKED_PAGES_COUNT = 10
    
    def __init__(self, word):
        self.word = word
        self.ranked_pages = list()

    def add(self, ranked_page):
        worst_page_index = -1
        for i in range(len(self.ranked_pages)):
            current_page = self.ranked_pages[i]
            if (
                worst_page_index == -1
                or current_page.score < self.ranked_pages[worst_page_index].score
            ):
                worst_page_index = i

        if len(self.ranked_pages) < Word.RANKED_PAGES_COUNT:
            self.ranked_pages.append(ranked_page)
        elif ranked_page.score > self.ranked_pages[worst_page_index].score:
            self.ranked_pages[worst_page_index] = ranked_page
        

# dict word(str) -> Word
words = dict()

for url, page in pages.items():
    total_word_count = sum(page['words'].values())
    for word_value, word_count in page['words'].items():
        word_score = (float(word_count) / total_word_count) * page['rank']
        ranked_page = RankedPage(url, word_score)
        ranked_word = words.get(word_value)
        if ranked_word == None:
            ranked_word = Word(word_value)
            words[word_value] = ranked_word
        ranked_word.add(ranked_page)


query = input('Enter search query: ')

ranked_word = words.get(query)
if ranked_word is None:
    print('Could not find results.')
    sys.exit(0)
    
ranked_pages = ranked_word.ranked_pages
if len(ranked_pages) < 1:
    print('Could not find results.')
    sys.exit(0)

best_result = ranked_pages[0]
for page in ranked_pages:
    if page.score > best_result.score:
        best_result = page
print(best_result.url)


    

