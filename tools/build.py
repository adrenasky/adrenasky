"""Builds the public subject pages for adrenasky.com (one static HTML file per subject)."""
import json, html, sys, os

OUT = sys.argv[1]
SITE = "https://www.adrenasky.com"
E = html.escape

SUBJECTS = json.load(open(os.path.join(os.path.dirname(__file__), "subjects.json")))

def shuffle(q, i):
    """Move the correct option to a varied position so it isn't always A."""
    opts = list(q["o"]); right = opts.pop(q["a"])
    pos = (i * 3 + 1) % 4
    opts.insert(pos, right)
    return opts, pos

CSS = """
:root{
  --bg:#0B1622; --surface:#13233A; --ink:#EAF1F7; --muted:#A9BCCB; --amber:#F2B33D; --cyan:#6FC3DF;
  --line:#22385A; --ok:#5BC489; --bad:#F2796F; --okbg:#173327; --badbg:#3A1E1D;
  --f-display:"Bricolage Grotesque","Arial Black",system-ui,sans-serif;
  --f-body:"Atkinson Hyperlegible",system-ui,-apple-system,"Segoe UI",sans-serif;
  --f-label:"Barlow Condensed","Arial Narrow",system-ui,sans-serif;
  color-scheme:dark;
}
*,*::before,*::after{box-sizing:border-box}
html{padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}
body{margin:0;background:var(--bg);color:var(--ink);font:400 17px/1.55 var(--f-body);-webkit-font-smoothing:antialiased;
  padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px));padding-block:0 48px}
.wrap{max-width:760px;margin:0 auto;display:flex;flex-direction:column;gap:48px}
h1,h2{font-family:var(--f-display);font-weight:800;text-transform:uppercase;letter-spacing:.01em;text-wrap:balance;margin:0;line-height:1}
h1{font-size:clamp(2.2rem,7vw,3.6rem)} h1 span{color:var(--amber)}
h2{font-size:clamp(1.5rem,4vw,2rem)}
p{margin:0}
a{color:var(--amber)}
.label{font:600 .85rem/1 var(--f-label);letter-spacing:.12em;text-transform:uppercase;color:var(--cyan)}
header.top{display:flex;justify-content:space-between;align-items:center;gap:12px;padding-block:20px 0}
.brand{font:800 1.5rem var(--f-display);letter-spacing:.04em;text-transform:uppercase;color:var(--ink);text-decoration:none}
.btn{display:inline-flex;align-items:center;justify-content:center;font:700 1rem var(--f-body);border-radius:12px;padding:13px 22px;text-decoration:none;border:2px solid var(--amber);cursor:pointer}
.btn.primary{background:var(--amber);color:var(--bg)}
.btn.ghost{background:transparent;color:var(--ink);border-color:var(--ink)}
.btn:focus-visible,.opt:focus-visible,summary:focus-visible,a:focus-visible{outline:3px solid var(--cyan);outline-offset:2px}
.hero{display:flex;flex-direction:column;gap:18px}
.lead{font-size:1.12rem;color:var(--muted);max-width:62ch}
.facts{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:10px;font-variant-numeric:tabular-nums}
.facts div{border:1px solid var(--line);border-radius:12px;padding:14px 16px;display:flex;flex-direction:column}
.facts b{font:800 1.9rem var(--f-display);color:var(--amber)}
.facts span{font-size:.9rem;color:var(--muted)}
.cta-row{display:flex;flex-wrap:wrap;gap:12px}
.chapters{display:flex;flex-direction:column;gap:14px}
.chips{display:flex;flex-wrap:wrap;gap:8px;margin:0;padding:0;list-style:none}
.chips li{font-size:.92rem;border:1px solid var(--line);border-radius:999px;padding:5px 12px;color:var(--muted)}
.chips li.hot{border-color:var(--amber);color:var(--amber);font-weight:700}
.hint{color:var(--muted);font-size:.95rem}
.qs{display:flex;flex-direction:column;gap:16px}
.qhead{display:flex;justify-content:space-between;align-items:flex-end;gap:12px;flex-wrap:wrap}
.qhead>div{display:flex;flex-direction:column;gap:8px}
.score{font:600 1rem var(--f-label);letter-spacing:.05em;color:var(--muted);font-variant-numeric:tabular-nums}
.q{background:var(--surface);border:1px solid var(--line);border-radius:14px;padding:20px;display:flex;flex-direction:column;gap:12px;min-width:0}
.q .meta{font:600 .82rem var(--f-label);letter-spacing:.1em;text-transform:uppercase;color:var(--cyan)}
.q .stem{font-weight:700}
.opts{display:flex;flex-direction:column;gap:8px}
.opt{text-align:left;font:400 1rem var(--f-body);color:var(--ink);background:var(--bg);border:1.5px solid var(--line);border-radius:10px;padding:10px 14px;cursor:pointer;display:flex;gap:10px}
.opt .k{font:700 1rem var(--f-label);color:var(--amber);min-width:1.1em}
.opt:hover:not(:disabled){border-color:var(--amber)}
.opt:disabled{cursor:default}
.opt.right{background:var(--okbg);border-color:var(--ok)}
.opt.wrong{background:var(--badbg);border-color:var(--bad)}
.why{font-size:.96rem;border-left:3px solid var(--ok);padding:4px 0 4px 12px;color:var(--muted)}
.why b{color:var(--ok)}
.why.no{border-color:var(--bad)} .why.no b{color:var(--bad)}
.notes{border:1px solid var(--line);border-radius:14px;padding:22px;display:flex;flex-direction:column;gap:14px}
.notes ul{margin:0;padding-left:20px;display:flex;flex-direction:column;gap:8px}
.notes li b{color:var(--amber)}
.ex{background:var(--surface);border-radius:10px;padding:14px 16px;font-variant-numeric:tabular-nums;display:flex;flex-direction:column;gap:6px}
.ex .t{font:700 .85rem var(--f-label);letter-spacing:.1em;text-transform:uppercase;color:var(--cyan)}
.locked{filter:blur(3.5px);user-select:none}
.lockmsg{font-weight:700;color:var(--amber)}
.final{border:2px solid var(--amber);border-radius:16px;padding:28px 24px;display:flex;flex-direction:column;gap:14px}
.final p{color:var(--muted)}
.final .btn{align-self:flex-start}
.faq{display:flex;flex-direction:column;gap:10px}
details{border:1px solid var(--line);border-radius:12px;padding:14px 18px}
summary{font-weight:700;cursor:pointer}
details p{margin-top:8px;color:var(--muted)}
.others{display:flex;flex-direction:column;gap:12px}
.others ul{display:flex;flex-wrap:wrap;gap:10px;list-style:none;margin:0;padding:0}
.others a{display:inline-block;border:1px solid var(--line);border-radius:10px;padding:10px 14px;color:var(--ink);text-decoration:none}
.others a:hover{border-color:var(--amber)}
footer{font-size:.9rem;color:var(--muted);text-align:center}
@media (prefers-reduced-motion:no-preference){.opt,.others a{transition:border-color .15s,background .15s}}
"""

