"""Testes das peças de implantação: URL do banco, carga inicial e entrega do front-end."""

from fastapi.testclient import TestClient

from app.bootstrap import popular
from app.config import normalizar_database_url
from app.database import get_db
from app.main import create_app
from app.models import Profissional, Servico


def test_normaliza_url_do_render_para_psycopg():
    assert normalizar_database_url("postgres://u:s@h:5432/db") == "postgresql+psycopg://u:s@h:5432/db"
    assert normalizar_database_url("postgresql://u:s@h/db") == "postgresql+psycopg://u:s@h/db"
    assert normalizar_database_url("sqlite:///./x.db") == "sqlite:///./x.db"


def test_carga_inicial_e_idempotente(db):
    assert popular(db, "senha-forte-123") == {"servicos": 4, "profissionais": 4}
    assert popular(db, "senha-forte-123") == {"servicos": 0, "profissionais": 0}
    assert db.query(Servico).count() == 4 and db.query(Profissional).count() == 4


def test_carga_inicial_sem_senha_nao_cria_equipe(db):
    criados = popular(db, None)
    assert criados["profissionais"] == 0
    assert db.query(Profissional).count() == 0


def test_carga_inicial_guarda_apenas_hash(db):
    popular(db, "senha-forte-123")
    assert all(p.senha_hash.startswith("$argon2id$") for p in db.query(Profissional))


def _app_com_front(tmp_path, db):
    (tmp_path / "index.html").write_text("<html>AgendaBella</html>", encoding="utf-8")
    (tmp_path / "main-ABCDEFGH.js").write_text("console.log(1)", encoding="utf-8")
    app = create_app(frontend_dist=tmp_path)
    app.dependency_overrides[get_db] = lambda: db
    return TestClient(app)


def test_serve_index_e_fallback_de_rotas_da_spa(tmp_path, db):
    client = _app_com_front(tmp_path, db)
    assert "AgendaBella" in client.get("/").text
    assert "AgendaBella" in client.get("/equipe/agenda").text  # rota do Angular
    assert client.get("/").headers["Cache-Control"] == "no-cache"


def test_arquivos_com_hash_recebem_cache_longo(tmp_path, db):
    client = _app_com_front(tmp_path, db)
    resp = client.get("/main-ABCDEFGH.js")
    assert resp.status_code == 200 and "immutable" in resp.headers["Cache-Control"]


def test_api_inexistente_nao_cai_no_index(tmp_path, db):
    client = _app_com_front(tmp_path, db)
    resp = client.get("/api/nao-existe")
    assert resp.status_code == 404 and resp.json()["detail"] == "Recurso não encontrado."


def test_bloqueia_path_traversal(tmp_path, db):
    (tmp_path.parent / "segredo.txt").write_text("nao", encoding="utf-8")
    client = _app_com_front(tmp_path, db)
    resp = client.get("/..%2Fsegredo.txt")
    assert "nao" != resp.text and "AgendaBella" in resp.text
