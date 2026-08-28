import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

BASE = r"C:\projects\saas-platform-v2\cliente-demo"
OUT = os.path.join(BASE, "slides")
os.makedirs(OUT, exist_ok=True)

def revenue_chart(fname):
    fig, ax = plt.subplots(figsize=(12.8, 7.2), dpi=100)
    fig.patch.set_facecolor("#0b1222")
    ax.set_facecolor("#0b1222")
    meses = ["Ene","Feb","Mar","Abr","May","Jun","Jul","Ago","Sep","Oct"]
    ventas = [2.1, 2.6, 3.2, 3.0, 3.9, 4.5, 5.2, 6.1, 7.0, 8.4]
    x = np.arange(len(meses))
    # area fill
    ax.fill_between(x, ventas, color="#2563eb", alpha=0.35)
    ax.plot(x, ventas, color="#3b82f6", lw=3.5, marker="o", markersize=8, markerfacecolor="#60a5fa")
    # gradient-ish highlight of last points
    for i in range(6, len(meses)):
        ax.annotate("", xy=(i, ventas[i]), xytext=(i-1, ventas[i-1]),
                    arrowprops=dict(arrowstyle="-", color="#34d399", lw=0))
    # labels
    for i, v in enumerate(ventas):
        ax.annotate(f"${v:,}k", (x[i], v), textcoords="offset points", xytext=(0,12),
                    ha="center", fontsize=12, color="#e2e8f0", fontweight="bold")
    ax.set_xticks(x); ax.set_xticklabels(meses, color="#94a3b8", fontsize=13)
    ax.set_yticks([])
    ax.spines[["top","right","left"]].set_visible(False)
    ax.spines["bottom"].set_color("#1e293b")
    ax.set_xlim(-0.5, len(meses)-0.3)
    ax.set_ylim(0, max(ventas)*1.35)
    # highlight growth badge
    ax.text(0.02, 0.94, "+300% en 10 meses", transform=ax.transAxes, fontsize=22,
            color="#34d399", fontweight="bold")
    ax.text(0.02, 0.86, "Ventas / mes (USD)", transform=ax.transAxes, fontsize=13,
            color="#94a3b8")
    plt.tight_layout()
    fig.savefig(os.path.join(OUT, fname), dpi=100, facecolor="#0b1222")
    plt.close(fig)
    print("chart ok", fname)

revenue_chart("s_chart_ganancias.png")
