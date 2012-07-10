# -*- coding: utf-8  -*-
#
# Copyright (C) 2009-2012 Ben Kurtovic <ben.kurtovic@verizon.net>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import re

from earwigbot import exceptions
from earwigbot.commands import Command

class Dictionary(Command):
    """Define words and stuff."""
    name = "dictionary"
    commands = ["dict", "dictionary", "define"]

    def process(self, data):
        if not data.args:
            self.reply(data, "what do you want me to define?")
            return

        term = " ".join(data.args)
        lang = self.bot.wiki.get_site().lang
        try:
            defined = self.define(term, lang)
        except exceptions.APIError:
            msg = "cannot find a {0}-language Wiktionary."
            self.reply(data, msg.format(lang))
        else:
            self.reply(data, defined.encode("utf8"))

    def define(self, term, lang):
        try:
            site = self.bot.wiki.get_site(project="wiktionary", lang=lang)
        except exceptions.SiteNotFoundError:
            site = self.bot.wiki.add_site(project="wiktionary", lang=lang)

        page = site.get_page(term)
        try:
            entry = page.get()
        except (exceptions.PageNotFoundError, exceptions.InvalidPageError):
            return "no definition found."

        languages = self.get_languages(entry)
        if not languages:
            return u"couldn't parse {0}!".format(page.url)

        result = []
        for lang, section in sorted(languages.items()):
            this = u"({0}) {1}".format(lang, self.get_definition(section))
            result.append(this)
        return u"; ".join(result)

    def get_languages(self, entry):
        regex = r"(?:\A|\n)==\s*([a-zA-Z0-9_ ]*?)\s*==(?:\Z|\n)"
        split = re.split(regex, entry)
        if len(split) % 2 == 0:
            return None

        split.pop(0)
        languages = {}
        for i in xrange(0, len(split), 2):
            languages[split[i]] = split[i + 1]
        return languages

    def get_definition(self, section):
        parts_of_speech = {
            "v.": "Verb",
            "n.": "Noun",
            "pron.": "Pronoun",
            "adj.": "Adjective",
            "adv.": "Adverb",
            "prep.": "Preposition",
            "conj.": "Conjunction",
            "inter.": "Interjection",
            "symbol": "Symbol",
            "suffix": "Suffix",
            "initialism": "Initialism",
            "phrase": "Phrase",
            "proverb": "Proverb",
            "prop. n.": "Proper noun",
            "abbr.": "\{\{abbreviation\}\}",
        }
        defs = []
        for part, fullname in parts_of_speech.iteritems():
            if re.search("===\s*" + fullname + "\s*===", section):
                regex = "===\s*" + fullname + "\s*===(.*?)(?:(?:===)|\Z)"
                body = re.findall(regex, section, re.DOTALL)
                if body:
                    definition = self.parse_body(body[0])
                    if definition:
                        msg = u"\x02{0}\x0F {1}"
                        defs.append(msg.format(part, definition))

        return "; ".join(defs)

    def parse_body(self, body):
        senses = []
        for line in body.splitlines():
            line = line.strip()
            if re.match("#\s*[^:*]", line):
                line = re.sub("\[\[(.*?)\|(.*?)\]\]", r"\2", line)
                line = self.strip_templates(line)
                line = line[1:].replace("'''", "").replace("''", "")
                line = line.replace("[[", "").replace("]]", "")
                senses.append(line.strip())

        if not senses:
            return None
        if len(senses) == 1:
            return senses[0]

        result = []  # Number the senses incrementally
        for i, sense in enumerate(senses):
            result.append(u"{0}. {1}".format(i + 1, sense))
        return " ".join(result)

    def strip_templates(self, line):
        line = list(line)
        stripped = ""
        depth = 0
        while line:
            this = line.pop(0)
            if line:
                next = line[0]
            else:
                next = ""
            if this == "{" and next == "{":
                line.pop(0)
                depth += 1
            elif this == "}" and next == "}":
                line.pop(0)
                depth -= 1
            elif depth == 0:
                stripped += this
        return stripped
