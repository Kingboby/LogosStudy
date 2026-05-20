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
        document.getElementById('btn-start-pause').textContent = 'Start';
    } else {
        isRunning = true;
        document.getElementById('btn-start-pause').textContent = 'Pause';
        vTimerInterval = setInterval(fnTick, 1000);
    }
}

function fnResetTimer() {
    clearInterval(vTimerInterval);
    isRunning = false;
    isBreak = false;
    vSecondsLeft = vTotalSeconds;
    document.getElementById('btn-start-pause').textContent = 'Start';
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
    document.getElementById('btn-start-pause').textContent = 'Start';

    if (isPomodoro) {
        if (!isBreak) {
            fnSaveSession(POMODORO_WORK, 'Pomodoro');
            isBreak = true;
            vSecondsLeft = POMODORO_BREAK;
            vTotalSeconds = POMODORO_BREAK;
            fnUpdateDisplay();
            isRunning = true;
            document.getElementById('btn-start-pause').textContent = 'Pause';
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
    document.getElementById('btn-start-pause').textContent = 'Start';
    document.getElementById('custom-input').style.display = 'none';
    fnUpdateDisplay();
    fnSetActiveMode('btn-pomodoro');
}

function fnSetCustom() {
    clearInterval(vTimerInterval);
    isRunning = false;
    isPomodoro = false;
    document.getElementById('custom-input').style.display = 'block';
    document.getElementById('btn-start-pause').textContent = 'Start';
    fnSetActiveMode('btn-custom');
}

function fnApplyCustomTime() {
    const vMinutes = parseInt(document.getElementById('custom-minutes').value);
    if (vMinutes > 0 && vMinutes <= 180) {
        vSecondsLeft = vMinutes * 60;
        vTotalSeconds = vSecondsLeft;
        fnUpdateDisplay();
    }
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

fnUpdateDisplay();
