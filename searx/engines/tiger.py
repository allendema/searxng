# SPDX-License-Identifier: AGPL-3.0-or-later

from typing import TYPE_CHECKING

import re
from random import choice
from datetime import datetime

from searx.utils import extract_text, eval_xpath, eval_xpath_list

from lxml import html

if TYPE_CHECKING:
    import logging

    logger: logging.Logger

# about
about = {
    "website": 'https://www.tiger.ch',
    "wikidata_id": '',
    "official_api_documentation": '',
    "use_official_api": False,
    "require_api_key": False,
    "results": 'HTML',
}

# engine dependent config
categories = ['general', 'web']
paging = True
max_page = 5
time_range_support = False
safesearch = False

base_url = 'https://tiger.ch'

# Set optional extras in settings.yml
extras = {}


def request(query, params):
    """Build search url and set params/cookies/headers"""

    # pylint: disable=line-too-long
    # https://learn.microsoft.com/en-us/dotnet/api/system.web.sessionstate.sessionidmanager?view=netframework-4.8.1&redirectedfrom=MSDN#remarks
    _alphabet = ("a", "b", "c", "d", "e", "f", "g", "0", "1", "2", "3", "4", "5")
    _random_session_id = ''.join(choice(_alphabet) for i in range(24))
    _preferences = '''Tiger.ch=Size=md&Wetter=2&Style=1&Checked=1&Widgets=0-0-0-0,&Full=1&Suche=0&Video=1',"'''

    params['url'] = f'{params.pop("base_url", base_url)}/Websuche.aspx?w={query}&page={params.pop("pageno", 1)}'

    params['headers']['cookie'] = 'ASP.NET_SessionId={}; {}'.format(
        extras.pop("session_id", _random_session_id), extras.pop("preferences", _preferences)
    )
    params['allow_redirects'] = True
    params['max_redirects'] = 1

    return params


def response(resp):
    """Parse response from tiger search request"""

    # use standalone *_xpath's without making use of results_xpath
    # results_xpath = extras.pop('results_xpath', '//table[@id="gS"]//tbody/./tr')

    # if availiable, read xpaths them from extras
    url_xpath = extras.pop('url_xpath', '//*[contains(@class, "btn-block weblink")]/@href')
    title_xpath = extras.pop('title_xpath', '//*[@class="btn-block weblink break"]/text()')
    content_xpath = extras.pop('content_xpath', '//*[contains(@id,"gS_lbB_")]')
    articles_xpath = extras.pop('articles_xpath', '//*[contains(@id, "gS_panNews")]')
    sponsored_xpath = extras.pop('sponsored_xpath', '//*[contains(@id, "panPaid")]')
    suggestion_xpath = extras.pop('suggestion_xpath', '//*[contains(@class, "linkAnders")]')
    correction_xpath = extras.pop('correction_xpath', '//*[contains(@id, "linkSpell")]')

    results = []

    dom = html.fromstring(resp.text)

    for sponsored in dom.xpath(sponsored_xpath):
        sponsored.getparent().remove(sponsored)

    for title, url, content_span in zip(
        eval_xpath(dom, title_xpath),
        eval_xpath(dom, url_xpath),
        eval_xpath(dom, content_xpath),
    ):

        content = extract_text(content_span, allow_none=True)

        # prevent bad results
        if 'Ihre Firma oder Produkte erscheinen...' in (title, content):
            continue
        if url.startswith("/Anmelden"):
            continue

        try:
            potentially_published_date = content[:10]  # type: ignore
            published_date = datetime.fromisoformat(potentially_published_date)
        except ValueError:
            published_date = None

        results.append(
            {
                'url': url,
                'title': title,
                'content': content,
                'thumbnail': None,
                'publishedDate': published_date,
            }
        )

    # also get ocasional articles
    # for title, url, content_span in eval_xpath(dom, articles_xpath):
    # pass

    for suggestion in eval_xpath_list(dom, suggestion_xpath):
        results.append({'suggestion': extract_text(suggestion)})

    for correction in eval_xpath_list(dom, correction_xpath):
        correction_text = extract_text(correction)

        # TODO #FIXME This is empty
        if not correction_text or correction_text == '':
            continue

        results.append({'correction': correction_text})

    return results
