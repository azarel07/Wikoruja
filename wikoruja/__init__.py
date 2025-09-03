
# -- light migration: add image_url column if missing (SQLite)
def _ensure_image_url_column(app):
    try:
        from .models import db
        eng = db.engine
        if 'sqlite' in str(eng.url.drivername):
            with eng.connect() as con:
                cols = []
                for row in con.execute("PRAGMA table_info(page)"):
                    try:
                        cols.append(row['name'])
                    except Exception:
                        try:
                            cols.append(row[1])
                        except Exception:
                            pass
                if 'image_url' not in cols:
                    con.execute("ALTER TABLE page ADD COLUMN image_url TEXT")
                    try:
                        app.logger.info("Added image_url column to page table.")
                    except Exception:
                        pass
    except Exception as e:
        try:
            app.logger.warning(f"Could not ensure image_url column: {e}")
        except Exception:
            pass


from flask import Flask
from .models import db, init_db, User, Role
from .auth import auth_bp, login_manager
from .pages import pages_bp
from flask_wtf.csrf import CSRFProtect
import click, os, textwrap
from werkzeug.security import generate_password_hash

def create_app():
    app = Flask(__name__)
    app.config.update(
        SECRET_KEY="dev-secret-key-change-me",              # TROCAR EM PRODUÇÃO
        SQLALCHEMY_DATABASE_URI="sqlite:///wikoruja.db",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        WTF_CSRF_ENABLED=True,
        MAX_CONTENT_LENGTH=32 * 1024 * 1024,                # 32 MB por upload
    )

    # Raiz para uploads (pasta 'uploads' dentro do projeto)
    app.config["UPLOAD_ROOT"] = os.path.join(app.root_path, "uploads")
    os.makedirs(app.config["UPLOAD_ROOT"], exist_ok=True)

    db.init_app(app)
    CSRFProtect(app)
    login_manager.init_app(app)

    app.register_blueprint(auth_bp)
    app.register_blueprint(pages_bp)

    # ---- CLI: criar tabelas ----
    @app.cli.command("init-db")
    def initdb_cmd():
        with app.app_context():
            init_db()
            click.echo("Banco inicializado.")

    # ---- CLI: criar usuário ----
    @app.cli.command("create-user")
    @click.option("--username", prompt=True)
    @click.option("--password", prompt=True, hide_input=True, confirmation_prompt=True)
    @click.option("--role", default="ADMIN", type=click.Choice(["ADMIN","INSTRUTOR","MONITOR","ALUNO","AUDITOR"]))
    def create_user_cmd(username, password, role):
        with app.app_context():
            if User.query.filter_by(username=username).first():
                click.echo("Usuário já existe."); return
            u = User(username=username, role=role, password_hash=generate_password_hash(password))
            db.session.add(u); db.session.commit()
            click.echo(f"Usuário {username} criado com papel {role}.")

    # ---- CLI: seed DOAMEPI ----
    @app.cli.command("bootstrap-doamepi")
    def bootstrap_doamepi_cmd():
        """Cria páginas base para D,O,A,M,E,P,I com texto inicial."""
        from .models import Page, Revision
        areas = [
            ("doutrina","Página Inicial de Doutrina"),
            ("organizacao","Página Inicial de Organização"),
            ("adestramento","Página Inicial de Adestramento"),
            ("material","Página Inicial de Material"),
            ("educacao","Página Inicial de Educação"),
            ("pessoal","Página Inicial de Pessoal"),
            ("infraestrutura","Página Inicial de Infraestrutura"),
        ]
        with app.app_context():
            created = 0
            for ns, title in areas:
                slug = "inicio"
                exists = Page.query.filter_by(namespace=ns, slug=slug).first()
                if exists: continue
                content = textwrap.dedent(f"""
                # {title}
                Bem-vindo ao namespace **{ns.capitalize()}**.

                - Use o botão *Criar & Editar* na Home para novas páginas.
                - Classifique o conteúdo conforme necessidade: `PÚBLICO`, `RESTRITO`, `CONFIDENCIAL`.
                """).strip()
                p = Page(namespace=ns, slug=slug, title=title, classification="PUBLICO", content=content)
                db.session.add(p); db.session.commit()
                db.session.add(Revision(page_id=p.id, content=content, author="bootstrap")); db.session.commit()
                created += 1
            click.echo(f"Namespaces inicializados. Páginas criadas: {created}")

    return app

app = create_app()

# -- limite de tamanho (POST/UPLOAD) para aceitar imagens base64 grandes --
try:
    app.config['MAX_CONTENT_LENGTH'] = 134217728*1024*1024  # 64 MB
except Exception:
    pass
