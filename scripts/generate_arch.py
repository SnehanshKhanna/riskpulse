import matplotlib.pyplot as plt

fig, ax = plt.subplots(figsize=(10, 6))
ax.axis("off")

# A very simple text-based diagram
ax.text(0.5, 0.9, "RiskPulse Architecture", fontsize=16, ha="center", weight="bold")

boxes = [
    (0.1, 0.6, 0.25, 0.2, "Data Sources\n(News, Social)"),
    (0.4, 0.6, 0.25, 0.2, "Offline Pipeline\n(Polars/HuggingFace)"),
    (0.7, 0.6, 0.25, 0.2, "Risk Engine\n(NLP/FinBERT)"),
    (0.1, 0.2, 0.25, 0.2, "Storage\n(SQLite/Parquet)"),
    (0.4, 0.2, 0.25, 0.2, "API\n(FastAPI)"),
    (0.7, 0.2, 0.25, 0.2, "Frontend\n(React)"),
    (0.7, 0.4, 0.25, 0.1, "Stress Engine\n(Module B)")
]

for (x, y, w, h, text) in boxes:
    rect = plt.Rectangle((x, y), w, h, fill=True, color="#e0f2fe", ec="#0369a1", lw=2)
    ax.add_patch(rect)
    ax.text(x + w/2, y + h/2, text, ha="center", va="center", fontsize=10, weight="bold")

# Arrows
ax.annotate("", xy=(0.35, 0.7), xytext=(0.4, 0.7), arrowprops=dict(arrowstyle="<-", lw=2))
ax.annotate("", xy=(0.65, 0.7), xytext=(0.7, 0.7), arrowprops=dict(arrowstyle="<-", lw=2))
ax.annotate("", xy=(0.825, 0.6), xytext=(0.825, 0.5), arrowprops=dict(arrowstyle="->", lw=2))
ax.annotate("", xy=(0.825, 0.4), xytext=(0.825, 0.3), arrowprops=dict(arrowstyle="->", lw=2))
ax.annotate("", xy=(0.7, 0.3), xytext=(0.65, 0.3), arrowprops=dict(arrowstyle="<-", lw=2))
ax.annotate("", xy=(0.4, 0.3), xytext=(0.35, 0.3), arrowprops=dict(arrowstyle="<-", lw=2))

plt.savefig("docs/architecture.png", bbox_inches="tight", dpi=150)
print("Saved docs/architecture.png")
