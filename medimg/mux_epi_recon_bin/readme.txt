This is a compiled version of our multiband (mux) reconstructiuon package (available in a private github repo). To run it, you will need to install the R2013b (i.e., version 8.2) Matlab run-time (MCR), available for free download from the Mathworks site:

  http://www.mathworks.com/products/compiler/mcr/index.html

We suggest that you install the MCR in the mux_epi_recon_bin directory (the same directory that contains the run_muxrecon.sh script) in a directory named 'lib'. E.g., here's what it looks like on our systems:

  $ ls mux_epi_recon_bin/
    lib  muxrecon  readme.txt  run_muxrecon.sh
  $ ls mux_epi_recon_bin/lib/
    appdata  bin  etc  extern  help  java  license.txt  mcr  MCR_license.txt  patents.txt  polyspace  resources  rtw  runtime  simulink  sys  toolbox  trademarks.txt  X11

To run the shell script that starts the recon, cd into the mux_epi_recon_bin directory and type
 
  ./run_muxrecon.sh ./lib [pfile] [outfile] [ext_cal] [slice] [n_vcoils] [recon_method]

at a Linux or Mac command prompt. The arguments are as follows:
  
  pfile       - Filename of the pfile. Note that the ref.dat and vrgf.dat files must be in the same directory as the pfile, and there should only be one of each in there. (I.e., keep each p-file and its associated files in a directory separate from other p-files.)
  outfile     - The file for saving the results. (This will be a Matlab 'mat' file.)
  ext_cal     - External calibration pfile. Leave empty for internally calibrated scans.
  slices      - Indices of the (muxed) slices to reconstruct. Leave empty to reconstruct all slices.
  n_vcoils    - Number of virtual coils for coil compression. Set to 0 for no coil compression.
  recon_method- '1Dgrappa', 'sense', 'slice-grappa', or 'split-slice-grappa'.
                Append '_sense1' to use sense coil combination. E.g., '1Dgrappa_sense1'.

For example, to recon all slices for an internally-calibrated scan using 1D GRAPPA with SENSE coil combination (the recommended recon method, especially for diffusion scans), and 16 virtual coils:

  ./run_muxrecon.sh ./lib /path/to/P01024.7 /path/to/outfile '' '' 16 1Dgrappa_sense1

Note that this reconstruction saves the resulting images in Matlab '.mat' files. To generate NIFTI files (and also allow parallelization of the recon), use nimsdata (https://github.com/cni/nimsdata/nimsdata.py). E.g.:

  ./nimsdata.py -i -p pfile -w nifti --parser_kwarg="num_jobs=4" --parser_kwarg="num_virtual_coils=16" --parser_kwarg="recon_type=1Dgrappa_sense1" /path/to/P01024.7 /path/to/outfile
  
Note that num_jobs is the number of slices to reconstruct in parallel. For diffusion scans, you can usually set this to the number of cores that you have (e.g., 4 for a quad-core system). The fMRI data, the number of parallel jobs you can do will probably limited by how much RAM you have.
