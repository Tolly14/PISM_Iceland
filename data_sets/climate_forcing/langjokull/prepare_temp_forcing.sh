#!/bin/bash
set -x -e 

cdo yearmean -seldate,1997-1-1,2015-1-1 -shifttime,-1days t2m_daily_dlr_iceland.nc t2m_iceland_ymean_1997-1-1_2015-1-1.nc

