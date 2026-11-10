from pathlib import Path
from datetime import datetime
import hashlib
import shutil
from openpyxl import load_workbook
from main import save_atomic


class Store:
    def __init__(self, path):
        self.path = Path(path)
        self.digest = self.fingerprint()
        self.book = load_workbook(path)
        self.sheet = self.book.active
        self.columns = {str(c.value).strip(): c.column for c in self.sheet[1] if c.value}
        self.key = next((self.columns[k] for k in ('联系人', '微信号', '手机号', '手机号码') if k in self.columns), None)
        if self.key is None:
            raise ValueError('需要联系人、微信号或手机号列')
        for key in ('验证消息', '状态', '处理时间', '备注'):
            if key not in self.columns:
                self.columns[key] = self.sheet.max_column + 1
                self.sheet.cell(1, self.columns[key], key)

    def fingerprint(self):
        return hashlib.sha256(self.path.read_bytes()).digest()

    def entries(self):
        entries = []
        for row in range(2, self.sheet.max_row + 1):
            cell = self.sheet.cell(row, self.key)
            if cell.value is None:
                continue
            if cell.data_type == 'f':
                raise ValueError(f'第 {row} 行联系人不能是公式')
            value = cell.value
            if isinstance(value, float) and value.is_integer():
                value = int(value)
            contact = str(value).strip()
            if contact:
                entries.append((row, contact, str(self.sheet.cell(row, self.columns['验证消息']).value or ''), str(self.sheet.cell(row, self.columns['状态']).value or '')))
        done = {c for _, c, _, s in entries if s in ('已发送申请', '已通过', '已是好友', '未找到', '待人工确认', '处理中')}
        seen = set()
        for row, contact, message, status in entries:
            eligible = contact not in done and contact not in seen
            seen.add(contact)
            yield row, contact, message, status, eligible

    def record(self, row, status, note=''):
        if self.digest != self.fingerprint():
            raise RuntimeError('Excel 已被其他程序修改，请重新载入')
        for key, value in {'状态': status, '处理时间': datetime.now().isoformat(timespec='seconds'), '备注': note}.items():
            self.sheet.cell(row, self.columns[key], value)
        save_atomic(self.book, self.path)
        self.digest = self.fingerprint()

    def backup(self):
        target = self.path.with_name(self.path.stem + datetime.now().strftime('.backup-%Y%m%d-%H%M%S-%f.xlsx'))
        shutil.copy2(self.path, target)
        return target
