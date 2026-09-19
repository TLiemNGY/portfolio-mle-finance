import matplotlib.pyplot as plt

from ml.training.train import build_results_df

results_df = build_results_df()

results_df_5 = results_df[results_df["horizon_days"] == 5]

fig, ax = plt.subplots()
ax.bar(results_df_5["model"], results_df_5["mae"])
ax.set_xlabel("Models")
ax.set_ylabel("MAE")
ax.set_title("MAE per model: 5-day horizon")
ax.set_xticklabels(results_df_5["model"], rotation=15, ha="right")
fig.savefig("ml/results/figures/MAE_per_model.png")
