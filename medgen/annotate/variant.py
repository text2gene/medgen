""" Variant-level annotation functions requiring ClinvarDB and Metapub (NCBI/eutils). """

import requests, json, urllib

from metapub.text_mining import is_pmcid, is_ncbi_bookID 
from metapub.pubmedcentral import get_pmid_for_otherid

from ..db.clinvar import ClinVarDB
from ..log import log

##########################################################################################
#
#   Functions
#
##########################################################################################

def _clinvar_variant_accession(hgvs_text):
    """
    See ClinVar FAQ http://www.ncbi.nlm.nih.gov/clinvar/docs/faq/#accs
    :param hgvs_text: c.DNA
    :return: RCVAccession "Reference ClinVar Accession"
    """
    try:
        return ClinVarDB().accession_for_hgvs_text(str(hgvs_text))
    except Exception as err:
        log.debug("no clinvar accession for variant hgvs_text %s " % hgvs_text)

def _clinvar_variant_allele_id(hgvs_text):
    """
    Get the unique AlleleID
    :param hgvs_text: c.DNA
    :return: AlleleID
    """
    try:
        return ClinVarDB().allele_id_for_hgvs_text(hgvs_text)
    except Exception as err:
        log.debug('no clinvar AlleleID for variant hgvs_text %s ' % hgvs_text)

def _clinvar_variant_variation_id(hgvs_text):
    """
    Get the unique VariationID
    :param hgvs_text: c.DNA
    :return: VariationID
    """
    try:
        return ClinVarDB().variation_id_for_hgvs_text(hgvs_text)
    except Exception as err:
        log.debug('no clinvar VariationID for variant hgvs_text %s ' % hgvs_text)

def _clinvar_variant2pubmed(hgvs_text):
    """
    Get PMID for clinvar variants using the AlleleID key.

    Keep GeneReviews book references (NKBxxxx) without argument.

    ONE EXPENSIVE LOOKUP HERE:
    If the citation_source is PubMedCentral, first convert responses to PMID.

    :param hgvs_text: c.DNA
    :return: set(PMIDs and possibly also NBK ids)
    """
    pubmeds = []
    citations = ClinVarDB().var_citations(hgvs_text)
    if citations:
        for cite in citations:
            some_id = cite['citation_id']

            if is_ncbi_bookID(some_id):
                # Todo: convert? drop??
                pubmeds.append(some_id)
            elif is_pmcid(some_id):
                try:
                    pmid = get_pmid_for_otherid(some_id)
                    if pmid is not None:
                        log.debug('found PubMedCentral PMCID %s, converted to PMID %s ', some_id, str(pmid))
                        pubmeds.append(pmid)
                    else:
                        log.debug('PMID not found for PMCID %s; discarding.', some_id)
                except Exception as err:
                    log.debug('error converting PMCID %s: %r', some_id, err)
            elif cite['citation_source'] == 'PubMed':
                pubmeds.append(some_id)

    #return set([int(entry) for entry in pubmeds])
    return set(pubmeds)


def clinvar2pmid_with_accessions(hgvs_list):
    ret = []
    citations = ClinVarDB().var_citations(hgvs_list)
    if citations:
        for cite in citations:
            article_id = cite['citation_id']
            if is_ncbi_bookID(article_id):
                pmid = article_id
            else:
                pmid = article_id if cite['citation_source'] == 'PubMed' else get_pmid_for_otherid(article_id)
            if pmid:
                ret.append({"hgvs_text": cite['HGVS'], "pmid": pmid, "accession": cite['RCVaccession']})
    return ret


##########################################################################################
#
# API
#
##########################################################################################

ClinvarAccession   = _clinvar_variant_accession
ClinvarAlleleID    = _clinvar_variant_allele_id
ClinvarPubmeds     = _clinvar_variant2pubmed
ClinvarVariationID = _clinvar_variant_variation_id
