import sys
import time
import tempfile
import webbrowser
from flask import Flask, request
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

CMD_FB_EMAIL = ""
CMD_FB_PASS = ""
CMD_BS_USER = ""
CMD_BS_PASS = ""

if len(sys.argv) > 1:
    CMD_FB_EMAIL = sys.argv[1] if len(sys.argv) > 1 else ""
    CMD_FB_PASS = sys.argv[2] if len(sys.argv) > 2 else ""
    CMD_BS_USER = sys.argv[3] if len(sys.argv) > 3 else ""
    CMD_BS_PASS = sys.argv[4] if len(sys.argv) > 4 else ""

app = Flask(__name__)

def log(msg):
    # with open("ftob_debug.log", "a", encoding="utf-8") as f:
    #     f.write(msg + "\n")
    print(msg)

@app.route("/")
def index():
    return f"""
<html>
<head>
<title>BuddyBridge</title>
<style>
    body {{
        font-family: Arial, sans-serif;
        background-color: #f5f5f5;
        margin: 0;
        padding: 0;
    }}
    .banner {{
        background-color: #4CAF50;
        color: white;
        padding: 20px;
        text-align: center;
        font-size: 24px;
        font-weight: bold;
    }}
    form {{
        background: #ffffff;
        padding: 20px;
        border-radius: 8px;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        width: 300px;
        margin: 40px auto;
    }}
    input[type="text"], input[type="password"] {{
        width: 100%;
        padding: 10px;
        margin: 10px 0;
        border: 1px solid #ccc;
        border-radius: 4px;
    }}
    input[type="submit"] {{
        background-color: #4CAF50;
        color: white;
        padding: 10px 15px;
        border: none;
        border-radius: 4px;
        cursor: pointer;
    }}
    input[type="submit"]:hover {{
        background-color: #45a049;
    }}
</style>
</head>
<body>
<div class="banner">Welcome to BuddyBridge</div>
<form action="/process" method="post">
    <label>Facebook Email:</label>
    <input type="text" name="fb_email" value="{CMD_FB_EMAIL}">
    <label>Facebook Password:</label>
    <input type="password" name="fb_password" value="{CMD_FB_PASS}">
    <label>Bluesky Username:</label>
    <input type="text" name="bs_username" value="{CMD_BS_USER}">
    <label>Bluesky Password:</label>
    <input type="password" name="bs_password" value="{CMD_BS_PASS}">
    <input type="submit" value="Submit">
</form>
</body>
</html>
"""

