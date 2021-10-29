import sys
import math
import json
import csv
from urllib import request
from pathlib import Path
from collections import Counter, defaultdict
import bs4
from bs4 import BeautifulSoup, NavigableString

SEARCH_DEPTH = 3
PAGES_FILE = Path("pages.json")
WORDS_FILE = Path("words.json")
MAX_WORD_LENGTH = 2000
REQUEST_TIMEOUT = 10
MAX_LINKS_PER_PAGE = 30


def network_get(url):
    req = request.Request(url)
    response = request.urlopen(req, timeout=REQUEST_TIMEOUT)
    return response.read().decode()


def get_text(bs):
    if isinstance(bs, bs4.element.NavigableString):
        return str(bs)
    return " ".join([get_text(content) for content in bs.contents])


class Page:
    def __init__(self, url, get_page=True):
        self.url = url
        if get_page:
            raw_text = network_get(self.url)
            self.words = dict(
                Counter(
                    list(
                        filter(
                            lambda x: len(x) < MAX_WORD_LENGTH,
                            [word.lower() for word in raw_text.split(" ")],
                        )
                    )
                )
            )
            soup = BeautifulSoup(raw_text, features="html.parser")
            self.links = [str(link["href"]) for link in soup.find_all("a")][
                :MAX_LINKS_PER_PAGE
            ]
            text = get_text(soup)
            self.rank = 1

    def value(self):
        return {
            "url": self.url,
            "links": self.links,
            "rank": self.rank,
            "words": self.words,
        }

    def load(value):
        to_return = Page(value["url"], False)
        to_return.links = value["links"]
        to_return.rank = value["rank"]
        to_return.words = value["words"]

    def __str__(self):
        return f"Page: {self.url}"

    def __repr__(self):
        return str(self)


# Dict url(str) -> Page.value()
pages = dict()


def crawl(url, depth=SEARCH_DEPTH, jump_domains=True):
    print(
        "crawl_domain", f"url={url}", f"depth={depth}", f"jump_domains={jump_domains}"
    )
    if str(url) in pages.keys():
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
    pages_object = json.load(open(PAGES_FILE))
    print(f"Read from {str(PAGES_FILE)}")

    for url, page_value in pages_object.items():
        pages[url] = Page.load(page_value)

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


class RankedPage:
    def __init__(self, url, score):
        self.url = url
        self.score = score

    def value(self):
        return {"url": self.url, "score": self.score}

    def load(value):
        return RankedPage(value["url"], value["score"])


class Word:
    RANKED_PAGES_COUNT = 10

    def __init__(self, ranked_pages):
        self.ranked_pages = ranked_pages

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

    def value(self):
        return [ranked_page.value() for ranked_page in self.ranked_pages]

    def load(value):
        to_return = Word(list())
        to_return.ranked_pages = [
            RankedPage.load(ranked_page_value) for ranked_page_value in value
        ]
        return to_return


if WORDS_FILE.exists():
    words_object = json.load(open(WORDS_FILE))
    print(f"Read from {str(WORDS_FILE)}")

    words = dict()
    for word_value, word in words_object.items():
        words[word_value] = Word.load(word)

else:
    # Calculate page rank
    for i in range(3):
        for url, page in pages.items():
            links = page.links
            value_per_link = float(page.rank) / max(len(links), 1)
            for link in links:
                linked_page = pages.get(link)
                if linked_page != None:
                    linked_page.rank += value_per_link

        for page in pages.values():
            page.rank = abs(math.log(max(page.rank, 1)))

    # dict word(str) -> Word
    words = dict()

    # Build word lookup
    for url, page in pages.items():
        total_word_count = sum(page.words.values())
        for word_value, word_count in page.words.items():
            word_score = (float(word_count) / total_word_count) * page.rank
            ranked_page = RankedPage(url, word_score)
            ranked_word = words.get(word_value)
            if ranked_word == None:
                ranked_word = Word(list())
                words[word_value] = ranked_word
            ranked_word.add(ranked_page)

    words_object = dict()
    for word_value, word in words.items():
        words_object[word_value] = word.value()

    words_json = json.dumps(words_object)

    with open(WORDS_FILE, "w") as words_file:
        words_file.write(words_json)
        print(f"wrote to {str(WORDS_FILE)}")


def search(query):
    query_words = list(filter(lambda x: len(x) < MAX_WORD_LENGTH, query.split(" ")))
    results = defaultdict(int)  # url (str) -> score (float)

    for query_word in query_words:
        ranked_word = words.get(query_word)
        if ranked_word is not None:
            ranked_pages = ranked_word.ranked_pages
            if len(ranked_pages) > 0:
                for page in ranked_pages:
                    results[page.url] += page.score
    return results


def run_search(query):
    results = search(query)

    ranked_results = list(
        map(lambda x: x[0], sorted(results.items(), key=lambda x: x[1], reverse=True))
    )

    return ranked_results
