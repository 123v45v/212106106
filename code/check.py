import os
from config import conn

cur = conn.cursor()


def is_existed(username, password):  # 账号密码验证
    sql = "SELECT * FROM user WHERE username ='%s' and password ='%s'" % (username, password)
    conn.ping(reconnect=True)
    cur.execute(sql)
    conn.commit()
    result = cur.fetchall()
    if (len(result) == 0):
        return False
    else:
        return True


def exist_user(username):  # 只验证账号（即密码错误的情况）
    sql = "SELECT * FROM user WHERE username ='%s'" % (username)
    conn.ping(reconnect=True)
    cur.execute(sql)
    conn.commit()
    result = cur.fetchall()
    if (len(result) == 0):
        return False
    else:
        return True


def get_user_id(username):  # 根据用户登录的username与获取user_id，为后续修改信息做准备
    sql = "SELECT user_id FROM user WHERE username ='%s'"
    conn.ping(reconnect=True)
    cur.execute(sql % (username))
    conn.commit()
    result = cur.fetchall()
    return result[0]  # 返回第一个结果的 id 字段


def add_user(username, password):  # 注册时添加用户
    sql = "INSERT INTO user(username, password) VALUES ('%s','%s')" % (username, password)
    cur.execute(sql)
    conn.commit()
    conn.close()


def update_user_info(user_id, nickname, school_name, personal_intro, age, gender):  # 修改信息
    sql = """
	        UPDATE user
	        SET nickname = %s, school_name = %s, personal_intro = %s, age = %s, gender = %s
	        WHERE user_id = %s
	    """
    conn.ping(reconnect=True)
    cur.execute(sql, (nickname, school_name, personal_intro, age, gender, user_id))
    conn.commit()  # 这里之所以不关闭数据库是因为为了确保待会退出查看修改后的信息不会报错(即保证连接)


def shequ(user_id):#存储风格迁移后的图片，在社区中再把存储的罗列出来就实现图片分享功能
    file_path = os.path.join(os.path.dirname(__file__), 'output', '20.jpg')
    with open(file_path, 'rb') as image_file:
        image_data = image_file.read()
    sql = "UPDATE user SET image = %s WHERE user_id = %s"
    conn.ping(reconnect=True)
    cur.execute(sql, (image_data,user_id))
    conn.commit()

