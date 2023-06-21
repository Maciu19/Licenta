from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from . import authorize, is_logged_in, storage
from .auth import auth
from .preprocess_model_violenta import execute_model
from .preprocesare_model_bagaje import execute_model_bagaje
import os
import time
import ffmpeg
from . import pb

views = Blueprint('views', __name__)

@views.route('/')
def root():
    if is_logged_in():
        return redirect(url_for('views.home'))
    else:
        return redirect(url_for("auth.login"))
    
@views.route('/profil', methods=['POST', 'GET'])
@authorize
def profil():
    token = session['authorization']
    info = pb.auth().get_account_info(token)["users"][0]

    email_verificat = info['emailVerified']
    email = info["email"]

    if request.method == 'POST':
        if "verificare_email" in request.form:
            pb.auth().send_email_verification(token)
            flash('Verifică email-ul', category='success')
        elif "schimbare_parola" in request.form:
            pb.auth().send_password_reset_email(email)
            flash('Verifică email-ul și schimbă parola', category='success')

    return render_template('profile.html', email=email, email_verificat=email_verificat)

@views.route('/home')
@authorize
def home():
    return render_template('home.html')

@views.route('/model1', methods=['POST', 'GET'])
@authorize
def model1():
    if request.method == 'POST':
        try:
            f = request.files['video_file']
            
            f.save(f.filename)
            execute_model(f.filename)

            intrare_stream = ffmpeg.input('output.mp4')
            iesire_stream = ffmpeg.output(intrare_stream, 'output2.mp4', vcodec='h264')
            ffmpeg.run(iesire_stream)

            os.remove(f.filename)
            os.remove('output.mp4')

            email = pb.auth().get_account_info(session['authorization'])["users"][0]["email"]
            curr_time = time.time()

            storage.child(f'/storage/model1/{email}/{f.filename}_{curr_time}.mp4').put('output2.mp4')  
            url = storage.child(f'/storage/model1/{email}/{f.filename}_{curr_time}.mp4').get_url(None)

            os.remove('output2.mp4')

            return render_template('model1.html', url=url)
        except FileNotFoundError:
            flash('Încarcă un fișier', category='error')

    return render_template('model1.html')

@views.route('/model2', methods=['POST', 'GET'])
@authorize
def model2():
    if request.method == 'POST':
        try:
            f = request.files['video_file']

            f.save(f.filename)
            execute_model_bagaje(f.filename)

            intrare_stream = ffmpeg.input('output.mp4')
            iesire_stream = ffmpeg.output(intrare_stream, 'output2.mp4', vcodec='h264')
            ffmpeg.run(iesire_stream)

            os.remove(f.filename)
            os.remove('output.mp4')

            email = pb.auth().get_account_info(session['authorization'])["users"][0]["email"]
            timp_curent = time.time()

            storage.child(f'/storage/model2/{email}/{f.filename}_{timp_curent}.mp4').put('output2.mp4')  
            url = storage.child(f'/storage/model2/{email}/{f.filename}_{timp_curent}.mp4').get_url(None)

            os.remove('output2.mp4')

            return render_template('model2.html', url=url)
        except FileNotFoundError:
            flash('Încarcă un fișier', category='error')

    return render_template('model2.html')

@views.route('/history')
@authorize
def history():
    email = pb.auth().get_account_info(session['authorization'])["users"][0]["email"]
    files = storage.child().list_files()
    
    linkuri_model1 = []
    nume_model1 = []

    linkuri_model2 = []
    nume_model2 = []

    for file in files:
        if file.name == 'storage/':
            continue
        if file.name.split('/')[2] == email:
            if file.name.split('/')[1] == 'model1':
                linkuri_model1.append(storage.child(file.name).get_url(None))
                nume_model1.append(file.name)
            elif file.name.split('/')[1] == 'model2':
                linkuri_model2.append(storage.child(file.name).get_url(None))
                nume_model2.append(file.name)

    return render_template('history.html', linkuri_model1=linkuri_model1, linkuri_model2=linkuri_model2, nume_model1=nume_model1, nume_model2=nume_model2)