from flask import Flask, render_template_string, send_file, jsonify
import threading
import time
import io
import mss
from PIL import Image
import pyautogui
import os

app = Flask(__name__)

ACCEPT_BUTTON_POS = (1033, 507)
DECLINE_BUTTON_POS = (1239, 665)
START_SEARCH_POS = (1687, 1020)
CANCEL_SEARCH_POS = (1843, 1029)

game_found = False
searching = False
paused = False
last_game_found_time = 0.0

HTML_TEMPLATE = """
<!doctype html>
<html>
  <head>
    <title>Dota 2: Remote Control</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
      body { font-family: 'Segoe UI', sans-serif; background: #121212; color: #eee; text-align: center; padding: 20px; margin: 0 auto; max-width: 480px; }
      h1, h2, h3 { margin: 0.5em 0; }
      img { max-width: 100%; border: 2px solid #444; border-radius: 8px; margin-bottom: 20px; }
      button { width: 90%; max-width: 400px; padding: 15px; font-size: 24px; border: none; border-radius: 8px; cursor: pointer; margin: 10px auto; display: block; }
      .start { background: #1565c0; color: #fff; }
      .accept { background: #2e7d32; color: #fff; }
      .decline { background: #b71c1c; color: #fff; }
      .cancel { background: #ffa000; color: #fff; }
      .resume { background: #607d8b; color: #fff; }
    </style>
    <script>
      let uiInterval, screenshotInterval;
      let alertPlayed = false;

      function playAlert() {
        const audio = new Audio('/static/alert.mp3');
        audio.play();
      }

      function sendAction(path) {
        fetch(path, {cache: 'no-store'}).then(updateUI);
      }

      function updateStatus() {
        return fetch('/status?ts=' + Date.now()).then(r => r.json());
      }

      function updateUI() {
        updateStatus().then(data => {
          const div = document.getElementById('controls');
          div.innerHTML = '';
          if (data.paused) {
            clearInterval(uiInterval);
            clearInterval(screenshotInterval);
            alertPlayed = false;
            div.innerHTML = `<h2 style="color:orange;">Пауза</h2><button class="resume" onclick="resumeApp()">Продолжить</button>`;
          } else if (data.game_found) {
            if (!alertPlayed) {
              playAlert();
              alertPlayed = true;
            }
            div.innerHTML = `<h2 style="color:#4caf50;">Матч найден!</h2><button class="accept" onclick="sendAction('/accept')">Принять</button><button class="decline" onclick="sendAction('/decline')">Отклонить</button>`;
          } else if (data.searching) {
            alertPlayed = false;
            div.innerHTML = `<h2>Поиск...</h2><button class="cancel" onclick="sendAction('/cancel_search')">Отменить поиск</button>`;
          } else {
            alertPlayed = false;
            div.innerHTML = `<h2>Матч не найден</h2><button class="start" onclick="sendAction('/start_search')">Начать поиск</button>`;
          }
        });
      }

      function updateScreenshot() {
        const img = document.getElementById('screenshot');
        img.src = '/screenshot?ts=' + Date.now();
      }

      function resumeApp() {
        fetch('/resume').then(() => {
          updateUI();
          uiInterval = setInterval(updateUI, 1000);
          screenshotInterval = setInterval(updateScreenshot, 700);
        });
      }

      window.onload = () => {
        updateUI();
        uiInterval = setInterval(updateUI, 1000);
        screenshotInterval = setInterval(updateScreenshot, 700);
      };
    </script>
  </head>
  <body>
    <h1>Dota 2 Remote</h1>
    <div id="controls"></div>
    <h3>Скриншот:</h3>
    <img id="screenshot" src="/screenshot" alt="screenshot">
  </body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/status')
def status():
    return jsonify({'game_found': game_found, 'searching': searching, 'paused': paused})

@app.route('/screenshot')
def screenshot():
    if paused:
        return ('', 204)
    with mss.mss() as sct:
        img = sct.grab(sct.monitors[0])
        im = Image.frombytes('RGB', img.size, img.rgb)
        buf = io.BytesIO()
        im.save(buf, format='JPEG', quality=17)
        buf.seek(0)
        return send_file(buf, mimetype='image/jpeg')

@app.route('/start_search')
def start_search():
    def act():
        for _ in range(2):
            pyautogui.moveTo(*START_SEARCH_POS)
            pyautogui.click()
            time.sleep(0.3)
    threading.Thread(target=act).start()
    global game_found, searching, paused
    game_found = False
    searching = True
    paused = False
    return ('', 204)

@app.route('/cancel_search')
def cancel_search():
    def act():
        pyautogui.moveTo(*CANCEL_SEARCH_POS)
        pyautogui.click()
    threading.Thread(target=act).start()
    global searching
    searching = False
    return ('', 204)

@app.route('/accept')
def accept():
    def act():
        pyautogui.moveTo(*ACCEPT_BUTTON_POS)
        pyautogui.click()
    threading.Thread(target=act).start()
    global searching, paused, game_found
    searching = False
    paused = True
    game_found = True
    return ('', 204)

@app.route('/decline')
def decline():
    def act():
        pyautogui.moveTo(*DECLINE_BUTTON_POS)
        pyautogui.click()
    threading.Thread(target=act).start()
    global game_found, searching
    game_found = False
    searching = True
    return ('', 204)

@app.route('/resume')
def resume():
    global paused, game_found
    paused = False
    game_found = False
    return ('', 204)

def monitor_accept():
    global game_found, searching, last_game_found_time
    while True:
        if not paused and searching:
            try:
                loc = pyautogui.locateOnScreen('accept_button.png', confidence=0.8)
                now = time.time()
                if loc:
                    if now - last_game_found_time > 3.5:
                        game_found = True
                        last_game_found_time = now
                else:
                    game_found = False
            except Exception:
                game_found = False
        time.sleep(0.7)

if __name__ == '__main__':
    threading.Thread(target=monitor_accept, daemon=True).start()
    app.run(host='0.0.0.0', port=5000)
