"""Offline batch integration test; never connects to WeChat."""
import random
import unittest
from pathlib import Path
from openpyxl import Workbook, load_workbook
from store import Store


class BatchTest(unittest.TestCase):
    def test_ten_simulated_contacts(self):
        target = Path(__file__).parent / 'data' / 'offline-test-10.xlsx'
        target.parent.mkdir(exist_ok=True)
        randomizer = random.Random(20261109)
        # Masked synthetic identifiers cannot be mistaken for callable numbers.
        contacts = [f'138TEST{n:04d}' for n in randomizer.sample(range(10000), 10)]
        book = Workbook()
        sheet = book.active
        sheet.title = '本地模拟测试_禁止发送'
        sheet.append(['联系人', '验证消息', '状态', '处理时间', '备注'])
        for contact in contacts:
            sheet.append([contact, '本地模拟测试', '', '', '非真实号码，不连接微信'])
        book.save(target)
        book.close()
        store = Store(target)
        self.assertEqual(len([e for e in store.entries() if e[4]]), 10)
        backup = store.backup()
        self.assertTrue(backup.exists())
        entries = list(store.entries())
        # Simulate interruption after three persisted outcomes.
        for entry in entries[:3]:
            store.record(entry[0], '已发送申请', '模拟结果，未实际发送')
        store.book.close()
        store = Store(target)
        remaining = [e for e in store.entries() if e[4]]
        self.assertEqual(len(remaining), 7)
        # An interrupted UI attempt must not be resent automatically.
        store.record(remaining[0][0], '处理中', '模拟进程中断，未实际发送')
        store.book.close()
        store = Store(target)
        self.assertEqual(len([e for e in store.entries() if e[4]]), 6)
        store.record(remaining[0][0], '待人工确认', '模拟未知结果，未实际发送')
        statuses = ['未找到', '已是好友', '已发送申请'] * 2
        for entry, status in zip([e for e in store.entries() if e[4]], statuses):
            store.record(entry[0], status, '模拟结果，未实际发送')
        store.book.close()
        store = Store(target)
        self.assertFalse(any(e[4] for e in store.entries()))
        store.book.close()
        saved = load_workbook(target)
        self.assertEqual(saved.active.max_row, 11)
        self.assertTrue(all(saved.active.cell(row, 4).value for row in range(2, 12)))
        self.assertEqual([saved.active.cell(row, 1).value for row in range(2, 12)], contacts)
        saved.close()
        print(f'Offline batch verified: {target}')


if __name__ == '__main__':
    unittest.main()
