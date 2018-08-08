## 两个版本
两个版本均基于python3
### 1. quick_version
直接针对问题的版本，抽象层次较低，速度相对较快。

### 2. orm_version
进行了适当的抽象， 实现了一个简单的基于csv或tsv文件的ORM类， 可以更好的支持各种格式和内容的csv或tsv文件。但速度相对较慢。

## 文件清单
- book.py: 主程序
- orm.py: 实现的一个简单的基于tsv文件或csv文件后端的orm模型
- benchmark.py: 性能测试
- test_book.py: 单元测试