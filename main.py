"""
Στοίχημα PRO 3 – κουπόνι όλων των αγώνων (ποδόσφαιρο, μπάσκετ, βόλεϊ) ανά χώρα και διοργάνωση,
πιθανότητες, έλεγχος φερεγγυότητας από πολλές πηγές, δελτία και ιστορικό επιτυχίας.
Καρτέλες: Αρχική · Κουπόνι · Δελτίο · Ιστορικό · Ρυθμίσεις.
"""
import datetime
import threading
import time
import webbrowser

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, Ellipse, Line, RoundedRectangle
from kivy.lang import Builder
from kivy.metrics import dp, sp
from kivy.properties import BooleanProperty, ListProperty, ObjectProperty, StringProperty
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.checkbox import CheckBox
from kivy.uix.label import Label
from kivy.uix.screenmanager import NoTransition, Screen
from kivy.uix.scrollview import ScrollView
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget

import betting as B
import model as M
import ui_widgets as UW
import updater as UP

TABS = ("home", "coupon", "slip", "history", "settings")
TITLES = {"home": "Στοίχημα PRO", "coupon": "Κουπόνι", "slip": "Δελτίο", "history": "Ιστορικό & επιτυχία",
          "settings": "Ρυθμίσεις", "match": "Αγώνας", "league": "Διοργάνωση"}
GREEN, RED, AMBER, BLUE = (0.13, 0.8, 0.45, 1), (0.95, 0.27, 0.32, 1), UW.WARN, (0.25, 0.55, 1.0, 1)
VIOLET, PINK, ORANGE, TEAL = (0.48, 0.36, 1.0, 1), (0.98, 0.25, 0.55, 1), (1.0, 0.55, 0.12, 1), (0.0, 0.78, 0.85, 1)
LIME, GOLD, INDIGO = (0.66, 0.93, 0.2, 1), (1.0, 0.78, 0.15, 1), (0.30, 0.30, 0.95, 1)
TAB_COL = {  # κάθε καρτέλα με το δικό της ντεγκραντέ
    "home": (INDIGO, TEAL), "coupon": ((0.0, 0.72, 0.5, 1), (0.05, 0.35, 0.75, 1)),
    "slip": (VIOLET, PINK), "history": (BLUE, (0.45, 0.25, 0.9, 1)), "settings": ((0.25, 0.32, 0.5, 1), TEAL),
}
SPORTS = ("football", "basketball", "volleyball")
SPORT_GR = {"football": "Ποδόσφαιρο", "basketball": "Μπάσκετ", "volleyball": "Βόλεϊ", "all": "Όλα"}
SPORT_ICON = {"football": "ball", "basketball": "bball", "volleyball": "vball", "all": "list"}
SPORT_COL = {"football": (0.0, 0.75, 0.45, 1), "basketball": ORANGE, "volleyball": GOLD, "all": INDIGO}
TRUST_COL = {"Φερέγγυος": GREEN, "Με προσοχή": ORANGE, "Αμφίβολος": RED}
SIGN_COL = {"1": GREEN, "Χ": ORANGE, "2": BLUE}
BOOKS = (("Πάμε Στοίχημα", "https://www.pamestoixima.gr/"), ("Stoiximan", "https://www.stoiximan.gr/"),
         ("Novibet", "https://www.novibet.gr/"), ("bet365", "https://www.bet365.gr/"))


def league_color(name):
    pal = [ORANGE, BLUE, VIOLET, PINK, TEAL, GREEN, GOLD, (0.85, 0.3, 0.3, 1)]
    if name.startswith("UEFA") or "Champions" in name:
        return (0.25, 0.35, 0.95, 1)
    if name.startswith("Ελλάδα"):
        return (0.1, 0.5, 0.95, 1)
    return pal[sum(ord(c) for c in name) % len(pal)]


def trust_col(score):
    return GREEN if score >= 70 else (ORANGE if score >= 45 else RED)


REL_RGBA = {"Υψηλή": GREEN, "Μέτρια": BLUE, "Χαμηλή": RED}
FOOT = ("Δεν υπάρχει σίγουρο αποτέλεσμα: ένα σημείο 80% χάνει 1 στις 5. Μακροπρόθεσμα κερδίζει μόνο όποιος "
        "παίζει αποδόσεις μεγαλύτερες από τις δίκαιες. Παίζε μόνο σε εταιρείες με άδεια ΕΕΕΠ και μόνο ποσά που "
        "αντέχεις να χάσεις. Αν το παιχνίδι γίνει πρόβλημα, υπάρχει βοήθεια (π.χ. ΚΕΘΕΑ ΑΛΦΑ).")

KV = """
#:import dp kivy.metrics.dp

<NavItem>:
    orientation: 'vertical'
    padding: 0, dp(6)
    spacing: dp(2)

<Root>:
    orientation: 'vertical'
    canvas.before:
        Color:
            rgba: app.c_bg
        Rectangle:
            pos: self.pos
            size: self.size
    BoxLayout:
        size_hint_y: None
        height: dp(62)
        padding: dp(8), dp(6)
        spacing: dp(6)
        canvas.before:
            Color:
                rgba: 1, 1, 1, 1
            Rectangle:
                pos: self.pos
                size: self.size
                texture: app.grad
        Button:
            text: '<'
            bold: True
            font_size: '24sp'
            size_hint_x: None
            width: dp(46) if app.can_back else 0
            opacity: 1 if app.can_back else 0
            disabled: not app.can_back
            background_normal: ''
            background_color: 1, 1, 1, 0.15
            on_release: app.back()
        BoxLayout:
            orientation: 'vertical'
            Label:
                text: app.title_text
                bold: True
                font_size: '20sp'
                halign: 'left'
                valign: 'bottom'
                text_size: self.size
                shorten: True
            Label:
                text: app.sub_text
                font_size: '11sp'
                color: 1, 1, 1, 0.85
                halign: 'left'
                valign: 'top'
                text_size: self.size
                shorten: True
                size_hint_y: 0.7
        RefreshBtn:
            size_hint_x: None
            width: dp(48)
            on_release: app.update()
            canvas.before:
                Color:
                    rgba: 1, 1, 1, 0.18 if not app.busy_flag else 0.35
                RoundedRectangle:
                    pos: self.x + dp(4), self.y + dp(4)
                    size: self.width - dp(8), self.height - dp(8)
                    radius: [dp(14)]
    ScreenManager:
        id: sm
    BoxLayout:
        id: nav
        size_hint_y: None
        height: dp(64)
        canvas.before:
            Color:
                rgba: app.c_card
            Rectangle:
                pos: self.pos
                size: self.size
            Color:
                rgba: app.c_line
            Rectangle:
                pos: self.x, self.top - dp(1)
                size: self.width, dp(1)
"""


class NavItem(ButtonBehavior, BoxLayout):
    pass


class Root(BoxLayout):
    pass


class Tap(ButtonBehavior, BoxLayout):
    pass


class RefreshBtn(ButtonBehavior, AnchorLayout):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.icon = UW.Icon(kind="refresh", size_hint=(None, None), size=(dp(26), dp(26)))
        self.add_widget(self.icon)


# ------------------------------------------------------------------ προστασία από κλεισίματα
from kivy.base import ExceptionHandler, ExceptionManager  # noqa: E402


class _Guard(ExceptionHandler):
    def handle_exception(self, inst):
        try:
            import traceback
            B.DATA_DIR.mkdir(parents=True, exist_ok=True)
            with open(B.DATA_DIR / "errors.log", "a", encoding="utf-8") as fh:
                fh.write(time.strftime("%d/%m %H:%M ") + "".join(
                    traceback.format_exception(type(inst), inst, inst.__traceback__))[-1500:] + "\n")
        except Exception:  # noqa: BLE001
            pass
        return ExceptionManager.PASS


ExceptionManager.add_handler(_Guard())


def esc(t):
    return str(t).replace("&", "&amp;").replace("[", "&bl;").replace("]", "&br;")


def gr(x):
    t = f"{x:.1f}".replace(".", ",")
    return t[:-2] if t.endswith(",0") else t


def euro(x):
    return f"{x:.2f}".replace(".", ",") + " €"




def _fold(t):
    import unicodedata
    t = unicodedata.normalize("NFD", (t or "").lower())
    return "".join(c for c in t if unicodedata.category(c) != "Mn").replace("ς", "σ")


COUPON_NOTE = ("Ο ΟΠΑΠ και οι ελληνικές εταιρείες δεν δίνουν δημόσια τα κουπόνια τους. Εδώ βλέπεις όλους τους αγώνες "
               "που έχουν αποδόσεις στην αγορά (Sofascore, football-data, ESPN), δηλαδή όσους υπάρχουν και στα "
               "ελληνικά κουπόνια και πολλούς ακόμα. Τις ακριβείς αποδόσεις του ΟΠΑΠ μπορείς να τις γράψεις στη σελίδα "
               "κάθε αγώνα για έλεγχο αξίας.")


THEMES_GR = {"night": "Νύχτα", "dark": "Σκοτεινό", "light": "Φωτεινό"}


def pct(x):
    return f"{x * 100:.0f}%"


def num(x):
    return f"{x:.2f}".replace(".", ",")


