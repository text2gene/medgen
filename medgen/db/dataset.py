# -*- coding: utf-8 -*-
from pyrfc3339 import parse
import MySQLdb
import MySQLdb.cursors as cursors

# Backup idea -- oracle's connector:
#import mysql.connector

#TODO: Streaming result set for very large returns
#      https://techualization.blogspot.com/2011/12/retrieving-million-of-rows-from-mysql.html

from ..log import log

DEFAULT_HOST = 'localhost'
DEFAULT_USER = 'medgen'
DEFAULT_PASS = 'medgen'
DEFAULT_DATASET = 'medgen'

SQLDATE_FMT = '%Y-%m-%d %H:%M:%S'
def EscapeString(value):
    value = value.encode("utf-8")
    #value = MySQLdb.escape_string(value)
    return '"{}"'.format(value)

def SQLdatetime(pydatetime_or_string):
    if hasattr(pydatetime_or_string, 'strftime'):
        dtobj = pydatetime_or_string
    else:
        # assume pyrfc3339 string
        dtobj = parse(pydatetime_or_string)
    return dtobj.strftime(SQLDATE_FMT)

class SQLData(object):
    """
    MySQL base class for config, select, insert, update, and delete of medgen linked databases.

    See https://dev.mysql.com/doc/connector-python/en/connector-python-example-connecting.html
    """
    def __init__(self, *args, **kwargs):
        self._cfg_section = kwargs.get('config_section', 'DEFAULT')

        from ..config import config
        self._db_host = kwargs.get('db_host', None) or config.get(self._cfg_section, 'db_host')
        self._db_user = kwargs.get('db_user', None) or config.get(self._cfg_section, 'db_user')
        self._db_pass = kwargs.get('db_pass', None) or config.get(self._cfg_section, 'db_pass')
        self._db_name = kwargs.get('dataset', None) or config.get(self._cfg_section, 'dataset')

        # will be connected upon first query, or can be set up "manually" by doing self.connect()
        self.conn = None

        #DEMOLITION / cruft from PySQLPool
        #self.commitOnEnd = kwargs.get('commitOnEnd', True) or config.get(self._cfg_section, 'commitOnEnd')

    def connect(self):
        self.conn = MySQLdb.connect(passwd=self._db_pass,
                                    user=self._db_user,
                                    db=self._db_name,
                                    host=self._db_host,
                                    cursorclass=cursors.DictCursor,
                                    charset='utf8',
                                    use_unicode=True,
                                   )
        return self.conn

    def cursor(self, execute_sql=None):
        if not self.conn:
            self.connect()
        cursor = self.conn.cursor(cursors.DictCursor)

        if execute_sql is not None:
            cursor.execute(execute_sql)

        return cursor

    def fetchall(self, select_sql, *args):
        """ For submitted select_sql with interpolation strings meant to match
        with supplied *args, build and execute the statement and fetch all results.

        Results will be returned as a list of dictionaries.

        Example:
            DB.fetchall('select HGVS from clinvar where PMID="%s"', ('21129721',))

        :param select_sql: (str)
        :returns: results as list of dictionaries
        :rtype: list
        """
        # this line opens a cursor, executes, gets the data, and closes the cursor.
        if args:
            results = self.cursor(select_sql % args).fetchall()
        else:
            results = self.cursor(select_sql).fetchall()
        return results

    def fetchrow(self, select_sql, *args):
        """
        If the query was successful:
            if 1 or more rows was returned, returns the first one
            else returns None
        Else:
            raises Exception
        """
        res = self.fetchall(select_sql, *args)
        return res[0] if len(res) > 0 else None

    #def fetchID(self, select_sql, id_colname='ID', *args, **kwargs):
    def fetchID(self, select_sql, *args, **kwargs):
        id_colname = kwargs.get('id_colname', 'ID')

        results = self.fetchrow(select_sql, *args)
        if results is not None:
            if id_colname in results:
                return results[id_colname]
            else:
                raise RuntimeError("No ID column found.  SQL query: %s" % select_sql)
        return None  # no results found

    # DEMOLITION / Probably not needed
    #def list_concepts(self, select_sql):
    #    """
    #    Fetch list of concepts
    #    :param select_sql: query
    #    :return: list cui
    #    """
    #    return self.fetchlist(select_sql, 'CUI')

    # DEMOLITION / Probably not needed
    #def list_genes(self, select_sql):
    #    """
    #    Fetch list of genes
    #    :param select_sql: query
    #    :return: list HGNC
    #    """
    #   return self.fetchlist(select_sql, 'gene_name')

    def insert(self, tablename, field_value_dict):
        """ Takes a tablename (should be found in selected DB) and a dictionary mapping
        column and value pairs, and inserts the dictionary as a row in target table.

        WARNING: this function trusts field names (not protected against sql injection attacks).

        :param: tablename: name of table to receive new row
        :param: field_value_dict: map of field=value
        :return: row_id (integer) (returns 0 if insert failed)
        """
        fields = []
        values = []

        for key, val in field_value_dict.items():
            fields.append(key)
            values.append(val)

        sql = 'insert into {} ({}) values ({});'.format(tablename, ','.join(fields), ','.join(['%s' for v in values]))
        cursor = self.execute(sql, *values)
        cursor.close()
        return self.conn.insert_id()

    def update(self, tablename, id_col_name, row_id, field_value_dict):
        """
        :param: tablename: name of table to update
        :param: row_id (int): row id of record to update
        :param: field_value_dict: map of field=value
        :return: row_id (integer) (returns 0 if insert failed)
        """
        fields = []
        values = []

        clauses = []

        for key, val in field_value_dict.items():
            clause = '%s=' % key
            # surround strings and datetimes with quotation marks
            if val == None:
                clause += 'NULL'
            elif hasattr(val, 'strftime'):
                clause += '"%s"' % val.strftime(SQLDATE_FMT)
            elif hasattr(val, 'lower'):
                clause += EscapeString(val)  #surrounds strings with quotes and unicodes them.
            else:
                clause += str(val)
            clauses.append(clause)

        sql = 'update '+tablename+' set %s where %s=%i;' % (', '.join(clauses), id_col_name, row_id)
        queryobj = self.execute(sql)
        # retrieve and return the row id of the insert. returns 0 if insert failed.
        return queryobj.lastInsertID

    def delete(self, tablename, field_value_dict):
        """
        :param: tablename: name of table from which rows will be deleted.
        :param: field_value_dict: map of field=value indicating which rows to delete.
        :return: row_id (integer) (returns 0 if delete failed)
        """
        if len(field_value_dict) == 0:
            raise RuntimeError("Do not support delete without a WHERE clause")

        where_sql = ''
        for key, val in field_value_dict.items():
            if val == None:
                val = 'NULL'
                where_sql += 'AND {} is NULL '.format(key)
            # surround strings and datetimes with quotation marks
            elif hasattr(val, 'strftime'):
                val = '"%s"' % val.strftime(SQLDATE_FMT)
                where_sql += 'AND {}={} '.format(key, val)
            elif hasattr(val, 'lower'):
                val = EscapeString(val)  # surrounds strings with quotes and unicodes them.
                where_sql += 'AND {}={} '.format(key, val)
            else:
                val = str(val)
                where_sql += 'AND {}={} '.format(key, val)

        where_sql = where_sql[len('AND '):]

        sql = 'delete from {} where {}'.format(tablename, where_sql)

        cursor = self.execute(sql)
        #TODO: does this do anything? work at all?? eek.
        result = cursor.fetchone()
        cursor.close()
        return result

    def drop_table(self, tablename):
        cursor = self.execute('drop table if exists ' + tablename)
        result = cursor.fetchone()
        cursor.close()
        return result

    def truncate(self, tablename):
        cursor = self.execute('truncate ' + tablename)
        result = cursor.fetchone()
        cursor.close()
        return result

    def execute(self, sql, *args):
        """
        Executes arbitrary sql string in current database connection.
        Use this method's args for positional string interpolation into sql.

        :param sql: (str)
        :return: MySQLdb cursor object
        """
        #try:
        log.debug('SQL.execute ' + sql, *args)
        #except TypeError as error:
        #    log.info('Arguments do not match number of string interpolations in SQL statement.')
        #    log.info('  SQL was: %s' % sql)
        #    log.info('  Args: %r' % args)

        try:
            cursor = self.cursor(sql % args)
        except Exception as err:
            log.info('Medgen SQL ERROR: %r' % err)
            full_sql = sql % args
            log.info('Tripped on a piece of SQL: ' + full_sql)
        return cursor 

    def ping(self):
        """
        Same effect as calling 'mysql> call mem'
        :returns::self.schema_info(()
        """
        try:
            return self.schema_info()
        except MySQLdb.Error as err:
            log.error('DB connection is dead %d: %s' % (err.args[0], err.args[1]))
            return False

    def schema_info(self):
        header = ['schema', 'engine', 'table', 'rows', 'million', 'data length', 'MB', 'index']
        return {'header': header, 'tables': self.fetchall('call mem')}

    def last_loaded(self, dbname=None):
        if dbname is None:
            dbname = self._db_name
        return self.fetchID('select event_time as ID from '+dbname+'.log where entity_name = "load_database.sh" and message = "done" order by idx desc limit 1')

    def unique_PMID(self, sql):
        """
        For given sql select query, return a list of unique PMID strings.
        """
        pubmeds = set()
        for row in self.fetchall(sql):
            pubmeds.add(str(row['PMID']))
        return pubmeds

    def unique_HGVS(self, sql):
        """
        For given sql select query, return a list of unique HGVS strings.
        """
        hgvs_texts = set()
        for row in self.fetchall(sql):
            hgvs_texts.add(str(row['HGVS']))
        return hgvs_texts

    def trunc_str(self, inp, maxlen):
        """
        Useful utility method for storing text in a database
        :param inp: a string
        :param maxlen: the max length of that string
        :return: '%s' % s or '%s...' % s[:m-3]
        """
        if maxlen < 3:
            raise RuntimeError('maxlen must be at least 3')
        if len(inp) > maxlen:
            inp = '%s...' % inp[:maxlen - 3]
        return inp

    def get_last_mirror_time(self, entity_name):
        """
        Get the last time some entity was mirrored

        :param entity_name: table name for db, for example, bic_brca1
        :return: datetime if found
        """
        sql_query = 'SELECT event_time FROM log WHERE entity_name = "%s" AND message like "rows loaded %s" ORDER BY event_time DESC limit 1'
        result = self.fetchrow(sql_query, entity_name, '%')
        if result:
            return result['event_time']
        sql_query = sql_query % (entity_name, '%')
        raise RuntimeError('Query "%s" returned no results. Have you loaded the %s table?' % (sql_query, entity_name))

    def create_index(self, table, colspec):
        """
        Create index on a specified table using the colums defined.
        Index start/stop times are logged to the "log" table.
        :param table: name of the table, example, "train"
        :param colspec: name of column, for example, "RQ"
        :return:
        """
        self.execute("call create_index(%s, %s) ", (table, colspec))

    def fetchlist(self, select_sql, column='gene_name'):
        """
        Fetch as list
        :param select_sql: query
        :param column: name of column you want to make a list out of
        :return: list
        """
        rows = self.fetchall(select_sql)
        return [] if rows is None else [str(r[column]) for r in rows]
