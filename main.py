from flask import Flask, render_template, request, url_for, redirect, flash, session
import psycopg2
import re
from psycopg2.extras import RealDictCursor

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Đặt một khóa bí mật cho phiên làm việc

def get_db_connection():
    conn = psycopg2.connect(
        host='localhost',
        dbname='hust_lib',
        user='postgres',
        password='postgre',
        port=5432
    )
    return conn

@app.route('/login_page')
def login_page():
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('user_role', None)
    flash('You have been logged out.')
    return redirect(url_for('login_page'))

@app.route('/')
def home_page():
    
    
    return render_template('index.html')

@app.route('/signup_page')
def signup_page():
    return render_template('signup.html')

@app.route('/signup', methods=['POST'])
def signup():
    if request.method == 'POST':
        first_name = request.form['FirstName']
        last_name = request.form['LastName']
        address = request.form['Address']
        phone_number = request.form['PhoneNumber']
        email = request.form['Email']
        password = request.form['Password']
        dob = request.form['DOB']
        gender = request.form['Gender']
        role = request.form['Role']

        conn = None
        cur = None

        try:
            conn = get_db_connection()
            with conn.cursor() as cur:
                cur.execute('''
                    INSERT INTO Person (FirstName, LastName, Address, PhoneNumber, Email, Password, DOB, Gender, Role)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ''', (first_name, last_name, address, phone_number, email, password, dob, gender, role))
                conn.commit()
                return "Signup success!"
        except Exception as error:
            conn.rollback()
            print(error)
        finally:
            if cur:
                cur.close()
            if conn:
                conn.close()
        return "Signup fail!"




PER_PAGE = 9  # Số sách hiển thị mỗi trang
@app.route('/search_page', methods=['GET'])
def search_page():
    # Lấy trang hiện tại từ tham số truy vấn, mặc định là trang 1
    page = request.args.get('page', 1, type=int)

    # Tính toán offset cho trang hiện tại
    offset = (page - 1) * PER_PAGE

    # Kết nối tới cơ sở dữ liệu và tạo một cursor
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    # Danh sách các điều kiện WHERE và tham số cho truy vấn
    where_clauses = []
    params = []

    # Lấy các tham số tìm kiếm từ chuỗi truy vấn và thêm vào điều kiện WHERE nếu có
    title = request.args.get('title')
    if title:
        title = re.sub(r'\s+', ' ', title.strip())  # Loại bỏ khoảng trắng thừa
        where_clauses.append('TRIM(Book.Title) ILIKE TRIM(%s)')
        params.append('%' + title + '%')

    author = request.args.get('author')
    if author:
        author = re.sub(r'\s+', ' ', author.strip())  # Loại bỏ khoảng trắng thừa
        where_clauses.append('TRIM(Author.Full_Name) ILIKE TRIM(%s)')
        params.append('%' + author + '%')

    category = request.args.get('category')
    if category and category != '0':
        where_clauses.append('Book_Category.CategoryID = %s')
        params.append(category)

    publisher = request.args.get('publisher')
    if publisher and publisher != '0':
        where_clauses.append('Book.PublisherID = %s')
        params.append(publisher)

    publish_year = request.args.get('publish_year')
    if publish_year:
        where_clauses.append('Book.PublishYear = %s')
        params.append(publish_year)

    # Xây dựng câu truy vấn để đếm tổng số sách dựa trên các điều kiện tìm kiếm
    count_query = '''
        SELECT COUNT(DISTINCT Book.BookID)
        FROM Book
        INNER JOIN Book_Author ON Book.BookID = Book_Author.BookID
        INNER JOIN Author ON Book_Author.AuthorID = Author.AuthorID
        INNER JOIN Book_Category ON Book.BookID = Book_Category.BookID
        INNER JOIN Category ON Book_Category.CategoryID = Category.CategoryID
        INNER JOIN Publisher ON Book.PublisherID = Publisher.PublisherID
    '''
    if where_clauses:
        count_query += ' WHERE ' + ' AND '.join(where_clauses)

    # Thực thi câu truy vấn để đếm tổng số sách
    cur.execute(count_query, params)
    total_books = cur.fetchone()[0]

    # Tính toán tổng số trang
    total_pages = (total_books + PER_PAGE - 1) // PER_PAGE

    # Xây dựng câu truy vấn chính
    query = '''
        SELECT
            Book.Title, Book.BookID,
            string_agg(DISTINCT Author.Full_Name, ', ') AS Author
        FROM Book
        INNER JOIN Book_Author ON Book.BookID = Book_Author.BookID
        INNER JOIN Author ON Book_Author.AuthorID = Author.AuthorID
        INNER JOIN Book_Category ON Book.BookID = Book_Category.BookID
        INNER JOIN Category ON Book_Category.CategoryID = Category.CategoryID
        INNER JOIN Publisher ON Book.PublisherID = Publisher.PublisherID
    '''

    # Thêm các điều kiện WHERE vào câu truy vấn nếu có
    if where_clauses:
        query += ' WHERE ' + ' AND '.join(where_clauses)

    # Thêm GROUP BY và ORDER BY
    query += '''
        GROUP BY Book.BookID, Book.Title
        ORDER BY Book.BookID
    '''

    # Thêm giới hạn và offset cho phân trang
    query += ' LIMIT %s OFFSET %s'

    # Thêm giới hạn và offset vào params
    params.extend([PER_PAGE, offset])

    # Thực thi câu truy vấn để lấy sách
    cur.execute(query, params)
    books = cur.fetchall()

    # Lấy danh sách thể loại từ cơ sở dữ liệu
    cur.execute('SELECT CategoryID, CategoryName FROM Category')
    categories = cur.fetchall()

    # Lấy danh sách nhà xuất bản từ cơ sở dữ liệu
    cur.execute('SELECT PublisherID, Name FROM Publisher')
    publishers = cur.fetchall()

    # Đóng kết nối cơ sở dữ liệu
    cur.close()
    conn.close()

    # Render trang tìm kiếm với dữ liệu cần thiết
    return render_template('search_book.html', books=books, categories=categories, publishers=publishers,
                           current_page=page, total_pages=total_pages)


