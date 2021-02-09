import os
import shutil
import argparse
import traceback
from datetime import datetime


HIRES = 'HIRES'
PROXY = 'PROXY'
THUMB = 'THUMBNAILS'

_IN_CONSOLE = False
_LOGGER = []


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
    _rename_files(path)


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


def _rename_files(path):   
    thm = os.path.join(path, THUMB)
    if os.path.exists(thm):
        for each in os.listdir(thm):
            _rename_file(os.path.join(thm, each), '{}.JPG', 0)
    
    hires = os.path.join(path, HIRES)
    if not os.path.exists(hires):
        return
    
    table = {}
    for each in os.listdir(hires):
        table[os.path.splitext(each)[0][2:]] = each

    proxy = os.path.join(path, PROXY)
    for each in os.listdir(proxy):
        try:
            sibling = table[os.path.splitext(each)[0][2:]]
        except KeyError:
            error = "Did not find hires for proxy media '{}'".format(each)
            raise IOError(error)
        
        src = os.path.join(proxy, each)
        dst = os.path.join(proxy, sibling)
        _print("Renaming {} > {}".format(src, dst))
        os.rename(src, dst)


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
    return _rename_folder(path, PROXY)


def _conform_thm_path(path):
    """
    Conform a THM folder by renaming it to 'THUMBNAILS'
    and then rename each .THM file to end in .JPG
    """
    return _rename_folder(path, THUMB)


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

    for level in os.walk(path):
        for fi in level[2]:
            # extract the extension and strip off the '.'
            ext = os.path.splitext(fi)[1][1:]
            # create the extensions subdirectory
            _mkdir(os.path.join(level[0], ext))
            # move the current file to the new subdirectory
            src = os.path.join(level[0], fi)
            dst = os.path.join(level[0], ext)
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


def _main():
    global _IN_CONSOLE
    global _LOGGER
    del _LOGGER[:]
    _IN_CONSOLE = True

    args = _parse_args()

    message = "Press ENTER to exit console."
    try:
        for node in args.input:
            sort_media(node)
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