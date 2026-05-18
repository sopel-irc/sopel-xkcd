# sopel-xkcd

xkcd plugin for Sopel IRC bots.

## Features & Usage

This plugin provides lookup commands and automatic URL expansion for
[xkcd](https://xkcd.com/) comics in Sopel IRC bots.

- `.xkcd` — Get a random comic
- `.xkcd <number>` — Get a specific comic by number (e.g., `.xkcd 303`)
- `.xkcd 0` — Get the most recent comic
- `.xkcd -<n>` — Get the nth-latest comic (e.g., `.xkcd -1` for the previous comic)
- `.xkcd <keywords>` — Search for a comic by keywords (e.g., `.xkcd battery staple`)
- Posting an `xkcd.com` URL in chat will fetch the comic's title and alt-text

## Installation

After installing Sopel, install this plugin with `pip`:

```shell
pip install sopel-xkcd
```

## Configuration

No configuration is required.

## Credits

This is a continuation of Sopel 8.0's built-in `xkcd` plugin. You can find the
original file [in Sopel's history][upstream-src].

[//]: # (upstream-src is also used in NEWS entry for 1.0.0)
[upstream-src]: https://github.com/sopel-irc/sopel/blob/c1541f419035c8d18aa66bf60fae9f096b4b362d/sopel/builtins/xkcd.py
