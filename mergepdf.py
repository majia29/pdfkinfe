#!/usr/bin/env python2
# -*- coding: utf-8 -*-

from __future__ import (
    absolute_import,
    division,
    print_function,
    unicode_literals,
)

import os
import sys

from PyPDF2 import PdfFileMerger, PdfFileReader

__all__ = (
)

reload(sys)
sys.setdefaultencoding("utf-8")

def abspath(f):
    """
    返回绝对路径。

    支持处理`~`符号。不检查文件存在。
    """
    return os.path.abspath(os.path.expanduser(f))

def ispdf(f):
    """
    判断文件是否为pdf文件

    仅检查文件文件后缀名是否为pdf。
    """
    fname, ext = os.path.splitext(f)
    if ext<>".pdf":
        return False
    return True

def _usage():
    """
    命令行说明
    """
    print("usage: mergepdf.py mypdf1.pdf mypdf2.pdf [-o output.pdf]")
    print("   or  mergepdf.py mypdf1.pdf mypdf2.pdf:1-200 [-o output.pdf]")
    sys.exit(-100)

def _input_parser(arg):
    """
    参数中的输入文件项的解析
    只做格式解析，不做文件是否存在，是否为pdf文件等有效性检查
    输出格式： ("文件名", "n-m")
    
    支持的格式: 文件名、文件名:n-m、文件名:n-、文件名:-m
    其中n,m分别代表从1开始计数的开始/结束页码。注意：如果m>n，表示从第m页逆序抽取页面。
    """
    input_item = arg.split(":")
    if len(input_item)==1:
        input_file, input_ranges = input_item[0], "1-"
    elif len(input_item)==2:
        input_file, input_ranges = input_item[0], input_item[1]
        native_ranges = input_ranges.split(",")
        ranges_list = []
        for native_range in native_ranges:
            # 切分破折号
            native_range = native_range.split("-")
            if len(native_range)==1:
                left_range, right_range = native_range[0], native_range[0]
            elif len(native_range)==2:
                left_range, right_range = native_range[0], native_range[1]
            else:
                print("error: invalid range(dash). {}".format(arg))
                _usage()
            # 检查破折号两端是否数字
            if (left_range=="" or left_range.isdigit()) and \
               (right_range=="" or right_range.isdigit()):
                pass
            else:
                print("error: invalid range(digit). {}".format(arg))
                _usage()
            # 从1开始计数的开始/结束页码
            if left_range=="0" or right_range=="0":
                print("error: invalid range(zero). {}".format(arg))
                _usage()
            # 额外调整（左侧为空）
            #if left_range=="": left_range = "1"
            ranges_list.append("{}-{}".format(left_range, right_range))
        input_ranges = ",".join(ranges_list)
    else:
        print("error: invalid format. {}".format(arg))
        _usage()
    return (input_file, input_ranges)

def _args_parser(args):
    """
    传入参数解析
    """
    input_files, output_file = [], "merged.pdf"
    if len(args)>0:
        output_flag = False
        for item in args:
            # 如果参数项为-o或者-O，表示其后参数项为输出文件名
            if item=="-o" or item=="-O":
                output_flag = True
                continue
            # 如果输出文件项标志为真，表示该参数项为输出文件项
            if output_flag==True:
                output_file = item
                output_flag = False
                continue
            # 接下来解析参数中的输入文件项
            input_item = _input_parser(item)
            input_files.append(input_item)
    else:
        _usage()
    return input_files, output_file

def _check_args(input_files, output_file):
    """
    检查解析后的传入参数

    检查输入文件存在，以及输出目录存在。
    """
    # 输入文件数应该大于0
    if len(input_files)==0:
        print("error: input is null.")
        sys.exit(-101)
    # 检查所有的输入文件
    for input_item in input_files:
        input_file, _ = input_item
        # 检查输入文件是否存在
        if not os.path.isfile(input_file):
            print("error: file not exists. {}".format(input_file))
            sys.exit(-102)
        # 检查输入文件是否为pdf
        if not ispdf(input_file):
            print("error: only use pdf. {}".format(input_file))
            sys.exit(-103)
    # 输出文件的目录应该存在或为当前目录
    output_path, _ = os.path.split(abspath(output_file))
    if not(output_path=="" or os.path.isdir(output_path)):
        print("error: output dir not exists. {}".format(output_file))
        sys.exit(-104)

def _merge_pdf(input_files, output_file):
    """
    合并处理
    """
    merger = PdfFileMerger()
    # 循环处理输入文件
    for input_file, input_ranges in input_files:
        print("[debug] reading {} ...".format(input_file))
        input_handle = open(input_file, "rb")
        # 额外处理，获取实际页数
        input_reader = PdfFileReader(input_handle)
        input_numpages = input_reader.getNumPages()
        # 多段循环处理
        for input_range in input_ranges.split(","):
            print("[debug] range {} ...".format(input_range))
            # 直接处理全文合并
            if input_range=="" or input_range=="-" or input_range=="1-":
                merger.append(input_handle)
                continue
            # 开始范围处理
            left_range, right_range = input_range.split("-")
            # 异常值调整（空值）
            if left_range=="": left_range = 1
            if right_range=="": right_range = input_numpages
            # 转换为整数
            left_range, right_range = int(left_range), int(right_range)
            # 异常值检查（超出实际页面范围）
            if left_range>input_numpages or right_range>input_numpages:
                print("error: out of range.")
                return -1
            # 顺序抽取的处理
            if left_range<=right_range:
                # pages参数从0开始
                begin_page = left_range - 1
                end_page = right_range
                merger.append(fileobj=input_handle, pages=(begin_page,end_page,1))
            # 逆序抽取的处理
            elif left_range>right_range:
                # bug: 逆序抽取错误
                # pages参数从0开始
                begin_page = right_range - 1
                end_page = left_range
                merger.append(fileobj=input_handle, pages=(begin_page,end_page,-1))
    # 写入输出文件
    print("[debug] writing {} ...".format(output_file))
    output_handle = open(output_file, "wb")
    merger.write(output_handle)
    merger.close()
    print("[debug] ok")
    return 0

def _main(*argv, **kwargs):
    """
    main()
    :return: exit code
    """    
    # 解析命令行参数
    args = list(*argv)[1:]
    input_files, output_file = _args_parser(args)
    # 参数有效性检查
    _check_args(input_files, output_file)
    # 执行合并
    ret = _merge_pdf(input_files, output_file)
    # 返回
    return ret

if __name__=="__main__":
    sys.exit(_main(sys.argv))
