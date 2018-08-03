#! /usr/bin/python3
# -*- encoding:UTF-8 -*-
"""
compile py file to pyc in batch
"""
import compileall
import argparse
import shutil
import re
import os
import os.path as ospath


class CppyOptParser:
    """
    argument parser
    """

    # default destination
    _DEFAULT_DEST = './cppy_output/'

    def __init__(self):
        self._parser = argparse.ArgumentParser()
        self._add_argument()
        self._src = ''
        self._is_all_file = False
        self._is_quiet = False
        self._is_clean = False
        self._is_force = False
        self._origin_list = []
        self._exclude_list = []
        self._remain_dest = False
        self._dest = CppyOptParser._DEFAULT_DEST
        self._hiding = True

    def _add_argument(self):
        self._parser.add_argument("src",
                                  help="src is the path you want to compile,it is a directory path")
        self._parser.add_argument("-a", "--all_file",
                                  action="store_true",
                                  help="whether copy the no-compiled file(except *.py) to the destination or not")
        self._parser.add_argument("-d", "--dest",
                                  help="dest is the directory you want to save the compile file or directory, default " + CppyOptParser._DEFAULT_DEST)
        self._parser.add_argument("-q", "--quiet",
                                  action="store_true",
                                  help="if only output the error msg")
        self._parser.add_argument("-c", "--clean",
                                  action="store_true",
                                  help="if remove all pyc file in src's __pycache__ before compile")
        self._parser.add_argument("-f", "--force",
                                  action="store_true",
                                  help="if compile all py file even exist pyc with the same name")
        self._parser.add_argument("-o", "--origin_list",
                                  help="copy the selected py file to dest, regex is support,format: -o reg_path1;reg_path2;...")
        self._parser.add_argument("-e", "--exclude_list",
                                  help="the file and directory whose name fits regex in exclude_list will be overlooked, if the regex was in origin_list,it will be overlooked.format: -e reg_path1;reg_path2;...")
        self._parser.add_argument("-r", "--remain_dest",
                                  action="store_true",
                                  help="if remain all data in dest")
        self._parser.add_argument("-n", "--nohiding",
                                  action="store_false",
                                  help="if copy and compile the hide data whose name starts with a '.',default hiding")

    def parse_args(self):
        """
        parse arguments and verify them
        """
        args = self._parser.parse_args()
        self._src = args.src
        self._is_all_file = args.all_file
        self._is_clean = args.clean
        self._is_quiet = args.quiet
        self._is_force = args.force
        self._dest = CppyOptParser._DEFAULT_DEST if args.dest is None else args.dest
        self._origin_list = CppyOptParser._get_origin_list(args)
        self._exclude_list = CppyOptParser._get_exclude_list(args)
        self._remain_dest = args.remain_dest
        self._hiding = args.nohiding
        self._validate()

    def _validate(self):
        """
        verify arguments whether valid or not
        """
        src_abs = ospath.abspath(self._src)
        dest_abs = ospath.abspath(self._dest)
        if not ospath.exists(src_abs) or ('.' in src_abs and src_abs.rfind('.') != 0):
            self._parser.error('src[ %s ] doesn\'t exist as a directory' % (self._src,))
        if '.' in dest_abs and dest_abs.rfind('.') != 1:
            self._parser.error("dest[ %s ] is not a directory" % (self._dest,))
        if dest_abs.startswith(src_abs):
            self._parser.error("dest[ %s ] is in src[ %s ]" % (self._src, self._dest))

    @staticmethod
    def _get_origin_list(args):
        """get original files list"""
        if args.origin_list is None:
            return []
        temp = args.origin_list.split(';')
        ans = list(filter(lambda x: len(x) != 0, map(lambda y: y.strip(), temp)))
        return ans

    @staticmethod
    def _get_exclude_list(args):
        """get files list which files need to be excluded"""
        if args.exclude_list is None:
            return []
        temp = args.exclude_list.split(';')
        ans = list(filter(lambda x: len(x) != 0, map(lambda y: y.strip(), temp)))
        return ans

    @property
    def src(self):
        return self._src

    @property
    def is_all_file(self):
        return self._is_all_file

    @property
    def dest(self):
        return self._dest

    @property
    def is_quiet(self):
        return self._is_quiet

    @property
    def is_clean(self):
        return self._is_clean

    @property
    def is_force(self):
        return self._is_force

    @property
    def origin_list(self):
        return self._origin_list

    @property
    def exclude_list(self):
        return self._exclude_list

    @property
    def remain_dest(self):
        return self._remain_dest

    @property
    def hiding(self):
        return self._hiding

    def get_error_interface(self):
        """
        :return: an interface using to print error message in termenal, need a argument named message
        """
        return self._parser.error