@app.route('/search_user_page', methods=['GET'])
def search_user_page():
    PER_PAGE = 30  # Số user hiển thị mỗi trang
    conn = None
    cur = None
    
    try:
        # Lấy trang hiện tại từ tham số truy vấn, mặc định là trang 1
        page = request.args.get('page', 1, type=int)

        # Tính toán offset cho trang hiện tại
        offset = (page - 1) * PER_PAGE    

        # Kết nối tới cơ sở dữ liệu và tạo một cursor
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        # Danh sách các điều kiện WHERE và tham số cho truy vấn
        where_clauses = []
        params = []

        # Lấy các tham số tìm kiếm từ chuỗi truy vấn và thêm vào điều kiện WHERE nếu có
        name = request.args.get('name')
        if name:
            name = re.sub(r'\s+', ' ', name.strip())  # Loại bỏ khoảng trắng thừa
            where_clauses.append('TRIM(CONCAT(Person.FirstName, \' \', Person.LastName)) ILIKE TRIM(%s)')
            params.append('%' + name + '%')
        
        id = request.args.get('id')
        if id:
            where_clauses.append('Person.PersonID = %s')
            params.append(id)
        
        phonenumber = request.args.get('phonenumber')
        if phonenumber:
            where_clauses.append('Person.PhoneNumber = %s')
            params.append(phonenumber)
            
        mail = request.args.get('mail')
        if mail:
            mail = re.sub(r'\s+', ' ', mail.strip())  # Loại bỏ khoảng trắng thừa
            where_clauses.append('TRIM(Person.Email) ILIKE TRIM(%s)')
            params.append('%' + mail + '%')
        
        # Xây dựng câu truy vấn để đếm tổng số user dựa trên các điều kiện tìm kiếm
        count_query = '''
            SELECT COUNT(Person.PersonID)
            FROM Person
        '''
        
        if where_clauses:
            count_query += ' WHERE ' + ' AND '.join(where_clauses)

        # Thực thi câu truy vấn để đếm tổng số user
        cur.execute(count_query, params)
        total_users = cur.fetchone()[0]
        
        # Tính toán tổng số trang
        total_pages = (total_users + PER_PAGE - 1) // PER_PAGE

        # Xây dựng câu truy vấn chính
        query = '''
            SELECT 
                Person.PersonID, 
                CONCAT(Person.FirstName, ' ', Person.LastName) AS FullName
            FROM Person
        '''    
        
        # Thêm các điều kiện WHERE vào câu truy vấn nếu có
        if where_clauses:
            query += ' WHERE ' + ' AND '.join(where_clauses)

        # Thêm giới hạn và offset cho phân trang
        query += ' LIMIT %s OFFSET %s'

        # Thêm giới hạn và offset vào params
        params.extend([PER_PAGE, offset])
        
        # Thực thi câu truy vấn để lấy người dùng
        cur.execute(query, params)
        users = cur.fetchall()
        
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

    return render_template('search_user.html', users=users, current_page=page, total_pages=total_pages)



