import os
from datetime import date, timedelta
from sqlalchemy import func
from flask import Flask, render_template, redirect, url_for, request, send_from_directory, abort, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db, loginManager
from models import User, StudySession

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


def fnBuildActivityGrid(dctSessionCounts):
    vToday = date.today()
    vEndDate = vToday + timedelta(days=(6 - vToday.weekday()))
    vStartDate = vEndDate - timedelta(days=363)

    lstWeeks = []
    lstMonthLabels = []
    vSeenMonths = set()

    for vWeekIndex in range(52):
        lstWeek = []
        for vDayIndex in range(7):
            vDate = vStartDate + timedelta(weeks=vWeekIndex, days=vDayIndex)
            vDateStr = vDate.strftime("%Y-%m-%d")
            vCount = dctSessionCounts.get(vDateStr, 0) if vDate <= vToday else 0
            vCssClass = "day-" + str(min(vCount, 3))
            lstWeek.append({"date": vDateStr, "count": vCount, "css_class": vCssClass})

            vMonthKey = (vDate.year, vDate.month)
            if vMonthKey not in vSeenMonths:
                vSeenMonths.add(vMonthKey)
                lstMonthLabels.append({"label": vDate.strftime("%b"), "col": vWeekIndex})

        lstWeeks.append(lstWeek)

    return lstWeeks, lstMonthLabels


@app.route("/")
@app.route("/welcome")
def fnRouteWelcome():
    return render_template("welcome.html")


@app.route("/home")
@login_required
def fnRouteDashboard():
    vToday = date.today()
    vYearAgo = vToday - timedelta(days=364)

    lstRawCounts = (
        db.session.query(
            func.date(StudySession.date).label("session_date"),
            func.count(StudySession.id).label("session_count")
        )
        .filter(StudySession.user_id == current_user.id)
        .filter(StudySession.date >= vYearAgo)
        .group_by(func.date(StudySession.date))
        .all()
    )

    dctSessionCounts = {str(row.session_date): row.session_count for row in lstRawCounts}
    lstActivityGrid, lstMonthLabels = fnBuildActivityGrid(dctSessionCounts)

    return render_template("home.html",
        tmplStreak=current_user.streak,
        tmplActivityGrid=lstActivityGrid,
        tmplMonthLabels=lstMonthLabels
    )


@app.route("/register", methods=["GET", "POST"])
def fnRouteRegister():
    if request.method == "POST":
        frmUsername = request.form.get("username")
        frmPassword = request.form.get("password")

        isUsernameTaken = User.query.filter_by(username=frmUsername).first()
        if isUsernameTaken:
            return render_template("auth/register.html",
                tmplError="That username is already taken. Please choose a different one.")

        vHashedPassword = generate_password_hash(frmPassword)
        dbUser = User(username=frmUsername, password=vHashedPassword)
        db.session.add(dbUser)
        db.session.commit()
        login_user(dbUser)
        return redirect(url_for("fnRouteDashboard"))

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
        return render_template("auth/login.html",
            tmplError="Incorrect username or password.")
    return render_template("auth/login.html")


@app.route("/logout")
@login_required
def fnRouteLogout():
    logout_user()
    return redirect(url_for("fnRouteLogin"))


@app.route("/save-session", methods=["POST"])
@login_required
def fnRouteSaveSession():
    vData = request.get_json()
    vDuration = vData.get("duration")
    vSessionType = vData.get("session_type")

    dbSession = StudySession(
        user_id=current_user.id,
        duration=vDuration,
        session_type=vSessionType
    )
    db.session.add(dbSession)

    vToday = date.today()
    vLastActive = current_user.last_active

    if vLastActive is None or (vToday - vLastActive).days > 1:
        current_user.streak = 1
    elif (vToday - vLastActive).days == 1:
        current_user.streak += 1

    current_user.last_active = vToday
    db.session.commit()

    return jsonify({"streak": current_user.streak})


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
@login_required
def fnRouteCommunity():
    return render_template("community.html")


@app.route("/profile")
@login_required
def fnRouteProfile():
    return render_template("profile.html")


@app.route("/offline")
def fnRouteOffline():
    return render_template("offline.html")


with app.app_context():
    db.create_all()


if __name__ == "__main__":
    app.run(debug=True)
