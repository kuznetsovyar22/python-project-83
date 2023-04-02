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
from jinja2 import Environment
import psycopg2
from dotenv import load_dotenv
from validators.url import url
import datetime


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
    cur.execute("SELECT DISTINCT ON (url_id) url_id, created_at FROM url_checks ORDER BY url_id, created_at DESC")
    lastcheck = cur.fetchall()
    print(lastcheck)
    return render_template('urls.html', urls=records, lastcheck=lastcheck)


@app.post('/urls')
def add_url():
    newurl = request.form.get('url')
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
    return render_template('cururl.html', messages=messages, current_url=current_url, allchecks=allchecks)


@app.post('/urls/<id>/checks')
def check_url(id):
    query = "INSERT INTO url_checks (url_id, status_code, h1, title, description, created_at) VALUES (%s, %s, %s, %s, %s, %s)"
    cur.execute(query, (id, 200, 'h1', 'title', 'description', datetime.datetime.now()))
    flash('Страница успешно проверена', 'success')
    return redirect(url_for('cur_url', id=id), 302)