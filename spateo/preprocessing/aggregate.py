"""
Aggregate buckets of AnnData object by binning.
"""
import numpy as np
import pandas as pd
import scipy
from anndata import AnnData

from ..configuration import SKM
from ..logging import logger_manager as lm


@SKM.check_adata_is_type(SKM.ADATA_UMI_TYPE, "adata")
def bin_adata(
    adata: AnnData,
    bin_size: int = 1,
    coords_key: str = "spatial",
) -> AnnData:
    """Aggregate cell-based AnnData by bin size. Cells within the same bin are aggregated together into one bucket.

    Args:
        adata: Input AnnData object
        bin_size: Shrinking factor to be applied to spatial coordinates; the size of this factor dictates the size of
            the regions that will be combined into one pseudo-cell (larger -> generally higher number of cells in
            each bin).
        coords_key: Key in .obsm where spatial coordinates are stored- bin coordinates will be used to update this
            array inplace.

    Returns:
        adata_binned: New AnnData object generated by this process.
    """
    adata = adata.copy()
    adata.obsm[coords_key] = (adata.obsm[coords_key] // bin_size).astype(np.int32)

    if scipy.issparse(adata.X):
        df = pd.DataFrame(adata.X.A, columns=adata.var_names)
    else:
        df = pd.DataFrame(adata.X, columns=adata.var_names)

    df[["x", "y"]] = adata.obsm[coords_key]
    df2 = df.groupby(by=["x", "y"]).sum()

    adata_binned = AnnData(df2)
    adata_binned.uns["__type"] = "UMI"
    adata_binned.obs_names = [str(i[0]) + "_" + str(i[1]) for i in df2.index.to_list()]
    adata_binned.obsm[coords_key] = np.array([list(i) for i in df2.index.to_list()], dtype=np.float64)

    return adata_binned
