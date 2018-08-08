import logging
import os
from collections import OrderedDict
from shutil import move
from tempfile import mkstemp

logging.basicConfig(level=logging.DEBUG)


def lines(filename):
    with open(filename, "r", encoding='utf-8') as f:
        return f.readlines()


def lines_without_header(filename):
    all_lines = lines(filename)
    del all_lines[0]
    return all_lines


class Field:
    """
    字段类型的基类， 支持设置为自增主键和调整保存在文件中的顺序
    """

    def __init__(self, column_name, index, primary_key):
        """
        :param column_name: 在csv或tsv文件中的列名
        :param index: 文件中的第几列，从0开始
        :param primary_key: 是否为自增主键
        """
        self.column_name = column_name
        self.index = index
        self.primary_key = primary_key

    def adapt(self, value):
        return value

    def python_value(self, value):
        return value if value is None else self.adapt(value)


class CharField(Field):
    def __init__(self, column_name, index, primary_key=False):
        super(CharField, self).__init__(column_name, index, primary_key)


class IntegerField(Field):
    def __init__(self, column_name, index, primary_key=False):
        super(IntegerField, self).__init__(column_name, index, primary_key)

    adapt = int


class TSVModelMetaclass(type):
    """
    Model的元类
    """

    def __new__(cls, name, bases, attrs):
        # 排除Model类本身:
        if name == 'Model':
            return type.__new__(cls, name, bases, attrs)
        # 获取文件名:
        filename = attrs.get('__filename__', None) or name.lower() + '.tsv'
        logging.info('found model: %s (filename: %s)' % (name, filename))

        # 获取所有的Field
        mappings = OrderedDict()
        primary_key = None
        for k, v in attrs.items():
            if isinstance(v, Field):
                logging.info('found mapping: %s ==> %s' % (k, v))
                mappings[k] = v
                if v.primary_key:
                    if primary_key:
                        raise ValueError('A model can only have one primary_key')
                    primary_key = k
        for k in mappings.keys():
            attrs.pop(k)
        # fields 按照index排序
        mappings = OrderedDict(sorted(mappings.items(), key=lambda x: x[1].index))
        attrs['__mappings__'] = mappings
        attrs['__filename__'] = filename
        attrs['__pk__'] = primary_key
        return type.__new__(cls, name, bases, attrs)


class TSVModel(dict, metaclass=TSVModelMetaclass):
    __mappings__ = OrderedDict()
    __filename__ = ''
    SEPARATOR = '\t'

    def __init__(self, line_number=None, **kwargs):
        self.line_number = line_number
        super(TSVModel, self).__init__(**kwargs)

    def __str__(self):
        values = [str(self[key]) for key in self.__mappings__.keys()]
        return self.SEPARATOR.join(values)

    def __getattr__(self, key):
        try:
            return self.__mappings__[key].python_value(self[key])

        except KeyError:
            raise AttributeError(r"'Model' object has no attribute '%s'" % key)

    def __setattr__(self, key, value):
        if key in self.__mappings__:
            self[key] = value
        else:
            super(TSVModel, self).__setattr__(key, value)

    def save(self):
        if self.line_number:  # 已经知道行号了, 更新
            self.update_to_file()
        else:  # 没有行号，新建
            with open(self.__filename__, 'a') as f:
                f.write(str(self) + '\n')

    @classmethod
    def header_string(cls):
        """根据Field生成csv文件的header"""
        return cls.SEPARATOR.join(field.column_name for field in cls.__mappings__.values())

    @classmethod
    def create_from_str(cls, record_str):
        """根据instance的数据，生成csv文件的一行"""
        instance = cls()
        for (key, field), value in zip(cls.__mappings__.items(), record_str.strip().split(cls.SEPARATOR)):
            instance[key] = field.python_value(str(value))
        return instance

    @classmethod
    def init_file(cls):
        """
        初始化文件，包含文件不存在，空文件处理和文件格式检查
        """
        correct_header = cls.header_string()
        try:
            # 文件存在， 检查文件header是否正确
            file_header = lines(filename=cls.__filename__)[0].strip()
            if file_header != correct_header:
                raise ValueError('invalid file header')
        except (IOError, IndexError):
            # 文件不存在或文件为空
            with open(cls.__filename__, "w") as f:
                f.write(correct_header + "\n")
                f.close()

    @classmethod
    def last(cls):
        """返回最后一条记录"""
        try:
            with open(cls.__filename__, "rb") as f:
                f.seek(-2, os.SEEK_END)
                while f.read(1) != b"\n":
                    f.seek(-2, os.SEEK_CUR)
                last_line = f.readline().decode()
                return cls.create_from_str(last_line)
        except OSError:
            return None

    @classmethod
    def all(cls):
        """所有的记录"""
        return (cls.create_from_str(line) for line in lines_without_header(cls.__filename__))

    @classmethod
    def count(cls):
        """
        统计记录的行数
        :return: int 记录行数
        """
        return len(lines_without_header(filename=cls.__filename__))

    def update_to_file(self):
        """将一条记录的更改信息同步到文件中"""
        fh, target_file_path = mkstemp()
        with open(target_file_path, 'w', encoding='utf-8') as target_file, \
                open(self.__filename__, 'r', encoding='utf-8') as source_file:
            for index, line in enumerate(source_file):
                if index == self.line_number:
                    target_file.write(str(self) + '\n')
                else:
                    target_file.write(line)
        os.remove(self.__filename__)
        move(target_file_path, self.__filename__)

    @classmethod
    def get_by_line_number(cls, line_number):
        """
        根据行号获取一条记录
        :param line_number: 行号
        :return: Model instance
        """
        with open(cls.__filename__, 'r', encoding='utf-8') as f:
            line = f.readlines()[line_number]
            instance = cls.create_from_str(line)
            instance.line_number = 1
            return instance

    @classmethod
    def get_by_pk(cls, pk):
        """
        根据主键获取一条记录
        :param pk: 主键值，注意这里默认pk值是auto_increment的
        :return: Model instance
        """
        pk_field = cls.__mappings__[cls.__pk__]
        for index, line in enumerate(lines_without_header(cls.__filename__)):
            if pk_field.python_value(line.split(cls.SEPARATOR)[pk_field.index]) == pk:
                instance = cls.create_from_str(line)
                instance.line_number = index + 1
                return instance
