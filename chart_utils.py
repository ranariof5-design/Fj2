from datetime import datetime
import calendar
import os
import logging

# ============================================================
# Optional matplotlib support
# ============================================================

try:
    import matplotlib
    matplotlib.use("Agg")

    from matplotlib.figure import Figure
    import matplotlib.pyplot as plt
    from matplotlib.patches import Circle
    import numpy as np

    logging.getLogger("matplotlib").setLevel(logging.WARNING)
    MATPLOTLIB_AVAILABLE = True
except Exception:
    MATPLOTLIB_AVAILABLE = False


# ============================================================
# Date helpers
# ============================================================

def parse_date(date_str):
    try:
        return datetime.strptime(date_str[:10], "%Y-%m-%d")
    except Exception:
        return None

# ... [Keep your existing aggregation functions here: aggregate_by_month, etc] ...
# (They are unchanged, omitting for brevity)
def aggregate_by_month(expenses, year):
    monthly_totals = [0] * 12
    per_month_expenses = [[] for _ in range(12)]
    for exp in expenses:
        dt = parse_date(exp.get("date", ""))
        if dt and dt.year == year:
            idx = dt.month - 1
            monthly_totals[idx] += exp.get("amount", 0)
            per_month_expenses[idx].append(exp)
    return monthly_totals, per_month_expenses

def aggregate_by_day(expenses, year, month):
    days = calendar.monthrange(year, month)[1]
    daily_totals = [0] * days
    per_day_expenses = [[] for _ in range(days)]
    for exp in expenses:
        dt = parse_date(exp.get("date", ""))
        if dt and dt.year == year and dt.month == month:
            idx = dt.day - 1
            daily_totals[idx] += exp.get("amount", 0)
            per_day_expenses[idx].append(exp)
    return daily_totals, per_day_expenses

def aggregate_by_week(expenses, year, month):
    week_totals = [0] * 5
    per_week_expenses = [[] for _ in range(5)]
    for exp in expenses:
        dt = parse_date(exp.get("date", ""))
        if dt and dt.year == year and dt.month == month:
            idx = min((dt.day - 1) // 7, 4)
            week_totals[idx] += exp.get("amount", 0)
            per_week_expenses[idx].append(exp)
    return week_totals, per_week_expenses

def aggregate_by_category(expenses):
    data = {}
    for exp in expenses:
        cat = exp.get("category", "Other")
        data[cat] = data.get(cat, 0) + exp.get("amount", 0)
    return data


# ============================================================
# Chart utilities
# ============================================================

def create_bar_chart(labels, values, title="Bar Chart"):
    # ... [Keep your existing bar chart code] ...
    if not MATPLOTLIB_AVAILABLE:
        return None
    
    fig = Figure(figsize=(10, 4.5), dpi=100, facecolor="#0b0b0b")
    ax = fig.add_subplot(111, facecolor="#1a1a1a")
    
    colors = ["#0FA3B1", "#0FC4C9", "#1ECFE5", "#2DB8D6", "#3CA1C7"]
    bar_colors = [colors[i % len(colors)] for i in range(len(values))]
    
    bars = ax.bar(range(len(values)), values, color=bar_colors, width=0.65, edgecolor="#0FA3B1", linewidth=1.5)
    
    for bar, val in zip(bars, values):
        if val > 0:
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height(), f"₱{val:,.0f}", ha="center", va="bottom", fontsize=9, color="white", fontweight="bold")
            
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=45, ha="right", fontsize=10, color="#B0B0B0")
    ax.set_ylabel("Amount (₱)", fontsize=9, color="#B0B0B0", fontweight="bold")
    ax.set_title(title, fontsize=13, fontweight="bold", color="white", pad=15)
    ax.grid(axis="y", alpha=0.2, color="#333333", linestyle="--", linewidth=0.8)
    ax.set_axisbelow(True)
    ax.tick_params(colors="#B0B0B0", labelsize=9)
    for spine in ax.spines.values():
        spine.set_edgecolor="#333333"
        spine.set_linewidth(1)
        
    fig.tight_layout()
    return fig

