import pandas as pd
import logging
import re
import inspect
import helper.lparser.utils.re_exp2 as re_exp
from helper.lparser.parser.android import android_parser, debug_parser, PAESER_MAIN_REGEX
from helper.lparser.op import get_op_func, get_op_name, get_op_func_init, get_op_arguments, get_op_pattern

PARSER_FORMAT = ['type', 'date', 'time', 'timestamp', 'pid', 'tid', 'level', 'tag', 'msg']


PARSER_MAP = {
    # 'debug': (debug_parser, PAESER_MAIN_REGEX),
    'android':  (android_parser, PAESER_MAIN_REGEX),
}

class LogParser():
    def __init__(self, path, op_maps, type=None, looper=None, end=None):
        self.path = path
        self.type = type
        self.op_maps = op_maps
        self.logs:pd.DataFrame = None
        self.op_result = []
        self.matchers = {}
        self._parser = { k: p[0] for k, p in PARSER_MAP.items() }
        self._parser_regex = { k: p[1] for k, p in PARSER_MAP.items() }
        if isinstance(looper, list):
            self.loopers = looper
        elif looper is None:
            self.loopers = None
        else:
            self.loopers = [looper]

        self.end = end

        with open(self.path, errors='ignore') as fp:
            lines = fp.readlines()
            lines = [l.strip() for l in lines] # remove \n
        self.lines = lines

        if type is None:
            type = self.auto_detect_type(lines)
            if type is None:
                raise Exception('无法自动检测日志类型')
        self.type = type

        if isinstance(op_maps, dict) and type in op_maps:
            pattern_list = self.gen_pattern_list(op_maps[type])
            self.matchers[type] = re_exp.FormatMatcher(pattern_list)
        else:
            pattern_list = self.gen_pattern_list(op_maps)
            self.matchers[type] = re_exp.FormatMatcher(pattern_list)

    def auto_detect_type(self, lines):
        for k in self._parser_regex:
            regex = re.compile(self._parser_regex[k])
            count = 0
            for i in range(100):
                if i >= len(lines): break
                if regex.match(lines[i]):
                    count += 1
                    if count >= 10:
                        return k
        return None

    def gen_pattern_list(self, op_map:list, type_default=None):
        names = set()
        patterns = set()
        last_name = None
        pattern_list = []

        for opid in range(len(op_map)):
            name = get_op_name(opid, op_map)
            pattern = get_op_pattern(opid, op_map)
            arguments = get_op_arguments(opid, op_map)

            if pattern in patterns:
                raise Exception(f'OP_MAP PATTERN 重复: {pattern}' )
            patterns.add(pattern)

            pattern_list.append([pattern, arguments]) # PATTERN, ARGUMENTS
                # OP_MAP.append([type, name, func_init, func, arguments, pattern]) # TYPE, NAME, FUNC_INIT, FUNC, ARGUMENTS, PATTERN
        return pattern_list


    def transfor_to_df(self, ffilter=None):
        lines = self.lines
        type = self.type

        op_maps= self.op_maps 
        if isinstance(op_maps, list):
            op_maps = {type: op_maps}
        elif isinstance(op_maps, dict):
            op_maps = {type: op_maps[type]}
        self.op_maps = op_maps

        if type is None:
            logging.error('can not detect log type')
        else:
            logging.info('log type: {}'.format(type))
            parser = self._parser[type]
            self.logs = parser(lines)

            if ffilter is None:
                logs = self.logs.copy()
            else:
                logs = self.logs[self.logs.apply(ffilter, axis=1)]
            return logs
        return None

    def _op_transfer(self, log):
        matcher = self.matchers[log.type]
        r = matcher.match(log.msg)

        if r is not None:
            type = log.type
            line = log.name
            timestamp = log.timestamp
            name = get_op_name(r[0], self.op_maps[type])
            op = r[0]
            args = r[1]
            tid = log.tid
            tag = log.tag
            msg = log.msg

            op_f = {'type': type, 'line': line, 'timestamp': timestamp, 'tid': tid, 'tag': tag, 'msg': msg, 'opname': name, 'op': op, 'args': args, 'n': 1}

            # 通过op_by_tid来缓存的op_f， 延迟放入op_result
            op_f_last = self.op_by_tid.get(tid)
            if op_f_last is not None and op_f_last['opname'] == name and get_op_func(op, self.op_maps[type]) is None:
                    new_args = {}
                    for k in args:
                        if k not in op_f_last['args']:
                            new_args[k] = args[k]
                        else:
                            new_args[k + '_' + str(op_f_last['n'])] = args[k]
                    op_f_last['args'].update(new_args)
                    op_f_last['n'] += 1
            else:
                self.op_by_tid[tid] = op_f
                self.op_result.append(op_f)            

    def transfor_to_op(self, log_df:pd.DataFrame):
        self.op_by_tid = {}
        self.op_result = []
        log_df.apply(self._op_transfer, axis=1)
        df = pd.DataFrame(self.op_result)
        return df


    def _call_func(self, func, **kwargs):
        signature = inspect.signature(func)
        parameters = signature.parameters.keys()
        filtered_kwargs = {key: value for key, value in kwargs.items() if key in parameters}
        return func(**filtered_kwargs)

    def op_execute_looper(self, op_df:pd.DataFrame):
        logging.debug('====== op_execute looper ======')

        for looper in self.loopers:
            for _, row in op_df.iterrows():
                op = row['op']
                name = row['opname']
                args = row['args']
                type = row['type']
                line = row['line']
                timestamp = row['timestamp']
                tag = row['tag']
                tid = row['tid']
                msg = row['msg']
            
                self._call_func(looper, name=name, args=args, timestamp=timestamp, line=line, type=type, tag=tag, tid=tid, msg=msg)

        if self.end:
            return self.end()

        return

    def op_execute(self, op_df: pd.DataFrame):
        execute_method = self.op_execute_looper
        return execute_method(op_df)

