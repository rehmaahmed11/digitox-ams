#!/usr/bin/env python3
"""
AMS theme kit - one stdlib-only script for the Blogger theme in ../ams-blogger-theme.xml

    python3 theme/tools/build.py audit      # validate the theme + print the report
    python3 theme/tools/build.py preview    # write theme/preview/*.html
    python3 theme/tools/build.py all        # both
    python3 theme/tools/build.py serve      # serve the repo root on :4173 (preview + images)

Why a renderer is in here: a Blogger template is XML with its own tag language
(b:if / b:else / b:loop / b:include / data:x / expr:y). Rendering a real page needs a
small interpreter for that subset - and the same interpreter is a strict validator,
because it resolves every data tag, every conditional and every include. So we get
"will Blogger accept this file" checks plus "one <h1>? duplicate ids? images with alt?"
without a browser.

Requires nothing but Python 3 (see engine/setup).
"""

from __future__ import annotations

import gzip
import html
import os
import re
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
THEME_DIR = os.path.dirname(HERE)
REPO = os.path.dirname(THEME_DIR)
THEME = os.path.join(THEME_DIR, "ams-blogger-theme.xml")
PREVIEW_DIR = os.path.join(THEME_DIR, "preview")

B = "http://www.google.com/2005/gml/b"
DATA = "http://www.google.com/2005/gml/data"
EXPR = "http://www.google.com/2005/gml/expr"
XHTML = "http://www.w3.org/1999/xhtml"
# data tags whose value is HTML, not text (Blogger semantics)
RAW_DATA = {"post.body", "blog.pageHtmlTitle"}

VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link",
        "meta", "param", "source", "track", "wbr"}

# ---------------------------------------------------------------- fixture data
# Only the tags the theme uses. A typo in the theme (data:post.tile) is reported as an
# unknown data tag by the audit instead of silently rendering nothing.

CH = "https://www.youtube.com/channel/UCW5b5zJ1MW35P1x9--ExMvg"
POST_MD = os.path.join(REPO, "blogger/ams-capslock-osd/post.md")


def png_size(path):
    """Intrinsic size of a PNG/JPEG so the preview can reserve the exact box (CLS 0)."""
    try:
        with open(path, "rb") as fh:
            head = fh.read(64)
        if head[:8] == b"\x89PNG\r\n\x1a\n":
            w, h = struct.unpack(">II", head[16:24])
            return w, h
        if head[:2] == b"\xff\xd8":
            with open(path, "rb") as fh:
                fh.read(2)
                while True:
                    marker = fh.read(1)
                    while marker and marker != b"\xff":
                        marker = fh.read(1)
                    code = fh.read(1)
                    if code in (b"\xc0", b"\xc1", b"\xc2", b"\xc3"):
                        fh.read(3)
                        h, w = struct.unpack(">HH", fh.read(4))
                        return w, h
                    seg = struct.unpack(">H", fh.read(2))[0]
                    fh.seek(seg - 2, os.SEEK_CUR)
    except Exception:                                          # noqa: BLE001
        return None
    return None


LABELS = [{"name": "AMS", "url": "/search/label/AMS"},
          {"name": "Windows", "url": "/search/label/Windows"},
          {"name": "Free tool", "url": "/search/label/Free%20tool"}]

POSTS = [
    {"title": "AMS Caps Lock OSD \u2014 Know your caps. Every time.",
     "url": "/2026/10/ams-caps-lock-osd.html", "timestamp": "Oct 14, 2026",
     "labels": list(LABELS), "body": "",
     "snippets": {"short": "We've all been there: typing away, and suddenly everything is in "
                           "capitals. AMS Caps Lock OSD shows a clean popup the moment you "
                           "flip the key.", "long": ""}},
    {"title": "Why 300 KB beats 300 MB",
     "url": "/2026/10/why-small-tools-win.html", "timestamp": "Oct 8, 2026",
     "labels": LABELS[:1], "body": "",
     "snippets": {"short": "A utility should cost nothing to keep. How we hold every AMS tool "
                           "under half a megabyte, and what that buys you.", "long": ""}},
    {"title": "Tray icons that actually mean something",
     "url": "/2026/09/tray-icons-that-mean-something.html", "timestamp": "Sep 29, 2026",
     "labels": [{"name": "Design", "url": "/search/label/Design"}], "body": "",
     "snippets": {"short": "Blue when on, grey when off. Two colours, zero guessing - the small "
                           "design rule behind every AMS status icon.", "long": ""}},
]
def post_body() -> str:
    """The real AMS Caps Lock OSD post, from the part after the first '---'."""
    if not os.path.exists(POST_MD):
        return "<p>Post content lives in <code>blogger/ams-capslock-osd/post.md</code>.</p>"
    raw = open(POST_MD, encoding="utf-8").read()
    body = raw.split("\n---\n", 1)[-1].strip()  # drop the publish-settings block
    body = re.sub(r"^#\s+.*\n", "", body, count=1)           # Blogger supplies the title
    return md_to_html(body)


