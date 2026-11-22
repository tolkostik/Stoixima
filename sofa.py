"""
Κουπόνι όλων των αγώνων (ποδόσφαιρο, μπάσκετ, βόλεϊ) από το Sofascore, χωρίς λογαριασμό.

Δίνει: όλους τους αγώνες κάθε ημέρας με χώρα, κατηγορία και διοργάνωση, αποδόσεις 1Χ2 (με την αρχική
απόδοση, για να φαίνεται η κίνηση της γραμμής), ψήφους κοινού, φόρμα, αποτελέσματα μεταξύ τους,
ιστορικό ποσοστό επιτυχίας των φαβορί με την ίδια απόδοση και τα τελικά αποτελέσματα.

Ο ΟΠΑΠ και οι ελληνικές εταιρείες δεν έχουν δημόσιο API. Το Sofascore καλύπτει όλους τους αγώνες που
βρίσκονται στα κουπόνια τους (και πολλούς ακόμα). Αν το Sofascore δεν απαντήσει, χρησιμοποιείται το
TheSportsDB (χωρίς αποδόσεις) ώστε το κουπόνι να μη μένει άδειο.
"""
import datetime
import json
import ssl
import time
import urllib.parse
import urllib.request

HOSTS = ("https://api.sofascore.com/api/v1", "https://www.sofascore.com/api/v1")
SPORTS = {"football": "Ποδόσφαιρο", "basketball": "Μπάσκετ", "volleyball": "Βόλεϊ"}
TSDB = "https://www.thesportsdb.com/api/v1/json/3/eventsday.php"
TSDB_SPORT = {"football": "Soccer", "basketball": "Basketball", "volleyball": "Volleyball"}
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/130.0.0.0 Mobile Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "el-GR,el;q=0.9,en;q=0.8",
    "Referer": "https://www.sofascore.com/",
    "Origin": "https://www.sofascore.com",
    "Cache-Control": "no-cache",
}

