// fixed pomodoro lengths in seconds
const POMODORO_WORK = 1500;
const POMODORO_BREAK = 300;

// live timer state shared across below functions
let vSecondsLeft = POMODORO_WORK;
let vTotalSeconds = POMODORO_WORK;
let vTimerInterval = null;
let isRunning = false;
let isPomodoro = true;
let isBreak = false;
let isFullscreen = false;

// redraws the mm:ss readout and the label + ring
function fnUpdateDisplay() {
    const vMinutes = Math.floor(vSecondsLeft / 60);
    const vSeconds = vSecondsLeft % 60;
    document.getElementById('timer-time').textContent =
        String(vMinutes).padStart(2, '0') + ':' + String(vSeconds).padStart(2, '0');

    if (isPomodoro) {
        document.getElementById('timer-label').textContent = isBreak ? 'Break' : 'Work';
    } else {
        document.getElementById('timer-label').textContent = 'Custom';
    }

    fnUpdateRing();
}

// draws coutndown ring - svg circle
function fnUpdateRing() {
    const vCircle = document.getElementById('timer-ring-progress');
    if (!vCircle) return;
    // dash the stroke to full circumference, then offset by elapsed timeout
    // fraction so the visible arc shrinks as time runs down
    const vCircumference = 2 * Math.PI * 70;
    const vProgress = vSecondsLeft / vTotalSeconds;
    vCircle.style.strokeDasharray = vCircumference;
    vCircle.style.strokeDashoffset = vCircumference * (1 - vProgress);

    const vTotalEl = document.getElementById('timer-total');
    if (vTotalEl) {
        const vTotalMins = Math.floor(vTotalSeconds / 60);
        const vTotalSecs = vTotalSeconds % 60;
        vTotalEl.textContent = '/ ' + String(vTotalMins).padStart(2, '0') + ':' + String(vTotalSecs).padStart(2, '0');
    }
}
// runs a second: counts down one second, or ends timer at 0
function fnTick() {
    if (vSecondsLeft > 0) {
        vSecondsLeft--;
        fnUpdateDisplay();
    } else {
        fnOnTimerEnd();
    }
}

// start button, pauses if running, otherwise starts
function fnToggleStartPause() {
    if (isRunning) {
        clearInterval(vTimerInterval);
        isRunning = false;
        document.getElementById('btn-start-pause').textContent = '▶ start';
    } else {
        isRunning = true;
        document.getElementById('btn-start-pause').textContent = '⏸ pause';
        vTimerInterval = setInterval(fnTick, 1000);
    }
}
// end button, stops timer, then resets the countdown back to full
function fnResetTimer() {
    clearInterval(vTimerInterval);
    isRunning = false;
    isBreak = false;
    vSecondsLeft = vTotalSeconds;
    document.getElementById('btn-start-pause').textContent = '▶ start';
    fnLockTimeDisplay();
    fnUpdateDisplay();
}
// posts a finished session to the server and updates streak count
function fnSaveSession(vDuration, vSessionType) {
    fetch('/save-session', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ duration: vDuration, session_type: vSessionType })
    })
    .then(function(vResponse) { return vResponse.json(); })
    .then(function(vData) {
        const vStreakEl = document.getElementById('streak-count');
        if (vStreakEl) {
            vStreakEl.textContent = vData.streak;
        }
    });
}
// handles the timer hitting 0
function fnOnTimerEnd() {
    clearInterval(vTimerInterval);
    isRunning = false;
    document.getElementById('btn-start-pause').textContent = '▶ start';

    // if pomodoro mode, a finished work block saves then auto starts the Break
    // a finished break resets to works
    // in custom mode just saves
    if (isPomodoro) {
        if (!isBreak) {
            fnSaveSession(POMODORO_WORK, 'Pomodoro');
            isBreak = true;
            vSecondsLeft = POMODORO_BREAK;
            vTotalSeconds = POMODORO_BREAK;
            fnUpdateDisplay();
            isRunning = true;
            document.getElementById('btn-start-pause').textContent = '⏸ pause';
            vTimerInterval = setInterval(fnTick, 1000);
        } else {
            isBreak = false;
            vSecondsLeft = POMODORO_WORK;
            vTotalSeconds = POMODORO_WORK;
            fnUpdateDisplay();
        }
    } else {
        fnSaveSession(vTotalSeconds, 'Custom');
    }
}
// switches to pomodoro and resets to 25min work
function fnSetPomodoro() {
    clearInterval(vTimerInterval);
    isRunning = false;
    isPomodoro = true;
    isBreak = false;
    vSecondsLeft = POMODORO_WORK;
    vTotalSeconds = POMODORO_WORK;
    document.getElementById('btn-start-pause').textContent = '▶ start';
    fnLockTimeDisplay();
    fnUpdateDisplay();
    fnSetActiveMode('btn-pomodoro');
}
// switches to custom mode and lets the user input custom
function fnSetCustom() {
    clearInterval(vTimerInterval);
    isRunning = false;
    isPomodoro = false;
    document.getElementById('btn-start-pause').textContent = '▶ start';
    fnUnlockTimeDisplay();
    fnSetActiveMode('btn-custom');
}
// makes the time display editable and selects its text
function fnUnlockTimeDisplay() {
    const vTimeEl = document.getElementById('timer-time');
    vTimeEl.contentEditable = 'true';
    vTimeEl.focus();
    const vRange = document.createRange();
    vRange.selectNodeContents(vTimeEl);
    const vSel = window.getSelection();
    vSel.removeAllRanges();
    vSel.addRange(vRange);
}
// makes the time display read only again
function fnLockTimeDisplay() {
    document.getElementById('timer-time').contentEditable = 'false';
}
// parses the typed custom time and if valid sets it as new duration
function fnApplyCustomTime() {
    const vTimeEl = document.getElementById('timer-time');
    const vText = vTimeEl.textContent.trim();
    let vTotalSecs = 0;
// accepts either mm:ss or a number of minutes
    if (vText.includes(':')) {
        const vParts = vText.split(':');
        vTotalSecs = parseInt(vParts[0]) * 60 + parseInt(vParts[1]);
    } else {
        vTotalSecs = parseInt(vText) * 60;
    }
// only sensible capped at 180 min
    if (vTotalSecs > 0 && vTotalSecs <= 10800) {
        vSecondsLeft = vTotalSecs;
        vTotalSeconds = vTotalSecs;
    }

    fnLockTimeDisplay();
    fnUpdateDisplay();
}
// highlights the chosen mode button and clears the other
function fnSetActiveMode(vActiveId) {
    document.querySelectorAll('.timer-mode-btn').forEach(function(vBtn) {
        vBtn.classList.remove('active');
    });
    document.getElementById(vActiveId).classList.add('active');
}
// toggles full focus view of timer
function fnToggleFullscreen() {
    const vWidget = document.getElementById('timer-widget');
    isFullscreen = !isFullscreen;
    vWidget.classList.toggle('timer-fullscreen', isFullscreen);
    document.getElementById('btn-fullscreen').textContent =
        isFullscreen ? 'Exit Full Focus' : 'Full Focus';
}
// enter confirms a typed custom time
document.getElementById('timer-time').addEventListener('keydown', function(vEvent) {
    if (vEvent.key === 'Enter') {
        vEvent.preventDefault();
        fnApplyCustomTime();
    }
});
// clicking the ime only enters edit if in custom timer while stopped
document.getElementById('timer-time').addEventListener('click', function() {
    if (!isPomodoro && !isRunning) {
        fnUnlockTimeDisplay();
    }
});
// load initial pomodoro 25min
fnUpdateDisplay();
