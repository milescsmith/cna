import warnings

import multianndata as mad
import numpy as np
import numpy.typing as npt
import pandas as pd
from numba import float64, int64, jit
from numba.typed import List
from scipy.stats import f as f_test

from cna.tools._nam import _df_to_array, nam
from cna.tools._out import select_output
from cna.tools._stats import conditional_permutation, empirical_fdrs


def _association(
    NAMsvd,
    NAMresid,
    M,
    r,
    y,
    batches,
    ks=None,
    Nnull: int = 1000,
    force_permute_all: bool = False,
    local_test: bool = True,
    seed: int | None = None,
    show_progress: bool = False,
):
    # output level
    out = select_output(show_progress)

    if seed is not None:
        np.random.seed(seed)
    if force_permute_all:
        batches = np.ones(len(y))

    # prep data
    U, *_ = NAMsvd
    y = (y - y.mean()) / y.std()
    n = len(y)

    if ks is None:
        incr = max(int(0.02 * n), 1)
        maxnpcs = min(4 * incr, int(n / 5))
        ks = np.arange(incr, maxnpcs + 1, incr)

    @jit(nopython=True)
    def _reg(q, k):
        Xpc = U[:, :k]
        beta = Xpc.T.dot(q)  # Xpc.T.dot(Xpc) = I so no need to compute it
        qhat = Xpc.dot(beta)
        return qhat, beta

    @jit(nopython=True)
    def _stats(yhat, ycond, k):
        ssefull = (yhat - ycond).dot(yhat - ycond)
        ssered = ycond.dot(ycond)
        deltasse = ssered - ssefull
        f = (deltasse / k) / (ssefull / n)
        p = f_test(f, k, n - (1 + r + k))  # F test
        r2 = 1 - ssefull / ssered
        return p, r2

    @jit((int64, float64, int64)(List(float64)), nopython=True)
    def _minp_stats(z: np.ndarray) -> tuple[np.int64, np.float64, np.float64]:
        zcond = M.dot(z)
        zcond = zcond / zcond.std()
        ps, r2s = np.array([_stats(_reg(zcond, k)[0], zcond, k) for k in ks]).T
        k_ = np.argmin(ps)
        return ks[k_], ps[k_], r2s[k_]

    # get non-null f-test p-value
    k, p, r2 = _minp_stats(y)
    if k == max(ks):
        warnings.warn(
            (
                f"data supported use of {k} NAM PCs, which is the maximum considered. "
                'Consider allowing more PCs by using the "ks" argument.'
            ),
            stacklevel=2,
        )

    # compute coefficients and r2 with chosen model
    ycond = M.dot(y)
    ycond /= ycond.std()
    yhat, beta = _reg(ycond, k)
    # _, fullbeta = _reg(ycond, n)
    r2_perpc = (beta / np.sqrt(ycond.dot(ycond))) ** 2

    # get neighborhood coefficients
    ncorrs = (y[:, None] * NAMresid).mean(axis=0)

    # compute final p-value using Nnull null f-test p-values
    y_: npt.ArrayLike = conditional_permutation(batches, y, Nnull)
    nullminps, nullr2s = np.array([_minp_stats(y__)[1:] for y__ in y_.T]).T
    pfinal = ((nullminps <= p + 1e-8).sum() + 1) / (Nnull + 1)
    if (nullminps <= p + 1e-8).sum() == 0:
        warnings.warn(
            "global association p-value attained minimal possible value. Consider increasing Nnull", stacklevel=2
        )

    # get neighborhood fdrs if requested
    fdrs, fdr_5p_t, fdr_10p_t = None, None, None
    if local_test:
        print("computing neighborhood-level FDRs", file=out)
        Nnull = min(1000, Nnull)
        y_ = y_[:, :Nnull]
        ycond_ = M.dot(y_)
        ycond_ /= ycond_.std(axis=0)
        U[:, :k].T.dot(ycond_)
        nullncorrs = np.abs(NAMresid.T.dot(ycond_) / n)

        maxcorr = np.abs(ncorrs).max()
        fdr_thresholds = np.arange(maxcorr / 4, maxcorr, maxcorr / 400)
        fdr_vals = empirical_fdrs(ncorrs, nullncorrs, fdr_thresholds)

        fdrs = pd.DataFrame(
            {
                "threshold": fdr_thresholds,
                "fdr": fdr_vals,
                "num_detected": [(np.abs(ncorrs) > t).sum() for t in fdr_thresholds],
            }
        )

        # find maximal FDR<5% and FDR<10% sets
        if np.min(fdrs.fdr) > 0.05:
            fdr_5p_t = None
        else:
            fdr_5p_t = fdrs[fdrs.fdr <= 0.05].iloc[0].threshold
        if np.min(fdrs.fdr) > 0.1:
            fdr_10p_t = None
        else:
            fdr_10p_t = fdrs[fdrs.fdr <= 0.1].iloc[0].threshold

        # del gamma_, nullncorrs

    # del y_

    res = {
        "p": pfinal,
        "nullminps": nullminps,
        "k": k,
        "ncorrs": ncorrs,
        "fdrs": fdrs,
        "fdr_5p_t": fdr_5p_t,
        "fdr_10p_t": fdr_10p_t,
        "yresid_hat": yhat,
        "yresid": ycond,
        "ks": ks,
        "beta": beta,
        "r2": r2,
        "r2_perpc": r2_perpc,
        "nullr2_mean": nullr2s.mean(),
        "nullr2_std": nullr2s.std(),
    }
    return res
    # return Namespace(**res)


def association(
    data: mad.MultiAnnData,
    y,
    batches=None,
    covs=None,
    nsteps=None,
    suffix="",
    force_recompute=False,
    show_progress=False,
    allow_low_sample_size=False,
    **kwargs,
):
    # output level
    out = select_output(show_progress)

    # formatting and error checking
    if batches is None:
        batches = np.ones(data.N)
    covs = _df_to_array(data, covs)
    batches = _df_to_array(data, batches)
    y = _df_to_array(data, y)
    if y.shape != (data.N,):
        msg = f"y should be an array of length data.N; instead its shape is: {y.shape!s}"
        raise ValueError(msg)
    if data.N < 10 and not allow_low_sample_size:
        msg = (
            "Dataset has fewer than 10 samples. CNA may have poor power at low sample sizes "
            "because its null distribution is one in which each sample's single-cell profile "
            "is unchanged but the sample labels are randomly assigned. If you want to run CNA "
            "at this sample size despite the possibility of low power, you can do so by "
            "invoking the association(...) function with the argument "
            "allow_low_sample_size=True."
        )
        raise ValueError(msg)

    if covs is not None:
        filter_samples = ~(np.isnan(y) | np.any(np.isnan(covs), axis=1))
    else:
        filter_samples = ~np.isnan(y)

    du = data.uns
    nam(
        data,
        batches=batches,
        covs=covs,
        filter_samples=filter_samples,
        nsteps=nsteps,
        suffix=suffix,
        force_recompute=force_recompute,
        show_progress=show_progress,
        **kwargs,
    )
    NAMsvd = (du["NAM_sampleXpc" + suffix].values, du["NAM_svs" + suffix], du["NAM_nbhdXpc" + suffix].values)

    print("performing association test", file=out)
    res = _association(
        NAMsvd,
        du["NAM_resid.T" + suffix].T,
        du["_M" + suffix],
        du["_r" + suffix],
        y[du["_filter_samples" + suffix]],
        batches[du["_filter_samples" + suffix]],
        show_progress=show_progress,
        **kwargs,
    )

    # add info about kept cells
    vars(res)["kept"] = du["keptcells" + suffix]

    return res
