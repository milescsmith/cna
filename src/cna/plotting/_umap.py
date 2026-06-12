from typing import Any

import anndata as ad
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import scanpy as sc
from matplotlib.axes import Axes


def umap_ncorr(data: ad.AnnData, fdr_thresh: float | None = None, key: str = "coef", **kwargs) -> None:
    """
    Parameters
    ----------
    data : :class:`ad.AnnData`
        The data object containing the obs dataframe with the neighborhood coefficients and FDR values.
    fdr_thresh : float, optional
        The FDR threshold to use for determining which neighborhoods are significant. If None, defaults to 0.1.
    key : str, default 'coef'
        The name of the column in obs that contains the neighborhood coefficients to plot. This should be the same as
        the key used in the association test.
    **kwargs :
        Additional keyword arguments to pass to the scatter plot of the significant neighborhoods. For instance, you
        can specify a colormap or vmin/vmax for the color scale.

    Returns
    -------
    None. Displays the plot.
    """
    if fdr_thresh is None:
        fdr_thresh = 0.1

    passed = data.obs[f"{key}_fdr"] <= fdr_thresh
    if len(passed) == 0:
        print("no neighborhoods were significant at FDR <", fdr_thresh)

    umap_overlay(data, passed, key, **kwargs)


def umap_overlay(
    data: ad.AnnData,
    mask: pd.Series,
    key: str,
    scatter0: dict[str, Any] | None = None,
    scatter1: dict[str, Any] | None = None,
    ax: Axes | None = None,
    *args,
    **kwargs,
):
    """
    Returns
    -------
    ax : matplotlib.axes.Axes
    """
    if scatter0 is None:
        scatter0 = {}
    if scatter1 is None:
        scatter1 = {}
    # set default plotting options
    if ax is None:
        ax = plt.gca()
    c = data.obs[mask][key]
    scatter0 = {**scatter0, **{"alpha": 0.8, "s": 2}}
    scatter1 = {
        **scatter1,
        **{
            "alpha": 0.9,
            "s": 8,
            "cmap": "seismic",
            "vmin": -np.abs(c).max() if len(c) > 0 else 0,
            "vmax": np.abs(c).max() if len(c) > 0 else 1,
        },
    }

    # do plotting
    sc.pl.umap(data, ax=ax, show=False, **scatter0)
    sc.pl.umap(data[mask], color=key, ax=ax, show=False, title="", **scatter1)

    return ax
