#!/usr/bin/env python
"""
    strategy - python module for classes and methods related to recommendation
               strategies.
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

import xapian
from singleton import Singleton
import recommender
from data import *

class PkgMatchDecider(xapian.MatchDecider):
    """
    Extend xapian.MatchDecider to not consider installed packages.
    """
    def __init__(self, pkgs_list):
        """
        Set initial parameters.
        """
        xapian.MatchDecider.__init__(self)
        self.pkgs_list = pkgs_list

    def __call__(self, doc):
        """
        True if the package is not already installed.
        """
        return doc.get_data() not in self.pkgs_list

class UserMatchDecider(xapian.MatchDecider):
    """
    Extend xapian.MatchDecider to match similar profiles.
    """

    def __init__(self, profile):
        """
        Set initial parameters.
        """
        xapian.MatchDecider.__init__(self)
        self.profile = profile

    def __call__(self, doc):
        """
        True if the user has more the half of packages from profile.
        """
        match=0
        for term in doc:
            if term.term in self.profile:
                match = match+1
        return (match >= len(self.profile)/2)

class PkgExpandDecider(xapian.ExpandDecider):
    """
    Extend xapian.ExpandDecider to consider packages only.
    """
    def __call__(self, term):
        """
        True if the term is a package.
        """
        # [FIXME] return term.startswith("XP")
        return not term.startswith("XT")

class TagExpandDecider(xapian.ExpandDecider):
    """
    Extend xapian.ExpandDecider to consider tags only.
    """
    def __call__(self, term):
        """
        True if the term is a tag.
        """
        return term.startswith("XT")

class RecommendationStrategy:
    """
    Base class for recommendation strategies.
    """
    pass

class ContentBasedStrategy(RecommendationStrategy):
    """
    Content-based recommendation strategy based on Apt-xapian-index.
    """
    def __init__(self,content,profile_size=50):
        self.description = "Content-based"
        self.content = content
        self.profile_size = profile_size

    def run(self,rec,user,limit):
        """
        Perform recommendation strategy.
        """
        profile = user.profile(rec.items_repository,self.content,
                               self.profile_size)
        # prepair index for querying user profile
        query = xapian.Query(xapian.Query.OP_OR,profile)
        enquire = xapian.Enquire(rec.items_repository)
        enquire.set_weighting_scheme(rec.weight)
        enquire.set_query(query)
        try:
            # retrieve matching packages
            mset = enquire.get_mset(0, limit, None, PkgMatchDecider(user.items()))
        except xapian.DatabaseError as error:
            logging.critical("Content-based strategy: "+error.get_msg())
        # compose result dictionary
        item_score = {}
        for m in mset:
            item_score[m.document.get_data()] = m.weight
        return recommender.RecommendationResult(item_score)

class CollaborativeStrategy(RecommendationStrategy):
    """
    Colaborative recommendation strategy.
    """
    def __init__(self,k,clustering=1):
        self.description = "Collaborative"
        self.clustering = clustering
        self.neighbours = k

    def run(self,rec,user,result_size):
        """
        Perform recommendation strategy.
        """
        profile = user.pkg_profile
        # prepair index for querying user profile
        query = xapian.Query(xapian.Query.OP_OR,profile)
        if self.clustering:
            enquire = xapian.Enquire(rec.clustered_users_repository)
        else:
            enquire = xapian.Enquire(rec.users_repository)
        enquire.set_weighting_scheme(rec.weight)
        enquire.set_query(query)
        try:
            # retrieve matching users
            mset = enquire.get_mset(0, self.neighbours)
        except xapian.DatabaseError as error:
            logging.critical("Collaborative strategy: "+error.get_msg())
        rset = xapian.RSet()
        logging.debug("Neighborhood composed by the following users (by hash)")
        for m in mset:
            rset.add_document(m.document.get_docid())
            logging.debug(m.document.get_data())
        # retrieve most relevant packages
        eset = enquire.get_eset(result_size,rset,PkgExpandDecider())
        # compose result dictionary
        item_score = {}
        for package in eset:
            item_score[package.term.lstrip("XP")] = package.weight
        return recommender.RecommendationResult(item_score)

class DemographicStrategy(RecommendationStrategy):
    """
    Recommendation strategy based on demographic data.
    """
    def __init__(self):
        self.description = "Demographic"
        logging.debug("Demographic recommendation not yet implemented.")
        raise Error

    def run(self,user,items_repository):
        """
        Perform recommendation strategy.
        """
        pass

class KnowledgeBasedStrategy(RecommendationStrategy):
    """
    Knowledge-based recommendation strategy.
    """
    def __init__(self):
        self.description = "Knowledge-based"
        logging.debug("Knowledge-based recommendation not yet implemented.")
        raise Error

    def run(self,user,knowledge_repository):
        """
        Perform recommendation strategy.
        """
        pass

class ReputationHeuristic(Singleton):
    """
    Abstraction for diferent reputation heuristics.
    """
    pass

class BugsHeuristic(ReputationHeuristic):
    """
    Reputation heuristic based on quantity of open bugs.
    """
    pass

class RCBugsHeuristic(ReputationHeuristic):
    """
    Reputation heuristic based on quantity of RC bugs.
    """
    pass

class PopularityHeuristic(ReputationHeuristic):
    """
    Reputation heuristic based on popularity of packages.
    """
    pass

class ItemReputationStrategy(RecommendationStrategy):
    """
    Recommendation strategy based on items reputation.
    """
    def __init__(self):
        self.description = "Item reputation"
        logging.debug("Item reputation recommendation not yet implemented.")
        raise Error

    def run(self,items_list,heuristic):
        """
        Perform recommendation strategy.
        """
        pass
