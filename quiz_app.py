"""Mind Arena - maths quiz game for ages 10-15 (Streamlit)."""
import html
import math
import random
import sqlite3
from datetime import datetime
from decimal import Decimal

# =====================================================================
# QUESTION ENGINE (no Streamlit needed here, so it can be tested alone)
# =====================================================================
SUP = str.maketrans("0123456789-", "⁰¹²³⁴⁵⁶⁷⁸⁹⁻")


def sup(n):
    return str(n).translate(SUP)


def mn(n):
    return str(n).replace("-", "−")


def sgn(n):
    return "+" if n >= 0 else "−"


def num(n):
    return f"{n:,}"


def money(c):
    return f"RM{c / 100:.2f}"


def rm2(v):
    return f"RM{v:.2f}"


def poly(m, c):
    mid = "" if m == 0 else f" {sgn(m)} {'' if abs(m) == 1 else abs(m)}x"
    const = "" if c == 0 else f" {sgn(c)} {abs(c)}"
    return f"x²{mid}{const}"


def build(topic, question, correct, wrong, tip, fmt=str, neg=False):
    """Make a multiple-choice question: 1 correct + 3 unique distractors."""
    opts, seen = [], {correct}
    for w in wrong:
        if w in seen:
            continue
        if not neg and isinstance(w, (int, float)) and w <= 0:
            continue
        seen.add(w)
        opts.append(w)
        if len(opts) == 3:
            break
    if isinstance(correct, (int, float)):
        step = 1
        while len(opts) < 3:
            for w in (correct + step, correct - step):
                if len(opts) < 3 and w not in seen and (neg or w > 0):
                    seen.add(w)
                    opts.append(w)
            step += 1
    if len(opts) < 3:
        return None
    choices = [fmt(correct)] + [fmt(w) for w in opts[:3]]
    if len(set(choices)) < 4:
        return None
    random.shuffle(choices)
    return dict(topic=topic, question=question, correct=fmt(correct),
                options=choices, tip=tip)


# ----------------------------- Primary 4 -----------------------------
def p4_add(d):
    lo, hi = 1000 * d, 3000 * d + 2000
    a, b = random.randint(lo, hi), random.randint(lo, hi)
    if random.random() < 0.5:
        ans, q = a + b, f"{num(a)} + {num(b)} = ?"
        tip = "Add column by column from the ones, carrying when you reach 10."
    else:
        a, b = max(a, b), min(a, b)
        ans, q = a - b, f"{num(a)} − {num(b)} = ?"
        tip = "Subtract column by column, borrowing when you need to."
    wrong = [ans + 10, ans - 10, ans + 100, ans - 100, ans + 1000, ans - 1000]
    return build("Add and subtract", q, ans, wrong, tip, num)


def p4_mult(d):
    n = random.choice([6, 8, 12, 15, 24])
    k = random.randint(8 + 2 * d, 14 + 5 * d)
    item = random.choice(["pencils", "stickers", "marbles", "cards"])
    ans = n * k
    q = f"A box holds {n} {item}. How many {item} are in {k} boxes?"
    wrong = [ans + n, ans - n, ans + 10, ans - 10, n + k, ans + k]
    return build("Multiplication", q, ans, wrong, f"Multiply {n} × {k}.", num)


def p4_fraction(d):
    den = random.choice([2, 3, 4, 5, 6, 8, 10])
    n = random.randint(1, den - 1)
    m = random.randint(2, 5 + 2 * d)
    total = den * m
    ans = n * m
    q = f"What is {n}/{den} of {total} sweets?"
    tip = f"Divide {total} by {den} to get {m}, then multiply by {n}."
    wrong = [m, (den - n) * m, ans + den, ans + m, total - m, ans - den]
    return build("Fractions", q, ans, wrong, tip)


def p4_money(d):
    a = random.randrange(150, 1000, 5)
    b = random.randrange(100, 600, 5)
    change = 2000 - (a + b)
    q = (f"A book costs {money(a)} and a pen costs {money(b)}. "
         f"You pay RM20.00. How much change do you get?")
    tip = "Add the two prices first, then subtract the total from RM20.00."
    wrong = [change + 50, change - 50, change + 100, change - 100, change + 10, a + b]
    return build("Money", q, change, wrong, tip, money)