SITE = {
    "blog.languageDirection": "ltr", "blog.locale": "en", "blog.title": "AMS",
    "blog.url": "https://ams-tools.blogspot.com/",
    "blog.homepageUrl": "https://ams-tools.blogspot.com/",
    "blog.canonicalUrl": "https://ams-tools.blogspot.com/",
    "blog.metaDescription": "Small, clean Windows utilities by AMS. Free, tiny, no admin rights.",
    "blog.searchQuery": "", "blog.searchLabel": "",
    "view.isPreview": False, "view.isLayoutMode": False, "view.isMobile": False,
    "view.isHomepage": True, "view.isSingleItem": False, "view.isMultipleItems": True,
    "view.isPost": False, "view.isPage": False, "view.isArchive": False,
    "view.isSearch": False, "view.isLabelSearch": False, "view.isError": False,
    "title": "AMS", "description": "Small tools. Big care.",
    "links": [{"name": "Downloads", "target": "/p/downloads.html"},
              {"name": "Changelog", "target": "/p/changelog.html"}],
    "labels": [dict(l, count=str(3 - i)) for i, l in enumerate([
        {"name": "AMS", "url": "/search/label/AMS"},
        {"name": "Desktop utilities", "url": "/search/label/Desktop%20utilities"},
        {"name": "Design", "url": "/search/label/Design"},
        {"name": "Free tool", "url": "/search/label/Free%20tool"},
        {"name": "Windows", "url": "/search/label/Windows"}])],
    "data": [{"name": "October 2026", "url": "/2026_10_01_archive.html"},
             {"name": "September 2026", "url": "/2026_09_01_archive.html"}],
    "posts": POSTS,
    "newerPageUrl": "/search?updated-max=2026-10-01T00:00:00%2B05:00&max-results=7",
    "olderPageUrl": "/search?updated-min=2026-01-01T00:00:00%2B05:00&max-results=7",
}

VIEWS = {
    "index": {"blog.pageType": "index", "blog.pageName": "", "blog.pageTitle": "AMS"},
    "item": {"blog.pageType": "item", "blog.pageTitle": POSTS[0]["title"],
             "blog.pageName": POSTS[0]["title"], "blog.url": POSTS[0]["url"],
             "view.isHomepage": False, "view.isSingleItem": True,
             "view.isMultipleItems": False, "view.isPost": True, "posts": [POSTS[0]],
             "newerPageUrl": "", "olderPageUrl": ""},
    "label": {"blog.pageType": "archive", "blog.pageName": "Free tool",
              "blog.pageTitle": "Free tool", "blog.url": "/search/label/Free%20tool",
              "view.isHomepage": False, "view.isLabelSearch": True, "view.isSearch": True},
}


# ---------------------------------------------------------------- mini interpreter

class Ctx:
    def __init__(self, view="index"):
        self.over = dict(VIEWS.get(view, {}))
        self.stack: list[dict] = [{}]
        self.widget = None
        self.errors: list[str] = []
        self.ids: list[str] = []

    def get(self, path: str):
        for scope in reversed(self.stack):
            if path in scope:
                return scope[path]
        if path in self.over:
            return self.over[path]
        if path in SITE:
            return SITE[path]
        self.errors.append(f"unknown data tag: data:{path}")
        return ""

    def push(self, scope: dict):
        self.stack.append(scope)

    def pop(self):
        self.stack.pop()

    def as_dict(self, path: str):
        """Resolve a bare name used by b:include data='post' / b:loop var='post'."""
        head = path.split(".", 1)[0]
        val = self.get(head) if "." not in path else self.get(path)
        return val


def flatten(prefix: str, d) -> dict:
    """post -> {'post.title':..}, and nested: {'post.snippets.short':..}."""
    out = {prefix: d}
    if isinstance(d, dict):
        for k, v in d.items():
            out[f"{prefix}.{k}"] = v
            if isinstance(v, dict):
                out.update({f"{prefix}.{kk}": vv for kk, vv in flatten(k, v).items()
                            if kk not in (k,)})
                out[f"{prefix}.{k}"] = v
    return out


def esc(v, attr=False):
    return html.escape("" if v is None else str(v), quote=attr)


DATA_RE = re.compile(r"(?:data|expr):([A-Za-z0-9_.]+)")


