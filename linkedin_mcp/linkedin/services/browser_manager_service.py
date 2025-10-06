import time
from typing import Optional

import undetected_chromedriver as uc
from fake_useragent import UserAgent
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager


class BrowserManagerService:
    """Manages browser instances for LinkedIn automation."""

    def __init__(self, headless: bool = False, use_undetected: bool = True):
        self.headless = headless
        self.use_undetected = use_undetected
        self.driver: Optional[webdriver.Chrome] = None
        self.wait: Optional[WebDriverWait] = None

    def _get_chrome_options(self) -> Options:
        """Configure Chrome options for LinkedIn automation."""
        options = Options()

        if self.headless:
            options.add_argument("--headless")

        # Anti-detection options
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)

        # Performance options
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-plugins")
        options.add_argument("--disable-images")

        # User agent
        ua = UserAgent()
        options.add_argument(f"--user-agent={ua.random}")

        return options

    def start_browser(self) -> webdriver.Chrome:
        """Start and configure the browser."""
        options = self._get_chrome_options()

        if self.use_undetected:
            self.driver = uc.Chrome(options=options)
        else:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)

        # Remove webdriver property
        self.driver.execute_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )

        self.wait = WebDriverWait(self.driver, 10)
        return self.driver

    def close_browser(self):
        """Close the browser and cleanup."""
        if self.driver:
            self.driver.quit()
            self.driver = None
            self.wait = None

    def navigate_to_linkedin(self):
        """Navigate to LinkedIn homepage."""
        if not self.driver:
            raise RuntimeError("Browser not started. Call start_browser() first.")

        self.driver.get("https://www.linkedin.com")
        time.sleep(2)

    def wait_for_element(self, by: By, value: str, timeout: int = 10):
        """Wait for an element to be present."""
        if not self.wait:
            raise RuntimeError("Browser not started. Call start_browser() first.")

        return self.wait.until(EC.presence_of_element_located((by, value)))

    def wait_for_clickable(self, by: By, value: str, timeout: int = 10):
        """Wait for an element to be clickable."""
        if not self.wait:
            raise RuntimeError("Browser not started. Call start_browser() first.")

        return self.wait.until(EC.element_to_be_clickable((by, value)))

    def random_delay(self, min_seconds: float = 1.0, max_seconds: float = 3.0):
        """Add random delay to mimic human behavior."""
        import random

        delay = random.uniform(min_seconds, max_seconds)
        time.sleep(delay)
