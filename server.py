from flask import Flask, render_template, request, redirect, flash, session
from mysqlconnection import connectToMySQL
from flask_bcrypt import Bcrypt

import re

app = Flask(__name__)
app.secret_key = "super secret squirel stuff"
bcrypt = Bcrypt(app)

EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$')
SCHEMA = 'beltExam'



@app.route('/')
def Landing_page():
    return render_template('index.html')




@app.route('/register', methods=['POST'])
def create_user():
    messages = []
    fname = request.form['f_name']
    lname = request.form['l_name']
    email = request.form['e_mail']
    password = request.form['password']
    confirm_pw = request.form['c_password']

    # first name cannot be blank
    if len(fname) < 1:
        messages.append('First name cannot be left blank')
    # last name cannot be blank
    if len(lname) < 1:
        messages.append('Last name cannot be left blank')
    # email must be valid format
    if not EMAIL_REGEX.match(email):
        messages.append('Email must be valid')
    # email must be unique
    db = connectToMySQL(SCHEMA)
    query = "SELECT * FROM users WHERE e_mail=%(email)s;"
    data = { "email": email }
    matching_users = db.query_db(query, data)
    if matching_users:
        messages.append("E-Mail already in use")
    # password must be at least 8 characters
    if len(password) < 8:
        messages.append('Password must be at least 8 characters long')
    # passwords and confirm password must match
    if password != confirm_pw:
        messages.append('Password and confirm password must match')
    #return to start, do not past go, do not collect $200( you got errors)
    if messages:
            for message in messages:
                print('you got problems')
                flash(message, 'registration')
            return redirect ('/')
    #get theat good breakfast hash
    pw_hash = bcrypt.generate_password_hash(request.form['password'])
    #load into database
    query='INSERT INTO users (f_name, l_name, e_mail, pw_hash) VALUES (%(fname)s, %(lname)s, %(email)s, %(pass_hash)s );'
    data= {
        'fname' : request.form['f_name'],
        'lname' : request.form['l_name'],
        'email' : request.form['e_mail'],
        'password' : request.form['password'],
        'pass_hash' : pw_hash,
    }
    mysql=connectToMySQL(SCHEMA)
    mysql.query_db(query, data)
    return redirect ('/')


@app.route("/login", methods=['POST'])
def index():
    db = connectToMySQL(SCHEMA)
    query = "SELECT id, f_name, l_name, e_mail, pw_hash FROM users WHERE e_mail = %(e_mail)s;"
    data = {
        'e_mail': request.form['e_mail']
    }
    match_user = db.query_db(query, data)
    if match_user:
        user = match_user[0]
        if bcrypt.check_password_hash(user['pw_hash'], request.form['password']):
            session['u_id'] = user['id']
            session['f_name'] = user['f_name']
            session['l_name'] = user['l_name']
            session['e_mail'] = user['e_mail']
            return redirect('/wishes')
    flash("ah ah ah, You didn't say the magic word.", 'login')
    return redirect('/')


@app.route('/wishes')
def wishes():
    
    query="Select * from wishes where wishes.wisher_id=%(id)s AND wishes.date_granted = '0'"
    data= {
        'id' : session['u_id'],
    }
    mysql=connectToMySQL(SCHEMA)
    your_wishes=mysql.query_db(query, data) 
    query="""Select wishes.id, wishes.wish, wishes.wish_description, wishes.created_at, wishes.updated_at, wishes.date_granted, wishes.wisher_id, users.id, users.f_name
                From wishes
                left JOIN users ON wisher_id = users.id
                Where wishes.date_granted IS NOT 'NULL'"""
    mysql=connectToMySQL(SCHEMA)
    all_wishes=mysql.query_db(query)
    return render_template('wishes.html', a_w=all_wishes, y_w=your_wishes)


@app.route('/wishes/new')
def newWish():
    return render_template('newWish.html')


@app.route('/newWish_process', methods=['POST'])
def newWish_process():
    messages=[]
    wish = request.form['wish']
    desc = request.form['desc']
    
    if len(wish) < 3:
        messages.append("I'm not good with acrynoms. A wish must consist of at least 3 characters! Spell it out.")
    if len(desc) < 3:
        messages.append('Please tell me more. A description must be provided!')
    if messages:
        for message in messages:
            print('you got problems with your wishes')
            flash(message, 'wishErrors')
        return redirect (request.referrer)
    else:
        query='INSERT INTO wishes (wish, wish_description, wisher_id) VALUES (%(wish)s, %(desc)s, %(u_id)s);'
    data= {
        'wish' : request.form['wish'],
        'desc' : request.form['desc'],
        'u_id' : session['u_id']
    }
    mysql=connectToMySQL(SCHEMA)
    mysql.query_db(query, data)
    return redirect('/wishes')


@app.route('/wishes/edit/<wish_id>')
def editWish(wish_id):
    db = connectToMySQL(SCHEMA)
    query = 'SELECT * FROM wishes where wishes.id = %(w_id)s;'
    data = {
        "w_id": wish_id
    }
    wish = db.query_db(query, data)

    wish=wish[0]
    return render_template('editWish.html', wish=wish)


@app.route('/wishes/edit_process', methods=['POST'])
def editWish_process():
    messages=[]
    wish = request.form['wish']
    desc = request.form['desc']
    
    if len(wish) < 3:
        messages.append("I'm not good with acrynoms. A wish must consist of at least 3 characters! Spell it out.")
    if len(desc) < 3:
        messages.append('Please tell me more. A description must be provided!')
    if messages:
        for message in messages:
            print('you got problems with your wishes')
            flash(message, 'wishErrors')
        return redirect (request.referrer)
    else:
        query='UPDATE wishes SET wish = %(wish)s, wish_description = %(desc)s Where wishes.id = %(w_id)s;'
    data= {
        'wish' : request.form['wish'],
        'desc' : request.form['desc'],
        'w_id' : request.form['w_id']
    }
    mysql=connectToMySQL(SCHEMA)
    mysql.query_db(query, data)
    return redirect('/wishes')


@app.route("/wishes/delete/<wish_id>")
def delete(wish_id):
    query='DELETE FROM wishes Where wishes.id = %(w_id)s;'
    data= {
        "w_id": wish_id
    }
    mysql=connectToMySQL(SCHEMA)
    mysql.query_db(query, data)
    return redirect('/wishes')

@app.route("/wishes/grant/<wish_id>")
def grant(wish_id):
    query='UPDATE wishes SET date_granted = 1 Where wishes.id = %(w_id)s;'
    data= {
        "w_id": wish_id
    }
    mysql=connectToMySQL(SCHEMA)
    mysql.query_db(query, data)
    return redirect('/wishes')

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__=="__main__":
    app.run(debug=True)
