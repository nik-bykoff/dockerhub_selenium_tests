import unittest
import time
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium_stealth import stealth

BASE_URL = "https://hub.docker.com"
TIMEOUT = 25 
USERNAME = os.getenv("DOCKER_USER")
PASSWORD = os.getenv("DOCKER_PASS")

class DockerHubAutomationSuite(unittest.TestCase):

    def setUp(self):
        # Chrome setup
        options = Options()
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--window-size=1920,1080")

        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()), 
            options=options
        )

        # Stealth settings
        stealth(self.driver,
                languages="uk",
                vendor="Google Inc.",
                platform="MacIntel",
                webgl_vendor="Intel Inc.",
                renderer="Intel Iris OpenGL Engine",
                fix_hairline=True,
        )
        
        self.wait = WebDriverWait(self.driver, TIMEOUT)
        self.driver.get(BASE_URL)

    def tearDown(self):
        if self.driver:
            self.driver.quit()

    # Helper for React inputs
    def safe_type(self, element, text):
        try:
            element.click()
            element.clear()
            element.send_keys(text)
        except:
            time.sleep(0.3)
            element = self.wait.until(EC.visibility_of(element))
            element.click()
            element.send_keys(text)
            
    def test_01_authentication_flow(self):
        print("Running auth test...")
        self.driver.get(f"{BASE_URL}/login")
        
        if not USERNAME or not PASSWORD:
            self.skipTest("Missing credentials")
            
        # Username input
        email_input = self.wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, "input[name='username'], *[autocomplete='username']")
        ))
        self.safe_type(email_input, USERNAME)
        
        # Continue
        continue_btn = self.wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//button[@type='submit']")
        ))
        continue_btn.click()
        
        # Password input
        password_input = self.wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, "input[name='password'], *[autocomplete='current-password']")
        ))
        self.safe_type(password_input, PASSWORD)
        
        # Sign in
        sign_in_btn = self.wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//button[@type='submit']")
        ))
        sign_in_btn.click()
        
        # Wait for redirect
        self.wait.until(lambda d: "/login" not in d.current_url)
        # Check avatar present
        self.wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, "header .MuiAvatar-root, header div[class*='Avatar']")
        ))
        print("Login OK")

    def test_02_search_functionality(self):
        print("Running search test...")
        self.driver.get(BASE_URL)
        
        # Open search
        search_button = self.wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, "button[data-heap='header-search-button']")
        ))
        search_button.click()
        
        # Type "python" and enter
        search_input = self.wait.until(EC.visibility_of_element_located(
            (By.CSS_SELECTOR, "input[placeholder='Search Docker Hub']")
        ))
        search_input.click()
        search_input.clear()
        search_input.send_keys("python")
        search_input.send_keys(Keys.RETURN)
        
        print("Waiting for results...")
        # First repo
        first_result = self.wait.until(EC.visibility_of_element_located(
            (By.CSS_SELECTOR, "a[data-testid='product-card-link']")
        ))
        self.assertIn("python", first_result.text.lower())
        
        # Check official badge
        card = first_result.find_element(By.XPATH, "./ancestor::div[contains(@class,'MuiPaper-root')]")
        official_badge = card.find_elements(
            By.CSS_SELECTOR, "div[data-testid='productBadge'], svg[data-testid='official-icon']"
        )
        self.assertTrue(len(official_badge) > 0, "Official badge missing")

    def test_03_repo_tags_verification(self):
        print("Checking repo tags...")
        self.driver.get(f"{BASE_URL}/_/alpine")

        tags_tab = self.wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//a[contains(@href,'tags')]")
        ))
        tags_tab.click()

        self.wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, "*[data-testid*='tag'], *[class*='tag']")
        ))
        self.assertIn("latest", self.driver.page_source.lower())
        print("'latest' tag found")

    def test_04_pull_command_verification(self):
        print("Checking pull command...")
        self.driver.get(f"{BASE_URL}/_/nginx")

        pull_cmd_element = self.wait.until(EC.presence_of_element_located(
            (By.XPATH, "//*[contains(text(),'docker pull')] | //input[contains(@value,'docker pull')]")
        ))

        command_text = pull_cmd_element.get_attribute("value") if pull_cmd_element.tag_name=="input" else pull_cmd_element.text
        print(f"Detected pull: {command_text}")
        self.assertIn("docker pull nginx", command_text.lower())

    def test_05_docs_navigation(self):
        print("Checking docs link...")
        self.driver.get(BASE_URL)
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

        docs_link = self.wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//footer//*[self::a and contains(@href,'docs.docker.com')]")
        ))

        orig_window = self.driver.current_window_handle
        docs_link.click()

        self.wait.until(EC.number_of_windows_to_be(2))

        for handle in self.driver.window_handles:
            if handle != orig_window:
                self.driver.switch_to.window(handle)
                break

        self.wait.until(EC.url_contains("docs.docker.com"))

        self.driver.close()
        self.driver.switch_to.window(orig_window)
        print("Docs link works")

if __name__ == "__main__":
    unittest.main()
