# cppy

cppy means **C**om**p**ile **Py**thon

## Instruction

This is a tool writing in python3 that compiles the .py files in the python project to .pyc files and saves them in the specified directory.

Using `python3 cppy.py -h` to know how to use this script.

```
usage: cppy.py [-h] [-a] [-d DEST] [-q] [-c] [-f] [-o ORIGIN_LIST]
               [-e EXCLUDE_LIST] [-r] [-n]
               src

positional arguments:
  src                   src is the path you want to compile,it is a directory
                        path

optional arguments:
  -h, --help            show this help message and exit
  -a, --all_file        whether copy the no-compiled file(except *.py) to the
                        destination or not
  -d DEST, --dest DEST  dest is the directory you want to save the compile
                        file or directory,default ./cppy_output/
  -q, --quiet           if only output the error msg
  -c, --clean           if remove all pyc file in src's __pycache__ before
                        compile
  -f, --force           if compile all py file even exist pyc with the same
                        name
  -o ORIGIN_LIST, --origin_list ORIGIN_LIST
                        copy the selected py file to dest,regex is
                        support,format: -o reg_path1;reg_path2;...
  -e EXCLUDE_LIST, --exclude_list EXCLUDE_LIST
                        the file and directory whose name fits regex in
                        exclude_list will be overlooked,if the regex was in
                        origin_list,it will be overlooked.format: -e
                        reg_path1;reg_path2;...
  -r, --remain_dest     if remain all data in dest
  -n, --nohiding        if copy and compile the hide data whose name starts
                        with a '.',default hiding

```

Note: Do not access the target directory when compilation is running, otherwise it might be terminated.

If you want to access the repository of cppy in gitee.com, here is the url: https://gitee.com/sineatos/cppy/tree/master

## 中文说明

cppy 意思是 **C**om**p**ile **Py**thon

一个使用python3编写的小工具，将指定路径中目录里面的所有py文件编译成pyc文件，然后提取到指定目录中

具体使用方法请使用```python3 cppy.py -h ```获得使用说明

##### 参数说明：
```
usage: cppy.py [-h] [-a] [-d DEST] [-q] [-f] src

必填参数:
  src                   源代码的目录路径

选填参数:
  -h, --help            显示帮助文档
  -a, --all_file        是否将pyc文件以外的非py文件复制到生成的目标目录
  -d DEST, --dest DEST  指定目标目录，默认为./cppy_output/
  -q, --quiet           安静模式，是否只输出错误结果
  -f, --force           是否重新编译所有的py文件，即使对应的pyc文件已经存在
  -o ORIGIN_LIST, --origin_list ORIGIN_LIST
                        复制选中的py文件到目标目录中，支持正则表达式，输入为一个列表，以分号(;)隔开，例如：-o reg_path1;reg_path2;...
  -e EXCLUDE_LIST, --exclude_list EXCLUDE_LIST
                        将文件名或者目录名匹配列表中的正则表达式的文件和路径忽略，如果这些文件同样附和origin_list的要求，同样忽略，正则表达式列表的格式为以分号(;)隔开，例如：-e reg_path1;reg_path2;...
  -r, --remain_dest     保留原来在dest目录中的所有数据，默认为不保留
  -n, --nohiding        是否复制和编译隐藏的数据(以'.'开头命名的文件和目录)，默认为不复制和编译这些隐藏数据
  -c, --clean			是否在编译之前删除源目录中所有的__pycache__中的所有pyc文件
```

#### 注意

如果当前正在浏览目标目录，那么如果发生删除操作，可能会终止编译过程，所以最好还是在编译的时候不要浏览目标目录里面的任何东西

如果想要访问cppy在gitee.com的仓库，可访问：https://gitee.com/sineatos/cppy/tree/master