# ------------------------------------------------------------------ χώρες στα ελληνικά
_CC = """GR:Ελλάδα CY:Κύπρος AL:Αλβανία AD:Ανδόρα AT:Αυστρία BE:Βέλγιο BA:Βοσνία-Ερζεγοβίνη BG:Βουλγαρία BY:Λευκορωσία CH:Ελβετία CZ:Τσεχία DE:Γερμανία DK:Δανία EE:Εσθονία ES:Ισπανία FI:Φινλανδία FR:Γαλλία GB:Ηνωμένο_Βασίλειο HR:Κροατία HU:Ουγγαρία IE:Ιρλανδία IS:Ισλανδία IT:Ιταλία XK:Κόσοβο LI:Λιχτενστάιν LT:Λιθουανία LU:Λουξεμβούργο LV:Λετονία MC:Μονακό MD:Μολδαβία ME:Μαυροβούνιο MK:Βόρεια_Μακεδονία MT:Μάλτα NL:Ολλανδία NO:Νορβηγία PL:Πολωνία PT:Πορτογαλία RO:Ρουμανία RS:Σερβία RU:Ρωσία SE:Σουηδία SI:Σλοβενία SK:Σλοβακία SM:Άγιος_Μαρίνος UA:Ουκρανία VA:Βατικανό TR:Τουρκία GE:Γεωργία AM:Αρμενία AZ:Αζερμπαϊτζάν AE:Ηνωμένα_Αραβικά_Εμιράτα AF:Αφγανιστάν BD:Μπανγκλαντές BH:Μπαχρέιν BN:Μπρουνέι BT:Μπουτάν CN:Κίνα ID:Ινδονησία IL:Ισραήλ IN:Ινδία IQ:Ιράκ IR:Ιράν JO:Ιορδανία JP:Ιαπωνία KG:Κιργιστάν KH:Καμπότζη KP:Βόρεια_Κορέα KR:Νότια_Κορέα KW:Κουβέιτ KZ:Καζακστάν LA:Λάος LB:Λίβανος LK:Σρι_Λάνκα MM:Μιανμάρ MN:Μογγολία MV:Μαλδίβες MY:Μαλαισία NP:Νεπάλ OM:Ομάν PH:Φιλιππίνες PK:Πακιστάν PS:Παλαιστίνη QA:Κατάρ SA:Σαουδική_Αραβία SG:Σιγκαπούρη SY:Συρία TH:Ταϊλάνδη TJ:Τατζικιστάν TL:Ανατολικό_Τιμόρ TM:Τουρκμενιστάν TW:Ταϊβάν UZ:Ουζμπεκιστάν VN:Βιετνάμ YE:Υεμένη EG:Αίγυπτος DZ:Αλγερία AO:Αγκόλα BJ:Μπενίν BW:Μποτσουάνα BF:Μπουρκίνα_Φάσο BI:Μπουρούντι CM:Καμερούν CV:Πράσινο_Ακρωτήριο CF:Κεντροαφρικανική_Δημοκρατία TD:Τσαντ KM:Κομόρες CG:Κονγκό CD:ΛΔ_Κονγκό CI:Ακτή_Ελεφαντοστού DJ:Τζιμπουτί GQ:Ισημερινή_Γουινέα ER:Ερυθραία SZ:Εσουατίνι ET:Αιθιοπία GA:Γκαμπόν GM:Γκάμπια GH:Γκάνα GN:Γουινέα GW:Γουινέα-Μπισάου KE:Κένυα LS:Λεσότο LR:Λιβερία LY:Λιβύη MG:Μαδαγασκάρη MW:Μαλάουι ML:Μάλι MR:Μαυριτανία MU:Μαυρίκιος MA:Μαρόκο MZ:Μοζαμβίκη NA:Ναμίμπια NE:Νίγηρας NG:Νιγηρία RW:Ρουάντα ST:Σάο_Τομέ_και_Πρίνσιπε SN:Σενεγάλη SC:Σεϋχέλλες SL:Σιέρα_Λεόνε SO:Σομαλία ZA:Νότια_Αφρική SS:Νότιο_Σουδάν SD:Σουδάν TZ:Τανζανία TG:Τόγκο TN:Τυνησία UG:Ουγκάντα ZM:Ζάμπια ZW:Ζιμπάμπουε US:Ηνωμένες_Πολιτείες CA:Καναδάς MX:Μεξικό GT:Γουατεμάλα BZ:Μπελίζ SV:Ελ_Σαλβαδόρ HN:Ονδούρα NI:Νικαράγουα CR:Κόστα_Ρίκα PA:Παναμάς CU:Κούβα JM:Τζαμάικα HT:Αϊτή DO:Δομινικανή_Δημοκρατία BS:Μπαχάμες BB:Μπαρμπάντος TT:Τρινιντάντ_και_Τομπάγκο AG:Αντίγκουα_και_Μπαρμπούντα DM:Ντομίνικα GD:Γρενάδα KN:Άγιος_Χριστόφορος_και_Νέβις LC:Αγία_Λουκία VC:Άγιος_Βικέντιος_και_Γρεναδίνες BR:Βραζιλία AR:Αργεντινή BO:Βολιβία CL:Χιλή CO:Κολομβία EC:Ισημερινός GY:Γουιάνα PY:Παραγουάη PE:Περού SR:Σουρινάμ UY:Ουρουγουάη VE:Βενεζουέλα AU:Αυστραλία NZ:Νέα_Ζηλανδία FJ:Φίτζι PG:Παπούα_Νέα_Γουινέα SB:Νήσοι_Σολομώντα VU:Βανουάτου WS:Σαμόα TO:Τόνγκα KI:Κιριμπάτι FM:Μικρονησία MH:Νήσοι_Μάρσαλ PW:Παλάου NR:Ναουρού TV:Τουβαλού"""
CC = {k: v.replace("_", " ") for k, v in (x.split(":", 1) for x in _CC.split())}
CC.update({"EN": "Αγγλία", "SX": "Σκωτία", "WA": "Ουαλία", "NI": "Βόρεια Ιρλανδία", "GB": "Αγγλία",
           "XK": "Κόσοβο", "US": "ΗΠΑ", "KR": "Νότια Κορέα"})
