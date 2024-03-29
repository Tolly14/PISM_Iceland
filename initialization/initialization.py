#!/usr/bin/env python3
# Copyright (C) 2016-21 Andy Aschwanden

import itertools
from collections import OrderedDict
import numpy as np
import os
import sys
import shlex
from os.path import join, abspath, realpath, dirname
import pandas as pd

try:
    import subprocess32 as sub
except:
    import subprocess as sub

from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
import sys

from typing import Any, Dict, List, Union

import pandas as pd
import xarray as xr

def current_script_directory():
    import inspect

    filename = inspect.stack(0)[0][1]
    return realpath(dirname(filename))


script_directory = current_script_directory()

sys.path.append(join(script_directory, "../resources"))
from resources import *


def map_dict(val, mdict):
    try:
        return mdict[val]
    except:
        return val


grid_choices = (500, 1000, 2000, 4000)
# set up the option parser
parser = ArgumentParser(formatter_class=ArgumentDefaultsHelpFormatter)
parser.description = "Generating scripts for model initialization."
parser.add_argument(
    "-i", "--initial_state_file", dest="initialstatefile", help="Input file to restart from", default=None
)
parser.add_argument(
    "-n", "--n_procs", dest="n", type=int, help="""number of cores/processors. default=4.""", default=4
)
parser.add_argument(
    "-w", "--wall_time", dest="walltime", help="""walltime. default: 100:00:00.""", default="100:00:00"
)
parser.add_argument(
    "-q", "--queue", dest="queue", choices=list_queues(), help="""queue. default=long.""", default="long"
)
parser.add_argument(
    "-d",
    "--domain",
    dest="domain",
    choices=["iceland", "vatnajoekull"],
    help="sets the modeling domain",
    default="iceland",
)
parser.add_argument("--exstep", dest="exstep", help="Writing interval for spatial time series", default=1)
parser.add_argument(
    "-f",
    "--o_format",
    dest="oformat",
    choices=["netcdf3", "netcdf4_parallel", "netcdf4_serial", "pnetcdf"],
    help="output format",
    default="netcdf3",
)
parser.add_argument(
    "-g", "--grid", dest="grid", type=int, choices=grid_choices, help="horizontal grid resolution", default=500
)
parser.add_argument("--i_dir", dest="input_dir", help="input directory", default=abspath(join(script_directory, "..")))
parser.add_argument("--o_dir", dest="output_dir", help="output directory", default="test_dir")
parser.add_argument(
    "--o_size",
    dest="osize",
    choices=["small", "medium", "big", "big_2d", "custom"],
    help="output size type",
    default="custom",
)
parser.add_argument(
    "-s",
    "--system",
    dest="system",
    choices=list_systems(),
    help="computer system to use.",
    default="pleiades_broadwell",
)
parser.add_argument(
    "--spatial_ts", dest="spatial_ts", choices=["basic", "pdd"], help="output size type", default="basic"
)
parser.add_argument(
    "--hydrology",
    dest="hydrology",
    choices=["null", "diffuse", "routing"],
    help="Basal hydrology model.",
    default="diffuse",
)
parser.add_argument(
    "--stable_gl",
    dest="float_kill_calve_near_grounding_line",
    action="store_false",
    help="Stable grounding line",
    default=True,
)
parser.add_argument(
    "--stress_balance",
    dest="stress_balance",
    choices=["sia", "ssa+sia", "ssa", "blatter"],
    help="stress balance solver",
    default="ssa+sia",
)
parser.add_argument("--start_year", dest="start_year", type=int, help="Simulation start year", default=0)
parser.add_argument("--duration", dest="duration", type=int, help="Years to simulate", default=100)
parser.add_argument("--step", dest="step", type=int, help="Step in years for restarting", default=100)
parser.add_argument(
    "-e",
    "--ensemble_file",
    dest="ensemble_file",
    help="File that has all combinations for ensemble study",
    default="../uncertainty_quantification/ctrl.csv",
)

options = parser.parse_args()

nn = options.n
input_dir = abspath(options.input_dir)
output_dir = abspath(options.output_dir)

oformat = options.oformat
osize = options.osize
queue = options.queue
walltime = options.walltime
system = options.system

spatial_ts = options.spatial_ts

exstep = options.exstep
initialstatefile = options.initialstatefile
grid = options.grid
hydrology = options.hydrology
stress_balance = options.stress_balance

ensemble_file = options.ensemble_file

