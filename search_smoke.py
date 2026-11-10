"""Observed-layout search-only smoke test. No friend requests are sent."""
import time
from pathlib import Path
from pywinauto import Desktop
from openpyxl import Workbook


def main():
    folder = Path(__file__).parent / 'review' / 'search-test'
    folder.mkdir(parents=True, exist_ok=True)
    desktop = Desktop(backend='win32')
    windows = desktop.windows(title='添加朋友')
    if len(windows) != 1:
        raise RuntimeError('需要唯一的添加朋友窗口')
    window = windows[0]
    rect = window.rectangle()
    if (rect.width(), rect.height()) != (376, 568):
        raise RuntimeError('窗口布局已变化，禁止使用本次校准坐标')
    book = Workbook()
    sheet = book.active
    sheet.append(['联系人', '状态', '处理时间', '备注', '截图'])
    for index in range(10):
        # Invalid mainland prefixes; these are deliberately not real phones.
        contact = f'000000000{index:02d}'
        if not window.is_visible():
            raise RuntimeError('搜索窗口已关闭')
        window.click_input(coords=(145, 70))
        window.type_keys('^a')
        window.type_keys(contact, pause=.08)
        window.click_input(coords=(312, 70))
        time.sleep(3)
        screenshot = folder / f'{index+1:02d}.png'
        window.capture_as_image().save(screenshot)
        sheet.append([contact, '待核对搜索截图', time.strftime('%Y-%m-%d %H:%M:%S'), '无效前缀；仅搜索，未发送申请', str(screenshot)])
        book.save(folder / 'results.xlsx')
        print(f'{index+1}/10 saved', flush=True)
    book.close()


if __name__ == '__main__':
    main()
