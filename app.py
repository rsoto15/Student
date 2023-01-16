from curses import flash
from operator import methodcaller
from telnetlib import SE
from flask import Flask, render_template, request, redirect, url_for, session
from flask_mysqldb import MySQL
import MySQLdb.cursors
import re
from datetime import datetime
import os
from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash

config = {
    "DEBUG": True  # run app in debug mode
}

app = Flask(__name__)

app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY")
app.config['MYSQL_HOST'] = os.environ.get('MYSQL_HOST')
app.config['MYSQL_USER'] = os.environ.get('MYSQL_USER')
app.config['MYSQL_PASSWORD'] = os.environ.get('MYSQL_PASSWORD')
app.config['MYSQL_DB'] = os.environ.get('MYSQL_DB')

app.config.from_mapping(config)

mysql = MySQL(app)


@app.route('/', methods=['GET', 'POST'])
def login():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM accounts WHERE username = %s and password = %s', (username, password))
        account = cursor.fetchone()

        if account:
            check_password_hash(account['password'], password)
            session['loggedin'] = True
            session['id'] = account['id']
            session['username'] = account['username']

            return redirect(url_for('home'))
        else:
            msg = 'Incorrect username/password!'

    return render_template('index.html', msg=msg)

@app.route('/login/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username', None)

    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    msg = ''
    
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form:
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM accounts WHERE username = %s and email = %s', (username, email))
        account = cursor.fetchone()
        
        if account:
            msg = 'Account already exists!'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Invalid email address!'
        elif not re.match(r'[A-Za-z0-9]+', username):
            msg = 'Username must contain only characters and numbers!'
        elif not username or not password or not email:
            msg = 'Please fill out the form!'
        else:
            hsp = generate_password_hash(
                request.form['password'],
                method='pbkdf2:sha256',
                salt_length=10
            )
            cursor.execute('INSERT INTO accounts values (NULL, %s, %s, %s)', (username, hsp, email))
            mysql.connection.commit()
            msg = 'You have successfully registered!'
    elif request.method == 'POST':
        msg = 'Please fill out the form!'
    return render_template('register.html', msg=msg)

@app.route('/home')
def home():
    if 'loggedin' in session:
        return render_template('home.html', username=session['username'], id=session['id'])
    return redirect(url_for('login'))

@app.route('/students', methods=['POST', 'GET'])
def students():
    if 'loggedin' in session:
        msg = ''
        if request.method == 'POST' and 'username' in request.form and 'studentID' in request.form and 'sped' in request.form and 'parentsName' in request.form and 'contactInfo' in request.form:
            username = request.form['username']
            studentID = request.form['studentID']
            sped = request.form['sped']
            parents_name = request.form['parentsName']
            phone_number = request.form['contactInfo']
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('SELECT * FROM add_students WHERE username = %s and student_id = %s and sped = %s and parents_name = %s and parents_number = %s', (username, studentID, sped, parents_name, phone_number))
            account = cursor.fetchone()
            
            if account:
                msg = 'Account already exists!'
            elif not re.match(r'[A-Za-z0-9]+', username):
                msg = 'Username must contain only characters and numbers!'
            elif not username or not studentID or not sped or not parents_name or not phone_number:
                msg = 'Please fill out the form!'
            else:
                cursor.execute('INSERT INTO add_students values (NULL, %s, %s, %s, %s, %s)', (username, studentID, sped, parents_name, phone_number))
                mysql.connection.commit()
                msg = 'You have successfully added a new student!'
        elif request.method == 'POST':
            msg = 'Please fill out the form!'
        return render_template('students.html', msg=msg)
    return redirect(url_for('login'))


@app.route('/students2', methods=['GET'])
def students2():
    if 'loggedin' in session:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM add_students')
        account = cursor.fetchall()
        return render_template('students2.html',account=account)
    return redirect(url_for('login'))

@app.route('/students2/update/<id>', methods=['GET', 'POST'])
def update(id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * from add_students WHERE id = %s', (id,))
    account = cursor.fetchone()
    
    if account:
        return render_template('update.html', account=account)

    

@app.route('/edit', methods=['POST', 'GET'])
def update_user():
    username = request.form['username']
    studentID = request.form['studentID']
    sped = request.form['sped']
    parents_name = request.form['parentsName']
    parents_number = request.form['contactInfo']
    id = request.form['id']

    if username and studentID and sped and parents_name and parents_number and request.method == 'POST':
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('UPDATE add_students SET username = %s, student_id = %s, sped = %s, parents_name = %s, parents_number = %s WHERE id = %s', (username, studentID, sped, parents_name, parents_number, id,))
        mysql.connection.commit()
        
        return redirect(url_for('students2'))

@app.route('/students2/delete/<id>')
def delete(id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * from add_students WHERE id = %s', (id,))
    account = cursor.fetchone()

    if account:
        return render_template('delete.html', account=account)

@app.route('/deleteuser', methods=['POST', 'GET'])
def delete_user():
    id = request.form['id']
    if request.method == 'POST':
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('DELETE FROM add_students WHERE id = %s', (id,))
        mysql.connection.commit()

        return redirect(url_for('students2'))

@app.route('/notesform/<id>', methods=['POST', 'GET'])
def notesform(id):
    if 'loggedin' in session:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * from add_students WHERE id = %s', (id,))
        account = cursor.fetchone()
        
        if account:

            if request.method == 'POST':            
                date_time = str(request.form['date_time'])
                #now = datetime.now()
                formatted_date = datetime.strptime(date_time, '%Y-%m-%dT%H:%M')
                student_parent = request.form['student_parent']
                purpose = request.form['purpose']
                outcome = request.form['outcome']
                studentID = request.form['studentID']
                cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
                cursor.execute('INSERT INTO student_notes_log values (NULL, %s, %s, %s, %s, %s)', (formatted_date, student_parent, studentID, purpose, outcome))
                mysql.connection.commit()
            return render_template('notesform.html', account=account)
            
    return redirect(url_for('login'))

@app.route('/notes', methods=['GET'])
def notes():
    if 'loggedin' in session:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM student_notes_log')
        account = cursor.fetchall()
        return render_template('notes.html',account=account)
    return redirect(url_for('login'))


@app.route('/students2/studentnotes/<student_id>', methods=['POST', 'GET'])
def studentnotes(student_id):
    if 'loggedin' in session:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM student_notes_log WHERE student_id = %s', (student_id,))
        account = cursor.fetchall()

        return render_template('studentnotes.html', account=account)

    return redirect(url_for('login'))