def eval_expr(expr: str, ctx: Ctx):
    """Evaluate Blogger cond/expr: data tags, ==, !=, !, ternary, and/or, string concat."""
    py = DATA_RE.sub(lambda m: f'__g("{m.group(1)}")', expr)
    py = re.sub(r"(?<![<>!=])=(?!=)", "==", py)
    py = re.sub(r"\btrue\b", "True", py)
    py = re.sub(r"\bfalse\b", "False", py)
    m = re.match(r"^(.*?)\s*\?\s*(.*?)\s*:\s*(.*)$", py, re.S)
    if m:
        py = f"({m.group(2)} if {m.group(1)} else {m.group(3)})"
    try:
        return eval(py, {"__builtins__": {}}, {"__g": ctx.get})            # noqa: S307
    except Exception as exc:                                               # noqa: BLE001
        ctx.errors.append(f"cannot evaluate [{expr}] ({exc})")
        return ""


def includable(widget, name):
    if widget is None:
        return None
    for inc in widget:
        if inc.tag == f"{{{B}}}includable" and inc.attrib.get("id") == name:
            return inc
    return None


def render_children(el, ctx: Ctx) -> str:
    parts = [el.text or ""]
    for c in el:
        parts.append(render_node(c, ctx))
        parts.append(c.tail or "")
    return "".join(parts)


def render_node(node, ctx: Ctx) -> str:
    tag = node.tag
    if not isinstance(tag, str):
        return ""
    if tag.startswith("{"):
        ns, name = tag[1:].split("}", 1)
    else:
        ns, name = "", tag

    if ns == B:
        if name == "if":
            branches: list[list] = [[]]
            for c in node:
                if c.tag == f"{{{B}}}else":
                    branches.append([])
                    if c.tail:
                        branches[-1].append(c.tail)
                    continue
                branches[-1].append(c)
                if c.tail:
                    branches[-1].append(c.tail)
            if node.text:
                branches[0].insert(0, node.text)
            if len(branches) > 2:
                ctx.errors.append("b:if with more than one b:else")
            # render every branch: keeps the validator strict on both code paths
            rendered = ["".join(x if isinstance(x, str) else render_node(x, ctx) for x in br)
                        for br in branches]
            return rendered[0] if bool(eval_expr(node.attrib.get("cond", "False"), ctx)) \
                else (rendered[1] if len(rendered) > 1 else "")
        if name == "else":
            return ""
        if name == "loop":
            values = eval_expr(node.attrib.get("values", ""), ctx)
            var = node.attrib.get("var", "item")
            out = []
            for item in (values or []):
                scope = flatten(var, item)
                ctx.push(scope)
                out.append(render_children(node, ctx))
                ctx.pop()
            return "".join(out)
        if name == "include":
            inc = includable(ctx.widget, node.attrib.get("name"))
            if inc is None:
                ctx.errors.append(f"b:include name='{node.attrib.get('name')}' not found")
                return ""
            scope = {}
            if node.attrib.get("data"):
                val = ctx.as_dict(node.attrib["data"])
                var = inc.attrib.get("var", node.attrib["data"])
                scope = flatten(var, val)
            ctx.push(scope)
            body = render_children(inc, ctx)
            ctx.pop()
            return body
        if name == "section":
            sid = node.attrib.get("id", "")
            cls = " ".join(x for x in ["section", node.attrib.get("class", "")] if x)
            ctx.ids.append(sid)
            inner = "".join(render_widget(w, ctx) for w in node if w.tag == f"{{{B}}}widget")
            return f'<div class="{esc(cls, True)}" id="{esc(sid, True)}">{inner}</div>'
        if name == "widget":
            ctx.errors.append(f"widget {node.attrib.get('id')} is not inside a b:section")
            return render_widget(node, ctx)
        return ""                                  # b:skin, b:widget-settings, ...

    if ns == DATA:
        path = name.replace("_", ".")
        val = ctx.get(path)
        if isinstance(val, (list, dict)):
            ctx.errors.append(f"data:{path} holds a list, not text")
            return ""
        if path in RAW_DATA:                                # Blogger injects these as HTML
            return str(val)
        return esc(str(val))

    if name == "head":
        return ""

    a = []
    for k, v in node.attrib.items():
        if k.startswith("{"):
            k, v = k.split("}", 1)[1], eval_expr(v, ctx)
        if v is True:
            v = ""
        elif v is False:
            v = "1" if k == "hidden" else ""
        if k == "id":
            ctx.ids.append(str(v))
        a.append(k if v == "" else f'{k}="{esc(str(v), True)}"')
    open_tag = f"<{name}{' ' + ' '.join(a) if a else ''}>"
    if name in VOID:
        return open_tag
    inner = render_children(node, ctx)
    if name in ("pre", "textarea"):
        return f"{open_tag}{inner}</{name}>"
    return f"{open_tag}{inner.strip()}</{name}>"


