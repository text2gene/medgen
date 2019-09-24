from unittest import TestCase
from hamcrest import *
from medgen.annotate.variant import ClinvarVariationID, ClinvarPubmeds, ClinvarAccession, ClinvarAlleleID
from medgen.annotate.pubmed import PMCID2Article
from medgen.db.clinvar import ClinVarDB


class TestClinVarDB(TestCase):
    def setUp(self):
        self.db = ClinVarDB()

    def test_get_random_example_hgvs(self):
        examples = self.db.random_example_hgvs()
        assert_that(len(examples), equal_to(1))
        examples = self.db.random_example_hgvs(10)
        assert_that(len(examples), equal_to(10))
        assert_that(examples[0], starts_with('NM_'))
        #print examples

    def test_bookID_citations_specific_to_clinvar(self):
        pubmeds = ClinvarPubmeds('NM_000410.3:c.845G>A')

        assert_that(len(pubmeds) > 35)
        assert_that('NBK1440', is_in(pubmeds))

    def test_convert_bidirectionally_hgvs_c_variation_id(self):
        variation_id = 47706
        hgvs_text = 'NM_133378.4:c.98772T>C'

        assert_that(variation_id in ClinvarVariationID(hgvs_text))
        assert_that(variation_id in ClinVarDB().variation_id_for_hgvs_text(hgvs_text))
        assert_that(hgvs_text in ClinVarDB().hgvs_text_for_variation_id(variation_id))

    def test_convert_pubmed_central_PMCID_to_pubmed_PMID(self):
        pmcid = int(3110945)
        pmid = int(15371902)

        assert_that(int(PMCID2Article(pmcid).pmid), equal_to(pmid))

    def test_BIOMED_413_accession_and_variation_id_for_hgvs_c(self):
        hgvs_c = 'NM_001232.3:c.919G>C'
        allele_id = 32649
        variation_id = 17610
        accession = 'RCV000019176'

        assert_that(accession in ClinVarDB().accession_for_hgvs_text(hgvs_c))
        assert_that(variation_id in ClinVarDB().variation_id_for_hgvs_text(hgvs_c))
        assert_that(allele_id in ClinVarDB().allele_id_for_hgvs_text(hgvs_c))
        assert_that(hgvs_c in ClinVarDB().hgvs_text_for_variation_id(variation_id))

    def test_BIOMED_405_hgvs_c_was_null_slang_used_in_variant_name(self):
        hgvs_c = 'NM_002485.4:c.1222A>G'
        variation_id = 127856
        allele_id = 133313
        accession1 = 'RCV000115778'
        accession2 = 'RCV000119194'

        assert_that(accession1 in ClinVarDB().accession_for_hgvs_text(hgvs_c))
        assert_that(accession2 in ClinVarDB().accession_for_hgvs_text(hgvs_c))
        assert_that(variation_id in ClinVarDB().variation_id_for_hgvs_text(hgvs_c))
        assert_that(allele_id in ClinVarDB().allele_id_for_hgvs_text(hgvs_c))
        assert_that(hgvs_c in ClinVarDB().hgvs_text_for_variation_id(variation_id))

    #def test_BIOMED_405_find_hgvs_for_previously_entered_LRG_slang_sloppy_variant_name(self):
    #    hgvs_c = 'NM_004006.2:c.5586+18A>G'
    #    variation_id = 94672
    #    allele_id = 100572
    #    accession = 'RCV000080662'

    #    assert_that(accession in ClinVarDB().accession_for_hgvs_text(hgvs_c))
    #    assert_that(variation_id in ClinVarDB().variation_id_for_hgvs_text(hgvs_c))
    #    assert_that(allele_id in ClinVarDB().allele_id_for_hgvs_text(hgvs_c))
    #    assert_that(hgvs_c in ClinVarDB().hgvs_text_for_variation_id(variation_id))

    def test_BIOMED_405__has_accession_for_previously_null_hgvs_c(self):
        hgvs_text = 'NM_000016.4:c.1091T>C'
        accession = 'RCV000077876'
        variation_id = 92253

        #TODO: replace this PMID (no longer valid)
        #pmid = 23757202
        #assert_that(pmid in ClinvarPubmeds(hgvs_text))

        assert_that(accession in ClinvarAccession(hgvs_text))
        assert_that(variation_id in ClinvarVariationID(hgvs_text))

    def test_get_version(self):
        version_str = self.db.get_version()
        assert_that(len(version_str), greater_than(0))
