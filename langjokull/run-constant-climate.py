#!/usr/bin/env python
# Copyright (C) 2016 Andy Aschwanden

import itertools
from collections import OrderedDict
import os
try:
    import subprocess32 as sub
except:
    import subprocess as sub
from argparse import ArgumentParser
import sys
sys.path.append('../resources/')
from resources import *

grid_choices = [400, 200, 100]

# set up the option parser
parser = ArgumentParser()
parser.description = "Generating scripts for prognostic simulations."
parser.add_argument("-n", '--n_procs', dest="n", type=int,
                    help='''number of cores/processors. default=2.''', default=24)
parser.add_argument("-w", '--wall_time', dest="walltime",
                    help='''walltime. default: 12:00:00.''', default="12:00:00")
parser.add_argument("-q", '--queue', dest="queue", choices=list_queues(),
                    help='''queue. default=medium.''', default='medium')
parser.add_argument("--climate", dest="climate",
                    choices=['const', 'pdd', 'pdd_lapse', 'flux'],
                    help="Climate", default='const')
parser.add_argument("-d", "--domain", dest="domain",
                    choices=['langjokull'],
                    help="sets the modeling domain", default='langjokull')
parser.add_argument("--dem_year", dest="dem_year",
                    choices=['1937', '1945', '1986', '1997', '2004'],
                    help="Year of surface DEM", default=2004)
parser.add_argument("--duration", dest="duration",
                    help="Duration of run", default=10)
parser.add_argument("-f", "--o_format", dest="oformat",
                    choices=['netcdf3', 'netcdf4_parallel', 'pnetcdf'],
                    help="output format", default='netcdf3')
parser.add_argument("-g", "--grid", dest="grid", type=int,
                    choices=grid_choices,
                    help="horizontal grid resolution", default=100)
parser.add_argument("--o_dir", dest="odir",
                    help="output directory. Default: current directory", default='.')
parser.add_argument("--o_size", dest="osize",
                    choices=['small', 'medium', 'big'],
                    help="output size type", default='medium')
parser.add_argument("-s", "--system", dest="system",
                    choices=list_systems(),
                    help="computer system to use.", default='debug')
parser.add_argument("--stress_balance", dest="stress_balance",
                    choices=['sia', 'ssa+sia', 'ssa'],
                    help="stress balance solver", default='sia')


options = parser.parse_args()

nn = options.n
odir = options.odir
oformat = options.oformat
osize = options.osize
queue = options.queue
walltime = options.walltime
system = options.system

climate = options.climate
dem_year = options.dem_year
duration = options.duration
grid = options.grid
stress_balance = options.stress_balance

domain = options.domain
pism_exec = generate_domain(domain)

pism_dataname = 'pism_Langjokull_{year}.nc'.format(year=dem_year)
if not os.path.isdir(odir):
    os.mkdir(odir)

start = 0
end = duration

hydrology = 'null'

# ########################################################
# set up model initialization
# ########################################################

ssa_n = (3.0)
ssa_e = (1.0)

sia_e_values = [1.0, 3.0]
ppq_values = [0.50]
tefo_values = [0.020]
plastic_phi_values = [20, 30, 40]
combinations = list(itertools.product(sia_e_values, ppq_values, tefo_values, plastic_phi_values))

tsstep = 'daily'
exstep = 'yearly'

scripts = []
scripts_post = []


