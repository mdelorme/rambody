import numpy as np
from scipy.io import FortranFile
import os
import os.path

try:
    import pynbody
    pynbody_available = True
except:
    print('WARNING : Cannot load pynbody, some functionalities might not be available')
    print('          Consider installing it : pip3 install pynbody --user')
    pynbody_available = False

### Warnings and Errors
warning_is_rambody = '''WARNING : Filename does not seem to be starting with "output_". 
Are you sure you are opening a Ramses output ?'''
error_snap_folder = '''Path provided for snapshot does not exists : {}'''
error_rbd_file = '''File path does not exists ({}). Are you sure this is a Rambody run ?'''

class RamsesHeader(object):
    def __init__(self, path, snap_id):
        ''' Class for reading a Ramses header '''
        s2Myr = 3.168808781402895e-14

        self.snap_id = snap_id
        self.path = path
        
        filename = os.path.join(path, 'info_{}.txt'.format(snap_id))
        f_in = open(filename, 'r')
        for i, line in enumerate(f_in):
            value = line[15:].strip()
            if i==0:
                self.ncpu = int(value)
            elif i==1:
                self.ndim = int(value)
            elif i==2:
                self.levelmin = int(value)
            elif i==3:
                self.levelmax = int(value)
            elif i==4:
                self.ngridmax = int(value)
            elif i==5:
                self.nstep_coarse = int(value)
            elif i==7:
                self.boxlen = float(value)
            elif i==8:
                self.time = float(value)
            elif i==9:
                self.aexp = float(value)
            elif i==10:
                self.H0 = float(value)
            elif i==11:
                self.omega_m = float(value)
            elif i==12:
                self.omega_l = float(value)
            elif i==13:
                self.omega_k = float(value)
            elif i==14:
                self.omega_b = float(value)
            elif i==15:
                self.unit_l = float(value)
            elif i==16:
                self.unit_d = float(value)
            elif i==17:
                self.unit_t = float(value)
        self.unit_m = self.unit_d / self.unit_l**3.0
        self.time = self.time * self.unit_t * s2Myr 