def clock(t):
    hh, mm = (t // 60) % 24, t % 60
    return f"{hh % 12 or 12}:{mm:02d} {'am' if hh < 12 else 'pm'}"


def p4_time(d):
    start = random.randrange(9 * 60, 14 * 60, 5)
    h = random.randint(1, 2 + (d > 1))
    m = random.choice(range(5, 60, 5))
    end = start + h * 60 + m
    hs = "hour" if h == 1 else "hours"
    q = f"A movie starts at {clock(start)} and lasts {h} {hs} {m} minutes. When does it end?"
    tip = "Add the hours first, then the minutes. Watch out when minutes pass 60."
    wrong = [end + 10, end - 10, end + 60, end - 60, end + 20, end - 20]
    return build("Time", q, end, wrong, tip, clock)


# ----------------------------- Primary 5 -----------------------------
def p5_decimal(d):
    a, b = random.randint(150, 1200 * d), random.randint(100, 900 * d)
    if random.random() < 0.5:
        ans, q = a + b, f"{a / 100:.2f} + {b / 100:.2f} = ?"
        tip = "Line up the decimal points, then add."
    else:
        a, b = max(a, b) + 1, min(a, b)
        ans, q = a - b, f"{a / 100:.2f} − {b / 100:.2f} = ?"
        tip = "Line up the decimal points, then subtract."
    wrong = [ans + 10, ans - 10, ans + 100, ans - 100, ans + 1, ans - 1]
    return build("Decimals", q, ans, wrong, tip, lambda c: f"{c / 100:.2f}")


def p5_percent(d):
    p = random.choice([10, 20, 25, 30, 40, 50, 60, 75])
    total = random.choice([40, 60, 80, 120, 160, 200, 240, 300, 400])
    ans = total * p // 100
    q = f"What is {p}% of {total}?"
    tip = f"{p}% means {p} out of 100. Work out {total} ÷ 100 × {p}."
    wrong = [total - ans, ans + 5, ans + 10, ans - 5, ans * 2, p + total // 10]
    return build("Percentage", q, ans, wrong, tip)


def p5_bodmas(d):
    a = random.randint(2, 9 + 3 * d)
    b, c = random.randint(2, 9), random.randint(2, 9)
    e = random.randint(1, a)
    ans = a + b * c - e
    q = f"{a} + {b} × {c} − {e} = ?"
    tip = "Multiply first, then add and subtract from left to right."
    wrong = [(a + b) * c - e, a + b * c + e, a + b + c - e, ans + 10, ans - 10, ans + 2]
    return build("Order of operations", q, ans, wrong, tip)


def p5_average(d):
    nums = [random.randint(10, 40 * d + 30) for _ in range(4)]
    base = random.randint(10, 70)
    fifth = base + ((-(sum(nums) + base)) % 5)
    nums.append(fifth)
    total = sum(nums)
    ans = total // 5
    q = f"Find the average of these 5 numbers: {', '.join(map(str, nums))}"
    tip = "Add all the numbers, then divide by how many there are (5)."
    wrong = [ans + 1, ans - 1, ans + 5, ans - 5, total, total // 4]
    return build("Average", q, ans, wrong, tip)


# ----------------------------- Primary 6 -----------------------------
def p6_ratio(d):
    a, b = random.choice([(2, 3), (3, 5), (1, 4), (2, 5), (3, 4), (4, 5), (3, 7)])
    u = random.choice([4, 5, 10, 12]) * random.randint(1, 3 * d)
    total = (a + b) * u
    ans = a * u
    q = f"Aina and Ben share RM{total:,} in the ratio {a}:{b}. How much does Aina get?"
    tip = f"Total parts = {a} + {b} = {a + b}. One part = {total:,} ÷ {a + b} = {u}."
    wrong = [b * u, total, ans + u, ans - u, a + b, ans * 2]
    return build("Ratio", q, ans, wrong, tip, lambda v: f"RM{v:,}")


def p6_speed(d):
    s = random.choice([40, 48, 60, 72, 80, 90])
    t = random.choice([1.5, 2, 2.5, 3, 3.5, 4])
    ans = int(s * t)
    q = f"A car travels at {s} km/h for {t:g} hours. How far does it travel?"
    wrong = [ans + s, ans - s, ans + 10, ans - 10, int(s / t), s + int(t)]
    return build("Speed and distance", q, ans, wrong,
                 "Distance = speed × time.", lambda v: f"{v} km")


def p6_discount(d):
    price = random.choice([40, 60, 80, 120, 150, 200, 250])
    disc = random.choice([10, 20, 25, 30, 40, 50])
    off = price * disc / 100
    sale = price - off
    q = f"A bag costs RM{price}. It is on sale with {disc}% off. What is the sale price?"
    tip = f"{disc}% of RM{price} is RM{off:g}. Subtract that from RM{price}."
    wrong = [off, price + off, sale + 10, sale - 10, price - disc, sale + 5]
    return build("Discount", q, sale, wrong, tip, rm2)


def p6_volume(d):
    l, w, h = (random.randint(3, 6 + 2 * d), random.randint(2, 5 + d),
               random.randint(2, 6 + d))
    ans = l * w * h
    q = f"A cuboid is {l} cm long, {w} cm wide and {h} cm high. What is its volume?"
    wrong = [2 * (l * w + l * h + w * h), l + w + h, l * w + h, ans + l * w, ans - w * h]
    return build("Volume", q, ans, wrong, "Volume = length × width × height.",
                 lambda v: f"{v} cm³")


# ----------------------------- Form 1 -----------------------------
def f1_integers(d):
    a, b, c = (random.randint(2, 9 + 3 * d) for _ in range(3))
    ans = -a + b + c
    q = f"−{a} + {b} − (−{c}) = ?"
    tip = "Subtracting a negative is the same as adding a positive."
    wrong = [-a + b - c, a + b + c, -a - b + c, a - b + c, ans + 2, ans - 2]
    return build("Integers", q, ans, wrong, tip, mn, neg=True)


def f1_equation(d):
    x = random.choice([n for n in range(-6, 10) if n != 0])
    a = random.randint(2, 9)
    b = random.choice([n for n in range(-9, 10) if n != 0])
    c = a * x + b
    q = f"Solve {a}x {sgn(b)} {abs(b)} = {mn(c)}"
    tip = f"Undo the {sgn(b)} {abs(b)} first, then divide both sides by {a}."
    wrong = [-x, x + 1, x - 1, c // a, (c + b) // a, x + 2]
    return build("Linear equations", q, x, wrong, tip, mn, neg=True)


def f1_hcf_lcm(d):
    g = random.choice(range(2, 5 + 2 * d))
    p, r = random.sample([2, 3, 4, 5, 6, 7], 2)
    a, b = g * p, g * r
    h = math.gcd(a, b)
    l = a * b // h
    if random.random() < 0.5:
        q = f"What is the highest common factor (HCF) of {a} and {b}?"
        tip = f"List the factors of {a} and {b}. The biggest one they share is the HCF."
        return build("HCF", q, h, [l, min(a, b), h * 2, h + 1, h - 1, a - b], tip)
    q = f"What is the lowest common multiple (LCM) of {a} and {b}?"
    tip = "List the multiples of both numbers. The smallest one they share is the LCM."
    return build("LCM", q, l, [a * b, max(a, b), l * 2, l + g, l - g, h], tip)


def f1_roots(d):
    r = random.randint(4, 12 + 2 * d)
    s = random.randint(2, 9)
    ans = r + s * s
    q = f"What is √{r * r} + {s}²?"
    tip = f"√{r * r} = {r} and {s}² = {s * s}."
    wrong = [r * r + s, r + 2 * s, r * r + s * s, ans + r, ans - 1, ans + 1]
    return build("Squares and roots", q, ans, wrong, tip)


# ----------------------------- Form 2 -----------------------------
TRIPLES = [(3, 4, 5), (6, 8, 10), (5, 12, 13), (9, 12, 15), (8, 15, 17),
           (12, 16, 20), (7, 24, 25), (20, 21, 29)]


def f2_pythag(d):
    a, b, c = random.choice(TRIPLES[: 4 + 2 * d])
    q = (f"A right-angled triangle has two shorter sides of {a} cm and {b} cm. "
         f"How long is the hypotenuse?")
    tip = f"c² = {a}² + {b}² = {a * a + b * b}. Then take the square root."
    wrong = [a + b, c + 1, c - 1, c + 2, c - 2, abs(b - a)]
    return build("Pythagoras", q, c, wrong, tip, lambda v: f"{v} cm")


def pw(k):
    return "x" if k == 1 else f"x{sup(k)}"


def f2_indices(d):
    a, b = random.randint(3, 9), random.randint(2, 6)
    c = random.randint(1, min(4, a + b - 2))
    n = a + b - c
    q = f"Simplify x{sup(a)} × x{sup(b)} ÷ x{sup(c)}"
    tip = "When multiplying, add the powers. When dividing, subtract them."
    wrong = [pw(k) for k in (a * b - c, a + b + c, a + b, n + 1, n - 1, a - b + c) if k > 0]
    return build("Indices", q, pw(n), wrong, tip)


def f2_circle(d):
    k = random.randint(1, 3)
    r = 7 * k
    ans = 154 * k * k
    q = f"Find the area of a circle with radius {r} cm. (Use π = 22/7)"
    tip = f"Area = π × r² = 22/7 × {r} × {r}."
    wrong = [44 * k, 154 * k, 77 * k * k, 308 * k * k, ans + 22, ans - 22]
    return build("Circles", q, ans, wrong, tip, lambda v: f"{v} cm²")


def f2_profit(d):
    cost = random.choice([40, 50, 80, 100, 120, 200, 250])
    pct = random.choice([10, 20, 25, 30, 40, 50])
    sell = cost * (100 + pct) / 100
    q = f"A shop buys a watch for RM{cost} and wants a {pct}% profit. What is the selling price?"
    tip = f"Profit = {pct}% of RM{cost} = RM{cost * pct / 100:g}. Add it to the cost."
    wrong = [cost * pct / 100, cost + pct, sell + 10, sell - 10, cost * (100 - pct) / 100, sell + 5]
    return build("Profit", q, sell, wrong, tip, rm2)


# ----------------------------- Form 3 -----------------------------
def f3_expand(d):
    a, b = random.sample(range(1, 7 + d), 2)
    q = f"Expand and simplify (x + {a})(x − {b})"
    tip = "Multiply every term in the first bracket by every term in the second, then collect like terms."
    wrong = [poly(a + b, -a * b), poly(a - b, a * b), poly(b - a, -a * b),
             poly(a + b, a * b), poly(a - b, -(a + b))]
    return build("Expansion", q, poly(a - b, -a * b), wrong, tip)


def roots_str(t):
    lo, hi = sorted(t)
    return f"x = {mn(lo)} or x = {mn(hi)}"


def f3_quadratic(d):
    r1, r2 = random.sample([n for n in range(-7, 8) if n != 0], 2)
    s, p = r1 + r2, r1 * r2
    q = f"Solve {poly(-s, p)} = 0"
    tip = (f"Find two numbers that multiply to {mn(p)} and add to {mn(-s)}. "
           f"Those give the brackets, so flip their signs to get x.")
    cands = [(-r1, -r2), (r1, -r2), (-r1, r2), (r1 + 1, r2), (r1, r2 - 1), (r1 + 1, r2 + 1)]
    return build("Quadratics", q, roots_str((r1, r2)), [roots_str(c) for c in cands], tip)


def f3_standard(d):
    m = random.choice([1.2, 2.5, 3.6, 4.5, 5.8, 6.4, 7.2, 8.9, 9.1])
    k = random.randint(3, 5 + d)
    val = format(Decimal(str(m)) * Decimal(10) ** (-k), "f")
    ans = f"{m} × 10{sup(-k)}"
    wrong = [f"{m} × 10{sup(-(k - 1))}", f"{m} × 10{sup(-(k + 1))}", f"{m} × 10{sup(k)}",
             f"{m * 10:g} × 10{sup(-(k + 1))}", f"{m / 10:g} × 10{sup(-(k - 1))}"]
    tip = "Standard form is A × 10ⁿ with 1 ≤ A < 10. Count how many places the decimal point moves."
    return build("Standard form", f"Write {val} in standard form", ans, wrong, tip)


def f3_gradient(d):
    m = random.choice([-4, -3, -2, -1, 2, 3, 4, 5])
    dx = random.randint(1, 4)
    x1, y1 = random.randint(-3, 4), random.randint(-4, 6)
    x2, y2 = x1 + dx, y1 + m * dx
    q = f"Find the gradient of the line through ({mn(x1)}, {mn(y1)}) and ({mn(x2)}, {mn(y2)})"
    tip = "Gradient = (y₂ − y₁) ÷ (x₂ − x₁)."
    wrong = [-m, m + 1, m - 1, y2 - y1, dx, m + 2]
    return build("Straight lines", q, m, wrong, tip, mn, neg=True)


def f3_trig(d):
    h = random.choice([8, 10, 12, 14, 16, 20, 24])
    ans = h // 2
    q = (f"In a right-angled triangle the hypotenuse is {h} cm and one angle is 30°. "
         f"How long is the side opposite that angle?")
    tip = "sin 30° = 1/2, so the opposite side = hypotenuse × 1/2."
    wrong = [h, h * 2, h // 4, ans + 2, ans - 2, int(h * 0.866)]
    return build("Trigonometry", q, ans, wrong, tip, lambda v: f"{v} cm")


LEVELS = [("P4", "Primary 4"), ("P5", "Primary 5"), ("P6", "Primary 6"),
          ("F1", "Form 1"), ("F2", "Form 2"), ("F3", "Form 3")]
GENS = {
    "P4": [p4_add, p4_mult, p4_fraction, p4_money, p4_time],
    "P5": [p5_decimal, p5_percent, p5_bodmas, p5_average],
    "P6": [p6_ratio, p6_speed, p6_discount, p6_volume],
    "F1": [f1_integers, f1_equation, f1_hcf_lcm, f1_roots],
    "F2": [f2_pythag, f2_indices, f2_circle, f2_profit],
    "F3": [f3_expand, f3_quadratic, f3_standard, f3_gradient, f3_trig],
}

# =====================================================================
# UI
# =====================================================================
import streamlit as st  # noqa: E402

st.set_page_config(page_title="Mind Arena", page_icon="🧠", layout="centered")

DB_PATH = "leaderboard.db"
AGES = list(range(10, 16))
LENGTHS = {10: "10 · Sprint", 20: "20 · Raid", 30: "30 · Boss run"}

CSS = """<style>
.stApp{background:#0B0D22}
.block-container{max-width:720px;padding-top:2rem}
.hero{display:flex;align-items:center;gap:14px;margin-bottom:10px}
.title{font-size:32px;font-weight:700;color:#EAF0FF;margin:0;line-height:1.1}
.sub{color:#22E3FF;font-size:15px;margin:4px 0 0}
.muted{color:#9AA6D6;font-size:13px}
.hud{display:flex;justify-content:space-between;color:#9AA6D6;font-size:14px;font-weight:600;margin-bottom:6px}
.combo{color:#FFE45E}
.bar{height:10px;background:#1A1F44;border-radius:99px;margin:6px 0 14px}
.bar>div{height:10px;background:#22E3FF;border-radius:99px;transition:width .4s}
.qrow{display:flex;gap:14px;align-items:flex-start;margin:6px 0 14px}
.bubble{background:#1A1F44;border:2px solid #8B5CFF;border-radius:6px 18px 18px 18px;padding:12px 16px;flex:1}
.tag{font-size:12px;color:#8B5CFF;font-weight:700;letter-spacing:.5px}
.bubble p{font-size:20px;font-weight:600;color:#EAF0FF;margin:6px 0 0}
.stButton>button{background:#1A1F44;color:#EAF0FF;border:2px solid #343C86;border-radius:12px;padding:.6rem 1rem;justify-content:flex-start}
.stButton>button p{font-size:17px;text-align:left}
.stButton>button:hover{border-color:#22E3FF;color:#22E3FF}
.stButton>button[kind="primary"],.stButton>button[data-testid="stBaseButton-primary"]{background:#B6FF3B;color:#0B0D22;border-color:#B6FF3B;justify-content:center}
.stButton>button[kind="primary"] p,.stButton>button[data-testid="stBaseButton-primary"] p{font-weight:700;text-align:center;color:#0B0D22}
.rx{display:flex;gap:16px;align-items:center;border-radius:16px;padding:14px;margin:8px 0 14px}
.rx.ok{background:#12361F;border:2px solid #B6FF3B}
.rx.bad{background:#3A1030;border:2px solid #FF2E93}
.rt{font-size:26px;font-weight:700;margin:0}
.rx.ok .rt{color:#B6FF3B}
.rx.bad .rt{color:#FF2E93}
.rx p{color:#EAF0FF;margin:4px 0 0;font-size:15px}
.rx .tip{color:#9AA6D6;font-size:14px}
.lrow{display:flex;align-items:center;gap:12px;background:#1A1F44;color:#EAF0FF;border-radius:10px;padding:9px 12px;margin:5px 0;border:2px solid transparent}
.lrow .nm{flex:1}
.lrow small{color:#9AA6D6}
.lrow.g1{border-color:#FFE45E}.lrow.g1 .xp,.lrow.g1 b:first-child{color:#FFE45E}
.lrow.me{border-color:#22E3FF;background:#10304A}
@keyframes bounce{0%,100%{transform:translateY(0)}50%{transform:translateY(-12px)}}
@keyframes shake{0%,100%{transform:translateX(0)}20%{transform:translateX(-9px)}40%{transform:translateX(9px)}60%{transform:translateX(-6px)}80%{transform:translateX(6px)}}
@keyframes float{0%,100%{transform:translateY(0)}50%{transform:translateY(-4px)}}
.ren{flex:none}
.ren.idle{animation:float 3s ease-in-out infinite}
.ren.happy{animation:bounce .8s ease-in-out 3}
.ren.sad{animation:shake .6s ease 1}
</style>"""

# ---- Ren, the original anime-style mascot (inline SVG) ----
REN_BASE = (
    '<path d="M20 70 L14 30 L36 44 L44 12 L62 38 L86 10 L90 44 L108 28 L100 70 Z" fill="#243282" stroke="#0B0D22" stroke-width="3" stroke-linejoin="round"/>'
    '<path d="M60 22 Q96 22 94 62 Q92 100 60 106 Q28 100 26 62 Q24 22 60 22 Z" fill="#FFD9BF" stroke="#0B0D22" stroke-width="3"/>'
    '<path d="M24 64 Q20 20 62 18 Q104 20 98 62 L88 42 L76 58 L64 32 L52 56 L40 36 L32 60 Z" fill="#2E3FA0" stroke="#0B0D22" stroke-width="3" stroke-linejoin="round"/>'
    '<path d="M64 32 L76 58 L71 59 L60 38 Z" fill="#22E3FF"/>'
    '<path d="M26 66 Q24 16 60 14 Q96 16 94 66" stroke="#FF2E93" stroke-width="6" fill="none"/>'
    '<rect x="16" y="56" width="13" height="26" rx="5" fill="#FF2E93" stroke="#0B0D22" stroke-width="2.5"/>'
    '<rect x="91" y="56" width="13" height="26" rx="5" fill="#FF2E93" stroke="#0B0D22" stroke-width="2.5"/>'
)
REN_HAPPY = (
    '<ellipse cx="46" cy="72" rx="8.5" ry="11" fill="#fff" stroke="#0B0D22" stroke-width="2.5"/>'
    '<ellipse cx="74" cy="72" rx="8.5" ry="11" fill="#fff" stroke="#0B0D22" stroke-width="2.5"/>'
    '<ellipse cx="46" cy="73" rx="6.5" ry="9" fill="#22E3FF"/><ellipse cx="74" cy="73" rx="6.5" ry="9" fill="#22E3FF"/>'
    '<ellipse cx="46" cy="74" rx="3.5" ry="5.5" fill="#0B0D22"/><ellipse cx="74" cy="74" rx="3.5" ry="5.5" fill="#0B0D22"/>'
    '<circle cx="43" cy="69" r="3" fill="#fff"/><circle cx="71" cy="69" r="3" fill="#fff"/>'
    '<path d="M36 60 L54 62 M84 60 L66 62" stroke="#0B0D22" stroke-width="3" stroke-linecap="round"/>'
    '<path d="M48 90 Q60 104 74 90 Z" fill="#7A1038" stroke="#0B0D22" stroke-width="2.5" stroke-linejoin="round"/>'
    '<path d="M104 22 L106 29 L113 31 L106 33 L104 40 L102 33 L95 31 L102 29 Z" fill="#FFE45E"/>'
    '<ellipse cx="36" cy="86" rx="5" ry="3" fill="#FF7AA8" opacity=".8"/><ellipse cx="84" cy="86" rx="5" ry="3" fill="#FF7AA8" opacity=".8"/>'
)
REN_SAD = (
    '<ellipse cx="46" cy="76" rx="8.5" ry="10" fill="#fff" stroke="#0B0D22" stroke-width="2.5"/>'
    '<ellipse cx="74" cy="76" rx="8.5" ry="10" fill="#fff" stroke="#0B0D22" stroke-width="2.5"/>'
    '<ellipse cx="46" cy="78" rx="6.5" ry="8" fill="#22E3FF"/><ellipse cx="74" cy="78" rx="6.5" ry="8" fill="#22E3FF"/>'
    '<ellipse cx="46" cy="79" rx="3" ry="4.5" fill="#0B0D22"/><ellipse cx="74" cy="79" rx="3" ry="4.5" fill="#0B0D22"/>'
    '<ellipse cx="46" cy="83" rx="6" ry="2.5" fill="#BFEFFF" opacity=".85"/><ellipse cx="74" cy="83" rx="6" ry="2.5" fill="#BFEFFF" opacity=".85"/>'
    '<circle cx="43" cy="74" r="2.5" fill="#fff"/><circle cx="71" cy="74" r="2.5" fill="#fff"/>'
    '<path d="M36 66 L54 61 M84 66 L66 61" stroke="#0B0D22" stroke-width="3" stroke-linecap="round"/>'
    '<path d="M50 98 Q55 92 60 98 Q65 104 70 98" stroke="#0B0D22" stroke-width="3" fill="none" stroke-linecap="round"/>'
    '<path d="M98 48 Q104 60 98 68 Q92 60 98 48 Z" fill="#8FDBFF" stroke="#0B0D22" stroke-width="1.5"/>'
    '<path d="M44 30 L44 44 M60 28 L60 44 M76 30 L76 44" stroke="#8B5CFF" stroke-width="3" stroke-linecap="round"/>'
)


def ren(mood="idle", size=84):
    face = REN_SAD if mood == "sad" else REN_HAPPY
    return (f'<svg class="ren {mood}" width="{size}" height="{size}" viewBox="0 0 120 120" '
            f'xmlns="http://www.w3.org/2000/svg">{REN_BASE}{face}</svg>')


def md(s):
    st.markdown(s, unsafe_allow_html=True)


# ---- leaderboard storage (SQLite) ----
def db():
    con = sqlite3.connect(DB_PATH)
    con.execute("CREATE TABLE IF NOT EXISTS scores (id INTEGER PRIMARY KEY AUTOINCREMENT, "
                "name TEXT, age INTEGER, levels TEXT, total INTEGER, correct INTEGER, "
                "xp INTEGER, ts TEXT)")
    return con


def save_score(name, age, levels, total, correct, xp):
    con = db()
    con.execute("INSERT INTO scores (name, age, levels, total, correct, xp, ts) VALUES (?,?,?,?,?,?,?)",
                (name, age, ",".join(levels), total, correct, xp,
                 datetime.now().isoformat(timespec="seconds")))
    con.commit()
    con.close()


def top_scores(age, limit=10):
    con = db()
    rows = con.execute("SELECT name, levels, xp, total FROM scores WHERE age=? "
                       "ORDER BY xp DESC, ts ASC LIMIT ?", (age, limit)).fetchall()
    con.close()
    return rows


def rank_of(age, xp):
    con = db()
    n = con.execute("SELECT COUNT(*) FROM scores WHERE age=? AND xp>?", (age, xp)).fetchone()[0]
    con.close()
    return n + 1


def board_html(age, me=None):
    rows = top_scores(age)
    if not rows:
        return '<p class="muted">No scores yet for this age. Be the first!</p>'
    out = []
    for i, (name, levels, xp, total) in enumerate(rows, 1):
        cls = "lrow" + (" g1" if i == 1 else "")
        if me and name == me[0] and xp == me[1]:
            cls += " me"
        out.append(f'<div class="{cls}"><b>{i}</b><span class="nm">{html.escape(name)} '
                   f'<small>· {html.escape(levels)} · {total}Q</small></span>'
                   f'<b class="xp">{xp} XP</b></div>')
    return "".join(out)


# ---- game state ----
def init_state():
    defaults = dict(stage="start", name="", age=12, levels=[], total=10, qi=0, xp=0,
                    combo=0, best=0, correct=0, difficulty=1, right_streak=0,
                    wrong_streak=0, asked=set(), q=None, last=None, saved=False, rank=None)
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def new_question():
    s = st.session_state
    q = None
    for _ in range(30):
        level = random.choice(s.levels)
        q = random.choice(GENS[level])(s.difficulty)
        if q:
            q["level"] = level
            if q["question"] not in s.asked:
                break
    s.asked.add(q["question"])
    return q


def reset_run():
    s = st.session_state
    s.update(qi=0, xp=0, combo=0, best=0, correct=0, difficulty=1, right_streak=0,
             wrong_streak=0, asked=set(), last=None, saved=False, rank=None)
    s.q = new_question()
    s.stage = "question"


def answer(choice):
    s = st.session_state
    ok = choice == s.q["correct"]
    gain = 0
    if ok:
        s.combo += 1
        s.best = max(s.best, s.combo)
        s.correct += 1
        gain = 10 + 5 * min(s.combo - 1, 4) + 3 * (s.difficulty - 1)
        s.xp += gain
        s.right_streak += 1
        s.wrong_streak = 0
        if s.right_streak >= 3 and s.difficulty < 3:
            s.difficulty += 1
            s.right_streak = 0
        title = random.choice(["Perfect!", "Nailed it!", "Big brain!", "Yatta!"])
    else:
        s.combo = 0
        s.wrong_streak += 1
        s.right_streak = 0
        if s.wrong_streak >= 2 and s.difficulty > 1:
            s.difficulty -= 1
            s.wrong_streak = 0
        title = random.choice(["Glitch! Not quite", "Oof, so close", "Eeeh?! Not this time"])
    s.last = dict(ok=ok, choice=choice, gain=gain, title=title)
    s.stage = "feedback"


def next_q():
    s = st.session_state
    s.qi += 1
    if s.qi >= s.total:
        s.stage = "result"
    else:
        s.q = new_question()
        s.stage = "question"


def to_start():
    st.session_state.stage = "start"


def hud():
    s = st.session_state
    done = s.qi + (1 if s.stage == "feedback" else 0)
    pct = int(done / s.total * 100)
    md(f'<div class="hud"><span>Q {s.qi + 1} / {s.total}</span>'
       f'<span class="combo">⚡ Combo x{s.combo}</span>'
       f'<span>{s.xp} XP · Power {s.difficulty}</span></div>'
       f'<div class="bar"><div style="width:{pct}%"></div></div>')


# ---- screens ----
def screen_start():
    md(f'<div class="hero">{ren("idle", 84)}<div><p class="title">Mind arena</p>'
       f'<p class="sub">Beat the quiz. Climb the ranks.</p></div></div>')
    name = st.text_input("Player name", max_chars=20, placeholder="Nickname or first name only")
    st.caption("Please don't use your full name. Scores show name, age and level.")
    age = st.radio("Age", AGES, index=2, horizontal=True)
    st.write("Level (tick any)")
    picked = []
    cols = st.columns(3)
    for i, (code, label) in enumerate(LEVELS):
        if cols[i % 3].checkbox(label, key=f"lv_{code}"):
            picked.append(code)
    total = st.radio("Quiz length", list(LENGTHS), format_func=LENGTHS.get, horizontal=True)
    if st.button("Enter arena", type="primary", use_container_width=True):
        if not name.strip():
            st.error("Enter a player name first.")
        elif not picked:
            st.error("Tick at least one level.")
        else:
            st.session_state.update(name=name.strip(), age=age, levels=picked, total=total)
            reset_run()
            st.rerun()
    with st.expander("Leaderboard"):
        tabs = st.tabs([f"Age {a}" for a in AGES])
        for tab, a in zip(tabs, AGES):
            with tab:
                md(board_html(a))


def screen_question():
    s = st.session_state
    q = s.q
    hud()
    md(f'<div class="qrow">{ren("idle", 72)}<div class="bubble">'
       f'<span class="tag">MATHS · {html.escape(q["level"])} · {html.escape(q["topic"].upper())}</span>'
       f'<p>{html.escape(q["question"])}</p></div></div>')
    for i, opt in enumerate(q["options"]):
        st.button(f"{'ABCD'[i]}   {opt}", key=f"opt{s.qi}_{i}", use_container_width=True,
                  on_click=answer, args=(opt,))


def screen_feedback():
    s = st.session_state
    q, last = s.q, s.last
    hud()
    if last["ok"]:
        body = (f'<p>+{last["gain"]} XP · combo x{s.combo}</p>'
                f'<p class="tip">Tip: {html.escape(q["tip"])}</p>')
        md(f'<div class="rx ok">{ren("happy", 96)}<div><p class="rt">{last["title"]}</p>{body}</div></div>')
    else:
        body = (f'<p>You picked {html.escape(last["choice"])}. The answer is '
                f'<b>{html.escape(q["correct"])}</b>. Combo reset, shake it off.</p>'
                f'<p class="tip">Tip: {html.escape(q["tip"])}</p>')
        md(f'<div class="rx bad">{ren("sad", 96)}<div><p class="rt">{last["title"]}</p>{body}</div></div>')
    label = "See results" if s.qi + 1 >= s.total else "Next question"
    st.button(label, type="primary", use_container_width=True, on_click=next_q)


def rank_title(acc):
    return ("Legend" if acc >= 0.9 else "Champion" if acc >= 0.75
            else "Challenger" if acc >= 0.5 else "Rookie")


def screen_result():
    s = st.session_state
    acc = s.correct / s.total
    if not s.saved:
        save_score(s.name, s.age, s.levels, s.total, s.correct, s.xp)
        s.rank = rank_of(s.age, s.xp)
        s.saved = True
        if acc >= 0.75:
            st.balloons()
    mood = "happy" if acc >= 0.5 else "sad"
    md(f'<div class="hero">{ren(mood, 96)}<div><p class="title">{rank_title(acc)}!</p>'
       f'<p class="sub">{html.escape(s.name)} · age {s.age} · rank #{s.rank} in age {s.age}</p></div></div>')
    c1, c2, c3 = st.columns(3)
    c1.metric("XP", s.xp)
    c2.metric("Correct", f"{s.correct} / {s.total}")
    c3.metric("Best combo", f"x{s.best}")
    st.write(f"Leaderboard · age {s.age}")
    md(board_html(s.age, me=(s.name, s.xp)))
    b1, b2 = st.columns(2)
    b1.button("Play again", type="primary", use_container_width=True, on_click=reset_run)
    b2.button("Change settings", use_container_width=True, on_click=to_start)


init_state()
md(CSS)
{"start": screen_start, "question": screen_question,
 "feedback": screen_feedback, "result": screen_result}[st.session_state.stage]()
