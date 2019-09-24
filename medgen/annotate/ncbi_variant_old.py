import requests, json, urllib

from metapub.text_mining import is_pmcid, is_ncbi_bookID 
from metapub.pubmedcentral import get_pmid_for_otherid

from ..db.clinvar import ClinVarDB
from ..log import log, IS_DEBUG_ENABLED

##########################################################################################
#
#   Functions
#
##########################################################################################


def _ncbi_variant_report_service(hgvs_text):
    """
    Return results from API query to the NCBI Variant Reporter Service
    See documentation at:
    http://www.ncbi.nlm.nih.gov/variation/tools/reporter
    :param hgvs_text: ( c.DNA | r.RNA | p.Protein | g.Genomic )
    :return: JSON (dictionary)
    """
    #r = requests.post("http://www.ncbi.nlm.nih.gov/projects/SNP/VariantAnalyzer/var_rep.cgi", data={"annot1": hgvs_text})
    hgvs_text = str(hgvs_text)
    r = requests.get("http://www.ncbi.nlm.nih.gov/projects/SNP/VariantAnalyzer/var_rep.cgi?annot1={}".format(urllib.parse.quote(hgvs_text)))
    res = r.text

    if 'Error' in res:
        error_str = 'An error occurred when using the NCBI Variant Report Service: "{}"\n'.format(res)
        error_str += 'To reproduce, visit: http://www.ncbi.nlm.nih.gov/projects/SNP/VariantAnalyzer/var_rep.cgi?annot1={}'.format(hgvs_text)
        raise RuntimeError(error_str)

    if IS_DEBUG_ENABLED:
        log.debug(res)

    res = res.split('\n')
    res = filter(
        lambda x: x != '' and not str.startswith(str(x), '.') and not str.startswith(str(x), '##') and not str.startswith(str(x), "Submitted"),
        res)
    res = map(lambda x: x.split('\t'), res)
    keys = map(lambda x: x.strip('# '), res[0])
    values = res[1:]
    res = map(lambda x: dict(zip(keys, x)), values)
    for r in res:
        if r.has_key('PMIDs'):
            if len(r['PMIDs']) == 0:
                r['PMIDs'] = []
            else:
                r['PMIDs'] = r.get('PMIDs').replace(', ', ';').split(';')

    return res


def _ncbi_variant_pubmeds(hgvs_text=None):
    """
    Retrieve PMIDs for a variant from the NCBI Variant Reporter Service
    :param hgvs_text:  ( c.DNA | r.RNA | p.Protein | g.Genomic )
    :return: list(PMID)
    """
    _report  = _ncbi_variant_report_service(hgvs_text)
    _pubmeds = None

    for _row in _report:
        _pubmeds = _row['PMIDs']
        if _pubmeds is not None:
            for _pmid in _pubmeds:
                if len(str(_pmid)) > 1:
                    pass

    return map(int, _pubmeds)

def _service_report_accession(hgvs_text=None):
    """
    Retrieve accession for a variant from the NCBI Variant Reporter Service
    :param hgvs_text: ( c.DNA | r.RNA | p.Protein | g.Genomic )
    :return: Accession (clinvar | dbSNP | dbVar)
    """
    _report  = _ncbi_variant_report_service(hgvs_text)

    for _row in _report:
        _accession = _row['ClinVar Accession']

        if _accession is not None:
            if len(str(_accession)) > 1:
                    return _accession

    log.debug("Variant accession not found in clinvar for "+ str(hgvs_text))
    return None

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

NCBIVariantReport  = _ncbi_variant_report_service
NCBIVariantPubmeds = _ncbi_variant_pubmeds
ClinvarAccession   = _clinvar_variant_accession
ClinvarAlleleID    = _clinvar_variant_allele_id
ClinvarPubmeds     = _clinvar_variant2pubmed
ClinvarVariationID = _clinvar_variant_variation_id
