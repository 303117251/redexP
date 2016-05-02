# coding=utf-8
import argparse
import os
import timeit
# coding=utf-8 临时文件来存储数据，但不需要同其他程序共享
import tempfile
# High-level file operations
import shutil
# atexit模块很简单，只定义了一个register函数用于注册程序退出时的回调函数，我们可以在这个回调函数中做一些资源清理的操作
import atexit
import zipfile
import sys
from os.path import join, isfile
timer = timeit.default_timer
per_file_compression = {}


def make_temp_dir(name='', debug=False):
    """ Make a temporary directory which will be automatically deleted """
    directory = tempfile.mkdtemp(name)

    if not debug:  # In debug mode, don't delete the directory
        def remove_directory():
            shutil.rmtree(directory)
        atexit.register(remove_directory)
    return directory


def extract_apk(apk, destination_directory):
    with zipfile.ZipFile(apk) as z:
        for info in z.infolist():
            per_file_compression[info.filename] = info.compress_type
        z.extractall(destination_directory)


def run_redex(args):
    debug_mode = args.unpack_only or args.debug
    unpac_start_time = timer()
    extracted_apk_dir = make_temp_dir('.redex_extracted_apk', debug_mode)
    log('Extracting apk...')
    extract_apk(args.input_apk, extracted_apk_dir)


def want_trace():
    try:
        trace = os.environ['TRACE']
    except KeyError:
        return False
    for t in trace.split(','):
        try:
            return int(t) > 0
        except ValueError:
            pass
        try:
            (module, level) = t.split(':')
            if module == 'REDEX' and int(level) > 0:
                return True
        except ValueError:
            pass
    return False


def log(*stuff):
    if want_trace():
        print(*stuff, file=sys.stderr)


def arg_parser(
        binary=None,
        config=None,
        keystore=None,
        keyalias=None,
        keypass=None,
):
    description = """
Given an APK, produce a better APK!
"""
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=description)

    parser.add_argument('input_apk', help='Input APK file')
    parser.add_argument('-o', '--out', nargs='?', default='redex-out.apk',
                        help='Output APK file name \
                        (defaults to redex-out.apk)')
    parser.add_argument('-j', '--jarpath', nargs='?')

    parser.add_argument('--redex-binary', nargs='?', default=binary,
                        help='Path to redex binary')

    parser.add_argument('-c', '--config', default=config,
                        help='Configuration file')

    parser.add_argument('-t', '--time', action='store_true',
                        help='Run redex passes with \
                        `time` to print CPU and wall time')

    parser.add_argument('--sign', action='store_true',
                        help='Sign the apk after optimizing it')
    parser.add_argument('-s', '--keystore', nargs='?', default=keystore)
    parser.add_argument('-a', '--keyalias', nargs='?', default=keyalias)
    parser.add_argument('-p', '--keypass', nargs='?', default=keypass)

    parser.add_argument('-u', '--unpack-only', action='store_true',
                        help='Unpack the apk and print\
                         the unpacked directories, don\'t '
                        'run any redex passes or repack the apk')

    parser.add_argument('-w', '--warn', nargs='?',
                        help='Control verbosity of warnings')

    parser.add_argument('-d', '--debug', action='store_true',
                        help='Unpack the apk and print the \
                        redex command line to run')

    parser.add_argument('-m', '--proguard-map', nargs='?',
                        help='Path to proguard mapping.txt \
                        for deobfuscating names')

    parser.add_argument('-P', '--proguard-config', nargs='?',
                        help='Path to proguard config')

    parser.add_argument('-k', '--keep', nargs='?',
                        help='Path to file containing classes to keep')

    parser.add_argument('-S', dest='passthru', action='append', default=[],
                        help='Arguments passed through to redex')
    parser.add_argument('-J', dest='passthru_json', action='append',
                        default=[], help='JSON-formatted arguments passed \
                        through to redex')

    return parser
if __name__ == '__main__':
    keys = {}
    try:
        keystore = join(os.environ['HOME'], '.android', 'debug.keystore')
        if isfile(keystore):
            keys['keystore'] = keystore
            keys['keyalias'] = 'androiddebugkey'
            keys['keypass'] = 'android'
    except:
        pass
args = arg_parser(**keys).parse_args()
run_redex(args)