@app.route('/search_rent_page')
def search_rent_page():
    return render_template('search_rent.html')

@app.route('/blacklist_manage_page')
def blacklist_manage_page():
    return render_template('search_blacklist.html')

@app.route('/search_group_page')
def search_group_page():
    return render_template('search_group.html')

@app.route('/chat_group_page/<int:person_id>')
def chat_group_page(person_id):
    # conn = None
    # cur = None
    # customer_id = None
    # list_groups= None
        
    # # Lấy PersonID đang đăng nhập từ session
    # if 'user_id' in session:
    #     person_id = session['user_id']
    # else:
    #     # Nếu không có session['user_id'], chuyển hướng người dùng về trang đăng nhập
    #     flash("Hãy đăng nhập để thực hiện chức năng này")
    # try:
    #     conn = get_db_connection()
    #     with conn.cursor() as cur:
    #         # Lấy CustomerID từ PersonID
    #         cur.execute('''
    #             SELECT CustomerID FROM Customer
    #             WHERE PersonID = %s
    #         ''', (person_id,))
                
    #         customer_id = cur.fetchone()[0]
            
            
    # except Exception as error:
    #     conn.rollback()
    # finally:
    #     if cur:
    #         cur.close()
    #     if conn:
    #         conn.close()
    return render_template('group.html',person_id=person_id)

@app.route('/add_to_cart/<int:book_id>')
def add_to_cart(book_id):
    if 'user_id' not in session:
        flash('Bạn cần đăng nhập để đưa sách vào giỏ mượn.')
        return redirect(url_for('login_page'))

    if not book_id:
        flash('Không tìm thấy mã sách.')
        return redirect(url_for('cart_page'))
    
    user_id = session['user_id']
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Lấy ra CustomerID tương ứng với personID
        cur.execute('''SELECT CustomerID FROM Person 
                       JOIN Customer ON Person.PersonID = Customer.PersonID
                       WHERE Person.PersonID = %s''', (user_id,))
        customer = cur.fetchone()
        
        if not customer:
            flash('Không tìm thấy khách hàng tương ứng.')
            return redirect(url_for('cart_page'))

        customer_id = customer[0]
        # Gọi hàm add_to_cart
        cur.execute('SELECT add_to_cart(%s, %s)', (customer_id, book_id))
        conn.commit()
        flash('Sách đã được thêm vào giỏ mượn.')
    except Exception as error:
        print(error)
        flash('Có lỗi xảy ra. Vui lòng thử lại.')
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()
        
    return redirect(url_for('cart_page'))

