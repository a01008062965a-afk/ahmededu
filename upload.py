import requests, base64, os, time
TOKEN = input("Token: ").strip()
h = {"Authorization": "token " + TOKEN}
files = [
    "app.py",
    "templates/index.html",
    "templates/register.html",
    "templates/success.html",
    "templates/login.html",
    "templates/student.html",
    "templates/admin_login.html",
    "templates/admin_home.html",
    "templates/admin_pending.html",
    "templates/admin_approved.html",
    "templates/admin_students.html",
    "templates/admin_videos.html",
    "templates/admin_homework.html"
]
ok = 0; err = 0
for p in files:
    if not os.path.exists(p): print("SKIP", p); continue
    with open(p, "rb") as f:
        c = base64.b64encode(f.read()).decode()
    url = "https://api.github.com/repos/a01008062965a-afk/ahmededu/contents/" + p
    r = requests.get(url, headers=h)
    data = {"message": "u " + p, "content": c, "branch": "main"}
    if r.status_code == 200: data["sha"] = r.json().get("sha")
    res = requests.put(url, headers=h, json=data)
    if res.status_code in (200, 201):
        print("OK  " + p); ok += 1
    else:
        print("ERR " + str(res.status_code) + " " + p); err += 1
    time.sleep(0.3)
print("")
print("OK:", ok, "ERR:", err)
