from flask import Blueprint, render_template, request, redirect, url_for, abort, flash, current_app, send_from_directory, jsonify
from flask_login import current_user, login_required
from .models import db, Page, Revision, Role
from .utils import slugify, render_markdown, first_image_src
from sqlalchemy import or_
from difflib import unified_diff
from werkzeug.utils import secure_filename
import os, pathlib, shutil

pages_bp = Blueprint("pages", __name__)

# ---- Permissão de edição ----
def can_edit():
    return current_user.is_authenticated and current_user.role in (Role.ADMIN, Role.INSTRUTOR, Role.MONITOR)

# ---- Uploads: utilidades ----
ALLOWED_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".pdf"}
def page_upload_dir(namespace: str, slug: str) -> str:
    root = current_app.config["UPLOAD_ROOT"]
    safe_ns = secure_filename(namespace) or "geral"
    safe_slug = secure_filename(slug) or "pagina"
    p = os.path.join(root, safe_ns, safe_slug)
    os.makedirs(p, exist_ok=True)
    return p

def list_attachments(namespace: str, slug: str):
    d = page_upload_dir(namespace, slug)
    files = []
    for name in sorted(os.listdir(d)):
        full = os.path.join(d, name)
        # Ignora o arquivo da capa
        if name.lower() == "cover.webp":
            continue
        if os.path.isfile(full):
            files.append(name)
    return files

def is_image(name: str) -> bool:
    return pathlib.Path(name).suffix.lower() in {".jpg",".jpeg",".png",".gif",".webp"}

# ---- Rotas principais ----
@pages_bp.route("/")
def home():
    return render_template("home.html")

@pages_bp.get("/ns/<namespace>")
def list_namespace(namespace):
    pages = Page.query.filter_by(namespace=namespace).order_by(Page.updated_at.desc()).all()
    return render_template("ns_list.html", namespace=namespace, pages=pages)

@pages_bp.get("/p/<namespace>/<slug>")
def view_page(namespace, slug):
    page = Page.query.filter_by(namespace=namespace, slug=slug).first()
    if not page:
        return redirect(url_for("pages.edit_page", namespace=namespace, slug=slug))
    html = render_markdown(page.content)
    attachments = list_attachments(namespace, slug)
    return render_template("page_view.html", page=page, html=html, attachments=attachments, is_image=is_image, can_edit=can_edit())

# ========= EDITAR PÁGINA =========
@pages_bp.route("/edit/<namespace>/<slug>", methods=["GET", "POST"])
@login_required
def edit_page(namespace, slug):
    page = Page.query.filter_by(namespace=namespace, slug=slug).first()
    if not page:
        page = Page(namespace=namespace, slug=slug, title="Nova página", content="", classification="PUBLICO")
        db.session.add(page)
        db.session.commit()

    if request.method == "POST":
        page.title = (request.form.get("title") or "").strip() or page.title
        page.classification = (request.form.get("classification") or page.classification).strip()
        page.content = request.form.get("content") or ""
        page.summary = (request.form.get("summary") or "").strip()
        image_url = (request.form.get("image_url") or "").strip()
        page.image_url = image_url or None
        db.session.commit()
        flash("Página salva.", "success")
        return redirect(url_for("pages.view_page", namespace=namespace, slug=slug))

    return render_template("page_edit.html", page=page)
    
# ========= EXCLUIR PÁGINA =========
@pages_bp.post("/delete/<namespace>/<slug>")
@login_required
def delete_page(namespace, slug):
    if not can_edit():
        abort(403)
        
    page = Page.query.filter_by(namespace=namespace, slug=slug).first_or_404()

    media_root = page_upload_dir(namespace, slug)
    if os.path.isdir(media_root):
        try:
            shutil.rmtree(media_root)
        except Exception:
            pass

    db.session.delete(page)
    db.session.commit()
    flash("Publicação excluída.", "success")
    return redirect(url_for("pages.list_namespace", namespace=namespace))

@pages_bp.get("/history/<namespace>/<slug>")
def history(namespace, slug):
    page = Page.query.filter_by(namespace=namespace, slug=slug).first_or_404()
    revs = Revision.query.filter_by(page_id=page.id).order_by(Revision.created_at.desc()).all()
    return render_template("history.html", page=page, revs=revs)

@pages_bp.get("/diff/<int:older_id>/<int:newer_id>")
def diff(older_id, newer_id):
    old = Revision.query.get_or_404(older_id)
    new = Revision.query.get_or_404(newer_id)
    lines = list(unified_diff(old.content.splitlines(), new.content.splitlines(), fromfile=f'#{old.id}', tofile=f'#{new.id}', lineterm=""))
    return render_template("diff.html", diff_lines=lines, old=old, new=new)