@app.route('/remove_from_cart/<int:book_id>', methods=['POST'])
def remove_from_cart(book_id):
    if 'user_id' not in session:
        flash('Bạn cần đăng nhập để xóa sách trong giỏ mượn.')
        return redirect(url_for('login_page'))

    if not book_id:
        flash('Không tìm thấy mã sách.')
        return redirect(url_for('cart_page'))
    
    user_id = session['user_id']
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Lấy ra CustomerID tương ứng với personID
        cur.execute('''SELECT CustomerID FROM Person 
                       JOIN Customer ON Person.PersonID = Customer.PersonID
                       WHERE Person.PersonID = %s''', (user_id,))
        customer = cur.fetchone()
        
        if not customer:
            flash('Không tìm thấy khách hàng tương ứng.')
            return redirect(url_for('cart_page'))

        customer_id = customer[0]
        # Gọi hàm add_to_cart
        cur.execute('SELECT remove_from_cart(%s, %s)', (customer_id, book_id))
        conn.commit()
        flash('Sách đã được xóa khỏi giỏ mượn.')
    except Exception as error:
        print(error)
        flash('Có lỗi xảy ra. Vui lòng thử lại.')
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()
        
    return redirect(url_for('cart_page'))


@app.route('/cart_page')
def cart_page():
    if 'user_id' not in session:
        flash('Bạn cần đăng nhập để đưa sách vào giỏ mượn.', 'error')
        return redirect(url_for('login_page'))

    user_id = session['user_id']
    cart_books = []
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Lấy ra CustomerID tương ứng với personID
        cur.execute('''SELECT CustomerID FROM Person 
                       JOIN Customer ON Person.PersonID = Customer.PersonID
                       WHERE Person.PersonID = %s''', (user_id,))
        customer = cur.fetchone()
        customer_id = customer[0]

        # Lấy thông tin sách trong giỏ mượn
        cur.execute('''
            SELECT Book.BookID, Book.Title, 
                   string_agg(DISTINCT Author.Full_Name, ', ') AS AuthorName,
                   string_agg(DISTINCT Category.CategoryName, ', ') AS CategoryName
            FROM Cart
            INNER JOIN Book ON Cart.BookID = Book.BookID
            INNER JOIN Book_Author ON Book.BookID = Book_Author.BookID
            INNER JOIN Author ON Book_Author.AuthorID = Author.AuthorID
            INNER JOIN Book_Category ON Book.BookID = Book_Category.BookID
            INNER JOIN Category ON Book_Category.CategoryID = Category.CategoryID
            WHERE Cart.CustomerID = %s
            GROUP BY Book.BookID
        ''', (customer_id,))
        cart_books = cur.fetchall()

    except Exception as error:
        print(error)
        flash('Có lỗi xảy ra. Vui lòng thử lại.')
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

    return render_template('cart.html', cart_books=cart_books)



@app.route('/confirm_rent', methods=['POST'])
def confirm_rent():
    if 'user_id' not in session:
        flash('Bạn cần đăng nhập để đưa sách vào giỏ mượn.')
        return redirect(url_for('login_page'))

    user_id = session['user_id']
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Lấy ra CustomerID tương ứng với personID
        cur.execute('''SELECT CustomerID FROM Person 
                       JOIN Customer ON Person.PersonID = Customer.PersonID
                       WHERE Person.PersonID = %s''', (user_id,))
        customer = cur.fetchone()
        
        if not customer:
            flash('Không tìm thấy khách hàng tương ứng.')
            return redirect(url_for('cart_page'))

        customer_id = customer[0]
        # Gọi hàm confirm_rent
        cur.execute('SELECT confirm_rent(%s)', (customer_id,))
        rent_id = cur.fetchone()[0]  # Lấy RentID trả về từ hàm confirm_rent
        conn.commit()
        
        # Lưu RentID vào session
        session['rent_id'] = rent_id
        session['blockrent']= True
        flash('Xác nhận mượn thành công.')
    except Exception as error:
        print(error)
        flash('Có lỗi xảy ra. Vui lòng thử lại.')
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()
    return redirect(url_for('cart_page'))