JS = """
const Q=__Q__;
let done=0,right=0;
const list=document.getElementById("qlist"),score=document.getElementById("score"),L="ABCD";
Q.forEach((x,i)=>{
  const el=list.children[i];
  el.querySelector(".opts").addEventListener("click",ev=>{
    const b=ev.target.closest(".opt");if(!b||b.disabled)return;
    const j=+b.dataset.j,ok=j===x.a;
    el.querySelectorAll(".opt").forEach(o=>{o.disabled=true;if(+o.dataset.j===x.a)o.classList.add("right")});
    if(!ok)b.classList.add("wrong");
    const w=document.createElement("p");w.className="why"+(ok?"":" no");
    w.innerHTML="<b>"+(ok?"Correct.":"Answer: "+L[x.a]+".")+"</b> "+x.e;el.appendChild(w);
    done++;if(ok)right++;
    score.textContent=done<Q.length?right+" right · "+done+" of "+Q.length+" answered":"You scored "+right+" of "+Q.length+". __MORE__ more questions inside.";
  });
});
"""

def page(s):
    url = f"{SITE}/{s['slug']}"
    qs = []
    for i, q in enumerate(s["questions"]):
        opts, a = shuffle(q, i)
        qs.append({"c": q["c"], "q": q["q"], "o": opts, "a": a, "e": q["e"]})
    hot = {t["name"] for t in sorted(s["topics"], key=lambda t: -t["w"])[:s.get("hot", 5)]}
    faqs = s["faq"]
    ld = {"@context": "https://schema.org", "@graph": [
        {"@type": "Course", "name": s["h1_plain"], "description": s["meta"], "url": url,
         "provider": {"@type": "EducationalOrganization", "name": "Adrenasky", "url": SITE + "/"},
         "inLanguage": "en", "educationalLevel": "ATPL theory",
         "hasCourseInstance": {"@type": "CourseInstance", "courseMode": "online", "courseWorkload": "PT40H"}},
        {"@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": f[0],
            "acceptedAnswer": {"@type": "Answer", "text": f[1]}} for f in faqs]},
        {"@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Adrenasky", "item": SITE + "/"},
            {"@type": "ListItem", "position": 2, "name": s["name"], "item": url}]}]}

    facts = [(f"{s['nq']:,}", "exam-style questions"), (str(len(s["topics"])), "chapters"),
             (str(s["np"]), "note points")] + [tuple(x) for x in s.get("extra_facts", [])]
    others = [o for o in SUBJECTS if o["slug"] != s["slug"]]
    more = s["nq"] - len(qs)

    qhtml = "".join(
        f'<article class="q"><span class="meta">Question {i+1} · {E(q["c"])}</span><p class="stem">{E(q["q"])}</p>'
        f'<div class="opts">' + "".join(
            f'<button type="button" class="opt" id="q{i}o{j}" data-j="{j}"><span class="k">{"ABCD"[j]}</span><span>{E(t)}</span></button>'
            for j, t in enumerate(q["o"])) + '</div></article>'
        for i, q in enumerate(qs))
    js = JS.replace("__Q__", json.dumps([{"a": q["a"], "e": E(q["e"])} for q in qs], ensure_ascii=False)).replace("__MORE__", f"{more:,}")
    n = s["notes"]
    ex_html = lambda ex, locked=False: (
        f'<div class="ex{" locked" if locked else ""}"{" aria-hidden=\"true\"" if locked else ""}><span class="t">{E(ex["t"])}</span>'
        + "".join(f"<span>{l}</span>" for l in ex["lines"]) + "</div>")

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{E(s['title'])}</title>
<meta name="description" content="{E(s['meta'])}">
<link rel="canonical" href="{url}">
<meta name="theme-color" content="#0B1622">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Adrenasky">
<meta property="og:title" content="{E(s['title'])}">
<meta property="og:description" content="{E(s['meta'])}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{SITE}/icon-512.png">
<link rel="icon" href="/icon-192.png">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Atkinson+Hyperlegible:wght@400;700&family=Barlow+Condensed:wght@600;700&family=Bricolage+Grotesque:opsz,wght@12..96,800&display=swap" rel="stylesheet">
<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>
<style>{CSS}</style>
</head>
<body>
<div class="wrap">
  <header class="top">
    <a class="brand" href="/">Adrenasky</a>
    <a class="btn ghost" href="/">Log in</a>
  </header>

  <section class="hero">
    <span class="label">ATPL theory · {E(s['code'])} {E(s['name'])}</span>
    <h1>{s['h1']}</h1>
    <p class="lead">{E(s['lead'])}</p>
    <div class="facts">{"".join(f'<div><b>{E(a)}</b><span>{E(b)}</span></div>' for a, b in facts)}</div>
    <div class="cta-row">
      <a class="btn primary" href="/">Start your free 7-day trial</a>
      <a class="btn ghost" href="#try">Try {len(qs)} questions now</a>
    </div>
  </section>

  <section class="chapters">
    <span class="label">What's covered</span>
    <h2>All {len(s['topics'])} chapters</h2>
    <ul class="chips">{"".join(f'<li class="{"hot" if t["name"] in hot else ""}">{E(t["name"])}</li>' for t in s["topics"])}</ul>
    <p class="hint">Highlighted chapters carry the most marks in the exam.</p>
  </section>

  <section class="qs" id="try">
    <div class="qhead">
      <div><span class="label">Free sample</span><h2>Try {len(qs)} practice questions</h2></div>
      <span class="score" id="score" aria-live="polite">0 of {len(qs)} answered</span>
    </div>
    <div id="qlist" class="qs">{qhtml}</div>
  </section>

  <section class="notes">
    <span class="label">Notes preview · {E(n['chapter'])}</span>
    <h2>Notes that show the working</h2>
    <ul>{"".join(f"<li><b>{E(b)}:</b> {E(t)}</li>" for b, t in n['points'])}</ul>
    {ex_html(n['example'])}
    {ex_html(n['locked'], True)}
    <p class="lockmsg">{E(n['more'])}</p>
  </section>

  <section class="final">
    <h2>{E(s['final'])}</h2>
    <p>Try any one subject free for 7 days. Practise on your phone between flights, with your progress saved across devices.</p>
    <a class="btn primary" href="/">Create a free account</a>
  </section>

  <section class="faq">
    <span class="label">Questions</span>
    <h2>About ATPL {E(s['name'])}</h2>
    {"".join(f"<details><summary>{E(q)}</summary><p>{E(a)}</p></details>" for q, a in faqs)}
  </section>

  <nav class="others" aria-label="Other subjects">
    <span class="label">Other subjects</span>
    <ul>{"".join(f'<li><a href="/{o["slug"]}">ATPL {E(o["name"])}</a></li>' for o in others)}</ul>
  </nav>

  <footer>© Adrenasky · ATPL theory revision · Nairobi, Kenya · <a href="/">www.adrenasky.com</a></footer>
</div>
<script>{js}</script>
</body>
</html>
"""

for s in SUBJECTS:
    open(os.path.join(OUT, s["slug"] + ".html"), "w").write(page(s))
    print("built", s["slug"], len(s["questions"]), "questions")
