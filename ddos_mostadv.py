import requests
import threading
import time
import sys
import random
import socket
from urllib.parse import urlparse
import json
from concurrent.futures import ThreadPoolExecutor
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

class BrowserVerificationDDoSTest:
    def __init__(self, url, threads=20, requests_per_thread=5):
        self.url = url
        self.threads = threads
        self.requests_per_thread = requests_per_thread
        self.success_count = 0
        self.error_count = 0
        self.start_time = None
        self.lock = threading.Lock()
        
        # Validate URL format
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            print("Invalid URL format. Please include http:// or https://")
            sys.exit(1)
        
        # Check if the server is reachable before starting the test
        self.check_server_reachable()
    
    def check_server_reachable(self):
        parsed = urlparse(self.url)
        host = parsed.hostname
        port = parsed.port or (443 if parsed.scheme == 'https' else 80)
        
        print(f"Checking if server at {host}:{port} is reachable...")
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((host, port))
            sock.close()
            
            if result != 0:
                print(f"ERROR: Server at {host}:{port} is not reachable!")
                print("Make sure your server is running and accessible from this machine.")
                sys.exit(1)
            else:
                print(f"Server at {host}:{port} is reachable. Starting test...")
        except Exception as e:
            print(f"ERROR: Failed to check server connectivity: {str(e)}")
            sys.exit(1)
    
    def browser_request(self):
        try:
            options = uc.ChromeOptions()
            options.add_argument('--headless')  # Run in background
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            options.add_argument('--window-size=1920,1080')
            
            # Create a new undetected Chrome driver
            driver = uc.Chrome(options=options)
            
            for _ in range(self.requests_per_thread):
                try:
                    # Random delay between requests
                    time.sleep(random.uniform(1, 3))
                    
                    # Navigate to the URL
                    driver.get(self.url)
                    
                    # Wait for the page to load or for verification to complete
                    try:
                        # Wait for either the verification to complete or timeout after 30 seconds
                        WebDriverWait(driver, 30).until(
                            lambda d: d.execute_script("return document.readyState") == "complete"
                        )
                        
                        # Check if we're still on a verification page
                        if "verifying" in driver.title.lower() or "challenge" in driver.title.lower():
                            # Try to wait for verification to complete
                            time.sleep(10)
                        
                        # Check if we successfully loaded the page
                        if "verifying" not in driver.title.lower() and "challenge" not in driver.title.lower():
                            with self.lock:
                                self.success_count += 1
                                print(f"Success: Page loaded successfully")
                        else:
                            with self.lock:
                                self.error_count += 1
                                print(f"Error: Still on verification page")
                    except TimeoutException:
                        with self.lock:
                            self.error_count += 1
                            print(f"Error: Timeout waiting for page load")
                except Exception as e:
                    with self.lock:
                        self.error_count += 1
                        print(f"Error during request: {str(e)}")
            
            driver.quit()
        except Exception as e:
            with self.lock:
                self.error_count += 1
                print(f"Error creating browser: {str(e)}")
    
    def run_test(self):
        self.start_time = time.time()
        
        print(f"Starting browser-based stress test on {self.url}")
        print(f"Using {self.threads} browser instances with {self.requests_per_thread} requests per instance")
        print(f"Total expected requests: {self.threads * self.requests_per_thread}")
        print("Note: This test uses actual browsers and will be slower but more realistic")
        
        # Use ThreadPoolExecutor for better thread management
        with ThreadPoolExecutor(max_workers=self.threads) as executor:
            for _ in range(self.threads):
                executor.submit(self.browser_request)
        
        elapsed_time = time.time() - self.start_time
        total_requests = self.threads * self.requests_per_thread
        
        print("\nTest Results:")
        print(f"Total requests sent: {total_requests}")
        print(f"Successful responses: {self.success_count}")
        print(f"Failed requests: {self.error_count}")
        print(f"Test duration: {elapsed_time:.2f} seconds")
        print(f"Requests per second: {total_requests/elapsed_time:.2f}")
        
        # Calculate success rate
        success_rate = (self.success_count / total_requests) * 100 if total_requests > 0 else 0
        print(f"Success rate: {success_rate:.2f}%")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python browser_ddos_test.py <URL> [threads] [requests_per_thread]")
        print("Example: python browser_ddos_test.py https://yourwebsite.com 10 3")
        print("\nNote: This script requires undetected-chromedriver. Install with:")
        print("pip install undetected-chromedriver")
        print("\nAlso make sure you have Chrome browser installed.")
        sys.exit(1)
    
    url = sys.argv[1]
    threads = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    requests_per_thread = int(sys.argv[3]) if len(sys.argv) > 3 else 3
    
    test = BrowserVerificationDDoSTest(url, threads, requests_per_thread)
    test.run_test()