@app.route('/cancel_rent', methods=['POST'])
def cancel_rent():
    if 'user_id' not in session:
        flash('Bạn cần đăng nhập để hủy mượn sách.')
        return redirect(url_for('login_page'))

    if 'rent_id' not in session:
        flash('Không tìm thấy mã mượn sách.')
        return redirect(url_for('cart_page'))
    
    user_id = session['user_id']
    rent_id = session['rent_id']
    
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Lấy ra CustomerID tương ứng với personID
        cur.execute('''SELECT CustomerID FROM Person 
                       JOIN Customer ON Person.PersonID = Customer.PersonID
                       WHERE Person.PersonID = %s''', (user_id,))
        customer = cur.fetchone()

        if not customer:
            flash('Không tìm thấy khách hàng tương ứng.')
            return redirect(url_for('cart_page'))

        customer_id = customer[0]

        # Gọi hàm cancel_rent
        cur.execute('SELECT cancel_rent(%s, %s)', (customer_id, rent_id))
        conn.commit()

        # Xóa RentID khỏi session
        session.pop('rent_id', None)
        session['blockrent'] = False
        flash('Hủy mượn sách thành công.')
    except psycopg2.Error as error:
        print(error)
        flash('Có lỗi xảy ra. Vui lòng thử lại.')
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()
    return redirect(url_for('cart_page'))





@app.route('/profile_page/<int:person_id>')
def profile_page(person_id):
    conn = None
    cur = None
    user_profile = None
    try:
        conn = psycopg2.connect(
            dbname='hust_lib',
            user='postgres',
            password='postgre',
            host='localhost',
            cursor_factory=RealDictCursor
        )
        with conn.cursor() as cur:
            cur.execute(
                    '''SELECT 
                    Person.FirstName, 
                    Person.LastName,
                    Person.PersonID,
                    Person.Gender,
                    Person.Dob,
                    Person.Address,
                    Person.PhoneNumber,
                    Person.Email,
                    Person.CreatedDate,
                    Person.LastActiveDate
                    FROM Person
                    WHERE Person.PersonID=%s''',
                    (person_id,)
                )
            user_profile = cur.fetchone()
    except Exception as error:
            print(error)
    finally:
            if cur:
                cur.close()
            if conn:
                conn.close()    
        
    
    return render_template('profile.html',person_id=person_id,user_profile=user_profile)



@app.route('/change_password_page', methods=['GET', 'POST'])
def change_password_page():
    if 'user_id' not in session:  # Kiểm tra xem người dùng đã đăng nhập chưa
        return redirect(url_for('login_page'))
    
    if request.method == 'POST':
        old_password = request.form['old_password']
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']
        
        if new_password != confirm_password:
            return "Mật khẩu nhập lại không khớp. Vui lòng nhập lại."
        
        user_id = session['user_id']
        conn = None
        cur = None
        try:
            conn = psycopg2.connect(
                dbname='hust_lib',
                user='postgres',
                password='postgre',
                host='localhost',
                cursor_factory=RealDictCursor
            )
            cur = conn.cursor()
            
            # Lấy mật khẩu hiện tại của người dùng từ cơ sở dữ liệu
            cur.execute('SELECT password FROM Person WHERE PersonID = %s', (user_id,))
            result = cur.fetchone()
            if not result:
                return "Người dùng không tồn tại trong hệ thống."
            
            current_password = result['password']  # Truy cập vào trường 'password' đúng cách
            
            # Kiểm tra mật khẩu cũ nhập vào có đúng không
            if old_password != current_password:
                return "Mật khẩu cũ không chính xác."
            
            # Tiến hành cập nhật mật khẩu mới
            cur.execute('UPDATE Person SET Password = %s WHERE PersonID = %s', (new_password, user_id))
            conn.commit()
            
            # Thực hiện đăng xuất sau khi đổi mật khẩu thành công (giả sử logout() là hàm đăng xuất của bạn)
            return logout()
        
        except Exception as error:
            print(f"Lỗi: {error}")
            return "Đã xảy ra lỗi khi thực hiện thay đổi mật khẩu."
        
        finally:
            if cur:
                cur.close()
            if conn:
                conn.close()
                    
    return render_template('change_password.html')


