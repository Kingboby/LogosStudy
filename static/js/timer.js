const POMODORO_WORK = 1500;
const POMODORO_BREAK = 300;

let vSecondsLeft = POMODORO_WORK;
let vTotalSeconds = POMODORO_WORK;
let vTimerInterval = null;
let isRunning = false;
let isPomodoro = true;
let isBreak = false;
let isFullscreen = false;

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

function fnUpdateRing() {
    const vCircle = document.getElementById('timer-ring-progress');
    if (!vCircle) return;
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

function fnTick() {
    if (vSecondsLeft > 0) {
        vSecondsLeft--;
        fnUpdateDisplay();
    } else {
        fnOnTimerEnd();
    }
}

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

function fnResetTimer() {
    clearInterval(vTimerInterval);
    isRunning = false;
    isBreak = false;
    vSecondsLeft = vTotalSeconds;
    document.getElementById('btn-start-pause').textContent = '▶ start';
    fnLockTimeDisplay();
    fnUpdateDisplay();
}

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

function fnOnTimerEnd() {
    clearInterval(vTimerInterval);
    isRunning = false;
    document.getElementById('btn-start-pause').textContent = '▶ start';

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

function fnSetCustom() {
    clearInterval(vTimerInterval);
    isRunning = false;
    isPomodoro = false;
    document.getElementById('btn-start-pause').textContent = '▶ start';
    fnUnlockTimeDisplay();
    fnSetActiveMode('btn-custom');
}

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

function fnLockTimeDisplay() {
    document.getElementById('timer-time').contentEditable = 'false';
}

function fnApplyCustomTime() {
    const vTimeEl = document.getElementById('timer-time');
    const vText = vTimeEl.textContent.trim();
    let vTotalSecs = 0;

    if (vText.includes(':')) {
        const vParts = vText.split(':');
        vTotalSecs = parseInt(vParts[0]) * 60 + parseInt(vParts[1]);
    } else {
        vTotalSecs = parseInt(vText) * 60;
    }

    if (vTotalSecs > 0 && vTotalSecs <= 10800) {
        vSecondsLeft = vTotalSecs;
        vTotalSeconds = vTotalSecs;
    }

    fnLockTimeDisplay();
    fnUpdateDisplay();
}

function fnSetActiveMode(vActiveId) {
    document.querySelectorAll('.timer-mode-btn').forEach(function(vBtn) {
        vBtn.classList.remove('active');
    });
    document.getElementById(vActiveId).classList.add('active');
}

function fnToggleFullscreen() {
    const vWidget = document.getElementById('timer-widget');
    isFullscreen = !isFullscreen;
    vWidget.classList.toggle('timer-fullscreen', isFullscreen);
    document.getElementById('btn-fullscreen').textContent =
        isFullscreen ? 'Exit Full Focus' : 'Full Focus';
}

document.getElementById('timer-time').addEventListener('keydown', function(vEvent) {
    if (vEvent.key === 'Enter') {
        vEvent.preventDefault();
        fnApplyCustomTime();
    }
});

document.getElementById('timer-time').addEventListener('click', function() {
    if (!isPomodoro && !isRunning) {
        fnUnlockTimeDisplay();
    }
});

fnUpdateDisplay();
