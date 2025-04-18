# visualization/text_report.py
from datetime import datetime
import pytz


# Generate a text report of the domain health check.
def generate_text_report(results, stats):

    report_file = "domain_health_report.txt"

    # Get current time from environment or use system time
    try:
        from datetime import datetime

        korean_tz = pytz.timezone("Asia/Seoul")
        current_time = datetime.now(korean_tz).strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        # Fallback to simple datetime if pytz is not available
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open(report_file, "w", encoding="utf-8") as f:
        f.write("Domain Health Check Report\n")
        f.write("=" * 80 + "\n")
        f.write(f"Date and Time: {current_time}\n")
        f.write("=" * 80 + "\n\n")

        f.write(f"Total domains: {stats['total']}\n")
        f.write(
            f"HTTP status OK: {stats['http_ok']} ({stats['http_ok']/stats['total']*100:.1f}%)\n"
        )
        f.write(
            f"HTTPS status OK: {stats['https_ok']} ({stats['https_ok']/stats['total']*100:.1f}%)\n"
        )
        f.write(
            f"SSL certificates valid: {stats['ssl_ok']} ({stats['ssl_ok']/stats['total']*100:.1f}%)\n"
        )
        f.write(
            f"Fully healthy domains: {stats['fully_healthy']} ({stats['fully_healthy']/stats['total']*100:.1f}%)\n"
        )
        f.write(
            f"Partially healthy domains: {stats['partially_healthy']} ({stats['partially_healthy']/stats['total']*100:.1f}%)\n"
        )
        f.write(
            f"Completely unhealthy domains: {stats['unhealthy']} ({stats['unhealthy']/stats['total']*100:.1f}%)\n\n"
        )

        # Add section for domains with expiring SSL certificates
        domains_with_expiring_certs = [
            r
            for r in results
            if r["ssl_valid"] == "OK" and r.get("days_until_expiry", 999) <= 30
        ]
        if domains_with_expiring_certs:
            f.write("DOMAINS WITH CERTIFICATES EXPIRING SOON:\n")
            f.write("-" * 80 + "\n")
            for r in sorted(
                domains_with_expiring_certs, key=lambda x: x.get("days_until_expiry", 0)
            ):
                days = r.get("days_until_expiry", 0)
                expiry_date = r.get("ssl_expiry", "Unknown")
                expiry_date_str = (
                    expiry_date.strftime("%Y-%m-%d")
                    if isinstance(expiry_date, datetime)
                    else "Unknown"
                )

                if days <= 7:
                    f.write(
                        f"⚠️ CRITICAL: {r['domain']} - ONLY {days} DAYS REMAINING (expires on {expiry_date_str}) ⚠️\n"
                    )
                else:
                    f.write(
                        f"⚠️ WARNING: {r['domain']} - {days} days remaining (expires on {expiry_date_str})\n"
                    )
            f.write("-" * 80 + "\n\n")

        f.write("Detailed results by domain:\n")
        f.write("=" * 80 + "\n")

        for idx, r in enumerate(results, 1):
            f.write(f"{idx}. {r['domain']}\n")
            f.write(
                f"   HTTP status: {r['http_status']} (Success rate: {r['http_success_rate']:.0f}%)\n"
            )
            f.write(
                f"   HTTPS status: {r['https_status']} (Success rate: {r['https_success_rate']:.0f}%)\n"
            )
            f.write(
                f"   SSL certificate: {r['ssl_valid']} (Success rate: {r['ssl_success_rate']:.0f}%)\n"
            )

            # Add response times if available
            if "avg_http_response_time" in r:
                f.write(
                    f"   Average HTTP response time: {r['avg_http_response_time']:.2f} seconds\n"
                )
            if "avg_https_response_time" in r:
                f.write(
                    f"   Average HTTPS response time: {r['avg_https_response_time']:.2f} seconds\n"
                )

            if r["ssl_valid"] == "OK" and r.get("ssl_expiry"):
                expiry_date = r["ssl_expiry"].strftime("%Y-%m-%d")
                days = r.get("days_until_expiry", "N/A")

                if days != "N/A" and days <= 7:
                    f.write(
                        f"   SSL expiry date: {expiry_date} (⚠️ CRITICAL: ONLY {days} DAYS REMAINING! ⚠️)\n"
                    )
                elif days != "N/A" and days <= 30:
                    f.write(
                        f"   SSL expiry date: {expiry_date} (⚠️ WARNING: ONLY {days} DAYS REMAINING!)\n"
                    )
                else:
                    f.write(f"   SSL expiry date: {expiry_date}\n")
                    f.write(f"   Days remaining: {days} days\n")

            # Add detailed test results
            f.write("\n   Individual test results:\n")
            for test_idx, test in enumerate(r["test_results"], 1):
                f.write(f"   Test {test_idx}: ")
                http_status = "✓" if test["http_status"].startswith("OK") else "✗"
                https_status = "✓" if test["https_status"].startswith("OK") else "✗"
                ssl_status = "✓" if test["ssl_valid"] == "OK" else "✗"
                f.write(
                    f"HTTP: {http_status}, HTTPS: {https_status}, SSL: {ssl_status}\n"
                )

            f.write("-" * 80 + "\n")

    print(f"Text report saved as '{report_file}'")
    return report_file