@app.route('/rent_manage_page')
def rent_manage_page():
    return render_template('rent_manage.html')


@app.route('/book_info_page/<int:book_id>')
def book_info_page(book_id):
    conn = None
    cur = None
   
    book_info = None
    count_rate = None
    count_rent = None
    same_author_books = []
    same_category_books = []
    comments = []
    
    try:
        conn = psycopg2.connect(
            dbname='hust_lib',
            user='postgres',
            password='postgre',
            host='localhost',
            cursor_factory=RealDictCursor
        )
        with conn.cursor() as cur:
            cur.execute(
            '''SELECT
                    Book.BookID,
                    Book.Title,
                    string_agg(DISTINCT Author.Full_Name, ', ') AS AuthorName,
                    string_agg(DISTINCT Category.CategoryName, ', ') AS CategoryName,
                    Book.PublishYear,
                    Book.Quantity,
                    ROUND(AVG(COALESCE(Rate.star, 0)), 1) AS AverageRate
                FROM Book
                INNER JOIN Book_Author ON Book.BookID = Book_Author.BookID
                INNER JOIN Author ON Book_Author.AuthorID = Author.AuthorID
                INNER JOIN Book_Category ON Book.BookID = Book_Category.BookID
                INNER JOIN Category ON Book_Category.CategoryID = Category.CategoryID
                LEFT JOIN Rate ON Book.BookID = Rate.BookID
                WHERE Book.BookID = %s
                GROUP BY Book.BookID''',
                (book_id,)
            )

            book_info = cur.fetchone()
            
            cur.execute(
                'SELECT COUNT(RatingID) AS NumRatedBook FROM Rate WHERE BookID = %s',
                (book_id,)
            )
            count_rate = cur.fetchone()
            
            cur.execute(
                'SELECT COUNT(RentlineID) AS NumBorrowedBooks FROM Rentline WHERE BookID = %s',
                (book_id,)
            )
            count_rent = cur.fetchone()
            
            
            if book_info:
                cur.execute(
                    '''SELECT DISTINCT Author.AuthorID
                    FROM Book
                    INNER JOIN Book_Author ON Book.BookID = Book_Author.BookID
                    INNER JOIN Author ON Book_Author.AuthorID = Author.AuthorID
                    WHERE Book.BookID = %s''',
                    (book_id,)
                )
                author_ids = [row['authorid'] for row in cur.fetchall()]

                if author_ids:
                    cur.execute(
                        '''SELECT DISTINCT Book.BookID, Book.Title,
                            string_agg(DISTINCT Author.Full_Name, ', ') AS AuthorName
                        FROM Book
                        INNER JOIN Book_Author ON Book.BookID = Book_Author.BookID
                        INNER JOIN Author ON Book_Author.AuthorID = Author.AuthorID
                        WHERE Book_Author.AuthorID IN %s AND Book.BookID != %s
                        GROUP BY Book.BookID''',
                        (tuple(author_ids), book_id)
                    )
                    same_author_books = cur.fetchall()

            if book_info:
                cur.execute(
                    '''SELECT DISTINCT Category.CategoryID
                    FROM Book
                    INNER JOIN Book_Category ON Book.BookID = Book_Category.BookID
                    INNER JOIN Category ON Book_Category.CategoryID = Category.CategoryID
                    WHERE Book.BookID = %s''',
                    (book_id,)
                )
                category_ids = [row['categoryid'] for row in cur.fetchall()]
                category_ids = tuple(set(category_ids))  # loại bỏ các id trùng nhau

                if category_ids:
                    cur.execute(
                        '''SELECT DISTINCT Book.BookID, Book.Title,
                            string_agg(DISTINCT Author.Full_Name, ', ') AS AuthorName
                        FROM Book
                        INNER JOIN Book_Author ON Book.BookID = Book_Author.BookID
                        INNER JOIN Author ON Book_Author.AuthorID = Author.AuthorID
                        INNER JOIN Book_Category ON Book.BookID = Book_Category.BookID
                        INNER JOIN Category ON Book_Category.CategoryID = Category.CategoryID
                        WHERE Book_Category.CategoryID IN %s AND Book.BookID != %s
                        GROUP BY Book.BookID''',
                        (category_ids, book_id)
                    )
                    same_category_books = cur.fetchall()
                    
                    cur.execute(
                        '''SELECT 
                            CONCAT(Person.Firstname, ' ', Person.LastName) AS RateFullName,
                            Rate.CustomerID AS RateCustomerID,
                            Rate.Star AS RateStar,
                            Rate.Comment AS CommentBook,
                            Rate.CommentTime AS RateCommentTime
                        FROM Rate 
                        INNER JOIN Customer ON Rate.CustomerID = Customer.CustomerID
                        INNER JOIN Person ON Customer.PersonID = Person.PersonID
                        WHERE BookID = %s''',
                        (book_id,)
                    )
                    comments = cur.fetchall()

    except Exception as error:
        print(error)
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()
        
        return render_template('book_info.html', 
                               book_info=book_info, 
                               same_author_books=same_author_books, 
                               same_category_books=same_category_books,
                               comments=comments,
                               count_rate=count_rate,
                               count_rent=count_rent)


        
