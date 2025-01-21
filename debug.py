import cna
import multianndata
import scanpy as sc
import numpy as np
import pandas as pd
import stackprinter

if __name__ == "__main__":
    stackprinter.set_excepthook(style="lightbg", suppressed_paths=[r"lib/python.*/site-packages"])
    bcells = sc.read_h5ad("only_with_olink_data.h5ad")
    d = multianndata.MultiAnnData(bcells, sampleid="sample")
    d.obs_to_sample(["batch",  "MAVS"])
    res_MAVS = cna.tl.association(
        data=d,
        y=d.samplem.MAVS,
        batches=d.samplem.batch
    )
    ax = cna.pl.violinplot(
        data=d,
        res=res_MAVS,
        stratification='leiden',
        )