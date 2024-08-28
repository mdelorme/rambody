from rambody_reader import *
import os, sys
import numpy as np
import matplotlib.pyplot as plt


if len(sys.argv) < 2:
    print('USAGE : python3 {} PATH'.format(sys.argv[0]))
    exit(1)

# Path to the data files
path = sys.argv[1]

# Extracting outputs
output_files = []
for f in os.listdir(path):
    if f.startswith('output_'):
        output_files.append(os.path.join(path, f))
output_files.sort()

positions = []
for f in output_files:
    print('Reading snapshot :', f)
    snap = RambodyFile(f, load_mesh=False)
    # Extracting only x and y coordinates of the guiding center of the cluster
    positions.append((snap.xc[0], snap.xc[1]))

positions=np.array(positions)

fig = plt.figure(figsize=(10, 10))
ax  = fig.add_subplot(111)
ax.plot(positions[:,0], positions[:,1], '-+r')

ax.set_xlim(59, 101)
ax.set_ylim(-1, 41)
ax.set_title('Trajectoire de l\'amas globulaire \nen orbite autour de la galaxie')
ax.set_xlabel('x [pc]')
ax.set_ylabel('y [pc]')
plt.show()
    
