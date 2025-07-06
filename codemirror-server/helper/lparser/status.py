import helper.lparser.conf as conf
import traceback


class ARG:
    def __init__(self, name, info=None, pos=None):
        self.name = name
        self.position = pos
        self.infomation = info

class OP:
    def __init__(self, name, pattern, func_init=None, func=None, args=[], info=None):
        self.name = name
        self.func_init = func_init if func_init is None or isinstance(func_init, list) else [func_init]
        self.func = func if func is None or isinstance(func, list) else [func]
        self.arguments = []
        self.arguments_info = []
        self.set_arguments(args)
        self.pattern = pattern
        self.infomation = info


    def set_arguments(self, args:list):
        pos = 0
        for arg in args:
            pos = arg.position if isinstance(arg, ARG) and arg.position is not None else len(self.arguments)
            self.set_argument(arg, pos)

    def set_argument(self, arg, pos):
        if pos >= len(self.arguments):
            self.arguments.extend(['_'] * (pos - len(self.arguments) + 1))
            self.arguments_info.extend([None] * (pos - len(self.arguments_info) + 1))
        if isinstance(arg, ARG):
            self.arguments[pos] = arg.name
            self.arguments_info[pos] = arg.infomation
        else:
            self.arguments[pos] = arg
            self.arguments_info[pos] = None

    def op_info(self):
        if self.infomation is not None:
            infomation = [f'{self.name}: {self.infomation}']
            if any(info is not None for info in self.arguments_info):
                infomation.append("参数说明如下")
                for arg, info in zip(self.arguments, self.arguments_info):
                    if info is not None:
                        infomation.append(f'- {arg}: {info}')
            
            return '\n'.join(infomation)
        return None

    def __str__(self):
        return self.name



class Error:
    CRITICAL = 'Critical'
    ERROR = 'Error'
    WARNING = 'Warning'
    INFO = 'Info'
    LEVELS = [CRITICAL, ERROR, WARNING, INFO]

    def __init__(self, status, msg, level=ERROR):
        self._status = status
        self.line = status.LINE
        self.msg = msg
        self.level = level
        self.related_lines = set()
        self.related_lines.add(self.line)

    def __enter__(self):
        self._status.set_trace_error(self)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self._status.set_trace_error(None)
        if conf.DEBUG and exc_type is not None:
            print('Type Error:', exc_val)
            print('Traceback (most recent call last):')
            for trace in traceback.format_tb(exc_tb):
                print(trace)
        return True

    def add_related_line(self, line):
        if isinstance(line, int):
            self.related_lines.add(line)

    def __str__(self):
        return self.get_error_msg()

    def get_error_msg(self, log_df = None):
        related_lines = sorted(self.related_lines)
        related_lines = [line for line in related_lines if line >= 0]
        if log_df is not None:
            return f'====== {self.level} at line {self.line}: {self.msg} ======\n{log_df.loc[related_lines]}'
        else:
            return f'====== {self.level} at line {self.line}: {self.msg} ======\nRelated lines: {related_lines}\n'

class Value:
    def __init__(self, status, value=None):
        self._status = status  # 存储status属性
        self.value = value      # 存储任意类型的值
        self.timestamp = status.TIMESTAMP    # 存储timestamp属性
        self.line = status.LINE      # 存储line属性
    
    def _add_related_line(self, line):
        if self._status.error_monitor is not None:
            self._status.error_monitor.add_related_line(line)

    def __hash__(self):
        return hash(self.value)
    
    def __bool__(self):
        self._status._add_related_line(self.line)
        return bool(self.value)

    def __set__(self, key, value):
        self.value[key] = value

    def __eq__(self, other):
        self._add_related_line(self.line)
        if isinstance(other, Value):
            return self.value == other.value
        return self.value == other

    def __ne__(self, other):
        self._add_related_line(self.line)
        return not (self == other)

    def __ge__(self, other):
        self._add_related_line(self.line)
        if isinstance(other, Value):
            return self.value >= other.value
        return self.value >= other

    def __le__(self, other):
        self._add_related_line(self.line)
        if isinstance(other, Value):
            return self.value <= other.value
        return self.value <= other

    def __gt__(self, other):
        self._add_related_line(self.line)
        if isinstance(other, Value):
            return self.value > other.value
        return self.value > other

    def __lt__(self, other):
        self._add_related_line(self.line)
        if isinstance(other, Value):
            return self.value < other.value
        return self.value < other
    
    def __add__(self, other):
        return Value(self._status, self.value + other)

    __radd__ = __add__  # 支持反向加法（如 other + self.value）

    def __sub__(self, other):
        return Value(self._status, self.value - other)

    __rsub__ = __sub__  # 支持反向减法（如 other - self.value）

    # 代理容器操作（如字典/列表的下标访问）
    def __getitem__(self, key):
        self._add_related_line(self.line)
        return self.value[key]

    # 代理其他常见容器方法（可选）
    def __iter__(self):
        return iter(self.value)

    def __len__(self):
        self._add_related_line(self.line)
        return len(self.value)

    def __contains__(self, item):
        self._add_related_line(self.line)
        return item in self.value

    def __repr__(self):
        self._add_related_line(self.line)
        return repr(self.value)  # 直接返回 value 的表示

    def __str__(self):
        self._add_related_line(self.line)
        return str(self.value)

    # 动态代理未定义的操作到 self.value（例如属性访问、方法调用）
    def __getattr__(self, name):
        self._add_related_line(self.line)
        return getattr(self.value, name)


