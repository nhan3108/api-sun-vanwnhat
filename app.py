from flask import Flask, request, jsonify
from collections import Counter
import requests
import os

app = Flask(__name__)

API_GOC = "https://wanglinapiws.up.railway.app/api/taixiu"

def get_tai_xiu(total):
    return "Tài" if 11 <= total <= 18 else "Xỉu"

def tai_xiu_stats(totals_list):
    types = [get_tai_xiu(t) for t in totals_list]
    cnt = Counter(types)
    return {
        "tai_count": cnt["Tài"],
        "xiu_count": cnt["Xỉu"],
        "average_total": round(sum(totals_list) / len(totals_list), 2),
    }

def call_api_goc(totals):
    try:
        r = requests.post(API_GOC, json={"totals_list": totals})
        if r.status_code == 200:
            return r.json()
    except:
        pass
    return {}

def rule1(totals):
    if len(totals) < 4: return None
    last = totals[-4:]
    if last[0] == last[2] == last[3] and last[1] != last[0]:
        return "Tài", 90, f"Cầu đặc biệt {last}."

def rule2(totals):
    if len(totals) < 3: return None
    l = totals[-3:]
    if l[0] == l[2] and l[0] != l[1]:
        res = get_tai_xiu(l[2])
        return "Xỉu" if res == "Tài" else "Tài", 88, f"Cầu sandwich {l}."

def rule3(totals):
    if len(totals) < 3: return None
    c = sum(1 for x in totals[-3:] if x in [7,9,10])
    if c >= 2:
        res = get_tai_xiu(totals[-1])
        return "Xỉu" if res == "Tài" else "Tài", 85, "≥2 số đặc biệt 7/9/10."

def rule4(totals):
    last = totals[-1]
    if totals[-6:].count(last) >= 3:
        return get_tai_xiu(last), 82, f"Số {last} lặp lại ≥3 lần."

def rule5(totals):
    if len(totals) < 3: return None
    l = totals[-3:]
    if l[0] == l[2] or l[1] == l[2]:
        res = get_tai_xiu(l[-1])
        return "Xỉu" if res == "Tài" else "Tài", 80, "Pattern A-B-A hoặc A-B-B"

def rule6(totals):
    types = [get_tai_xiu(x) for x in totals]
    chain = 1
    for i in range(len(types)-1, 0, -1):
        if types[i] == types[i-1]: chain += 1
        else: break
    if chain >= 4:
        return "Xỉu" if types[-1]=="Tài" else "Tài", 78, f"{chain} lần {types[-1]} liên tiếp"

def rule7(totals):
    if len(totals) < 3: return None
    a,b,c = totals[-3:]
    if a<b<c or a>b>c:
        res = get_tai_xiu(c)
        return "Xỉu" if res == "Tài" else "Tài", 77, "3 phiên tăng/giảm liên tiếp"

def rule8(totals):
    if totals[-1] <= 5 or totals[-1] >= 16:
        res = get_tai_xiu(totals[-1])
        return "Xỉu" if res == "Tài" else "Tài", 76, "Tổng cực trị"

def rule9(totals):
    if len(totals) < 6: return None
    avg = sum(totals[-6:]) / 6
    return ("Tài", 74, "Trung bình cao → Tài") if avg >= 11.5 else ("Xỉu", 74, "Trung bình thấp → Xỉu")

def rule10(totals):
    t = totals[-1]
    return ("Tài", 70, "Mặc định bẻ cầu") if get_tai_xiu(t) == "Xỉu" else ("Xỉu", 70, "Mặc định bẻ cầu")

def run_all_rules(totals):
    for rule in [rule1, rule2, rule3, rule4, rule5, rule6, rule7, rule8, rule9]:
        res = rule(totals)
        if res: return res
    return rule10(totals)

@app.route('/api/taixiu', methods=['POST'])
def api_taixiu():
    data = request.get_json()
    totals = data.get("totals_list", [])
    if not isinstance(totals, list) or not all(isinstance(x, int) for x in totals):
        return jsonify({"error": "totals_list phải là list số nguyên"}), 400

    pred, conf, reason = run_all_rules(totals)
    thongke = tai_xiu_stats(totals)
    tong = totals[-1]
    phien = len(totals)
    api_truoc = call_api_goc(totals)

    return jsonify({
        "Phien": phien,
        "Phien_sau": phien + 1,
        "Phien_truoc": api_truoc.get("Phien"),
        "Ket_qua_truoc": api_truoc.get("Ket_qua"),
        "Xuc_xac_truoc": [api_truoc.get("Xuc_xac1"), api_truoc.get("Xuc_xac2"), api_truoc.get("Xuc_xac3")],
        "Tong_truoc": api_truoc.get("Tong"),
        "Tong": tong,
        "Du_doan": pred,
        "Tin_cay": f"{conf}%",
        "Mau_cau": reason,
        "So_lan_tai": thongke["tai_count"],
        "So_lan_xiu": thongke["xiu_count"]
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host="0.0.0.0", port=port)
