# -*- coding: utf-8  -*-
#
# Copyright (C) 2009, 2010, 2011 by Ben Kurtovic <ben.kurtovic@verizon.net>
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

import logging

from earwigbot.config import config
from earwigbot import wiki

__all__ = ["BaseTask"]

class BaseTask(object):
    """A base class for bot tasks that edit Wikipedia."""
    name = None
    number = 0

    def __init__(self):
        """Constructor for new tasks.

        This is called once immediately after the task class is loaded by
        the task manager (in tasks._load_task()).
        """
        pass

    def _setup_logger(self):
        """Set up a basic module-level logger."""
        logger_name = ".".join(("earwigbot", "tasks", self.name))
        self.logger = logging.getLogger(logger_name)
        self.logger.setLevel(logging.DEBUG)

    def run(self, **kwargs):
        """Main entry point to run a given task.

        This is called directly by tasks.start() and is the main way to make a
        task do stuff. kwargs will be any keyword arguments passed to start()
        which are entirely optional.

        The same task instance is preserved between runs, so you can
        theoretically store data in self (e.g.
        start('mytask', action='store', data='foo')) and then use it later
        (e.g. start('mytask', action='save')).
        """
        pass

    def make_summary(self, comment):
        """Makes an edit summary by filling in variables in a config value.

        config.wiki["summary"] is used, where $2 is replaced by the main
        summary body, given as a method arg, and $1 is replaced by the task
        number.

        If the config value is not found, we just return the arg as-is.
        """
        try:
            summary = config.wiki["summary"]
        except KeyError:
            return comment
        return summary.replace("$1", str(self.number)).replace("$2", comment)

    def shutoff_enabled(self, site=None):
        """Returns whether on-wiki shutoff is enabled for this task.

        We check a certain page for certain content. This is determined by
        our config file: config.wiki["shutoff"]["page"] is used as the title,
        with $1 replaced by our username and $2 replaced by the task number,
        and config.wiki["shutoff"]["disabled"] is used as the content.

        If the page has that content or the page does not exist, then shutoff
        is "disabled", meaning the bot is supposed to run normally, and we
        return False. If the page's content is something other than what we
        expect, shutoff is enabled, and we return True.

        If a site is not provided, we'll try to use self.site if it's set.
        Otherwise, we'll use our default site.
        """
        if not site:
            try:
                site = self.site
            except AttributeError:
                site = wiki.get_site()

        try:
            cfg = config.wiki["shutoff"]
        except KeyError:
            return False
        title = cfg.get("page", "User:$1/Shutoff/Task $2")
        username = site.get_user().name()
        title = title.replace("$1", username).replace("$2", str(self.number))
        page = site.get_page(title)

        try:
            content = page.get()
        except wiki.PageNotFoundError:
            return False
        if content == cfg.get("disabled", "run"):
            return False

        self.logger.warn("Emergency task shutoff has been enabled!")
        return True