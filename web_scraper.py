"""
网页抓取模块 - 使用Selenium动态抓取招聘网站
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os


class JobScraper:
    def __init__(self, headless=True):
        """
        初始化Selenium WebDriver
        Args:
            headless: 是否使用无头模式(不显示浏览器窗口)
        """
        self.driver = None
        self.wait = None

        try:
            chrome_options = Options()
            if headless:
                chrome_options.add_argument('--headless=new')  # 使用新的headless模式
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--disable-software-rasterizer')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_argument('--log-level=3')  # 隐藏日志
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
            chrome_options.add_experimental_option('useAutomationExtension', False)

            # 自动下载并使用ChromeDriver
            print("正在初始化ChromeDriver...")

            # 方法1: 首先尝试使用系统ChromeDriver(如果有)
            try:
                self.driver = webdriver.Chrome(options=chrome_options)
                print("✓ 使用系统ChromeDriver")
            except:
                print("系统ChromeDriver不可用,尝试webdriver-manager...")
                # 方法2: 使用webdriver-manager
                try:
                    from webdriver_manager.chrome import ChromeDriverManager
                    service = Service(ChromeDriverManager(driver_version="latest").install())
                    self.driver = webdriver.Chrome(service=service, options=chrome_options)
                    print("✓ 使用webdriver-manager")
                except Exception as e:
                    # 方法3: 尝试项目目录中的chromedriver
                    driver_path = os.path.join(os.path.dirname(__file__), "chromedriver.exe")
                    if os.path.exists(driver_path):
                        service = Service(driver_path)
                        self.driver = webdriver.Chrome(service=service, options=chrome_options)
                        print(f"✓ 使用本地ChromeDriver: {driver_path}")
                    else:
                        raise Exception(
                            "ChromeDriver初始化失败!\n\n"
                            "请按照以下步骤手动安装ChromeDriver:\n"
                            "1. 访问: https://googlechromelabs.github.io/chrome-for-testing/\n"
                            "2. 点击 'stable' 版本\n"
                            "3. 下载 'win64' 版本的chromedriver-win64.zip\n"
                            "4. 解压后将chromedriver.exe放到项目目录:\n"
                            f"   {os.path.dirname(__file__)}\n"
                        )

            self.wait = WebDriverWait(self.driver, 10)
            print("ChromeDriver初始化完成")
        except Exception as e:
            print(f"初始化ChromeDriver失败: {e}")
            print("\n请尝试以下解决方案:")
            print("1. 确保已安装Chrome浏览器")
            print("2. 手动下载ChromeDriver: https://chromedriver.chromium.org/")
            print("3. 将ChromeDriver放到系统PATH或Python Scripts目录")
            raise

    def scrape_jobs(self, url, keywords, max_jobs=None, progress_callback=None, exclude_keywords=None):
        """
        抓取职位信息 - 支持多页抓取
        Args:
            url: 目标网站URL
            keywords: 关键字列表(只要包含任一关键字即匹配)
            max_jobs: 最大抓取职位数,None表示不限制
            progress_callback: 进度回调函数 callback(current, total, percent)
        Returns:
            list: 职位信息列表,包含title和url
        """
        jobs = []
        keyword_set = set(k.lower() for k in keywords if k.strip())
        exclude_set = set(k.lower() for k in exclude_keywords) if exclude_keywords else set()
        page_num = 1
        max_pages = 10  # 最多抓取10页,防止无限循环

        if exclude_set:
            print(f"已设置排除关键字: {', '.join(exclude_set)}")

        target_count = max_jobs if max_jobs else 100

        while page_num <= max_pages:
            # 检查是否已达到最大数量
            if max_jobs and len(jobs) >= max_jobs:
                print(f"\n已达到最大职位数: {max_jobs}")
                break

            print(f"\n===== 正在抓取第 {page_num} 页 =====")

            # 访问页面
            if page_num == 1:
                print(f"正在访问 {url}...")
                self.driver.get(url)
            else:
                # 后续页面已在翻页后加载
                print(f"当前页面: {self.driver.current_url}")

            # 等待页面完全加载 - 增加等待时间
            print("等待页面加载...")
            time.sleep(8)

            # 滚动页面以加载所有内容
            print("正在加载页面内容(滚动)...")
            for i in range(5):
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1)

            # 回到顶部
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(2)

            # 等待职位卡片加载
            print("等待职位卡片加载...")
            time.sleep(3)

            # 查找所有链接元素
            print("正在搜索职位链接...")

            # 获取页面上所有的链接
            all_links = self.driver.find_elements(By.TAG_NAME, "a")
            print(f"本页找到 {len(all_links)} 个链接")

            seen_urls = set()
            seen_titles = set()
            page_jobs = []  # 本页找到的职位

            for elem in all_links:
                # 检查是否已达到最大数量
                if max_jobs and len(jobs) >= max_jobs:
                    print(f"\n已达到最大职位数: {max_jobs}")
                    break

                try:
                    href = elem.get_attribute('href')
                    text = elem.text.strip()

                    if not href or not text:
                        continue

                    # 过滤: 只保留看起来像职位的链接
                    if not self._is_job_link(href, text):
                        continue

                    # 全局去重 - 检查是否在之前页面已抓取
                    if href in seen_urls:
                        continue
                    seen_urls.add(href)

                    # 标题去重(避免重复的职位标题)
                    text_normalized = text.lower().strip()
                    if text_normalized in seen_titles:
                        continue
                    seen_titles.add(text_normalized)

                    # 检查是否包含排除关键字
                    if exclude_set and self._match_keywords(text, exclude_set):
                        print(f"⊗ [跳过] {text[:60]}... (包含排除关键字)")
                        continue

                    # 检查是否包含关键字
                    if self._match_keywords(text, keyword_set):
                        job_info = {
                            'title': text,
                            'url': href
                        }
                        jobs.append(job_info)
                        page_jobs.append(job_info)
                        print(f"✓ [总计:{len(jobs)}] {text[:60]}...")

                        # 更新进度
                        if progress_callback:
                            percent = min(95, int((len(jobs) / target_count) * 100))
                            progress_callback(len(jobs), target_count, percent)

                except Exception:
                    continue

            print(f"本页找到 {len(page_jobs)} 个匹配职位")

            # 检查是否需要翻页
            if max_jobs and len(jobs) >= max_jobs:
                print(f"\n已达到最大职位数: {max_jobs},停止翻页")
                break

            if len(page_jobs) == 0:
                print(f"本页没有找到职位,可能已到最后一页")
                break

            # 尝试点击下一页
            print("\n尝试点击下一页...")

            # 智联招聘特殊处理: 直接修改URL中的页码
            if 'zhaopin.com' in self.driver.current_url:
                print("检测到智联招聘,尝试URL翻页...")
                current_url = self.driver.current_url
                # 将/p1改为/p2,或添加/p2
                if '/p1' in current_url or '/p1?' in current_url:
                    next_url = current_url.replace('/p1', '/p2')
                    print(f"下一页URL: {next_url}")
                    self.driver.get(next_url)
                    page_num += 1
                    time.sleep(5)
                    continue
                elif '.com/' in current_url and '/p' not in current_url.split('.com/')[-1]:
                    # URL中没有页码,添加/p2
                    next_url = current_url.rstrip('/') + '/p2'
                    print(f"下一页URL: {next_url}")
                    self.driver.get(next_url)
                    page_num += 1
                    time.sleep(5)
                    continue

            # 其他网站使用点击方式
            if not self._click_next_page():
                print("没有找到下一页按钮,抓取结束")
                break

            page_num += 1
            time.sleep(3)  # 等待下一页加载

        return jobs

    def _click_next_page(self):
        """
        尝试点击下一页按钮 - 增强版
        Returns:
            bool: True表示成功点击下一页,False表示没有下一页
        """
        try:
            print("正在查找下一页按钮...")

            # 方法1: 使用多种XPath选择器
            next_selectors = [
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
                "//a[contains(@class, 'Next')]",
                "//button[contains(@class, 'next')]",

                # 通用翻页按钮
                "//a[@aria-label='Next']",
                "//a[@aria-label='next']",
                "//button[@aria-label='Next']",

                # 智联招聘特定
                "//a[contains(@href, '/p2/')]",
                "//a[contains(@href, 'p2')]",
            ]

            for selector in next_selectors:
                try:
                    next_button = self.driver.find_element(By.XPATH, selector)
                    if next_button.is_display() and next_button.is_enabled():
                        print(f"✓ 找到下一页按钮: {selector}")
                        print(f"  按钮文本: {next_button.text}")
                        print(f"  按钮href: {next_button.get_attribute('href')}")
                        next_button.click()
                        time.sleep(1)
                        return True
                except Exception as e:
                    continue

            # 方法2: 查找所有包含"2"或"下一页"的链接
            print("尝试查找页码链接...")
            all_links = self.driver.find_elements(By.TAG_NAME, "a")
            for link in all_links:
                try:
                    text = link.text.strip()
                    href = link.get_attribute('href', '')

                    # 查找指向第2页的链接
                    if 'p2' in href or ('/p' in href and 'p1' not in href):
                        if link.is_display() and link.is_enabled():
                            print(f"✓ 找到第2页链接")
                            print(f"  文本: {text}")
                            print(f"  href: {href}")
                            link.click()
                            time.sleep(1)
                            return True

                    # 查找包含数字2的翻页链接
                    if text == '2' or text == '2 ' or text == ' 2':
                        if link.is_display() and link.is_enabled():
                            print(f"✓ 找到页码2链接")
                            link.click()
                            time.sleep(1)
                            return True
                except:
                    continue

            # 方法3: 打印所有链接用于调试
            print("\n调试信息: 页面上的前30个链接")
            all_links = self.driver.find_elements(By.TAG_NAME, "a")
            for i, link in enumerate(all_links[:30]):  # 显示前30个
                try:
                    text = link.text.strip()
                    href = link.get_attribute('href', '')
                    if text and len(text) > 0:  # 只显示有文本的链接
                        print(f"  [{i}] 文本='{text[:50]}' href='{href[:80]}'")
                except:
                    pass

            print("未找到可用的下一页按钮")
            return False

        except Exception as e:
            print(f"点击下一页时出错: {e}")
            import traceback
            traceback.print_exc()
            return False

    def _is_job_link(self, href, text):
        """
        判断是否为职位链接 - 放宽条件以减少漏抓
        """
        # 排除一些明显不是职位的链接
        exclude_keywords = ['login', 'register', 'home', 'sitemap', 'about', 'contact',
                          'help', 'faq', 'privacy', 'terms', 'javascript:', 'mailto:',
                          '.css', '.js', '.png', '.jpg', '.gif', '.svg', '.woff', '.ttf',
                          '#', 'tel:', 'weixin:', 'download']

        href_lower = href.lower()

        # 排除包含排除关键字的链接
        for keyword in exclude_keywords:
            if keyword in href_lower:
                return False

        # 排除纯域名链接
        if href_lower.count('/') <= 2:  # 只有协议+域名
            return False

        # 文本长度检查 - 放宽限制
        if len(text) < 3 or len(text) > 200:
            return False

        # 排除纯数字或特殊符号的文本
        if text.strip().isdigit() or not any(c.isalpha() or '\u4e00' <= c <= '\u9fff' for c in text):
            return False

        # 只要有合理的文本长度,就认为是职位相关(大幅放宽条件)
        return True

    def _match_keywords(self, text, keywords):
        """
        检查文本是否包含任一关键字
        Args:
            text: 要检查的文本
            keywords: 关键字集合
        Returns:
            bool: True表示匹配,False表示不匹配
        """
        text_lower = text.lower()
        for keyword in keywords:
            if keyword in text_lower:
                return True
        return False

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
