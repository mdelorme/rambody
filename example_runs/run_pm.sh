#!/bin/bash

# These should point to the symbolic links in your bin folder
RBD_DIR=../bin
NB6_BIN=$RBD_DIR/nbody6++
RMS_BIN=$RBD_DIR/ramses3d

# These are the names of the parameter files
NB6_PRM=cluster.nml
RMS_PRM=retro.nml

# The number of MPI processes for Nbody6 (1 per GPU), and for Ramses (1 per core left)
export NB6_PROCS=1
export RAMSES_PROCS=1

###### Open MPI Run
export LOG_DIR=./logs
echo "Running rambody. Logs can be found in ${LOG_DIR}"
echo "mpirun --output-filename ${LOG_DIR} -quiet -np ${NB6_PROCS} ${NB6_BIN} ${NB6_PRM} : -np ${RAMSES_PROCS} ${RMS_BIN} ${RMS_PRM} > /dev/null 2> /dev/null"
mpirun --output-filename ${LOG_DIR} -quiet -np ${NB6_PROCS} ${NB6_BIN} ${NB6_PRM} : -np ${RAMSES_PROCS} ${RMS_BIN} ${RMS_PRM} > /dev/null 2> /dev/null
echo "All done !"
