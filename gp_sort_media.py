import os
import shutil
import argparse
import traceback
from datetime import datetime


HIRES = 'HIRES'
PROXY = 'PROXY'
THUMB = 'THUMBNAILS'

LRV_PROPERTIES = ('GH{}.MP4', 2)
THM_PROPERTIES = ('{}.JPG', 0)

_IN_CONSOLE = False
_LOGGER = []


def conform_files(files):
    """
    Given a list of files, conform the files in place.
    Supported types: LVR, THM

    Make sure to not conform LVR files in the same directory
    as the corresponding MP4 file

    :param files: list of file names
    """
    if isinstance(files, str):
        files = (files,)

    for fi in files:
        _process_file(os.path.abspath(fi))


def sort_media(path):
    """
    Given a path of GoPro media (100GOPRO) sort the media
    into folders based on extensions. LRV and THM files will
    be conformed and their extension directories renamed
    
    :param path: path
    """
    path = os.path.abspath(path)
    _sort_dir(path)
    _conform_paths(path)


def conform_lrv_file(path):
    return _rename_file(path, *LRV_PROPERTIES)


def conform_thm_file(path):
    return _rename_file(path, *THM_PROPERTIES)


def _process_file(path):
    """
    Process a file to see if it can be conformed.
    If the file type is unsupported raise an IOError
    """
    ext = os.path.splitext(path)[-1][1:]

    try:
        func = globals()['conform_{}_file'.format(ext.lower())]
    except KeyError:
        error = ".{} file support not available".format(ext)
        raise IOError(error)
    
    return func(path)


def _rename_file(src, fmt, index):
    basename, ext = os.path.splitext(os.path.basename(src))
    dst = os.path.join(os.path.dirname(src),
                       fmt.format(basename[index:]))
    
    if os.path.exists(dst):
        error = "{} already exists".format(dst)
        raise FileExistsError(error)

    _print("Renaming {} {} > {}".format(
        ext[1:], src, dst
    ))
    os.rename(src, dst)

    return dst


def _conform_mp4_path(path):
    """
    Rename the MP4 path to 'HIRES'
    """
    return _rename_folder(path, HIRES)


def _conform_lrv_path(path):
    """
    Conform a THM folder by renaming it to 'PROXY'
    and then rename each .LRV file to end in .MP4
    and changed the prefix from 'GL' to 'GH'
    """
    path = _rename_folder(path, PROXY)

    for each in os.listdir(path):
        _rename_file(os.path.join(path, each), *LRV_PROPERTIES)
    
    return path


def _conform_thm_path(path):
    """
    Conform a THM folder by renaming it to 'THUMBNAILS'
    and then rename each .THM file to end in .JPG
    """
    path = _rename_folder(path, THUMB)

    for each in os.listdir(path):
        _rename_file(os.path.join(path, each), *THM_PROPERTIES)

    return path


def _rename_folder(src, dst):
    """
    :param src: folder path
    :param dst: new name only (not the full path)
    """
    dst = os.path.join(os.path.dirname(src), dst)
    if os.path.exists(dst):
        raise IOError("{} already exists".format(dst))
    _print("Renaming directory {} > {}".format(src, dst))
    shutil.move(src, dst)
    return dst


def _conform_paths(path):
    """
    query the subdirectory paths that are valid for
    conforming. example: LRV, THM
    """

    glo = globals()

    for each in os.listdir(path):
        try:
            glo['_conform_{}_path'.format(each.lower())](
                os.path.join(path, each))
        except KeyError:
            continue


def _sort_dir(path):

    _print("Sorting GoPro media in: {}".format(path))

    for each in os.listdir(path):
        # extract the extension and strip off the '.'
        ext = os.path.splitext(each)[1][1:]
        # create the extensions subdirectory
        _mkdir(os.path.join(path, ext))
        # move the current file to the new subdirectory
        src = os.path.join(path, each)
        dst = os.path.join(path, ext)
        _print("Moving {} > {}".format(src, dst))
        shutil.move(src, dst)


def _mkdir(path):
    if not os.path.exists(path):
        os.mkdir(path)


def _parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("input", nargs="+")
    return parser.parse_args()


def _print(msg):
    if _IN_CONSOLE:
        print(msg)
        global _LOGGER
        _LOGGER.append(msg)


def _sort_input(arg_input):

    table = (
        (os.path.isdir, []),
        (os.path.isfile, [])
    )

    for each in arg_input:
        for func, array in table:
            each = os.path.abspath(each)
            if func(each):
                array.append(each)
                break
        else:
            error = "Unsopported node type '{}'".format(each)
            raise IOError(error)
    
    return table


def _main():
    global _IN_CONSOLE
    global _LOGGER
    del _LOGGER[:]
    _IN_CONSOLE = True

    args = _parse_args()
    nodes = _sort_input(args.input)

    message = "Press ENTER to exit console."
    try:
        for node in nodes[0][1]:
            sort_media(node)
        if nodes[1][1]:
            conform_files(nodes[1][1])
    except:
        fname = "{}.{}.error".format(
            os.path.splitext(__file__)[0],
            datetime.now().strftime("%Y%m%d-%H%M%S")
        )
        error_log = os.path.join(os.getcwd(), fname)
        logs = '\n'.join(_LOGGER)
        logs += traceback.format_exc()
        with open(error_log, 'w') as x:
            x.write(logs)
        message = "Error detected.\nLog file {}\n{}".format(
            error_log, message
        )
        input(message)
    else:
        input(message)


if __name__ == '__main__':
    _main()