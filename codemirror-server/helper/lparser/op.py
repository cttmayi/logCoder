import os
from helper.lparser.basic.file import file_read
from helper.lparser.status import OP, ARG
from helper.lparser.utils.utils import get_modules, import_module


def op_reset(file):
    regex_full_list = file_read(file)

    op_map = []
    for name, pattern, info, args in regex_full_list:
        args_ARG = []
        for k, v in args.items():
            args_ARG.append(ARG(k, v))
        op_map.append(
            OP(name, pattern, info=info,
                args=args))

    return op_map


# =========================================================================

def get_op_name(id, op_map):
    return op_map[id].name

def get_op_pattern(id, op_map):
    return op_map[id].pattern

def get_op_arguments(id, op_map):
    return op_map[id].arguments

def get_op_func(id, op_map):
    return op_map[id].func

def get_op_func_init(id, op_map):
    return op_map[id].func_init


def get_op_infos(op_map):
    ret = {}

    for op in op_map:
        if op.name not in ret:
            info = op.op_info()
            if info is not None:
                ret[op.name] = info
    return [ op_info for op_info in ret.values()]


