"""
简洁的图形化用户界面 - 带进度条和错误提示
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from job_finder import JobFinder
import threading
import os
import sys


class JobFinderGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("职位查找器 v1.0")
        self.root.geometry("650x700")
        self.root.resizable(False, False)

        self.finder = JobFinder()
        self.is_running = False

        self.create_widgets()

    def create_widgets(self):
        """创建GUI组件"""

        # 主框架
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 标题
        title_label = ttk.Label(
            main_frame,
            text="职位查找器",
            font=("Microsoft YaHei", 16, "bold")
        )
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 15))

        # 1. 网站URL
        ttk.Label(main_frame, text="网站URL:").grid(row=1, column=0, sticky=tk.W, pady=8)
        self.url_entry = ttk.Entry(main_frame, width=50)
        self.url_entry.grid(row=1, column=1, columnspan=2, pady=8, sticky=tk.EW)
        self.url_entry.insert(0, "https://www.zhaopin.com/sou/jl530/kw010G0I8/p1")

        # 2. 关键字
        ttk.Label(main_frame, text="关键字:").grid(row=2, column=0, sticky=tk.W, pady=8)
        self.keywords_entry = ttk.Entry(main_frame, width=50)
        self.keywords_entry.grid(row=2, column=1, columnspan=2, pady=8, sticky=tk.EW)
        self.keywords_entry.insert(0, "AI 人工智能")

        # 关键字提示
        hint_label = ttk.Label(
            main_frame,
            text="(多个关键字用空格隔开,包含任一即匹配)",
            font=("Microsoft YaHei", 8),
            foreground="gray"
        )
        hint_label.grid(row=3, column=1, sticky=tk.W, pady=(0, 8))

        # 3. 排除关键字
        ttk.Label(main_frame, text="排除关键字:").grid(row=4, column=0, sticky=tk.W, pady=8)
        self.exclude_entry = ttk.Entry(main_frame, width=50)
        self.exclude_entry.grid(row=4, column=1, columnspan=2, pady=8, sticky=tk.EW)
        self.exclude_entry.insert(0, "校招 实习生")

        # 排除关键字提示
        exclude_hint_label = ttk.Label(
            main_frame,
            text="(职位包含这些关键字将跳过,留空则不过滤)",
            font=("Microsoft YaHei", 8),
            foreground="orange"
        )
        exclude_hint_label.grid(row=5, column=1, sticky=tk.W, pady=(0, 8))

        # 4. 最大职位个数
        ttk.Label(main_frame, text="最大职位数:").grid(row=6, column=0, sticky=tk.W, pady=8)
        self.max_jobs_entry = ttk.Entry(main_frame, width=20)
        self.max_jobs_entry.grid(row=6, column=1, sticky=tk.W, pady=8)
        self.max_jobs_entry.insert(0, "30")  # 默认30个

        # 最大职位数提示
        max_hint_label = ttk.Label(
            main_frame,
            text="(留空表示搜索所有)",
            font=("Microsoft YaHei", 8),
            foreground="gray"
        )
        max_hint_label.grid(row=7, column=1, sticky=tk.W, pady=(0, 8))

        # 5. 输出文件名(CSV)
        ttk.Label(main_frame, text="输出文件(CSV):").grid(row=8, column=0, sticky=tk.W, pady=8)
        self.output_entry = ttk.Entry(main_frame, width=40)
        self.output_entry.grid(row=8, column=1, pady=8, sticky=tk.EW)

        # 默认输出文件名(CSV格式)
        default_output = os.path.join(os.path.dirname(__file__), "jobs_result.csv")
        self.output_entry.insert(0, default_output)

        # 浏览按钮
        browse_button = ttk.Button(
            main_frame,
            text="浏览...",
            command=self.browse_output_file,
            width=10
        )
        browse_button.grid(row=8, column=2, padx=(5, 0), pady=8)

        # 进度条
        progress_frame = ttk.LabelFrame(main_frame, text="搜索进度", padding="10")
        progress_frame.grid(row=9, column=0, columnspan=3, sticky=tk.EW, pady=(10, 10))

        self.progress_var = tk.DoubleVar(value=0)
        self.progress_bar = ttk.Progressbar(
            progress_frame,
            variable=self.progress_var,
            maximum=100,
            length=500,
            mode='determinate'
        )
        self.progress_bar.pack(fill=tk.X, pady=5)

        self.progress_label = ttk.Label(progress_frame, text="就绪", foreground="gray")
        self.progress_label.pack()

        # 日志输出区域
        log_frame = ttk.LabelFrame(main_frame, text="运行日志", padding="10")
        log_frame.grid(row=10, column=0, columnspan=3, sticky=tk.EW, pady=(0, 10))

        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            height=10,
            font=("Consolas", 9),
            wrap=tk.WORD
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)

        # 配置日志标签颜色
        self.log_text.tag_config("INFO", foreground="#2c3e50")
        self.log_text.tag_config("SUCCESS", foreground="#27ae60", font=("Consolas", 9, "bold"))
        self.log_text.tag_config("ERROR", foreground="#e74c3c", font=("Consolas", 9, "bold"))
        self.log_text.tag_config("WARNING", foreground="#f39c12")

        # 按钮框架
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=11, column=0, columnspan=3, pady=10)

        # 开始按钮
        self.start_button = ttk.Button(
            button_frame,
            text="开始查找",
            command=self.start_search,
            width=20
        )
        self.start_button.pack(side=tk.LEFT, padx=5)

        # 停止按钮
        self.stop_button = ttk.Button(
            button_frame,
            text="停止",
            command=self.stop_search,
            state=tk.DISABLED,
            width=20
        )
        self.stop_button.pack(side=tk.LEFT, padx=5)

        # 清空日志按钮
        clear_button = ttk.Button(
            button_frame,
            text="清空日志",
            command=self.clear_log,
            width=20
        )
        clear_button.pack(side=tk.LEFT, padx=5)

        # 状态栏
        self.status_var = tk.StringVar(value="就绪")
        status_bar = ttk.Label(
            self.root,
            textvariable=self.status_var,
            relief=tk.SUNKEN,
            anchor=tk.W
        )
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        main_frame.columnconfigure(1, weight=1)

    def browse_output_file(self):
        """浏览并选择输出文件"""
        file_path = filedialog.asksaveasfilename(
            title="选择输出文件",
            defaultextension=".csv",
            filetypes=[("CSV文件", "*.csv"), ("所有文件", "*.*")]
        )
        if file_path:
            self.output_entry.delete(0, tk.END)
            self.output_entry.insert(0, file_path)

    def log(self, message, level="INFO"):
        """添加日志信息"""
        self.log_text.insert(tk.END, message + "\n", level)
        self.log_text.see(tk.END)
        self.root.update_idletasks()

    def clear_log(self):
        """清空日志"""
        self.log_text.delete(1.0, tk.END)

    def update_progress(self, value, text):
        """更新进度条"""
        self.progress_var.set(value)
        self.progress_label.config(text=text)
        self.root.update_idletasks()

    def start_search(self):
        """开始搜索"""
        # 获取参数
        url = self.url_entry.get().strip()
        keywords_str = self.keywords_entry.get().strip()
        exclude_str = self.exclude_entry.get().strip()
        max_jobs_str = self.max_jobs_entry.get().strip()
        output_file = self.output_entry.get().strip()

        # 验证输入
        if not url:
            messagebox.showerror("错误", "请输入网站URL")
            return

        if not keywords_str:
            messagebox.showerror("错误", "请输入关键字")
            return

        if not output_file:
            messagebox.showerror("错误", "请指定输出文件")
            return

        # 解析关键字
        keywords = [k.strip() for k in keywords_str.split() if k.strip()]

        # 解析排除关键字
        exclude_keywords = [k.strip() for k in exclude_str.split() if k.strip()] if exclude_str else []

        # 解析最大职位数
        max_jobs = None
        if max_jobs_str:
            try:
                max_jobs = int(max_jobs_str)
                if max_jobs <= 0:
                    raise ValueError()
            except ValueError:
                messagebox.showerror("错误", "最大职位数必须是正整数")
                return

        # 清空并准备日志
        self.clear_log()
        self.update_progress(0, "准备中...")

        # 禁用开始按钮
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.is_running = True

        # 重定向print输出到日志框
        self._redirect_print()

        # 在新线程中执行搜索 - 始终使用无头模式
        thread = threading.Thread(
            target=self._run_search,
            args=(url, keywords, output_file, max_jobs, exclude_keywords),
            daemon=True
        )
        thread.start()

    def _redirect_print(self):
        """重定向print输出到日志框"""
        class TextRedirector:
            def __init__(self, widget, tag="INFO"):
                self.widget = widget
                self.tag = tag

            def write(self, text):
                if text.strip():
                    self.widget.insert(tk.END, text.strip(), self.tag)
                    self.widget.see(tk.END)
                    self.widget.update_idletasks()

            def flush(self):
                pass

        # 重定向stdout
        sys.stdout = TextRedirector(self.log_text, "INFO")
        sys.stderr = TextRedirector(self.log_text, "ERROR")

    def _restore_print(self):
        """恢复print输出"""
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__

    def _run_search(self, url, keywords, output_file, max_jobs, exclude_keywords):
        """在后台线程中运行搜索"""
        try:
            self.status_var.set("正在搜索...")
            self.log("===== 开始搜索 =====", "INFO")
            self.log(f"目标网站: {url}", "INFO")
            self.log(f"关键字: {', '.join(keywords)}", "INFO")
            if exclude_keywords:
                self.log(f"排除关键字: {', '.join(exclude_keywords)}", "WARNING")
            self.log(f"输出文件: {output_file}", "INFO")

            # 更新进度: 10%
            self.update_progress(10, "正在初始化浏览器...")

            # 定义进度回调函数
            def progress_callback(current, total, percent):
                """进度回调"""
                if max_jobs:
                    # 有最大数量限制时,显示 找到的数量/目标数量
                    progress_text = f"已找到: {current}/{total} 个职位"
                else:
                    # 没有最大数量限制时,显示 已找到数量
                    progress_text = f"已找到: {current} 个职位 (搜索中...)"

                self.update_progress(percent, progress_text)

            # 执行搜索 - 始终使用无头模式
            self.finder.find_jobs(
                url=url,
                keywords=keywords,
                output_file=output_file,
                max_jobs=max_jobs,
                headless=True,  # 固定为True,不再提供选项
                progress_callback=progress_callback,
                exclude_keywords=exclude_keywords
            )

            # 更新进度: 100%
            self.update_progress(100, "搜索完成!")

            self.log("===== 搜索完成 =====", "SUCCESS")
            self.status_var.set("搜索完成")

            # 检查文件是否生成
            if os.path.exists(output_file):
                file_size = os.path.getsize(output_file)
                self.log(f"✓ CSV文件已生成: {output_file}", "SUCCESS")
                self.log(f"✓ 文件大小: {file_size} 字节", "SUCCESS")

                # 读取并显示找到的职位数量
                with open(output_file, 'r', encoding='utf-8-sig') as f:
                    lines = f.readlines()
                    job_count = len(lines) - 1  # 减去表头
                    self.log(f"✓ 共保存 {job_count} 个职位", "SUCCESS")

                messagebox.showinfo(
                    "完成",
                    f"搜索完成!\n\n找到 {job_count} 个职位\n文件已保存到:\n{output_file}\n\n文件大小: {file_size} 字节"
                )
            else:
                self.log(f"✗ 警告: 文件未生成: {output_file}", "ERROR")
                messagebox.showwarning(
                    "警告",
                    f"搜索完成,但CSV文件未生成。\n\n请检查日志了解详情。"
                )

        except Exception as e:
            self.update_progress(0, "搜索失败")
            self.log(f"✗ 错误: {str(e)}", "ERROR")
            self.log("=" * 50, "ERROR")
            self.status_var.set("搜索失败")
            messagebox.showerror(
                "错误",
                f"搜索过程中发生错误:\n\n{str(e)}\n\n请查看日志了解详情。"
            )

        finally:
            # 恢复print输出
            self._restore_print()

            # 恢复按钮状态
            self.start_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
            self.is_running = False

    def stop_search(self):
        """停止搜索"""
        if self.is_running:
            self.is_running = False
            self.update_progress(0, "正在停止...")
            self.status_var.set("正在停止...")
            self.log("正在停止搜索...", "WARNING")


def main():
    """主函数"""
    root = tk.Tk()
    app = JobFinderGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