@app.route('/submit_review/<int:book_id>', methods=['POST'])
def submit_review(book_id):
    if request.method == 'POST':
        new_rating = int(request.form.get('rating')) # Lấy thông tin số sao từ việc nhấn nút
        new_comment = request.form.get('comment')
        conn = None
        cur = None
        customer_id = None
        
        # Lấy PersonID đang đăng nhập từ session
        if 'user_id' in session:
            person_id = session['user_id']
        else:
            # Nếu không có session['user_id'], chuyển hướng người dùng về trang đăng nhập
            flash("Hãy đăng nhập để thực hiện chức năng này")
        try:
            conn = get_db_connection()
            with conn.cursor() as cur:
                # Lấy CustomerID từ PersonID
                cur.execute('''
                    SELECT CustomerID FROM Customer
                    WHERE PersonID = %s
                ''', (person_id,))
                
                customer_id = cur.fetchone()[0]
                
                # Thêm đánh giá mới vào bảng Rate
                cur.execute('''
                    INSERT INTO Rate (CustomerID, BookID, Star, Comment)
                    VALUES (%s, %s, %s, %s)
                ''', (customer_id, book_id, new_rating, new_comment))
                
                conn.commit()
        except Exception as error:
            conn.rollback()
            print("Lỗi khi thêm đánh giá vào cơ sở dữ liệu:", error)
        finally:
            if cur:
                cur.close()
            if conn:
                conn.close()
    return redirect(url_for('book_info_page', book_id=book_id))








@app.route('/book_manage_page')
def book_manage_page():
    return render_template('book_manage.html')

@app.route('/book_update_page')
def book_update_page():
    return render_template('book_update.html')

@app.route('/book_insert_page')
def book_insert_page():
    return render_template('book_insert.html')

@app.route('/stats_page')

def stats_quantity():
    conn = None
    cur = None
    quantity_person = None
    quantity_book = None
    quantity_author = None
    quantity_rent = None
    quantity_group = None
    
    
    authors_data = None
    
    publishers_data= None

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Lấy số lượng
        cur.execute("SELECT COUNT(*) FROM Person")
        quantity_person = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM Book")
        quantity_book = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM Author")
        quantity_author = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM Rent")
        quantity_rent = cur.fetchone()[0]

        cur.execute('SELECT COUNT(*) FROM "Group"')
        quantity_group = cur.fetchone()[0]
        
        

        # Lấy danh sách 10 tác giả hàng đầu
        cur.execute('''
            SELECT Author.Full_Name, COUNT(Book_Author.BookID) AS NumberOfBooks
            FROM Author
            JOIN Book_Author ON Author.AuthorID = Book_Author.AuthorID
            GROUP BY Author.AuthorID, Author.Full_Name
            ORDER BY NumberOfBooks DESC
            LIMIT 10
        ''')
        authors_data = cur.fetchall()
        cur.execute('''
            SELECT 
                Publisher.Name AS PublisherName,
                COUNT(Book.BookID) AS NumberOfBooks
            FROM Publisher
            LEFT JOIN Book ON Publisher.PublisherID = Book.PublisherID
            GROUP BY Publisher.PublisherID, Publisher.Name
            ORDER BY NumberOfBooks DESC
            LIMIT 10
        ''')
        publishers_data = cur.fetchall()

    except Exception as error:
        print(error)
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()
        
    # Render template stats.html với tất cả dữ liệu
    return render_template('stats.html', user_count=quantity_person, book_count=quantity_book,
                           author_count=quantity_author, rent_count=quantity_rent, group_count=quantity_group,
                           authors_data=authors_data,
                           publishers_data=publishers_data)