class CompileController:
    """
    Compile controller firstly compiles files or project to pyc file.
    Secondly it traverses every directory.
    Thirdly it copies pyc file in __pycache__ to the corresponding directory in the specified directory.
    If some exceptions appear during the compilation process,
     this script will remove all files and directories generated by it.
    """

    # compileall output format: test.python-36.pyc
    PYC_FILE_REOBJ = re.compile('^(.*?)(\..*)?(\.pyc)$')

    def __init__(self):
        self._parser = CppyOptParser()
        self._parser.parse_args()
        self._src = ospath.abspath(self._parser.src)
        self._dest = ospath.abspath(self._parser.dest)
        self._is_all_file = self._parser.is_all_file
        self._is_quiet = self._parser.is_quiet
        self._is_clean = self._parser.is_clean
        self._is_force = self._parser.is_force
        self._origin_list = list(map(re.compile, self._parser.origin_list))
        self._exclude_list = list(map(re.compile, self._parser.exclude_list))
        self._remain_dest = self._parser.remain_dest
        self._hiding = self._parser.hiding
        self._error = self._parser.get_error_interface()
        # record the paths of files and directories generated by this script, and remove them when exception raises
        self._create_paths_list = []
        self._start_mission()

    def _create_directory(self, path):
        """
        create directory if the given path doesn't exist
        :param path: directory path
        :return if directory has exist at beginning, returns False otherwise returns True.
        """
        if not ospath.exists(path):
            os.makedirs(path)
            self._create_paths_list.append(path)
            return True
        return False

    def _create_dest_directory(self):
        """
        create paths of destination directory, and added them into list
        """
        paths = list(ospath.split(ospath.abspath(self._dest)))
        paths.reverse()
        if paths[-1] == '':
            paths.pop()
        path_list = []
        while len(paths) != 0:
            path_list.append(paths.pop())
            path = os.sep.join(path_list)
            self._create_directory(path)

    def _copy_file(self, src, dest):
        """
        copy source file to destination, if there is a file with the same name in destination, overwrites it.
        :param src:  source file path
        :param dest: destination file path
        """
        shutil.copy(src, dest)
        self._create_paths_list.append(dest)
        if not self._is_quiet:
            print(src + ' -----> ' + dest)

    def _delete_all_in_create_paths_list(self):
        """
        remove all directories and files in create_path_list according to the reverse creating order.
        """
        for path in self._create_paths_list:
            if ospath.isfile(path):
                os.remove(path)
            else:
                os.rmdir(path)

    def _remove_dest(self):
        """
        remove all data of destination and remove the destination directory.
        """
        if self._remain_dest:
            return
        for root, dirs, files in os.walk(self._dest, topdown=False):
            for file in files:
                file_path = ospath.join(root, file)
                if not self._is_quiet:
                    print("remove: " + file_path)
                os.remove(file_path)
            if not self._is_quiet:
                print("remove: " + root)
            os.rmdir(root)

    @staticmethod
    def _remove_version_tag(name):
        """
        remove the version in name(test.python3.6.pyc --> test.pyc)
        :param name: file name
        :return: new name
        """
        reobj = CompileController.PYC_FILE_REOBJ.match(name)
        if reobj is None:
            return name
        return reobj.group(1) + ".pyc"

    def _copy_pyc_in_pycache(self, src_path, dest_path):
        """
        copy file in __pycache__ to destination
        :param src_path: source directory
        :param dest_path: destination directory
        """
        for name in os.listdir(src_path):
            src = ospath.join(src_path, name)
            if ospath.isfile(src):
                new_name = CompileController._remove_version_tag(name)
                dest = ospath.join(dest_path, new_name)
                self._copy_file(src, dest)

    def _remove_all_pyc(self, src_path):
        """
        remove all .pyc file in the specified directory.
        :param src_path: path of the specified directory
        """
        for root, dirs, files in os.walk(src_path, topdown=True):
            if self._hiding and root[0] == '.':
                continue
            if self._hiding:
                files = filter(lambda x: x[0] != '.', files)
            files = filter(lambda x: x.lower().endswith(".pyc"), files)
            for file in map(lambda x: ospath.join(root, file), files):
                if not self._is_quiet:
                    print("remove: " + file)
                os.remove(file)

    def _walk_in_directory(self, src_path, dest_path):
        """
        traverses directory
        :param src_path: source directory
        :param dest_path: destination directory
        """
        self._create_directory(dest_path)  # create directory first
        for root, dirs, files in os.walk(src_path, topdown=True):
            if self._hiding and root[0] == '.':
                break
            if self._hiding:
                # if the hiding files and directories are chosen
                dirs = list(filter(lambda x: x[0] != '.', dirs))
                files = list(filter(lambda x: x[0] != '.', files))

                # exclude directories that match the regular expression in self._exclude_list
                for exclude in self._exclude_list:
                    dirs = list(filter(lambda d: not exclude.search(d), dirs))

                # exclude files that match the regular expression in self._exclude_list
                for exclude in self._exclude_list:
                    files = list(filter(lambda f: not exclude.search(f), files))

            gen = ((ospath.join(root, file), (ospath.join(dest_path, file))) for file in files)
            for src, dest in gen:
                if src.lower().endswith('.pyc'):
                    # copy pyc
                    dest = CompileController._remove_version_tag(dest)
                    self._copy_file(src, dest)
                if self._is_all_file and not src.lower().endswith('.py'):
                    # do not copy if file name end with py
                    self._copy_file(src, dest)

                if src.lower().endswith('.py') and any(map(lambda x: x.search(src), self._origin_list)):
                    # copy file if the file match regular expression
                    self._copy_file(src, dest)

            gen_d = ((ospath.join(root, d), (ospath.join(dest_path, d))) for d in dirs)
            for sd, dd in gen_d:
                if '__pycache__' in sd.lower():
                    # handle the directory named __pycache__
                    self._copy_pyc_in_pycache(sd, ospath.dirname(dd))
                else:
                    self._walk_in_directory(sd, dd)
            # only traverse current directory
            break

    def _remove_pycache_dirs(self):
        """remove all cache directories and their files"""
        if not self._is_clean:
            return
        for root, dirs, files in os.walk(self._src, topdown=True):
            if (self._hiding and root[0] == '.') or '__pycache' not in root.lower():
                continue
            if self._hiding:
                files = filter(lambda x: x[0] != '.', files)
            files = filter(lambda x: x.lower().endswith(".pyc"), files)
            for file in map(lambda x: ospath.join(root, x), files):
                if not self._is_quiet:
                    print("remove: " + file)
                os.remove(file)

    def _start_mission(self):
        """
        start compile mission
        """
        try:
            self._remove_pycache_dirs()
            self._remove_dest()
            self._create_dest_directory()
            compileall.compile_dir(self._src, maxlevels=100, force=self._is_force, quiet=self._is_quiet)
            basename = ospath.basename(self._src)
            self._dest = ospath.join(self._dest, basename)
            self._walk_in_directory(self._src, self._dest)
        except Exception as e:
            self._delete_all_in_create_paths_list()
            self._error(str(e))


if __name__ == "__main__":
    CompileController()
