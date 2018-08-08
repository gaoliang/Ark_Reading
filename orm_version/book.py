from orm_version.orm import TSVModel, IntegerField, CharField


class Book(TSVModel):
    __filename__ = 'book.tsv'

    id = IntegerField(column_name='ID', index=0, primary_key=True)
    title = CharField(column_name='Title', index=1)
    author = CharField(column_name='Author', index=2)
    price = IntegerField(column_name='Price', index=3)
    saleable = IntegerField(column_name='Saleable', index=4)

    @classmethod
    def create(cls, title, author, price, saleable=1):
        book = Book(
            id=cls.last().id + 1 if cls.last() else 1,
            title=title,
            author=author,
            price=price,
            saleable=saleable
        )
        book.save()
        book.line_number = Book.count()
        return book

    def update(self, title, author, price, saleable):
        self.title = title
        self.author = author
        self.price = price
        self.saleable = saleable
        self.save()

    @classmethod
    def get(cls, id):
        return cls.get_by_pk(id)

    @classmethod
    def get_multi_by_author(cls, author):
        for book in cls.all():
            if book.author == author:
                yield book

    @classmethod
    def search(cls, query, min_price=None, max_price=None, start=0, limit=30):
        all_match = []
        title_match = []
        author_match = []
        for book in cls.all():
            if book.saleable != 1:
                continue
            if min_price and book.price < min_price:
                continue
            if max_price and book.price > max_price:
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
