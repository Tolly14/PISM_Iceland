#!/usr/bin/env python

# Copyright (C) 2011-2012 Andy Aschwanden

from argparse import ArgumentParser
from dateutil.rrule import *
from datetime import *
from dateutil.parser import parse
from dateutil.relativedelta import *
import numpy as np

import netCDF4 as netCDF
NC = netCDF.Dataset
from netcdftime import utime

# Set up the option parser
parser = ArgumentParser()
parser.description = "Script adds time bounds to time axis"
parser.add_argument("FILE", nargs='*')
parser.add_argument("-i", "--in_file", dest="infile",
                    help='''Temperature file to add smb''',
                    default='climate_forcing.nc')

def copy_attributes(var_in, var_out):
    """Copy attributes from var_in to var_out. Give special treatment to
    _FillValue and coordinates.
    """

    for att in var_in.ncattrs():
        if att == '_FillValue':
            continue
        else:        
            setattr(var_out, att, getattr(var_in, att))


options = parser.parse_args()
args = options.FILE
infile = options.infile

nc = NC(infile, 'a')

time_var = nc.variables['time']

var = "climatic_mass_balance"
cmb_var = nc.createVariable(var, "double", dimensions=("time", "y", "x"))
cmb_var.units = "kg m-2 year-1"
cmb_var.mapping = "Lambert_Conformal"
cmb_var.standard_name = "land_ice_surface_mass_balance_flux"

time_units = time_var.units
time_calendar = time_var.calendar

cdftime = utime(time_units, time_calendar)
bnds_datelist = cdftime.num2date(nc.variables['time_bnds'][:])

for t, my_file in enumerate(args):
    print('Processing from {} to {} from file {}'.format(bnds_datelist[t, 0], bnds_datelist[t, 1], my_file))
    nc_in = NC(my_file, 'r')
    cmb_in = nc_in.variables['climatic_mass_balance']
    cmb_var[t, Ellipsis] = cmb_in[Ellipsis]
    nc.sync()
    nc_in.close()

nc.close()
