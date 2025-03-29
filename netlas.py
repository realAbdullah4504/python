import json
import logging
import subprocess
import re

logger = logging.getLogger(__name__)


def remove_ansi_escape_sequences(text):
    """Removes ANSI escape sequences (like color codes) from text output."""
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)


def run_command(cmd, shell=False, remove_ansi_sequence=False):
    """Execute a shell command and return the output."""
    try:
        process = subprocess.Popen(
            cmd if shell else cmd.split(),
            shell=shell,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        output, error = process.communicate()
        
        if remove_ansi_sequence:
            output = remove_ansi_escape_sequences(output)

        if process.returncode != 0:
            logger.error(f"Command failed: {cmd}")
            logger.error(f"Error: {error.strip()}")
            return process.returncode, error.strip()

        return process.returncode, output.strip()
    
    except Exception as e:
        logger.error(f"Error executing command: {cmd}")
        logger.error(str(e))
        return -1, str(e)

def get_netlas_key():
    """Retrieve Netlas API key (replace with your method of storing the key)."""
    return "YOUR_NETLAS_API_KEY"

def fetch_whois_data_using_netlas(target):
    """
    Fetch WHOIS data using netlas.
    Args:
        target (str): IP address or domain name.
    Returns:
        dict: WHOIS information.
    """
    logger.info(f'Fetching WHOIS data for {target} using Netlas...')

    command = f'netlas host {target} -f json'
    netlas_key = '9ejZs2zirkpsnIQ5ZsYFsulnryPZRPxm'
    
    if netlas_key:
        command += f' -a {netlas_key}'

    try:
        _, result = run_command(command, remove_ansi_sequence=True)

        if "Failed to parse response data" in result:
            return {"status": False, "message": "Netlas limit exceeded."}
        if "api key doesn\'t exist" in result:
            return {"status": False, "message": "Invalid Netlas API Key!"}
        if "Request limit" in result:
            return {"status": False, "message": "Netlas request limit exceeded."}

        data = json.loads(result)

        if not data:
            return {"status": False, "message": "No data available for the given domain or IP."}

        return {"status": True, "data": data}

    except json.JSONDecodeError:
        return {"status": False, "message": "Failed to parse JSON response from Netlas."}
    except Exception as e:
        return {"status": False, "message": f"An error occurred: {str(e)}"}

# Example usage:
result = fetch_whois_data_using_netlas("google.com")
print(result)
