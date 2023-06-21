from flask import Flask, session, request, flash, url_for, redirect
from functools import wraps
import pyrebase
import json

pb = pyrebase.initialize_app(json.load(open('website/config/fbconfig.json')))
storage = pb.storage()

def create_app():
    app = Flask(__name__)

    with open("website/config/secret.txt") as f:
        secret = f.readlines()
    app.secret_key = secret
    
    from .views import views
    from .auth import auth
    from .preprocess_model_violenta import execute_model
    from .preprocesare_model_bagaje import execute_model_bagaje

    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')

    return app

def authorize(f):
    @wraps(f)
    async def decorated_function(*args,**kwargs):   
        try:
            not_check = False
            if (request.referrer and request.referrer.endswith(url_for('auth.login'))) or (request.referrer and request.referrer.endswith(url_for('auth.signup'))):
                # request.reffer = contine URL-ul de unde a venit request-ul
                # Daca request-ul vine de la login sau sign-up nu vom verifica token-ul pentru ca sigur este valid
                not_check = True

            if not_check == True:
                return f(*args, **kwargs)

            if not 'authorization' in session:
                session.clear()
                return redirect(url_for("auth.login"))
            
            user = pb.auth().get_account_info(session['authorization'])
        
        except Exception as e:
            session.clear()
            flash('Autentifică-te din nou', category='error')
            return redirect(url_for("auth.login"))
        
        return f(*args, **kwargs)
    return decorated_function

def is_logged_in():
    try:
        if not 'authorization' in session:
            return False
        else:
            user = pb.auth().get_account_info(session['authorization'])
            if user:
                return True
            return False
    except Exception:
        session.clear()
        flash('Autentifică-te din nou', category='error')
        return redirect(url_for("auth.login"))