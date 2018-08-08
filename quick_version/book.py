import linecache
import os
from collections import namedtuple
from shutil import move
from tempfile import mkstemp


def lines(filename):
    with open(filename, "r", encoding='utf-8') as f:
        return f.readlines()


def lines_without_header(filename):
    all_lines = lines(filename)
    del all_lines[0]
    return all_lines


Model = namedtuple('Data', ['id', 'title', 'author', 'price', 'saleable'])


class Book(Model):
    __filename__ = 'book.tsv'
    SEPARATOR = '\t'

    @classmethod
    def all(cls):
        for line in lines_without_header(cls.__filename__):
            yield Book(*line.strip().split(cls.SEPARATOR))

    @classmethod
    def create_from_str(cls, string):
        return Book(*string.strip().split(cls.SEPARATOR))

    def __str__(self):
        return self.SEPARATOR.join(map(str, self))

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
    def create(cls, title, author, price, saleable=1):
        last_book = cls.last()
        book = Book(
            id=int(last_book.id) + 1,
            title=title,
            author=author,
            price=price,
            saleable=saleable
        )
        with open(cls.__filename__, 'a', encoding='utf-8') as f:
            f.write(str(book) + '\n')
        return book

    def update(self, title, author, price, saleable):
        """
        更新, 注意自身不会更改，更新后的对象为返回值
        """
        if not self.id:
            raise ValueError('instance has no id')
        updated_book = Book(
            id=self.id,
            title=title,
            author=author,
            price=price,
            saleable=saleable
        )

        fh, target_file_path = mkstemp()
        with open(target_file_path, 'w', encoding='utf-8') as target_file, \
                open(self.__filename__, 'r', encoding='utf-8') as source_file:
            for line_number, line in enumerate(source_file):
                if line_number == 0 or int(line.split()[0]) != updated_book.id:
                    target_file.write(line)
                else:
                    target_file.write(str(updated_book) + '\n')
        os.remove(self.__filename__)
        move(target_file_path, self.__filename__)

    @classmethod
    def get(cls, id):
        line_number = id - 100000 + 1
        line = linecache.getline(cls.__filename__, line_number)
        if not line:
            raise ValueError('can not get book with id: {}'.format(id))
        return cls.create_from_str(line)

    @classmethod
    def get_multi_by_author(cls, author):
        for book in Book.all():
            if book.author == author:
                yield book

    @classmethod
    def search(cls, query, min_price=None, max_price=None, start=0, limit=30):
        all_match = []
        title_match = []
        author_match = []
        for book in cls.all():
            if int(book.saleable) != 1:
                continue
            price = int(book.price)
            if min_price and price < min_price:
                continue
            if max_price and price > max_price:
                continue
            if query in book.title and query in book.author:
                all_match.append(book)
            elif query in book.title and query not in book.author:
                title_match.append(book)
            elif query not in book.title and query in book.author:
                author_match.append(book)

        all_match.extend(title_match)
        all_match.extend(author_match)
        return all_match[start: start + limit]
