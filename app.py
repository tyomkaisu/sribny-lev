from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user, UserMixin
import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Важливо для сесій

DB = 'reservations.db'

login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

class User(UserMixin):
    def __init__(self, id_, username, is_admin):
        self.id = id_
        self.username = username
        self.is_admin = is_admin

def get_user_by_id(user_id):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT id, username, is_admin FROM users WHERE id = ?", (user_id,))
    row = c.fetchone()
    conn.close()
    if row:
        return User(row[0], row[1], bool(row[2]))
    return None

def get_user_by_username(username):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT id, username, password, is_admin FROM users WHERE username = ?", (username,))
    row = c.fetchone()
    conn.close()
    if row:
        return {'id': row[0], 'username': row[1], 'password': row[2], 'is_admin': bool(row[3])}
    return None

# Ось ця функція — перевіряє, чи є користувач з таким username
def user_exists(username):
    return get_user_by_username(username) is not None

@login_manager.user_loader
def load_user(user_id):
    return get_user_by_id(user_id)

def init_db():
    db_exists = os.path.exists(DB)
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    if not db_exists:
        c.execute('''
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                is_admin INTEGER NOT NULL DEFAULT 0
            )
        ''')
        c.execute('''
            CREATE TABLE reservations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date_from TEXT NOT NULL,
                date_to TEXT NOT NULL,
                rooms INTEGER NOT NULL,
                room_type TEXT NOT NULL,
                guests INTEGER NOT NULL,
                user_id INTEGER,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        admin_password = generate_password_hash("zxc")
        c.execute('INSERT INTO users (username, password, is_admin) VALUES (?, ?, ?)', ("admin", admin_password, 1))
    else:
        try:
            c.execute("ALTER TABLE reservations ADD COLUMN user_id INTEGER")
        except sqlite3.OperationalError:
            pass
        try:
            c.execute("ALTER TABLE reservations ADD COLUMN room_type TEXT NOT NULL DEFAULT 'Двомісна'")
        except sqlite3.OperationalError:
            pass
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/menu')
def menu():
    popular_dishes = [
        ('🍣 Суші-сет "Срібний лев"', 300),
        ('🍲 Котлета по-київськи', 180),
        ('🥗 Салат "Цезар" з куркою', 130),
        ('🍮 Десерт "Наполеон"', 100),
        ('🍛 Галушки з м’ясом', 130),
        ('🍹 Свіжовижатий сік', 70),
    ]
    return render_template('menu.html', popular_dishes=popular_dishes)

@app.route('/menu/<category>')
def menu_category(category):
    categories = {
        'hot': {
            'title': 'Гарячі страви',
            'dishes': [
                ('🥣 Борщ український зі сметаною', 120),
                ('🥟 Вареники з картоплею та грибами', 110),
                ('🍲 Котлета по-київськи', 180),
                ('🍛 Галушки з м’ясом', 130),
                ('🍖 Запечена свинина з овочами', 220),
                ('🥗 Овочевий борщ із домашнім хлібом', 115),
                ('🍗 Курячі крильця барбекю', 190),
                ('🥘 Рагу з яловичини та овочів', 250),
            ]
        },
        'japanese': {
            'title': 'Японська кухня',
            'dishes': [
                ('🍣 Суші-сет "Срібний лев"', 300),
                ('🍜 Рамен з куркою', 200),
                ('🍡 Мочі з полуницею', 80),
                ('🍵 Зелений чай матча', 90),
                ('🥢 Темпура з овочами', 180),
                ('🍤 Ебі-фрай (смажені креветки)', 220),
                ('🍙 Онігірі з лососем', 130),
                ('🍥 Такоякі (кульки з восьминога)', 170),
            ]
        },
        'drinks': {
            'title': 'Напої',
            'dishes': [
                ('🍹 Свіжовижатий сік', 70),
                ('🍶 Традиційне саке', 150),
                ('☕ Кава американо', 60),
                ('🍵 Зелений чай матча', 90),
                ('🥤 Домашній лимонад', 80),
                ('🍺 Пиво світле', 90),
                ('🍷 Червоне вино', 180),
                ('🍸 Коктейль "Мохіто"', 220),
            ]
        },
        'salads': {
            'title': 'Салати',
            'dishes': [
                ('🥗 Салат "Цезар" з куркою', 130),
                ('🥬 Грецький салат', 110),
                ('🌽 Олів’є', 100),
                ('🥒 Овочевий салат із оливковою олією', 90),
                ('🥑 Авокадо з томатами', 140),
                ('🍅 Капрезе з моцарелою', 150),
                ('🌿 Салат з руколою та горіхами', 160),
                ('🥕 Морквяний салат з родзинками', 95),
            ]
        },
        'desserts': {
            'title': 'Десерти',
            'dishes': [
                ('🍰 Тірамісу', 120),
                ('🍮 Десерт "Наполеон"', 100),
                ('🍓 Полуниця зі збитими вершками', 90),
                ('🍫 Шоколадний мус', 130),
                ('🍪 Печиво "Орео"', 80),
                ('🍧 Мохіто сорбет', 110),
                ('🍨 Ванільне морозиво', 95),
                ('🥧 Чізкейк з ягодами', 140),
            ]
        }
    }

    if category not in categories:
        return render_template('404.html'), 404

    data = categories[category]
    return render_template('menu_category.html', title=data['title'], dishes=data['dishes'])

@app.route('/contacts')
def contacts():
    return render_template('contacts.html')

@app.route('/reservation', methods=['GET', 'POST'])
@login_required
def reservation():
    if request.method == 'POST':
        date_from = request.form.get('date_from')
        date_to = request.form.get('date_to')
        rooms = request.form.get('rooms')
        room_type = request.form.get('room_type')
        guests = request.form.get('guests')

        conn = sqlite3.connect(DB)
        c = conn.cursor()
        c.execute('''
            INSERT INTO reservations (date_from, date_to, rooms, room_type, guests, user_id)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (date_from, date_to, rooms, room_type, guests, current_user.id))
        conn.commit()
        conn.close()

        flash('Бронювання успішно створено!', 'success')
        return redirect(url_for('index'))

    return render_template('reservation.html')