@app.route('/process_login', methods=['POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = None
        try:
            conn = get_db_connection()
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                cur.execute('SELECT * FROM Person WHERE Email = %s AND Password = %s', (email, password))
                user = cur.fetchone()
                if user:
                    # Lưu thông tin người dùng vào session
                    session['user_id'] = user['personid']
                    session['user_role'] = user['role']
                    flash('Login success!')

                    # Cập nhật LastActiveDate mỗi khi đăng nhập thành công
                    cur.execute('''
                        UPDATE Person
                        SET LastActiveDate = CURRENT_TIMESTAMP
                        WHERE personid = %s
                    ''', (user['personid'],))
                    conn.commit()

                    # Kiểm tra và lưu trạng thái BlockRent vào session
                    cur.execute('''
                        SELECT BlockRent FROM Customer WHERE PersonID = %s
                    ''', (user['personid'],))
                    blockrent = cur.fetchone()

                    session['blockrent'] = blockrent['blockrent']  # Lưu trạng thái BlockRent vào session

                    return redirect(url_for('profile_page', person_id=session['user_id']))  # Chuyển hướng đến trang hồ sơ
                else:
                    flash('Invalid email or password. Please try again.')
                    return redirect(url_for('login_page'))
        except Exception as error:
            print(error)
            flash('An error occurred. Please try again later.')
            return redirect(url_for('login_page'))  # Thêm return trong trường hợp có lỗi
        finally:
            if conn is not None:
                conn.close()

    # Thêm return trong trường hợp phương thức không phải POST
    return redirect(url_for('login_page'))




from flask import flash

@app.route('/update_profile', methods=['POST'])
def update_profile():
    if 'user_id' in session:
        user_id = session['user_id']
        updated_field = list(request.form.keys())[0]
        # Loại bỏ dấu nháy đơn từ tên trường
        clean_updated_field = updated_field.strip("'")
        updated_value = request.form[clean_updated_field]

        try:
            update_user_profile(user_id, updated_field, updated_value)
            flash('Profile updated successfully', 'success')
        except Exception as error:
            flash(str(error), 'error')
        
        return redirect(url_for('profile_page', person_id=user_id))
    return redirect(url_for('login_page'))

def update_user_profile(user_id, field, value):
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Sử dụng prepared statements và parametrized queries để tránh lỗi injection và bảo vệ dữ liệu
        sql = f"UPDATE Person SET \"{field}\" = %s WHERE PersonID = %s"

        cur.execute(sql, (value, user_id))
        conn.commit()
    except Exception as error:
        # Xử lý lỗi và ném ra ngoại lệ để xử lý ở route handler
        if conn:
            conn.rollback()
        raise Exception("Failed to update profile: " + str(error))
    finally:
        # Đóng các kết nối và con trỏ
        if cur:
            cur.close()
        if conn:
            conn.close()







                



# @app.route('/admin_page')
# def admin_page():
#     user_role = session.get('user_role')
#     if user_role != 'Admin':
#         flash('Access denied.')
#         return redirect(url_for(''))

#     # Thực hiện các chức năng dành riêng cho admin
#     return render_template('admin.html')
               
                
                
        
if __name__ == '__main__':
    app.run(debug=True)