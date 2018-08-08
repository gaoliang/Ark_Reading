import time

from book import Book


def timer(func):
    def function_timer(*args, **kwargs):
        start = time.time()
        value = func(*args, **kwargs)
        end = time.time()
        runtime = end - start
        msg = "The runtime for {func} took {time} seconds to complete"
        print(msg.format(func=func.__name__, time=runtime))
        return value

    return function_timer


@timer
def benchmark_get():
    for i in range(100001, 100101):
        Book.get(i)


@timer
def benchmark_create():
    for i in range(100):
        Book.create(
            title='awesome_title',
            author='awesome_author',
            price=i,
            saleable=1
        )


@timer
def benchmark_update():
    book = Book.get(100001)
    for i in range(100):
        book.update(
            title='awesome_title',
            author='awesome_author',
            price=i,
            saleable=1
        )


@timer
def benchmark_get_multi_by_author():
    for i in range(10):
        list(Book.get_multi_by_author(author='author'))


@timer
def benchmark_search():
    for i in range(10):
        Book.search(query='awesome', min_price=0, max_price=300, start=0, limit=10)


if __name__ == "__main__":
    benchmark_create()
    benchmark_update()
    benchmark_get()
    benchmark_get_multi_by_author()
    benchmark_search()