@app.route('/bookings')
@login_required
def bookings():
    if not current_user.is_admin:
        flash("Доступ заборонено!", "danger")
        return redirect(url_for('index'))

    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('SELECT r.id, r.date_from, r.date_to, r.rooms, r.room_type, r.guests, u.username '
              'FROM reservations r LEFT JOIN users u ON r.user_id = u.id '
              'ORDER BY r.id DESC')
    reservations = c.fetchall()
    conn.close()
    return render_template('bookings.html', reservations=reservations)

@app.route('/my_bookings')
@login_required
def my_bookings():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('SELECT id, date_from, date_to, rooms, room_type, guests FROM reservations WHERE user_id = ? ORDER BY id DESC', (current_user.id,))
    reservations = c.fetchall()
    conn.close()
    return render_template('my_bookings.html', reservations=reservations)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form['username']

        if user_exists(username):
            flash("Користувач з таким логіном вже існує", "error")
            return redirect(url_for('register'))

        password = request.form['password']
        if not username or not password:
            flash("Будь ласка, заповніть усі поля.", "warning")
            return redirect(url_for('register'))

        hashed_pw = generate_password_hash(password)
        conn = sqlite3.connect(DB)
        c = conn.cursor()
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_pw))
        conn.commit()
        conn.close()

        flash("Реєстрація пройшла успішно. Ви можете увійти.", "success")
        return redirect(url_for('login'))

    return render_template('auth.html', active_form='register')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = get_user_by_username(username)
        if user and check_password_hash(user['password'], password):
            user_obj = User(user['id'], user['username'], user['is_admin'])
            login_user(user_obj)
            flash("Вхід успішний!", "success")
            return redirect(url_for('index'))
        else:
            flash("Неправильний логін або пароль.", "danger")
            return redirect(url_for('login'))

    return render_template('auth.html', active_form='login')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Ви вийшли з системи.", "info")
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)
