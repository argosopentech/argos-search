import sys
import math
import json
import csv
import subprocess
from pathlib import Path
from collections import Counter, defaultdict
import bs4
from bs4 import BeautifulSoup, NavigableString

SEARCH_DEPTH = 0
PAGES_FILE = Path("pages.json")
WORDS_FILE = Path("words.json")
MAX_WORD_LENGTH = 15
REQUEST_TIMEOUT = 10
MAX_LINKS_PER_PAGE = 30


def network_get(url):
    res = subprocess.run(["curl", url], capture_output=True)
    return str(res.stdout)


def get_text(bs):
    if isinstance(bs, bs4.element.NavigableString):
        return str(bs)
    return " ".join([get_text(content) for content in bs.contents])


def get_words(s):
    s = s.lower()
    split = s.split(" ")
    for meta_word_size in range(2, 4):
        for i in range(0, len(split) - meta_word_size):
            split.append(" ".join(split[i : i + meta_word_size]))
    return list(filter(lambda x: len(x) < MAX_WORD_LENGTH, split))


class Link:
    def parse_url(url):
        """Parse a url string.

        Return tuple (protocol, domain, path) or None
        """
        colon_index = url.find("://")
        if colon_index < 0:
            return None
        protocol = url[:colon_index]
        domain_start = colon_index + len("://")
        domain_end = url.find("/", domain_start)
        if domain_end < 0:
            return None
        domain = url[domain_start:domain_end]
        path = url[domain_end:]
        return (protocol, domain, path)

    def resolve_url(url, context):
        parsed_url = Link.parse_url(url)
        if parsed_url is not None:
            return url
        else:
            parsed_context = Link.parse_url(context)
            if parsed_context is None:
                return None
            context_protocol, context_domain, _ = parsed_context
            relative_url = context_protocol + "://" + context_domain + url
            parsed_url = Link.parse_url(relative_url)
            if parsed_url is None:
                return None
            return relative_url

    def create(link, context=""):
        to_return = Link()
        href = link.get("href")
        if href is None:
            return None
        to_return.url = Link.resolve_url(str(href), context)
        if to_return.url is None:
            return None
        to_return.words = get_words(get_text(link))
        return to_return

    def value(self):
        return {"url": self.url, "words": self.words}

    def load(value):
        to_return = Link()
        to_return.url = value["url"]
        to_return.words = value["words"]
        return to_return


class Page:
    def __init__(self, url, get_page=True):
        self.url = url
        if get_page:
            raw_text = network_get(self.url)
            self.words = dict(Counter(get_words(raw_text)))
            soup = BeautifulSoup(raw_text, features="html.parser")
            self.links = list(
                filter(
                    lambda x: x is not None,
                    [
                        Link.create(link, context=self.url)
                        for link in soup.find_all("a")
                    ][:MAX_LINKS_PER_PAGE],
                )
            )
            text = get_text(soup)
            self.rank = 1
            self.title = self.url
            titles = soup.find_all("title")
            if len(titles) > 0:
                self.title = get_text(titles[0])
            else:
                h1s = soup.find_all("h1")
                if len(h1s) > 0:
                    self.title = get_text(h1s[0])

    def value(self):
        return {
            "url": self.url,
            "links": [link.value() for link in self.links],
            "rank": self.rank,
            "words": self.words,
            "title": self.title,
        }

    def load(value):
        to_return = Page(value["url"], False)
        to_return.links = [Link.load(link) for link in value["links"]]
        to_return.rank = value["rank"]
        to_return.words = value["words"]
        to_return.title = value["title"]
        return to_return

    def __str__(self):
        return f"Page: {self.url}"


# Dict url(str) -> Page.value()
pages = dict()


def crawl(url, depth=SEARCH_DEPTH):
    print("crawl_domain", f"url={url}", f"depth={depth}")
    page = pages.get(url)
    if page is None:
        try:
            page = Page(url)
            pages[url] = page
        except Exception as e:
            print(e)
    if depth > 0:
        for link in page.links:
            crawl(link.url, depth - 1)


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

print(f"Scraped {len(pages.items())} pages")


class ScoredPage:
    def __init__(self, url, score):
        self.url = url
        self.score = score

    def value(self):
        return {"url": self.url, "score": self.score}

    def load(value):
        return ScoredPage(value["url"], value["score"])


