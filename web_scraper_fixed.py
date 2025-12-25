"""
网页抓取模块 - 使用Selenium动态抓取招聘网站
修复版本 - 专门针对Windows 11 64位
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import subprocess
import os
import time
import platform


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
                chrome_options.add_argument('--headless=new')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--disable-software-rasterizer')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_argument('--log-level=3')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
            chrome_options.add_experimental_option('useAutomationExtension', False)

            # 尝试多种方式初始化ChromeDriver
            print("正在初始化ChromeDriver...")

            # 方法1: 直接使用系统ChromeDriver(如果已安装)
            try:
                self.driver = webdriver.Chrome(options=chrome_options)
                print("✓ 使用系统ChromeDriver成功")
            except:
                print("系统ChromeDriver不可用,尝试其他方法...")

                # 方法2: 使用webdriver-manager
                try:
                    from webdriver_manager.chrome import ChromeDriverManager
                    service = Service(ChromeDriverManager(driver_version="latest").install())
                    self.driver = webdriver.Chrome(service=service, options=chrome_options)
                    print("✓ 使用webdriver-manager成功")
                except Exception as e1:
                    print(f"webdriver-manager失败: {e1}")

                    # 方法3: 手动指定路径
                    try:
                        # 尝试常见路径
                        possible_paths = [
                            r"C:\chromedriver\chromedriver.exe",
                            r"C:\webdrivers\chromedriver.exe",
                            os.path.join(os.path.dirname(__file__), "chromedriver.exe"),
                        ]

                        driver_path = None
                        for path in possible_paths:
                            if os.path.exists(path):
                                driver_path = path
                                break

                        if driver_path:
                            service = Service(driver_path)
                            self.driver = webdriver.Chrome(service=service, options=chrome_options)
                            print(f"✓ 使用本地ChromeDriver成功: {driver_path}")
                        else:
                            raise Exception("找不到ChromeDriver")
                    except Exception as e2:
                        raise Exception(f"所有ChromeDriver初始化方法都失败了。请手动下载ChromeDriver:\n"
                                      f"1. 访问: https://googlechromelabs.github.io/chrome-for-testing/\n"
                                      f"2. 下载stable版本的chromedriver-win64.zip\n"
                                      f"3. 解压后将chromedriver.exe放到项目目录")

            self.wait = WebDriverWait(self.driver, 10)
            print("ChromeDriver初始化完成\n")

        except Exception as e:
            print(f"初始化ChromeDriver失败: {e}\n")
            raise

    def scrape_jobs(self, url, keywords, max_jobs=None):
        """
        抓取职位信息
        Args:
            url: 目标网站URL
            keywords: 关键字列表(只要包含任一关键字即匹配)
            max_jobs: 最大抓取职位数,None表示不限制
        Returns:
            list: 职位信息列表,包含title和url
        """
        jobs = []
        keyword_set = set(k.lower() for k in keywords if k.strip())

        print(f"正在访问 {url}...")
        self.driver.get(url)

        # 等待页面加载
        time.sleep(8)

        # 滚动页面以加载所有内容
        print("正在加载页面内容...")
        for i in range(3):
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)

        # 回到顶部
        self.driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(2)

        # 查找所有链接元素
        print("正在搜索职位链接...")

        # 获取页面上所有的链接
        all_links = self.driver.find_elements(By.TAG_NAME, "a")
        print(f"找到 {len(all_links)} 个链接")

        seen_urls = set()

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

                # 去重
                if href in seen_urls:
                    continue
                seen_urls.add(href)

                # 检查是否包含关键字
                if self._match_keywords(text, keyword_set):
                    jobs.append({
                        'title': text,
                        'url': href
                    })
                    print(f"✓ [{len(jobs)}] {text[:50]}...")

            except Exception:
                continue

        return jobs

    def _is_job_link(self, href, text):
        """
        判断是否为职位链接
        """
        # 排除一些明显不是职位的链接
        exclude_keywords = ['login', 'register', 'home', 'index', 'about', 'contact',
                          'help', 'faq', 'privacy', 'terms', 'javascript:', 'mailto:',
                          'http', 'https', '.css', '.js', '.png', '.jpg', '.gif']

        href_lower = href.lower()

        # 排除包含排除关键字的链接
        for keyword in exclude_keywords:
            if keyword in href_lower:
                return False

        # 只保留包含job相关路径的链接
        job_indicators = ['job', 'position', 'career', 'recruit', '职位', 'campus']
        has_job_indicator = any(indicator in href_lower for indicator in job_indicators)

        # 或者文本看起来像职位标题(长度合理,不包含特殊符号)
        text_reasonable = 5 < len(text) < 100 and not text.startswith('>') and not text.endswith('...')

        return has_job_indicator or text_reasonable

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
