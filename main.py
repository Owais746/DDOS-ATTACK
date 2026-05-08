import subprocess
import sys
import time

# Check if URL argument is provided
if len(sys.argv) < 2:
    print("Usage: python main.py <url>")
    sys.exit(1)

url = sys.argv[1]

print(f"Starting loop for URL: {url}")

while True:
    try:
        # Run target file
        subprocess.run(
            ["python", "ddos_test.py", url],
            check=True
        )

        print("Script completed. Restarting in 2 seconds...\n")
        time.sleep(2)

    except KeyboardInterrupt:
        print("\nLoop stopped by user.")
        break

    except Exception as e:
        print(f"Error: {e}")
        print("Restarting in 2 seconds...\n")
        time.sleep(2)