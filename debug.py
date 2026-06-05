import anndata as ad
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import scanpy as sc

import cna

np.random.seed(0)

# read in data
d = ad.read_h5ad('demo/data.h5ad')

# create sample-level metadata by combining across all cells from each sample 
samplem = cna.ut.obs_to_sample(
    d,
    ['case','male','batch'],
    'id'
)

p = cna.tl.association(
    d,
    samplem.case,
    "id",
    covs=samplem[["male"]],
    batches=samplem.batch,
    key_added="case_coef",
    ks=10,
)
print(p)