from selenium.webdriver.common.by import By

from linkedin_mcp.linkedin.services import AuthState, BrowserManager, LinkedInAuthGraph


class LinkedInAuthService:
    """Service for LinkedIn authentication."""

    def __init__(self):
        self.auth_graph = LinkedInAuthGraph()

    def authenticate(
        self, email: str, password: str, browser_manager: BrowserManager
    ) -> AuthState:
        """
        Authenticate with LinkedIn using provided credentials.

        Args:
            email: LinkedIn email
            password: LinkedIn password
            browser_manager: Browser manager instance

        Returns:
            AuthState with authentication result
        """
        return self.auth_graph.execute(email, password, browser_manager)

    def is_authenticated(self, browser_manager: BrowserManager) -> bool:
        """
        Check if currently authenticated with LinkedIn.

        Args:
            browser_manager: Browser manager instance

        Returns:
            True if authenticated, False otherwise
        """
        try:
            driver = browser_manager.driver
            if not driver:
                return False

            current_url = driver.current_url

            # Check if we're on a LinkedIn page that requires authentication
            if "linkedin.com" in current_url and "/login" not in current_url:
                # Look for user-specific elements
                try:
                    driver.find_element(
                        By.CSS_SELECTOR, '[data-test-id="nav-top-profile"]'
                    )
                    return True
                except:
                    try:
                        driver.find_element(
                            By.CSS_SELECTOR, 'input[aria-label*="Search job"]'
                        )
                        return True
                    except:
                        return False

            return False

        except Exception:
            return False
