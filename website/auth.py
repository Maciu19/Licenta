from flask import Blueprint, render_template, session, request, flash, redirect, url_for
import json
from . import pb
from requests.exceptions import HTTPError
from . import authorize, is_logged_in

auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['POST', 'GET'])
def login():
    if is_logged_in():
        return redirect(url_for("views.home"))
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        try:
            user = pb.auth().sign_in_with_email_and_password(email, password)
            session['authorization'] = user['idToken']

            flash('Autentificare cu succes', category='success')
            return redirect(url_for('views.home'))
        except HTTPError as err:
            if json.loads(err.strerror)['error']['message'] == 'EMAIL_NOT_FOUND':
                flash('Email-ul nu exista', category='error')
            elif json.loads(err.strerror)['error']['message'] == 'INVALID_PASSWORD':
                flash('Parola incorecta, încearca din nou', category='error')
            elif json.loads(err.strerror)['error']['message'] == 'INVALID_EMAIL':
                flash('Completează email-ul', category='error')
            elif json.loads(err.strerror)['error']['message'] == 'MISSING_PASSWORD':
                flash('Completează parola', category='error')

    return render_template('login.html')

@auth.route('/logout')
@authorize
def logout():
    session.clear()
    flash('Ieșire din cont cu succes', category='success')
    return redirect(url_for('auth.login'))

@auth.route('/signup', methods=['POST', 'GET'])
def signup():
    if is_logged_in():
        return redirect(url_for("views.home"))
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        try:
            user = pb.auth().create_user_with_email_and_password(email, password)
            session['authorization'] = user['idToken']

            flash('Cont creat!', category='success')
            return redirect(url_for('views.home'))
        except HTTPError as err:
            if json.loads(err.strerror)['error']['message'] == 'EMAIL_EXISTS':
                flash('Email-ul este deja folosit', category='error')
            elif json.loads(err.strerror)['error']['message'] == 'INVALID_EMAIL':
                flash('Completează email-ul', category='error')
            elif json.loads(err.strerror)['error']['message'] == 'MISSING_PASSWORD':
                flash('Completează parola', category='error')
            elif json.loads(err.strerror)['error']['message'] == 'WEAK_PASSWORD : Password should be at least 6 characters':
                flash('Parola trebuie sa aiba cel puțin 6 caractere', category='error')        

    return render_template('signup.html')
