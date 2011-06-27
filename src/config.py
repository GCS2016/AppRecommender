#!/usr/bin/env python
"""
    config - python module for configuration options.
"""
__author__ = "Tassia Camoes Araujo <tassia@gmail.com>"
__copyright__ = "Copyright (C) 2011 Tassia Camoes Araujo"
__license__ = """
    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import getopt
import sys
import os
from logging import *
import logging.handlers

from ConfigParser import *

class Config():
    """
    Class to handle configuration options.
    """
    def __init__(self):
        """
        Set configuration options.
        """
        self.debug = 0
        self.verbose = 0
        self.output = "/dev/null"
        self.config = None
        self.tags_db = "/var/lib/debtags/package-tags"
        self.tags_index = "~/.app-recommender/debtags_index"
        self.axi = "/var/lib/apt-xapian-index/index"
        self.axi_values = "/var/lib/apt-xapian-index/values"
        self.popcon_index = "~/.app-recommender/popcon_index"
        self.popcon_dir = "~/.app-recommender/popcon_dir"
        self.clusters_dir = "~/.app-recommender/clusters_dir"
        self.strategy = "cb"    # defaults to the cheapest one
        self.weight = "bm25"
        self.load_options()
        self.set_logger()

    def usage(self):
        """
        Print usage help.
        """
        print "\n [ general ]"
        print "  -h, --help              Print this help"
        print "  -d, --debug             Set logging level to debug."
        print "  -v, --verbose           Set logging level to verbose."
        print "  -o, --output=PATH       Path to file to save output."
        print "  -c, --config=PATH       Path to configuration file."
        print ""
        print " [ recommender ]"
        print "  -a, --axi=PATH          Path to Apt-xapian-index."
        print "  -p, --popconindex=PATH  Path to popcon dedicated index."
        print "  -m, --popcondir=PATH    Path to popcon submissions dir."
        print "  -l, --clustersdir=PATH  Path to popcon clusters dir."
        print "  -w, --weight=OPTION     Search weighting scheme."
        print "  -s, --strategy=OPTION   Recommendation strategy."
        print ""
        print " [ weight options ] "
        print "  trad = traditional probabilistic weighting "
        print "  bm25 = bm25 weighting scheme "
        print ""
        print " [ strategy options ] "
        print "  cb = content-based "
        print "  cbt = content-based using only tags as content "
        print "  cbd = content-based using only package descriptions as content "
        print "  col = collaborative "
        #print "  colct = collaborative through tags content "
        #print "  colcp = collaborative through package descriptions content "

    def read_option(self, section, option):
        """
        Read option from configuration file if it is defined there or return
        default value.
        """
        var = "self.%s" % option
        if self.config.has_option(section, option):
            return self.config.get(section, option)
        else:
            return eval(var)

    def load_options(self):
        """
        Load options from configuration file and command line arguments.
        """
        try:
            self.config = ConfigParser()
            self.config.read(['/etc/apprecommender/recommender.conf',
                              os.path.expanduser('~/apprecommender.rc')])
        except (MissingSectionHeaderError), err:
            logging.error("Error in config file syntax: %s", str(err))
            os.abort()

        self.debug = self.read_option('general', 'debug')
        self.debug = self.read_option('general', 'verbose')
        self.output_filename = self.read_option('general', 'output')
        self.config = self.read_option('general', 'config')

        self.axi = self.read_option('recommender', 'axi')
        self.popcon_index = self.read_option('recommender', 'popcon_index')
        self.popcon_dir = self.read_option('recommender', 'popcon_dir')
        self.clusters_dir = self.read_option('recommender', 'clusters_dir')
        self.weight = self.read_option('recommender', 'weight')
        self.strategy = self.read_option('recommender', 'strategy')

        short_options = "hdvo:c:a:p:m:l:w:s:"
        long_options = ["help", "debug", "verbose", "output=", "config=",
                        "axi=", "popconindex=", "popcondir=", "clustersdir=",
                        "weight=", "strategy="]
        try:
            opts, args = getopt.getopt(sys.argv[1:], short_options,
                                       long_options)
        except getopt.GetoptError as error:
            self.set_logger()
            logging.error("Bad syntax: %s" % str(error))
            self.usage()
            sys.exit()

        for o, p in opts:
            if o in ("-h", "--help"):
                self.usage()
                sys.exit()
            elif o in ("-d", "--debug"):
                self.debug = 1
            elif o in ("-v", "--verbose"):
                self.verbose = 1
            elif o in ("-o", "--output"):
                self.output = p
            elif o in ("-c", "--config"):
                self.config = p
            elif o in ("-a", "--axi"):
                self.axi = p + "/index"
                self.axi_values = p + "/values"
            elif o in ("-p", "--popconindex"):
                self.popcon_index = p
            elif o in ("-m", "--popcondir"):
                self.popcon_dir = p
            elif o in ("-l", "--clustersdir"):
                self.popcon_dir = p
            elif o in ("-w", "--weight"):
                self.weight = p
            elif o in ("-s", "--strategy"):
                self.strategy = p
            else:
                assert False, "unhandled option"

    def set_logger(self):
        """
        Configure application logger and log level.
        """
        self.logger = getLogger('')  # root logger is used by default
        self.logger.setLevel(DEBUG)

        if self.debug == 1:
            log_level = DEBUG
        elif self.verbose == 1:
            log_level = INFO
        else:
            log_level = WARNING

        console_handler = StreamHandler(sys.stdout)
        console_handler.setFormatter(Formatter('%(levelname)s: %(message)s'))
        console_handler.setLevel(log_level)
        self.logger.addHandler(console_handler)

        file_handler = logging.handlers.RotatingFileHandler(self.output,
                                                            maxBytes=5000,
                                                            backupCount=5)
        log_format = '%(asctime)s AppRecommender %(levelname)-8s %(message)s'
        file_handler.setFormatter(Formatter(log_format))
        file_handler.setLevel(log_level)
        self.logger.addHandler(file_handler)
