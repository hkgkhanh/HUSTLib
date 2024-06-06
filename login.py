from flask import Flask, render_template, request
import psycopg2
import psycopg2.extras 


app = Flask(__name__)





@app.route('/login_page')
def login_page():
    return render_template('login.html')

@app.route('/')
def home_page():
    return render_template('index.html')

@app.route('/signup_page')
def signup_page():
    return render_template('signup.html')

@app.route('/search_page')
def search_page():
    return render_template('search_book.html')

@app.route('/search_user_page')
def search_user_page():
    return render_template('search_user.html')

@app.route('/search_group_page')
def chat_group_page():
    return render_template('search_group.html')

@app.route('/chat_group_page')
def search_group_page():
    return render_template('group.html')

@app.route('/cart_page')
def cart_page():
    return render_template('cart.html')

@app.route('/profile_page')
def profile_page():
    return render_template('profile.html')

@app.route('/profile_temp_page')
def profile_temp_page():
    return render_template('profile_temp.html')

@app.route('/rent_manage_page')
def rent_manage_page():
    return render_template('rent_manage.html')

@app.route('/book_info_page')
def book_info_page():
    return render_template('book_info.html')


@app.route('/book_manage_page')
def book_manage_page():
    return render_template('book_manage.html')

@app.route('/process_login', methods=['POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        # Xử lý dữ liệu email và password ở đây
       
        hostname = 'localhost'
        database = 'hust_lib'
        username = 'postgres'
        pwd = 'skadi123'
        port_id = 5432

        # Khởi tạo các biến kết nối và con trỏ
        conn = None
        cur = None

        try:
            # Kết nối đến cơ sở dữ liệu
            conn = psycopg2.connect(
                host=hostname,
                dbname=database,
                user=username,
                password=pwd,
                port=port_id
            )

            # Sử dụng con trỏ với kiểu trả về là từ điển (DictCursor)
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                # Thực thi câu lệnh SQL để kiểm tra thông tin đăng nhập
                cur.execute('SELECT * FROM Person WHERE Email = %s AND Password = %s', (email, password))
                user = cur.fetchone()
                if user:
                    # Xử lý khi đăng nhập thành công
                    return "Login success!"
                else:
                    # Xử lý khi đăng nhập không thành công
                    return "Invalid email or password. Please try again."

        except Exception as error:
            # In ra lỗi nếu có bất kỳ lỗi nào xảy ra trong quá trình thực thi mã
            print(error)

        finally:
            # Đóng kết nối đến cơ sở dữ liệu sau khi hoàn thành công việc
            if conn is not None:
                conn.close()

if __name__ == '__main__':
    app.run(debug=True)

