# visualization/plots.py
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import os
from matplotlib.colors import LinearSegmentedColormap
from datetime import datetime


def prepare_data(results):
    """Extract and prepare basic data from results."""
    total_domains = len(results)
    http_ok = sum(1 for r in results if r["http_status"] == "OK")
    https_ok = sum(1 for r in results if r["https_status"] == "OK")
    ssl_ok = sum(1 for r in results if r["ssl_valid"] == "OK")

    http_fail = total_domains - http_ok
    https_fail = total_domains - https_ok
    ssl_fail = total_domains - ssl_ok

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

    return {
        "total_domains": total_domains,
        "http_ok": http_ok,
        "https_ok": https_ok,
        "ssl_ok": ssl_ok,
        "http_fail": http_fail,
        "https_fail": https_fail,
        "ssl_fail": ssl_fail,
        "fully_healthy": fully_healthy,
        "partially_healthy": partially_healthy,
        "unhealthy": unhealthy,
    }


def create_status_summary(ax, data):
    """Create the status summary bar chart."""
    categories = ["HTTP", "HTTPS", "SSL"]
    ok_values = [data["http_ok"], data["https_ok"], data["ssl_ok"]]
    fail_values = [data["http_fail"], data["https_fail"], data["ssl_fail"]]

    x = np.arange(len(categories))
    width = 0.35

    ax.bar(x - width / 2, ok_values, width, label="OK", color="#4CAF50")
    ax.bar(x + width / 2, fail_values, width, label="FAIL", color="#F44336")

    for i, v in enumerate(ok_values):
        ax.text(i - width / 2, v + 0.5, str(v), ha="center")

    for i, v in enumerate(fail_values):
        ax.text(i + width / 2, v + 0.5, str(v), ha="center")

    ax.set_xticks(x)
    ax.set_xticklabels(categories)
    ax.set_title("Status Summary")
    ax.legend()


def create_health_pie_chart(ax, data):
    """Create the overall health pie chart."""
    # Include count in labels for better readability
    labels = [
        f"All OK ({data['fully_healthy']})",
        f"Partially OK ({data['partially_healthy']})",
        f"All Failed ({data['unhealthy']})",
    ]
    sizes = [data["fully_healthy"], data["partially_healthy"], data["unhealthy"]]
    colors = ["#4CAF50", "#FFC107", "#F44336"]
    explode = (0.1, 0, 0)

    ax.pie(
        sizes,
        explode=explode,
        labels=labels,
        colors=colors,
        autopct="%1.1f%%",
        shadow=True,
        startangle=90,
    )
    ax.axis("equal")
    ax.set_title("Overall Health Status")