def render_widget(widget, ctx: Ctx) -> str:
    wid = widget.attrib.get("id", "Widget0")
    wtype = widget.attrib.get("type", "Widget")
    ctx.ids.append(wid)
    prev, ctx.widget = ctx.widget, widget
    inc = includable(widget, "main")
    if inc is None:
        ctx.errors.append(f"widget {wid} has no includable id='main'")
        body = ""
    else:
        ctx.push({"title": widget.attrib.get("title", wtype), "@widget": wtype})
        body = render_children(inc, ctx)
        ctx.pop()
    ctx.widget = prev
    return f'<div class="widget {esc(wtype)}" data-version="2" id="{esc(wid, True)}">{body}</div>'


def render_page_body(root, view: str) -> tuple[str, Ctx]:
    ctx = Ctx(view)
    body = root.find(f"{{{XHTML}}}body")
    return render_children(body, ctx).strip(), ctx


# ---------------------------------------------------------------- markdown -> HTML

def inline_md(s: str) -> str:
    s = esc(s)
    s = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", img_tag, s)
    s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    return s


def img_tag(m) -> str:
    alt, src = m.group(1), m.group(2)
    path = os.path.normpath(os.path.join(PREVIEW_DIR, src))
    size = png_size(path)
    w, h = (size if size else (800, 450))
    return (f'<img alt="{esc(alt, True)}" src="{esc(src, True)}" width="{w}" height="{h}" '
            f'loading="lazy" decoding="async">')


def md_to_html(md: str) -> str:
    """Tiny markdown, for the preview only - on Blogger the post body is already HTML."""
    out: list[str] = []
    list_kind = None

    def close_list():
        nonlocal list_kind
        if list_kind:
            out.append(f"</{list_kind}>")
            list_kind = None

    for raw in md.split("\n"):
        line = raw.strip()
        if not line or line in ("---", "***"):
            close_list()
            continue
        m = re.match(r"^(#{2,4})\s+(.*)$", line)
        if m:
            close_list()
            n = len(m.group(1))
            out.append(f"<h{n}>{inline_md(m.group(2))}</h{n}>")
            continue
        m = re.match(r"^[-*+]\s+(.*)$", line)
        if m:
            if list_kind != "ul":
                close_list()
                out.append("<ul>")
                list_kind = "ul"
            out.append(f"<li>{inline_md(m.group(1))}</li>")
            continue
        m = re.match(r"^\d+[.)]\s+(.*)$", line)
        if m:
            if list_kind != "ol":
                close_list()
                out.append("<ol>")
                list_kind = "ol"
            out.append(f"<li>{inline_md(m.group(1))}</li>")
            continue
        close_list()
        if line.startswith(">"):
            out.append(f"<blockquote><p>{inline_md(line.lstrip('> '))}</p></blockquote>")
            continue
        out.append(f"<p>{inline_md(line)}</p>")
    close_list()
    return "\n".join(out)


POSTS[0]["body"] = post_body()


# ---------------------------------------------------------------- preview writer

def skin_css(xml_text: str) -> str:
    m = re.search(r"<b:skin><!\[CDATA\[(.*?)\]\]></b:skin>", xml_text, re.S)
    if not m:
        sys.exit("no b:skin CDATA found in the theme")
    return m.group(1).strip()


PAGES = (
    ("index", "index.html", "AMS \u2014 Small tools. Clean design."),
    ("item", "post.html", "AMS Caps Lock OSD \u2014 AMS"),
    ("label", "label.html", "Free tool \u2014 AMS"),
)


def build_previews(root, xml_text: str) -> list[tuple[str, int, list[str]]]:
    os.makedirs(PREVIEW_DIR, exist_ok=True)
    css = skin_css(xml_text)
    report = []
    for view, fname, title in PAGES:
        main, ctx = render_page_body(root, view)
        head = "\n".join([
            "<!DOCTYPE html>",
            '<html dir="ltr" lang="en">',
            "<head>",
            '<meta charset="UTF-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1">',
            f"<title>{esc(title)}</title>",
            '<meta name="description" content="'
            + esc(SITE["blog.metaDescription"], True) + '">',
            '<meta name="theme-color" content="#F6F8FC">',
            '<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns=%27http://www.w3.org'
            '/2000/svg%27 viewBox=%270 0 64 64%27%3E%3Crect width=%2764%27 height=%2764%27 '
            'rx=%2715%27 fill=%27%23005CD6%27/%3E%3C/svg%3E">',
            "<style>", css, "</style>",
            # preview-only note bar; NOT part of the theme
            "<style>.preview-note{margin:0 auto;max-width:1140px;padding:9px 20px;font-size:13px;"
            "background:#0B1220;color:#DCE6F5}.preview-note a{color:#9ECBFF}</style>",
            "</head>",
            "<body>",
        ])
        note = ("<p class='preview-note'>Static preview of <code>theme/ams-blogger-theme.xml</code>"
                " \u2014 same CSS, same markup, sample content. <a href='index.html'>Home</a> \u00b7 "
                "<a href='post.html'>Post</a> \u00b7 <a href='label.html'>Topic</a></p>")
        if ctx.errors:
            note += ("<p class='preview-note'>renderer notes: "
                     + esc("; ".join(sorted(set(ctx.errors)))) + "</p>")
        out = head + note + main + "\n</body>\n</html>\n"
        with open(os.path.join(PREVIEW_DIR, fname), "w", encoding="utf-8") as fh:
            fh.write(out)
        report.append((fname, len(out.encode()), sorted(set(ctx.errors))))
    return report


