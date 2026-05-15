import os
from flask import Flask, render_template, redirect, url_for, request, send_from_directory, abort
from flask_login import login_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db, loginManager
from models import User

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///logos.db"
app.config["SECRET_KEY"] = "dev-secret-key"

db.init_app(app)
loginManager.init_app(app)

LIBRARY_ROOT = os.path.join("static", "library")


@loginManager.user_loader
def fnLoadUser(vUserId):
    return User.query.get(int(vUserId))


def fnScanFolder(vFolderPath):
    lstFolders = []
    lstFiles = []
    if not os.path.exists(vFolderPath):
        return lstFolders, lstFiles
    for vItem in sorted(os.listdir(vFolderPath)):
        vItemPath = os.path.join(vFolderPath, vItem)
        if os.path.isdir(vItemPath):
            lstFolders.append(vItem)
        elif os.path.isfile(vItemPath):
            lstFiles.append(vItem)
    return lstFolders, lstFiles


@app.route("/")
@app.route("/welcome")
def fnRouteWelcome():
    return render_template("welcome.html")


@app.route("/home")
@login_required
def fnRouteDashboard():
    return render_template("home.html")


@app.route("/register", methods=["GET", "POST"])
def fnRouteRegister():
    if request.method == "POST":
        frmUsername = request.form.get("username")
        frmPassword = request.form.get("password")
        vHashedPassword = generate_password_hash(frmPassword)
        dbUser = User(username=frmUsername, password=vHashedPassword)
        db.session.add(dbUser)
        db.session.commit()
        return redirect(url_for("fnRouteLogin"))
    return render_template("auth/register.html")


@app.route("/login", methods=["GET", "POST"])
def fnRouteLogin():
    if request.method == "POST":
        frmUsername = request.form.get("username")
        frmPassword = request.form.get("password")
        dbUser = User.query.filter_by(username=frmUsername).first()
        isValidUser = dbUser and check_password_hash(dbUser.password, frmPassword)
        if isValidUser:
            login_user(dbUser)
            return redirect(url_for("fnRouteDashboard"))
    return render_template("auth/login.html")


@app.route("/logout")
@login_required
def fnRouteLogout():
    logout_user()
    return redirect(url_for("fnRouteLogin"))


@app.route("/library")
@app.route("/library/<path:vSubPath>")
@login_required
def fnRouteLibrary(vSubPath=""):
    vRealRoot = os.path.realpath(LIBRARY_ROOT)
    vRealPath = os.path.realpath(os.path.join(LIBRARY_ROOT, vSubPath))

    if not vRealPath.startswith(vRealRoot):
        abort(403)

    if not os.path.isdir(vRealPath):
        abort(404)

    lstFolders, lstFiles = fnScanFolder(vRealPath)

    vParentPath = vSubPath.rsplit("/", 1)[0] if "/" in vSubPath else ""
    isAtRoot = vSubPath == ""

    return render_template("library.html",
        tmplFolders=lstFolders,
        tmplFiles=lstFiles,
        tmplSubPath=vSubPath,
        tmplParentPath=vParentPath,
        tmplIsAtRoot=isAtRoot,
        tmplCurrentFolder=os.path.basename(vSubPath) if vSubPath else "Library"
    )


@app.route("/download/<path:vFilePath>")
@login_required
def fnRouteDownload(vFilePath):
    vRealRoot = os.path.realpath(LIBRARY_ROOT)
    vRealFile = os.path.realpath(os.path.join(LIBRARY_ROOT, vFilePath))

    if not vRealFile.startswith(vRealRoot):
        abort(403)

    return send_from_directory(LIBRARY_ROOT, vFilePath, as_attachment=True)


@app.route("/community")
def fnRouteCommunity():
    return render_template("community.html")


@app.route("/profile")
def fnRouteProfile():
    return render_template("profile.html")


@app.route("/offline")
def fnRouteOffline():
    return render_template("offline.html")


with app.app_context():
    db.create_all()


if __name__ == "__main__":
    app.run(debug=True)
