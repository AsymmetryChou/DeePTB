## Usage 
1. run NEGF calculation:
```shell
$ dptb negf  -i input.json  --struct struct.xyz -fmt xyz --nn_off true
```
**Note**: here i used the  multiprocessing to accelerate the calculation. 
     but in order to avoid the competition between the openmp and multiprocessing, 
     you'd better set the OMP_NUM_THREADS to be a smaller number.

or use the `ase api` to calculate NEGF
```shell
$ dptb negf  -i input.json --struct struct.xyz -fmt xyz --nn_off true --use_ase true
```

1. plot  transmission coefficient  T(E) and current  I-V curve.
```shell
$ python3 plot.py
```

## Device structure format:
```shell
...  | H H |  H H  |  H H H H  |  H H  | H H | ...
...  | | | |  | |  |  | | | |  |  | |  | | | | ...
...  | C-C |  C-C- |  C-C-C-C- |  C-C- | C-C | ...
...  | | | |  | |  |  | | | |  |  | |  | | | | ...
...  | C-C |  C-C- |  C-C-C-C- |  C-C- | C-C | ...
...  | .   |  .    |    .   .  |    .  |   . | ...
...  | .   |  .    |    .   .  |    .  |   . | ...
...  | .   |  .    |    .   .  |    .  |   . | ...
...  | C-C |  C-C- |  C-C-C-C- |  C-C- | C-C | ...
...  | | | |  | |  |  | | | |  |  | |  | | | | ...
...  | H H |  H H  |  H H H H  |  H H  | H H | ...
     |     |       |           |       |     | ...
...  | PL2 |  PL1  |           |  PL1  | PL2 | ...  
...  |     |       |           |       |     | ... 
...  |    Contact  |  Scatter  |   Contact   | ...  
...  |    Source   |           |   Drain     | ...    
```
### Description of the structure :
1. The device structure is desined in the above fromat. in the center lies the **scatter** region, or center region. On the two ends, there are two semi-infinite contacts named **source** and **drain**. 
2. The contact will be used to calculate the surface green's function which involves the iterative procedure, where the principal layer (PL) is defined. There are two PLs given in the device structure for each contact. The PL2 is nothing but a replica of PL1, with PL2 = PL1 + R . R is the translation vector.
3. The choice of PL should be integer times unit cell of the material, and makes the coupling only involves the adjective  between different adjacent layers. e.g. the couple of PL1 and PL3  is 0.
4. The file format for the struct used here is **xyz** or **extxyz**. xyz is for non-periodic system extxyz is for periodic system. here, periodic means the along the direction perpendicular to the transport direction.
5. The coordinates of the atoms in the devices should be arranged as : 
   - atoms of scatter, 
   - atoms of contact1's PL1, 
   - atoms of contact1's PL2,
   - atoms of contact2's PL1,
   - atoms of contact2's PL2.