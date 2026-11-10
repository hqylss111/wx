import tempfile
import unittest
from pathlib import Path
from openpyxl import Workbook, load_workbook
from store import Store


class StoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / 'contacts.xlsx'
        book = Workbook()
        book.active.append(['手机号', '状态'])
        book.active.append(['00123', ''])
        book.active.append(['00123', '已发送申请'])
        book.active.append(['00456', ''])
        book.save(self.path)
        book.close()

    def tearDown(self):
        self.temp.cleanup()

    def test_duplicate_and_resume(self):
        store = Store(self.path)
        self.assertEqual([e[4] for e in store.entries()], [False, False, True])
        store.record(4, '处理中')
        store.book.close()
        store = Store(self.path)
        self.assertFalse(any(e[4] for e in store.entries()))
        self.assertEqual(list(store.entries())[2][1], '00456')
        store.book.close()

    def test_external_changes_preserved(self):
        store = Store(self.path)
        book = load_workbook(self.path)
        book.active['A4'] = 'changed'
        book.save(self.path)
        book.close()
        with self.assertRaises(RuntimeError):
            store.record(4, '已发送申请')
        store.book.close()


if __name__ == '__main__':
    unittest.main()
