import multianndata as mad
import scanpy as sc


# # why?
def read(filename, **kwargs):
    return mad.MultiAnnData(sc.read(filename, **kwargs))
