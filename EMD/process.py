import numpy as np
from scipy import sparse
import scipy.io as sio
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from EMD import *

LABELS = ['EF_node', 'Spelling_node', 'Naming_node', 'Syntax_node']

def get_EMD(idx, indicator, plot_name = ""):
    """
    Get the earth-movers distances between two ranks
    Parameters
    ----------
    idx: ndarray(N)
        Rank of each node
    indicator: ndarray(N)
        An array which is 1 if it's part of the node type
        and 0 if it's another type
    plot_name: string
        If non-empty, plot and save to a file with this name
    """
    # Nodes that are part of this type
    T = np.zeros_like(idx)
    T[idx[indicator == 1]] = 1
    T = T/np.sum(T)
    # Rest of nodes
    F = np.zeros_like(idx)
    F[idx[indicator == 0]] = 1 
    F = F/np.sum(F)
    cT = np.cumsum(T) # True CDF
    cF = np.cumsum(F) # False CDF
    dist = np.sum(np.abs(cT-cF))
    if len(plot_name) > 0:
        plt.clf()
        plt.subplot(211)
        plt.stem(T, use_line_collection=True)
        plt.title("%s, %.3g"%(plot_name, dist))
        plt.subplot(212)
        plt.stem(F, use_line_collection=True)
        plt.savefig(plot_name, bbox_inches='tight')
    return dist

def do_permtest(df, n_perms, prefix):
    """
    Do the analyses on a particular dataframe
    Parameters
    ----------
    df: pandas dataframe
        The dataframe
    n_perms: int
        Number of random permutations to use as the null hypothesis
    prefix: string
        prefix for filenames
    """
    names = df.columns[1:-4]
    labels = df[LABELS].to_numpy()
    labels[np.isnan(labels)] = 0
    N = labels.shape[0]
    for l, label in enumerate(LABELS):
        print(label)
        ## Step 1: Scores on actual data
        emds = []
        mean_ranks = []
        for name in names:
            # Get ranks
            idx = np.zeros(N, dtype=int)
            idx[np.argsort(-df[name].to_numpy())] = np.arange(N)
            emd = get_EMD(idx, labels[:, l])#, "{}_{}.png".format(label, name))
            emds.append(emd)
            mean_ranks.append(np.mean(idx[labels[:, l] == 1]))
        emds = np.array(emds)
        mean_ranks = np.array(mean_ranks)
        ## Step 2: Scores on random permutations
        emds_null = np.zeros(n_perms)
        mean_ranks_null = np.zeros(n_perms)
        np.random.seed(0)
        for p in range(n_perms):
            idx = np.random.permutation(N)
            emd = get_EMD(idx, labels[:, l])
            emds_null[p] = emd
            mean_ranks_null[p] = np.mean(idx[labels[:, l] == 1])
        nauroc = 2*(getAUROC(emds, emds_null)['auroc']-0.5)
        #auroc = max(getAUROC(emds, emds_null)['auroc'], getAUROC(emds_null, emds)['auroc'])
        plt.figure(figsize=(8, 4))
        sns.distplot(emds, kde=True, norm_hist=True, label="True Distances")
        sns.distplot(emds_null, kde=True, norm_hist=True, label="Monte Carlo")
        plt.title("EMDs of {} for {}, NAUROC = {:.3f}".format(label, prefix, nauroc))
        plt.xlabel("Earth Movers Distance")
        plt.ylabel("Density")
        plt.savefig("{}_EMD_{}.svg".format(prefix, label), bbox_inches='tight')
        plt.clf()
        #auroc = max(getAUROC(mean_ranks, mean_ranks_null)['auroc'], getAUROC(mean_ranks_null, mean_ranks)['auroc'])
        nauroc = 2*(getAUROC(mean_ranks, mean_ranks_null)['auroc']-0.5)
        sns.distplot(mean_ranks, kde=True, norm_hist=True)
        sns.distplot(mean_ranks_null, kde=True, norm_hist=True)
        plt.xlabel("Mean Rank")
        plt.ylabel("Density")
        plt.title("Mean Ranks of {} for {}, NAUROC = {:.3f}".format(label, prefix, nauroc))
        plt.savefig("{}_MR_{}.svg".format(prefix, label), bbox_inches='tight')


def do_analyses_feat(feat):
    """
    Parameters
    ----------
    feat: string
        Type of feature (either PD or WD)
    """
    controls = pd.read_csv("{}_controls.csv".format(feat))
    patients = pd.read_csv("{}_patients.csv".format(feat))
    do_permtest(controls, 1000, "{}_controls".format(feat))
    do_permtest(patients, 1000, "{}_patients".format(feat))

do_analyses_feat("WD")
do_analyses_feat("PC")