from flask import Flask, render_template, request, url_for, redirect, flash, session
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Đặt một khóa bí mật cho phiên làm việc

def get_db_connection():
    conn = psycopg2.connect(
        host='localhost',
        dbname='hust_lib',
        user='postgres',
        password='skadi123',
        port=5432
    )
    return conn

@app.route('/login_page')
def login_page():
    return render_template('login.html')

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
import re
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
    
@app.route('/search_user_page')
def search_user_page():
    return render_template('search_user.html')

@app.route('/search_rent_page')
def search_rent_page():
    return render_template('search_rent.html')

@app.route('/search_group_page')
def search_group_page():
    return render_template('search_group.html')

@app.route('/chat_group_page')
def chat_group_page():
    return render_template('group.html')

@app.route('/cart_page/<int:book_id>')
def cart_page():
    
    return render_template('cart.html')

@app.route('/profile_page/<int:person_id>')
def profile_page(person_id):
    conn = None
    cur = None
    user_profile = None
    try:
        conn = psycopg2.connect(
            dbname='hust_lib',
            user='postgres',
            password='skadi123',
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


@app.route('/rent_manage_page')
def rent_manage_page():
    return render_template('rent_manage.html')


@app.route('/book_info_page/<int:book_id>')
def book_info_page(book_id):
    conn = None
    cur = None
    
    ########
    book_info = None  # lưu thông tin về cuốn sách có id = book_id
    same_author_books = [] # lưu các cuốn sách có chung ít nhất 1 tác giả với cuốn sách có id=book_id
    same_category_books = [] # lưu thông tin các cuốn sách có chung ít nhất 1 tag category trùng với cuốn sách có id=book_id
    comments = []  # lưu thông tin các đánh giá của sách có id=book_id
    
    try:
        conn = psycopg2.connect(
            dbname='hust_lib',
            user='postgres',
            password='skadi123',
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
                    COUNT(Rentline.RentlineID) AS NumBorrowedBooks,
                    ROUND(AVG(Rate.star), 1) AS AverageRate,
                    COUNT(Rate.RatingID) AS NumRatedBook
                FROM Book
                INNER JOIN Book_Author ON Book.BookID = Book_Author.BookID
                INNER JOIN Author ON Book_Author.AuthorID = Author.AuthorID
                INNER JOIN Book_Category ON Book.BookID = Book_Category.BookID
                INNER JOIN Category ON Book_Category.CategoryID = Category.CategoryID
                INNER JOIN Publisher ON Book.PublisherID = Publisher.PublisherID
                LEFT JOIN Rentline ON Book.BookID = Rentline.BookID
                LEFT JOIN Rate ON Book.BookID = Rate.BookID               
                WHERE Book.BookID = %s
                GROUP BY Book.BookID''',
                (book_id,)
            )

            book_info = cur.fetchone()
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
                category_ids = tuple(set(category_ids))  # Loại bỏ các thể loại trùng lặp

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
                    WHERE BookID = %s ''',
                    (book_id,)
                    )
                    comments=cur.fetchall()
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
                               comments=comments)
        
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
        cur = None

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
                    # cập nhập LastActiveDate mỗi khi đăng nhập thành công
                    cur.execute('''
                            UPDATE Person
                            SET LastActiveDate = CURRENT_TIMESTAMP
                            WHERE personid = %s
                        ''', (user['personid'],))
                    conn.commit()
                    return redirect(url_for('profile_page',person_id=session['user_id']))  # Chuyển hướng đến trang hồ sơ
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
                
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('user_role', None)
    flash('You have been logged out.')
    return redirect(url_for('login_page'))


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
