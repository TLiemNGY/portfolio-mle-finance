"""Distribution of daily returns: how far are they from a normal distribution?

The volatility tool builds price ranges as last close +/- k standard deviations,
with coverages taken from the normal distribution (68 % at 1 sigma, 95 % at
2 sigma). This analysis checks that assumption on the price history.

Statistics are computed per ticker: pooling tickers with different volatility
levels would create fat tails that do not exist in any single ticker.
"""

import logging
from pathlib import Path
from statistics import NormalDist

import numpy as np
import pandas as pd
from google.cloud import bigquery
from matplotlib.figure import Figure

from core.config import PROJECT_ID
from ml.training.build_features import (
    compute_return_and_volatility_features,
    get_price_history,
)

logger = logging.getLogger(__name__)
REPO_ROOT = Path(__file__).resolve().parents[2]
FIGURE_PATH = REPO_ROOT / "docs" / "images" / "return_distribution.png"

# Chart colors (light background).
SURFACE = "#fcfcfb"
TEXT_PRIMARY = "#0b0b0b"
TEXT_SECONDARY = "#52514e"
GRID = "#e4e3df"
SERIES = {
    "z_unconditional": ("#2a78d6", "Divided by the average volatility"),
    "z_conditional": ("#eb6834", "Divided by the previous day's 20-day volatility"),
}
HISTOGRAM_RANGE = (-8.0, 8.0)


def compute_return_stats(df: pd.DataFrame, column: str = "return") -> pd.DataFrame:
    """Compute the shape statistics of a return column, per ticker.

    Args:
        df: One row per ticker and day, with a "ticker" column and the column
            to describe.
        column: The return column to describe (raw or standardized).

    Returns:
        One row per ticker (index: ticker) with the columns n_days, std, skew
        and excess_kurtosis. Excess kurtosis is 0 for a normal distribution and
        positive for fat tails.
    """
    stats = df.groupby("ticker")[column].agg(["count", "std", "skew", pd.Series.kurt])
    return stats.rename(columns={"count": "n_days", "kurt": "excess_kurtosis"})


def standardize_returns(df: pd.DataFrame) -> pd.DataFrame:
    """Add daily returns expressed in numbers of standard deviations.

    - z_unconditional: return divided by the ticker's standard deviation over
      the whole history (how extreme the day was on average).
    - z_conditional: return divided by the previous day's 20-day volatility,
      i.e. the volatility known before the return happened (how extreme the
      day was given recent conditions). Using the same day's volatility would
      leak the return into its own denominator and hide fat tails.

    Args:
        df: One row per ticker and day, sorted by ticker and date, with the
            columns "ticker", "return" and "volatility_20d".

    Returns:
        The same DataFrame with the columns z_unconditional and z_conditional.
    """
    by_ticker = df.groupby("ticker")
    df["z_unconditional"] = df["return"] / by_ticker["return"].transform("std")
    df["z_conditional"] = df["return"] / by_ticker["volatility_20d"].shift(1)

    return df


def plot_return_distribution(df: pd.DataFrame, path: Path) -> None:
    """Save a log-scale density and a QQ-plot of standardized returns vs a normal distribution.

    Args:
        df: Standardized returns, with the columns listed in SERIES.
        path: Where to save the PNG figure.
    """
    normal = NormalDist()
    fig = Figure(figsize=(11, 4.8), facecolor=SURFACE, layout="constrained")
    density_ax, qq_ax = fig.subplots(1, 2)
    bins = np.linspace(*HISTOGRAM_RANGE, 49)

    for column, (color, label) in SERIES.items():
        z = np.sort(df[column].dropna().to_numpy())
        density_ax.hist(
            z,
            bins=bins,
            density=True,
            histtype="step",
            linewidth=2,
            color=color,
            label=label,
        )
        probabilities = (np.arange(1, len(z) + 1) - 0.5) / len(z)
        normal_quantiles = [normal.inv_cdf(p) for p in probabilities]
        qq_ax.plot(normal_quantiles, z, linewidth=2, color=color)

    x = np.linspace(*HISTOGRAM_RANGE, 400)
    density_ax.plot(
        x,
        [normal.pdf(value) for value in x],
        linestyle="--",
        linewidth=1.5,
        color=TEXT_SECONDARY,
        label="Normal distribution",
    )
    density_ax.set_yscale("log")
    density_ax.set_ylim(1e-4, 1)
    density_ax.set_title(
        "Density (log scale): the tails", color=TEXT_PRIMARY, fontsize=11, loc="left"
    )
    density_ax.set_xlabel("Daily return, in standard deviations", color=TEXT_SECONDARY)
    density_ax.set_ylabel("Density", color=TEXT_SECONDARY)

    limit = max(abs(value) for value in qq_ax.get_xlim())
    qq_ax.plot(
        [-limit, limit],
        [-limit, limit],
        linestyle="--",
        linewidth=1.5,
        color=TEXT_SECONDARY,
    )
    qq_ax.set_title(
        "QQ-plot: points off the diagonal are not normal",
        color=TEXT_PRIMARY,
        fontsize=11,
        loc="left",
    )
    qq_ax.set_xlabel("Quantiles of a normal distribution", color=TEXT_SECONDARY)
    qq_ax.set_ylabel("Observed quantiles", color=TEXT_SECONDARY)

    for ax in (density_ax, qq_ax):
        ax.set_facecolor(SURFACE)
        ax.grid(color=GRID, linewidth=0.8)
        ax.set_axisbelow(True)
        ax.tick_params(colors=TEXT_SECONDARY, labelsize=9)
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)
        for side in ("left", "bottom"):
            ax.spines[side].set_color(GRID)

    fig.suptitle(
        "Daily returns vs a normal distribution (all tickers pooled)",
        color=TEXT_PRIMARY,
        fontsize=13,
        x=0.01,
        ha="left",
    )
    fig.legend(
        *density_ax.get_legend_handles_labels(),
        loc="outside lower center",
        ncols=3,
        frameon=False,
        labelcolor=TEXT_SECONDARY,
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=150, facecolor=SURFACE)
    logger.info("Figure saved to %s", path)


def main() -> None:
    client = bigquery.Client(project=PROJECT_ID)
    df = get_price_history(client)
    df = compute_return_and_volatility_features(df)
    df = standardize_returns(df)

    raw = compute_return_stats(df)
    conditional = compute_return_stats(df, column="z_conditional")
    comparison = pd.DataFrame(
        {
            "kurtosis_raw": raw["excess_kurtosis"],
            "kurtosis_conditional": conditional["excess_kurtosis"],
            "std_conditional": conditional["std"],
        }
    ).sort_values("kurtosis_raw", ascending=False)
    logger.info(
        "Excess kurtosis per ticker, raw vs conditional:\n%s",
        comparison.round(3).to_string(),
    )

    pooled = df[["z_unconditional", "z_conditional"]].agg(
        ["count", "std", "skew", pd.Series.kurt]
    )
    logger.info("All tickers pooled:\n%s", pooled.round(3).to_string())
    plot_return_distribution(df, FIGURE_PATH)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
