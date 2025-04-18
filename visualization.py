import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from matplotlib.colors import LinearSegmentedColormap
from datetime import datetime


def generate_plots(results):
    """
    Generate visualizations of domain health check results.

    Args:
        results (list): List of domain check results

    Returns:
        dict: Statistics about the results for reporting
    """
    # Prepare data
    total_domains = len(results)
    http_ok = sum(1 for r in results if r["http_status"] == "OK")
    https_ok = sum(1 for r in results if r["https_status"] == "OK")
    ssl_ok = sum(1 for r in results if r["ssl_valid"] == "OK")

    http_fail = total_domains - http_ok
    https_fail = total_domains - https_ok
    ssl_fail = total_domains - ssl_ok

    # Create a figure with subplots
    fig = plt.figure(figsize=(15, 12))
    fig.suptitle(
        f"Domain Health Check Results (Total: {total_domains} domains)", fontsize=16
    )

    # 1. Summary bar chart
    ax1 = plt.subplot(3, 2, 1)
    categories = ["HTTP", "HTTPS", "SSL"]
    ok_values = [http_ok, https_ok, ssl_ok]
    fail_values = [http_fail, https_fail, ssl_fail]

    x = np.arange(len(categories))
    width = 0.35

    ax1.bar(x - width / 2, ok_values, width, label="OK", color="#4CAF50")
    ax1.bar(x + width / 2, fail_values, width, label="FAIL", color="#F44336")

    for i, v in enumerate(ok_values):
        ax1.text(i - width / 2, v + 0.5, str(v), ha="center")

    for i, v in enumerate(fail_values):
        ax1.text(i + width / 2, v + 0.5, str(v), ha="center")

    ax1.set_xticks(x)
    ax1.set_xticklabels(categories)
    ax1.set_title("Status Summary")
    ax1.legend()

    # 2. Pie chart for overall health
    ax2 = plt.subplot(3, 2, 2)
    fully_healthy = sum(
        1
        for r in results
        if r["http_status"] == "OK"
        and r["https_status"] == "OK"
        and r["ssl_valid"] == "OK"
    )
    partially_healthy = (
        sum(
            1
            for r in results
            if (
                r["http_status"] == "OK"
                or r["https_status"] == "OK"
                or r["ssl_valid"] == "OK"
            )
        )
        - fully_healthy
    )
    unhealthy = total_domains - fully_healthy - partially_healthy

    labels = ["All OK", "Partially OK", "All Failed"]
    sizes = [fully_healthy, partially_healthy, unhealthy]
    colors = ["#4CAF50", "#FFC107", "#F44336"]
    explode = (0.1, 0, 0)

    ax2.pie(
        sizes,
        explode=explode,
        labels=labels,
        colors=colors,
        autopct="%1.1f%%",
        shadow=True,
        startangle=90,
    )
    ax2.axis("equal")
    ax2.set_title("Overall Health Status")

    # 3. Success rates horizontal bar chart
    ax3 = plt.subplot(3, 2, 3)

    # Extract domain names and success rates
    domains = [r["domain"] for r in results]
    http_rates = [r["http_success_rate"] for r in results]
    https_rates = [r["https_success_rate"] for r in results]
    ssl_rates = [r["ssl_success_rate"] for r in results]

    # Sort by average success rate
    avg_success_rates = [
        (d, (h + s + l) / 3)
        for d, h, s, l in zip(domains, http_rates, https_rates, ssl_rates)
    ]
    avg_success_rates.sort(key=lambda x: x[1], reverse=True)

    sorted_domains = [item[0] for item in avg_success_rates]
    sorted_http_rates = [
        next(r["http_success_rate"] for r in results if r["domain"] == d)
        for d in sorted_domains
    ]
    sorted_https_rates = [
        next(r["https_success_rate"] for r in results if r["domain"] == d)
        for d in sorted_domains
    ]
    sorted_ssl_rates = [
        next(r["ssl_success_rate"] for r in results if r["domain"] == d)
        for d in sorted_domains
    ]

    # Create horizontal bars
    y_pos = np.arange(len(sorted_domains))
    bar_height = 0.25

    ax3.barh(
        y_pos - bar_height, sorted_http_rates, bar_height, label="HTTP", color="#2196F3"
    )
    ax3.barh(y_pos, sorted_https_rates, bar_height, label="HTTPS", color="#673AB7")
    ax3.barh(
        y_pos + bar_height, sorted_ssl_rates, bar_height, label="SSL", color="#009688"
    )

    # Removed percentage text labels as requested

    ax3.set_yticks(y_pos)
    ax3.set_yticklabels(sorted_domains)
    ax3.set_xlim(0, 105)

    # Add a vertical grid to help estimate percentages
    ax3.grid(axis="x", linestyle="--", alpha=0.7)
    ax3.set_xticks([0, 20, 40, 60, 80, 100])

    ax3.set_title("Success Rate by Domain")
    ax3.set_xlabel("Success Rate (%)")
    ax3.legend(loc="lower right")

    # 4. SSL expiry heat map (for domains with valid SSL)
    ax4 = plt.subplot(3, 2, 4)

    # Filter domains with valid SSL and sort by expiry
    ssl_valid_domains = [r for r in results if r["ssl_valid"] == "OK"]
    if ssl_valid_domains:
        ssl_valid_domains.sort(key=lambda x: x.get("days_until_expiry", 0))

        # Prepare data for heatmap
        ssl_domains = [r["domain"] for r in ssl_valid_domains]
        days_left = [r.get("days_until_expiry", 0) for r in ssl_valid_domains]

        # Create custom colormap - green for long time, yellow for medium, red for expiring soon
        cmap = LinearSegmentedColormap.from_list(
            "ssl_expiry",
            [
                (0, "#F44336"),  # Red for soon expiring
                (0.2, "#FFC107"),  # Yellow for medium
                (1, "#4CAF50"),
            ],
        )  # Green for long time

        # Create a DataFrame for easier plotting
        df = pd.DataFrame({"Domain": ssl_domains, "Days Until Expiry": days_left})

        # Plot horizontal bar chart
        bars = ax4.barh(
            df["Domain"],
            df["Days Until Expiry"],
            color=cmap(np.array(days_left) / max(max(days_left), 365)),
        )

        # Improved display of days until expiry
        for i, (days, domain) in enumerate(zip(days_left, ssl_domains)):
            # Determine text color based on urgency
            if days <= 30:  # For soon expiring
                text_color = "#F44336"  # Red
                days_text = f"⚠️ {days} DAYS"
                fontweight = "bold"

                # Add extra warning for critical certs (≤ 7 days)
                if days <= 7:
                    days_text = f"⚠️ CRITICAL: {days} DAYS ⚠️"
            elif days <= 90:  # Medium term
                text_color = "#FFC107"  # Yellow/Amber
                days_text = f"{days} days"
                fontweight = "normal"
            else:  # Long term
                text_color = "#4CAF50"  # Green
                days_text = f"{days} days"
                fontweight = "normal"

            # Position the text to the right of the bar
            # Get the current axes width in data units
            x_lim = ax4.get_xlim()[1]
            bar_end = days

            # Calculate text position - to the right of the bar with padding
            text_x = bar_end + (x_lim * 0.01)  # Add a small padding

            # Add text with background for better visibility
            ax4.text(
                text_x,
                i,
                days_text,
                va="center",
                ha="left",
                color=text_color,
                fontweight=fontweight,
                fontsize=10,
                bbox=dict(
                    facecolor="white",
                    alpha=0.8,
                    edgecolor="gray",
                    boxstyle="round,pad=0.3",
                ),
            )

        ax4.set_title("Days Until SSL Certificate Expiry")
        ax4.set_xlabel("Days")

        # Ensure x-axis is wide enough to show labels
        current_xlim = ax4.get_xlim()
        ax4.set_xlim(0, current_xlim[1] * 1.3)  # Extend x-axis by 30%

        # Add a colorbar as a legend
        sm = plt.cm.ScalarMappable(cmap=cmap)
        sm.set_array([])
        cbar = plt.colorbar(sm, ax=ax4)
        cbar.set_label("Expiry Urgency")

        # Add vertical guidelines for critical/warning thresholds
        ax4.axvline(x=30, color="#FFC107", linestyle="--", alpha=0.7)
        ax4.axvline(x=7, color="#F44336", linestyle="--", alpha=0.7)

        # Add annotations for thresholds
        ax4.text(
            30,
            -0.8,
            "30 days",
            va="center",
            ha="center",
            color="#FFC107",
            fontweight="bold",
            bbox=dict(facecolor="white", alpha=0.8, edgecolor="#FFC107"),
        )
        ax4.text(
            7,
            -0.8,
            "7 days",
            va="center",
            ha="center",
            color="#F44336",
            fontweight="bold",
            bbox=dict(facecolor="white", alpha=0.8, edgecolor="#F44336"),
        )
    else:
        ax4.text(
            0.5,
            0.5,
            "No valid SSL certificates found",
            ha="center",
            va="center",
            fontsize=14,
        )
        ax4.set_title("Days Until SSL Certificate Expiry")

    # 5. Response time comparison chart
    ax5 = plt.subplot(3, 1, 3)

    # Get domains with response time data
    response_time_domains = [
        r
        for r in results
        if "avg_http_response_time" in r or "avg_https_response_time" in r
    ]

    if response_time_domains:
        # Sort by HTTP response time (if available)
        response_time_domains.sort(
            key=lambda x: x.get("avg_http_response_time", float("inf"))
        )

        domains_rt = [r["domain"] for r in response_time_domains]
        http_times = [r.get("avg_http_response_time", 0) for r in response_time_domains]
        https_times = [
            r.get("avg_https_response_time", 0) for r in response_time_domains
        ]

        # Create positions
        y_pos = np.arange(len(domains_rt))
        bar_height = 0.35

        # Create bars
        ax5.barh(
            y_pos - bar_height / 2,
            http_times,
            bar_height,
            label="HTTP",
            color="#2196F3",
        )
        ax5.barh(
            y_pos + bar_height / 2,
            https_times,
            bar_height,
            label="HTTPS",
            color="#673AB7",
        )

        # Add time text
        for i, (h, s) in enumerate(zip(http_times, https_times)):
            if h > 0:
                ax5.text(h + 0.05, i - bar_height / 2, f"{h:.2f}s", va="center")
            if s > 0:
                ax5.text(s + 0.05, i + bar_height / 2, f"{s:.2f}s", va="center")

        ax5.set_yticks(y_pos)
        ax5.set_yticklabels(domains_rt)
        ax5.set_title("Average Response Time (seconds)")
        ax5.set_xlabel("Time (seconds)")
        ax5.legend()
    else:
        ax5.text(
            0.5,
            0.5,
            "No response time data available",
            ha="center",
            va="center",
            fontsize=14,
        )
        ax5.set_title("Average Response Time")

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])

    # Save the plot with a generic filename
    filename = "domain_health_check_results.png"
    plt.savefig(filename, dpi=300, bbox_inches="tight")

    print(f"Results image saved as '{filename}'")

    # Return data for the text report
    return {
        "total": total_domains,
        "http_ok": http_ok,
        "https_ok": https_ok,
        "ssl_ok": ssl_ok,
        "fully_healthy": fully_healthy,
        "partially_healthy": partially_healthy,
        "unhealthy": unhealthy,
    }


def generate_text_report(results, stats):
    """
    Generate a text report of the domain health check.

    Args:
        results (list): List of domain check results
        stats (dict): Statistics about the results

    Returns:
        str: Path to the generated report file
    """
    report_file = "domain_health_report.txt"

    # Get current time and user information from environment (if available)
    current_time = "2025-04-18 06:04:27"  # Default time
    current_user = "gunh0"  # Default user

    with open(report_file, "w", encoding="utf-8") as f:
        f.write("Domain Health Check Report\n")
        f.write("=" * 80 + "\n")
        f.write(f"Date and Time: {current_time}\n")
        f.write(f"User: {current_user}\n")
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
