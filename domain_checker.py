import requests
import ssl
import socket
from urllib.parse import urlparse
from datetime import datetime
import time
import statistics


def check_domain_health(domain, test_count=5):
    """
    Check HTTP/HTTPS status and SSL certificate for a domain with multiple tests.

    Args:
        domain (str): Domain to check
        test_count (int): Number of tests to run

    Returns:
        dict: Aggregated results of all tests
    """
    single_results = []

    for test_num in range(test_count):
        print(f"    Running test {test_num+1}/{test_count}...")

        result = {
            "domain": domain,
            "http_status": "FAIL",
            "https_status": "FAIL",
            "ssl_valid": "FAIL",
            "ssl_expiry": None,
            "http_response_time": None,
            "https_response_time": None,
            "error": None,
        }

        # Add http:// prefix if not present
        if not domain.startswith("http"):
            domain_with_http = f"http://{domain}"
            domain_with_https = f"https://{domain}"
        else:
            parsed = urlparse(domain)
            domain_name = parsed.netloc or parsed.path
            domain_with_http = f"http://{domain_name}"
            domain_with_https = f"https://{domain_name}"

        # Check HTTP
        try:
            start_time = time.time()
            http_response = requests.get(domain_with_http, timeout=10)
            http_time = time.time() - start_time
            result["http_response_time"] = http_time
            result["http_status"] = (
                "OK"
                if http_response.status_code == 200
                else f"FAIL ({http_response.status_code})"
            )
        except Exception as e:
            result["http_status"] = f"FAIL (Error)"
            result["error"] = str(e)

        # Check HTTPS and SSL
        try:
            start_time = time.time()
            https_response = requests.get(domain_with_https, timeout=10)
            https_time = time.time() - start_time
            result["https_response_time"] = https_time
            result["https_status"] = (
                "OK"
                if https_response.status_code == 200
                else f"FAIL ({https_response.status_code})"
            )

            # Extract domain name without protocol
            hostname = urlparse(domain_with_https).netloc

            # Check SSL certificate
            context = ssl.create_default_context()
            with socket.create_connection((hostname, 443), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                    cert = ssock.getpeercert()

                    # Get expiry date
                    expire_date_str = cert["notAfter"]
                    expire_date = datetime.strptime(
                        expire_date_str, "%b %d %H:%M:%S %Y %Z"
                    )

                    # Calculate days until expiry
                    days_left = (expire_date - datetime.now()).days

                    result["ssl_valid"] = "OK"
                    result["ssl_expiry"] = expire_date
                    result["days_until_expiry"] = days_left

        except Exception as e:
            result["https_status"] = "FAIL (Error)"
            result["ssl_valid"] = "FAIL"
            result["error"] = str(e)

        single_results.append(result)

        # Small delay between tests to avoid rate limiting
        if test_num < test_count - 1:
            time.sleep(1)

    # Aggregate results
    aggregated_result = {
        "domain": domain,
        "http_status": (
            "OK"
            if sum(1 for r in single_results if r["http_status"].startswith("OK"))
            >= (test_count / 2)
            else "FAIL"
        ),
        "https_status": (
            "OK"
            if sum(1 for r in single_results if r["https_status"].startswith("OK"))
            >= (test_count / 2)
            else "FAIL"
        ),
        "ssl_valid": (
            "OK"
            if sum(1 for r in single_results if r["ssl_valid"] == "OK")
            >= (test_count / 2)
            else "FAIL"
        ),
        "ssl_expiry": next(
            (r["ssl_expiry"] for r in single_results if r["ssl_expiry"]), None
        ),
        "http_success_rate": sum(
            1 for r in single_results if r["http_status"].startswith("OK")
        )
        / test_count
        * 100,
        "https_success_rate": sum(
            1 for r in single_results if r["https_status"].startswith("OK")
        )
        / test_count
        * 100,
        "ssl_success_rate": sum(1 for r in single_results if r["ssl_valid"] == "OK")
        / test_count
        * 100,
        "test_results": single_results,
    }

    # Calculate average response times (only for successful requests)
    http_times = [
        r["http_response_time"] for r in single_results if r["http_response_time"]
    ]
    https_times = [
        r["https_response_time"] for r in single_results if r["https_response_time"]
    ]

    if http_times:
        aggregated_result["avg_http_response_time"] = statistics.mean(http_times)

    if https_times:
        aggregated_result["avg_https_response_time"] = statistics.mean(https_times)

    # Get days until expiry if SSL is valid
    if aggregated_result["ssl_valid"] == "OK" and aggregated_result["ssl_expiry"]:
        aggregated_result["days_until_expiry"] = (
            aggregated_result["ssl_expiry"] - datetime.now()
        ).days

    return aggregated_result


def read_domains_from_file(file_path):
    """
    Read domain list from a text file.

    Args:
        file_path (str): Path to the text file containing one domain per line

    Returns:
        list: List of domain strings
    """
    with open(file_path, "r") as file:
        domains = [line.strip() for line in file if line.strip()]
    return domains
