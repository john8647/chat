import requests
import socket
import ssl

URL = "https://electrical-operator-brokers-engine.trycloudflare.com"


def comfyui_alive():
    try:
        r = requests.get(f"{URL}/api/version", timeout=5)
        print("FAILED")
        return r.status_code == 200
    except Exception:
        return False


def test_basic_request():
    print("\n=== BASIC REQUEST (no headers) ===")
    try:
        r = requests.get(URL, timeout=10)
        print("Status:", r.status_code)
        print("First 300 chars of response:")
        print(r.text[:300])
    except Exception as e:
        print("Error:", e)


def test_browser_headers():
    print("\n=== REQUEST WITH BROWSER HEADERS ===")
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "*/*",
        "Connection": "keep-alive"
    }
    try:
        r = requests.get(URL, headers=headers, timeout=10)
        print("Status:", r.status_code)
        print("First 300 chars of response:")
        print(r.text[:300])
    except Exception as e:
        print("Error:", e)


def test_dns():
    print("\n=== DNS RESOLUTION TEST ===")
    try:
        host = URL.split("/")[2]
        print("Resolving:", host)
        print("IP:", socket.gethostbyname(host))
    except Exception as e:
        print("DNS Error:", e)


def test_ssl():
    print("\n=== SSL TEST ===")
    try:
        host = URL.split("/")[2]
        ctx = ssl.create_default_context()
        with socket.create_connection((host, 443), timeout=10) as sock:
            with ctx.wrap_socket(sock, server_hostname=host) as ssock:
                print("SSL handshake OK")
                print("Cipher:", ssock.cipher())
    except Exception as e:
        print("SSL Error:", e)


def test_google():
    print("\n=== GENERAL HTTPS CONNECTIVITY TEST (Google) ===")
    try:
        r = requests.get("https://www.google.com", timeout=10)
        print("Google Status:", r.status_code)
    except Exception as e:
        print("Error:", e)


if __name__ == "__main__":
    print("Testing Cloudflare Tunnel Connectivity...\n")
    comfyui_alive()
    # test_dns()
    # test_ssl()
    # test_basic_request()
    # test_browser_headers()
    # test_google()
