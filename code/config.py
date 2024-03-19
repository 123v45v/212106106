import pymysql

conn = pymysql.connect(#数据库基本配置
        host='localhost',
        port=3306,
        user='root',
        password='123456',
        database='test'
    )
