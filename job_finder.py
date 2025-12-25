"""
职位查找器 - 核心逻辑
"""

from web_scraper import JobScraper
import os
from datetime import datetime


class JobFinder:
    def __init__(self):
        """初始化职位查找器"""
        pass

    def find_jobs(self, url, keywords, output_file, max_jobs=None, headless=True, progress_callback=None, exclude_keywords=None):
        """
        查找职位并保存到文件
        Args:
            url: 招聘网站URL
            keywords: 关键字列表
            output_file: 输出文件路径
            max_jobs: 最大抓取职位数,None表示不限制
            headless: 是否使用无头浏览器
            progress_callback: 进度回调函数 callback(current, total, percent)
            exclude_keywords: 排除关键字列表
        """
        print("=" * 60)
        print("职位查找器启动")
        print("=" * 60)
        print(f"目标网站: {url}")
        print(f"关键字: {', '.join(keywords)}")
        if exclude_keywords:
            print(f"排除关键字: {', '.join(exclude_keywords)}")
        print(f"最大职位数: {'不限' if max_jobs is None else max_jobs}")
        print(f"输出文件: {output_file}")
        print("=" * 60)

        # 网页抓取
        print("\n正在抓取职位信息...")
        scraper = JobScraper(headless=headless)

        try:
            jobs = scraper.scrape_jobs(url, keywords, max_jobs, progress_callback, exclude_keywords)

            if not jobs:
                print("未找到匹配的职位信息")
                return

            print(f"\n✓ 成功找到 {len(jobs)} 个匹配职位")

        except Exception as e:
            print(f"✗ 抓取职位失败: {e}")
            return
        finally:
            scraper.close()

        # 保存结果
        print(f"\n正在保存结果到 {output_file}...")
        self._save_results(jobs, output_file, keywords)

        print("\n" + "=" * 60)
        print("✓ 任务完成!")
        print(f"✓ 共找到 {len(jobs)} 个职位")
        print(f"✓ 结果已保存到: {output_file}")
        print("=" * 60)

    def _save_results(self, jobs, output_file, keywords):
        """
        保存职位信息到CSV文件
        Args:
            jobs: 职位信息列表
            output_file: 输出文件路径
            keywords: 搜索关键字
        """
        import csv

        # 确保目录存在
        dir_path = os.path.dirname(output_file)
        if dir_path:
            os.makedirs(dir_path, exist_ok=True)

        # 如果文件名不是.csv,自动添加.csv扩展名
        if not output_file.endswith('.csv'):
            output_file = output_file.rsplit('.', 1)[0] + '.csv'

        with open(output_file, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.writer(f)

            # 写入CSV头部
            writer.writerow(['职位标题', '职位链接'])

            # 写入职位数据
            for job in jobs:
                writer.writerow([
                    job.get('title', '未知'),
                    job.get('url', '')
                ])

        print(f"CSV格式: 第一列=职位标题, 第二列=职位链接")