SPECIAL = {
    "international": "Διεθνή", "world": "Διεθνή", "europe": "Ευρώπη", "south america": "Νότια Αμερική",
    "north & central america": "Βόρεια & Κεντρική Αμερική", "north and central america": "Βόρεια & Κεντρική Αμερική",
    "asia": "Ασία", "africa": "Αφρική", "oceania": "Ωκεανία", "england": "Αγγλία", "scotland": "Σκωτία",
    "wales": "Ουαλία", "northern ireland": "Βόρεια Ιρλανδία", "usa": "ΗΠΑ", "united states": "ΗΠΑ",
    "greece": "Ελλάδα", "cyprus": "Κύπρος", "spain": "Ισπανία", "italy": "Ιταλία", "germany": "Γερμανία",
    "france": "Γαλλία", "netherlands": "Ολλανδία", "portugal": "Πορτογαλία", "belgium": "Βέλγιο",
    "turkey": "Τουρκία", "türkiye": "Τουρκία", "russia": "Ρωσία", "brazil": "Βραζιλία", "argentina": "Αργεντινή",
    "nba": "ΗΠΑ", "euroleague": "Ευρώπη", "south korea": "Νότια Κορέα", "republic of korea": "Νότια Κορέα",
    "czech republic": "Τσεχία", "czechia": "Τσεχία", "bosnia & herzegovina": "Βοσνία-Ερζεγοβίνη",
    "ncaa": "ΗΠΑ", "amateur": "Ερασιτεχνικά", "esports": "Ηλεκτρονικά",
}
# σειρά εμφάνισης: πρώτα Ελλάδα, μετά διεθνείς διοργανώσεις, μεγάλα πρωταθλήματα, οι υπόλοιπες αλφαβητικά
COUNTRY_ORDER = ["Ελλάδα", "Ευρώπη", "Διεθνή", "Αγγλία", "Ισπανία", "Ιταλία", "Γερμανία", "Γαλλία", "Κύπρος",
                 "Ολλανδία", "Πορτογαλία", "Τουρκία", "Βέλγιο", "Σκωτία", "ΗΠΑ"]
CONTINENT = {"Ευρώπη", "Διεθνή", "Νότια Αμερική", "Βόρεια & Κεντρική Αμερική", "Ασία", "Αφρική", "Ωκεανία"}
SKIP_CATS = {"esports", "simulated reality league", "srl", "amateur"}


def country_gr(cat):
    """Ελληνικό όνομα της κατηγορίας του Sofascore (χώρα ή ήπειρος)."""
    cat = cat or {}
    name = (cat.get("name") or "").strip()
    a2 = (cat.get("alpha2") or "").upper()
    low = name.lower()
    if low in SPECIAL:
        return SPECIAL[low]
    if a2 in CC:
        return CC[a2]
    return name or "Άλλες"


def country_rank(c):
    return (COUNTRY_ORDER.index(c) if c in COUNTRY_ORDER else len(COUNTRY_ORDER), c)


# ------------------------------------------------------------------ δίκτυο
_last_ok = {"host": HOSTS[0]}
BLOCKED = {"until": 0}


def _ctx():
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except Exception:  # noqa: BLE001
        return ssl.create_default_context()


def _raw(url, timeout=15, headers=None):
    req = urllib.request.Request(url, headers=headers or HEADERS)
    with urllib.request.urlopen(req, timeout=timeout, context=_ctx()) as r:
        data = r.read()
        if r.headers.get("Content-Encoding") == "gzip":
            import gzip
            data = gzip.decompress(data)
        return data


