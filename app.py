import queue
import threading
import time
import subprocess
import sys
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from store import Store
from main import create_template, inspect_wechat


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('微信好友助手')
        self.geometry('900x650')
        self.events = queue.Queue()
        self.stop_event = threading.Event()
        self.pause_event = threading.Event()
        self.running = False
        self.task_limit = None
        self.inspect_cancel = threading.Event()
        self.exporting = False
        self.path = tk.StringVar()
        self.message = tk.StringVar()
        self.interval = tk.StringVar(value='30')
        bar = ttk.Frame(self, padding=10)
        bar.pack(fill='x')
        ttk.Entry(bar, textvariable=self.path, width=65).pack(side='left', expand=True, fill='x')
        ttk.Button(bar, text='选择 Excel', command=self.choose).pack(side='left')
        ttk.Button(bar, text='生成模板', command=self.template).pack(side='left')
        form = ttk.Frame(self, padding=10)
        form.pack(fill='x')
        ttk.Label(form, text='默认验证消息：').pack(side='left')
        ttk.Entry(form, textvariable=self.message, width=45).pack(side='left')
        ttk.Label(form, text='间隔秒数：').pack(side='left')
        ttk.Entry(form, textvariable=self.interval, width=6).pack(side='left')
        buttons = ttk.Frame(self, padding=10)
        buttons.pack(fill='x')
        for label, callback in [('预览', self.preview), ('导出微信控件', self.inspect), ('开始发送', self.start), ('暂停/继续', self.pause), ('停止', self.stop)]:
            button = ttk.Button(buttons, text=label, command=callback)
            button.pack(side='left', padx=4)
            if label == '暂停/继续':
                self.pause_button = button
                button.configure(text='暂停')
        self.activity = tk.StringVar(value='就绪')
        ttk.Label(self, textvariable=self.activity).pack(anchor='w', padx=10)
        self.progress = ttk.Progressbar(self, mode='indeterminate')
        self.progress.pack(fill='x', padx=10, pady=4)
        self.table = ttk.Treeview(self, columns=('row', 'contact', 'status', 'eligible'), show='headings', height=12)
        for key, label in zip(self.table['columns'], ('行号', '联系人', '当前状态', '是否待处理')):
            self.table.heading(key, text=label)
        self.table.pack(fill='both', expand=True, padx=10)
        self.log = tk.Text(self, height=10, state='disabled')
        self.log.pack(fill='both', padx=10, pady=10)
        self.protocol('WM_DELETE_WINDOW', self.close)
        self.after(100, self.poll)

    def choose(self):
        if not self.running:
            path = filedialog.askopenfilename(filetypes=[('Excel', '*.xlsx')])
            if path:
                self.path.set(path)
                self.preview()

    def template(self):
        path = filedialog.asksaveasfilename(defaultextension='.xlsx', filetypes=[('Excel', '*.xlsx')])
        if path:
            try:
                create_template(Path(path))
                self.path.set(path)
            except Exception as exc:
                messagebox.showerror('生成失败', str(exc))

    def preview(self):
        if self.running:
            return
        store = None
        try:
            store = Store(self.path.get())
            rows = list(store.entries())
            self.table.delete(*self.table.get_children())
            for row, contact, _, status, eligible in rows:
                self.table.insert('', 'end', values=(row, contact, status, '是' if eligible else '跳过'))
        except Exception as exc:
            messagebox.showerror('读取失败', str(exc))
        finally:
            if store:
                store.book.close()

    def inspect(self):
        if self.running:
            self.events.put('已有任务正在运行，请先停止或等待结束')
            return
        self.running = True
        self.exporting = True
        self.inspect_cancel.clear()
        self.progress.start(15)
        self.activity.set('正在导出微信控件（最多 30 秒，可点击停止）')
        self.events.put('开始导出：后台读取微信控件，界面可以继续操作')
        threading.Thread(target=self.export_worker, daemon=True).start()

    def export_worker(self):
        process = None
        try:
            target = Path(__file__).with_name('logs')
            target.mkdir(exist_ok=True)
            output_path = target / 'wechat-controls.txt'
            python = Path(sys.executable).with_name('python.exe')
            env = __import__('os').environ.copy()
            env['PYTHONIOENCODING'] = 'utf-8'
            started = time.monotonic()
            with output_path.open('w', encoding='utf-8') as output:
                command = [sys.executable, '--export-worker', str(output_path)] if getattr(sys, 'frozen', False) else [str(python), '-u', str(Path(__file__).with_name('export_controls.py'))]
                process = subprocess.Popen(command, stdout=output, stderr=subprocess.STDOUT, env=env, creationflags=subprocess.CREATE_NO_WINDOW)
                offset = 0
                heartbeat = 0
                while True:
                    with output_path.open(encoding='utf-8', errors='replace') as reader:
                        reader.seek(offset)
                        lines = reader.readlines()
                        offset = reader.tell()
                    for line in lines:
                        self.events.put(line.rstrip())
                    elapsed = time.monotonic() - started
                    if process.poll() is not None:
                        # Flush any final output after child exit.
                        with output_path.open(encoding='utf-8', errors='replace') as reader:
                            reader.seek(offset)
                            for line in reader:
                                self.events.put(line.rstrip())
                        if process.returncode:
                            raise RuntimeError(f'导出失败，退出码 {process.returncode}，详情见 {output_path}')
                        self.events.put(f'导出完成，耗时 {elapsed:.1f} 秒：{output_path}')
                        break
                    if self.inspect_cancel.is_set() or elapsed >= 30:
                        process.kill()
                        process.wait(timeout=5)
                        reason = '用户停止' if self.inspect_cancel.is_set() else '读取微信控件超过 30 秒，已终止，界面未卡死'
                        self.events.put(f'{reason}；已读取的内容保留在 {output_path}')
                        break
                    if elapsed >= heartbeat:
                        self.events.put(f'导出仍在运行，已用 {elapsed:.0f} 秒；等待微信返回控件信息')
                        heartbeat = elapsed + 3
                    time.sleep(.2)
        except Exception as exc:
            import traceback
            self.events.put('导出异常：' + str(exc) + '\n' + traceback.format_exc())
        finally:
            if process is not None and process.poll() is None:
                process.kill()
                process.wait()
            self.events.put(None)

    def stop(self):
        self.stop_event.set()
        self.inspect_cancel.set()
        self.events.put('收到停止指令，正在停止当前任务')

    def start(self):
        if self.running:
            self.events.put('无法开始：已有任务正在运行')
            return
        self.events.put('收到开始指令，正在检查 Excel、间隔和微信配置')
        validation_store = None
        try:
            interval = float(self.interval.get())
            if not 5 <= interval <= 3600:
                raise ValueError('间隔应为 5–3600 秒')
            path = self.path.get()
            if not Path(path).is_file():
                raise ValueError('请先选择 Excel')
            import json
            validation_store = Store(path)
            pending = [e for e in validation_store.entries() if e[4]]
            self.events.put(f'Excel 检查：{len(pending)} 个待处理联系人')
            problems = []
            if not pending:
                problems.append('没有待处理联系人')
            config = json.loads(Path(__file__).with_name('selectors.json').read_text(encoding='utf-8'))
            if not config.get('calibrated'):
                problems.append('微信发送适配未完成：搜索测试已通过，但申请窗口和成功提示尚未校准')
            for problem in problems:
                self.events.put('启动检查未通过：' + problem)
            if problems:
                self.activity.set('启动检查未通过，详细原因见下方日志')
                return
        except Exception as exc:
            self.events.put(f'启动检查失败：{exc}')
            messagebox.showerror('无法开始', str(exc))
            return
        finally:
            if validation_store:
                validation_store.book.close()
        self.running = True
        self.activity.set('正在处理联系人，详情见下方日志')
        self.progress.start(15)
        self.stop_event.clear()
        self.pause_event.clear()
        self.pause_button.configure(text='暂停')
        threading.Thread(target=self.run, args=(path, self.message.get(), interval), daemon=True).start()

    def run(self, path, default_message, interval):
        store = None
        initialized = False
        try:
            import pythoncom
            pythoncom.CoInitialize()
            initialized = True
            from driver import Driver
            self.events.put('正在加载微信控件配置')
            driver = Driver(self.stop_event.is_set, self.events.put)
            self.events.put('微信配置检查通过，正在读取 Excel')
            store = Store(path)
            entries = [e for e in store.entries() if e[4]]
            if self.task_limit is not None:
                entries = entries[:self.task_limit]
            self.events.put(f'本次处理 {len(entries)} 个联系人，间隔 {interval:g} 秒')
            self.events.put(f'备份已保存：{store.backup()}')
            for index, (row, contact, message, _, _) in enumerate(entries):
                if self.pause_event.is_set():
                    self.events.put(('status', f'已暂停；点击“继续”处理第 {row} 行'))
                while self.pause_event.is_set() and not self.stop_event.wait(.2):
                    pass
                if self.stop_event.is_set():
                    break
                # Persist BEFORE UI operations; interrupted rows never auto-resend.
                store.record(row, '处理中', '中断后请人工核对状态再重置')
                self.events.put(f'处理第 {row} 行')
                try:
                    status = driver.add(contact, message or default_message)
                except Exception as exc:
                    store.record(row, '待人工确认', str(exc))
                    raise
                store.record(row, status)
                self.events.put(f'第 {row} 行：{status}')
                if status in ('已发送申请', '已是好友') and driver.find('close_search') is not None:
                    driver.click('close_search')
                if index + 1 < len(entries):
                    next_row = entries[index + 1][0]
                    self.events.put(f'本条已保存；等待 {interval:g} 秒后自动处理第 {next_row} 行，无需再次点击开始')
                    deadline = time.monotonic() + interval
                    last_seconds = None
                    while not self.stop_event.is_set():
                        remaining = max(0, __import__('math').ceil(deadline - time.monotonic()))
                        if remaining != last_seconds:
                            last_seconds = remaining
                            status = f'间隔剩余 {remaining} 秒；下一条第 {next_row} 行'
                            if self.pause_event.is_set():
                                status += '；已设为暂停，点击“继续”恢复'
                            self.events.put(('status', status))
                            if remaining % 5 == 0:
                                self.events.put(status)
                        if remaining == 0:
                            break
                        self.stop_event.wait(.1)
            self.events.put('任务结束，可重新预览 Excel')
        except Exception as exc:
            self.events.put(f'已停止：{exc}')
        finally:
            if store:
                store.book.close()
            if initialized:
                pythoncom.CoUninitialize()
            self.events.put(None)

    def pause(self):
        if not self.running or self.exporting:
            self.events.put('当前没有可暂停的联系人任务')
            return
        if self.pause_event.is_set():
            self.pause_event.clear()
            self.pause_button.configure(text='暂停')
            self.activity.set('已继续，正在等待或处理下一条')
            self.events.put('继续处理')
        else:
            self.pause_event.set()
            self.pause_button.configure(text='继续')
            self.activity.set('已请求暂停；当前联系人完成后暂停，点击“继续”恢复')
            self.events.put('将在当前联系人处理完成后暂停')

    def poll(self):
        while not self.events.empty():
            item = self.events.get()
            if isinstance(item, tuple) and item[0] == 'status':
                self.activity.set(item[1])
            elif item is None:
                self.running = False
                self.exporting = False
                self.progress.stop()
                self.progress.configure(value=0)
                self.pause_button.configure(text='暂停')
                self.activity.set('任务已结束，结果见日志')
            else:
                target = Path(__file__).with_name('logs')
                target.mkdir(exist_ok=True)
                entry = time.strftime('%Y-%m-%d %H:%M:%S ') + item + '\n'
                try:
                    with (target / 'application.log').open('a', encoding='utf-8') as output:
                        output.write(entry)
                except OSError:
                    entry += '日志文件写入失败，请检查磁盘空间或权限\n'
                self.log.configure(state='normal')
                self.log.insert('end', entry)
                self.log.see('end')
                self.log.configure(state='disabled')
        self.after(100, self.poll)

    def close(self):
        if self.running:
            self.stop()
            messagebox.showinfo('正在停止', '等待当前操作停止并保存记录后，再关闭窗口。')
        else:
            self.destroy()


if __name__ == '__main__':
    if '--export-worker' in sys.argv:
        import export_controls
        with Path(sys.argv[sys.argv.index('--export-worker') + 1]).open('w', encoding='utf-8') as worker_output:
            sys.stdout = sys.stderr = worker_output
            try:
                export_controls.main()
            except Exception:
                __import__('traceback').print_exc()
                sys.exit(1)
        sys.exit(0)
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--file', type=Path, help='启动时预览指定 Excel，不自动发送')
    parser.add_argument('--limit', type=int, help='限制本次处理条数')
    parser.add_argument('--interval', type=float, default=30)
    parser.add_argument('--autostart', action='store_true')
    args = parser.parse_args()
    application = App()
    application.task_limit = args.limit
    application.interval.set(str(args.interval))
    if args.file:
        application.path.set(str(args.file.resolve()))
        application.after(100, application.preview)
    if args.autostart:
        application.after(700, application.start)
    application.mainloop()
