from flask import Flask, render_template

app = Flask(__name__)


@app.route('/')
@app.route('/welcome')
def welcome():
    return render_template('welcome.html')


@app.route('/home')
def home():
    return render_template('home.html')


@app.route('/library')
def library():
    return render_template('library.html')


@app.route('/community')
def community():
    return render_template('community.html')


@app.route('/profile')
def profile():
    return render_template('profile.html')


@app.route('/login')
def login():
    return render_template('auth/login.html')


@app.route('/register')
def register():
    return render_template('auth/register.html')


@app.route('/offline')
def offline():
    return render_template('offline.html')


if __name__ == '__main__':
    app.run(debug=True)
