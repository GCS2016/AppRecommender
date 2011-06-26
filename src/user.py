#!/usr/bin/env python
"""
    user - python module for classes and methods related to recommenders' users.
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

import random
import commands
import xapian
import logging
import apt
from singleton import Singleton
import data

class FilterTag(xapian.ExpandDecider):
    """
    Extend xapian.ExpandDecider to consider only tag terms.
    """
    def __call__(self, term):
        """
        Return true if the term is a tag, else false.
        """
        return term.startswith("XT")

class FilterDescription(xapian.ExpandDecider):
    """
    Extend xapian.ExpandDecider to consider only package description terms.
    """
    def __call__(self, term):
        """
        Return true if the term is a tag, else false.
        """
        return (term.islower())

class DemographicProfile(Singleton):
    def __init__(self):
        self.admin   = set(["admin", "hardware", "mail", "protocol",
                            "network", "security", "web", "interface::web"])
        self.devel   = set(["devel", "role::devel-lib", "role::shared-lib"])
        self.desktop = set(["x11", "accessibility", "game", "junior", "office",
                            "interface::x11"])
        self.art     = set(["field::arts", "sound"])
        self.science = set(["science", "biology", "field::astronomy",
                            "field::aviation",  "field::biology",
                            "field::chemistry", "field::eletronics",
                            "field::finance", "field::geography",
                            "field::geology", "field::linguistics",
                            "field::mathematics", "field::medicine",
                            "field::meteorology", "field::physics",
                            "field::statistics"])

    def __call__(self,profiles_set):
        demographic_profile = set()
        for profile in profiles_set:
            demographic_profile = (demographic_profile | eval("self."+profile,{},{"self":self}))
        return demographic_profile

class User:
    """
    Define a user of a recommender.
    """
    def __init__(self,item_score,user_id=0,demo_profiles_set=0):
        """
        Set initial user attributes. pkg_profile gets the whole set of items,
        a random user_id is set if none was provided and the demographic
        profile defaults to 'desktop'.
        """
        self.item_score = item_score
        self.pkg_profile = self.items()

        if user_id:
            self.id = user_id
        else:
            random.seed()
            self.id = random.getrandbits(128)

        if not demo_profiles_set:
            profiles_set = set(["desktop"])
        self.set_demographic_profile(profiles_set)

    def items(self):
        """
        Return the set of user items.
        """
        return self.item_score.keys()

    def set_demographic_profile(self,profiles_set):
        """
        Set demographic profle based on labels in 'profiles_set'.
        """
        self.demographic_profile = DemographicProfile()(profiles_set)

    def profile(self,items_repository,content,size):
        """
        Get user profile for a specific type of content: packages tags,
        description or both (full_profile)
        """
        if content == "tag": return self.tag_profile(items_repository,size)
        if content == "desc": return self.desc_profile(items_repository,size)
        if content == "full": return self.full_profile(items_repository,size)

    def tag_profile(self,items_repository,size):
        """
        Return most relevant tags for a list of packages.
        """
        enquire = xapian.Enquire(items_repository)
        matches = data.axi_search_pkgs(items_repository,self.pkg_profile)
        rset_packages = xapian.RSet()
        for m in matches:
            rset_packages.add_document(m.docid)
        # statistically good differentiators
        eset_tags = enquire.get_eset(size, rset_packages, FilterTag())
        profile = [res.term for res in eset_tags]
        return profile

    def desc_profile(self,items_repository,size):
        """
        Return most relevant keywords for a list of packages based on their
        text descriptions.
        """
        enquire = xapian.Enquire(items_repository)
        matches = data.axi_search_pkgs(items_repository,self.pkg_profile)
        rset_packages = xapian.RSet()
        for m in matches:
            rset_packages.add_document(m.docid)
        eset_keywords = enquire.get_eset(size, rset_packages,
                                         FilterDescription())
        profile = [res.term for res in eset_keywords]
        return profile

    def full_profile(self,items_repository,size):
        """
        Return most relevant tags and keywords for a list of packages based
        their tags and descriptions.
        """
        tag_profile = self.tag_profile(items_repository,size)[:size/2]
        desc_profile = self.desc_profile(items_repository,size)[:size/2]
        return tag_profile+desc_profile

    def maximal_pkg_profile(self):
        """
        Return list of packages that are not dependence of any other package in
        the list.
        """
        cache = apt.Cache()
        old_profile_size = len(self.pkg_profile)
        for p in self.pkg_profile[:]:     #iterate list copy
            try:
                if cache.has_key(p):
                    pkg = cache[p]
                    if pkg.candidate:
                        for dep in pkg.candidate.dependencies:
                            for or_dep in dep.or_dependencies:
                                if or_dep.name in self.pkg_profile:
                                    self.pkg_profile.remove(or_dep.name)
            except:
                logging.debug("Disconsidering package not found in cache: %s"
                              % p)
        profile_size = len(self.pkg_profile)
        logging.info("Reduced packages profile size from %d to %d." %
                     (old_profile_size, profile_size))
        return self.pkg_profile

class LocalSystem(User):
    """
    Extend the class User to consider the packages installed on the local
    system as the set of selected itens.
    """
    def __init__(self):
        """
        Set initial parameters.
        """
        item_score = {}
        dpkg_output = commands.getoutput('/usr/bin/dpkg --get-selections')
        for line in dpkg_output.splitlines():
            pkg = line.split('\t')[0]
            item_score[pkg] = 1
        User.__init__(self,item_score)

    def no_auto_pkg_profile(self):
        """
        Return list of packages voluntarily installed.
        """
        cache = apt.Cache()
        old_profile_size = len(self.pkg_profile)
        for p in self.pkg_profile[:]:     #iterate list copy
            try:
                if cache.has_key(p):
                    pkg = cache[p]
                    if pkg.is_auto_installed:
                        self.pkg_profile.remove(p)
            except:
                logging.debug("Disconsidering package not found in cache: %s"
                              % p)
        profile_size = len(self.pkg_profile)
        logging.info("Reduced packages profile size from %d to %d." %
                     (old_profile_size, profile_size))
