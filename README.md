# This is the Rambody repository

Rambody is the coupling of two legacy astrophysics open-source codes : [RAMSES](https://bitbucket.org/rteyssie/ramses/) and [Nbody6++](https://github.com/nbody6ppgpu/Nbody6PPGPU-beijing).

This coupling allows the resolution of collisional systems such as globular-clusters in collisionless environment such as giant molecular clouds, galaxies or cosmological environment.

*This code is a work in progress.*.

# License

All the original parts of both codes are subject to their own licenses. All modifications of the codes for Rambody are to be taken as compliant with their original licenses.

# Usage

## Cloning the repository

The Rambody repository relies on two submodules defined in separate repositories which are the modified version of the two original codes. To start, clone the Rambody repository enabling submodules :

```
git clone --recurse-submodules git@github.com:mdelorme/rambody.git .
```

## Compiling the codes

You need then to build both codes. Please refer to the respective repo to have all the details on the compilation of the codes.

For Nbody6++, your build step should look like :

```
cd nbody6_rambody
./configure --enable-gpu --disable-openmp --enable-simd=no
make -j 4
```

Which should generate a `nbody6++.gpu.mpi` executable in the `build` folder

For RAMSES

```
cd ramses_rambody/bin
make
```

(Do not activate multi-threaded build as the compilation will fail)

Please note that by default, RAMSES' makefile should be edited to enable 3d, and all the correct parameters.
Buiding the code should create a `ramses3d` executable in the `bin` folder.

## Making the links to the executables

To make the code more resilient, Rambody relies on having two symbolic links created in the `bin` folder :

```
cd bin
ln -s ../ramses_rambody/bin/ramses3d ramses3d
ln -s ../nbody6_rambody/build/nbody6++.gpu.mpi nbody6++
```

Note that if you have enabled a different set of configuration options, your `nbody6++` executable might have a different name.

## Running the code

Once both codes have been compiled and symbolic links have been created, you can run a test-run from the `example_runs` folder :

```
./run_pm.sh
```

Please note that the number of MPI processes attributed to both ramses and nbody6 can be changed. As a rule of thumb, on a single node with N cores and M GPUs, the distribution should be : M processes for Nbody6, N-M processes for RAMSES.


## Parametrizing the run

Defining a run for Rambody is (almost) simple. First you have to define a Nbody6 and a Ramses "standard" run as you would normally do when separating them.
The Nbody6 parameter file will not change from the original version.
The Ramses namelist has now a new section :

```
&RBD_PARAMS
rambody=.true.
rbdpartmax=50001
sync_method='coarse_dt'
rbd_xc0=3.086e22, 0.0, 0.0
rbd_vc0=0.0, 6555006, 0.0
refine_on_rambody=.false.
rbd_mesh_Nx=5
rbd_nbody6_force=.false.
max_nb6_steps=1
rbd_limit_dt=.false.
rbd_max_rms_dt=0.0
rbd_store_escapers=.true.
rbd_epsilon=1.0e-3
rbd_restart=.false.
/
```

The new parameters are the following: 
 * `rambody`: indicates if we should use rambody or if the ramses run is without the coupling
 * `rbdpartmax` indicates the maximum number of particles associated with the rambody force mesh
 * `sync_method` indicates which type of synchronization between both code is used. For now, only `coarse_dt` is usable.
 * `rbd_xc0` initial position of the guiding center of the cluster, in CGS before centering of the data (so this would indicate a GC at 10kpc from the center of the box)
 * `rbd_vx0` initial velocity of the cluster in the frame of reference of Ramses, in CGS
 * `refine_on_rambody` should Ramses refine the grid around the cluster
 * `rbd_mesh_Nx` number of points along each direction in the Rambody force mesh
 * `rbd_nbody6_force` should gravitational potential of the cluster be also applying a force on the gas
 * `max_nb6_steps` maximum number of nbody6 steps between two syncs. This is used to prevent Ramses from moving the guiding center too far between two updates
 * `rbd_limit_dt` should we limit the maximum ramses timestep to a fixed value
 * `rbd_max_rms` maximum value of dt when `rbd_limit_dt` is set to `.true.`
 * `rbd_store_escapers` should Nbody6 escaping stars be reinjected in Ramses as tracer particles
 * `rbd_epsilon` smoothing length for the interpolation on the grid in Nbody6++
 * `rbd_restart` shoudl be `.true.` if the run is restarting a previous Rambody run (but `.false.` if the run is restarting from a previous pure Ramses run)