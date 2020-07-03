from flask import Flask,render_template,request,session,redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json
from flask_mail import Mail
import os
from werkzeug.utils import secure_filename
import math

with open('config.json','r') as c:
    params = json.load(c)["params"]
local_server = True

app = Flask(__name__)
app.secret_key = 'super-secret-key'
app.config['UPLOAD_FOLDER'] = params['upload_location']
app.config.update(
    MAIL_SERVER = 'smtp.gmail.com',
    MAIL_PORT = '465',
    MAIL_USE_SSL = True,
    MAIL_USERNAME= params["gmail-user"],
    MAIL_PASSWORD= params["gmail-password"]
)

mail = Mail(app)

if local_server:
    app.config['SQLALCHEMY_DATABASE_URI'] = params['local_uri']
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = params['prod_uri']

db = SQLAlchemy(app)


class Contacts(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=False, nullable=False)
    phone_num = db.Column(db.String(15), unique=True, nullable=False)
    msg = db.Column(db.String(500), nullable=False)
    date = db.Column(db.String(12),nullable=True)
    email = db.Column(db.String(120), unique=True, nullable=False)

class Codes(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), nullable=False)
    subheading = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(15), nullable=False)
    content = db.Column(db.String(500), nullable=False)
    date = db.Column(db.String(12),nullable=True)
    img_file = db.Column(db.String(30),nullable=True)

@app.route('/')
def home():
    codes = Codes.query.filter_by().all()
    last = math.ceil(len(codes)/params["no_of_posts"])

    page = request.args.get('page')
    if not str(page).isnumeric():
        page = 1
    page = int(page)

    codes = codes[(page-1)*params["no_of_posts"]:min(page*params["no_of_posts"],len(codes))]

    
    if page==1:
        prev='#'
        next = '/?page='+str(page+1)
    elif page==last:
        prev = '/?page='+str(page-1)
        next='#'
    else:
        prev = '/?page='+str(page-1)
        next = '/?page='+str(page+1)

    return render_template('index.html',params=params,codes=codes,prev=prev,next=next)

@app.route('/about')
def about():
    return render_template('about.html',params=params)

@app.route('/dashboard',methods=['GET','POST'])
def dashboard():

    if 'user' in session and session['user'] == params['admin_user']:
        codes = Codes.query.all()
        return render_template('dashboard.html',params=params,codes=codes)
    
    if request.method=='POST':
        
        username = request.form.get('uname')
        userpass = request.form.get('pass')
        print(username)
        if username==params['admin_user'] and userpass==params['admin_password']:
            session['user'] = username
            codes = Codes.query.all()
            return render_template('dashboard.html',params=params,codes=codes)
    
    return render_template('login.html',params=params)

@app.route('/edit/<string:sno>',methods=['GET','POST'])
def edit(sno):
    
    if 'user' in session and session['user']==params['admin_user']:
        if request.method=='POST':
            title = request.form.get('title')
            subheading = request.form.get('subheading')
            slug = request.form.get('slug')
            content = request.form.get('content')
            img_file = request.form.get('img_file')
            date = datetime.now()
            
            if sno=='0':
                code = Codes(title=title,subheading=subheading,slug=slug,content=content,img_file=img_file,date = date)
                db.session.add(code)
                db.session.commit()
            else:
                code = Codes.query.filter_by(sno=sno).first()
                code.title = title
                code.subheading = subheading
                code.slug = slug
                code.content = content
                code.img_file = img_file
                code.date = code.date
                db.session.add(code)
                db.session.commit()
                return redirect('/edit/'+sno)
        
        code = Codes.query.filter_by(sno=sno).first()
        return render_template('edit.html',params=params,code=code)

@app.route('/uploader',methods=['GET','POST'])
def uploader():
    if 'user' in session and session['user']==params['admin_user']:
        if request.method=='POST':
            f = request.files['file1']
            f.save(os.path.join(app.config['UPLOAD_FOLDER'],
            secure_filename(f.filename)))
            return "Uploaded Successfully !!"

@app.route('/logout')
def logout():
    session.pop('user')
    return redirect('/')

@app.route('/delete/<string:sno>')
def delete(sno):
    if 'user' in session and session['user']==params['admin_user']:
        code = Codes.query.filter_by(sno=sno).first()
        db.session.delete(code)
        db.session.commit()
        return redirect('/dashboard')

@app.route('/contact',methods=['GET','POST'])
def contact():
    if(request.method=='POST'):
        ''' Add entry to the database '''
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone_num')
        message = request.form.get('msg')

        entry = Contacts(name=name,phone_num=phone,msg=message,
                        email=email,date=datetime.now())
        db.session.add(entry)
        db.session.commit()
        print(params['gmail-user'])
        mail.send_message("New message from "+name,
                            sender=email,
                            recipients=[params['gmail-user']],
                            body = message+'\n'+phone)
    return render_template('contact.html',params=params)

@app.route('/code/<string:code_slug>',methods=['GET'])
def code_route(code_slug):
    code = Codes.query.filter_by(slug=code_slug).first()
    return render_template('code.html',params=params,code=code)


@app.route('/code')
def code():
    code = Codes(title='Heaven of Codes',subheading='My Girlfriend speaks binary',
                date='1st September',img_file='code-home4.jpg',content='Coding is my last love')
    return render_template('code.html',params=params,code=code)

app.run(debug=True)