class Status:
    def __init__(self):
        self._value_list = set()
        self._current_timestamp = 0
        self._current_line = -1
        self.__setattr_func__ = None
        self.__getattribute_func__ = None

        self.error_monitor:Error = None
        self.error_recoder = []
        self._golbal_status:Status = None

        self.enable_attribute__mode()
        self.init_attribute()
        self.disable_attribute_mode()

    def init_attribute(self):
        raise NotImplementedError

    def end_checker(self) -> Error:
        return None
    
    def op_looper(self, op):
        pass

    def raise_error(self, error:Error=None):
        if error is None:
            error = self.error_monitor
        self.error_recoder.append(error)

    def get_error(self):
        return self.error_recoder

    def reset_error(self):
        self.error_recoder = []

    def set_global_status(self, global_status):
        self._golbal_status = global_status

    def set_trace_error(self, error):
        self.error_monitor = error
        if self._golbal_status is not None:
            self._golbal_status.set_trace_error(error)

    def set_current_info(self, timestamp, line_number):
        self._current_timestamp = timestamp
        self._current_line = line_number

    def __getattr__(self, name):
        if self._golbal_status is not None:
            return getattr(self._golbal_status, name)
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")

    def get_status(self, value_list, dict_or_list, name=None):
        values = {}
        timestamp = {}
        for key in value_list:
            new_name = [name, str(key)] if name else [str(key)]
            new_name = '.'.join(new_name)
            if isinstance(dict_or_list[key], Value):
                values[new_name] = dict_or_list[key].value
                timestamp[new_name] = dict_or_list[key].timestamp
            elif isinstance(dict_or_list[key], dict):
                v, m = self.get_status(dict_or_list[key].keys(), dict_or_list[key], new_name)
                values.update(v)
                timestamp.update(m)
            elif isinstance(dict_or_list[key], list):
                v, m = self.get_status(range(len(dict_or_list[key])), dict_or_list[key], new_name)
                values.update(v)
                timestamp.update(m)
            else:
                values[new_name] = dict_or_list[key]
        return values, timestamp


    def get_all_status(self):
        values, timestamp = self.get_status(self._value_list, self.__dict__)        
        # return {'values': values, 'timestamp': timestamp}
        return {'values': values}

######################################################################
    @property
    def TIMESTAMP(self):
        return self._current_timestamp

    @property
    def LINE(self):
        return self._current_line
    
    def DURATION(self, value:Value):
        if isinstance(value, Value):
            if self.error_monitor is not None:
                self.error_monitor.add_related_line(value.line)
                self.error_monitor.add_related_line(self.LINE)
            ret = self._current_timestamp - value.timestamp
        else:
            ret = self._current_timestamp
        return ret

#####################################################################
    # 关闭保护模式，允许动态添加属性
    def enable_attribute__mode(self):
        self.__setattr_func__ = self.__attribute_setattr__

    # 打开保护模式，禁止动态添加属性
    def disable_attribute_mode(self):
        self.__setattr_func__ = self.__protected_setattr__

    def __setattr__(self, name, value):
        if self.__dict__.get('__setattr_func__') is not None:
            self.__setattr_func__(name, value)
        else:
            super().__setattr__(name, value)

    def __attribute_setattr__(self, name, value):
        if name not in self.__dict__:
            self._value_list.add(name)
        super().__setattr__(name, value)

    def __protected_setattr__(self, name, value):
        # if name not in self.__dict__:
        #     raise AttributeError(f"Cannot set new attribute '{name}' dynamically")
        super().__setattr__(name, value)
