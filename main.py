"""Excel queue and WeChat desktop automation entry point."""
import argparse
import os
from datetime import datetime
from pathlib import Path

from openpyxl import Workbook, load_workbook

HEADERS = ['联系人', '验证消息', '状态', '处理时间', '备注']


def save_atomic(workbook, path):
    temporary = path.with_name(path.stem + '.tmp.xlsx')
    workbook.save(temporary)
    os.replace(temporary, path)


def create_template(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise FileExistsError(f'文件已存在：{path}')
    book = Workbook()
    sheet = book.active
    sheet.title = '联系人'
    sheet.append(HEADERS)
    sheet.freeze_panes = 'A2'
    for column in 'ABCDE':
        sheet.column_dimensions[column].width = 24
    sheet.column_dimensions['A'].number_format = '@'
    save_atomic(book, path)


def inspect_wechat():
    from pywinauto import Desktop
    windows = Desktop(backend='uia').windows()
    matches = [w for w in windows if any(s in w.window_text().lower() for s in ('微信', 'wechat', 'weixin'))]
    if not matches:
        raise RuntimeError('未找到微信窗口，请打开并登录电脑版微信。')
    for window in matches:
        window.print_control_identifiers()


def process(path, execute=False):
    if execute:
        raise RuntimeError('微信操作尚未配置；需要根据实际微信版本及演示接入后才能发送申请。')
    book = load_workbook(path)
    sheet = book.active
    columns = {cell.value: cell.column for cell in sheet[1]}
    missing = set(HEADERS) - columns.keys()
    if missing:
        raise ValueError('缺少表头：' + '、'.join(sorted(missing)))
    seen = set()
    pending = 0
    for row in range(2, sheet.max_row + 1):
        value = sheet.cell(row, columns['联系人']).value
        if value is None or not str(value).strip():
            continue
        contact = str(value).strip()
        status = sheet.cell(row, columns['状态']).value
        if contact in seen:
            print(f'第 {row} 行：重复联系人，跳过')
            continue
        seen.add(contact)
        if status in ('已发送申请', '已通过', '已是好友'):
            continue
        pending += 1
        print(f'第 {row} 行：待处理联系人 {contact}')
    print(f'预览完成：{pending} 个待处理联系人；未发送申请，未修改表格。')
    book.close()


def record_result(path, row, status, note=''):
    """Persist one verified UI outcome immediately, preserving other rows."""
    if status not in ('已发送申请', '已通过', '已是好友', '未找到', '失败', '待人工确认'):
        raise ValueError('不支持的状态')
    book = load_workbook(path)
    sheet = book.active
    columns = {cell.value: cell.column for cell in sheet[1]}
    if row < 2 or row > sheet.max_row:
        raise ValueError('记录行号无效')
    for key, value in {'状态': status, '处理时间': datetime.now().isoformat(timespec='seconds'), '备注': note}.items():
        sheet.cell(row, columns[key], value)
    save_atomic(book, path)
    book.close()


def main():
    parser = argparse.ArgumentParser(description='微信好友申请与 Excel 记录助手')
    sub = parser.add_subparsers(dest='command', required=True)
    template = sub.add_parser('template', help='生成空白 Excel 模板')
    template.add_argument('file', type=Path)
    preview = sub.add_parser('preview', help='预览联系人队列')
    preview.add_argument('file', type=Path)
    sub.add_parser('inspect', help='检查微信可访问性控件')
    args = parser.parse_args()
    if args.command == 'template':
        create_template(args.file)
    elif args.command == 'preview':
        process(args.file)
    else:
        inspect_wechat()


if __name__ == '__main__':
    main()
