import numpy as np
import pandas as pd

ifile = "MassBalance_07022019.xlsx"


def merge_sectors(df, idx):

    return np.int(np.floor(df["Sector"].loc[idx]))


# These are the variables names aka Excel sheet_names
var_names = ["F", "b-dot_ds", "delS_ds", "D", "b-dot", "m-dot"]


for s, mvar in enumerate(var_names):
    # Read sheet into DataFrame
    df = pd.read_excel(ifile, sheet_name=mvar)
    # Remove totals and labels
    df = df.drop([0, 20], axis=0).astype("float")
    # Name of the uncertainty variable
    mvar_sigma = mvar + "_sigma"

    for k, year in enumerate(range(1995, 2016)):
        # Column index of year of variable
        year_idx = df.columns.get_loc(year)
        # Column name of associated sigma
        sigma_col = "Unnamed: {}".format(year_idx + 1)
        # DataFrame of variable
        v_df = pd.DataFrame(data=df[year].values, columns=[mvar])
        # Merge with Sector, need to reset index to start a 0
        v_df = pd.merge(df["Sector"].reset_index(drop=True), v_df, left_index=True, right_index=True)
        # Apply grouping function, sum up
        # We could write
        # v_df = v_df.groupby(lambda x: merge_sectors(v_df, x)).sum()
        # but we use agg and lambda instead to show the similarity to the sum of squares for sigmas
        v_df = v_df.groupby(lambda x: merge_sectors(v_df, x)).agg(lambda x: np.sum(x))
        # DataFrame of of associated sigma variable
        vs_df = pd.DataFrame(data=df[sigma_col].values, columns=[mvar_sigma])
        # Merge with Sector, need to reset index to start a 0
        vs_df = pd.merge(df["Sector"].reset_index(drop=True), vs_df, left_index=True, right_index=True)
        # Apply grouping function, sum up squares
        vs_df = vs_df.groupby(lambda x: merge_sectors(vs_df, x)).agg(lambda x: np.sqrt(np.sum(x ** 2)))
        v_df["Sector"] = v_df.index.values
        v_df.reset_index(drop=True, inplace=True)
        vs_df["Sector"] = vs_df.index.values
        vs_df.reset_index(drop=True, inplace=True)
        m_df = pd.merge(v_df, vs_df, on="Sector")
        year_df = pd.DataFrame(data=np.zeros(len(v_df["Sector"]), dtype=np.int) + year, columns=["Year"])
        m_df = pd.merge(m_df, year_df, left_index=True, right_index=True)

        if k == 0:
            merged_df = m_df
        else:
            merged_df = pd.concat([merged_df, m_df])

    if s == 0:
        flux_df = merged_df
    else:
        flux_df = pd.merge(flux_df, merged_df, how="left")

# Make DataFrame with cumulative values
cumsum_df = flux_df.cumsum()
cumsum_df["Sector"] = flux_df["Sector"]
cumsum_df["Year"] = flux_df["Year"]

total_flux = flux_df.groupby("Year").agg(lambda x: np.sqrt(np.sum(x ** 2)) if "sigma" in x else np.sum(x))

import seaborn as sns

colors = sns.cubehelix_palette(8, start=0.5, rot=-0.75).as_hex()

for mvar in ["m-dot"]:

    mvar_sigma = mvar + "_sigma"

    fig = plt.figure()
    ax = fig.add_subplot(111)
    for sector in range(8):
        df = cumsum_df[cumsum_df["Sector"] == sector]
        ax.fill_between(
            df["Year"],
            df[mvar] - df[mvar_sigma],
            df[mvar] + df[mvar_sigma],
            color=colors[sector],
            alpha=0.1,
            linewidth=0.25,
        )
        ax.plot(df["Year"], df[mvar], color=colors[sector], linewidth=0.5)
        fig.savefig("promice-{}.pdf".format(mvar), bbox_inches="tight")

for mvar in ["m-dot"]:

    mvar_sigma = mvar + "_sigma"

    fig = plt.figure()
    ax = fig.add_subplot(111)
    for sector in range(8):
        df = cumsum_df[cumsum_df["Sector"] == sector]
        df = flux_df[cumsum_df["Sector"] == sector]
        ax.errorbar(df["Year"], df[mvar], yerr=df[mvar_sigma], color=colors[sector], linewidth=0.5, fmt="o")
        fig.savefig("promice-{}.pdf".format(mvar), bbox_inches="tight")

for mvar in ["m-dot"]:

    mvar_sigma = mvar + "_sigma"

    fig = plt.figure()
    ax = fig.add_subplot(111)
    df = cumsum_df.groupby(["Sector", "Year"]).sum()
    ax.plot(df["Year"], df[mvar], color=colors[sector], linewidth=0.5)
    fig.savefig("promice-{}.pdf".format(mvar), bbox_inches="tight")


for mvar in ["m-dot"]:

    mvar_sigma = mvar + "_sigma"
    sns.barplot
    fig.savefig("promice-{}.pdf".format(mvar), bbox_inches="tight")