class Word:
    SCORED_PAGES_COUNT = 50

    def __init__(self, scored_pages):
        self.scored_pages = scored_pages

    def add(self, scored_page):
        worst_page_index = -1
        for i in range(len(self.scored_pages)):
            current_page = self.scored_pages[i]
            if (
                worst_page_index == -1
                or current_page.score < self.scored_pages[worst_page_index].score
            ):
                worst_page_index = i

        if len(self.scored_pages) < Word.SCORED_PAGES_COUNT:
            self.scored_pages.append(scored_page)
        elif scored_page.score > self.scored_pages[worst_page_index].score:
            self.scored_pages[worst_page_index] = scored_page

    def value(self):
        return [scored_page.value() for scored_page in self.scored_pages]

    def load(value):
        to_return = Word(list())
        to_return.scored_pages = [
            ScoredPage.load(scored_page_value) for scored_page_value in value
        ]
        return to_return


pages = dict(filter(lambda x: x[1] is not None, pages.items()))


if WORDS_FILE.exists():
    words_object = json.load(open(WORDS_FILE))
    print(f"Read from {str(WORDS_FILE)}")

    words = dict()
    for word_value, word in words_object.items():
        words[word_value] = Word.load(word)

else:
    # Calculate page rank
    for url, page in pages.items():
        page.points = 10
    for i in range(2):
        for url, page in pages.items():
            links = page.links
            value_per_link = math.exp(page.rank) / max(len(links), 1)
            for link in links:
                linked_page = pages.get(link.url)
                if linked_page != None:
                    linked_page.points += value_per_link

        for page in pages.values():
            page.rank += abs(math.log(max(page.points, 1)))
    print(
        f"Calculated PageRank avg={float(sum([page.rank for page in pages.values()])) / len(pages.items())}"
    )

    # dict word(str) -> Word
    words = dict()

    # Add links to words dict

    # dict word(str) -> (dict url(str) -> score)
    link_score = dict()
    for url, page in pages.items():
        for link in page.links:
            for word in link.words:
                if link_score.get(word) is None:
                    link_score[word] = defaultdict(float)
                link_score[word][link.url] = link_score[word][link.url] + math.exp(
                    page.rank
                )
    for word, score_dict in link_score.items():
        for page, score in score_dict.items():
            score = math.log(max(1, score))
            scored_page = ScoredPage(page, score)
            ranked_word = words.get(word)
            if ranked_word == None:
                ranked_word = Word(list())
                words[word] = ranked_word
            ranked_word.add(scored_page)

    # Add page content to words dict
    for url, page in pages.items():
        total_word_count = sum(page.words.values())
        for word_value, word_count in page.words.items():
            word_score = math.log(
                max(1, (float(word_count) / total_word_count) * math.exp(page.rank))
            )
            scored_page = ScoredPage(url, word_score)
            ranked_word = words.get(word_value)
            if ranked_word == None:
                ranked_word = Word(list())
                words[word_value] = ranked_word
            ranked_word.add(scored_page)

    words_object = dict()
    for word_value, word in words.items():
        words_object[word_value] = word.value()

    words_json = json.dumps(words_object)

    with open(WORDS_FILE, "w") as words_file:
        words_file.write(words_json)
        print(f"wrote to {str(WORDS_FILE)}")


def search(query):
    query = query.lower()
    query_words = get_words(query)
    results = defaultdict(int)  # url (str) -> score (float)

    for query_word in query_words:
        ranked_word = words.get(query_word)
        if ranked_word is not None:
            scored_pages = ranked_word.scored_pages
            if len(scored_pages) > 0:
                for page in scored_pages:
                    results[page.url] += page.score
    return results


class Result:
    pass


def run_search(query):
    results = search(query)

    ranked_results = list(
        map(lambda x: x[0], sorted(results.items(), key=lambda x: x[1], reverse=True))
    )

    to_return = list()
    for result in ranked_results:
        page = pages.get(result)
        to_add = Result()
        if page is None:
            to_add.url = result
            to_add.title = result
        else:
            to_add.url = page.url
            to_add.title = page.title
        to_return.append(to_add)

    return to_return
