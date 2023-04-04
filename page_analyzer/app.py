from flask import (
    Flask,
    flash,
    get_flashed_messages,
    redirect,
    render_template,
    request,
    url_for,
)
import os
import psycopg2
from dotenv import load_dotenv
from validators.url import url
import datetime
import requests
from bs4 import BeautifulSoup


load_dotenv('analyzer.env')


app = Flask(__name__)
SECRET_KEY = os.getenv('SECRET_KEY')
app.secret_key = SECRET_KEY


DATABASE_URL = os.getenv('DATABASE_URL')
conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()


@app.route('/')
def index():
    messages = get_flashed_messages(with_categories=True)
    return render_template('app.html', messages=messages)


@app.get('/urls')
def get_urls():
    cur.execute("SELECT * FROM urls")
    records = cur.fetchall()[::-1]
    cur.execute('''
    SELECT DISTINCT ON (url_id) url_id, status_code, created_at
    FROM url_checks
    ORDER BY url_id, status_code, created_at DESC
    ''')
    lastcheck = cur.fetchall()
    return render_template('urls.html', urls=records, lastcheck=lastcheck)


@app.post('/urls')
def add_url():
    newurl = request.form.get('url')
    cur.execute("SELECT * FROM urls")
    records = cur.fetchall()
    for record in records:
        if record[1] == newurl:
            flash('Страница уже существует', 'info')
            return redirect(url_for('cur_url', id=record[0]), 302)
    if url(newurl) and len(newurl) < 255:
        query = "INSERT INTO urls (name, created_at) VALUES (%s, %s)"
        cur.execute(query, (newurl, datetime.datetime.now()))
        cur.execute('SELECT id FROM urls ORDER BY id DESC')
        id = cur.fetchall()[0]
        flash('Страница успешно добавлена', 'success')
        return redirect(url_for('cur_url', id=id[0]), 302)
    else:
        if len(newurl) == 0:
            flash('URL обязателен', 'warning')
        flash('Некорректный URL', 'warning')
        return redirect(url_for('index'), 402)


@app.route('/urls/<id>')
def cur_url(id):
    cur.execute(f"SELECT * FROM urls WHERE id={id} ORDER BY id DESC")
    current_url = cur.fetchall()[0]
    cur.execute(f"SELECT * FROM url_checks WHERE url_id={id} ORDER BY id DESC")
    allchecks = cur.fetchall()
    messages = get_flashed_messages(with_categories=True)
    return render_template('cururl.html', messages=messages, current_url=current_url, allchecks=allchecks)  # noqa: E501


@app.post('/urls/<id>/checks')
def check_url(id):
    cur.execute(f"SELECT name FROM urls WHERE id={id}")
    current_url = cur.fetchall()[0]
    try:
        r = requests.get(current_url[0])
        if r.status_code != 200:
            raise requests.RequestException
        page = r.text
        soup = BeautifulSoup(page, 'html.parser')
        query = '''INSERT INTO url_checks
        (url_id, status_code, h1, title, description, created_at)
        VALUES (%s, %s, %s, %s, %s, %s)'''
        h1 = soup.find("h1").text if soup.find("h1") else ''
        title = soup.find("title").text if soup.find("title") else ''
        content = soup.find(attrs={"name": "description"}).get('content') if soup.find(attrs={"name": "description"}) else ''  # noqa: E501
        cur.execute(query, (id, r.status_code, h1, title, content, datetime.datetime.now()))  # noqa: E501
        flash('Страница успешно проверена', 'success')
        return redirect(url_for('cur_url', id=id), 302)
    except requests.RequestException:
        flash('Произошла ошибка при проверке', 'warning')
        return redirect(url_for('cur_url', id=id), 402)
