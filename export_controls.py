"""Isolated UIA worker: parent can terminate a blocked provider call."""
import sys
import traceback
import time

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')


def main():
    print('[1/4] 正在加载 pywinauto', flush=True)
    from pywinauto import Desktop
    print('[2/4] 使用 win32 查找微信窗口', flush=True)
    windows = Desktop(backend='win32').windows(title='微信')
    if len(windows) != 1:
        raise RuntimeError(f'需要一个微信主窗口，实际找到 {len(windows)} 个')
    window = windows[0]
    print(f'找到微信：句柄 {window.handle}，进程 {window.process_id()}', flush=True)
    print('[3/4] 连接 UIA；微信不响应时主程序将在 30 秒后终止本任务', flush=True)
    ui = Desktop(backend='uia').window(handle=window.handle).wrapper_object()
    print('[4/4] 逐层读取控件（最多 40 层、1500 个）', flush=True)
    pending = [(ui, 0)]
    count = 0
    while pending and count < 1500:
        control, depth = pending.pop()
        info = control.element_info
        print(f'{count:04d} ' + '  ' * depth + f'{info.control_type} title={info.name!r} auto_id={info.automation_id!r}', flush=True)
        count += 1
        if depth < 40:
            pending.extend((child, depth + 1) for child in reversed(control.children()))
    print(f'完成：读取 {count} 个控件' + ('（已达到数量上限）' if pending else ''), flush=True)


if __name__ == '__main__':
    try:
        main()
    except Exception:
        traceback.print_exc()
        sys.exit(1)
