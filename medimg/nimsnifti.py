# @author:  Gunnar Schaefer
#           Bob Dougherty
#           Kevin S Hahn

"""
nimsdata.medimg.nimsnifti
=========================

NIMSNifti provide NIfti writing capabilities for MR datasets read by any subclass of NIMSMRReader.

Provides nifti specifics, inherits from NIMSMRReader, NIMSMRWriter.

"""

import os
import bson
import logging
import nibabel
import json

import numpy as np

import medimg

log = logging.getLogger(__name__)

# NIFITI1-style slice order codes:
SLICE_ORDER_UNKNOWN = 0
SLICE_ORDER_SEQ_INC = 1
SLICE_ORDER_SEQ_DEC = 2
SLICE_ORDER_ALT_INC = 3
SLICE_ORDER_ALT_DEC = 4
SLICE_ORDER_ALT_INC2 = 5  # interleave, ascending, starting at 2nd slice
SLICE_ORDER_ALT_DEC2 = 6  # interleave, decreasing, starting at 2nd to last slice


class NIMSNiftiError(medimg.MedImgError):
    pass


class NIMSNifti(medimg.MedImgReader, medimg.MedImgWriter):

    """
    Read elements of a NIMSData subclass.

    Dataset must have a 'data' attribute that contains voxel data in a np.darray. Dataset must
    also have contain metadata attributes to define nims required attributes.

    Parameters
    ----------
    path : str
        filepath of input nifti, in .nii or .nii.gz format.
    load_data : bool [default False]
        attempt to load all data. has no affect.

    Returns
    -------
    None : NoneType

    Raises
    ------
    NIMSNiftiError
        TODO: explain plz.

    """

    domain = u'mr'
    filetype = u'nifti'
    state = ['orig']

    def __init__(self, path, load_data=False):
        super(NIMSNifti, self).__init__(path, load_data)
        log.debug('reading %s' % path)
        try:
            # TODO: load sorting/identification header
            self.nifti = nibabel.load(path)
        except Exception as e:
            raise NIMSNiftiError(e)

        # TODO: read metadata from nifti extension header

        if load_data:
            self.load_data()

    def load_data(self):
        super(NIMSNifti, self).load_data()
        log.debug('loading data...')
        self.data = {'': self.nifti.get_data()}
        self.qto_xyz = self.nifti.get_affine()
        self.sform = self.nifti.get_sform()
        self.qform = self.nifti.get_qform()
        self.scan_type = 'unknown'   # FIXME

    @property
    def nims_group(self):
        return self.metadata.group

    @property
    def nims_project(self):
        return self.metadata.project

    @property
    def nims_session(self):
        return self.metadata.exam_uid.replace('.', '_')

    @property
    def nims_session_name(self):
        return self.metadata.timestamp.strftime('%Y-%m-%d %H:%M') if self.metadata.series_no == 1 and self.metadata.acq_no == 1 else None

    @property
    def nims_session_subject(self):
        return self.metadata.subj_code

    @property
    def nims_acquisition(self):
        return self.metadata.acquisition

    @property
    def nims_acquisition_name(self):
        pass

    @property
    def nims_acquisition_description(self):
        pass

    @property
    def nims_file_name(self):
        return self.nims_acquisition + '_' + self.filetype

    @property
    def nims_file_ext(self):
        return '.tgz'

    @property
    def nims_file_domain(self):
        return self.domain

    @property
    def nims_file_type(self):
        return self.filetype

    @property
    def nims_file_kinds(self):
        return self.scan_type

    @property
    def nims_file_state(self):
        return self.state

    @property
    def nims_timestamp(self):  # FIXME: should return UTC time and timezone
        return self.timestamp.replace(tzinfo=bson.tz_util.FixedOffset(-7 * 60, 'pacific'))  # FIXME: use pytz

    @property
    def nims_timezone(self):
        return None

    @classmethod
    def write(cls, metadata, imagedata, outbase, voxel_order=None):
        """
        Write the metadata and imagedata to niftis.

        Constructs a description from the metadata, and applies as much metadata into the nifti
        header as is applicable.  Creates .bvec and .bval files if bvecs and bvals exist.

        Parameters
        ----------
        metadata : object
            fully loaded instance of a NIMSReader.
        imagedata : dict or string containing a path to a dir containing nifti(s)
            dictionary of np.darrays. label suffix as keys, with np.darrays as values.
        outbase : str
            output name prefix.
        voxel_order : str [default None]
            three character string indicating the voxel order, ex. 'LPS'.

        Returns
        -------
        results : list
            list of files written.

        Raises
        ------
        NIMSDataError
            metadata or data is None.

        """
        if isinstance(imagedata, basestring):
            from glob import glob
            from shutil import copyfile
            # imagedata is a directory containing nifti(s)
            log.info('Loading files from %s' % imagedata)
            niftis = glob(imagedata + '/' + str(metadata.exam_no) + '_' + str(metadata.series_no) + '_' + str(metadata.acq_no) + '*.nii.gz')
            results = []
            for f in niftis:
                filepath = os.path.join(os.path.dirname(outbase), os.path.basename(f))
                copyfile(f, filepath)
                results.append(filepath)
        else:
            super(NIMSNifti, cls).write(metadata, imagedata, outbase, voxel_order)  # XXX FAIL! unexpected imagedata = None
            results = []
            for data_label, data in imagedata.iteritems():
                if data is None:
                    continue
                if voxel_order:
                    data, qto_xyz = cls.reorder_voxels(data, metadata.qto_xyz, voxel_order)
                else:
                    qto_xyz = metadata.qto_xyz
                outname = outbase + data_label

                log.debug('creating nifti for %s' % data_label)

                # TODO: nimsmrdata.adjust_bvecs to use affine from after reorient
                if metadata.is_dwi and metadata.bvals is not None and metadata.bvecs is not None:
                    filepath = outbase + '.bval'
                    with open(filepath, 'w') as bvals_file:
                        bvals_file.write(' '.join(['%0.1f' % value for value in metadata.bvals]))
                    log.debug('generated %s' % os.path.basename(filepath))
                    filepath = outbase + '.bvec'
                    with open(filepath, 'w') as bvecs_file:
                        bvecs_file.write(' '.join(['%0.4f' % value for value in metadata.bvecs[0, :]]) + '\n')
                        bvecs_file.write(' '.join(['%0.4f' % value for value in metadata.bvecs[1, :]]) + '\n')
                        bvecs_file.write(' '.join(['%0.4f' % value for value in metadata.bvecs[2, :]]) + '\n')
                    log.debug('generated %s' % os.path.basename(filepath))

                # write nifti
                nifti = nibabel.Nifti1Image(data, None)
                nii_header = nifti.get_header()
                nifti.update_header()               # XXX are data and header ever "non-harmonious"
                num_slices = data.shape[2]          # Don't trust metatdata.num_slices; might not match the # acquired.
                nii_header.set_xyzt_units('mm', 'sec')
                nii_header.set_qform(qto_xyz, 'scanner')
                nii_header.set_sform(qto_xyz, 'scanner')
                nii_header.set_dim_info(*([1, 0, 2] if metadata.phase_encode == 0 else [0, 1, 2]))
                nii_header['slice_start'] = 0
                nii_header['slice_end'] = num_slices - 1

                nii_header.set_slice_duration(metadata.slice_duration)
                nii_header['slice_code'] = metadata.slice_order
                if np.iscomplexobj(data):
                    clip_vals = np.percentile(np.abs(data), (10.0, 99.5))
                else:
                    clip_vals = np.percentile(data, (10.0, 99.5))
                nii_header.structarr['cal_min'] = clip_vals[0]
                nii_header.structarr['cal_max'] = clip_vals[1]
                nii_header.set_data_dtype(data.dtype)

                # Stuff some extra data into the description field (max of 80 chars)
                # Other unused fields: nii_header['data_type'] (10 chars), nii_header['db_name'] (18 chars),
                te = 0 if not metadata.te else metadata.te
                ti = 0 if not metadata.ti else metadata.ti
                flip_angle = 0 if not metadata.flip_angle else metadata.flip_angle
                effective_echo_spacing = 0. if not metadata.effective_echo_spacing else metadata.effective_echo_spacing
                acquisition_matrix = [0, 0] if metadata.acquisition_matrix == (None, None) else metadata.acquisition_matrix
                mt_offset_hz = 0. if not metadata.mt_offset_hz else metadata.mt_offset_hz
                phase_encode_undersample = 1 if not metadata.phase_encode_undersample else metadata.phase_encode_undersample
                slice_encode_undersample = 1 if not metadata.slice_encode_undersample else metadata.slice_encode_undersample
                nii_header['descrip'] = 'te=%.2f;ti=%.0f;fa=%.0f;ec=%.4f;acq=[%s];mt=%.0f;rp=%.1f;' % (
                        te * 1000.,
                        ti * 1000.,
                        flip_angle,
                        effective_echo_spacing * 1000.,
                        ','.join(map(str, acquisition_matrix)),
                        mt_offset_hz,
                        1. / phase_encode_undersample,
                        )
                if '3D' in (metadata.acquisition_type or ''):
                    nii_header['descrip'] = str(nii_header['descrip']) + 'rs=%.1f' % (1. / slice_encode_undersample)
                if metadata.phase_encode_direction != None:
                    nii_header['descrip'] = str(nii_header['descrip']) + 'pe=%d' % (metadata.phase_encode_direction)
                if metadata.is_fastcard:
                    nii_header['descrip'] = str(nii_header['descrip']) + 'ves=%f;ve=%d' % (metadata.velocity_encode_scale or 0., metadata.velocity_encoding or 0)

                nii_header['pixdim'][4] = metadata.tr   # XXX pixdim[4] = TR, even when non-timeseries. not nifti compliant

                filepath = outname + '.nii.gz'
                nibabel.save(nifti, filepath)
                results.append(filepath)
                log.info('generated %s' % os.path.basename(filepath))

        if hasattr(metadata, 'md_json'):
            filepath = outbase + '.json'
            with open(filepath, 'w') as fp:
                json.dump(metadata.md_json, fp, indent=2, sort_keys=True)
            log.info('generated %s' % os.path.basename(filepath))
            results.append(filepath)
            log.info('json file %s' % filepath)

        return results

write = NIMSNifti.write