def get(path, timeout=15):
    """GET στο Sofascore με εναλλαγή host. 404 → None (δεν υπάρχει το στοιχείο)."""
    import urllib.error
    if time.time() < BLOCKED["until"]:
        raise RuntimeError("Το Sofascore δεν απαντά προσωρινά")
    hosts = [_last_ok["host"]] + [h for h in HOSTS if h != _last_ok["host"]]
    err = None
    for h in hosts:
        try:
            js = json.loads(_raw(h + path, timeout))
            _last_ok["host"] = h
            return js
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            err = e
        except Exception as e:  # noqa: BLE001
            err = e
    if isinstance(err, urllib.error.HTTPError) and err.code in (403, 429):
        BLOCKED["until"] = time.time() + 600        # μην επιμένεις για 10 λεπτά
    raise RuntimeError(f"Sofascore: {err}")


# ------------------------------------------------------------------ αποδόσεις
def frac(x):
    """«13/10» → 2.30 (δεκαδική απόδοση)."""
    try:
        a, b = str(x).split("/")
        v = float(a) / float(b) + 1
        return round(v, 3) if v > 1.0 else None
    except (ValueError, ZeroDivisionError):
        try:
            v = float(x)
            return v if v > 1 else None
        except (TypeError, ValueError):
            return None


def _choice_map(market):
    out = {}
    for ch in market.get("choices") or []:
        nm = str(ch.get("name", "")).strip().upper()
        key = {"1": "1", "X": "X", "2": "2", "HOME": "1", "AWAY": "2", "DRAW": "X", "OVER": "O", "UNDER": "U",
               "YES": "Y", "NO": "N", "1X": "1X", "X2": "X2", "12": "12"}.get(nm)
        if key:
            out[key] = (frac(ch.get("fractionalValue")), frac(ch.get("initialFractionalValue")))
    return out


def parse_markets(markets, sport):
    """Από τη λίστα αγορών του Sofascore: x12 [1, Χ, 2], open [αρχικές], ou (Over/Under 2,5), btts."""
    res = {}
    for mk in markets or []:
        name = (mk.get("marketName") or "").lower()
        group = str(mk.get("choiceGroup") or "")
        cm = _choice_map(mk)
        if name in ("full time", "1x2", "home/away", "winner", "match winner") and "x12" not in res:
            if sport == "football":
                if all(cm.get(k, (None,))[0] for k in ("1", "X", "2")):
                    res["x12"] = [cm["1"][0], cm["X"][0], cm["2"][0]]
                    res["open"] = [cm["1"][1], cm["X"][1], cm["2"][1]]
            elif cm.get("1", (None,))[0] and cm.get("2", (None,))[0]:
                res["x12"] = [cm["1"][0], None, cm["2"][0]]
                res["open"] = [cm["1"][1], None, cm["2"][1]]
        elif sport == "football" and name == "match goals" and group in ("2.5", "2,5"):
            if cm.get("O", (None,))[0] and cm.get("U", (None,))[0]:
                res["ou"] = [cm["O"][0], cm["U"][0]]
        elif sport == "football" and name == "both teams to score":
            if cm.get("Y", (None,))[0] and cm.get("N", (None,))[0]:
                res["btts"] = [cm["Y"][0], cm["N"][0]]
    return res


