import matplotlib.pyplot as plt
import numpy as np
import scanpy as sc


def umap_ncorr(data, fdr_thresh=None, key="coef", **kwargs):
    """
    Parameters
    ----------
    data : cna.data.Data
        The data object containing the obs dataframe with the neighborhood coefficients and FDR values.
    fdr_thresh : float, optional
        The FDR threshold to use for determining which neighborhoods are significant. If None, defaults to 0.1.
    key : str, default 'coef'
        The name of the column in obs that contains the neighborhood coefficients to plot. This should be the same as the key used in the association test.
    **kwargs :
        Additional keyword arguments to pass to the scatter plot of the significant neighborhoods. For instance, you can specify a colormap or vmin/vmax for the color scale.

    Returns
    -------
    ax : matplotlib.axes.Axes
    """
    if fdr_thresh is None:
        fdr_thresh = 0.1

    passed = data.obs[f"{key}_fdr"] <= fdr_thresh
    if len(passed) == 0:
        print("no neighborhoods were significant at FDR <", fdr_thresh)

    umap_overlay(data, passed, key, **kwargs)


def umap_overlay(data, mask, key, scatter0=None, scatter1=None, ax=None, *args, **kwargs):

    if scatter0 is None:
        scatter0 = {}
    if scatter1 is None:
        scatter1 = {}
    # set default plotting options
    if ax is None:
        ax = plt.gca()
    c = data.obs[mask][key]
    scatter0_ = {"alpha": 0.8, "s": 2}
    scatter1_ = {
        "alpha": 0.9,
        "s": 8,
        "cmap": "seismic",
        "vmin": -np.abs(c).max() if len(c) > 0 else 0,
        "vmax": np.abs(c).max() if len(c) > 0 else 1,
    }
    scatter0_.update(scatter0)
    scatter1_.update(scatter1)

    # do plotting
    sc.pl.umap(data, ax=ax, show=False, **scatter0_)
    sc.pl.umap(data[mask], color=key, ax=ax, show=False, title="", **scatter1_)

    return ax
