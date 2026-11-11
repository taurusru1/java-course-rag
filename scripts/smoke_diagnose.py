import json, urllib.request
base = "http://127.0.0.1:18082"
def post(path, payload, token=None):
    req = urllib.request.Request(base + path, data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
                                 headers={"Content-Type": "application/json; charset=utf-8"})
    if token: req.add_header("Authorization", "Bearer " + token)
    return json.loads(urllib.request.urlopen(req).read().decode("utf-8"))
login = post("/api/auth/login", {"account": "student", "password": "123456", "role": "STUDENT"})
token = login["data"]["token"]
samples = json.load(open("data/errors/javac_errors.json", encoding="utf-8"))["items"]
for item in samples:
    r = post("/api/diagnose", {"error": item["message"]}, token)
    d = r["data"]
    got = d.get("case", {}).get("errorCode") if d.get("case") else None
    print(f"{item['sample']:<22} expect={item['error_code']:<26} got={got!s:<26} conf={d['confidence']}")
