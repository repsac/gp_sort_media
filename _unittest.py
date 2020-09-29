import os
import tempfile
import shutil
from pathlib import Path
import gp_sort_media


# padding format
PADDING = '{{:0{}d}}'
# format used by the LRV files
GL = 'GL{}.{}'
# format used by MP4 and THM files
GH = 'GH{}.{}'
# common extensions used in testing
MP4 = 'MP4'
LRV = 'LRV'
THM = 'THM'
JPG = 'JPG'


def unittest():

    # first test by passing in a folder path, this folder is structured
    # like what you would find on a GP's memory card (100GOPRO)
    _test_folder_path()

    # test passing through specific LRV files
    _test_lrv_files()

    # test passing through specific THM files
    _test_thm_files()

    # test passing through specific unsupport files
    _test_unsupported_files()


def _test_unsupported_files():
    """
    test that file types that are not supported for conform
    (conform only applied to THM and LRV)
    do indeed result in an exception being raised
    """
    tmpdir = tempfile.mkdtemp()

    # I am wrapping this in its own try/except because
    # we are writing files to disk and there is a possiblity
    # that we could trigger an IOError in a different context
    try:
        nodes = _create_loose_test_files(
            tmpdir,
            ((MP4, gp_sort_media.HIRES, GH),),
            gp_sort_media.HIRES)
    except:
        shutil.rmtree(tmpdir)
        raise

    passed = False
    try:
        gp_sort_media.conform_files(nodes)
    except IOError:
        # if this specific exception came up then we're good
        passed = True
    finally:
        shutil.rmtree(tmpdir)

    assert passed, "Failed to detected unsupported file types"


def _test_thm_files():
    """
    test that the THM files were renamed to have JPG extensions
    """
    tmpdir = tempfile.mkdtemp()
    try:
        _renamed_thm_files(tmpdir)
    finally:
        shutil.rmtree(tmpdir)


def _test_lrv_files():
    """
    the first test is to test that all LRV files were
    conformed to match the naming convention  of the MP4 files

    the second test is to address conflicts that may happen
    if someone is trying to conform LRV files livining in
    the same folder as the corresponding MP4 files
    """
    for func in (_renamed_lrv_files,
                 _renamed_lrv_files_with_conflict):

        tmpdir = tempfile.mkdtemp()
        try:
            func(tmpdir)
        finally:
            shutil.rmtree(tmpdir)


def _create_loose_test_files(tmpdir, mapping, key):
    nodes = _touch_paths(tmpdir, 1, 6, mapping)
    return [os.path.join(tmpdir, x) for x in nodes[key]]


def _renamed_lrv_files_with_conflict(tmpdir):
    """
    Test that if a conformed LRV file is going to clash with
    the corresponding MP4 in the same directory.
    Conforms with LRV should not occur in the same path as the
    source MP4 files.

    checking for FileExistsError exception
    """
    # create the LRV nodes
    nodes = _create_loose_test_files(
        tmpdir,
        ((LRV, gp_sort_media.PROXY, GL),),
        gp_sort_media.PROXY)

    # create the conflicting file
    mapping = ((MP4, gp_sort_media.HIRES, GH),)
    _touch_paths(tmpdir, 5, 6, mapping)

    passed = False
    try:
        gp_sort_media.conform_files(nodes)
    except FileExistsError:
        # if this specific exception came up then we're good
        passed = True

    assert passed, "Failed to detected existing file"


def _renamed_files(tmpdir, mapping, key, ext):
    # create the loose files for testing
    nodes =_create_loose_test_files(tmpdir, mapping, key)
    # pass them in for conforming
    gp_sort_media.conform_files(nodes)

    # the actual nodes in the test directory
    actual = os.listdir(tmpdir)
    # what we exepcted to see in the test directory
    expected = [GH.format(PADDING.format(6).format(x), ext)
                for x in range(1, 6)]

    error = "Renamed {} files incorrect. Expected {} found {}".format(
            ext, expected, actual
        )
    assert expected == actual, error


def _renamed_thm_files(tmpdir):
    _renamed_files(
        tmpdir,
        ((THM, gp_sort_media.THUMB, GH),),
        gp_sort_media.THUMB,
        JPG)


def _renamed_lrv_files(tmpdir):
    _renamed_files(
        tmpdir,
        ((LRV, gp_sort_media.PROXY, GL),),
        gp_sort_media.PROXY,
        MP4)


def _test_folder_path():
    tmpdir = tempfile.mkdtemp()

    try:
        nodes = _create_test_nodes(tmpdir)
        gp_sort_media.sort_media(tmpdir)
        _test_nodes(tmpdir, nodes)
    finally:
        shutil.rmtree(tmpdir)


def _test_nodes(tmpdir, nodes):

    for each in os.listdir(tmpdir):

        # look for any unknown nodes that should
        # not exist at the root level
        error = "{} is an unknown node".format(each)
        assert each in nodes, error

        # in each subfolder (for each file type)
        # look for mismatched node names
        actual = os.listdir(os.path.join(tmpdir, each))
        error = "Mismatched nodes ({}). Expected {} found {}".format(
            each, nodes[each], actual
        )
        assert nodes[each] == actual, error


def _create_test_nodes(tmpdir):

    nodes = {}

    # create 15 files that correspond to 5 recordings
    # each recording has an MP4, LRV, and THM
    video = ((MP4, gp_sort_media.HIRES, GH),
             (THM, gp_sort_media.THUMB, GH),
             (LRV, gp_sort_media.PROXY, GL))
    nodes.update(_touch_paths(tmpdir, 1, 6, video))

    # create 6 files that correspond to 3 exposures
    # each exposure has a GPR (raw) and JPG
    # JPG and GPR files use this format
    go = 'GOPR{}.{}'
    image = (('GPR', 'GPR', go),
             (JPG, JPG, go))    
    nodes.update(_touch_paths(tmpdir, 1, 4, image))

    # locate the LRV and THM files and rename them in a way that
    # they will be expected to be after conforming is complete
    for key, prop in ((gp_sort_media.PROXY, gp_sort_media.LRV_PROPERTIES ),
                      (gp_sort_media.THUMB, gp_sort_media.THM_PROPERTIES)):

        for index, each in enumerate(nodes[key]):
            each = os.path.splitext(each)[0]
            nodes[key][index] = prop[0].format(each[prop[1]:])

    return nodes


def _touch_paths(tmpdir, start, end, mapping):

    nodes = {}

    for index in range(start, end):

        # create the padding index: 000002
        index = PADDING.format(end).format(index)

        for ext in mapping:
            # create a new that matches the current extensions
            nodes.setdefault(ext[1], [])
            # build the file name with the prefix and extension
            filename = ext[2].format(index, ext[0])
            # add to the extenion's list
            nodes[ext[1]].append(filename)
            # create the empty file on disk
            Path(os.path.join(tmpdir, filename)).touch()

    return nodes


def _main():
    gp_sort_media._IN_CONSOLE = True
    unittest()


if __name__ == '__main__':
    _main()