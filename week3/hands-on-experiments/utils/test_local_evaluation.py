import sqlite3, tempfile, unittest
from pathlib import Path
from local_evaluation import sql_ast, results_match, execute

class EvaluationChecks(unittest.TestCase):
    def test_read_only_ast(self):
        sql_ast('WITH x AS (SELECT 1 AS a) SELECT a FROM x')
        for sql in ['DELETE FROM t', 'SELECT 1; SELECT 2', "ATTACH DATABASE 'other.db' AS other", 'CREATE TABLE t(x INT)']:
            with self.assertRaises(Exception): sql_ast(sql)

    def test_only_outer_order_matters(self):
        self.assertFalse(bool(sql_ast('SELECT * FROM (SELECT 1 ORDER BY 1)').args.get('order')))
        self.assertTrue(bool(sql_ast('SELECT 1 ORDER BY 1').args.get('order')))

    def test_duplicate_multiplicity_and_order(self):
        result = lambda rows: {'ok': True, 'columns': ['x'], 'rows': rows}
        self.assertFalse(results_match(result([[1], [1]]), result([[1]]), False))
        self.assertTrue(results_match(result([[1], [2]]), result([[2], [1]]), False))
        self.assertFalse(results_match(result([[1], [2]]), result([[2], [1]]), True))

    def test_null_numbers_and_column_count(self):
        a = {'ok': True, 'columns': ['x'], 'rows': [[None], [1], [2.1234567]]}
        b = {'ok': True, 'columns': ['y'], 'rows': [[None], [1.0], [2.12345671]]}
        self.assertTrue(results_match(a, b, False))
        b['rows'][0] = ['None']
        self.assertFalse(results_match(a, b, False))
        b['columns'].append('extra')
        self.assertFalse(results_match(a, b, False))

    def test_worker_enforces_no_writes_and_no_extensions(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); db = root/'db.sqlite'
            with sqlite3.connect(db) as c:
                c.execute('CREATE TABLE t(x INTEGER)'); c.execute('INSERT INTO t VALUES(7)')
            self.assertTrue(execute(db, 'SELECT x FROM t', root/'read.sql')['ok'])
            self.assertFalse(execute(db, 'DELETE FROM t', root/'write.sql')['ok'])
            self.assertFalse(execute(db, "SELECT load_extension('anything')", root/'extension.sql')['ok'])
            with sqlite3.connect(db) as c: self.assertEqual(c.execute('SELECT x FROM t').fetchall(), [(7,)])

if __name__ == '__main__': unittest.main()