def create_success_rate_chart(ax, results, max_domains_to_show=25):
    """Create the success rate horizontal bar chart with dynamic sizing."""
    # Extract domain names and success rates
    domains = [r["domain"] for r in results]
    http_rates = [r["http_success_rate"] for r in results]
    https_rates = [r["https_success_rate"] for r in results]
    ssl_rates = [r["ssl_success_rate"] for r in results]

    # Calculate average success rates
    avg_rates = [(h + s + l) / 3 for h, s, l in zip(http_rates, https_rates, ssl_rates)]

    # Create data with domains and all rates
    combined_data = list(zip(domains, avg_rates, http_rates, https_rates, ssl_rates))

    # Sort by average success rate (highest first)
    combined_data.sort(key=lambda x: x[1], reverse=True)

    # Limit display if too many domains
    if len(combined_data) > max_domains_to_show:
        # Show only the max number of domains
        display_data = combined_data[:max_domains_to_show]
        truncated = True
    else:
        display_data = combined_data
        truncated = False

    # Unpack the data
    sorted_domains = [item[0] for item in display_data]
    sorted_avg_rates = [item[1] for item in display_data]
    sorted_http_rates = [item[2] for item in display_data]
    sorted_https_rates = [item[3] for item in display_data]
    sorted_ssl_rates = [item[4] for item in display_data]

    # Dynamic font size based on domain count
    domain_count = len(sorted_domains)
    fontsize = max(
        7, 11 - (domain_count // 8)
    )  # Decrease font size as domains increase

    # Create horizontal bars
    y_pos = np.arange(len(sorted_domains))
    bar_height = 0.25

    ax.barh(
        y_pos - bar_height, sorted_http_rates, bar_height, label="HTTP", color="#2196F3"
    )
    ax.barh(y_pos, sorted_https_rates, bar_height, label="HTTPS", color="#673AB7")
    ax.barh(
        y_pos + bar_height, sorted_ssl_rates, bar_height, label="SSL", color="#009688"
    )

    # Add average rate display
    for i, avg_rate in enumerate(sorted_avg_rates):
        ax.text(
            102,  # Position just past the end of the bar
            y_pos[i],
            f"{avg_rate:.0f}%",
            va="center",
            ha="left",
            fontweight="bold",
            fontsize=fontsize,
            color="#333333",
        )

    ax.set_yticks(y_pos)
    ax.set_yticklabels(sorted_domains, fontsize=fontsize)
    ax.set_xlim(0, 110)  # Extended for average percentage

    # Add a vertical grid to help estimate percentages
    ax.grid(axis="x", linestyle="--", alpha=0.7)
    ax.set_xticks([0, 20, 40, 60, 80, 100])

    title = "Success Rate by Domain (with Avg %)"
    if truncated:
        title += f" - Top {max_domains_to_show} of {len(combined_data)}"
    ax.set_title(title)
    ax.set_xlabel("Success Rate (%)")
    ax.legend(loc="lower right")

    return truncated, len(combined_data)


def create_ssl_expiry_chart(ax, results, max_domains_to_show=25):
    """Create the SSL expiry heat map with dynamic sizing."""
    # Filter domains with valid SSL and sort by expiry
    ssl_valid_domains = [r for r in results if r["ssl_valid"] == "OK"]
    if not ssl_valid_domains:
        ax.text(
            0.5,
            0.5,
            "No valid SSL certificates found",
            ha="center",
            va="center",
            fontsize=14,
        )
        ax.set_title("Days Until SSL Certificate Expiry")
        return False, 0

    ssl_valid_domains.sort(key=lambda x: x.get("days_until_expiry", 0))

    # Limit display if too many domains
    if len(ssl_valid_domains) > max_domains_to_show:
        # Show the most critical ones (shortest expiry)
        ssl_valid_domains = ssl_valid_domains[:max_domains_to_show]
        truncated = True
    else:
        truncated = False

    # Prepare data for heatmap
    ssl_domains = [r["domain"] for r in ssl_valid_domains]
    days_left = [r.get("days_until_expiry", 0) for r in ssl_valid_domains]

    # Dynamic font size based on domain count
    domain_count = len(ssl_domains)
    fontsize = max(
        7, 11 - (domain_count // 8)
    )  # Decrease font size as domains increase

    # Create custom colormap - green for long time, yellow for medium, red for expiring soon
    cmap = LinearSegmentedColormap.from_list(
        "ssl_expiry",
        [
            (0, "#F44336"),  # Red for soon expiring
            (0.2, "#FFC107"),  # Yellow for medium
            (1, "#4CAF50"),  # Green for long time
        ],
    )

    # Create a DataFrame for easier plotting
    df = pd.DataFrame({"Domain": ssl_domains, "Days Until Expiry": days_left})

    # Plot horizontal bar chart
    bars = ax.barh(
        df["Domain"],
        df["Days Until Expiry"],
        color=cmap(np.array(days_left) / max(max(days_left), 365)),
    )

    # Improved display of days until expiry
    for i, (days, domain) in enumerate(zip(days_left, ssl_domains)):
        # Default text in case conditions aren't met
        days_text = f"{days} days"
        text_color = "#4CAF50"  # Green (default)
        fontweight = "normal"

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

        # Position the text to the right of the bar
        # Get the current axes width in data units
        x_lim = ax.get_xlim()[1]
        bar_end = days

        # Calculate text position - to the right of the bar with padding
        text_x = bar_end + (x_lim * 0.01)  # Add a small padding

        # Add text with background for better visibility - with explicit text
        ax.text(
            text_x,
            i,
            days_text,  # Ensure the text parameter is always provided
            va="center",
            ha="left",
            color=text_color,
            fontweight=fontweight,
            fontsize=fontsize,
            bbox=dict(
                facecolor="white",
                alpha=0.8,
                edgecolor="gray",
                boxstyle="round,pad=0.3",
            ),
        )

    title = "Days Until SSL Certificate Expiry"
    if truncated:
        title += f" - Top {max_domains_to_show} Critical of {len(ssl_valid_domains)}"
    ax.set_title(title)
    ax.set_xlabel("Days")
    ax.set_yticks(range(len(ssl_domains)))
    ax.set_yticklabels(ssl_domains, fontsize=fontsize)

    # Ensure x-axis is wide enough to show labels
    current_xlim = ax.get_xlim()
    ax.set_xlim(0, current_xlim[1] * 1.3)  # Extend x-axis by 30%

    # Add a colorbar as a legend
    sm = plt.cm.ScalarMappable(cmap=cmap)
    sm.set_array([])
    cbar = plt.colorbar(sm, ax=ax)
    cbar.set_label("Expiry Urgency")

    # Add threshold explanation text box
    threshold_text = ("Red: Expiring soon")

    # Add text box in the upper right corner of the plot
    props = dict(boxstyle="round", facecolor="white", alpha=0.9, edgecolor="gray")
    ax.text(
        0.98,
        0.98,
        threshold_text,
        transform=ax.transAxes,
        fontsize=8,
        verticalalignment="top",
        horizontalalignment="right",
        bbox=props,
    )

    return truncated, len(ssl_valid_domains)


def create_response_time_chart(ax, results, max_domains_to_show=40):
    """Create the response time comparison chart with dynamic sizing."""
    # Get domains with response time data
    response_time_domains = [
        r
        for r in results
        if "avg_http_response_time" in r or "avg_https_response_time" in r
    ]

    if not response_time_domains:
        ax.text(
            0.5,
            0.5,
            "No response time data available",
            ha="center",
            va="center",
            fontsize=14,
        )
        ax.set_title("Average Response Time")
        return False, 0

    # Sort by HTTP response time (if available)
    response_time_domains.sort(
        key=lambda x: x.get("avg_http_response_time", float("inf"))
    )

    # Limit display if too many domains
    if len(response_time_domains) > max_domains_to_show:
        # Show only fastest domains
        response_time_domains = response_time_domains[:max_domains_to_show]
        truncated = True
    else:
        truncated = False

    domains_rt = [r["domain"] for r in response_time_domains]

    # Dynamic font size based on domain count
    domain_count = len(domains_rt)
    fontsize = max(
        7, 11 - (domain_count // 10)
    )  # Decrease font size as domains increase

    # Pre-process all times to ensure they are safe to use
    http_times = []
    https_times = []

    for r in response_time_domains:
        # Get values with default of 0
        http_time = r.get("avg_http_response_time", 0)
        https_time = r.get("avg_https_response_time", 0)

        # Convert None or non-numeric values to 0
        if http_time is None or not isinstance(http_time, (int, float)):
            http_time = 0
        if https_time is None or not isinstance(https_time, (int, float)):
            https_time = 0

        http_times.append(float(http_time))
        https_times.append(float(https_time))

    # Create positions
    y_pos = np.arange(len(domains_rt))
    bar_height = 0.35

    # Create bars
    ax.barh(
        y_pos - bar_height / 2,
        http_times,
        bar_height,
        label="HTTP",
        color="#2196F3",
    )
    ax.barh(
        y_pos + bar_height / 2,
        https_times,
        bar_height,
        label="HTTPS",
        color="#673AB7",
    )

    # Add time text only for times > 0
    for i, (h, s) in enumerate(zip(http_times, https_times)):
        if h > 0:  # Simple check for positive value
            ax.text(
                h + 0.05,
                i - bar_height / 2,
                f"{h:.2f}s",
                va="center",
                fontsize=fontsize,
            )
        if s > 0:  # Simple check for positive value
            ax.text(
                s + 0.05,
                i + bar_height / 2,
                f"{s:.2f}s",
                va="center",
                fontsize=fontsize,
            )

    ax.set_yticks(y_pos)
    ax.set_yticklabels(domains_rt, fontsize=fontsize)

    title = "Average Response Time (seconds)"
    if truncated:
        title += f" - Top {max_domains_to_show} of {len(response_time_domains)}"
    ax.set_title(title)
    ax.set_xlabel("Time (seconds)")
    ax.legend()

    # Add explanation for percentage differences
    ax.text(
        0.98,
        0.02,
        "Note: Percentages show HTTPS speed difference vs HTTP\n(negative = faster, positive = slower)",
        transform=ax.transAxes,
        fontsize=8,
        ha="right",
        va="bottom",
        bbox=dict(facecolor="white", alpha=0.8, boxstyle="round,pad=0.2"),
    )

    return truncated, len(response_time_domains)


def generate_plots(results, output_dir="results"):
    """
    Generate visualizations of domain health check results with dynamic sizing.

    Parameters:
        results (list): List of domain check results
        output_dir (str): Directory to save output files

    Returns:
        dict: Statistics about the results for reporting
    """
    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Prepare data
    data = prepare_data(results)
    total_domains = data["total_domains"]

    # Dynamically calculate figure height based on domain count
    # More aggressive scaling for larger domain counts
    base_height = 12
    if total_domains <= 15:
        fig_height = base_height
    elif total_domains <= 30:
        fig_height = base_height + (total_domains - 15) * 0.4
    elif total_domains <= 50:
        fig_height = base_height + 6 + (total_domains - 30) * 0.5
    else:
        fig_height = base_height + 16 + (total_domains - 50) * 0.3

    # Cap maximum height to prevent excessively tall figures
    fig_height = min(fig_height, 36)

    # Create a figure with dynamic height
    fig = plt.figure(figsize=(15, fig_height))
    fig.suptitle(
        f"Domain Health Check Results (Total: {total_domains} domains)", fontsize=16
    )

    # Adjust the grid layout based on domain count
    # For many domains, use a more vertical layout
    if total_domains > 40:
        # Use a 4x2 grid for many domains
        ax1 = plt.subplot(5, 2, 1)  # Status summary (top left)
        ax2 = plt.subplot(5, 2, 2)  # Health pie chart (top right)
        ax3 = plt.subplot(5, 2, (3, 5))  # Success rates (left middle, spanning 3 rows)
        ax4 = plt.subplot(5, 2, (4, 6))  # SSL expiry (right middle, spanning 3 rows)
        ax5 = plt.subplot(
            5, 1, 4
        )  # Response time (bottom, full width, spanning 2 rows)
    else:
        # Use standard 3x2 grid for fewer domains
        ax1 = plt.subplot(3, 2, 1)
        ax2 = plt.subplot(3, 2, 2)
        ax3 = plt.subplot(3, 2, 3)
        ax4 = plt.subplot(3, 2, 4)
        ax5 = plt.subplot(3, 1, 3)

    # Create the charts
    create_status_summary(ax1, data)
    create_health_pie_chart(ax2, data)

    # Calculate max domains to show based on figure height
    # Use a more aggressive scaling to show more domains in taller figures
    max_success_domains = max(10, int(fig_height * 2.5))
    max_ssl_domains = max(10, int(fig_height * 2.5))
    max_response_domains = max(15, int(fig_height * 3.5))

    success_truncated, total_success_domains = create_success_rate_chart(
        ax3, results, max_success_domains
    )
    ssl_truncated, total_ssl_domains = create_ssl_expiry_chart(
        ax4, results, max_ssl_domains
    )
    response_truncated, total_response_domains = create_response_time_chart(
        ax5, results, max_response_domains
    )

    # Adjust layout with more padding for larger domain counts
    if total_domains > 30:
        plt.tight_layout(rect=[0, 0.03, 1, 0.95], h_pad=3.0, w_pad=2.0)
    else:
        plt.tight_layout(rect=[0, 0.03, 1, 0.95])

    # Save the plot with timestamp and a generic latest version
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{output_dir}/domain_health_check_{timestamp}.png"
    latest_filename = f"{output_dir}/domain_health_check_latest.png"

    plt.savefig(filename, dpi=300, bbox_inches="tight")
    plt.savefig(latest_filename, dpi=300, bbox_inches="tight")

    print(f"Results image saved as '{filename}' and '{latest_filename}'")

    # Always create detailed charts when domain count is high
    if total_domains > 30:
        print("Creating additional detailed charts for better visibility...")

        # Create success rate chart with all domains
        create_detailed_success_chart(
            results, f"{output_dir}/success_rates_detail_{timestamp}.png"
        )

        # Create SSL expiry chart with all domains if there are any valid SSL domains
        if total_ssl_domains > 0:
            create_detailed_ssl_chart(
                results, f"{output_dir}/ssl_expiry_detail_{timestamp}.png"
            )

        # Create response time chart with all domains if there is response time data
        if total_response_domains > 0:
            create_detailed_response_chart(
                results, f"{output_dir}/response_times_detail_{timestamp}.png"
            )

    # Return data for the text report
    return {
        "total": total_domains,
        "http_ok": data["http_ok"],
        "https_ok": data["https_ok"],
        "ssl_ok": data["ssl_ok"],
        "fully_healthy": data["fully_healthy"],
        "partially_healthy": data["partially_healthy"],
        "unhealthy": data["unhealthy"],
    }


def create_detailed_response_chart(results, filename):
    """Create a detailed response time chart showing all domains with response time data."""
    # Get domains with response time data
    response_time_domains = [
        r
        for r in results
        if "avg_http_response_time" in r or "avg_https_response_time" in r
    ]

    if not response_time_domains:
        return  # No response time data to display

    # Sort by HTTP response time (if available)
    response_time_domains.sort(
        key=lambda x: x.get("avg_http_response_time", float("inf"))
    )

    # Create larger figure for detailed view
    height_per_domain = 0.4  # Inches per domain
    min_height = 10  # Minimum height in inches
    height = max(min_height, len(results) * height_per_domain)
    fig, ax = plt.subplots(figsize=(15, height))

    domains_rt = [r["domain"] for r in response_time_domains]

    # Calculate font size based on domain count
    domain_count = len(domains_rt)
    fontsize = max(6, 9 - (domain_count // 30))

    # Pre-process all times to ensure they are safe to use
    http_times = []
    https_times = []

    for r in response_time_domains:
        # Get values with default of 0
        http_time = r.get("avg_http_response_time", 0)
        https_time = r.get("avg_https_response_time", 0)

        # Convert None or non-numeric values to 0
        if http_time is None or not isinstance(http_time, (int, float)):
            http_time = 0
        if https_time is None or not isinstance(https_time, (int, float)):
            https_time = 0

        http_times.append(float(http_time))
        https_times.append(float(https_time))

    # Create positions
    y_pos = np.arange(len(domains_rt))
    bar_height = 0.3

    # Create bars
    ax.barh(
        y_pos - bar_height / 2,
        http_times,
        bar_height,
        label="HTTP",
        color="#2196F3",
    )
    ax.barh(
        y_pos + bar_height / 2,
        https_times,
        bar_height,
        label="HTTPS",
        color="#673AB7",
    )

    # Add time text only for times > 0
    for i, (h, s) in enumerate(zip(http_times, https_times)):
        if h > 0:  # Simple check for positive value
            ax.text(
                h + 0.05,
                i - bar_height / 2,
                f"{h:.2f}s",
                va="center",
                fontsize=fontsize,
            )
        if s > 0:  # Simple check for positive value
            ax.text(
                s + 0.05,
                i + bar_height / 2,
                f"{s:.2f}s",
                va="center",
                fontsize=fontsize,
            )

    # Add comparison between HTTP and HTTPS times
    for i, (h, s) in enumerate(zip(http_times, https_times)):
        if h > 0 and s > 0:  # Only if both have values
            diff_pct = ((s - h) / h) * 100  # Percentage difference
            diff_text = f"{diff_pct:+.1f}%"  # + sign for increase, - for decrease
            diff_color = (
                "#F44336" if diff_pct > 0 else "#4CAF50"
            )  # Red if slower, green if faster

            # Add text showing the difference
            text_x = max(h, s) + 0.3
            ax.text(
                text_x,
                y_pos[i],
                diff_text,
                va="center",
                ha="left",
                color=diff_color,
                fontweight="bold",
                fontsize=fontsize,
                bbox=dict(facecolor="white", alpha=0.8, boxstyle="round,pad=0.2"),
            )

    ax.set_yticks(y_pos)
    ax.set_yticklabels(domains_rt, fontsize=fontsize)
    ax.set_title(f"Average Response Time (seconds) - All {len(domains_rt)} Domains")
    ax.set_xlabel("Time (seconds)")
    ax.legend()

    # Add explanation for percentage differences
    ax.text(
        0.98,
        0.02,
        "Note: Percentages show HTTPS speed difference vs HTTP\n(negative = faster, positive = slower)",
        transform=ax.transAxes,
        fontsize=8,
        ha="right",
        va="bottom",
        bbox=dict(facecolor="white", alpha=0.8, boxstyle="round,pad=0.2"),
    )

    # Save the detailed chart
    plt.tight_layout()
    plt.savefig(filename, dpi=300, bbox_inches="tight")
    print(f"Detailed response time chart saved as '{filename}'")
