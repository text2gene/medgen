#### metapub
from metapub import PubMedFetcher, PubMedArticle
from medgen.db.medgen import MedGenDB

##########################################################################################
#
#  Functions
#
##########################################################################################

def _pubmed_pmid_to_article(pmid):
    """
    Use NCBI eutils to fetch pubmed article information.

    :param pmid: int or str
    :return: PubMedArticle
    """
    return PubMedFetcher().article_by_pmid(str(pmid))

def _pubmed_central_pmcid_to_article(pmcid):
    """
    Specific to PMC PubMed Central.
    Use NCBI eutils to fetch pubmed article information.

    :param pmcid:
    :return: PubMedArticle
    """
    return PubMedFetcher().article_by_pmcid(str(pmcid))

##########################################################################################
#
#       API
#
##########################################################################################
PMID2Article = _pubmed_pmid_to_article
PMCID2Article = _pubmed_central_pmcid_to_article