for n, combination in enumerate(combinations):

    sia_e, ppq, tefo, plastic_phi = combination


    name_options = OrderedDict()
    name_options['sia_e'] = sia_e
    name_options['plastic_phi'] = plastic_phi
    name_options['dem'] = dem_year
    experiment =  '_'.join([climate, '_'.join(['_'.join([k, str(v)]) for k, v in name_options.items()])])

      # full_exp_name =  '_'.join([climate, vversion, bed_type, '_'.join(['_'.join([k, str(v)]) for k, v in name_options.items()])])
    # full_outfile = '{domain}_g{grid}m_{experiment}.nc'.format(domain=domain.lower(),grid=grid, experiment=full_exp_name)
    full_outfile = ''
    full_exp_name = ''
    
    outfiles = []

    script = 'cc_{}_g{}m_{}.sh'.format(domain.lower(), grid, experiment)
    scripts.append(script)
    
    for filename in (script):
        try:
            os.remove(filename)
        except OSError:
            pass

    batch_header, batch_system = make_batch_header(system, nn, walltime, queue)
            
    with open(script, 'w') as f:

        f.write(batch_header)

        outfile = '{domain}_g{grid}m_{experiment}_{start}_{end}.nc'.format(domain=domain.lower(),
                                                                           grid=grid,
                                                                           experiment=experiment,
                                                                           start=start,
                                                                           end=end)

        prefix = generate_prefix_str(pism_exec)

        general_params_dict = OrderedDict()
        general_params_dict['i'] = pism_dataname
        general_params_dict['bootstrap'] = ''
        general_params_dict['ys'] = start
        general_params_dict['ye'] = end
        general_params_dict['o'] = os.path.join(odir, outfile)
        general_params_dict['o_format'] = oformat
        general_params_dict['o_size'] = osize
        
        grid_params_dict = generate_grid_description(grid, domain)

        sb_params_dict = OrderedDict()
        sb_params_dict['sia_e'] = sia_e
        sb_params_dict['ssa_e'] = ssa_e
        sb_params_dict['ssa_n'] = ssa_n
        sb_params_dict['pseudo_plastic_q'] = ppq
        sb_params_dict['till_effective_fraction_overburden'] = tefo
        sb_params_dict['plastic_phi'] = plastic_phi
        sb_params_dict['bed_smoother_range'] = 0.

        stress_balance_params_dict = generate_stress_balance(stress_balance, sb_params_dict)
        surface_file = 'climate_langjokull_100m_mean_1997-1-1_2015-1-1.nc'
        climate_params_dict = generate_climate(climate,
                                                   surface_given_file=surface_file,
                                               force_to_thickness_file=pism_dataname)
        ocean_params_dict = generate_ocean('const')
        hydro_params_dict = generate_hydrology(hydrology)

        exvars = default_spatial_ts_vars()
        spatial_ts_dict = generate_spatial_ts(outfile, exvars, exstep, odir=odir)
        scalar_ts_dict = generate_scalar_ts(outfile, tsstep, odir=odir)

        all_params_dict = merge_dicts(general_params_dict, grid_params_dict, stress_balance_params_dict, climate_params_dict, ocean_params_dict, hydro_params_dict, spatial_ts_dict, scalar_ts_dict)
        all_params = ' '.join([' '.join(['-' + k, str(v)]) for k, v in all_params_dict.items()])
        
        cmd = ' '.join([batch_system['mpido'], prefix, all_params, '> {odir}/job.${batch}  2>&1'.format(odir=odir, batch=batch_system['job_id'])])

        f.write(cmd)
        f.write('\n')


    script_post = 'cc_{}_g{}m_{}_post.sh'.format(domain.lower(), grid, experiment)
    scripts_post.append(script_post)

    post_header = make_batch_post_header(system)
    
    with open(script_post, 'w') as f:

        f.write(post_header)
        cmd = ' '.join(['ncpdq -O -4 -L 3 -a time,y,x,z', outfile, outfile, '\n'])
        f.write(cmd)
        extra_file = spatial_ts_dict['extra_file']
        cmd = ' '.join(['ncpdq -O -4 -L 3 -a time,y,x,z', extra_file, extra_file, '\n'])
        f.write(cmd)


scripts = uniquify_list(scripts)
scripts_post = uniquify_list(scripts_post)
print '\n'.join([script for script in scripts])
print('\nwritten\n')
print '\n'.join([script for script in scripts_post])
print('\nwritten\n')

submit = 'submit_{domain}_g{grid}m_{climate}.sh'.format(domain=domain.lower(), grid=grid, climate=climate)
try:
    os.remove(submit)
except OSError:
    pass

with open(submit, 'w') as f:

    f.write('#!/bin/bash\n')
    for k in range(len(scripts)):
        f.write('JOBID=$({batch_submit} {script})\n'.format(batch_submit=batch_system['submit'], script=scripts[k]))