domain = options.domain
pism_exec = generate_domain(domain)


print(domain)
if domain.lower() in ("iceland", "vatnajoekull"):
    pism_dataname = f"$input_dir/data_sets/bed_dem/pism_g{grid}m_Iceland_2010.nc"
else:
    print("Domain {} not recognized".format(domain))

regridvars = "litho_temp,enthalpy,age,tillwat,bmelt,ice_area_specific_volume,thk"

dirs = {"output": "$output_dir"}
for d in ["performance", "state", "scalar", "spatial", "jobs", "basins"]:
    dirs[d] = "$output_dir/{dir}".format(dir=d)

if spatial_ts == "none":
    del dirs["spatial"]

# use the actual path of the run scripts directory (we need it now and
# not during the simulation)
scripts_dir = join(output_dir, "run_scripts")
if not os.path.isdir(scripts_dir):
    os.makedirs(scripts_dir)

# generate the config file *after* creating the output directory
pism_config = "pism"
pism_config_nc = join(output_dir, pism_config + ".nc")

cmd = "ncgen -o {output} {input_dir}/config/{config}.cdl".format(
    output=pism_config_nc, input_dir=input_dir, config=pism_config
)
sub.call(shlex.split(cmd))

# these Bash commands are added to the beginning of the run scrips
run_header = """# stop if a variable is not defined
set -u
# stop on errors
set -e

# path to the config file
config="{config}"
# path to the input directory (input data sets are contained in this directory)
input_dir="{input_dir}"
# output directory
output_dir="{output_dir}"
# create required output directories
for each in {dirs};
do
  mkdir -p $each
done

""".format(
    input_dir=input_dir,
    output_dir=output_dir,
    config=pism_config_nc,
    dirs=" ".join(list(dirs.values())),
)

master_config_file = get_path_to_config()


# ########################################################
# set up model initialization
# ########################################################

uq_df = pd.read_csv(ensemble_file)
uq_df.fillna(False, inplace=True)

tsstep = "monthly"

scripts = []
scripts_combinded = []
scripts_post = []

start = options.start_year
end = options.start_year + options.duration


batch_header, batch_system = make_batch_header(system, nn, walltime, queue)
post_header = make_batch_post_header(system)

