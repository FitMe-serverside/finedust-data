"""에어코리아(한국환경공단) 대기질 값을 받아 data/now.json, data/stations.json 으로 저장한다.

- now.json: 10분마다 확인. 전국 실시간 측정값을 sidoName=전국 한 번에 받는다(1번 호출).
  값이 바뀌었을 때만 파일을 고친다(커밋도 그때만).
  전국 호출이 실패하면 17개 시도를 하나씩 받는다(17번 호출).
- stations.json: 하루 한 번(또는 없을 때). 전국 측정소 위치(1번 호출).
호출 수: 보통 하루 144 + 1 = 145번 (기능별 하루 500번 한도 안).
값은 바꾸지 않고 그대로 옮긴다(라이선스: 저작자표시-변경금지). 출처: 에어코리아(환경부·한국환경공단).
"""
import json
import os
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone, timedelta

KEY = os.environ.get("AIRKOREA_KEY", "").strip()
BASE = "https://apis.data.go.kr/B552584"
SIDO = ["서울", "부산", "대구", "인천", "광주", "대전", "울산", "경기", "강원",
        "충북", "충남", "전북", "전남", "경북", "경남", "제주", "세종"]
KST = timezone(timedelta(hours=9))
HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "data")


def call(path, **params):
    params.update(serviceKey=KEY, returnType="json")
    url = f"{BASE}/{path}?" + urllib.parse.urlencode(params)
    last = None
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "finedust-data/1.0"})
            with urllib.request.urlopen(req, timeout=30) as r:
                body = r.read().decode("utf-8")
            j = json.loads(body)
            head = j["response"]["header"]
            if head.get("resultCode") != "00":
                raise RuntimeError(f"{head.get('resultCode')} {head.get('resultMsg')}")
            return j["response"]["body"]["items"]
        except Exception as e:  # 잠깐 실패는 재시도
            last = e
            time.sleep(3 * (attempt + 1))
    raise RuntimeError(f"{path} failed: {last}")


def num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None  # "-" 등 측정 없음


def write(name, obj):
    os.makedirs(DATA, exist_ok=True)
    tmp = os.path.join(DATA, name + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, separators=(",", ":"))
    os.replace(tmp, os.path.join(DATA, name))


def update_stations():
    path = os.path.join(DATA, "stations.json")
    if os.path.exists(path):
        try:
            old = json.load(open(path, encoding="utf-8"))
            if old.get("date") == datetime.now(KST).strftime("%Y-%m-%d"):
                return
        except Exception:
            pass
    items = call("MsrstnInfoInqireSvc/getMsrstnList", numOfRows=1000, pageNo=1)
    st = []
    for it in items:
        lat, lon = num(it.get("dmX")), num(it.get("dmY"))
        if lat is None or lon is None:
            continue
        st.append({"n": it.get("stationName"), "lat": lat, "lon": lon, "addr": it.get("addr")})
    if len(st) < 100:
        raise RuntimeError(f"too few stations: {len(st)}")
    write("stations.json", {"date": datetime.now(KST).strftime("%Y-%m-%d"),
                             "source": "에어코리아(환경부·한국환경공단)", "stations": st})
    print("stations", len(st))


def row(it, sido):
    return {
        "t": it.get("dataTime"), "s": sido,
        "pm10": num(it.get("pm10Value")), "pm25": num(it.get("pm25Value")),
        "o3": num(it.get("o3Value")), "no2": num(it.get("no2Value")),
        "co": num(it.get("coValue")), "so2": num(it.get("so2Value")),
        "khai": num(it.get("khaiValue")),
    }


def fetch_all():
    """전국을 한 번에 받는다(실패하면 None)."""
    try:
        items = call("ArpltnInforInqireSvc/getCtprvnRltmMesureDnsty",
                     sidoName="전국", numOfRows=1000, pageNo=1, ver="1.0")
    except Exception as e:
        print("all failed", e, file=sys.stderr)
        return None
    out = {it["stationName"]: row(it, it.get("sidoName") or "") for it in items}
    return out if len(out) >= 300 else None


def fetch_by_sido(prev):
    out, failed = {}, []
    for sido in SIDO:
        try:
            items = call("ArpltnInforInqireSvc/getCtprvnRltmMesureDnsty",
                         sidoName=sido, numOfRows=1000, pageNo=1, ver="1.0")
        except Exception as e:
            print("fail", sido, e, file=sys.stderr)
            failed.append(sido)
            continue
        for it in items:
            out[it["stationName"]] = row(it, sido)
    # 일부 시도가 실패하면 지난 값을 남겨 둔다(앱은 t로 오래된 값을 알 수 있음).
    for k, v in prev.items():
        if v.get("s") in failed and k not in out:
            out[k] = v
    print("by sido, failed", failed)
    return out


def update_now():
    path = os.path.join(DATA, "now.json")
    prev = {}
    if os.path.exists(path):
        try:
            prev = json.load(open(path, encoding="utf-8")).get("stations", {})
        except Exception:
            pass
    out = fetch_all() or fetch_by_sido(prev)
    if not out:
        raise RuntimeError("no data at all")
    if out == prev:
        print("no new data")
        return
    write("now.json", {"updated": datetime.now(KST).strftime("%Y-%m-%d %H:%M"),
                        "source": "에어코리아(환경부·한국환경공단)", "stations": out})
    print("now", len(out))


if __name__ == "__main__":
    if not KEY:
        sys.exit("AIRKOREA_KEY secret is missing")
    try:
        update_stations()
    except Exception as e:  # 측정소 목록 실패는 지난 파일로 버틴다
        print("stations error", e, file=sys.stderr)
    update_now()
