import pandas as pd


def obs_to_sample(d, columns, sid_name, aggregate="mean"):
    """Aggregate feature values from obs to sample level, using the specified aggregate function.
    I.e. for each sample, compute the mean (or other aggregate) of the feature values across all cells in that sample.

    Note that if you are trying to look for associations for a categorical variable (e.g. case/control), you
    will need to recode those as a integer.

    Parameters
    ----------
    d : cna.data.Data
        The data object containing the obs dataframe.
    columns : str or list of str
        The column(s) in obs that have features to aggregate. For instance, an ELIZA or Olink levels.
    sid_name : str
        The name of the column in obs that contains the sample IDs.
    aggregate : str, default 'mean'
        The aggregate function to use. Can be any function supported by pandas groupby aggregate, such as 'mean', 'median', 'sum', etc.

    Returns
    -------
    samplem : pd.DataFrame
        A dataframe with index as sample IDs and columns as the aggregated feature values.
    """
    if isinstance(columns, str):
        columns = [columns]

    samplem = pd.DataFrame(index=d.obs[sid_name].unique())
    samplem[columns] = d.obs.groupby(by=sid_name)[columns].aggregate(aggregate)

    return samplem
