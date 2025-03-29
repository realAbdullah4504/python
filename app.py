import os
import subprocess
import sys

# Configuration
EYEWITNESS_PATH = "./EyeWitness/Python/EyeWitness.py"  # Update if different
URL_FILE = "urls.txt"  # File containing URLs (one per line)
OUTPUT_DIR = "screenshots"  # Directory to store screenshots
TIMEOUT = 15  # Timeout per request (in seconds)
THREADS = 5  # Number of threads for parallel processing

def run_eyewitness():
    """Runs EyeWitness to capture screenshots."""
    if not os.path.exists(URL_FILE):
        print(f"❌ URL file '{URL_FILE}' not found!")
        sys.exit(1)

    # Ensure the output directory exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Construct the command
    cmd = [
    "python", EYEWITNESS_PATH,
    "-f", URL_FILE,
    "-d", OUTPUT_DIR,
    "--no-prompt",
    "--timeout", str(TIMEOUT),
    "--threads", str(THREADS),
    "--show-selenium"  # ✅ Forces Chrome to run on Windows
]

    print("🚀 Running EyeWitness to capture screenshots...")
    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        print(result.stdout)
        if result.stderr:
            print("⚠️ Errors:", result.stderr)
    except Exception as e:
        print(f"❌ Error running EyeWitness: {e}")
        sys.exit(1)

    print(f"✅ Screenshots saved in: {OUTPUT_DIR}")

if __name__ == "__main__":
    run_eyewitness()