for n, row in enumerate(uq_df.iterrows()):
    print(row)
    combination = row[1]

    run_id = combination["id"]
    name_options = {}
    try:
        name_options["id"] = "{:d}".format(int(run_id))
    except:
        name_options["id"] = "{}".format(str(run_id))

    full_exp_name = "_".join(["_".join(["_".join([k, str(v)]) for k, v in list(name_options.items())])])
    full_outfile = "{domain}_g{grid}m_{experiment}.nc".format(domain=domain.lower, grid=grid, experiment=full_exp_name)

    # All runs in one script file for coarse grids that fit into max walltime
    script = join(scripts_dir, "run_g{}m_{}_j.sh".format(grid, full_exp_name))
    with open(script, "w") as f:

        experiment = "_".join(
            [
                "_".join(["_".join([k, str(v)]) for k, v in list(name_options.items())]),
                "{}".format(start),
                "{}".format(end),
            ]
        )

        for filename in script:
            try:
                os.remove(filename)
            except OSError:
                pass


        f.write(batch_header)
        f.write(run_header)

        outfile = "{domain}_g{grid}m_{experiment}.nc".format(
            domain=domain.lower(), grid=grid, experiment=experiment
        )

        pism = generate_prefix_str(pism_exec)

        general_params_dict = {
            "ys": start,
            "ye": end,
            "calendar": "365_day",
            "o": join(dirs["state"], outfile),
            "o_format": oformat,
            "config_override": "$config",
            "stress_balance.blatter.coarsening_factor": 4,
            "blatter_Mz": 17,
            "bp_ksp_type": "gmres",
            "bp_pc_type": "mg",
            "bp_pc_mg_levels": 3,
            "bp_mg_levels_ksp_type": "richardson",
            "bp_mg_levels_pc_type": "sor",
            "bp_mg_coarse_ksp_type": "gmres",
            "bp_mg_coarse_pc_type": "bjacobi",
            "bp_snes_monitor_ratio": "",
            "bp_ksp_monitor" : "",
            "bp_ksp_view_singularvalues": "", 
            "bp_snes_ksp_ew": 1,
            "bp_snes_ksp_ew_version": 3,
            "stress_balance.ice_free_thickness_standard": 5,
        }

        if initialstatefile is None:
            general_params_dict["bootstrap"] = ""
            general_params_dict["i"] = pism_dataname
        else:
            general_params_dict["bootstrap"] = ""
            general_params_dict["i"] = pism_dataname
            general_params_dict["regrid_file"] = initialstatefile
            general_params_dict["regrid_vars"] = regridvars

        if osize != "custom":
            general_params_dict["o_size"] = osize
        else:
            general_params_dict["output.sizes.medium"] = "sftgif,velsurf_mag,usurf,mask,uvelsurf,vvelsurf"

        grid_params_dict = generate_grid_description(grid, domain)


        sb_params_dict: Dict[str, Union[str, int, float]] = {
            "stress_balance.sia.flow_law": "isothermal_glen",
            "stress_balance.ssa.flow_law": "isothermal_glen",
            "stress_balance.blatter.flow_law": "isothermal_glen",
            "stress_balance.sia.Glen_exponent": combination["sia_n"],
            "stress_balance.blatter.Glen_exponent": combination["sia_n"],
            "flow_law.isothermal_Glen.ice_softness": combination["a_glen"],
            "basal_resistance.pseudo_plastic.q": combination["pseudo_plastic_q"],
            "basal_yield_stress.mohr_coulomb.topg_to_phi.enabled": "yes",
            "basal_yield_stress.mohr_coulomb.till_effective_fraction_overburden": combination["till_effective_fraction_overburden"],
            }
        phi_min = combination["phi_min"]
        phi_max = combination["phi_max"]
        z_min = combination["z_min"]
        z_max = combination["z_max"]

        sb_params_dict[
            "basal_yield_stress.mohr_coulomb.topg_to_phi.phi_max"
        ] = phi_max
        sb_params_dict[
            "basal_yield_stress.mohr_coulomb.topg_to_phi.phi_min"
        ] = phi_min
        sb_params_dict[
            "basal_yield_stress.mohr_coulomb.topg_to_phi.topg_max"
        ] = z_max
        sb_params_dict[
            "basal_yield_stress.mohr_coulomb.topg_to_phi.topg_min"
        ] = z_min

        stress_balance_params_dict = generate_stress_balance(stress_balance, sb_params_dict)

        climate_file = combination["climate_file"]
        climate_parameters = {"surface_given_file": f"""../data_sets/climate_forcing/{climate_file}""",
                              "surface.force_to_thickness.file": pism_dataname}

        climate = combination["climate"]
        climate_params_dict = generate_climate(climate, **climate_parameters)

        hydro_params_dict = generate_hydrology(hydrology)

        calving_params_dict = {"calving": "float_kill", "front_retreat_file": pism_dataname}

        scalar_ts_dict = generate_scalar_ts(
            outfile, tsstep, start=start, end=end, odir=dirs["scalar"]
        )

        all_params_dict = merge_dicts(
            general_params_dict,
            grid_params_dict,
            stress_balance_params_dict,
            climate_params_dict,
            hydro_params_dict,
            calving_params_dict,
            scalar_ts_dict,
        )

        if not spatial_ts == "none":
            exvars = spatial_ts_vars[spatial_ts]
            spatial_ts_dict = generate_spatial_ts(outfile, exvars, exstep, odir=dirs["spatial"], split=False)
            all_params_dict = merge_dicts(all_params_dict, spatial_ts_dict)
            
        print("\nChecking parameters")
        print("------------------------------------------------------------")
        with xr.open_dataset(master_config_file) as ds:
            for key in all_params_dict:
                if hasattr(ds["pism_config"], key) is False:
                    print(f"  - {key} not found in pism_config")
        print("------------------------------------------------------------\n")

        all_params = " \\\n  ".join(["-{} {}".format(k, v) for k, v in list(all_params_dict.items())])

        if system == "debug":
            redirect = " 2>&1 | tee {jobs}/job"
        else:
            redirect = " > {jobs}/job.${job_id} 2>&1"

        template = "{mpido} {pism} {params}" + redirect

        context = merge_dicts(batch_system, dirs, {"pism": pism, "params": all_params})
        cmd = template.format(**context)

        f.write(cmd)
        f.write("\n")
        f.write(batch_system.get("footer", ""))


    scripts.append(script)


scripts = uniquify_list(scripts)
scripts_combinded = uniquify_list(scripts_combinded)
print("\n".join([script for script in scripts]))
print("\nwritten\n")
print("\n".join([script for script in scripts_combinded]))
print("\nwritten\n")
