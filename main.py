import datetime
import fbchat # Fork from https://github.com/JustAnyones/fbchat
import json
import os
import requests
import warnings

from io import BytesIO
from PIL import Image
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

from config import (
    PHANTOMJS_PATH,
    MESSENGER_THREAD_ID,
    PAGALBUKAS_BASE_URL,
    PAGALBUKAS_USERNAME,
    PAGALBUKAS_PASSWORD
)

# Supress selenium errors
warnings.filterwarnings("ignore")

def session_from_cookies() -> fbchat.Session:
    """Takes facebook cookies and creates facebook session from them."""
    if os.path.exists("session.json"):
        try:
            with open("session.json") as f:
                cookies = json.load(f)
            return fbchat.Session.from_cookies(cookies)
        except Exception:
            return
    raise OSError("session.json file is not present")


client = fbchat.Client(session=session_from_cookies())

# Gets the thread we care about
threads = client.fetch_threads(limit=25)
thread = [t for t in threads if t.id == MESSENGER_THREAD_ID] or [None]
thread = thread[0]

if thread is None:
    exit("Thread does not exist")

# Time management
# You wouldn't have school during the weekend, would you?
current_date = datetime.datetime.utcnow()
current_date += datetime.timedelta(days=1)
wk_day = current_date.weekday()
if wk_day == 5:
    current_date += datetime.timedelta(days=2)
elif wk_day == 6:
    current_date += datetime.timedelta(days=1)

schedule_date = current_date.strftime("%Y-%m-%d")

# Starts PhantomJS headless browser driver
print("Start headless browser")
driver = webdriver.PhantomJS(PHANTOMJS_PATH)
driver.set_window_size(1980, 1080)
driver.get(f'https://{PAGALBUKAS_BASE_URL}/')

# pls dont hack
res = requests.post(f"https://{PAGALBUKAS_BASE_URL}/api/user/login", {
    "email": PAGALBUKAS_USERNAME,
    "password": PAGALBUKAS_PASSWORD
})
token = res.cookies["token"]

# Workaround for PhantomJS bug of assigning session cookies
try:
    driver.add_cookie({
        "name": "token",
        "value": token,
        "path": "/",
        "secure": False
    })
except Exception:
    driver.add_cookie({
        "name": "token",
        "value": token,
        "path": "/",
        "secure": False,
        "domain": PAGALBUKAS_BASE_URL
    })

# Get the actual data page and wait 10 secs at max for it to load
driver.get(f'https://{PAGALBUKAS_BASE_URL}/?date=' + schedule_date)
WebDriverWait(driver, 10).until(
    EC.presence_of_element_located((By.CLASS_NAME, 'view-lesson'))
)
print("Page loaded")

# I wont write another version of HTML to just display the schedule table alone so we just kill some components with JS
driver.execute_script("document.getElementsByClassName('navbar sticky-top navbar-expand-lg navbar-light bg-light')[0].remove();") # noqa
driver.execute_script("document.getElementsByClassName('col-md-12')[0].remove();")
driver.execute_script("document.getElementsByClassName('btn-group')[0].remove();")
driver.execute_script("document.getElementsByClassName('col-md-4')[0].remove();")

# Determine the size of table dynamically
res_data = driver.execute_script("""
    var elab_w = 0;
    var elab_h = 0;
    var table = document.getElementsByTagName("table")[0];
    for (var i = 0; i < table.rows.length; i++) {
        elab_w = table.rows[i].clientWidth;
        elab_h += table.rows[i].clientHeight;
    }
    return [elab_w, elab_h];
""")

w_off, h_off = res_data
w, h = w_off + 20, h_off + 50

# Take a screnshot and load it directly into pillow
img = Image.open(BytesIO(driver.get_screenshot_as_png()))

# Actual image manipulation of cropping it
cropped = img.crop((0, 0, w, h)) # Crop from 0x0 to dynamic resolution
print(f"Screenshot taken and cropped to the following resolution: {w}x{h}")

# Save image in memory
output = BytesIO()
cropped.save(output, "png")

# Close original bytes IO
img.close()

# Upload and close the output bytes IO
files = client.upload(("image.png", output.getvalue(), "image/png"))
output.close()
print("Image uploaded")

thread.send_text(f"Automatinė suvestinė {schedule_date}", files=files)
print("Message sent")
