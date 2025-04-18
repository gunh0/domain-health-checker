import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
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
    labels = ["All OK", "Partially OK", "All Failed"]
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


def create_success_rate_chart(ax, results):
    """Create the success rate horizontal bar chart."""
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

    ax.barh(
        y_pos - bar_height, sorted_http_rates, bar_height, label="HTTP", color="#2196F3"
    )
    ax.barh(y_pos, sorted_https_rates, bar_height, label="HTTPS", color="#673AB7")
    ax.barh(
        y_pos + bar_height, sorted_ssl_rates, bar_height, label="SSL", color="#009688"
    )

    ax.set_yticks(y_pos)
    ax.set_yticklabels(sorted_domains)
    ax.set_xlim(0, 105)

    # Add a vertical grid to help estimate percentages
    ax.grid(axis="x", linestyle="--", alpha=0.7)
    ax.set_xticks([0, 20, 40, 60, 80, 100])

    ax.set_title("Success Rate by Domain")
    ax.set_xlabel("Success Rate (%)")
    ax.legend(loc="lower right")


def create_ssl_expiry_chart(ax, results):
    """Create the SSL expiry heat map."""
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
        return

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
            fontsize=10,
            bbox=dict(
                facecolor="white",
                alpha=0.8,
                edgecolor="gray",
                boxstyle="round,pad=0.3",
            ),
        )

    ax.set_title("Days Until SSL Certificate Expiry")
    ax.set_xlabel("Days")

    # Ensure x-axis is wide enough to show labels
    current_xlim = ax.get_xlim()
    ax.set_xlim(0, current_xlim[1] * 1.3)  # Extend x-axis by 30%

    # Add a colorbar as a legend
    sm = plt.cm.ScalarMappable(cmap=cmap)
    sm.set_array([])
    cbar = plt.colorbar(sm, ax=ax)
    cbar.set_label("Expiry Urgency")


def create_response_time_chart(ax, results):
    """Create the response time comparison chart."""
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
        return

    # Sort by HTTP response time (if available)
    response_time_domains.sort(
        key=lambda x: x.get("avg_http_response_time", float("inf"))
    )

    domains_rt = [r["domain"] for r in response_time_domains]
    
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
            ax.text(h + 0.05, i - bar_height / 2, f"{h:.2f}s", va="center")
        if s > 0:  # Simple check for positive value
            ax.text(s + 0.05, i + bar_height / 2, f"{s:.2f}s", va="center")

    ax.set_yticks(y_pos)
    ax.set_yticklabels(domains_rt)
    ax.set_title("Average Response Time (seconds)")
    ax.set_xlabel("Time (seconds)")
    ax.legend()


def generate_plots(results):
    """Generate visualizations of domain health check results."""
    # Prepare data
    data = prepare_data(results)
    total_domains = data["total_domains"]

    # Create a figure with subplots
    fig = plt.figure(figsize=(15, 12))
    fig.suptitle(
        f"Domain Health Check Results (Total: {total_domains} domains)", fontsize=16
    )

    # 1. Summary bar chart
    ax1 = plt.subplot(3, 2, 1)
    create_status_summary(ax1, data)

    # 2. Pie chart for overall health
    ax2 = plt.subplot(3, 2, 2)
    create_health_pie_chart(ax2, data)

    # 3. Success rates horizontal bar chart
    ax3 = plt.subplot(3, 2, 3)
    create_success_rate_chart(ax3, results)

    # 4. SSL expiry heat map
    ax4 = plt.subplot(3, 2, 4)
    create_ssl_expiry_chart(ax4, results)

    # 5. Response time comparison chart
    ax5 = plt.subplot(3, 1, 3)
    create_response_time_chart(ax5, results)

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])

    # Save the plot with a generic filename
    filename = "domain_health_check_results.png"
    plt.savefig(filename, dpi=300, bbox_inches="tight")

    print(f"Results image saved as '{filename}'")

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