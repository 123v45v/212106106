from flask import Flask, render_template, request, send_file, redirect, url_for, session, g, make_response
from check import is_existed, exist_user, add_user, update_user_info, get_user_id,shequ
from config import conn
from functools import wraps
from train import NeuralStyleTransfer
from io import BytesIO
import settings
import utils
import os

cur = conn.cursor()
app = Flask(__name__)
app.secret_key = os.urandom(24)

app.config['UPLOAD_FOLDER'] = 'images'
app.config['OUTPUT_FOLDER'] = 'output'


def set_g_user_id(f):  # 这个函数是为了确保g对象从session获取到user_id
    @wraps(f)
    def decorated_function(*args, **kwargs):
        g.user_id = session.get('user_id')
        return f(*args, **kwargs)

    return decorated_function


@app.route('/')  # 直接定向到登录页面
def index():
    return redirect(url_for('user_login'))


@app.route('/user_login', methods=['GET', 'POST'])  # 登录页面的验证
def user_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if is_existed(username, password):
            user_id = get_user_id(username)  # 这三行是为了后面根据用户Id把修改后的信息存到对应的行里
            session['user_id'] = user_id
            g.user_id = user_id
            return redirect(url_for('zhuye'))
        elif exist_user(username):
            login_massage = "温馨提示：密码错误，请输入正确密码"
            return render_template('login.html', message=login_massage)
        else:
            login_massage = "温馨提示：不存在该用户，请先注册"
            return render_template('login.html', message=login_massage)
    return render_template('login.html')


@app.route("/regiser", methods=["GET", 'POST'])  # 注册页面的验证
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if exist_user(username):
            login_massage = "温馨提示：用户已存在，请直接登录"
            return render_template('register.html', message=login_massage)
        else:
            add_user(request.form['username'], request.form['password'])
            return redirect(url_for('user_login'))
    return render_template('register.html')


@app.route('/new_index', methods=['GET', 'POST'])  # 自定义风格迁移
def new_index():
    if request.method == 'POST':
        if request.method == 'POST' and 'input-image' in request.files and 'style-image' in request.files:#为了应对不同的请求
            content_image = request.files['input-image']
            style_image = request.files['style-image']
            if os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], 'content.jpg')):
                os.remove(os.path.join(app.config['UPLOAD_FOLDER'], 'content.jpg'))
            if os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], 'style.jpg')):
                os.remove(os.path.join(app.config['UPLOAD_FOLDER'], 'style.jpg'))
            content_image.save(os.path.join(app.config['UPLOAD_FOLDER'], 'content.jpg'))
            style_image.save(os.path.join(app.config['UPLOAD_FOLDER'], 'style.jpg'))
            nst = NeuralStyleTransfer()
            nst.train(20, settings.STEPS_PER_EPOCH)
            return render_template('index.html', output_image=True)
        else:
            return render_template('index.html')
    else:
        return render_template('index.html')


@app.route('/new_index2', methods=['GET', 'POST'])
def new_index2():
    if request.method == 'POST':
        if request.method == 'POST' and 'input-image' in request.files:
            content_image = request.files['input-image']
            style_image_name = request.form.get('style-image')
            if os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], 'content.jpg')):
                os.remove(os.path.join(app.config['UPLOAD_FOLDER'], 'content.jpg'))
            if os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], 'style.jpg')):
                os.remove(os.path.join(app.config['UPLOAD_FOLDER'], 'style.jpg'))
            content_image.save(os.path.join(app.config['UPLOAD_FOLDER'], 'content.jpg'))
            with open(os.path.join(app.config['UPLOAD_FOLDER'], 'style.jpg'), 'wb') as f:
                f.write(open(style_image_name, 'rb').read())
                nst = NeuralStyleTransfer()
                nst.train(20, settings.STEPS_PER_EPOCH)
            return render_template('index2.html', output_image=True)
        else:
            return render_template('index2.html')
    else:
        return render_template('index2.html')


@app.route('/zhuye')  # 登录成功后的主页面
def zhuye():
    return render_template('yemian.html')


@app.route('/abab')  # 风格迁移后的功能选择页面
def abab():
    return render_template('anniu.html')

@app.route('/wwdnb')  # 处理图片分享
@set_g_user_id
def wwdnb():
    user_id = g.user_id
    shequ(user_id)
    return redirect(url_for('new_index'))

@app.route('/pinglun')#图片分享，获取有Image数据的列
def pinglun():
    cur.execute("SELECT * FROM user WHERE image IS NOT NULL")
    users = cur.fetchall()
    return render_template('shequ.html', users=users)

@app.route('/image/<int:image_id>')#图像二进制数据转为图片
def get_image(image_id):
    sql = "SELECT image FROM user WHERE user_id = %s"
    with conn.cursor() as cursor:
        cursor.execute(sql, (image_id,))
        image_data = cursor.fetchone()
        if image_data:# 将二进制数据转换为图片流
            image_stream = BytesIO(image_data[0])
            response = make_response(send_file(image_stream, mimetype='image/jpg'))
            return response
        else:
            return "Image not found", 404


@app.route('/change', methods=["GET", 'POST'])  # 修改信息并保存在表中
@set_g_user_id
def change():
    if request.method == 'POST':
        user_id = g.user_id
        nickname = request.form.get('nickname')
        school_name = request.form.get('school_name')
        personal_intro = request.form.get('personal_intro')
        age = request.form.get('age')
        gender = request.form.get('gender')
        update_user_info(user_id, nickname, school_name, personal_intro, age, gender)
        return render_template('Web2.html', chenggong=True)
    return render_template('Web2.html')


@app.route('/geren')  # 与前端页面结合，根据id去数据库中获得对应信息，在页面上展示
@set_g_user_id
def geren():
    user_id = g.user_id  # 当前登录用户的ID
    sql = "SELECT nickname, school_name, personal_intro, age, gender FROM user WHERE user_id = %s"
    cur.execute(sql, (user_id,))
    result = cur.fetchone()
    if result:
        user = {
            'nickname': result[0],
            'school_name': result[1],
            'personal_intro': result[2],
            'age': result[3],
            'gender': result[4]
        }
    return render_template('Web.html', user=user)

@app.route('/output_image')  # 风格迁移将最终的结果进行展示
def output_image():
    return send_file('output/20.jpg', mimetype='image/jpg')


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8501, debug=True)
