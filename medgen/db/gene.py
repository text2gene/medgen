from .dataset import SQLData

##########################################################################################
#
#       SQLData Class
#
##########################################################################################

class GeneBorg:
    __shared_state = {}
    __gene2pubmed = {}
    __gene2id = {}
    cnt = 0

    def __init__(self, db):
        self.__dict__ = self.__shared_state
        self._db = db

    def gene2pubmed(self, ncbi_gene_id):
        """
        mysql> desc gene.gene2pubmed;
        +--------+------------------+------+-----+---------+-------+
        | tax_id | int(5) unsigned  | YES  | MUL | NULL    |       |
        | GeneID | int(10) unsigned | YES  | MUL | NULL    |       |
        | PMID   | varchar(10)      | YES  | MUL | NULL    |       |
        +--------+------------------+------+-----+---------+-------+
        """
        ncbi_gene_id = self._db.get_gene_id(ncbi_gene_id)
        if ncbi_gene_id not in self.__gene2pubmed:
            self.__gene2pubmed[ncbi_gene_id] = self._db.fetchall('select PMID from gene2pubmed where GeneID = "{}"'.format(ncbi_gene_id))
            self.cnt += 1
        return self.__gene2pubmed[ncbi_gene_id]

    def get_gene_id_for_gene_name(self, hgnc_gene_name_symbol):
        if hgnc_gene_name_symbol not in self.__gene2id:
            self.__gene2id[hgnc_gene_name_symbol] = self._db.fetchID('select GeneID as ID from gene_info where Symbol = "{}" limit 1'.format(hgnc_gene_name_symbol.upper()))
            self.cnt += 1

        return self.__gene2id[hgnc_gene_name_symbol]

