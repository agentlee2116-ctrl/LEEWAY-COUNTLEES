import tempfile, unittest, sqlite3
from pathlib import Path
from accounts import Accounts
class Tests(unittest.TestCase):
    def test_account_lifecycle(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'accounts.db'; a=Accounts(p); pw='Long test password 123'
            with self.assertRaises(ValueError): a.register('tester','short','short')
            with self.assertRaises(ValueError): a.register('tester',pw,'different password')
            a.register('Tester',pw,pw)
            with self.assertRaises(ValueError): a.register('tester',pw,pw)
            self.assertEqual(Accounts(p).authenticate('tester',pw),'Tester')
            self.assertIsNone(a.authenticate('tester','wrong'))
            self.assertIsNone(a.authenticate('absent',pw))
            self.assertNotIn(pw.encode(),p.read_bytes())
if __name__=='__main__': unittest.main()