def create_pie_chart_donut(data, title=None, explode=None):
    if not MATPLOTLIB_AVAILABLE or not data:
        return None, None

    labels = list(data.keys())
    values = list(data.values())
    total = sum(values)

    colors = [
        "#0FA3B1", "#1ECFE5", "#3FA9D6", "#5B8BC4", "#7B68BE",
        "#9B4FB3", "#BB4FA3", "#DB5F9D", "#E77F87", "#F39C12"
    ]

    if len(labels) > len(colors):
        colors *= (len(labels) // len(colors) + 1)

    # Calculate figure height dynamically
    # 0.4 inches per item ensures consistent spacing
    fig_height = max(5, len(labels) * 0.4)
    fig = Figure(figsize=(10, fig_height), dpi=100, facecolor="#0b0b0b")

    gs = fig.add_gridspec(1, 2, width_ratios=[1, 1], wspace=0)
    ax_donut = fig.add_subplot(gs[0, 0], facecolor="#0b0b0b")
    ax_legend = fig.add_subplot(gs[0, 1], facecolor="#0b0b0b")

    wedges, texts = ax_donut.pie(
        values,
        startangle=90,
        colors=colors[:len(labels)],
        explode=explode if explode else [0] * len(labels),
        wedgeprops=dict(width=0.45, edgecolor="#1a1a1a", linewidth=2.5),
        counterclock=False
    )

    for t in texts:
        t.set_text("")

    if title:
        ax_donut.text(
            0.5, 0.95, title,
            ha="center", va="top",
            fontsize=14, fontweight="bold", color="white",
            transform=ax_donut.transAxes
        )

    ax_legend.axis("off")

    legend_labels = []
    for i, (label, value) in enumerate(zip(labels, values)):
        pct = (value / total * 100) if total > 0 else 0
        short = label[:18] + ".." if len(label) > 18 else label
        prefix = "▶ " if explode and explode[i] > 0 else ""
        legend_labels.append(f"{prefix}{short:<18} {pct:>5.1f}% (₱{value:,.0f})")

    legend_elements = [
        Circle((0, 0), radius=0.4, facecolor=colors[i], edgecolor="#1a1a1a", linewidth=1)
        for i in range(len(labels))
    ]

    # Create Legend
    legend = ax_legend.legend(
        legend_elements,
        legend_labels,
        loc="center left", # This centers the block vertically
        frameon=False,
        fontsize=11,
        handlelength=1.5,
        labelspacing=1.0 
    )

    for i, text in enumerate(legend.get_texts()):
        text.set_family("monospace")
        if explode and explode[i] > 0:
            text.set_color(colors[i])
            text.set_fontweight("bold")
        else:
            text.set_color("#B0B0B0")

    # Important: Fill the figure completely to prevent savefig from resizing/cropping
    fig.subplots_adjust(0, 0, 1, 1)
    
    # ---------------------------------------------------------
    # CALCULATE METADATA MATHEMATICALLY
    # ---------------------------------------------------------
    # We allocated 0.4 inches of height per legend item in fig_height logic.
    # We can use this to calculate the exact normalized coordinates.
    
    num_items = len(labels)
    row_height_inch = 0.3
    
    # Normalized height of one row (0.0 to 1.0)
    row_height_norm = row_height_inch / fig_height
    
    # Total height of the legend block
    total_legend_height_norm = num_items * row_height_norm
    
    # Calculate Top Y (Center + Half Height)
    legend_center_y = 0.5
    legend_top_y = legend_center_y + (total_legend_height_norm / 2)
    
    items = []
    
    # The legend is in the RIGHT half (x=0.5 to x=1.0)
    # But inside the metadata, we want coordinates relative to the whole figure 
    # OR relative to the legend widget? The previous code used Figure coords.
    # Figure coords for the legend area are roughly x=0.5 to x=1.0
    
    # However, for the bbox, we want the touchable area.
    # Let's define the width as the full right half (0.5 width) or tighter.
    # Let's make it user-friendly: slightly left of center to right edge.
    legend_x0 = 0.55  
    legend_width = 0.45

    for i in range(num_items):
        # Top of this item
        item_top = legend_top_y - (i * row_height_norm)
        # Bottom of this item
        item_bottom = item_top - row_height_norm
        
        items.append({
            "index": i,
            "category": labels[i],
            # bbox: x, y, w, h (Normalized 0-1)
            "bbox": (legend_x0, item_bottom, legend_width, row_height_norm),
            "center_y": item_bottom + (row_height_norm / 2)
        })

    metadata = {
        "bbox": (0.5, 0.0, 0.5, 1.0), # Entire right half
        "items": items,
        "categories": labels,
        "num_items": len(labels)
    }

    return fig, metadata


# ============================================================
# Save helpers
# ============================================================

def save_figure_to_image(fig, filename):
    if not fig:
        return None

    path = os.path.abspath(filename)
    
    # CRITICAL FIX: Removed bbox_inches="tight"
    # "tight" crops the image, invalidating our coordinate calculations.
    # Since we set fig.subplots_adjust(0,0,1,1), the figure is already tight.
    fig.savefig(path, dpi=100, facecolor="#0b0b0b")
    
    plt.close(fig)
    return path
