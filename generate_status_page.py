import requests
import socket
from datetime import datetime
from ping3 import ping
import concurrent.futures
import logging
from typing import Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

ping.EXCEPTIONS = True

API_URL = "https://api.brandmeister.network/v2/master"
TCP_PORT = 50180
HTTP_TIMEOUT = 3
MAX_WORKERS = 10

# Check TCP connection
def check_tcp(host: str, port: int, timeout: int = 3) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except Exception as e:
        logging.debug(f"TCP check failed for {host}: {str(e)}")
        return False

# Check HTTP connection
def check_http(address: str) -> bool:
    try:
        url = f"https://{address}"
        response = requests.get(url, timeout=HTTP_TIMEOUT, verify=False)
        return response.status_code == 200
    except Exception as e:
        logging.debug(f"HTTP check failed for {address}: {str(e)}")
        return False

# Check ICMP (ping)
def check_icmp(host: str) -> bool:
    try:
        response_time = ping(host, timeout=3)
        return response_time is not None
    except Exception as e:
        logging.debug(f"ICMP check failed for {host}: {str(e)}")
        return False

def check_server(server: Dict[str, Any]) -> Dict[str, Any]:
    address = server["address"]
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        tcp_future = executor.submit(check_tcp, address, TCP_PORT)
        http_future = executor.submit(check_http, address)
        icmp_future = executor.submit(check_icmp, address)
        
        return {
            "id": server["id"],
            "country": server["country"],
            "address": address,
            "tcp_ok": tcp_future.result(),
            "http_ok": http_future.result(),
            "icmp_ok": icmp_future.result()
        }

def main():
    try:
        response = requests.get(API_URL, timeout=10)
        response.raise_for_status()
        servers = response.json()
    except Exception as e:
        logging.error(f"Failed to get server list: {e}")
        return

    # Process servers in parallel
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        results = list(executor.map(check_server, servers))

    # Generate HTML with improved styling
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>BrandMeister Server Status</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            h1 { color: #333; }
            table { border-collapse: collapse; width: 100%; max-width: 1200px; margin: 20px 0; }
            th, td { padding: 12px; text-align: left; border: 1px solid #ddd; }
            th { background-color: #f5f5f5; }
            tr:nth-child(even) { background-color: #f9f9f9; }
            tr:hover { background-color: #f0f0f0; }
            .status { font-size: 1.2em; }
            .timestamp { color: #666; }
            @media (max-width: 768px) {
                table { font-size: 14px; }
                th, td { padding: 8px; }
            }
        </style>
    </head>
    <body>
    """
    
    html += f"<h1>BrandMeister Master Status</h1>"
    html += f"<p class='timestamp'>Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>"
    html += "<table>"
    html += "<tr><th>ID</th><th>Country</th><th>Address</th><th>TCP</th><th>HTTP</th><th>ICMP</th></tr>"

    for result in results:
        tcp_status = "🟢" if result["tcp_ok"] else "🔴"
        http_status = "🟢" if result["http_ok"] else "🔴"
        icmp_status = "🟢" if result["icmp_ok"] else "🔴"

        html += f"""
        <tr>
            <td>{result['id']}</td>
            <td>{result['country']}</td>
            <td>{result['address']}</td>
            <td class='status'>{tcp_status}</td>
            <td class='status'>{http_status}</td>
            <td class='status'>{icmp_status}</td>
        </tr>
        """

    html += "</table></body></html>"

    try:
        with open("index.html", "w", encoding='utf-8') as f:
            f.write(html)
        logging.info("HTML page successfully created: index.html")
    except Exception as e:
        logging.error(f"Failed to write HTML file: {e}")

if __name__ == "__main__":
    main()
