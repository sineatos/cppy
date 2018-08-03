#! /usr/bin/python3
# -*- encoding:UTF-8 -*-
"""
批量将py编译成pyc
"""
import compileall
import argparse
import shutil
import re
import os
import os.path as ospath
import time


class CppyOptParser:
    """
    参数解析器
    """

    # 默认的目标地址
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
                                  help="dest is the directory you want to save the compile file or directory,default " + CppyOptParser._DEFAULT_DEST)
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
                                  help="copy the selected py file to dest,regex is support,format: -o reg_path1;reg_path2;...")
        self._parser.add_argument("-e", "--exclude_list",
                                  help="the file and directory whose name fits regex in exclude_list will be overlooked,if the regex was in origin_list,it will be overlooked.format: -e reg_path1;reg_path2;...")
        self._parser.add_argument("-r", "--remain_dest",
                                  action="store_true",
                                  help="if remain all data in dest")
        self._parser.add_argument("-n", "--nohiding",
                                  action="store_false",
                                  help="if copy and compile the hide data whose name starts with a '.',default hiding")

    def parse_args(self):
        """
        解析参数并且对其进行校验
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
        校验输入的参数是否合法
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
        """获取目标地址需要源文件的列表"""
        if args.origin_list is None:
            return []
        temp = args.origin_list.split(';')
        ans = list(filter(lambda x: len(x) != 0, map(lambda y: y.strip(), temp)))
        return ans

    @staticmethod
    def _get_exclude_list(args):
        """获取目标地址需要排除的源文件的列表"""
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
        :return: 在终端上显示错误信息的接口，需要一个参数message
        """
        return self._parser.error


class CompileController:
    """
    编译控制器
    先将文件或者项目编译成pyc文件，然后遍历每一个目录，
    将__cache__目录里面的pyc文件复制到其上一层目录的对应副本中，
    如果在编译的过程中发生了异常，会将该脚本生成的副本文件以及目录删除
    """

    # compileall输出的pyc文件的命名格式如：test.python-36.pyc
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
        # 将所有由该脚本创建的所有文件和目录保存在该列表中，在遇到异常的时候会将它们全部删除
        self._create_paths_list = []
        self._start_mission()

    def _create_directory(self, path):
        """
        创建目录，如果给定的路径上已经存在目录则不会有任何操作
        :param path: 目录路径
        :return 如果目录一开始已存在返回False,否则返回True
        """
        if not ospath.exists(path):
            os.makedirs(path)
            self._create_paths_list.append(path)
            return True
        return False

    def _create_dest_directory(self):
        """
        创建目标目录的路径，并且将创建的每一个目录都存入创建列表中
        """
        # 将目标目录路径按路径分隔符分隔，然后整个列表转置
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
        将指定路径上的文件复制到指定目录中,如果当前目录中已经有了同名的文件则覆盖就旧文件
        :param src:  源文件路径
        :param dest: 目标文件路径
        """
        shutil.copy(src, dest)
        self._create_paths_list.append(dest)
        if not self._is_quiet:
            print(src + ' -----> ' + dest)

    def _delete_all_in_create_paths_list(self):
        """
        按照创建顺序的逆序销毁创建列表中的所有目录和文件
        """
        for path in self._create_paths_list:
            if ospath.isfile(path):
                os.remove(path)
            else:
                os.rmdir(path)

    def _remove_dest(self):
        """
        删除目标目录中的所有数据以及该目录
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
        去除名称中的版本号(test.python3.6.pyc --> test.pyc)
        :param name: 文件名
        :return:
        """
        reobj = CompileController.PYC_FILE_REOBJ.match(name)
        if reobj is None:
            return name
        return reobj.group(1) + ".pyc"

    def _copy_pyc_in_pycache(self, src_path, dest_path):
        """
        将缓存目录中的文件复制到目标目录中
        :param src_path: 源目录
        :param dest_path:目标目录
        """
        for name in os.listdir(src_path):
            src = ospath.join(src_path, name)
            if ospath.isfile(src):
                new_name = CompileController._remove_version_tag(name)
                dest = ospath.join(dest_path, new_name)
                self._copy_file(src, dest)

    def _remove_all_pyc(self, src_path):
        """
        删除指定目录中的所有pyc结尾的文件
        :param src_path: 指定目录路径
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
        遍历目录，并操作
        :param src_path: 源目录
        :param dest_path: 目标目录
        """
        self._create_directory(dest_path)  # 先创建目标目录
        for root, dirs, files in os.walk(src_path, topdown=True):
            if self._hiding and root[0] == '.':
                break
            if self._hiding:
                # 如果选择隐藏任何数据
                dirs = list(filter(lambda x: x[0] != '.', dirs))
                files = list(filter(lambda x: x[0] != '.', files))

                # 将目录名符合正则表达式名称列表中的正则表达式的目录排除
                for exclude in self._exclude_list:
                    dirs = list(filter(lambda d: not exclude.search(d), dirs))  # 这里需要将dirs变为列表，否则会丢失数据

                # 将文件名符合正则表达式名称列表中的正则表达式的文件排除
                for exclude in self._exclude_list:
                    files = list(filter(lambda f: not exclude.search(f), files))  # 这里需要将files变为列表，否则会丢失数据

            gen = ((ospath.join(root, file), (ospath.join(dest_path, file))) for file in files)
            for src, dest in gen:
                if src.lower().endswith('.pyc'):
                    # 复制pyc
                    dest = CompileController._remove_version_tag(dest)
                    self._copy_file(src, dest)
                if self._is_all_file and not src.lower().endswith('.py'):
                    # 如果后缀名为py的则不复制到副本中
                    self._copy_file(src, dest)

                if src.lower().endswith('.py') and any(map(lambda x: x.search(src), self._origin_list)):
                    # 如果指定的文件为符合正则表达式要求的文件则复制到副本中
                    self._copy_file(src, dest)

            gen_d = ((ospath.join(root, d), (ospath.join(dest_path, d))) for d in dirs)
            for sd, dd in gen_d:
                if '__pycache__' in sd.lower():
                    # 该目录为保存pyc文件的目录，另外处理
                    self._copy_pyc_in_pycache(sd, ospath.dirname(dd))
                else:
                    self._walk_in_directory(sd, dd)
            # os.walk会遍历目录下任何的文件和子目录，由于已经使用了递归的方法访问子目录，所以每一次遍历目录只需要访问一层即可
            break

    def _remove_pycache_dirs(self):
        """删除源目录中的所有缓存目录及其文件"""
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
        开始编译任务
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
