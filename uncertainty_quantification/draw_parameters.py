#!/usr/bin/env python

"""
Uncertainty quantification using Latin Hypercube Sampling or Sobol Sequences
"""

from argparse import ArgumentParser
from typing import Any, Dict

import numpy as np
import pandas as pd
from pyDOE import lhs
from scipy.stats.distributions import randint, uniform, truncnorm


dists: Dict[str, Any] = {
    "speed-calib": {
        "uq": {"a_glen": uniform(0.25e-24, 2e-24),
               "sia_n": uniform(2, 3),
               "pseudo_plastic_q": uniform(0.4, 0.4),
               "z_min": uniform(-1000, 1000),
               "z_max": uniform(0, 1000),
               "phi_min": uniform(15, 20),
               "phi_max": uniform(25, 20),
               "till_effective_fraction_overburden": uniform(0.02, 0.04),
               "pseudo_plastic_uthreshold": uniform(25, 175)},
        "default_values": {
            "climate": "harmonie_flux",
            "climate_file": "HARMONIE_glac_corr_1980_2016_TM.nc",
            "sia_n": 3,
            "a_glen": 2e-24,
            "pseudo_plastic_q": 0.5,
            "z_min": -1000,
            "z_max": 100,
            "phi_min": 20,
            "phi_max": 40,
            "till_effective_fraction_overburden": 0.04,
            "pseudo_plastic_uthreshold": 100,
        },
    },
    "random-calib": {
        "uq": {"a_glen": uniform(0.25e-24, 2e-24),
               "sia_n": uniform(2, 3),
               "pseudo_plastic_q": uniform(0.4, 0.4),
               "till_effective_fraction_overburden": uniform(0.02, 0.03),
               "pseudo_plastic_uthreshold": uniform(25, 175)},
        "default_values": {
            "climate": "harmonie_flux",
            "climate_file": "HARMONIE_glac_corr_1980_2016_TM.nc",
            "sia_n": 3,
            "a_glen": 2e-24,
            "pseudo_plastic_q": 0.5,
            "z_min": -1000,
            "z_max": 100,
            "phi_min": 20,
            "phi_max": 40,
            "till_effective_fraction_overburden": 0.04,
            "pseudo_plastic_uthreshold": 100,
        },
    },
}

parser = ArgumentParser()
parser.description = "Generate UQ using Latin Hypercube or Sobol Sequences."
parser.add_argument(
    "-s",
    "--n_samples",
    dest="n_samples",
    type=int,
    help="""number of samples to draw. default=10.""",
    default=10,
)
parser.add_argument(
    "-d",
    "--distribution",
    dest="distribution",
    choices=dists.keys(),
    help="""Choose set.""",
    default="speed-calib",
)
parser.add_argument(
    "--posterior_file",
    help="Posterior predictive parameter file",
    default=None,
)
parser.add_argument(
    "OUTFILE",
    nargs=1,
    help="Ouput file (CSV)",
    default="velocity_calibration_samples.csv",
)
options = parser.parse_args()
n_draw_samples = options.n_samples
outfile = options.OUTFILE[-1]
distribution_name = options.distribution
posterior_file = options.posterior_file

print(f"\nDrawing {n_draw_samples} samples from distribution set {distribution_name}")
distributions = dists[distribution_name]["uq"]

problem = {
    "num_vars": len(distributions.keys()),
    "names": distributions.keys(),
    "bounds": [[0, 1]] * len(distributions.keys()),
}

keys_prior = list(distributions.keys())

unif_sample = lhs(len(keys_prior), n_draw_samples)

n_samples = unif_sample.shape[0]
# To hold the transformed variables
dist_sample = np.zeros_like(unif_sample, dtype="object")

# For each variable, transform with the inverse of the CDF (inv(CDF)=ppf)
for i, key in enumerate(keys_prior):
    dist_sample[:, i] = distributions[key].ppf(unif_sample[:, i])

if posterior_file:
    X_posterior = pd.read_csv(posterior_file).drop(
        columns=["Unnamed: 0", "Model"], errors="ignore"
    )
    keys_mc = list(X_posterior.keys())
    keys = list(set(keys_prior + keys_mc))
    print(keys_prior, keys_mc)
    if len(keys_prior) + len(keys_mc) != len(keys):
        print("Duplicate keys, exciting.")
    keys = keys_prior + keys_mc
    mc_indices = np.random.choice(range(X_posterior.shape[0]), n_samples)
    X_sample = X_posterior.to_numpy()[mc_indices, :]

    dist_sample = np.hstack((dist_sample, X_sample))

else:
    keys = keys_prior


# Convert to Pandas dataframe, append column headers, output as csv
df = pd.DataFrame(dist_sample, columns=keys)
df.to_csv(outfile, index=True, index_label="id")

print("\nAdding default values\n")
for key, val in dists[distribution_name]["default_values"].items():
    if key not in df.columns:
        df[key] = val
        print(f"{key}: {val}")

df.to_csv(f"ensemble_{outfile}", index=True, index_label="id")