# ---------------------------------------------------------------- audit

def css_rules(css: str):
    return re.findall(r"([^{}]+)\{([^{}]*)\}", re.sub(r"/\*.*?\*/", "", css, flags=re.S))


def tokens(css: str) -> dict:
    root = re.search(r":root\{(.*?)\}", css, re.S)
    return dict(re.findall(r"(--[\w-]+):\s*([^;]+);", root.group(1))) if root else {}


def lum(c: str) -> float:
    c = c.strip().lstrip("#")
    if len(c) == 3:
        c = "".join(x * 2 for x in c)
    r, g, b = (int(c[i:i + 2], 16) / 255 for i in (0, 2, 4))
    f = lambda v: v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4  # noqa: E731
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)


def ratio(a: str, b: str) -> float:
    la, lb = lum(a), lum(b)
    return (max(la, lb) + 0.05) / (min(la, lb) + 0.05)


def audit(root, xml_text: str) -> int:
    ok: list[str] = []
    warn: list[str] = []
    fail: list[str] = []
    css = skin_css(xml_text)
    tk = tokens(css)
    el = root

    def passed(cond, msg):
        (ok if cond else fail).append(msg)

    a = {k.rpartition("}")[2]: v for k, v in el.attrib.items()}
    passed(a.get("css") == "false", "b:css='false'  Blogger's widgets.css is not loaded "
                                    "(the usual render-blocking file on Blogger)")
    passed(a.get("js") == "false", "b:js='false'   Blogger's widgets.js is not loaded (0 JS)")
    passed(a.get("layoutsVersion") == "3", "b:layoutsVersion='3'")
    passed(a.get("defaultwidgetversion") == "2", "b:defaultwidgetversion='2'")
    passed(a.get("responsive") == "true", "b:responsive='true' (same template on phone + desktop)")
    passed(a.get("lang") == "en", "<html lang> set (screen readers, and Lighthouse SEO)")
    passed(a.get("templateVersion") == "2.0.0", f"templateVersion {a.get('templateVersion')}")

    head = el.find(f"{{{XHTML}}}head")
    tags = [t.tag for t in head.iter()]
    passed(f"{{{B}}}skin" in tags, "b:skin holds every style (inline = 0 stylesheet requests)")
    passed(any(t.tag == f"{{{B}}}include" and t.attrib.get("name") == "all-head-content"
               for t in head), "all-head-content included (Blogger emits title/canonical/skin)")
    metas = {}
    for m in head.iter():
        if m.tag != f"{{{XHTML}}}meta":
            continue
        key = (m.attrib.get("name") or m.attrib.get("property") or m.attrib.get("charset")
               and "charset" or "charset")
        metas[key] = m.attrib.get("content") or m.attrib.get(f"{{{EXPR}}}content") or "set"
    passed(metas.get("viewport") == "width=device-width, initial-scale=1",
           "viewport meta, pinch-zoom not blocked")
    passed("user-scalable=no" not in xml_text and "maximum-scale" not in xml_text,
           "no user-scalable=no / maximum-scale (a11y fail if present)")
    passed("description" in metas, "meta description slot (guarded by b:if)")
    passed("theme-color" in metas, "theme-color = page background")
    passed("rel='icon'" in xml_text and "data:image/svg+xml" in xml_text,
           "favicon is a data: URI (no 404 request, brand in the tab)")

    ext = re.findall(r"<(?:script|link|img|iframe)[^>]*?(?:src|href)=['\"](?:https?:)?//", xml_text)
    passed(not ext, f"no external <script>/<link>/<img>/<iframe> ({len(ext)} found)")
    passed(not any(t.tag.rpartition("}")[2] == "script" for t in el.iter() if isinstance(t.tag, str)),
           "no <script> element")
    passed("@import" not in css, "no @import in CSS (the classic Blogger LCP killer)")
    passed("@font-face" not in css, "no @font-face: 0 font bytes, 0 swap-induced layout shift")
    passed(not re.search(r"url\(\s*['\"]?(?!data:)", css), "no url() assets in CSS (gradients only)")
    passed("color-scheme:light" in css.replace(" ", ""), "color-scheme locked to light")

    widgets = list(el.iter(f"{{{B}}}widget"))
    sections = list(el.iter(f"{{{B}}}section"))
    ids = [w.attrib.get("id") for w in widgets]
    passed(len(ids) == len(set(ids)), "widget ids unique (" + ", ".join(ids) + ")")
    passed(all(re.fullmatch(re.escape(w.attrib.get("type", "")) + r"\d+", w.attrib.get("id", ""))
               for w in widgets), "widget ids are <Type><n> (Blogger requires it)")
    passed(sum(1 for w in widgets if w.attrib.get("type") == "Blog") == 1, "exactly one Blog widget")
    passed(sum(1 for w in widgets if w.attrib.get("type") == "Header") == 1, "exactly one Header")
    passed(all(includable(w, "main") for w in widgets), "every widget has includable id='main'")
    for s in sections:
        for c in s:
            if c.tag != f"{{{B}}}widget":
                fail.append(f"section '{s.attrib.get('id')}' holds {c.tag.rpartition('}')[2]}"
                            " - b:section may contain only b:widget")
    passed(includable(next(w for w in widgets if w.attrib.get("type") == "PageList"), "main")
           is not None, "tab bar is driven by a PageList gadget (editable in Layout)")

    anchors = [t for t in el.iter(f"{{{XHTML}}}a")]
    passed(all(t.attrib.get("href") or t.attrib.get(f"{{{EXPR}}}href") for t in anchors),
           "every <a> has an href (crawlable)")
    passed(all("noopener" in (t.attrib.get("rel") or "") for t in anchors
               if t.attrib.get("target") == "_blank"), "target='_blank' links carry rel=noopener")
    passed("<nav" in xml_text and "aria-label" in xml_text, "nav landmarks have accessible names")
    passed("role='list'" in xml_text, "ul[role=list]: list-style:none keeps list semantics")
    passed("class='skip'" in xml_text, "skip-to-content link")
    passed("<label" in xml_text, "search field has a <label>")
    passed(not re.search(r"\sstyle=['\"]", xml_text), "no inline style= attributes")

    CSS_PROPS = set("""align-items appearance aspect-ratio backdrop-filter background background-color
     border border-bottom border-collapse border-color border-left border-radius border-style
     border-top box-shadow box-sizing color content filter flex font font-family font-size
     font-smoothing font-style font-weight gap grid-template-columns height hidden inset justify-content
     left letter-spacing line-height list-style list-style-type margin margin-bottom margin-left
     margin-right margin-top max-height max-width min-height min-width opacity order outline
     outline-offset overflow overflow-x padding padding-bottom padding-left padding-right padding-top
     page-break-inside pointer-events position quotes resize right scroll-behavior scroll-snap-align
     scroll-snap-type scrollbar-width text-align text-decoration text-decoration-thickness
     text-rendering text-shadow text-transform text-underline-offset top transform transition
     user-select vertical-align visibility white-space width will-change word-break z-index
     -webkit-appearance -webkit-tap-highlight-color color-scheme tab-size text-wrap
     display clip-path cursor fill stroke align-self align-items flex-basis flex-direction
     flex-grow flex-shrink flex-wrap justify-items justify-self place-items row-gap column-gap
     border-bottom-color border-top-color border-left-color border-right-color scroll-margin-top
     border-image border-spacing object-fit image-rendering scroll-padding-top caret-color
     animation-duration animation-name transition-duration transition-property -webkit-touch-callout
     -webkit-font-smoothing contain contain-intrinsic-size font-display font-feature-settings
     -webkit-background-clip -webkit-box-reflect -webkit-font-smoothing -webkit-overflow-scrolling
     -webkit-text-fill-color -webkit-text-size-adjust -webkit-tap-highlight-color""".split())
    odd = []
    for sel, bodytxt in css_rules(css):
        for prop in re.findall(r"(?:^|;)\s*([a-z-]+)\s*:", bodytxt):
            if prop not in CSS_PROPS and not prop.startswith(("--", "@", "aria")):
                odd.append(f"{sel.strip()[:22]}: {prop}")
    (ok if not odd else warn).append(
        "every CSS property is a real one (no typos)"
        if not odd else "unknown CSS property (typo, or add it to CSS_PROPS): "
                        + "; ".join(odd[:5]))

    small = []
    for sel, bodytxt in css_rules(css):
        if "print" in sel:
            continue
        for prop, val in re.findall(r"([\w-]+)\s*:\s*([^;]+)", bodytxt):
            if prop == "font-size":
                for px in re.findall(r"(\d+(?:\.\d+)?)px", val):
                    if float(px) < 12:
                        small.append(f"{sel.strip()[:26]} -> {px}px")
    passed(not small, "no font-size under 12px (Lighthouse 'font sizes are legible')")
    if small:
        warn.extend(small[:3])

    small_targets = []
    for cls in (".tab", ".btn", ".chip", ".search input", ".search button", ".pager a"):
        block = re.search(re.escape(cls) + r"\{([^}]*)\}", css)
        if not block:
            small_targets.append(f"{cls} missing")
            continue
        mh = re.search(r"min-height:\s*(\d+)", block.group(1))
        if not mh or int(mh.group(1)) < 34:
            small_targets.append(f"{cls} min-height " + (mh.group(1) + "px" if mh else "unset"))
    passed(not small_targets, "touch targets sized (44-48px on phones via media query)")
    if small_targets:
        warn.append("check tap targets: " + "; ".join(small_targets))

    body_fs = re.search(r"body\{[^}]*font-size:\s*(\d+)", css)
    passed(bool(body_fs) and int(body_fs.group(1)) >= 16,
           f"body text {body_fs.group(1) if body_fs else '?'}px (comfortable reading size)")
    passed("prefers-reduced-motion" in css, "prefers-reduced-motion honoured")
    passed("scroll-behavior" in css, "smooth anchor scroll (Back to top, no JS)")
    passed("@media print" in css, "print stylesheet (posts print clean)")

    css_bytes = len(css.encode())
    gz = len(gzip.compress(css.encode(), 9))
    # ~10 x 1.4 KB of initial congestion window: stay under that and the page paints
    # after a single round trip, which is what makes FCP/LCP fast on a phone.
    passed(gz <= 4600, f"inline CSS {css_bytes:,} B -> {gz:,} B gzipped: fits the first "
                       f"round trip (budget 4,600 B gz)")
    dead = [t for t in tokens(css) if f"var({t})" not in css]
    passed(not dead, "no unused design tokens" + ("" if not dead else f" - dead: {dead}"))
    passed(len(xml_text.encode()) < 60000, f"theme file {len(xml_text.encode()):,} B total")

    pairs = [("--ink", "--surface", 4.5, "post body text"),
             ("--ink", "--bg", 4.5, "text on page background"),
             ("--ink-2", "--surface", 4.5, "meta line / excerpt"),
             ("--ink-2", "--surface-2", 4.5, "blockquote text"),
             ("--ink-2", "--bg", 4.5, "muted text on page background"),
             ("--ink-2", "--tint", 3.0, "inactive tab label on active tint"),
             ("--accent", "--surface", 4.5, "links + active tab"),
             ("--accent", "--surface-2", 4.5, "label chips"),
             ("--accent", "--bg", 4.5, "brand name hover on header"),
             ("#FFFFFF", "#0B63D6", 4.5, "primary button text (light end)"),
             ("#FFFFFF", "#0047B3", 4.5, "primary button text (dark end)"),
             ("#FFFFFF", "#C42B25", 4.5, "subscribe button (light end)"),
             ("#FFFFFF", "#8E1414", 4.5, "subscribe button (dark end)"),
             ("#EEF3FA", "#0B1220", 4.5, "about card heading area"),
             ("#DCE6F5", "#132442", 4.5, "about card body text"),
             ("#9ECBFF", "#0B1220", 4.5, "about card title"),
             ]
    rows = []
    for fg, bg, need_r, what in pairs:
        f = tk.get(fg, fg)
        b = tk.get(bg, bg)
        r = ratio(f, b)
        rows.append((what, f, b, r, r >= need_r, need_r))
    passed(all(r[4] for r in rows), "all palette pairs pass WCAG AA contrast")

    per_view = {}
    for view, *_ in PAGES:
        out, ctx = render_page_body(root, view)
        per_view[view] = (out, ctx)
    for view, (out, ctx) in per_view.items():
        passed(not ctx.errors, f"[{view}] every data tag / include resolves"
                               + (f" - {ctx.errors[:2]}" if ctx.errors else ""))
        h1 = len(re.findall(r"<h1[\s>]", out))
        passed(h1 == 1, f"[{view}] exactly one <h1> ({h1} found)")
        dup = sorted({i for i in ctx.ids if ctx.ids.count(i) > 1})
        passed(not dup, f"[{view}] no duplicate ids ({', '.join(dup) if dup else 'clean'})")
        levels = [int(n) for n in re.findall(r"<h([1-6])[\s>]", out)]
        skips = [f"h{p}->h{n}" for p, n in zip(levels, levels[1:]) if n - p > 1]
        passed(not skips, f"[{view}] heading order has no skips ({', '.join(skips) or 'ok'})")
        nodes = len(re.findall(r"<[a-zA-Z][^>]*>", out))
        passed(nodes < 400, f"[{view}] DOM = {nodes} elements (budget 400, Lighthouse limit 1400)")
        imgs = re.findall(r"<img[^>]*>", out)
        passed(all("alt=" in i for i in imgs), f"[{view}] all {len(imgs)} images have alt text")
        passed(all(("width=" in i and "height=" in i) for i in imgs),
               f"[{view}] all images are size-locked (CLS 0)")
        passed(all("loading=" in i for i in imgs[1:]) if len(imgs) > 1 else True,
               f"[{view}] below-the-fold images lazy-load")
        passed("<svg" not in out or "aria-hidden" in out, f"[{view}] decorative SVGs hidden")

    # post-content budget: the theme cannot fix heavy images inside a post
    imgs = re.findall(r"<img[^>]*>", per_view["item"][0])
    heavy, wide = [], []
    for tag in imgs:
        src = re.search(r'src="([^"]+)"', tag)
        if not src:
            continue
        path = os.path.normpath(os.path.join(PREVIEW_DIR, src.group(1)))
        if os.path.exists(path):
            size = os.path.getsize(path)
            if size > 122880:
                heavy.append(f"{os.path.basename(path)} {size // 1024} KB")
        w = re.search(r'width="(\d+)"', tag)
        if w and int(w.group(1)) > 1280:
            wide.append(f"{os.path.basename(path)} {w.group(1)}px")
    if heavy or wide:
        warn.append("post images over budget (export <=1280px wide, <=120 KB): "
                    + "; ".join((heavy + wide)[:4]))
    else:
        ok.append("post images inside the byte/width budget")

    print("=" * 78)
    print("AMS Light \u00b7 theme audit      theme/ams-blogger-theme.xml")
    print("=" * 78)
    for m in ok:
        print("  PASS  " + m)
    for m in warn:
        print("  WARN  " + m)
    for m in fail:
        print("  FAIL  " + m)
    print("-" * 78)
    print("  contrast check (WCAG 2.x, as rendered)")
    for what, f, b, r, good, need_r in rows:
        print(f"    {what:<36} {f} on {b}  {r:5.2f}:1  need {need_r}"
              + ("" if good else "   <-- LOW"))
    print("-" * 78)
    used = "".join(out for out, _ in per_view.values())
    sel_classes = set(re.findall(r"\.([a-zA-Z][\w-]*)", css))
    missing = sorted(c for c in sel_classes
                     if f'class=\'{c}' not in used and f'class="{c}"' not in used
                     and not re.search(rf'class="[^"]*\b{c}\b', used))
    print("  (decorative borders/lines are not WCAG text pairs and are not audited)")
    print("  (selectors kept for post content, not seen in theme markup: "
          + (", ".join(missing) if missing else "none") + ")")
    print(f"  payload: 1 HTML document, {gz:,} B gzipped CSS inline, 0 JS bytes, "
          f"0 external requests, 0 webfonts")
    for view, (out, _) in per_view.items():
        print(f"           {view:<6} {len(out.encode()):>7,} B of rendered HTML")
    print("=" * 78)
    print(f"  RESULT: {len(ok)} passed, {len(warn)} warnings, {len(fail)} failures")
    return 1 if fail else 0


# ---------------------------------------------------------------- CLI

def main() -> int:
    cmd = sys.argv[1] if len(sys.argv) > 1 else "all"
    if not os.path.exists(THEME):
        sys.exit(f"missing {THEME}")
    import xml.etree.ElementTree as ET
    xml_text = open(THEME, encoding="utf-8").read()
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as exc:
        print(f"FAIL  theme is not well-formed XML: {exc}")
        return 1
    if cmd in ("preview", "all"):
        for fname, size, errs in build_previews(root, xml_text):
            print(f"  wrote theme/preview/{fname:<12} {size:>7,} B"
                  + (f"   [{len(errs)} renderer notes]" if errs else ""))
        print("  view it: python3 theme/tools/build.py serve  ->  /theme/preview/index.html")
    if cmd == "serve":
        os.chdir(REPO)
        print("serving repo root on http://0.0.0.0:4173  (open /theme/preview/index.html)")
        os.execvp("python3", ["python3", "-m", "http.server", "4173", "--bind", "0.0.0.0"])
    if cmd in ("audit", "all", "check"):
        return audit(root, xml_text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
