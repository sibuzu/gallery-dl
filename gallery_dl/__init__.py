# -*- coding: utf-8 -*-

# Copyright 2014-2017 Mike Fährmann
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.

from __future__ import unicode_literals, print_function

__author__ = "Mike Fährmann"
__copyright__ = "Copyright 2014-2017 Mike Fährmann"
__license__ = "GPLv2"
__maintainer__ = "Mike Fährmann"
__email__ = "mike_faehrmann@web.de"

import sys

if sys.hexversion < 0x3030000:
    print("Python 3.3+ required", file=sys.stderr)
    sys.exit(1)

import logging
from . import version, config, option, extractor, job, exception

__version__ = version.__version__
log = logging.getLogger("gallery-dl")


def initialize_logging():
    # convert levelnames to lowercase
    for level in (10, 20, 30, 40, 50):
        name = logging.getLevelName(level)
        logging.addLevelName(level, name.lower())
    # setup basic logging to stderr
    formatter = logging.Formatter("[%(name)s][%(levelname)s] %(message)s")
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.addHandler(handler)


def sanatize_input(file):
    for line in file:
        line = line.strip()
        if line:
            yield line


def main():
    try:
        initialize_logging()
        config.load()

        parser = option.build_parser()
        args = parser.parse_args()

        if args.cfgfiles:
            config.load(*args.cfgfiles, strict=True)
        if args.yamlfiles:
            config.load(*args.yamlfiles, format="yaml", strict=True)
        for key, value in args.options:
            config.set(key, value)

        if args.list_modules:
            for module_name in extractor.modules:
                print(module_name)
        elif args.list_extractors:
            for extr in extractor.extractors():
                print(extr.__name__)
                if extr.__doc__:
                    print(extr.__doc__)
                if hasattr(extr, "test") and extr.test:
                    print("Example:", extr.test[0][0])
                print()
        else:
            if not args.urls and not args.inputfile:
                parser.error("the following arguments are required: URL")

            if args.list_urls:
                jobtype = job.UrlJob
                jobtype.maxdepth = args.list_urls
            elif args.list_keywords:
                jobtype = job.KeywordJob
            else:
                jobtype = job.DownloadJob

            urls = args.urls
            if args.inputfile:
                try:
                    if args.inputfile == "-":
                        file = sys.stdin
                    else:
                        file = open(args.inputfile)
                    import itertools
                    urls = itertools.chain(urls, sanatize_input(file))
                except OSError as err:
                    log.error(err)

            urlbase = "https://danbooru.donmai.us/posts/"
            i = int(urls[0].split('/')[-1])
            if True:       
                try:
                    for j in range(1000):
                        idx = i * 1000 + j + 1
                        url = urlbase + str(idx)
                        if j == 0:
                            jobx = jobtype(url)
                        else:
                            jobx.handle_queue(url)
                    jobx.run()
                except exception.NoExtractorError:
                    log.error("No suitable extractor found for '%s'", url)

    except KeyboardInterrupt:
        print("\nKeyboardInterrupt", file=sys.stderr)
    except BrokenPipeError:
        pass
    except IOError as err:
        import errno
        if err.errno != errno.EPIPE:
            raise