class StoiximaApp(App):
    title = "Stoixima"
    c_bg = ListProperty([0.031, 0.043, 0.086, 1])
    c_card = ListProperty([0.071, 0.094, 0.165, 1])
    c_line = ListProperty([0.13, 0.17, 0.28, 1])
    grad = ObjectProperty(None, allownone=True)
    can_back = BooleanProperty(False)
    busy_flag = BooleanProperty(False)
    title_text = StringProperty("Στοίχημα PRO")
    sub_text = StringProperty("")

    # ================================================================== εκκίνηση
    def build(self):
        B.set_dir(self.user_data_dir)
        UP.set_dir(self.user_data_dir)
        self.s = {**B.DEFAULTS, "bankroll": 100.0, "risk": "Συντηρητικό", "week_limit": 10, "use_model": True,
                  "theme": "night", "auto_min": 30, **B.load_settings()}
        if not self.s.get("v3"):                       # πρώτη εκκίνηση της έκδοσης 3: νέα εμφάνιση
            self.s.update(v3=True, theme="night", volleyball=True, sofa=True)
            B.save_settings(self.s)
        UW.set_theme(self.s.get("theme", "night"))
        self.c_bg, self.c_card, self.c_line = list(UW.C["bg"]), list(UW.C["card"]), list(UW.C["line"])
        Window.clearcolor = UW.C["bg"]
        self._grads = {k: UW.gradient(a, b) for k, (a, b) in TAB_COL.items()}
        self._sgrads = {k: UW.gradient(SPORT_COL[k], (0.05, 0.08, 0.2, 1)) for k in SPORT_COL}
        self.grad = self._grads["home"]
        Builder.load_string(KV)
        self.root_w = Root()
        self.sm = self.root_w.ids.sm
        self.sm.transition = NoTransition()
        self.pages = {}
        for name in TITLES:
            scr = Screen(name=name)
            sv = ScrollView(do_scroll_x=False, bar_width=dp(4))
            box = BoxLayout(orientation="vertical", size_hint_y=None, padding=(dp(12), dp(12)), spacing=dp(12))
            box.bind(minimum_height=box.setter("height"))
            sv.add_widget(box)
            scr.add_widget(sv)
            self.sm.add_widget(scr)
            self.pages[name] = (sv, box)
        self.nav_items = {}
        for key, icon, label in (("home", "home", "Αρχική"), ("coupon", "list", "Κουπόνι"),
                                 ("slip", "ticket", "Δελτίο"), ("history", "chart", "Ιστορικό"),
                                 ("settings", "gear", "Ρυθμίσεις")):
            it = NavItem()
            ic = UW.Icon(kind=icon, size_hint_y=None, height=dp(26))
            lb = Label(text=label, font_size=sp(11), size_hint_y=None, height=dp(18))
            it.add_widget(ic)
            it.add_widget(lb)
            it.icon, it.lab = ic, lb
            it.bind(on_release=lambda w, k=key: self.tab(k))
            self.root_w.ids.nav.add_widget(it)
            self.nav_items[key] = it
        self.models = B._read("models.json", {})
        self.busy = False
        self.settle_busy = False
        self._token = 0
        self.stack = []
        self.slip_mode = "Αυτόματο"
        self.manual = B._read("manual_slip.json", [])
        self.sport = "all"
        self.csport = "football"
        self.filters = {"day": "Όλες", "kind": "Με αποδόσεις", "q": ""}
        self.open_c = {"football": {"Ελλάδα"}, "basketball": {"Ελλάδα"}, "volleyball": {"Ελλάδα"}}
        self.extra = {}
        self.status_msg = ""
        self.update_info = None
        self._cur_match = None
        Window.bind(on_keyboard=self._key)
        self._set_sub()
        self.tab("home")
        if self._stale(6 * 60):
            Clock.schedule_once(lambda dt: self.update(), 0.8)
        Clock.schedule_interval(self._auto, 60)
        if UP.due():
            Clock.schedule_once(lambda dt: self.check_update(silent=True), 4)
        return self.root_w

    def on_pause(self):
        return True

    def on_resume(self):
        self._auto(0)

    def _stale(self, minutes):
        cache = B.load_cache()
        if not cache.get("updated"):
            return True
        try:
            t = datetime.datetime.strptime(cache["updated"], "%d/%m/%Y %H:%M")
        except ValueError:
            return True
        return datetime.datetime.now() - t > datetime.timedelta(minutes=minutes)

    def _auto(self, dt):
        """Αυτόματη ανανέωση όσο η εφαρμογή είναι ανοιχτή (κάθε Χ λεπτά, από τις ρυθμίσεις)."""
        mins = int(self.s.get("auto_min", 30) or 0)
        if mins and not self.busy and self._stale(mins) and self.sm.current in ("home", "coupon"):
            self.update(silent=True)

    def _set_sub(self):
        cache = B.load_cache()
        if self.busy:
            self.sub_text = self.status_msg or "Ενημέρωση…"
        elif cache.get("updated"):
            self.sub_text = f"Ενημέρωση {cache['updated'][-5:]} · {len(cache.get('matches', []))} αγώνες"
        else:
            self.sub_text = "Πάτα την ανανέωση πάνω δεξιά"

    # ================================================================== πλοήγηση
    def page(self, name):
        sv, box = self.pages[name]
        box.clear_widgets()
        sv.scroll_y = 1
        return box

    def show(self, name, push=True):
        if push and self.sm.current != name:
            self.stack.append(self.sm.current)
        self.sm.current = name
        self.title_text = TITLES.get(name, "Στοίχημα")
        self.can_back = name not in TABS
        tab = name if name in TABS else (self.stack[0] if self.stack and self.stack[0] in TABS else "home")
        if getattr(self, "_grad_tab", None) != tab:
            self._grad_tab = tab
            self.grad = self._grads[tab]
        for k, it in self.nav_items.items():
            on = k == tab
            col = TAB_COL[k][1] if on else UW.C["muted"]
            it.icon.rgba = list(col)
            it.lab.color = col
            it.lab.bold = on

    def tab(self, name):
        self.stack = []
        getattr(self, "build_" + name)()
        self.show(name, push=False)

    def back(self):
        if not self.stack:
            return False
        prev = self.stack.pop()
        if prev in TABS:
            getattr(self, "build_" + prev)()
        self.show(prev, push=False)
        return True

    def _key(self, win, key, *a):
        if key == 27:
            return self.back()
        return False

    def refresh_current(self):
        cur = self.sm.current
        if cur in TABS:
            sv = self.pages[cur][0]
            y = sv.scroll_y
            getattr(self, "build_" + cur)()
            sv.scroll_y = y

    # ================================================================== στοιχεία
    def card(self, box, pad=14):
        c = UW.CardBox(pad=pad)
        box.add_widget(c)
        return c

    def grad_box(self, box, tex, pad=16, radius=22):
        g = BoxLayout(orientation="vertical", size_hint_y=None, padding=(dp(pad), dp(pad - 2)), spacing=dp(8))
        g.bind(minimum_height=g.setter("height"))

        def bg(*a):
            g.canvas.before.clear()
            with g.canvas.before:
                Color(1, 1, 1, 1)
                RoundedRectangle(pos=g.pos, size=g.size, radius=[dp(radius)], texture=tex)
        g.bind(pos=bg, size=bg)
        box.add_widget(g)
        return g

    def btn(self, parent, text, cb, color=None, fg=(1, 1, 1, 1), h=50):
        b = Button(text=text, bold=True, size_hint_y=None, height=dp(h), background_normal="",
                   background_color=color or UW.PRIMARY, color=fg, font_size=sp(15))
        b.bind(on_release=lambda *a: cb())
        parent.add_widget(b)
        return b

    def ghost(self, parent, text, cb, h=44):
        return self.btn(parent, text, cb, color=UW.C["line"], fg=UW.C["ink"], h=h)

    def chips(self, parent, items, h=30):
        row = BoxLayout(size_hint_y=None, height=dp(h), spacing=dp(6))
        for t, col in items:
            row.add_widget(UW.Chip(t, col))
        row.add_widget(Widget())
        parent.add_widget(row)
        return row

    def seg(self, parent, options, current, cb, h=38):
        row = BoxLayout(size_hint_y=None, height=dp(h), spacing=dp(6))
        for opt in options:
            on = opt == current
            b = Button(text=opt, bold=on, background_normal="", font_size=sp(12.5),
                       background_color=UW.PRIMARY if on else UW.C["line"], color=(1, 1, 1, 1) if on else UW.C["ink"])
            b.bind(on_release=lambda w, o=opt: cb(o))
            row.add_widget(b)
        parent.add_widget(row)

    def sport_pills(self, parent, current, cb, counts, with_all=False):
        """Επιλογή αθλήματος: χρωματιστές «κάψουλες» με εικονίδιο και πλήθος αγώνων."""
        row = BoxLayout(size_hint_y=None, height=dp(58), spacing=dp(6))
        keys = (("all",) if with_all else ()) + SPORTS
        for k in keys:
            if k != "all" and not self.s.get(k, True):
                continue
            on = k == current
            t = Tap(orientation="vertical", padding=(0, dp(5)), spacing=0)
            col = SPORT_COL[k]

            def bg(w, *a, c=col, o=on, kk=k):
                w.canvas.before.clear()
                with w.canvas.before:
                    if o:
                        Color(1, 1, 1, 1)
                        RoundedRectangle(pos=w.pos, size=w.size, radius=[dp(16)], texture=self._sgrads[kk])
                    else:
                        Color(*UW.C["card"])
                        RoundedRectangle(pos=w.pos, size=w.size, radius=[dp(16)])
                        Color(*c[:3], 0.9)
                        Line(rounded_rectangle=(w.x + 1, w.y + 1, w.width - 2, w.height - 2, dp(16)), width=1.1)
            t.bind(pos=bg, size=bg)
            ic = UW.Icon(kind=SPORT_ICON[k], size_hint_y=None, height=dp(22), rgba=list((1, 1, 1, 1) if on else col))
            lb = Label(text=f"[b]{SPORT_GR[k]}[/b] {counts.get(k, 0)}", markup=True, font_size=sp(11.5),
                       color=(1, 1, 1, 1) if on else UW.C["ink"], size_hint_y=None, height=dp(22))
            t.add_widget(ic)
            t.add_widget(lb)
            t.bind(on_release=lambda w, kk=k: cb(kk))
            row.add_widget(t)
        parent.add_widget(row)

    def toast(self, msg):
        self.status_msg = msg
        self.sub_text = msg
        Clock.schedule_once(lambda dt: self._set_sub() if not self.busy else None, 4)

    # ================================================================== ανάλυση
    def upcoming(self, sport=None):
        ups = B.upcoming(B.load_cache(), self.s)
        sport = sport or "all"
        return ups if sport == "all" else [m for m in ups if m["sport"] == sport]

    def enrich_pick(self, m, p):
        mp = M.model_prob(self.models, m, p["sign"]) if self.s.get("use_model") else None
        ap = B.consensus(m, p["sign"])
        rs, rl, why = M.reliability(m, p, mp, ap)
        return {"model": mp, "alt": ap, "rel": rs, "rel_label": rl, "why": why}

    def enrich(self, items):
        return [(m, p, self.enrich_pick(m, p)) for m, p in items]

    def trust(self, m):
        return M.match_trust(m, self.models, self.extra.get(m.get("sid")))

    def auto_slip(self, ups, greek=False):
        pool_m = [m for m in ups if M.is_greek(m)] if greek else ups
        stds = B.standards(pool_m, self.s)
        if greek and len(stds) < int(self.s["slip"]):
            stds = B.standards(pool_m, {**self.s, "min_prob": 50})
        rich = [x for x in self.enrich(stds) if not x[1].get("double")]
        for x in rich:
            x[2]["trust"] = self.trust(x[0])["score"]
        good = sorted([x for x in rich if x[2]["trust"] >= 70], key=lambda x: -x[1]["prob"])
        mid = sorted([x for x in rich if 45 <= x[2]["trust"] < 70], key=lambda x: -x[1]["prob"])
        rest = sorted([x for x in rich if x[2]["trust"] < 45], key=lambda x: -x[1]["prob"])
        return (good + mid + rest)[: max(1, int(self.s["slip"]))]

    def pick_card(self, parent, m, p, ex, on_tap=None, show_add=True):
        """Κάρτα επιλογής: δαχτυλίδι πιθανότητας, αγώνας, σημείο, φερεγγυότητα."""
        r = Tap(orientation="horizontal", size_hint_y=None, height=dp(100), spacing=dp(10), padding=(dp(10), dp(10)))
        lc = SPORT_COL.get(m["sport"], league_color(m["league"]))
        tr = ex.get("trust")
        if tr is None:
            tr = self.trust(m)["score"]
        tc = trust_col(tr)

        def bg(*a):
            r.canvas.before.clear()
            with r.canvas.before:
                Color(*UW.C["card"])
                RoundedRectangle(pos=r.pos, size=r.size, radius=[dp(18)])
                Color(*lc)
                RoundedRectangle(pos=(r.x, r.y + dp(12)), size=(dp(4), r.height - dp(24)), radius=[dp(2)])
        r.bind(pos=bg, size=bg)
        ring = UW.ScoreRing(size_hint=(None, None), size=(dp(70), dp(70)), thickness=dp(6), text_size_sp=17,
                            percent=True, color_override=list(tc))
        ring.set_score(p["prob"] * 100, animate=False)
        a = AnchorLayout(size_hint_x=None, width=dp(72))
        a.add_widget(ring)
        r.add_widget(a)
        col = BoxLayout(orientation="vertical")
        t = Label(text=f"[b]{esc(m['home'])} – {esc(m['away'])}[/b]", markup=True, color=UW.C["ink"], font_size=sp(14),
                  halign="left", valign="middle", shorten=True)
        t.bind(size=lambda w, s: setattr(w, "text_size", s))
        sub = Label(text=f"[color={UW.hexc(lc)}][b]{esc(SPORT_GR.get(m['sport'], ''))}[/b][/color] · "
                         f"{esc(m['league'])} · {B.local_time(m)}", markup=True,
                    color=UW.C["muted"], font_size=sp(11), halign="left", valign="middle", shorten=True)
        sub.bind(size=lambda w, s: setattr(w, "text_size", s))
        odds = f" @ {num(p['best'])}" if p.get("best") else ""
        sign = Label(text=f"[b][size=18sp]{esc(p['sign'])}[/size][/b]{odds}  "
                          f"[color={UW.hexc(tc)}][b]φερεγγυότητα {tr}%[/b][/color]",
                     markup=True, color=UW.C["ink"], font_size=sp(12), halign="left", valign="middle", shorten=True)
        sign.bind(size=lambda w, s: setattr(w, "text_size", s))
        col.add_widget(t)
        col.add_widget(sub)
        col.add_widget(sign)
        r.add_widget(col)
        if show_add:
            add = Button(text="+", bold=True, font_size=sp(22), size_hint_x=None, width=dp(42), background_normal="",
                         background_color=UW.C["line"], color=UW.PRIMARY)
            add.bind(on_release=lambda *x: self.add_manual(m, p))
            r.add_widget(add)
        r.bind(on_release=lambda *x: (on_tap or (lambda: self.open_match(m)))())
        parent.add_widget(r)
        return r

    # ================================================================== ενημέρωση
    def update(self, silent=False):
        if self.busy:
            return
        self.busy = True
        self.busy_flag = True
        self._token += 1
        token = self._token
        self.status_msg = "Ενημέρωση από όλες τις πηγές…"
        self._set_sub()
        if not silent:
            self.refresh_current()

        def watchdog(dt):
            if self.busy and self._token == token:
                self.busy = self.busy_flag = False
                self.status_msg = "Η ενημέρωση άργησε πολύ (αργή σύνδεση;). Δοκίμασε ξανά."
                self._set_sub()
                self.refresh_current()
        Clock.schedule_once(watchdog, 150)

        def log(msg):
            def put(dt):
                self.status_msg = msg
                self.sub_text = msg
                lbl = getattr(self, "_status_lbl", None)
                if lbl is not None:
                    lbl.text = msg
            Clock.schedule_once(put)

        def work():
            err = None
            try:
                data = B.fetch_all(self.s, log)
                if self.s.get("use_model") and self.s.get("football"):
                    ups = [m for m in B.upcoming(data, self.s) if m["sport"] == "football" and
                           (m.get("div") or m.get("espn"))]
                    models = M.build_models(ups, log)
                    B._write("models.json", models)
                    self.models = models
                if data.get("notes"):
                    err = "Μερική ενημέρωση: " + data["notes"][0]
            except Exception as e:  # noqa: BLE001
                err = "Σφάλμα: " + str(e)[:120]
            Clock.schedule_once(lambda dt: done(err) if self._token == token else None)

        def done(err):
            self.busy = self.busy_flag = False
            self.status_msg = err or ""
            self._set_sub()
            if err:
                self.sub_text = err[:90]
            if self.sm.current in TABS:
                self.refresh_current()
        threading.Thread(target=work, daemon=True).start()

    def check_update(self, silent=False):
        def work():
            try:
                res, err = UP.check(), None
            except Exception as e:  # noqa: BLE001
                res, err = None, e
            Clock.schedule_once(lambda dt: done(res, err), 0)

        def done(res, err):
            if res:
                self.update_info = res
                if self.sm.current in ("home", "settings"):
                    self.refresh_current()
                if not silent:
                    self.toast("Βρέθηκε νέα έκδοση της εφαρμογής!")
            elif not silent:
                self.toast("Έχεις την τελευταία έκδοση." if err is None else
                           f"Δεν έγινε έλεγχος: {err if isinstance(err, RuntimeError) else 'χωρίς σύνδεση'}")
        if not silent:
            self.toast("Έλεγχος για νέα έκδοση…")
        threading.Thread(target=work, daemon=True).start()

    def update_card(self, box):
        u = self.update_info
        if not u:
            return
        h = self.grad_box(box, self._grads["slip"])
        h.add_widget(UW.text(f"[b]Νέα έκδοση εφαρμογής{(' ' + u['version']) if u['version'] else ''} "
                             f"(build {u['build']})[/b]", 16, (1, 1, 1, 1)))
        h.add_widget(UW.text("Κατέβασε το APK και εγκατάστησέ το πάνω από την τωρινή εφαρμογή. Τα δελτία και το "
                             "ιστορικό σου μένουν.", 12, (1, 1, 1, 0.9)))
        b = Button(text="ΛΗΨΗ ΕΝΗΜΕΡΩΣΗΣ", bold=True, size_hint_y=None, height=dp(44), background_normal="",
                   background_color=(1, 1, 1, 0.25))
        b.bind(on_release=lambda *a: webbrowser.open(u["apk"] or u["page"]))
        h.add_widget(b)

    # ================================================================== ΑΡΧΙΚΗ
    def build_home(self):
        box = self.page("home")
        cache = B.load_cache()
        all_ups = self.upcoming()
        counts = {"all": len(all_ups)}
        for m in all_ups:
            counts[m["sport"]] = counts.get(m["sport"], 0) + 1
        ups = all_ups if self.sport == "all" else [m for m in all_ups if m["sport"] == self.sport]
        stds = self.enrich(B.standards(ups, self.s))
        for x in stds:
            x[2]["trust"] = self.trust(x[0])["score"]
        vals = self.enrich(B.value_picks(ups, self.s))
        with_odds = sum(1 for m in ups if m.get("x12"))
        trusted = [x for x in stds if x[2]["trust"] >= 70]

        hero = self.grad_box(box, self.grad)
        hero.add_widget(UW.text("[b]Η ανάλυση της ημέρας[/b]", size=21, color=(1, 1, 1, 1)))
        hero.add_widget(UW.text(f"{SPORT_GR[self.sport]} · {with_odds} αγώνες με αποδόσεις από "
                                f"{len({B.country_of(m) for m in ups})} χώρες", size=12, color=(1, 1, 1, 0.85)))
        stats = BoxLayout(size_hint_y=None, height=dp(72), spacing=dp(6))
        for n, label, col in ((len(ups), "αγώνες", (1, 1, 1, 0.14)), (len(stds), "σταντάρ", (1, 1, 1, 0.2)),
                              (len(trusted), "φερέγγυα", (1, 1, 1, 0.26)), (len(vals), "με αξία", (1, 1, 1, 0.32))):
            st = BoxLayout(orientation="vertical", padding=(0, dp(6)))

            def sbg(w, *a, c=col):
                w.canvas.before.clear()
                with w.canvas.before:
                    Color(*c)
                    RoundedRectangle(pos=w.pos, size=w.size, radius=[dp(14)])
            st.bind(pos=sbg, size=sbg)
            st.add_widget(Label(text=f"[b]{n}[/b]", markup=True, font_size=sp(24), color=(1, 1, 1, 1)))
            st.add_widget(Label(text=label, font_size=sp(11), color=(1, 1, 1, 0.9)))
            stats.add_widget(st)
        hero.add_widget(stats)
        upd = (f"Ενημέρωση: {cache['updated']}" if cache.get("updated") else "Δεν έχει γίνει ενημέρωση")
        if cache.get("updated") and not cache.get("sofa", True):
            upd += " · το κουπόνι Sofascore δεν ήταν διαθέσιμο"
        self._status_lbl = UW.text(self.status_msg or upd, size=12, color=(1, 1, 1, 0.9))
        hero.add_widget(self._status_lbl)
        b = Button(text="Ενημέρωση…" if self.busy else "ΕΝΗΜΕΡΩΣΗ ΤΩΡΑ", bold=True, size_hint_y=None, height=dp(44),
                   background_normal="", background_color=(1, 1, 1, 0.22), disabled=self.busy)
        b.bind(on_release=lambda *a: self.update())
        hero.add_widget(b)
        self.sport_pills(box, self.sport, lambda k: (setattr(self, "sport", k), self.build_home()), counts,
                         with_all=True)
        self.update_card(box)

        st = M.stats()
        bank = M.bankroll_now(self.s)
        c = self.card(box)
        top = BoxLayout(size_hint_y=None, height=dp(56))
        pc = GREEN if st["profit"] >= 0 else RED
        top.add_widget(UW.text(f"[b]Το κεφάλαιό μου[/b]\n[size=22sp][b]{num(bank)} €[/b][/size]  "
                               f"[color={UW.hexc(pc)}]{'+' if st['profit'] >= 0 else ''}{num(st['profit'])} €[/color]",
                               size=13))
        picks = [pk for s_ in M.load_slips() for pk in s_["picks"] if pk.get("won") is not None]
        if picks:
            hr = sum(1 for pk in picks if pk["won"]) / len(picks)
            exp = sum(pk["prob"] for pk in picks) / len(picks)
            top.add_widget(UW.text(f"[b]Επιτυχία σημείων[/b]\n[size=22sp][b][color={UW.hexc(GREEN if hr >= exp - 0.03 else ORANGE)}]"
                                   f"{pct(hr)}[/color][/b][/size] [size=11sp]αναμ. {pct(exp)}[/size]", size=13,
                                   halign="right"))
        c.add_widget(top)
        limit = bank * float(self.s.get("week_limit", 10)) / 100
        spent = M.week_spent()
        c.add_widget(UW.NutrientBar("Αυτή την εβδομάδα", num(spent), f" € από {num(limit)} €",
                                    "υψηλή" if spent > limit * 0.8 else ("μέτρια" if spent > limit * 0.5 else "χαμηλή"),
                                    max(limit, 0.01)))

        top_picks = sorted(trusted, key=lambda x: (-x[2]["trust"] // 10, -x[1]["prob"]))[:8] or \
            sorted(stds, key=lambda x: -x[2]["trust"])[:6]
        sug = self.auto_slip(ups)
        if sug:
            prob, fair = 1.0, 1.0
            for _, p_, _ in sug:
                prob *= p_["prob"]
                fair *= p_["fair_odds"]
            sc = self.grad_box(box, self._grads["slip"], pad=16, radius=20)
            sc.add_widget(UW.text(f"[b]Προτεινόμενο δελτίο ημέρας[/b]\n{len(sug)} αγώνες · πιθανότητα "
                                  f"[b]{pct(prob)}[/b] · δίκαιη απόδοση [b]{num(fair)}[/b]", size=14,
                                  color=(1, 1, 1, 1)))
            for m_, p_, ex_ in sug:
                sc.add_widget(UW.text(f"[b]{esc(p_['sign'])}[/b]  {esc(m_['home'])} – {esc(m_['away'])}  "
                                      f"[size=11sp]({pct(p_['prob'])} · φερεγγ. {ex_['trust']}%)[/size]", size=13,
                                      color=(1, 1, 1, 0.95)))
            bb = Button(text="ΑΝΟΙΓΜΑ ΔΕΛΤΙΟΥ", bold=True, size_hint_y=None, height=dp(42), background_normal="",
                        background_color=(1, 1, 1, 0.25))
            bb.bind(on_release=lambda *a: (setattr(self, "slip_mode", "Αυτόματο"), self.tab("slip")))
            sc.add_widget(bb)
        box.add_widget(UW.text("[b]Τα πιο σίγουρα[/b]  [size=12sp](υψηλή πιθανότητα και φερεγγυότητα 70%+)[/size]",
                               size=16))
        if not top_picks:
            box.add_widget(UW.text("Δεν υπάρχουν ακόμα επιλογές. Πάτα «Ενημέρωση τώρα».", color=UW.C["muted"]))
        for m, p, ex in top_picks:
            self.pick_card(box, m, p, ex)
        if vals:
            box.add_widget(UW.text("[b]Ευκαιρίες αξίας[/b]  [size=12sp](απόδοση πάνω από τη δίκαιη)[/size]", size=16))
            for m, p, ex in vals[:4]:
                self.pick_card(box, m, p, ex)
        row = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(8))
        self.btn(row, "ΚΟΥΠΟΝΙ", lambda: self.tab("coupon"), color=TAB_COL["coupon"][0])
        self.btn(row, "ΦΤΙΑΞΕ ΔΕΛΤΙΟ", lambda: self.tab("slip"), color=VIOLET)
        box.add_widget(row)
        box.add_widget(UW.text(FOOT, size=11, color=UW.C["muted"]))


    # ================================================================== ΚΟΥΠΟΝΙ
    def coupon_matches(self):
        all_ups = self.upcoming()
        counts = {}
        for m in all_ups:
            counts[m["sport"]] = counts.get(m["sport"], 0) + 1
        ups = [m for m in all_ups if m["sport"] == self.csport]
        f = self.filters
        if f["day"] != "Όλες":
            off = {"Σήμερα": 0, "Αύριο": 1, "Μεθαύριο": 2}[f["day"]]
            target = datetime.date.today() + datetime.timedelta(days=off)
            ups = [m for m in ups if B._start(m) and B._start(m).astimezone().date() == target]
        if f["kind"] == "Με αποδόσεις":
            ups = [m for m in ups if m.get("x12")]
        elif f["kind"] == "Φερέγγυοι":
            ups = [m for m in ups if m.get("x12") and self.trust(m)["score"] >= 70]
        elif f["kind"] == "Ελλάδα":
            ups = [m for m in ups if M.is_greek(m)]
        q = f.get("q", "").strip()
        if q:
            qn = _fold(q)
            ups = [m for m in ups if qn in _fold(m["home"] + " " + m["away"] + " " + m["league"] + " " +
                                                 B.country_of(m))]
        return ups, counts

    def build_coupon(self):
        box = self.page("coupon")
        ups, counts = self.coupon_matches()
        self.sport_pills(box, self.csport, lambda k: (setattr(self, "csport", k), self.build_coupon()), counts)
        self.seg(box, ["Σήμερα", "Αύριο", "Μεθαύριο", "Όλες"], self.filters["day"],
                 lambda o: (self.filters.__setitem__("day", o), self.build_coupon()))
        self.seg(box, ["Με αποδόσεις", "Φερέγγυοι", "Ελλάδα", "Όλοι"], self.filters["kind"],
                 lambda o: (self.filters.__setitem__("kind", o), self.build_coupon()))
        sr = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(6))
        ti = TextInput(text=self.filters.get("q", ""), hint_text="Αναζήτηση ομάδας, χώρας ή διοργάνωσης",
                       multiline=False, font_size=sp(14), padding=(dp(10), dp(12)),
                       background_color=UW.C["card"], foreground_color=UW.C["ink"], cursor_color=UW.PRIMARY,
                       hint_text_color=UW.C["muted"])
        ti.bind(on_text_validate=lambda w: (self.filters.__setitem__("q", w.text), self.build_coupon()))
        sr.add_widget(ti)
        go = Button(text="Βρες" if not self.filters.get("q") else "x", bold=True, size_hint_x=None, width=dp(60),
                    background_normal="", background_color=UW.PRIMARY)
        go.bind(on_release=lambda *a: (self.filters.__setitem__("q", ti.text if not self.filters.get("q") else ""),
                                       self.build_coupon()))
        sr.add_widget(go)
        box.add_widget(sr)
        cache = B.load_cache()
        if self.busy:
            box.add_widget(UW.text(self.status_msg or "Ενημέρωση…", size=12, color=UW.C["muted"]))
        if not ups:
            box.add_widget(UW.text("Δεν υπάρχουν αγώνες με αυτά τα φίλτρα." + (
                "" if cache.get("updated") else " Πάτα την ανανέωση πάνω δεξιά."), color=UW.C["muted"]))
            box.add_widget(UW.text(COUPON_NOTE, size=11, color=UW.C["muted"]))
            return
        tree = B.tree(ups).get(self.csport, {})
        nl = sum(len(v) for v in tree.values())
        box.add_widget(UW.text(f"[b]{len(ups)} αγώνες[/b] · {len(tree)} χώρες · {nl} διοργανώσεις   "
                               f"[size=11sp]% = πιθανότητα · δίπλα η απόδοση[/size]", size=13, color=UW.C["muted"]))
        opened = self.open_c.setdefault(self.csport, set())
        force = bool(self.filters.get("q")) or len(ups) <= 25
        for country, leagues in tree.items():
            n = sum(len(v) for v in leagues.values())
            sec = UW.Section(f"{esc(country)}   [color={UW.hexc(UW.C['muted'])}][size=12sp]{n} αγώνες · "
                             f"{len(leagues)} διοργ.[/size][/color]",
                             opened=force or country in opened,
                             builder=lambda body, lg=leagues, c=country: self._fill_country(body, c, lg))
            sec.bind(opened=lambda w, v, c=country: opened.add(c) if v else opened.discard(c))
            box.add_widget(sec)
        box.add_widget(UW.text(COUPON_NOTE, size=11, color=UW.C["muted"]))

    def _fill_country(self, body, country, leagues):
        for lg, ms in leagues.items():
            hr = BoxLayout(size_hint_y=None, height=dp(34), spacing=dp(6))
            tier = min(x.get("tier", 3) or 3 for x in ms)
            hr.add_widget(UW.Chip(esc(lg)[:38], league_color(country + lg)))
            if tier == 1:
                hr.add_widget(UW.Chip("TOP", GOLD))
            hr.add_widget(Widget())
            cnt = Label(text=f"{len(ms)}", color=UW.C["muted"], font_size=sp(12), size_hint_x=None, width=dp(30))
            hr.add_widget(cnt)
            body.add_widget(hr)
            for m in ms[:20]:
                self.coupon_row(body, m)
            if len(ms) > 20:
                self.ghost(body, f"Όλοι οι αγώνες ({len(ms)})",
                           lambda c=country, l_=lg, mm=ms: self.open_league(c, l_, mm), h=38)

    def open_league(self, country, lg, ms):
        box = self.page("league")
        h = self.grad_box(box, self._sgrads[self.csport])
        h.add_widget(UW.text(f"[b]{esc(lg)}[/b]\n{esc(country)} · {len(ms)} αγώνες", size=17, color=(1, 1, 1, 1)))
        c = self.card(box, pad=10)
        for m in ms:
            self.coupon_row(c, m)
        self.show("league")
        self.title_text = lg[:28]

    def coupon_row(self, parent, m):
        """Γραμμή κουπονιού: ώρα · ομάδες · 1/Χ/2 με πιθανότητα και απόδοση · φερεγγυότητα."""
        r = Tap(orientation="horizontal", size_hint_y=None, height=dp(62), spacing=dp(6), padding=(dp(2), dp(4)))

        def bg(*a):
            r.canvas.before.clear()
            with r.canvas.before:
                Color(*UW.C["line"][:3], 0.55)
                RoundedRectangle(pos=(r.x, r.y + dp(1)), size=(r.width, r.height - dp(2)), radius=[dp(12)])
        r.bind(pos=bg, size=bg)
        t = B._start(m)
        tl = t.astimezone() if t else None
        when = Label(text=(f"[b]{tl:%H:%M}[/b]\n[size=10sp]{B.GR_DAYS[tl.weekday()]} {tl:%d/%m}[/size]" if tl else ""),
                     markup=True, color=UW.C["ink"], font_size=sp(13), size_hint_x=None, width=dp(48), halign="center")
        r.add_widget(when)
        names = Label(text=f"{esc(m['home'])}\n{esc(m['away'])}", color=UW.C["ink"], font_size=sp(12.5),
                      halign="left", valign="middle", shorten=True, markup=True)
        names.bind(size=lambda w, s: setattr(w, "text_size", s))
        r.add_widget(names)
        o = m.get("x12")
        if o and o[0] and o[2]:
            f = B._fair(o)
            best = max(range(3), key=lambda i: f[i])
            for i, sgn in enumerate(("1", "Χ", "2")):
                if not o[i]:
                    continue
                on = i == best
                cell = BoxLayout(orientation="vertical", size_hint_x=None, width=dp(46))

                def cbg(w, *a, hl=on):
                    w.canvas.before.clear()
                    with w.canvas.before:
                        Color(*(UW.PRIMARY if hl else UW.C["card"]))
                        RoundedRectangle(pos=(w.x, w.y + dp(4)), size=(w.width, w.height - dp(8)), radius=[dp(9)])
                cell.bind(pos=cbg, size=cbg)
                fg = (1, 1, 1, 1) if on else UW.C["ink"]
                cell.add_widget(Label(text=f"[b]{f[i] * 100:.0f}%[/b]", markup=True, font_size=sp(12.5), color=fg))
                cell.add_widget(Label(text=f"{sgn} {num(o[i])}", font_size=sp(9.5),
                                      color=(1, 1, 1, 0.85) if on else UW.C["muted"]))
                r.add_widget(cell)
            sc = self.trust(m)["score"]
            badge = Label(text=f"[b]{sc}[/b]", markup=True, font_size=sp(12), color=(1, 1, 1, 1), size_hint_x=None,
                          width=dp(34))

            def bbg(w, *a, c=trust_col(sc)):
                w.canvas.before.clear()
                with w.canvas.before:
                    Color(*c)
                    d = dp(30)
                    Ellipse(pos=(w.center_x - d / 2, w.center_y - d / 2), size=(d, d))
            badge.bind(pos=bbg, size=bbg)
            r.add_widget(badge)
        else:
            r.add_widget(Label(text="χωρίς\nαποδόσεις", font_size=sp(10.5), color=UW.C["muted"], size_hint_x=None,
                               width=dp(80), halign="center"))
        r.bind(on_release=lambda *a: self.open_match(m))
        parent.add_widget(r)

    # ================================================================== ΑΓΩΝΑΣ
    def open_match(self, m):
        self._cur_match = m
        sid = m.get("sid")
        ext = self.extra.get(sid) if sid else None
        if ext and not m.get("x12") and (ext.get("odds") or {}).get("x12"):
            o = ext["odds"]
            m = dict(m, x12=o["x12"], max=o["x12"], open=o.get("open"), ou=o.get("ou"), btts=o.get("btts"),
                     margin=B._margin(o["x12"]))
        box = self.page("match")
        h = self.grad_box(box, self._sgrads.get(m["sport"], self.grad))
        h.add_widget(UW.text(f"[b]{esc(m['home'])}[/b]\n[size=13sp]κατά[/size]\n[b]{esc(m['away'])}[/b]", size=19,
                             halign="center", color=(1, 1, 1, 1)))
        h.add_widget(UW.text(f"{esc(SPORT_GR.get(m['sport'], ''))} · {esc(m['league'])}\n{B.local_time(m)}", size=12,
                             color=(1, 1, 1, 0.9), halign="center"))
        srcs = [(s_, (1, 1, 1, 0.22)) for s_ in (m.get("sources") or [])]
        if m.get("pin"):
            srcs.append(("Pinnacle", (1, 1, 1, 0.3)))
        self.chips(h, srcs)
        # φόρμα: από το μοντέλο (ποδόσφαιρο) ή από το Sofascore
        fh, fa = M.team_form(self.models, m)
        sf = (ext or {}).get("form") or {}
        if not (fh or fa) and sf:
            fh, fa = (sf.get("home") or {}).get("form"), (sf.get("away") or {}).get("form")
        if fh or fa:
            c = self.card(box)

            def fchips(team, f, pos=None):
                row = BoxLayout(size_hint_y=None, height=dp(30), spacing=dp(4))
                lab = Label(text=team + (f" ({pos}ος)" if pos else ""), color=UW.C["ink"], font_size=sp(12),
                            size_hint_x=0.45, halign="left", valign="middle", shorten=True)
                lab.bind(size=lambda w, s: setattr(w, "text_size", s))
                row.add_widget(lab)
                for ch in (f or ""):
                    row.add_widget(UW.Chip(ch, GREEN if ch == "Ν" else (RED if ch == "Η" else UW.C["muted"])))
                row.add_widget(Widget())
                return row
            c.add_widget(UW.text("[b]Φόρμα[/b] (τελευταίοι 5, πιο πρόσφατος αριστερά · Ν νίκη, Ι ισοπαλία, Η ήττα)",
                                 size=13))
            c.add_widget(fchips(m["home"], fh, (sf.get("home") or {}).get("pos")))
            c.add_widget(fchips(m["away"], fa, (sf.get("away") or {}).get("pos")))
        self._trust_card(box, m)
        if sid and ext is None:
            box.add_widget(UW.text("Φόρτωση επιπλέον στοιχείων (κοινό, φόρμα, ιστορικό αποδόσεων)…", size=12,
                                   color=UW.C["muted"]))
            self._load_extra(m)
        elif ext:
            self._extra_card(box, m, ext)
        picks = B.picks_for(m, self.s["overunder"])
        if not picks:
            c = self.card(box)
            c.add_widget(UW.text("[b]Δεν υπάρχουν ακόμα αποδόσεις[/b] για αυτόν τον αγώνα. Συνήθως ανοίγουν 1–3 ημέρες "
                                 "πριν. Μπορείς να γράψεις τις αποδόσεις του ΟΠΑΠ παρακάτω.", size=13))
        groups = [("Τελικό αποτέλεσμα", [p for p in picks if p["sign"] in ("1", "Χ", "2")]),
                  ("Διπλή ευκαιρία", [p for p in picks if p.get("double")]),
                  ("Γκολ", [p for p in picks if p["sign"].startswith(("Over", "Under")) or "Γκολ" in p["sign"]])]
        for title, ps in groups:
            if not ps:
                continue
            cc = self.card(box)
            cc.add_widget(UW.text(f"[b]{title}[/b]  [size=11sp]πιθανότητα κέρδους · δίκαιη απόδοση[/size]", size=15))
            for p in ps:
                ex = self.enrich_pick(m, p)
                row = BoxLayout(size_hint_y=None, height=dp(52), spacing=dp(8))
                info = []
                if ex["model"] is not None:
                    info.append(f"μοντέλο {pct(ex['model'])}")
                if ex["alt"] is not None:
                    info.append(f"2η πηγή {pct(ex['alt'])}")
                if p.get("best"):
                    info.append(f"απόδοση {num(p['best'])}")
                hr = M.hit_rate(p["prob"])
                if hr:
                    info.append(f"στο ιστορικό σου βγήκε {pct(hr[0])} ({hr[1]})")
                bar = UW.NutrientBar(f"{p['sign']}  {p['name']}", pct(p['prob']), f"   δίκαιη {num(p['fair_odds'])}",
                                     None, 1.0)
                bar.children[-1].text += (f"\n[size=11sp][color={UW.hexc(UW.C['muted'])}]{' · '.join(info)}"
                                          f"[/color][/size]" if info else "")
                bar.children[-1].shorten = True
                bar.height = dp(56)
                bar.children[-1].height = dp(36)
                row.add_widget(bar)
                add = Button(text="+", bold=True, font_size=sp(22), size_hint_x=None, width=dp(44),
                             background_normal="", background_color=UW.C["line"], color=UW.PRIMARY)
                add.bind(on_release=lambda w, pp=p: self.add_manual(m, pp))
                row.add_widget(add)
                cc.add_widget(row)
                self._fill_bar(bar, p["prob"], REL_RGBA.get(ex["rel_label"], UW.PRIMARY))
        self._opap_card(box, m)
        best = B.best_pick(m, self.s["overunder"])
        if best:
            ex = self.enrich_pick(m, best)
            rc = self.card(box)
            rc.add_widget(UW.text(f"[b]Αξιοπιστία εκτίμησης: [color={UW.hexc(REL_RGBA[ex['rel_label']])}]"
                                  f"{ex['rel_label']} ({ex['rel']}/100)[/color][/b]", size=14))
            if ex["why"]:
                rc.add_widget(UW.text(" · ".join(ex["why"]), size=12, color=UW.C["muted"]))
        box.add_widget(UW.text(FOOT, size=11, color=UW.C["muted"]))
        self.show("match")

    def _load_extra(self, m):
        sid = m["sid"]

        def work():
            try:
                import sofa as SF
                d = SF.details(sid, m["sport"])
            except Exception:  # noqa: BLE001
                d = {}
            Clock.schedule_once(lambda dt: done(d))

        def done(d):
            self.extra[sid] = d
            if len(self.extra) > 300:
                self.extra.pop(next(iter(self.extra)))
            if self.sm.current == "match" and self._cur_match is not None and self._cur_match.get("sid") == sid:
                sv = self.pages["match"][0]
                y = sv.scroll_y
                self.open_match(self._cur_match)
                sv.scroll_y = y
        threading.Thread(target=work, daemon=True).start()

    def _extra_card(self, box, m, ext):
        """Κοινό, αποτελέσματα μεταξύ τους και ιστορικό ποσοστό επιτυχίας για την ίδια απόδοση."""
        if not any(ext.get(k) for k in ("votes", "h2h", "win")):
            return
        c = self.card(box)
        c.add_widget(UW.text("[b]Τι άλλο δείχνουν τα στοιχεία[/b]", size=15))
        v = ext.get("votes")
        if v:
            c.add_widget(UW.text(f"Ψήφοι κοινού ({v['n']})", size=12, color=UW.C["muted"]))
            c.add_widget(self._tri_bar(v["p"]))
        hh = ext.get("h2h")
        if hh and sum(hh.values()):
            tot = sum(hh.values())
            c.add_widget(UW.text(f"Μεταξύ τους ({tot} αγώνες): {esc(m['home'])} [b]{hh['home']}[/b] · ισοπαλίες "
                                 f"[b]{hh['draw']}[/b] · {esc(m['away'])} [b]{hh['away']}[/b]", size=12))
        w = ext.get("win") or {}
        for sgn, team in (("1", m["home"]), ("2", m["away"])):
            d = w.get(sgn)
            if not d:
                continue
            good = d["actual"] >= d["expected"]
            c.add_widget(UW.text(
                f"[b]{sgn}[/b] {esc(team)}: με απόδοση {num(d['odds'] or 0)} ιστορικά κερδίζει "
                f"[color={UW.hexc(GREEN if good else ORANGE)}][b]{pct(d['actual'])}[/b][/color] (αναμενόμενο "
                f"{pct(d['expected'])})", size=12))

    def _fill_bar(self, bar, frac, col):
        """Επαναχρωματισμός της μπάρας με το χρώμα της αξιοπιστίας."""
        w = bar.bar

        def draw(*a):
            w.canvas.clear()
            with w.canvas:
                Color(*UW.C["line"])
                RoundedRectangle(pos=w.pos, size=w.size, radius=[dp(6)])
                Color(*col)
                RoundedRectangle(pos=w.pos, size=(w.width * max(0.02, min(1, frac)), w.height), radius=[dp(6)])
        w.bind(pos=draw, size=draw)
        Clock.schedule_once(draw, 0.1)


    # ================================================================== φερεγγυότητα & ΟΠΑΠ
    def _trust_card(self, box, m):
        t = M.match_trust(m, self.models, self.extra.get(m.get("sid")))
        col = trust_col(t["score"])
        c = self.card(box)
        top = BoxLayout(size_hint_y=None, height=dp(96), spacing=dp(12))
        ring = UW.ScoreRing(size_hint=(None, None), size=(dp(90), dp(90)), thickness=dp(8), text_size_sp=20,
                            percent=True, color_override=list(col))
        Clock.schedule_once(lambda dt: ring.set_score(t["score"]), 0.05)
        a = AnchorLayout(size_hint_x=None, width=dp(94))
        a.add_widget(ring)
        top.add_widget(a)
        top.add_widget(UW.text(f"[b]Φερεγγυότητα αγώνα[/b]\n[color={UW.hexc(col)}][b]{t['label']}[/b][/color]"
                               f"\n[size=12sp]από {len(t['rows'])} πηγές και {len(t['checks'])} ελέγχους[/size]",
                               size=16))
        c.add_widget(top)
        if t["rows"]:
            c.add_widget(UW.text("[b]Τι λέει κάθε πηγή[/b]  [size=11sp](πιθανότητα 1 · Χ · 2)[/size]", size=13))
            for name, probs in t["rows"]:
                c.add_widget(UW.text(name, size=12, color=UW.C["muted"]))
                c.add_widget(self._tri_bar(probs))
        for ok, txt in t["checks"]:
            tag, tc = ({True: ("Καλό", (0.15, 0.75, 0.4, 1)), None: ("Προσοχή", ORANGE),
                        False: ("Κίνδυνος", (0.9, 0.25, 0.25, 1))})[ok]
            r = BoxLayout(size_hint_y=None, height=dp(30), spacing=dp(8))
            r.add_widget(UW.Chip(tag, tc))
            lb = UW.text(txt, size=12)
            r.add_widget(lb)
            lb.bind(height=lambda w, v, rr=r: setattr(rr, "height", max(dp(30), v)))
            c.add_widget(r)

    def _tri_bar(self, probs):
        """Μία μπάρα χωρισμένη σε 1 / Χ / 2 με χρώματα και ποσοστά."""
        w = Widget(size_hint_y=None, height=dp(22))
        labels = [Label(text="", bold=True, font_size=sp(11), color=(1, 1, 1, 1)) for _ in range(3)]
        for lb in labels:
            w.add_widget(lb)

        def draw(*a):
            w.canvas.before.clear()
            x = w.x
            tot = sum(probs) or 1
            with w.canvas.before:
                for i, (sgn, pv) in enumerate(zip(("1", "Χ", "2"), probs)):
                    ww = w.width * pv / tot
                    Color(*SIGN_COL[sgn])
                    RoundedRectangle(pos=(x, w.y), size=(max(1, ww - dp(2)), w.height), radius=[dp(6)])
                    labels[i].pos = (x, w.y)
                    labels[i].size = (ww, w.height)
                    labels[i].text = f"{sgn} {pv * 100:.0f}%" if ww > dp(46) else ""
                    x += ww
        w.bind(pos=draw, size=draw)
        Clock.schedule_once(draw, 0.15)
        return w

    def _opap_card(self, box, m):
        c = self.card(box)
        c.add_widget(UW.text("[b]Αποδόσεις ΟΠΑΠ / ελληνικής εταιρείας[/b]", size=15))
        c.add_widget(UW.text("Γράψε τις αποδόσεις του κουπονιού σου για να δεις αν αξίζουν. Μπαίνουν και στον "
                             "έλεγχο φερεγγυότητας.", size=12, color=UW.C["muted"]))
        three = m["sport"] == "football"
        signs = ("1", "Χ", "2") if three else ("1", "2")
        op = B.opap_get(m)
        o = m.get("x12")
        fair = {}
        if o and o[0] and o[2]:
            fair = dict(zip(("1", "Χ", "2"), B._fair(o)))
        row = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(6))
        ins = {}
        for sgn in signs:
            ti = TextInput(text=f"{op[sgn]:g}" if op.get(sgn) else "", hint_text=sgn, input_filter="float",
                           multiline=False, halign="center", background_color=UW.C["line"],
                           foreground_color=UW.C["ink"], hint_text_color=UW.C["muted"])
            ins[sgn] = ti
            row.add_widget(ti)
        c.add_widget(row)
        res = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(4))
        res.bind(minimum_height=res.setter("height"))
        c.add_widget(res)

        def show():
            res.clear_widgets()
            cur = B.opap_get(m)
            for sgn in signs:
                if not cur.get(sgn):
                    continue
                if not fair.get(sgn):
                    imp = 1 / cur[sgn]
                    res.add_widget(UW.text(f"[b]{sgn}[/b]: απόδοση {num(cur[sgn])} → η εταιρεία δίνει πιθανότητα "
                                           f"{pct(imp)} (μαζί με το κέρδος της)", size=13))
                    continue
                v = B.opap_value(fair[sgn], cur[sgn])
                good = v > 0
                txt = (f"[b]{sgn}[/b]: {num(cur[sgn])} · δίκαιη {num(1 / fair[sgn])} · κέρδος {pct(fair[sgn])} → "
                       + (f"[color={UW.hexc(GREEN)}][b]ΑΞΙΑ +{v * 100:.0f}%[/b][/color]" if good else
                          f"[color={UW.hexc(RED)}]χωρίς αξία ({v * 100:.0f}%)[/color]"))
                res.add_widget(UW.text(txt, size=13))

        def save():
            for sgn, ti in ins.items():
                try:
                    v = float(ti.text.replace(",", ".")) if ti.text.strip() else None
                except ValueError:
                    v = None
                B.opap_set(m, sgn, v if v and v > 1 else None)
            show()
            self.toast("Αποθηκεύτηκαν οι αποδόσεις")
        self.btn(c, "ΕΛΕΓΧΟΣ ΑΞΙΑΣ", save, color=VIOLET, h=44)
        links = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(6))
        for name, url in BOOKS:
            b = Button(text=name, font_size=sp(11.5), background_normal="", background_color=UW.C["line"],
                       color=UW.C["ink"])
            b.bind(on_release=lambda w, u=url: webbrowser.open(u))
            links.add_widget(b)
        c.add_widget(links)
        show()

    # ================================================================== ΔΕΛΤΙΟ
    def add_manual(self, m, p):
        key = (m["home"], m["away"], m["start"][:10])
        self.manual = [x for x in self.manual if (x["m"]["home"], x["m"]["away"], x["m"]["start"][:10]) != key]
        self.manual.append({"m": m, "p": p})
        B._write("manual_slip.json", self.manual)
        self.slip_mode = "Δικό μου"
        self.status_msg = f"Μπήκε στο δελτίο: {m['home']} – {m['away']} ({p['sign']})"

    def build_slip(self):
        box = self.page("slip")
        self.seg(box, ["Αυτόματο", "Ελληνικό", "Δικό μου"], self.slip_mode,
                 lambda o: (setattr(self, "slip_mode", o), self.build_slip()))
        ups = self.upcoming()
        if self.slip_mode == "Δικό μου":
            now = datetime.datetime.now(datetime.timezone.utc)
            self.manual = [x for x in self.manual if B._start(x["m"]) and B._start(x["m"]) > now]
            chosen = [(x["m"], x["p"], self.enrich_pick(x["m"], x["p"])) for x in self.manual]
            if not chosen:
                box.add_widget(UW.text("Το δελτίο σου είναι άδειο. Πάτα «+» σε μια επιλογή (Σήμερα, Αγώνες ή σελίδα "
                                       "αγώνα).", color=UW.C["muted"]))
        else:
            chosen = self.auto_slip(ups, greek=self.slip_mode == "Ελληνικό")
            if not chosen:
                box.add_widget(UW.text("Δεν υπάρχουν αρκετοί αγώνες. Πάτα ενημέρωση ή άλλαξε τις ρυθμίσεις.",
                                       color=UW.C["muted"]))
        for m, p, ex in chosen:
            card = self.pick_card(box, m, p, ex, show_add=False)
            if self.slip_mode == "Δικό μου":
                rm = Button(text="x", size_hint_x=None, width=dp(40), background_normal="",
                            background_color=UW.C["line"], color=RED)
                rm.bind(on_release=lambda w, mm=m: self._rm_manual(mm))
                card.add_widget(rm)
        if not chosen:
            return
        prob, fair = 1.0, 1.0
        for _, p, _ in chosen:
            prob *= p["prob"]
            fair *= p["fair_odds"]
        c = self.card(box)
        row = BoxLayout(size_hint_y=None, height=dp(110), spacing=dp(12))
        ring = UW.ScoreRing(size_hint=(None, None), size=(dp(104), dp(104)), thickness=dp(9), text_size_sp=24,
                            percent=True)
        Clock.schedule_once(lambda dt: ring.set_score(prob * 100), 0.05)
        a = AnchorLayout(size_hint_x=None, width=dp(108))
        a.add_widget(ring)
        row.add_widget(a)
        info = BoxLayout(orientation="vertical")
        info.add_widget(UW.text(f"[b]Πιθανότητα να βγει όλο[/b]\n{len(chosen)} επιλογές", size=14))
        info.add_widget(UW.text(f"Δίκαιη συνολική απόδοση: [b]{num(fair)}[/b]", size=14))
        row.add_widget(info)
        c.add_widget(row)
        c.add_widget(UW.text(f"Αν ο ΟΠΑΠ δίνει πάνω από {num(fair)}, το δελτίο έχει αξία. Αν δίνει λιγότερο, "
                             f"μακροπρόθεσμα χάνεις.", size=12, color=UW.C["muted"]))
        c2 = self.card(box)
        c2.add_widget(UW.text(f"[b]Πόσα να ποντάρω[/b]   κεφάλαιο {num(M.bankroll_now(self.s))} € · "
                              f"{self.s.get('risk')}", size=14))
        r2 = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(6))
        odds_in = TextInput(hint_text="Συνολική απόδοση ΟΠΑΠ", input_filter="float", multiline=False)
        stake_in = TextInput(hint_text="Ποσό €", input_filter="float", multiline=False)
        r2.add_widget(odds_in)
        r2.add_widget(stake_in)
        c2.add_widget(r2)
        advice = UW.text("", size=13)
        c2.add_widget(advice)

        def recalc(*a):
            try:
                o = float(odds_in.text.replace(",", ".")) if odds_in.text else None
            except ValueError:
                o = None
            stv, note, left = M.suggest_stake(self.s, prob, o)
            stake_in.text = f"{stv:g}"
            advice.text = f"Πρόταση: [b]{num(stv)} €[/b]. {esc(note)}"
        odds_in.bind(text=recalc)
        recalc()

        def save():
            try:
                stv = float(stake_in.text.replace(",", ".") or 0)
                o = float(odds_in.text.replace(",", ".")) if odds_in.text else fair
            except ValueError:
                return
            M.add_slip([M.pick_record(m, p, ex["model"], ex["rel"]) for m, p, ex in chosen], stv, o, self.slip_mode)
            if self.slip_mode == "Δικό μου":
                self.manual = []
                B._write("manual_slip.json", [])
            self.tab("history")
        self.btn(c2, "ΑΠΟΘΗΚΕΥΣΗ ΣΤΟ ΙΣΤΟΡΙΚΟ", save, color=GREEN)
        box.add_widget(UW.text(FOOT, size=11, color=UW.C["muted"]))

    def _rm_manual(self, m):
        key = (m["home"], m["away"], m["start"][:10])
        self.manual = [x for x in self.manual if (x["m"]["home"], x["m"]["away"], x["m"]["start"][:10]) != key]
        B._write("manual_slip.json", self.manual)
        self.build_slip()

    # ================================================================== ΙΣΤΟΡΙΚΟ
    def build_history(self):
        box = self.page("history")
        st = M.stats()
        bank = M.bankroll_now(self.s)
        c = self.card(box)
        row = BoxLayout(size_hint_y=None, height=dp(70))
        for v, label, col in ((f"{num(bank)} €", "κεφάλαιο", UW.C["ink"]),
                              (f"{'+' if st['profit'] >= 0 else ''}{num(st['profit'])} €", "κέρδος/ζημιά",
                               GREEN if st["profit"] >= 0 else RED),
                              (f"{st['won']}/{st['settled']}", "κερδισμένα", UW.C["ink"])):
            b = BoxLayout(orientation="vertical")
            b.add_widget(Label(text=f"[b]{v}[/b]", markup=True, color=col, font_size=sp(19)))
            b.add_widget(Label(text=label, color=UW.C["muted"], font_size=sp(11)))
            row.add_widget(b)
        c.add_widget(row)
        if st.get("clv_n"):
            share = st["clv_pos"] / st["clv_n"]
            c.add_widget(UW.text(f"[b]Κίνηση γραμμής:[/b] σε {st['clv_pos']} από {st['clv_n']} επιλογές ({pct(share)}) η "
                                 f"αγορά κινήθηκε προς τη δική σου επιλογή μέχρι την έναρξη. Πάνω από 50% σημαίνει ότι "
                                 f"διαλέγεις καλά, ακόμα κι όταν η τύχη δεν βοηθά.", size=13))
        if st["buckets"]:
            cc = self.card(box)
            cc.add_widget(UW.text("[b]Πόσο σωστές βγήκαν οι πιθανότητες[/b]", size=15))
            for lo, (n, w, ps) in st["buckets"].items():
                nb = UW.NutrientBar(f"Σημεία {lo}–{lo + 10}%", pct(w / n), f"  ({w}/{n}, αναμ. {pct(ps / n)})", None, 1.0)
                cc.add_widget(nb)
                self._fill_bar(nb, w / n, GREEN if w / n >= ps / n - 0.03 else AMBER)
        per = {}
        for sl in M.load_slips():
            for pk in sl["picks"]:
                if pk.get("won") is not None:
                    e = per.setdefault(pk["sport"], [0, 0, 0.0])
                    e[0] += 1
                    e[1] += 1 if pk["won"] else 0
                    e[2] += pk["prob"]
        if per:
            cc = self.card(box)
            cc.add_widget(UW.text("[b]Ποσοστό επιτυχίας ανά άθλημα[/b]", size=15))
            for sp_, (n, w_, ps) in per.items():
                nb = UW.NutrientBar(SPORT_GR.get(sp_, sp_), pct(w_ / n), f"  ({w_}/{n}, αναμ. {pct(ps / n)})", None, 1.0)
                cc.add_widget(nb)
                self._fill_bar(nb, w_ / n, SPORT_COL.get(sp_, GREEN))
        self.btn(box, "Έλεγχος αποτελεσμάτων…" if self.settle_busy else "ΕΛΕΓΧΟΣ ΑΠΟΤΕΛΕΣΜΑΤΩΝ", self.settle)
        if self.status_msg:
            box.add_widget(UW.text(self.status_msg, size=12, color=UW.C["muted"]))
        slips = M.load_slips()
        if not slips:
            box.add_widget(UW.text("Δεν έχεις αποθηκεύσει ακόμα δελτία.", color=UW.C["muted"]))
        for sl in slips[:60]:
            col = {"κέρδισε": GREEN, "χάθηκε": RED}.get(sl["status"], BLUE)
            cc = self.card(box, pad=12)
            self.chips(cc, [({"κέρδισε": "ΚΕΡΔΙΣΕ", "χάθηκε": "ΧΑΘΗΚΕ"}.get(sl["status"], "ΕΚΚΡΕΜΕΙ"), col),
                            (sl["kind"], UW.C["line"])])
            cc.add_widget(UW.text(f"{sl['date']} · ποσό {num(sl['stake'])} € · απόδοση {num(sl['odds'] or 0)}",
                                  size=12, color=UW.C["muted"]))
            for pk in sl["picks"]:
                mark = ("[color=#2FAE5A]ΝΑΙ[/color]" if pk.get("won") else "[color=#E03131]ΟΧΙ[/color]") \
                    if pk.get("won") is not None else "…"
                res = f" ({pk['result']})" if pk.get("result") else ""
                cc.add_widget(UW.text(f"{mark}  {esc(pk['home'])} – {esc(pk['away'])}: [b]{esc(pk['sign'])}[/b] "
                                      f"{pct(pk['prob'])}{res}", size=13))
            self.ghost(cc, "Διαγραφή", lambda sid=sl["id"]: (M.delete_slip(sid), self.build_history()), h=36)
        if any(s_["status"] == "εκκρεμεί" for s_ in slips) and not self.settle_busy and not getattr(self, "_auto_settled", 0):
            self._auto_settled = 1
            Clock.schedule_once(lambda dt: self.settle(), 0.5)

    def settle(self):
        if self.settle_busy:
            return
        self.settle_busy = True

        def work():
            try:
                n = M.settle_all()
                msg = f"Ενημερώθηκαν {n} αποτελέσματα." if n else "Δεν υπάρχουν ακόμα νέα αποτελέσματα."
            except Exception as e:  # noqa: BLE001
                msg = "Σφάλμα ελέγχου: " + str(e)[:80]
            Clock.schedule_once(lambda dt: done(msg))

        def done(msg):
            self.settle_busy = False
            self.status_msg = msg
            if self.sm.current == "history":
                self.build_history()
        threading.Thread(target=work, daemon=True).start()

    # ================================================================== ΡΥΘΜΙΣΕΙΣ
    def build_settings(self):
        box = self.page("settings")
        s = self.s
        w = {}

        def line(parent, label, widget):
            r = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(8))
            lb = Label(text=label, color=UW.C["ink"], halign="left", valign="middle", font_size=sp(14))
            lb.bind(size=lambda x, v: setattr(x, "text_size", v))
            r.add_widget(lb)
            widget.size_hint_x = 0.42
            r.add_widget(widget)
            parent.add_widget(r)

        self.update_card(box)
        c = self.card(box)
        c.add_widget(UW.text("[b]Αθλήματα και πηγές[/b]", size=15))
        for key, label in (("football", "Ποδόσφαιρο"), ("basketball", "Μπάσκετ"), ("volleyball", "Βόλεϊ"),
                           ("sofa", "Κουπόνι όλων των αγώνων (Sofascore)"), ("overunder", "Και Over/Under, Γκολ-Γκολ"),
                           ("use_model", "Στατιστικό μοντέλο και φόρμα")):
            cb = CheckBox(active=bool(s.get(key, True)), color=UW.C["ink"])
            w[key] = cb
            line(c, label, cb)
        for key, label, vals in (("hours", "Αγώνες των επόμενων ωρών", ["24", "48", "72", "96", "120"]),
                                 ("min_prob", "Ελάχιστη πιθανότητα «σταντάρ» %", ["55", "60", "65", "70", "75", "80", "85"]),
                                 ("slip", "Αγώνες στο αυτόματο δελτίο", ["1", "2", "3", "4", "5", "6"]),
                                 ("auto_min", "Αυτόματη ανανέωση (λεπτά, 0 = όχι)", ["0", "15", "30", "60", "120"])):
            sp_ = Spinner(text=str(s.get(key, 30)), values=vals)
            w[key] = sp_
            line(c, label, sp_)
        c2 = self.card(box)
        c2.add_widget(UW.text("[b]Διαχείριση κεφαλαίου[/b]", size=15))
        bank = TextInput(text=f"{float(s.get('bankroll', 100)):g}", input_filter="float", multiline=False)
        w["bankroll"] = bank
        line(c2, "Αρχικό κεφάλαιο (€)", bank)
        risk = Spinner(text=s.get("risk", "Συντηρητικό"), values=list(M.RISK))
        w["risk"] = risk
        line(c2, "Προφίλ ρίσκου", risk)
        wl = Spinner(text=str(s.get("week_limit", 10)), values=["5", "10", "15", "20", "30"])
        w["week_limit"] = wl
        line(c2, "Όριο εβδομάδας (% κεφαλαίου)", wl)
        c3 = self.card(box)
        c3.add_widget(UW.text("[b]Εμφάνιση[/b]", size=15))
        th = Spinner(text=THEMES_GR.get(s.get("theme", "night"), "Νύχτα"), values=list(THEMES_GR.values()))
        w["theme"] = th
        line(c3, "Θέμα (με επανεκκίνηση)", th)
        msg = UW.text("", size=12, color=GREEN)

        def save():
            keys = ("football", "basketball", "volleyball", "sofa", "hours", "use_model")
            old = tuple(s.get(k) for k in keys)
            try:
                bv = float(w["bankroll"].text.replace(",", "."))
            except ValueError:
                bv = 100.0
            s.update(football=w["football"].active, basketball=w["basketball"].active,
                     volleyball=w["volleyball"].active, sofa=w["sofa"].active,
                     overunder=w["overunder"].active, use_model=w["use_model"].active, hours=int(w["hours"].text),
                     min_prob=int(w["min_prob"].text), slip=int(w["slip"].text), auto_min=int(w["auto_min"].text),
                     bankroll=bv, risk=w["risk"].text, week_limit=int(w["week_limit"].text),
                     theme={v: k for k, v in THEMES_GR.items()}.get(w["theme"].text, "night"))
            B.save_settings(s)
            msg.text = "Αποθηκεύτηκε."
            if tuple(s.get(k) for k in keys) != old:
                self.update()
        self.btn(box, "ΑΠΟΘΗΚΕΥΣΗ", save, color=GREEN)
        box.add_widget(msg)
        c4 = self.card(box)
        c4.add_widget(UW.text("[b]Πηγές[/b]", size=15))
        c4.add_widget(UW.text("Κουπόνι: Sofascore (όλοι οι αγώνες ποδοσφαίρου, μπάσκετ και βόλεϊ ανά χώρα και "
                              "διοργάνωση, αποδόσεις, αρχικές αποδόσεις για την κίνηση γραμμής, ψήφοι κοινού, φόρμα, "
                              "μεταξύ τους, ιστορικό επιτυχίας ανά απόδοση, αποτελέσματα). Εφεδρικά: TheSportsDB. "
                              "Ποδόσφαιρο: football-data.co.uk (Pinnacle και μέσος όρος αγοράς) + ESPN (~45 "
                              "διοργανώσεις). Μπάσκετ: ESPN. Μοντέλο Poisson και φόρμα από τα αποτελέσματα της σεζόν.",
                              size=12, color=UW.C["muted"]))
        c4.add_widget(UW.text(COUPON_NOTE, size=12, color=UW.C["muted"]))
        c5 = self.card(box)
        c5.add_widget(UW.text("[b]Η εφαρμογή[/b]", size=15))
        c5.add_widget(UW.text(esc(UP.version_text()), size=12, color=UW.C["muted"]))
        self.ghost(c5, "ΕΛΕΓΧΟΣ ΓΙΑ ΝΕΑ ΕΚΔΟΣΗ", lambda: self.check_update(), h=42)
        box.add_widget(UW.text(FOOT, size=11, color=UW.C["muted"]))


if __name__ == "__main__":
    StoiximaApp().run()
