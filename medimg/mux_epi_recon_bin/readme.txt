This is a compiled version of our multiband (mux) reconstructiuon package (available in a private github repo). To run it, you will need to install the R2013b (i.e., version 8.2) Matlab run-time (MCR), available for free download from the Mathworks site:

  http://www.mathworks.com/products/compiler/mcr/index.html

We suggest that you install teh MCR in the mux_epi_recon_bin directory (the same directory that contains the run_muxrecon.sh script) in a directory call 'lib'. E.g., here's what it looks like on our systems:

  $ ls mux_epi_recon_bin/
    lib  muxrecon  readme.txt  run_muxrecon.sh
  $ ls mux_epi_recon_bin/lib/
    appdata  bin  etc  extern  help  java  license.txt  mcr  MCR_license.txt  patents.txt  polyspace  resources  rtw  runtime  simulink  sys  toolbox  trademarks.txt  X11

To run the shell script that starts the recon, cd into the mux_epi_recon_bin directory and type
 
  ./run_muxrecon.sh ./lib <argument_list>

at Linux or Mac command prompt. <argument_list> is all the arguments you want to pass to the recon:

  ./run_muxrecon.sh ./lib [pfile] [outfile] [ext_cal] [slice] [n_vcoils] [recon_method]
  
  pfile       - Filename of the pfile, or the directory containing a pfile.
  outfile     - The file for saving the results.
  ext_cal     - External calibration pfile name (either mux>1 or mux=1). Leave empty for internally calibrated scans.
  slices      - Indices of the (muxed) slices to reconstruct. Default: All slices.
  n_vcoils    - Number of virtual coils for coil compression. Set to 0 for no coil compression.
  recon_method- '1Dgrappa' or numbers other than 1: use 1D-GRAPPA;
                'sense' or number 1: use SENSE;
                'slice-grappa': use slice-GRAPPA;
                'split-slice-grappa': use split-slice-GRAPPA.
                Append '_sense1' to use sense coil combination. E.g., '1Dgrappa_sense1'.

For example, to recon all slices for an internally-calibrated scan using 1D GRAPPA with SENSE coil combination (the recommended recon, especially for diffusion scans) and 16 virtual coils:

  ./run_muxrecon.sh ./lib /path/to/P01024.7 /path/to/outfile '' '' 16 1Dgrappa_sense1

Note that this reconstruction saves the resulting images in Matlab '.mat' files. To generate NIFTI files (and also allow parallelization of the recon), use nimsdata (https://github.com/cni/nimsdata/nimsdata.py). E.g.:

  ./nimsdata.py -i -p pfile -w nifti --parser_kwarg="num_jobs=4" --parser_kwarg="num_virtual_coils=16" --parser_kwarg="recon_type=1Dgrappa_sense1" /path/to/P01024.7 /path/to/outfile
  
Note that num_jobs is the number of slices to reconstruct in parallel. For diffusion scans, you can usually set this to the number of cores that you have (e.g., 4 for a quad-core system). The fMRI data, the number of parallel jobs you can do will probably limited by how much RAM you have.