@app.route("/process", methods=["POST"])
def process():
    fb_email = request.form.get("fb_email")
    fb_password = request.form.get("fb_password")
    bs_username = request.form.get("bs_username")
    bs_password = request.form.get("bs_password")
    friends_data = get_facebook_friends(fb_email, fb_password)
    matches = find_bluesky_matches(bs_username, bs_password, friends_data)
    
    out = f"""
<html>
<head>
<title>BuddyBridge</title>
<style>
    body {{
        font-family: Arial, sans-serif;
        margin: 20px;
        background: linear-gradient(to right, #e3f2fd, #ffffff);
    }}
    .banner {{
        background-color: #4CAF50;
        color: white;
        padding: 20px;
        text-align: center;
        font-size: 24px;
        font-weight: bold;
    }}
    table {{
        border-collapse: collapse;
        width: 100%;
        margin: 20px auto;
        background: #ffffff;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        border-radius: 8px;
        border: 1px solid #ddd;
    }}
    th, td {{
        padding: 12px;
        border: 1px solid #ddd;
        text-align: left;
        vertical-align: top;
    }}
    th {{
        background-color: #4CAF50;
        color: white;
        text-align: center;
    }}
    img {{
        border-radius: 50%;
        height: 50px;
        width: 50px;
    }}
    .profile-link {{
        color: #007BFF;
        text-decoration: none;
    }}
    .profile-link:hover {{
        text-decoration: underline;
    }}
    .section-header {{
        margin-top: 20px;
        font-size: 18px;
        color: #333;
        text-align: center;
        font-weight: bold;
    }}
    .instructions {{
        margin: 20px auto;
        width: 90%;
        text-align: center;
        font-size: 16px;
        color: #555;
    }}
</style>
</head>
<body>
    <div class="banner">Welcome to BuddyBridge</div>
    <div class="instructions">
        <p>Below, you will find a list of potential matches between your Facebook friends and BlueSky profiles. 
        Matches are categorized as already matched, photo matches, and non-photo matches. Click the links to view profiles and take action.</p>
    </div>
    <div class="section-header">Already Matched Profiles</div>
    <table>
        <thead>
            <tr>
                <th>Facebook</th>
                <th>BlueSky Matches</th>
            </tr>
        </thead>
        <tbody>
    """
    
    for fn, fp, bs_name, bs_photo, already_followed, profile_url in matches["photo_matches"]:
        if already_followed:
            out += f"""
            <tr>
                <td>
                    <img src="{fp}" alt="Facebook Photo"><br>{fn}
                </td>
                <td>
                    <div>
                        <img src="{bs_photo}" alt="BlueSky Photo"><br>{bs_name}<br>
                        <a href="{profile_url}" target="_blank" class="profile-link">Open Profile</a>
                    </div>
                </td>
            </tr>
            """
    
    out += """
        </tbody>
    </table>
    <div class="section-header">Photo Matches</div>
    <table>
        <thead>
            <tr>
                <th>Facebook</th>
                <th>BlueSky Matches</th>
            </tr>
        </thead>
        <tbody>
    """
    
    for fn, fp, bs_name, bs_photo, already_followed, profile_url in matches["photo_matches"]:
        if not already_followed:
            out += f"""
            <tr>
                <td>
                    <img src="{fp}" alt="Facebook Photo"><br>{fn}
                </td>
                <td>
                    <div>
                        <img src="{bs_photo}" alt="BlueSky Photo"><br>{bs_name}<br>
                        <a href="{profile_url}" target="_blank" class="profile-link">Open Profile</a>
                    </div>
                </td>
            </tr>
            """
    
    out += """
        </tbody>
    </table>
    <div class="section-header">Non-Photo Matches</div>
    <table>
        <thead>
            <tr>
                <th>Facebook</th>
                <th>BlueSky Matches</th>
            </tr>
        </thead>
        <tbody>
    """
    
    for fn, fp, alt_list in matches["name_only"]:
        alt_html = "".join([
            f"""
            <div>
                <img src="{pmp}" alt="Match Photo"><br>{pmn}<br>
                <a href="{profile_url}" target="_blank" class="profile-link">Open Profile</a>
            </div>
            """
            for pmn, pmp, already_followed, profile_url in alt_list
        ])
        out += f"""
        <tr>
            <td>
                <img src="{fp}" alt="Facebook Photo"><br>{fn}
            </td>
            <td>{alt_html}</td>
        </tr>
        """
    
    out += """
        </tbody>
    </table>
</body>
</html>
"""
    return out

def create_driver():
    o = Options()
    o.add_argument("--headless")
    o.add_argument("--incognito")
    tmp_dir = tempfile.mkdtemp()
    o.add_argument("--user-data-dir=" + tmp_dir)
    d = webdriver.Chrome(options=o)
    d.delete_all_cookies()
    return d

