import random
import time
from typing import Optional

import undetected_chromedriver as uc
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

from linkedin_mcp.linkedin.interfaces.services import IBrowserManager
from linkedin_mcp.linkedin.utils.logging_config import get_mcp_logger
from linkedin_mcp.linkedin.utils.user_agent_rotator import user_agent_rotator


class BrowserManagerService(IBrowserManager):
    """Manages browser instances for LinkedIn automation."""

    def __init__(self, headless: bool = False, use_undetected: bool = True):
        self.headless = headless
        self.use_undetected = use_undetected
        self.driver: Optional[webdriver.Chrome] = None
        self.wait: Optional[WebDriverWait] = None
        self.viewport_sizes = [
            (1920, 1080),
            (1366, 768),
            (1536, 864),
            (1440, 900),
            (1280, 720),
        ]

    def _get_chrome_options(self) -> Options:
        """Configure Chrome options for LinkedIn automation."""
        options = Options()
        logger = get_mcp_logger("browser-manager")

        # Random viewport size
        if not self.headless:
            width, height = random.choice(self.viewport_sizes)
            options.add_argument(f"--window-size={width},{height}")
            # Random window position
            x_pos = random.randint(0, 100)
            y_pos = random.randint(0, 100)
            options.add_argument(f"--window-position={x_pos},{y_pos}")
        else:
            options.add_argument("--headless")

        # Basic options for compatibility
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")

        # Anti-detection experimental options (removed problematic ones)
        # options.add_experimental_option("excludeSwitches", ["enable-automation"])
        # options.add_experimental_option("useAutomationExtension", False)

        # Performance options
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-plugins")
        options.add_argument("--disable-images")

        # Use random user agent for each session
        random_user_agent = user_agent_rotator.get_random_user_agent()
        options.add_argument(f"--user-agent={random_user_agent}")
        logger.info(f"Using user agent: {random_user_agent[:80]}...")

        return options

    def start_browser(self) -> webdriver.Chrome:
        """Start and configure the browser."""
        options = self._get_chrome_options()

        if self.use_undetected:
            # Let undetected_chromedriver auto-detect the Chrome version
            self.driver = uc.Chrome(options=options)
        else:
            # Auto-install compatible ChromeDriver version
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

    # Interface methods
    def get_driver(self):
        """Get the current WebDriver instance."""
        if not self.driver:
            self.start_browser()
        return self.driver

    def navigate_to_job(self, job_id: str) -> None:
        """Navigate to a specific job page."""
        if not self.driver:
            self.start_browser()

        job_url = f"https://www.linkedin.com/jobs/view/{job_id}/"
        self.driver.get(job_url)

        # Wait for page to load
        self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "main")))

    def cleanup(self) -> None:
        """Clean up browser resources."""
        self.close_browser()

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
        delay = random.uniform(min_seconds, max_seconds)
        time.sleep(delay)

    def human_type(self, element, text: str):
        """Type text with human-like patterns."""
        element.clear()
        for char in text:
            element.send_keys(char)
            # Random typing speed
            time.sleep(random.uniform(0.05, 0.2))
            # Occasional longer pauses (like thinking)
            if random.random() < 0.1:
                time.sleep(random.uniform(0.3, 0.8))

    def random_scroll(self):
        """Add random scrolling to mimic human browsing."""
        if self.driver:
            # Random scroll direction and amount
            scroll_amount = random.randint(-300, 300)
            self.driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
            time.sleep(random.uniform(0.5, 1.5))

    def human_click(self, element):
        """Click with human-like mouse movement."""
        if self.driver:
            # Move to element with slight randomness
            actions = ActionChains(self.driver)
            actions.move_to_element_with_offset(
                element, random.randint(-5, 5), random.randint(-5, 5)
            )
            actions.pause(random.uniform(0.1, 0.3))
            actions.click()
            actions.perform()
            time.sleep(random.uniform(0.2, 0.6))

    def random_mouse_movement(self):
        """Add random mouse movements to appear more human."""
        if self.driver:
            actions = ActionChains(self.driver)
            # Random movements
            for _ in range(random.randint(1, 3)):
                x_offset = random.randint(-100, 100)
                y_offset = random.randint(-100, 100)
                actions.move_by_offset(x_offset, y_offset)
                actions.pause(random.uniform(0.1, 0.5))
            actions.perform()
