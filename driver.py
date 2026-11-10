import json
import time
import re
from pathlib import Path


class Driver:
    def __init__(self, stopped, log=lambda message: None):
        self.log = log
        from pywinauto import Desktop
        self.desktop = Desktop(backend='uia')
        self.native = Desktop(backend='win32')
        self.stopped = stopped
        self.config = json.loads(Path(__file__).with_name('selectors.json').read_text(encoding='utf-8'))
        if not self.config.get('calibrated'):
            raise RuntimeError('微信控件尚未校准，请先导出控件树；当前禁止发送')
        main = self.native.windows(title='微信')
        if len(main) != 1:
            raise RuntimeError('需要唯一的微信主窗口')
        self.process_id = main[0].process_id()
        required = ('plus', 'add_friend', 'search_input', 'search_button', 'not_found', 'already_friend', 'add_contact', 'message', 'submit', 'sent', 'close_search', 'restricted')
        if any(k not in self.config['controls'] for k in required):
            raise RuntimeError('控件配置不完整')

    def find(self, key):
        rule = self.config['controls'][key]
        found = []
        # Global UIA window enumeration can block on unrelated applications.
        # Discover native handles first, then connect only to matching windows.
        for native in self.native.windows(process=self.process_id, **rule['window']):
            window = self.desktop.window(handle=native.handle).wrapper_object()
            if 'child' in rule:
                selector = rule['child']
                candidates = window.descendants(control_type=selector['control_type']) if 'control_type' in selector else window.descendants()
                for candidate in candidates:
                    if 'title' in selector and candidate.window_text() != selector['title']:
                        continue
                    if 'auto_id' in selector and candidate.element_info.automation_id != selector['auto_id']:
                        continue
                    if 'title_re' in selector and not re.search(selector['title_re'], candidate.window_text()):
                        continue
                    found.append(candidate)
            else:
                found.append(window)
        found = [c for c in found if c.is_visible()]
        if 'expected_count' in rule:
            if len(found) != rule['expected_count']:
                raise RuntimeError(f'{key} 控件数量改变，已停止')
            found = [found[rule['index']]]
        if len(found) > 1:
            raise RuntimeError(f'{key} 匹配不唯一，已停止')
        return found[0] if found else None

    def wait(self, keys):
        self.log('等待界面：' + '、'.join(keys) + '（最多 15 秒）')
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            if self.stopped():
                raise RuntimeError('用户停止，请人工确认当前申请状态')
            for key in ('restricted', *keys):
                if self.find(key) is not None:
                    if key == 'restricted':
                        raise RuntimeError('出现限制或验证码，请人工处理')
                    return key
            time.sleep(.25)
        raise RuntimeError('等待界面结果超时，请人工确认')

    def click(self, key):
        self.log(f'准备点击控件：{key}')
        self.wait([key])
        c = self.find(key)
        if c is None or not c.is_enabled():
            raise RuntimeError(f'{key} 不可操作')
        # Prefer UIA InvokePattern: independent of screenshot geometry and DPI.
        # Never retry a failed invocation with a physical click: the action may
        # already have happened, especially for the submit button.
        if self.config.get('click_mode', 'physical') == 'physical':
            c.click_input()
            return
        try:
            invoke = c.iface_invoke
        except (AttributeError, NotImplementedError):
            invoke = None
        except Exception as exc:
            from pywinauto.uia_defines import NoPatternInterfaceError
            if isinstance(exc, NoPatternInterfaceError):
                invoke = None
            else:
                raise
        if invoke is not None:
            invoke.Invoke()
        else:
            c.click_input()

    def fill(self, key, value):
        self.log(f'填写控件：{key}，随后校验输入内容')
        self.wait([key])
        c = self.find(key)
        c.set_edit_text(value)
        if c.window_text() != value:
            raise RuntimeError('输入校验失败')

    def add(self, contact, message):
        self.click('plus')
        self.click('add_friend')
        self.fill('search_input', contact)
        self.click('search_button')
        result = self.wait(['not_found', 'already_friend', 'add_contact'])
        if result in ('not_found', 'already_friend'):
            self.click('close_search')
            return '未找到' if result == 'not_found' else '已是好友'
        self.click('add_contact')
        if message.strip():
            self.fill('message', message)
        else:
            self.log('验证消息留空：保留微信默认内容')
        if self.find('sent') is not None:
            raise RuntimeError('发现旧的发送成功提示，请人工确认')
        self.click('submit')
        result = self.wait(['sent', 'already_friend'])
        return '已是好友' if result == 'already_friend' else '已发送申请'