def get_facebook_friends(email, password):
    d = create_driver()
    d.get("https://www.facebook.com/")
    time.sleep(5)
    try:
        WebDriverWait(d, 10).until(EC.presence_of_element_located((By.ID, "email")))
        time.sleep(5)
        d.find_element(By.ID, "email").send_keys(email)
        d.find_element(By.ID, "pass").send_keys(password)
        d.find_element(By.NAME, "login").click()
    except Exception as e:
        log("FB login error: " + str(e))
    try:
        WebDriverWait(d, 10).until(EC.title_contains("Facebook"))
        time.sleep(5)
    except:
        pass
    d.get("https://www.facebook.com/friends/list")
    time.sleep(5)
    try:
        WebDriverWait(d, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        time.sleep(5)
    except:
        log("FB friends body not found.")
    try:
        t = d.find_element(By.TAG_NAME, "title").get_attribute("innerHTML")
        if "Page Not Found" in t:
            log("FB friends page not found.")
            d.quit()
            return []
    except:
        pass
    friends = []
    seen = set()
    scrolls = 0
    try:
        container = d.find_element(By.CSS_SELECTOR, "div.x135pmgq")
    except:
        log("Cannot find friends container")
        d.quit()
        return []
        # container = d.find_element(By.TAG_NAME, "body")
    while scrolls < 2:
        scrollable_container = d.find_element(By.CSS_SELECTOR, "div.xb57i2i.x1q594ok.x5lxg6s.x78zum5.xdt5ytf.x6ikm8r.x1ja2u2z.x1pq812k.x1rohswg.xfk6m8.x1yqm8si.xjx87ck.x1l7klhg.x1iyjqo2.xs83m0k.x2lwn1j.xx8ngbg.xwo3gff.x1oyok0e.x1odjw0f.x1e4zzel.x1n2onr6.xq1qtft")
        cards = container.find_elements(By.XPATH, ".//a[contains(@href,'facebook.com/') and (contains(@class,'x1i10hfl') or contains(@class,'x78zum5'))]")
        log("found cards: " + str(len(cards)))
        for c in cards:
            if c not in seen:
                seen.add(c)
                name = ""
                img_src = ""
                try:
                    svgs = c.find_elements(By.TAG_NAME, "svg")
                    if svgs:
                        try:
                            name = svgs[0].get_attribute("aria-label") or ""
                        except:
                            pass
                        try:
                            im_el = svgs[0].find_element(By.TAG_NAME, "image")
                            img_src = im_el.get_attribute("xlink:href") or ""
                        except:
                            pass
                    if not name:
                        txt = c.text.strip()
                        lines = txt.split("\n")
                        name = lines[0] if lines else ""
                except Exception as e:
                    log("Error reading friend card: " + str(e))
                friends.append((name, img_src))
        d.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight;", scrollable_container)
        time.sleep(5)
        scrolls += 1
    d.quit()
    return friends

def find_bluesky_matches(username, password, friends_data):
    d = create_driver()
    d.get("https://bsky.app")
    try:
        WebDriverWait(d, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    except:
        log("No bsky body loaded?")
    try:
        sign_in_btns = d.find_elements(By.XPATH, "//button//div[contains(text(),'Sign in')]")
        if sign_in_btns:
            sign_in_btns[0].click()
            WebDriverWait(d, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[data-testid='loginUsernameInput']")))
            u = d.find_element(By.CSS_SELECTOR, "input[data-testid='loginUsernameInput']")
            p = d.find_element(By.CSS_SELECTOR, "input[data-testid='loginPasswordInput']")
            u.send_keys(username)
            p.send_keys(password)
            nxt = d.find_element(By.CSS_SELECTOR, "button[data-testid='loginNextButton']")
            nxt.click()
            WebDriverWait(d, 15).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    except Exception as e:
        log("bsky login error: " + str(e))
    pm = []
    no = []
    for idx, (fname, fphoto) in enumerate(friends_data):
        if idx >= 10:
            break
        q = fname.strip().replace(" ", "%20")
        log( "looking for " + fname)
        d.get(f"https://bsky.app/search?q={q}")
        time.sleep(2)
        try:
            people_tab = WebDriverWait(d, 5).until(EC.element_to_be_clickable((By.XPATH, "//div[@role='tab' and contains(.,'People')]")))
            d.execute_script("arguments[0].click();", people_tab)
        except:
            log("Could not click People tab for " + fname)
            pass
        try:
            WebDriverWait(d, 5).until(EC.presence_of_all_elements_located((By.XPATH, "//div[@class='css-175oi2r r-sa2ff0']//a[contains(@href,'/profile/') and @role='link']")))
            time.sleep(2)
        except:
            pass
        cards = d.find_elements(By.XPATH, "//div[@id='root']//div[contains(@class, 'css-175oi2r') and contains(@class, 'r-13awgt0')]//div/div/div[2]/div/div[position() >= 2]/a[@role='link' and contains(@href, '/profile/')]")
        photo_found = False
        alt_list = []
        for c in cards:
            bs_name = ""
            bs_img = ""
            already_followed = False
            profile_url = c.get_attribute("href")
            try:
                n_div = c.find_element(By.XPATH, ".//div[@style and contains(@style,'font-weight: 600')]")
                bs_name = n_div.text.strip()
            except:
                pass
            try:
                i_div = c.find_element(By.XPATH, ".//*[@data-testid='userAvatarImage']")
                i_img = i_div.find_element(By.TAG_NAME, "img")
                bs_img = i_img.get_attribute("src")
            except:
                pass
            try:
                f_btn = c.find_element(By.XPATH, ".//button")
                fb_txt = f_btn.text.strip().lower()
                if "unfollow" in fb_txt or "following" in fb_txt:
                    already_followed = True
            except:
                pass
            if fphoto and bs_img and fphoto == bs_img and not photo_found:
                pm.append((fname, fphoto, bs_name, bs_img, already_followed, profile_url))
                photo_found = True
            else:
                alt_list.append((bs_name, bs_img, already_followed, profile_url))
        if not photo_found:
            no.append((fname, fphoto, alt_list))
    d.quit()
    return {"photo_matches": pm, "name_only": no}

def add_friend_to_bluesky(username, password, match_name):
    log(f"Skipping auto-follow: {match_name}. User can open link themselves.")

if __name__ == "__main__":
    log("Starting BuddyBridge")
    port = 5000  # Port number the Flask app is running on
    url = f"http://127.0.0.1:{port}/"
    webbrowser.open(url)  # Open the URL in the default browser
    app.run("0.0.0.0", port)
