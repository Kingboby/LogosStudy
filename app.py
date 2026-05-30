import os
import requests
from datetime import date, datetime, timedelta
from icalendar import Calendar as ICalendar
from sqlalchemy import func
from flask import Flask, render_template, redirect, url_for, request, send_from_directory, abort, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db, loginManager
from models import User, StudySession, Goal

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
    vStartDate = vEndDate - timedelta(days=181)

    lstWeeks = []
    lstMonthLabels = []
    vSeenMonths = set()

    for vWeekIndex in range(26):
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
    vSixMonthsAgo = vToday - timedelta(days=182)

    lstRawCounts = (
        db.session.query(
            func.date(StudySession.date).label("session_date"),
            func.count(StudySession.id).label("session_count")
        )
        .filter(StudySession.user_id == current_user.id)
        .filter(StudySession.date >= vSixMonthsAgo)
        .group_by(func.date(StudySession.date))
        .all()
    )

    dctSessionCounts = {str(row.session_date): row.session_count for row in lstRawCounts}
    lstActivityGrid, lstMonthLabels = fnBuildActivityGrid(dctSessionCounts)

    lstIncompleteGoals = (
        Goal.query
        .filter_by(user_id=current_user.id, is_complete=False)
        .order_by(Goal.created_at.desc())
        .limit(5)
        .all()
    )
    lstAllGoals = (
        Goal.query
        .filter_by(user_id=current_user.id)
        .order_by(Goal.is_complete.asc(), Goal.created_at.desc())
        .all()
    )

    vHour = datetime.now().hour
    if vHour < 12:
        vGreeting = "Good morning"
    elif vHour < 17:
        vGreeting = "Good afternoon"
    else:
        vGreeting = "Good evening"

    vDateDisplay = vToday.strftime("%a").upper() + " " + str(vToday.day) + " " + vToday.strftime("%b").upper()
    vWeekNum = vToday.isocalendar()[1]

    vFourteenDaysAgo = vToday - timedelta(days=13)
    lstLast14Raw = (
        db.session.query(
            func.date(StudySession.date).label("session_date"),
            func.count(StudySession.id).label("session_count")
        )
        .filter(StudySession.user_id == current_user.id)
        .filter(StudySession.date >= vFourteenDaysAgo)
        .group_by(func.date(StudySession.date))
        .all()
    )
    dctLast14Counts = {str(row.session_date): row.session_count for row in lstLast14Raw}
    lstLast14Days = []
    for vDayOffset in range(13, -1, -1):
        vDayDate = vToday - timedelta(days=vDayOffset)
        vDayStr = vDayDate.strftime("%Y-%m-%d")
        vDayCount = dctLast14Counts.get(vDayStr, 0)
        lstLast14Days.append({
            "date": vDayStr,
            "css_class": "day-" + str(min(vDayCount, 3))
        })

    vGoalTotalCount = Goal.query.filter_by(user_id=current_user.id).count()
    vGoalCompleteCount = Goal.query.filter_by(user_id=current_user.id, is_complete=True).count()

    return render_template("home.html",
        tmplStreak=current_user.streak,
        tmplActivityGrid=lstActivityGrid,
        tmplMonthLabels=lstMonthLabels,
        tmplIncompleteGoals=lstIncompleteGoals,
        tmplAllGoals=lstAllGoals,
        tmplUsername=current_user.username,
        tmplLongestStreak=current_user.longest_streak,
        tmplLast14Days=lstLast14Days,
        tmplGreeting=vGreeting,
        tmplDateStr=vDateDisplay,
        tmplWeekNum=vWeekNum,
        tmplGoalTotalCount=vGoalTotalCount,
        tmplGoalCompleteCount=vGoalCompleteCount
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
    if current_user.streak > current_user.longest_streak:
        current_user.longest_streak = current_user.streak
    db.session.commit()

    return jsonify({"streak": current_user.streak})


@app.route("/goal/add", methods=["POST"])
@login_required
def fnRouteAddGoal():
    vData = request.get_json()
    vDescription = vData.get("description", "").strip()
    if not vDescription:
        return jsonify({"error": "Description is empty"}), 400
    dbGoal = Goal(user_id=current_user.id, description=vDescription)
    db.session.add(dbGoal)
    db.session.commit()
    return jsonify({
        "id": dbGoal.id,
        "description": dbGoal.description,
        "is_complete": dbGoal.is_complete
    })


@app.route("/goal/complete/<int:vGoalId>", methods=["POST"])
@login_required
def fnRouteGoalComplete(vGoalId):
    dbGoal = Goal.query.get_or_404(vGoalId)
    if dbGoal.user_id != current_user.id:
        return jsonify({"error": "Unauthorised"}), 403
    dbGoal.is_complete = not dbGoal.is_complete
    db.session.commit()
    return jsonify({"id": dbGoal.id, "is_complete": dbGoal.is_complete})


@app.route("/goal/delete/<int:vGoalId>", methods=["POST"])
@login_required
def fnRouteDeleteGoal(vGoalId):
    dbGoal = Goal.query.get_or_404(vGoalId)
    if dbGoal.user_id != current_user.id:
        return jsonify({"error": "Unauthorised"}), 403
    db.session.delete(dbGoal)
    db.session.commit()
    return jsonify({"deleted": vGoalId})


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


@app.route("/calendar")
@login_required
def fnRouteCalendar():
    if not current_user.calendar_url:
        return render_template("calendar.html",
            tmplShowSetup=True,
            tmplCalendarUrl=None
        )

    vToday = date.today()
    lstEvents = []

    try:
        vResponse = requests.get(current_user.calendar_url, timeout=10)
        vResponse.raise_for_status()
        vCal = ICalendar.from_ical(vResponse.content)

        for vComponent in vCal.walk():
            if vComponent.name != "VEVENT":
                continue
            vDtstart = vComponent.get("DTSTART")
            if vDtstart is None:
                continue
            vStart = vDtstart.dt

            if isinstance(vStart, datetime):
                if vStart.tzinfo:
                    vStart = vStart.replace(tzinfo=None)
                vStartDate = vStart.date()
                vDisplayDate = vStart.strftime("%a %d %b")
                vDisplayTime = vStart.strftime("%H:%M")
            else:
                vStartDate = vStart
                vDisplayDate = vStart.strftime("%a %d %b")
                vDisplayTime = "all day"

            if vStartDate < vToday:
                continue

            lstEvents.append({
                "title": str(vComponent.get("SUMMARY", "Untitled event")),
                "start": vStart,
                "description": str(vComponent.get("DESCRIPTION", "")),
                "display_date": vDisplayDate,
                "display_time": vDisplayTime
            })

        lstEvents.sort(key=lambda e: e["start"] if isinstance(e["start"], datetime)
            else datetime(e["start"].year, e["start"].month, e["start"].day))
        lstEvents = lstEvents[:20]

    except Exception:
        return render_template("calendar.html",
            tmplShowSetup=True,
            tmplCalendarUrl=current_user.calendar_url,
            tmplError="Could not load calendar."
        )

    return render_template("calendar.html",
        tmplShowSetup=False,
        tmplEvents=lstEvents,
        tmplCalendarUrl=current_user.calendar_url
    )


@app.route("/calendar/save-url", methods=["POST"])
@login_required
def fnRouteSaveCalendarUrl():
    frmCalendarUrl = request.form.get("calendar_url", "").strip()
    if not frmCalendarUrl or not frmCalendarUrl.endswith(".ics"):
        return redirect(url_for("fnRouteCalendar"))
    current_user.calendar_url = frmCalendarUrl
    db.session.commit()
    return redirect(url_for("fnRouteCalendar"))


@app.route("/profile")
@login_required
def fnRouteProfile():
    vTotalSessions = StudySession.query.filter_by(user_id=current_user.id).count()
    vTotalSeconds = db.session.query(func.sum(StudySession.duration)).filter(StudySession.user_id == current_user.id).scalar() or 0
    vTotalMinutes = round(vTotalSeconds / 60)
    return render_template("profile.html",
        tmplUsername=current_user.username,
        tmplTotalSessions=vTotalSessions,
        tmplTotalMinutes=vTotalMinutes
    )


@app.route("/offline")
def fnRouteOffline():
    return render_template("offline.html")


with app.app_context():
    db.create_all()


if __name__ == "__main__":
    app.run(debug=True)
