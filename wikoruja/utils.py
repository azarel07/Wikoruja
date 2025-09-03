import re, unicodedata

def slugify(value: str) -> str:
    value = unicodedata.normalize('NFKD', value or '').encode('ascii', 'ignore').decode('ascii')
    value = re.sub(r'[^a-zA-Z0-9]+', '-', value).strip('-').lower()
    return value or 'pagina'

# === sanitize + markdown com suporte a imagens base64 (data:) ===
def render_markdown(text):
    import markdown as md
    import bleach
    html = md.markdown(text or '', extensions=['fenced_code','tables','toc','codehilite'])
    tags = set(bleach.sanitizer.ALLOWED_TAGS) | {
        'p','img','h1','h2','h3','h4','h5','h6','pre','code','blockquote','hr',
        'table','thead','tbody','tr','th','td','sup','sub'
    }
    attrs = dict(bleach.sanitizer.ALLOWED_ATTRIBUTES)
    attrs.setdefault('img', ['src','alt','title','width','height'])
    attrs.setdefault('a',   ['href','title','target','rel'])
    protocols = set(bleach.sanitizer.ALLOWED_PROTOCOLS) | {'data'}  # aceita data:
    cleaner = bleach.Cleaner(tags=tags, attributes=attrs, protocols=protocols, strip=True)
    return cleaner.clean(html)
# --- primeira imagem do conteúdo (markdown ou html) ---
def first_image_src(md_text: str):
    import re
    if not md_text:
        return None
    # markdown: ![alt](SRC)
    m = re.search(r'!\[[^\]]*\]\((?P<src>[^)]+)\)', md_text, re.IGNORECASE)
    if not m:
        # html: <img src="SRC">
        m = re.search(r'<img[^>]+src=["\'](?P<src>[^"\']+)["\']', md_text, re.IGNORECASE)
    return m.group('src') if m else None
