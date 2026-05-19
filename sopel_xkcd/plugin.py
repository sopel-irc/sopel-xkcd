"""sopel-xkcd - Sopel xkcd Plugin

Continued from Sopel 8.0's built-in `xkcd.py` plugin,
https://github.com/sopel-irc/sopel/blob/c1541f419035c8d18aa66bf60fae9f096b4b362d/sopel/builtins/xkcd.py

Copyright 2010, Michael Yanovich (yanovich.net), and Morgan Goose
Copyright 2012, Lior Ramati
Copyright 2013, Elsie Powell (embolalia.com)
Copyright 2026, dgw

Licensed under the Eiffel Forum License 2.

https://sopel.chat
"""
from __future__ import annotations

from json import JSONDecodeError
import logging
import random
import re

import requests

from sopel import plugin, tools


LOGGER = tools.get_logger('xkcd')
PLUGIN_OUTPUT_PREFIX = '[xkcd] '

# used with permission of site owner
# https://bsky.app/profile/jasonbosco.bsky.social/post/3mm7dsbqkjk2n
FINDXKCD_API = 'https://qtg5aekc2iosjh93p.a1.typesense.net/multi_search'


class FindXkcdError(Exception):
    """Generic exception to raise if there was a problem contacting the API."""


class SearchConnectionError(FindXkcdError):
    """Couldn't reach the search endpoint."""


class ResponseFormatError(FindXkcdError):
    """Response format couldn't be parsed."""


class NoResultsError(FindXkcdError):
    """Response could be parsed, but it was empty."""


def get_info(number=None):
    if number:
        url = 'https://xkcd.com/{}/info.0.json'.format(number)
    else:
        url = 'https://xkcd.com/info.0.json'
    data = requests.get(url).json()
    data['url'] = 'https://xkcd.com/' + str(data['num'])
    return data


def findxkcd_search(query):
    params = {
        "use_cache": "true",
        "x-typesense-api-key": "8hLCPSQTYcBuK29zY5q6Xhin7ONxHy99",
    }
    payload = {
        "searches": [
            {
                "query_by": "title,altTitle,transcript,topics,embedding",
                "query_by_weights": "127,80,80,1,1",
                "num_typos": 1,
                "exclude_fields": "embedding",
                "vector_query": "embedding:([], k: 30, distance_threshold: 0.1, alpha: 0.9)",
                "highlight_full_fields": "title,altTitle,transcript,topics,embedding",
                "collection": "xkcd",
                "q": query,
                "facet_by": "publishDateYear,topics",
                "max_facet_values": 100,
                "page": 1,
                "per_page": 5,
            }
        ]
    }
    try:
        response = requests.post(
            FINDXKCD_API,
            params=params,
            json=payload,
            timeout=5,
        )
    except requests.exceptions.ConnectionError as e:
        LOGGER.debug("Unable to reach findxkcd API: %s", e)
        raise SearchConnectionError(str(e))
    except Exception as e:
        LOGGER.debug("Unexpected error calling findxkcd API: %s", e)
        raise FindXkcdError(str(e))

    try:
        hits = response.json()['results'][0]['hits']
        if not hits:
            raise NoResultsError
        first = hits[0]['document']['id']
    except (JSONDecodeError, LookupError):
        msg = "Data format from findxkcd API could not be understood."
        LOGGER.warning(msg)
        LOGGER.debug("Response text: %r", response.text)
        raise ResponseFormatError(msg)

    return first


@plugin.command('xkcd')
@plugin.example(".xkcd 1782", user_help=True)
@plugin.example(".xkcd", user_help=True)
@plugin.output_prefix(PLUGIN_OUTPUT_PREFIX)
def xkcd(bot, trigger):
    """Finds an xkcd comic strip.

    Takes one of 3 inputs:

      * If no input is provided it will return a random comic
      * If numeric input is provided it will return that comic, or the
        nth-latest comic if the number is negative
      * If non-numeric input is provided it will return the first search result
        for those keywords from findxkcd.com

    """
    # get latest comic, for random selection and validating numeric input
    latest = get_info()
    max_int = latest['num']

    # if no input is given (pre - lior's edits code)
    if not trigger.group(2):  # get random comic
        random.seed()
        requested = get_info(random.randint(1, max_int + 1))
    else:
        query = trigger.group(2).strip()
        numbered = re.match(r"^(#|\+|-)?(\d+)$", query)

        if numbered:
            query = int(numbered.group(2))
            if numbered.group(1) == "-":
                query = -query
            return numbered_result(bot, query, latest)
        else:
            # Non-number: search the web.
            if (query.lower() == "latest" or query.lower() == "newest"):
                requested = latest
            else:
                try:
                    number = findxkcd_search(query)
                except NoResultsError:
                    bot.reply("Sorry, I couldn't find any comics for that query.")
                    return
                except FindXkcdError:
                    bot.reply(
                        "A technical problem prevented me from searching. "
                        "Please ask my owner to check my logs.")
                    return

                requested = get_info(number)

    say_result(bot, requested)


def numbered_result(bot, query, latest, commanded=True):
    max_int = latest['num']
    if query > max_int:
        bot.reply(("Sorry, comic #{} hasn't been posted yet. "
                   "The last comic was #{}").format(query, max_int))
        return
    elif query <= -max_int:
        bot.reply(("Sorry, but there were only {} comics "
                   "released yet so far").format(max_int))
        return
    elif abs(query) == 0:
        requested = latest
    elif query == 404 or max_int + query == 404:
        bot.say("404 - Not Found")  # don't error on that one
        return
    elif query > 0:
        requested = get_info(query)
    else:
        # Negative: go back that many from current
        requested = get_info(max_int + query)

    say_result(bot, requested, commanded)


def say_result(bot, result, commanded=True):
    parts = [
        result['title'],
        'Alt-text: ' + result['alt'],
    ]

    if commanded:
        parts.append(result['url'])

    bot.say(' | '.join(parts))


@plugin.url(r'xkcd.com/(\d+)')
@plugin.output_prefix(PLUGIN_OUTPUT_PREFIX)
def get_url(bot, trigger, match):
    latest = get_info()
    numbered_result(bot, int(match.group(1)), latest, commanded=False)


@plugin.url(r'https?://xkcd\.com/?$')
@plugin.output_prefix(PLUGIN_OUTPUT_PREFIX)
def xkcd_main_page(bot, trigger, match):
    latest = get_info()
    numbered_result(bot, 0, latest, commanded=False)