class RambodyFile(object):
    def __init__(self, path, load_mesh=True, load_amr=False, verbose=False):
        ''' Class for reading Rambody outputs '''

        self.verbose = verbose
        self.path    = os.path.normpath(os.path.expanduser(path))

        if not os.path.exists(self.path):
            raise FileNotFoundError(0, error_snap_folder.format(path))

        if not path.split('/')[-1].startswith('output_'):
            print(warning_is_rambody)


        self.snap_id  = self.path.split('_')[-1]

        self.header = RamsesHeader(self.path, self.snap_id)
        
        self.read_particles()

        if load_mesh:
            self.read_mesh()
        if pynbody_available:
            self.read_rms()

        if load_amr:
            self.read_amr()

    def read_amr(self):
        self.amr = {}
        filenames = []

        for f in os.listdir(self.path):
            if not f.startswith('amr_'):
                continue

            cpu_id = int(f[-5:])
            print('Reading', f)
            fn = os.path.join(self.path, f)

            f_in = FortranFile(fn, 'r')

            # Reading int lines
            for i in range(9):
                tmp = f_in.read_ints()
                if i == 0:
                    ncpu = int(tmp[0])
                elif i == 1:
                    ndim = int(tmp[0])
                elif i == 3:
                    self.levelmax = int(tmp[0])
                elif i == 5:
                    nboundary = int(tmp[0])

            # Then 5 reals
            for i in range(5):
                tmp = f_in.read_reals()

            tmp = f_in.read_ints() # nstep, nstep_coarse
            for i in range(4):
                tmp = f_in.read_reals()

            # Level variables
            headl = f_in.read_ints()
            taill = f_in.read_ints()
            numbl = f_in.read_ints().reshape((self.levelmax, ncpu))
            numbtot = f_in.read_ints()

            # Free memory
            tmp = f_in.read_ints()

            # Ordering
            tmp = f_in.read_ints()

            # Bound keys
            tmp = f_in.read_ints()

            # Coarse level
            for i in range(3):
                tmp = f_in.read_ints()

            # FINALLY !
            for i in range(self.levelmax):
                dx = 1.0 / (2**i) * 0.5
                
                # Boundaries ... WDGAF
                for j in range(nboundary+ncpu):
                    xg = [None, None, None]

                    ncache = numbl[i][j]
                    if ncache == 0:
                        continue

                    cur = (j == cpu_id)
                    tmp = f_in.read_ints() # Grid id
                    tmp = f_in.read_ints() # Grid next
                    tmp = f_in.read_ints() # Grid prev
                    for k in range(ndim):
                        gc = f_in.read_reals() # Grid center

                        # We store the upper left corner :
                        xg[k] = np.asarray(gc) - dx
                    tmp = f_in.read_ints() # Grid father
                    for k in range(6):
                        tmp = f_in.read_ints() # Neighbor
                    for k in range(8):
                        tmp = f_in.read_ints() # Son
                    for k in range(8):
                        tmp = f_in.read_ints() # CPU
                    for k in range(8):
                        tmp = f_in.read_ints() # Refinement

                    vec = np.asarray(xg)
                    if i not in self.amr:
                        self.amr[i] = vec
                    else:
                        self.amr[i] = np.concatenate((self.amr[i], vec), axis=1)
            f_in.close()


    def read_rms(self):
        self.pnb = pynbody.load(self.path)
        self.pnb['pos'] -= 0.5 * self.pnb.properties['boxsize']
        
        self.stream = {}
        self.stream['pos'] = self.pnb.tracer['pos']

    def read_particles(self):
        filename = 'rbd_' + self.snap_id + '.out'
        filepath = os.path.join(self.path, filename)

        if not os.path.exists(filepath):
            raise FileNotFoundError(1, error_rbd_file.format(filepath))

        if self.verbose:
            print('Reading particles from {}'.format(os.path.split(filepath)[-1]))

        f_in = FortranFile(filepath, 'r')

        # General info
        self.ncpu       = f_in.read_ints()[0]
        self.ndim       = f_in.read_ints()[0]
        self.nb6_npart  = f_in.read_ints()[0]
        self.mesh_scale = f_in.read_reals()[0]

        # Guiding center
        self.xc = f_in.read_reals() - self.header.boxlen*0.5
        self.vc = f_in.read_reals()
        self.gc_owner = f_in.read_ints()

        if self.verbose:
            print('Guiding center :')
            print(' - position [kpc]  = ({0[0]:.3f}, {0[1]:.3f}, {0[2]:.3f})'.format(self.xc))
            print(' - velocity [km/s] = ({0[0]:.3f}, {0[1]:.3f}, {0[2]:.3f})'.format(self.vc))
            print(' - currently on process #{}'.format(self.gc_owner[0]))

        self.nb6 = {}
        self.nb6['gpos']  = np.zeros((self.nb6_npart, 3)) 
        self.nb6['vel']  = np.zeros((self.nb6_npart, 3))
        self.nb6['mass'] = np.zeros((self.nb6_npart,))

        for i in range(3):
            self.nb6['gpos'][:,i] = f_in.read_reals() - self.header.boxlen*0.5
            
        for i in range(3):
            self.nb6['vel'][:,i] = f_in.read_reals()

        self.nb6['mass'] = f_in.read_reals()
        self.nb6['cpos'] = self.nb6['gpos'] - self.xc
        self.nb6['rc']   = np.linalg.norm(self.nb6['cpos'], axis=1)

        if self.verbose:
            print('Cluster statistics :')
            print(' - N bound = ', self.nb6_npart)
            print(' - Avg mass = {} Msun'.format(np.mean(self.nb6['mass']))) # In RMS units ...
            print(' - Avg rc = {}'.format(np.mean(self.nb6['rc'])))
            print(' - Std rc = {}'.format(np.std(self.nb6['rc'])))

    def read_mesh(self):
        filename = 'rbd_mesh_' + self.snap_id + '.out'
        filepath = os.path.join(self.path, filename)

        if not os.path.exists(filepath):
            raise FileNotFoundError(1, error_rbd_file.format(filepath))

        if self.verbose:
            print('Reading mesh from {}'.format(os.path.split(filepath)[-1]))
            
        f_in = FortranFile(filepath, 'r')
        
        # No need to read the guiding center info, we already have it
        tmp = f_in.read_reals()
        tmp = f_in.read_reals()
        tmp = f_in.read_ints()

        # Reading mesh size
        mdim = f_in.read_ints()
        self.n_mesh_points = mdim[0]
        self.n_mesh_Nx     = mdim[1]

        self.mesh = {}
        self.mesh['pos'] = np.zeros((self.n_mesh_points, 3))
        self.mesh['F']   = np.zeros((self.n_mesh_points, 3))
        
        for i in range(3):
            self.mesh['pos'][:,i] = f_in.read_reals() - self.xc[i] - self.header.boxlen*0.5

        for i in range(3):
            self.mesh['F'][:,i] = f_in.read_reals()

        if self.verbose:
            print('Mesh statistics : ')
            print(' - N = {} ({}^3+1)'.format(self.n_mesh_points, self.n_mesh_Nx))
            
        

if __name__ == '__main__':
    f = RambodyFile('../../eriII/core_100k/output_00001', True)

    import matplotlib.patches as patches
    import matplotlib.pyplot as plt

    levelmin = 4
    levelmax = 6
    bl = f.header.boxlen

    fig = plt.figure(figsize=(10, 10))
    ax = fig.add_subplot(111)

    margin = 0.1 * bl
    ax.set_xlim = (0.0, bl)
    ax.set_ylim = (0.0, bl)

    for i in range(levelmin, levelmax+1):
        print('Drawing level {} with {} cells'.format(i, f.amr[i].shape[1]))
        dx = 1.0 / 2.0**i

        Nc = f.amr[i].shape[1]
        counter = 5000
        k = 0
        for j in range(Nc):
            if counter == 0:
                counter = 5000
                k += 1
                print(' {}/{}'.format(k*5000, Nc))
            counter -= 1
            x, y, z = f.amr[i].T[j]
            r = patches.Rectangle((x, y), dx, dx, linewidth=1, edgecolor='r',facecolor='none')
            ax.add_patch(r)
    plt.show()
        
