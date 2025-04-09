import requests
import socket
from datetime import datetime
from ping3 import ping

ping.EXCEPTIONS = True

API_URL = "https://api.brandmeister.network/v2/master"
TCP_PORT = 50180
HTTP_TIMEOUT = 3

# Check TCP connection
def check_tcp(host, port, timeout=3):
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except Exception:
        return False

# Check HTTP connection
def check_http(address):
    try:
        url = f"http://{address}"
        response = requests.get(url, timeout=HTTP_TIMEOUT)
        return response.status_code == 200
    except Exception:
        return False

# Check ICMP (ping)
def check_icmp(host):
    try:
        response_time = ping(host, timeout=3)  # Ping timeout of 3 seconds
        return response_time is not None
    except exceptions.PingError:
        return False

def main():
    try:
        response = requests.get(API_URL, timeout=10)
        response.raise_for_status()
        servers = response.json()
    except Exception as e:
        print(f" Не удалось получить список серверов: {e}")
        return

    html = "<html><head><title>BrandMeister Server Status</title></head><body>"
    html += f"<h1>BrandMeister master status</h1>"
    html += f"<p>Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>"
    html += "<table border='1' cellpadding='5' cellspacing='0'>"
    html += (
        f"<tr><th>ID</th><th>Страна</th><th>Адрес</th><th>TCP {TCP_PORT}</th><th>HTTP</th><th>ICMP</th></tr>"
    )

    for server in servers:
        server_id = server["id"]
        address = server["address"]
        country = server["country"]

        tcp_ok = check_tcp(address, TCP_PORT)
        http_ok = check_http(address)
        icmp_ok = check_icmp(address)

        tcp_status = "🟢" if tcp_ok else "🔴"
        http_status = "🟢" if http_ok else "🔴"
        icmp_status = "🟢" if icmp_ok else "🔴"

        html += f"<tr><td>{server_id}</td><td>{country}</td><td>{address}</td><td>{tcp_status}</td><td>{http_status}</td><td>{icmp_status}</td></tr>"

    html += "</table></body></html>"

    with open("index.html", "w") as f:
        f.write(html)

    print(" HTML-страница успешно создана: index.html")

if __name__ == "__main__":
    main()
