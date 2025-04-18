#!/usr/bin/env python3
"""
Domain Health Checker
--------------------
This script checks domain health by testing HTTP/HTTPS status and SSL certificate validity.
It performs multiple tests on each domain and generates both visual and text reports.
"""

import sys
import os
from datetime import datetime
import pytz
import dotenv

# Import modules
from domain_checker import check_domain_health, read_domains_from_file
from visualization import generate_plots, generate_text_report
from visualization.utils import get_korean_time


def main():
    """Main function to run the domain health checker."""
    # Load environment variables
    dotenv.load_dotenv()

    # Get test count from environment variable or use default
    test_count = int(os.getenv("TEST_COUNT", 5))

    # Display header
    print("===== Domain Health Checker =====")

    # Get current time in Korean timezone
    current_time = get_korean_time()
    print(f"Current time (KST): {current_time}")

    # Set default values
    file_path = "domains.txt"  # Default file to read domains from

    try:
        # Check if the domains file exists
        if not os.path.exists(file_path):
            print(f"Error: Domain list file '{file_path}' not found.")
            print(
                f"Please create a '{file_path}' file in the current directory with one domain per line."
            )
            return 1

        # Read domains from file
        domains = read_domains_from_file(file_path)
        print(f"Loaded {len(domains)} domains from '{file_path}'.")
        print(f"Test count: {test_count}")

        # Check each domain
        results = []
        domains_with_expiring_certs = []

        for i, domain in enumerate(domains, 1):
            print(f"[{i}/{len(domains)}] Checking {domain}... ({test_count} tests)")
            result = check_domain_health(domain, test_count=test_count)

            # Check for domains with expiring SSL certificates
            if result["ssl_valid"] == "OK" and result.get("days_until_expiry", 0) <= 30:
                days = result.get("days_until_expiry", 0)
                expiry_date = result.get("ssl_expiry", "Unknown")
                expiry_date_str = (
                    expiry_date.strftime("%Y-%m-%d")
                    if isinstance(expiry_date, datetime)
                    else "Unknown"
                )

                domains_with_expiring_certs.append(
                    {
                        "domain": domain,
                        "days_remaining": days,
                        "expiry_date": expiry_date_str,
                    }
                )

            results.append(result)

        # Generate visualizations
        print("\nGenerating visualizations...")
        stats = generate_plots(results)

        # Generate text report
        print("Creating text report...")
        report_file = generate_text_report(results, stats)

        # Print warning about expiring certificates
        if domains_with_expiring_certs:
            print("\n⚠️ WARNING: The following domains have certificates expiring soon:")
            print("-" * 65)
            print(f"{'DOMAIN':<40} {'DAYS REMAINING':<15} {'EXPIRY DATE'}")
            print("-" * 65)

            # Sort by days remaining (ascending)
            domains_with_expiring_certs.sort(key=lambda x: x["days_remaining"])

            for domain_info in domains_with_expiring_certs:
                days = domain_info["days_remaining"]
                domain = domain_info["domain"]
                expiry = domain_info["expiry_date"]

                if days <= 7:
                    print(f"{domain:<40} ⚠️ CRITICAL: {days:<5} {expiry}")
                else:
                    print(f"{domain:<40} {days:<15} {expiry}")
            print("-" * 65)

        print("\nDomain health check completed!")
        print(f"Results saved in the current directory.")
        print("=" * 40)

        return 0  # Success

    except Exception as e:
        print(f"Error occurred: {str(e)}")
        return 1  # Error


if __name__ == "__main__":
    sys.exit(main())