# ------------------------------------------------------------------ αγώνες ημέρας
def _ev_basic(ev, sport):
    t = ev.get("tournament") or {}
    ut = t.get("uniqueTournament") or {}
    cat = t.get("category") or ut.get("category") or {}
    if (cat.get("name") or "").lower() in SKIP_CATS or (cat.get("slug") or "") in SKIP_CATS:
        return None
    home = (ev.get("homeTeam") or {}).get("name")
    away = (ev.get("awayTeam") or {}).get("name")
    ts = ev.get("startTimestamp")
    if not (home and away and ts):
        return None
    country = country_gr(cat)
    lg = ut.get("name") or t.get("name") or ""
    users = int(ut.get("userCount") or 0)
    prio = int(t.get("priority") or 0)
    start = datetime.datetime.fromtimestamp(int(ts), datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    st = (ev.get("status") or {}).get("type") or ""
    return {"sport": sport, "sid": ev.get("id"), "home": home, "away": away, "start": start,
            "country": country, "league": f"{country} – {lg}" if country not in ("Ευρώπη", "Διεθνή") else lg,
            "tournament": lg, "ut": ut.get("id"), "users": users, "prio": prio, "state": st,
            "women": "women" in (lg + " " + str(ev.get("homeTeam", {}).get("gender", ""))).lower()
                     or (ev.get("homeTeam") or {}).get("gender") == "F",
            "tier": tier_of(country, lg, users, prio, sport), "src": "Sofascore"}


BIG = {"football": ("Champions League", "Europa League", "Conference League", "Premier League", "LaLiga",
                    "Serie A", "Bundesliga", "Ligue 1", "World Cup", "EURO", "Nations League", "Copa Libertadores"),
       "basketball": ("NBA", "EuroLeague", "Euroleague", "EuroCup"),
       "volleyball": ("CEV Champions League", "SuperLega", "PlusLiga", "Nations League", "World Championship")}
TOP_COUNTRIES = {"Αγγλία", "Ισπανία", "Ιταλία", "Γερμανία", "Γαλλία"}


def tier_of(country, lg, users, prio, sport):
    """1 = μεγάλη διοργάνωση (πολλή πληροφόρηση), 2 = μεσαία, 3 = μικρή."""
    low = lg.lower()
    if any(b.lower() == low or (len(b) > 6 and b.lower() in low) for b in BIG.get(sport, ())) and \
            "women" not in low and "u19" not in low and "u21" not in low:
        return 1
    if users >= 300000:
        return 1
    if users >= 40000 or country == "Ελλάδα" or (country in TOP_COUNTRIES and prio >= 300):
        return 2
    return 3


def day_events(sport, date):
    """Όλοι οι αγώνες της ημέρας (date: datetime.date) που δεν έχουν ξεκινήσει ακόμα."""
    js = get(f"/sport/{sport}/scheduled-events/{date.isoformat()}", timeout=25) or {}
    out = []
    for ev in js.get("events", []):
        st = ((ev.get("status") or {}).get("type") or "")
        if st not in ("notstarted", ""):
            continue
        b = _ev_basic(ev, sport)
        if b:
            out.append(b)
    return out


def day_odds(sport, date):
    """Αποδόσεις όλων των αγώνων της ημέρας με μία κλήση: {event_id: {x12, open, …}}."""
    js = get(f"/sport/{sport}/odds/1/{date.isoformat()}", timeout=25)
    if js is None:
        raise RuntimeError("χωρίς αποδόσεις ημέρας")
    out = {}
    for eid, mk in (js.get("odds") or {}).items():
        mks = mk if isinstance(mk, list) else [mk]
        r = parse_markets(mks, sport)
        if r.get("x12"):
            try:
                out[int(eid)] = r
            except ValueError:
                pass
    return out


def event_odds(eid, sport):
    js = get(f"/event/{eid}/odds/1/all") or {}
    return parse_markets(js.get("markets") or [], sport)


# ------------------------------------------------------------------ λεπτομέρειες αγώνα
def votes(eid):
    v = (get(f"/event/{eid}/votes") or {}).get("vote") or {}
    n1, nx, n2 = int(v.get("vote1") or 0), int(v.get("voteX") or 0), int(v.get("vote2") or 0)
    tot = n1 + nx + n2
    if tot < 20:
        return None
    return {"n": tot, "p": [n1 / tot, nx / tot, n2 / tot]}


def pregame_form(eid):
    js = get(f"/event/{eid}/pregame-form") or {}
    tr = {"W": "Ν", "D": "Ι", "L": "Η"}
    out = {}
    for side in ("homeTeam", "awayTeam"):
        t = js.get(side) or {}
        if t:
            out[side[:4]] = {"form": "".join(tr.get(x, "") for x in (t.get("form") or [])[::-1])[:5],
                             "pos": t.get("position"), "rating": t.get("avgRating"), "pts": t.get("value")}
    return out or None


def h2h(eid):
    d = (get(f"/event/{eid}/h2h") or {}).get("teamDuel") or {}
    if not d:
        return None
    return {"home": int(d.get("homeWins") or 0), "draw": int(d.get("draws") or 0), "away": int(d.get("awayWins") or 0)}


def winning_odds(eid):
    """Ιστορικό: πόσο συχνά κέρδισε ομάδα με αυτή την απόδοση (actual) σε σχέση με το αναμενόμενο (expected)."""
    js = get(f"/event/{eid}/provider/1/winning-odds") or {}
    out = {}
    for side, k in (("home", "1"), ("away", "2")):
        d = js.get(side) or {}
        if d.get("expected") is not None and d.get("actual") is not None:
            out[k] = {"expected": float(d["expected"]) / 100, "actual": float(d["actual"]) / 100,
                      "odds": frac(d.get("fractionalValue"))}
    return out or None


def details(eid, sport):
    """Όλα τα επιπλέον στοιχεία ενός αγώνα (κάθε ένα προαιρετικό)."""
    out = {}
    for key, fn in (("votes", lambda: votes(eid)), ("form", lambda: pregame_form(eid)),
                    ("h2h", lambda: h2h(eid)), ("win", lambda: winning_odds(eid)),
                    ("odds", lambda: event_odds(eid, sport))):
        try:
            v = fn()
            if v:
                out[key] = v
        except Exception:  # noqa: BLE001
            pass
    return out


def result(eid):
    """(γκολ/πόντοι/σετ γηπεδούχου, φιλοξενούμενου) αν ο αγώνας τελείωσε, αλλιώς None."""
    ev = (get(f"/event/{eid}") or {}).get("event") or {}
    if ((ev.get("status") or {}).get("type")) != "finished":
        return None
    try:
        return int(ev["homeScore"]["current"]), int(ev["awayScore"]["current"])
    except (KeyError, TypeError, ValueError):
        return None


# ------------------------------------------------------------------ εφεδρική πηγή: TheSportsDB
def tsdb_day(sport, date):
    url = TSDB + "?" + urllib.parse.urlencode({"d": date.isoformat(), "s": TSDB_SPORT[sport]})
    js = json.loads(_raw(url, 20, {"User-Agent": "Stoixima/3.0"}))
    out = []
    now = datetime.datetime.now(datetime.timezone.utc)
    for ev in js.get("events") or []:
        ts = ev.get("strTimestamp") or ""
        try:
            t = datetime.datetime.fromisoformat(ts.replace("Z", "")).replace(tzinfo=datetime.timezone.utc)
        except ValueError:
            continue
        if t < now or not ev.get("strHomeTeam") or not ev.get("strAwayTeam"):
            continue
        country = SPECIAL.get((ev.get("strCountry") or "").lower()) or ev.get("strCountry") or "Άλλες"
        lg = ev.get("strLeague") or ""
        out.append({"sport": sport, "home": ev["strHomeTeam"], "away": ev["strAwayTeam"],
                    "start": t.strftime("%Y-%m-%dT%H:%M:%SZ"), "country": country,
                    "league": f"{country} – {lg}" if country not in ("Ευρώπη", "Διεθνή") else lg,
                    "tournament": lg, "tier": tier_of(country, lg, 0, 0, sport), "src": "TheSportsDB"})
    return out