@pages_bp.get("/search")
def search():
    q = request.args.get("q","").strip()
    pages = []
    if q:
        like = f"%{q}%"
        pages = Page.query.filter(or_(Page.title.ilike(like), Page.content.ilike(like))).order_by(Page.updated_at.desc()).all()
    return render_template("search.html", q=q, pages=pages)

@pages_bp.post("/new")
@login_required
def new_page():
    if not can_edit(): abort(403)
    title = request.form.get("title","Nova Página").strip()
    namespace = request.form.get("namespace","geral").strip() or "geral"
    slug = slugify(title)
    return redirect(url_for("pages.edit_page", namespace=namespace, slug=slug))

# ---- Uploads ----
@pages_bp.post("/upload/<namespace>/<slug>")
@login_required
def upload(namespace, slug):
    if not can_edit(): abort(403)
    f = request.files.get("file")
    if not f or f.filename == "":
        flash("Selecione um arquivo.", "error")
        return redirect(url_for("pages.edit_page", namespace=namespace, slug=slug))
    filename = secure_filename(f.filename)
    ext = pathlib.Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTS:
        flash("Tipo não permitido. Envie imagens (.jpg/.png/.webp) ou PDF.", "error")
        return redirect(url_for("pages.edit_page", namespace=namespace, slug=slug))
    dest = os.path.join(page_upload_dir(namespace, slug), filename)
    f.save(dest)
    flash("Arquivo anexado.", "ok")
    return redirect(url_for("pages.edit_page", namespace=namespace, slug=slug))

@pages_bp.get("/media/<namespace>/<slug>/<path:filename>")
def serve_media(namespace, slug, filename):
    d = page_upload_dir(namespace, slug)
    return send_from_directory(d, filename, as_attachment=False)

@pages_bp.post("/delete-attachment/<namespace>/<slug>/<path:filename>")
@login_required
def delete_attachment(namespace, slug, filename):
    if not can_edit(): abort(403)
    d = page_upload_dir(namespace, slug)
    target = os.path.join(d, filename)
    if os.path.isfile(target):
        os.remove(target)
        flash("Anexo removido.", "ok")
    return redirect(url_for("pages.edit_page", namespace=namespace, slug=slug))

# PATCH: add preview route
@pages_bp.post("/preview")
def preview():
    md = request.json.get("markdown","") if request.is_json else ""
    html = render_markdown(md)
    return jsonify({"html": html})

# === Spotlight API: /api/suggest ===
@pages_bp.get("/api/suggest")
def api_suggest():
    q = (request.args.get("q") or "").strip()
    out = []
    if q:
        query = Page.query.filter(
            or_(
                Page.title.ilike(f"%{q}%"),
                Page.slug.ilike(f"%{q}%"),
                Page.namespace.ilike(f"%{q}%"),
            )
        )
        col = getattr(Page, "updated_at", getattr(Page, "created_at", None))
        if col is not None:
            query = query.order_by(col.desc())
        else:
            query = query.order_by(Page.title.asc())

        for p in query.limit(10).all():
            out.append({
                "title": p.title,
                "namespace": p.namespace,
                "slug": p.slug,
                "path": url_for("pages.view_page", namespace=p.namespace, slug=p.slug),
            })

    return jsonify(out)

@pages_bp.get("/new/<namespace>")
@login_required
def create_page(namespace):
    if not can_edit():
        abort(403)
    base = slugify("nova pagina")
    slug = base
    i = 1
    while Page.query.filter_by(namespace=namespace, slug=slug).first():
        slug = f"{base}-{i}"
        i += 1
    return redirect(url_for("pages.edit_page", namespace=namespace, slug=slug))

@pages_bp.post("/upload-cover/<namespace>/<slug>")
def upload_cover(namespace, slug):
    file = request.files.get("file")
    if not file:
        return jsonify({"error": "no file"}), 400

    media_root = page_upload_dir(namespace, slug)
    dest = os.path.join(media_root, "cover.webp")

    try:
        from PIL import Image
        img = Image.open(file.stream).convert("RGB")
        max_side = 1600
        w, h = img.size
        if max(w, h) > max_side:
            if w >= h:
                new_w = max_side; new_h = int(h * max_side / w)
            else:
                new_h = max_side; new_w = int(w * max_side / h)
            img = img.resize((new_w, new_h), Image.LANCZOS)
        img.save(dest, "WEBP", quality=82, method=6)
    except Exception:
        file.seek(0)
        file.save(dest)

    url = url_for("pages.serve_media", namespace=namespace, slug=slug, filename="cover.webp")
    return jsonify({"url": url}), 200
