import time
import unittest

from book import Book


class TestBook(unittest.TestCase):

    def test_create(self):
        last_id = int(Book.last().id)
        data = dict(
            title='awesome_title',
            author='awesome_author',
            price=1997,
            saleable=1
        )
        book = Book.create(**data)
        self.assertEqual(book.id, last_id + 1)

        # 测试是否成的写入了文件
        with open(Book.__filename__, encoding='utf-8') as f:
            self.assertEqual(f.readlines()[-1].strip(), str(book))

    def test_get(self):
        book = Book.get(id=100001)
        self.assertEqual(int(book.id), 100001)
        self.assertEqual(book.title, 'The Outskirts Of Poverty: And Sad Many A')
        self.assertEqual(book.author, 'Barry Unsworth')
        self.assertEqual(int(book.price), 290)
        self.assertEqual(int(book.saleable), 1)
        assert book

    def test_update(self):
        book = Book.get(id=100002)
        book.update(
            title='new_title',
            author='new_author',
            price=102,
            saleable=0
        )

        # 测试是否成功写入了文件
        with open(Book.__filename__, encoding='utf-8') as f:
            self.assertEqual(f.readlines()[2].strip(), str(book))

    def test_get_multi_by_author(self):
        author = 'awesome_author_{}'.format(time.time())
        for i in range(3):
            Book.create(
                title='masterpiece_{}'.format(i + 1),
                author=author,
                price=99 * (i + 1),
                saleable=1
            )
        self.assertEqual(len(list(Book.get_multi_by_author(author=author))), 3)

    def test_search(self):
        query = 'awesome_{}'.format(time.time())
        Book.create(
            title='xxx{}xxx'.format(query),
            author='not_match',
            price=100,
            saleable=1
        )
        Book.create(
            title='xxx{}xxx'.format(query),
            author='xxx{}xxx'.format(query),
            price=100,
            saleable=1
        )
        Book.create(
            title='not_match',
            author='xxx{}xxx'.format(query),
            price=100,
            saleable=1
        )
        # 测试排序
        books = Book.search(query=query, min_price=0, max_price=300, start=0, limit=10)
        self.assertEqual(len(books), 3)
        self.assertIn(query, books[0].title)
        self.assertIn(query, books[0].author)
        self.assertNotIn(query, books[1].author)
        self.assertNotIn(query, books[2].title)

        # 测试价格限制
        books = Book.search(query=query, min_price=200, max_price=300, start=0, limit=10)
        self.assertEqual(len(books), 0)

        # 测试分页
        books = Book.search(query=query, min_price=0, max_price=300, start=0, limit=2)
        self.assertEqual(len(books), 2)


if __name__ == '__main__':
    unittest.main()