class GeneDB(SQLData):
    """
    NCBI Entrez Gene contains links to pubmed (gene2pubmed), MedGen, OMIM, and other sources.
    """
    def __init__(self):
        super(GeneDB, self).__init__(config_section='gene')

    def gene2pubmed(self, ncbi_gene_id):
        """
        Get pubmed entries for gene

        cached: gene2pubmed entries for Entrez GeneID

        :param ncbi_gene_id: int
        :return: list of PMIDs
        """
        return GeneBorg(self).gene2pubmed(ncbi_gene_id)

    def get_gene_id_for_gene_name(self, hgnc_gene_name_symbol):
        """
        cached: Get GeneName (hugo hgnc) for GeneID (ncbi entrez)
        """
        return GeneBorg(self).get_gene_id_for_gene_name(hgnc_gene_name_symbol)

    def gene2mim(self, ncbi_gene_id):
        """
        Online Mendelian Inheritance in Man (OMIM) is a standard reference

        mysql> desc mim2gene_medgen;
        +-----------+------------------+------+-----+---------+-------+
        | Field     | Type             | Null | Key | Default | Extra |
        +-----------+------------------+------+-----+---------+-------+
        | MIM       | int(10) unsigned | YES  | MUL | NULL    |       |
        | GeneID    | int(10) unsigned | YES  | MUL | NULL    |       |
        | MIM_type  | varchar(20)      | YES  |     | NULL    |       |
        | MIM_vocab | varchar(20)      | YES  |     | NULL    |       |
        | MedGenCUI | varchar(20)      | YES  | MUL | NULL    |       |
        +-----------+------------------+------+-----+---------+-------+

        :param ncbi_gene_id: int
        :return: OMIM identifiers with links to MedGen.
        """
        ncbi_gene_id = self.get_gene_id(ncbi_gene_id)
        return self.fetchall('select * from mim2gene_medgen where GeneID = {}'.format(ncbi_gene_id))

    def gene_function(self, ncbi_gene_id):
        """
        get gene-reference-in-function (RIF) for a given gene id.
        This is a textual description of what the gene actually DOES.

        :param ncbi_gene_id:  int
        :return: SQL result GeneRIF with list of pubmeds
        """
        ncbi_gene_id = self.get_gene_id(ncbi_gene_id)
        return self.fetchall('select distinct pubmeds, GeneRIF from generifs_basic where GeneID = {}'.format(ncbi_gene_id))

    def get_gene_id(self, gene):
        """
        Entrez Gene ID.
        (Guard) Ensures we are referring to the NCBI GeneID and not a HGNC gene name
        :param gene: either Entrez gene id or HGNC gene name
        :return: GeneID from NCBI Entrez
        """
        try:
            int(gene)
        except ValueError:
            return self.get_gene_id_for_gene_name(gene)
        except AttributeError:
            return gene.GeneID
        else:
            return gene

    def get_gene_name(self, ncbi_gene_id):
        """
        Get HUGO Gene Name (Symbol) for Entrez gene ID
        :param ncbi_gene_id: int
        :return: string
        """
        ncbi_gene_id = self.get_gene_id(ncbi_gene_id)
        return self.fetchID('select Symbol as ID from gene_info where GeneID = {} limit 1'.format(ncbi_gene_id))

    def get_gene_info(self, ncbi_gene_id):
        """
        NCBI Gene Info for a given gene
        :param ncbi_gene_id: gene id (integer)
        :return: SQL result

        mysql> desc gene.get_gene_info;
        +--------------+------------------+------+-----+---------+-------+
        | Field        | Type             | Null | Key | Default | Extra |
        +--------------+------------------+------+-----+---------+-------+
        | tax_id       | int(5) unsigned  | YES  | MUL | NULL    |       |
        | GeneID       | int(10) unsigned | YES  | MUL | NULL    |       |
        | Symbol       | varchar(50)      | YES  | MUL | NULL    |       |
        | LocusTag     | varchar(20)      | YES  |     | NULL    |       |
        | Synonyms     | text             | YES  |     | NULL    |       |
        | dbXrefs      | text             | YES  |     | NULL    |       |
        | chromosome   | varchar(50)      | YES  |     | NULL    |       |
        | map_loc      | varchar(20)      | YES  |     | NULL    |       |
        | GeneDesc     | text             | YES  |     | NULL    |       |
        | GeneType     | varchar(20)      | YES  |     | NULL    |       |
        | Nomen_symbol | varchar(20)      | YES  |     | NULL    |       |
        | Nomen_source | varchar(20)      | YES  |     | NULL    |       |
        | Nomen_status | varchar(20)      | YES  |     | NULL    |       |
        | GeneOther    | text             | YES  |     | NULL    |       |
        | LastModified | varchar(10)      | YES  |     | NULL    |       |
        +--------------+------------------+------+-----+---------+-------+
        """
        ncbi_gene_id = self.get_gene_id(ncbi_gene_id)
        return self.fetchrow('select * from gene_info where GeneID = %s limit 1'.format(ncbi_gene_id))

    def get_gene_synonyms(self, symbol):
        """
        Get gene synonyms, including symbols that may not be officially recognized.

        :param symbol: Hugo gene name
        :return: list [Synonyms, Symbol, GeneID]
        """
        permutations = (symbol, symbol,       # identity
                        '%|' + symbol,        # symbol at end of list
                        symbol + '|%',        # symbol at start of list
                        '%|' + symbol + '|%', # symbol in middle of list
                        symbol                # identity Nomen_symbol placement
                       )
        _sql = """select Synonyms, Symbol, GeneID from gene_info where 
            Symbol = %s OR
            (Synonyms   = %s or
            Synonyms like %s or
            Synonyms like %s or
            Synonyms like %s) OR
        Nomen_symbol = %s
        """
        return self.fetchall(_sql, *permutations)

    def get_gene_list_from_mim(self, mim):
        mim = str(mim)
        sql = """
            SELECT Symbol AS gene_name FROM gene_info WHERE GeneID IN
            (SELECT  DISTINCT GeneID from mim2gene_medgen WHERE MIM = %s""" 
        return self.list_genes(sql, mim)

