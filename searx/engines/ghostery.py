# SPDX-License-Identifier: AGPL-3.0-or-later
"""ghosterysearch.com which itself uses search.brave.com but maybe more chill captcha (10 reqs per 10 min)"""

from typing import Any, TYPE_CHECKING

from urllib.parse import urlencode, urlparse
from dateutil import parser

from searx.enginelib.traits import EngineTraits
from searx.utils import (
    extract_text,
    eval_xpath,
    extract_url,
    get_embeded_stream_url,
)

from lxml import html

if TYPE_CHECKING:
    import logging

    logger: logging.Logger

traits: EngineTraits

about = {
    "website": 'https://ghosterysearch.com/',
    "wikidata_id": '',
    "official_api_documentation": None,
    "use_official_api": False,
    "require_api_key": False,
    "results": 'HTML',
}

base_url = 'https://ghosterysearch.com/'


send_accept_language_header = True
paging = True
max_page = 10
"""upstream-of-upstream itself supports max 10."""

safesearch = False
time_range_support = False
extras: dict = None


def request(query, params):

    # Don't accept br encoding / see https://github.com/searxng/searxng/pull/1787
    params['headers']['Accept-Encoding'] = 'gzip, deflate'

    params['url'] = f"{base_url}search?q={query}&page={params.get('pageno', 1)}"

    engine_region = params['searxng_locale']
    # https://ghosterysearch.com/scripts/settings.js?v=d17fa069c4fc7b08f3cf96916b881589%27
    if engine_region == 'all':
        params['cookies']['ctry'] = ''
    else:
        params['cookies']['ctry'] = engine_region.rpartition('-')[2].upper()  # type: ignore

    params['cookies']['noads'] = 'true'


def response(resp):

    results = []
    dom = html.fromstring(resp.text)

    # _results_xpath = extras.pop('results_xpath', '//*[@class="results"]/ol/*[contains(@class, "result")]')

    title_xpath = extras.pop('title_xpath', '//h2/a')
    url_xpath = extras.pop('url_xpath', '//h2/a/@href')
    content_xpath = extras.pop('content_xpath', '//*/*[@class="description"]/p')

    for title_element, url_element, content_element in zip(
        eval_xpath(dom, title_xpath),
        eval_xpath(dom, url_xpath),
        eval_xpath(dom, content_xpath),
    ):

        url = extract_url(url_element, base_url=base_url)
        item = {
            'title': extract_text(title_element),
            'url': url,
            'content': extract_text(content_element),
            'thumbnail': None,
            'publishedDate': None,
        }

        iframe_src = get_embeded_stream_url(url)
        if iframe_src:
            item.update({'iframe_src': iframe_src, 'template': 'videos.html'})

        results.append(item)

    return results


'''
def fetch_traits(engine_traits: EngineTraits):
    from searx.engines.brave import fetch_traits as upstream_fetch_traits
    """Fetch :ref:`languages <brave languages>` and :ref:`regions <brave
    regions>` from Brave (upstream)."""

    return upstream_fetch_traits(engine_traits=engine_traits)
'''
