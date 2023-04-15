# SPDX-License-Identifier: AGPL-3.0-or-later
"""Petalsearch Images

"""

from json import loads
from urllib.parse import urlencode
from datetime import datetime

from lxml import html

from searx.utils import extract_text

about = {
    "website": "https://petalsearch.com/",
    "wikidata_id": "Q104399280",
    "official_api_documentation": False,
    "use_official_api": False,
    "require_api_key": False,
    "results": "JSON",
}

categories = ["images"]
paging = True

safesearch = True
safesearch_table = {0: "off", 1: "moderate", 2: "on"}


base_url = "https://petalsearch.com/"
search_string = "search?{query}&channel=image&ps=50&pn={page}&region={lang}&ss_mode={safesearch}&ss_type=normal"


def request(query, params):

    search_path = search_string.format(
        query=urlencode({"query": query}),
        page=params["pageno"],
        lang=params["language"].lower(),
        safesearch=safesearch_table[params["safesearch"]],
    )

    params["url"] = base_url + search_path
    params["headers"] = {
        "User-Agent": ("Mozilla/5.0 (Linux; Android 7.0;) AppleWebKit/537.36 (KHTML, like Gecko)"
                       "Mobile Safari/537.36 (compatible; PetalBot;+https://webmaster.petalsearch.com/site/petalbot)")
    }

    return params


def response(resp):
    results = []

    tree = html.fromstring(resp.text)

    found_json = tree.find('.//*[@type="application/json"]')
    json_content = extract_text(found_json)

    data = loads(json_content)

    for result in data["imagePreviewData"]["data"]:
        url = result["link"]
        title = result["title"]
        thumbnail_src = result["image"]
        date_from_api = result.get("publishTime")

        pic_dict = result.get("itemContent")

        width = pic_dict.get("width")
        height = pic_dict.get("height")
        img_src = pic_dict.get("real_url")

        if img_src is None:
            continue

        if date_from_api != "0":
            publishedDate = datetime.fromtimestamp(int(date_from_api))

        results.append(
            {
                "template": "images.html",
                "url": url,
                "title": title,
                "img_src": img_src,
                "thumbnail_src": thumbnail_src,
                "width": width,
                "height": height,
                "publishedDate": publishedDate,
                "upstream_extra": pic_dict,
            }
        )

    for suggestion in data["relatedSearchList"]:
        results.append({"suggestion": suggestion})

    return results
