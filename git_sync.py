import os
import subprocess
import threading

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def _git(*args, cwd=BASE_DIR):
    result = subprocess.run(
        ["git"] + list(args),
        cwd=cwd, capture_output=True, text=True, timeout=60,
    )
    return result.returncode, result.stdout.strip(), result.stderr.strip()

def _configurar():
    token  = os.getenv("GIT_TOKEN", "").strip()
    repo   = os.getenv("GIT_REPO", "").strip()
    branch = os.getenv("GIT_BRANCH", "main").strip()
    name   = os.getenv("GIT_USER_NAME", "Deploy Bot")
    email  = os.getenv("GIT_USER_EMAIL", "bot@descubranv.com")

    if not token or not repo:
        print("[GIT] ⚠️  GIT_TOKEN ou GIT_REPO não configurados — sync desativado")
        return None

    _git("config", "user.name", name)
    _git("config", "user.email", email)
    _git("remote", "set-url", "origin", f"https://{token}@github.com/{repo}.git")
    return branch

def commit_and_push(message: str = "chore: update dados"):
    branch = _configurar()
    if branch is None:
        return

    _git("fetch", "origin", branch)
    _git("add", "dados/", "admin/user.xml")

    rc, _, _ = _git("diff", "--cached", "--quiet")
    if rc == 0:
        print("[GIT] ✅ Nada a commitar")
        return

    rc, _, err = _git("commit", "-m", message)
    if rc != 0:
        print(f"[GIT] ❌ Erro no commit: {err}")
        return

    rc, _, err = _git("push", "origin", f"HEAD:{branch}")
    if rc == 0:
        print(f"[GIT] 🚀 Push: {message}")
    else:
        print(f"[GIT] ❌ Erro no push: {err}")

def sync_async(message: str = "chore: update dados"):
    t = threading.Thread(target=commit_and_push, args=(message,), daemon=True)
    t.start()
