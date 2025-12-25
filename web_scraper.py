"""
网页抓取模块 - 使用Selenium动态抓取招聘网站

功能:
- 支持多页抓取
- 自动识别招聘网站类型(智联、猎聘等)
- 智能翻页(直接修改URL参数)
- 职位过滤和去重
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os
import re


class JobScraper:
    """职位抓取器 - 自动抓取招聘网站职位信息"""

    def __init__(self, headless=True):
        """
        初始化Selenium WebDriver
        Args:
            headless: 是否使用无头模式(不显示浏览器窗口)
        """
        self.driver = None
        self.wait = None

        try:
            self._init_driver(headless)
            print("ChromeDriver初始化完成")
        except Exception as e:
            print(f"初始化ChromeDriver失败: {e}")
            self._print_install_guide()
            raise

    def _init_driver(self, headless):
        """初始化ChromeDriver"""
        chrome_options = self._get_chrome_options(headless)
        print("正在初始化ChromeDriver...")

        # 尝试多种方式初始化ChromeDriver
        if self._try_system_driver(chrome_options):
            print("✓ 使用系统ChromeDriver")
        elif self._try_webdriver_manager(chrome_options):
            print("✓ 使用webdriver-manager")
        elif self._try_local_driver(chrome_options):
            print("✓ 使用本地ChromeDriver")
        else:
            raise Exception("所有ChromeDriver初始化方法都失败")

        self.wait = WebDriverWait(self.driver, 10)

    def _get_chrome_options(self, headless):
        """获取Chrome配置选项"""
        options = Options()
        if headless:
            options.add_argument('--headless=new')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-software-rasterizer')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--log-level=3')
        options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
        options.add_experimental_option('useAutomationExtension', False)
        return options

    def _try_system_driver(self, options):
        """尝试使用系统ChromeDriver"""
        try:
            self.driver = webdriver.Chrome(options=options)
            return True
        except:
            return False

    def _try_webdriver_manager(self, options):
        """尝试使用webdriver-manager自动下载"""
        try:
            from webdriver_manager.chrome import ChromeDriverManager
            service = Service(ChromeDriverManager(driver_version="latest").install())
            self.driver = webdriver.Chrome(service=service, options=options)
            return True
        except:
            return False

    def _try_local_driver(self, options):
        """尝试使用项目目录中的ChromeDriver"""
        driver_path = os.path.join(os.path.dirname(__file__), "chromedriver.exe")
        if os.path.exists(driver_path):
            try:
                service = Service(driver_path)
                self.driver = webdriver.Chrome(service=service, options=options)
                return True
            except:
                pass
        return False

    def _print_install_guide(self):
        """打印ChromeDriver安装指南"""
        print("\n请尝试以下解决方案:")
        print("1. 确保已安装Chrome浏览器")
        print("2. 手动下载ChromeDriver: https://googlechromelabs.github.io/chrome-for-testing/")
        print("3. 下载stable版本的win64 chromedriver-win64.zip")
        print("4. 解压后将chromedriver.exe放到项目目录")
        print(f"   目录: {os.path.dirname(__file__)}")

    def scrape_jobs(self, url, keywords, max_jobs=None, progress_callback=None, exclude_keywords=None):
        """
        抓取职位信息 - 主入口方法
        Args:
            url: 目标网站URL
            keywords: 匹配关键字列表(只要包含任一即匹配)
            max_jobs: 最大抓取职位数,None表示不限制
            progress_callback: 进度回调函数 callback(current, total, percent)
            exclude_keywords: 排除关键字列表
        Returns:
            list: 职位信息列表,包含title和url
        """
        jobs = []
        keyword_set = self._normalize_keywords(keywords)
        exclude_set = self._normalize_keywords(exclude_keywords) if exclude_keywords else set()
        page_num = 1
        max_pages = 10

        if exclude_set:
            print(f"已设置排除关键字: {', '.join(exclude_set)}")

        target_count = max_jobs if max_jobs else 100

        # 多页抓取循环
        while page_num <= max_pages:
            # 检查是否达到最大数量
            if max_jobs and len(jobs) >= max_jobs:
                print(f"\n已达到最大职位数: {max_jobs}")
                break

            print(f"\n===== 正在抓取第 {page_num} 页 =====")

            # 访问页面
            self._visit_page(url, page_num)

            # 等待页面加载
            self._wait_for_page_load()

            # 抓取当前页职位
            page_jobs = self._scrape_current_page(keyword_set, exclude_set, target_count, jobs, progress_callback)

            print(f"本页找到 {len(page_jobs)} 个匹配职位")

            # 检查是否需要翻页
            if self._should_stop_paging(jobs, max_jobs, page_jobs):
                break

            # 翻页
            if not self._go_to_next_page(url, page_num):
                break

            page_num += 1

        return jobs

    def _normalize_keywords(self, keywords):
        """标准化关键字(转小写去空)"""
        if not keywords:
            return set()
        return set(k.lower() for k in keywords if k.strip())

    def _visit_page(self, base_url, page_num):
        """访问指定页面"""
        if page_num == 1:
            print(f"正在访问 {base_url}...")
            self.driver.get(base_url)
        else:
            print(f"当前页面: {self.driver.current_url}")

    def _wait_for_page_load(self):
        """等待页面完全加载"""
        print("等待页面加载...")
        time.sleep(8)

        print("正在加载页面内容(滚动)...")
        for _ in range(5):
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1)

        self.driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(2)

        print("等待职位卡片加载...")
        time.sleep(3)

    def _scrape_current_page(self, keyword_set, exclude_set, target_count, jobs, progress_callback):
        """
        抓取当前页的职位信息
        Returns:
            list: 本页找到的职位列表
        """
        print("正在搜索职位链接...")

        all_links = self.driver.find_elements(By.TAG_NAME, "a")
        print(f"本页找到 {len(all_links)} 个链接")

        seen_urls = set()
        seen_titles = set()
        page_jobs = []

        for elem in all_links:
            # 检查是否已达到最大数量
            if target_count and len(jobs) >= target_count:
                break

            try:
                href = elem.get_attribute('href')
                text = elem.text.strip()

                if not href or not text:
                    continue

                # 过滤非职位链接
                if not self._is_valid_job_link(href, text):
                    continue

                # 去重
                if not self._is_unique_job(href, text, seen_urls, seen_titles):
                    continue

                seen_urls.add(href)
                seen_titles.add(text.lower().strip())

                # 排除关键字过滤
                if exclude_set and self._match_keywords(text, exclude_set):
                    print(f"⊗ [跳过] {text[:60]}... (包含排除关键字)")
                    continue

                # 匹配关键字
                if self._match_keywords(text, keyword_set):
                    job_info = {'title': text, 'url': href}
                    jobs.append(job_info)
                    page_jobs.append(job_info)
                    print(f"✓ [总计:{len(jobs)}] {text[:60]}...")

                    # 更新进度
                    if progress_callback:
                        percent = min(95, int((len(jobs) / target_count) * 100))
                        progress_callback(len(jobs), target_count, percent)

            except Exception:
                continue

        return page_jobs

    def _is_valid_job_link(self, href, text):
        """判断是否为有效的职位链接"""
        # 排除明显不是职位的链接
        exclude_patterns = [
            'login', 'register', 'home', 'sitemap', 'about', 'contact',
            'help', 'faq', 'privacy', 'terms', 'javascript:', 'mailto:',
            '.css', '.js', '.png', '.jpg', '.gif', '.svg', '.woff', '.ttf',
            '#', 'tel:', 'weixin:', 'download'
        ]

        href_lower = href.lower()

        # 检查排除模式
        for pattern in exclude_patterns:
            if pattern in href_lower:
                return False

        # 排除纯域名链接
        if href_lower.count('/') <= 2:
            return False

        # 文本长度检查
        if not (3 <= len(text) <= 200):
            return False

        # 排除纯数字或特殊符号
        if text.strip().isdigit():
            return False

        return True

    def _is_unique_job(self, href, text, seen_urls, seen_titles):
        """检查职位是否唯一"""
        if href in seen_urls:
            return False
        if text.lower().strip() in seen_titles:
            return False
        return True

    def _match_keywords(self, text, keywords):
        """检查文本是否包含任一关键字"""
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in keywords)

    def _should_stop_paging(self, jobs, max_jobs, page_jobs):
        """判断是否应该停止翻页"""
        if max_jobs and len(jobs) >= max_jobs:
            print(f"已达到最大职位数: {max_jobs},停止翻页")
            return True

        if len(page_jobs) == 0:
            print("本页没有找到职位,可能已到最后一页")
            return True

        return False

    def _go_to_next_page(self, url, page_num):
        """
        翻到下一页
        Returns:
            bool: True表示成功翻页,False表示失败
        """
        print("\n尝试点击下一页...")

        current_url = self.driver.current_url

        # 智联招聘: /p1 -> /p2 -> /p3
        if 'zhaopin.com' in current_url:
            return self._paginate_zhaopin(current_url)

        # 猎聘: currentPage=0 -> currentPage=1
        elif 'liepin.com' in current_url:
            return self._paginate_liepin(current_url)

        # 其他网站: 尝试点击按钮
        else:
            return self._click_next_button()

    def _paginate_zhaopin(self, current_url):
        """智联招聘翻页策略"""
        print("检测到智联招聘,尝试URL翻页...")
        print(f"当前URL: {current_url}")

        # 提取并递增页码
        page_match = re.search(r'/p(\d+)', current_url)

        if page_match:
            current_page = int(page_match.group(1))
            next_page = current_page + 1
            next_url = re.sub(r'/p\d+', f'/p{next_page}', current_url)
            print(f"当前页码: p{current_page}, 下一页: p{next_page}")
        else:
            # URL中没有页码,添加/p2
            next_url = current_url.rstrip('/') + '/p2'
            print(f"添加页码: p2")

        print(f"下一页URL: {next_url}")
        self.driver.get(next_url)
        time.sleep(5)
        return True

    def _paginate_liepin(self, current_url):
        """猎聘翻页策略"""
        print("检测到猎聘,尝试URL翻页...")

        # 提取并递增currentPage参数
        page_match = re.search(r'currentPage=(\d+)', current_url)

        if page_match:
            current_page = int(page_match.group(1))
            next_page = current_page + 1
            next_url = re.sub(r'currentPage=\d+', f'currentPage={next_page}', current_url)
            print(f"当前页码: {current_page}, 下一页: {next_page}")
        else:
            # URL中没有currentPage,添加currentPage=1
            separator = '&' if '?' in current_url else '?'
            next_url = current_url + separator + 'currentPage=1'
            print(f"添加页码: currentPage=1")

        print(f"下一页URL: {next_url}")
        self.driver.get(next_url)
        time.sleep(5)
        return True

    def _click_next_button(self):
        """
        尝试点击下一页按钮(通用方法)
        Returns:
            bool: 是否成功点击
        """
        print("正在查找下一页按钮...")

        # 定义多种选择器
        selectors = [
            # 文本匹配
            "//a[contains(text(), '下一页')]",
            "//a[contains(text(), '下一页>')]",
            "//a[contains(text(), '»')]",
            "//a[contains(text(), '>')]",
            "//span[contains(text(), '下一页')]/parent::a",
            "//button[contains(text(), '下一页')]",
            # class属性匹配
            "//a[contains(@class, 'next')]",
            "//li[contains(@class, 'next')]/a",
            "//li[contains(@class, 'Next')]/a",
            "//button[contains(@class, 'next')]",
            # 通用翻页
            "//a[@aria-label='Next']",
            "//a[@aria-label='next']",
        ]

        # 尝试每个选择器
        for selector in selectors:
            try:
                next_button = self.driver.find_element(By.XPATH, selector)
                if next_button.is_display() and next_button.is_enabled():
                    print(f"✓ 找到下一页按钮")
                    self.driver.execute_script("arguments[0].click();", next_button)
                    time.sleep(1)
                    return True
            except:
                continue

        # 尝试查找页码链接(如"2")
        print("尝试查找页码链接...")
        all_links = self.driver.find_elements(By.TAG_NAME, "a")
        for link in all_links:
            try:
                href = link.get_attribute('href', '')
                text = link.text.strip()

                # 查找指向第2页的链接
                if ('/p2' in href or '/p2?' in href or 'currentPage=1' in href):
                    if link.is_display() and link.is_enabled():
                        print(f"✓ 找到第2页链接")
                        link.click()
                        time.sleep(1)
                        return True

                # 查找包含数字2的翻页链接
                if text == '2':
                    if link.is_display() and link.is_enabled():
                        print(f"✓ 找到页码2链接")
                        link.click()
                        time.sleep(1)
                        return True
            except:
                continue

        # 调试信息
        self._print_page_links_debug()

        print("未找到可用的下一页按钮")
        return False

    def _print_page_links_debug(self):
        """打印页面链接用于调试"""
        print("\n调试信息: 页面上的前30个链接")
        all_links = self.driver.find_elements(By.TAG_NAME, "a")
        for i, link in enumerate(all_links[:30]):
            try:
                text = link.text.strip()
                href = link.get_attribute('href', '')
                if text:
                    print(f"  [{i}] 文本='{text[:50]}' href='{href[:80]}'")
            except:
                pass

    def close(self):
        """关闭浏览器"""
        if hasattr(self, 'driver') and self.driver:
            try:
                self.driver.quit()
                print("\n浏览器已关闭")
            except:
                pass

    def __del__(self):
        """析构函数,确保浏览器被关闭"""
        try:
            self.close()
        except:
            pass
