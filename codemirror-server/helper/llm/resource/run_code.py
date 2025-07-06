from helper.lparser import conf
conf.DEBUG = False
from helper.lparser.parser import LogParser
from helper.lparser.op import op_reset


format_file = None
### <FORMAT_FILE> ###

op_maps = op_reset(format_file)

def tool_parser(path, looper, end=None):
    lp:LogParser = LogParser(path, op_maps, looper=looper, end=end)
    logs = lp.transfor_to_df()
    if logs is None:
        raise Exception('log格式无法识别')

    ops = lp.transfor_to_op(logs)
    return lp.op_execute(ops)

files = None
file = None
### <FILES> ###

def looper1(**kwargs):
    raise Exception('未定义looper1函数')

def looper2(**kwargs):
    pass

def end(**kwargs):
    raise Exception('未定义end函数')

### <CODE> ###



if file is None:
    if files is None or len(files) == 0:
        raise Exception('未上传log文件')

    file = files[-1]
result = tool_parser(file, looper=[looper1, looper2], end=end)
