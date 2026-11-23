"""HTTP adapter: routing, sessions, access control and static-file delivery."""
from __future__ import annotations

import json
import mimetypes
import secrets
import time
from http import HTTPStatus
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlsplit

from . import library, security, views
from .config import COOKIE_SECURE, MAX_FORM_BYTES, SESSION_TTL_SECONDS, STATIC_ROOT
from .storage import database_health, init_db

SESSIONS: dict[str, dict] = {}
LOGIN_FAILURES: dict[str, list[float]] = {}
LOGIN_WINDOW_SECONDS = 600
LOGIN_MAX_FAILURES = 8


class LibraryHandler(BaseHTTPRequestHandler):
    server_version = "WaraqLibrary/2.0"
    sys_version = ""

    def log_message(self, fmt, *args):
        print(f"[{self.log_date_time_string()}] {self.address_string()} - {fmt % args}")

    def _new_session(self) -> None:
        self.session_id = secrets.token_urlsafe(32)
        self.session = {"csrf": secrets.token_urlsafe(24), "user": None,
                        "expires": time.time() + SESSION_TTL_SECONDS, "flash": None}
        SESSIONS[self.session_id] = self.session
        self.new_session = True

    def _load_session(self) -> None:
        cookie = SimpleCookie()
        try:
            cookie.load(self.headers.get("Cookie", ""))
        except Exception:
            pass
        morsel = cookie.get("waraq_session")
        session_id = morsel.value if morsel else ""
        existing = SESSIONS.get(session_id)
        now = time.time()
        if existing and existing.get("expires", 0) > now:
            existing["expires"] = now + SESSION_TTL_SECONDS
            self.session_id, self.session, self.new_session = session_id, existing, False
        else:
            if session_id:
                SESSIONS.pop(session_id, None)
            self._new_session()
        if len(SESSIONS) > 500:
            for key in list(SESSIONS):
                if SESSIONS[key].get("expires", 0) <= now:
                    SESSIONS.pop(key, None)

    def _rotate_session(self) -> None:
        SESSIONS.pop(getattr(self, "session_id", ""), None)
        self._new_session()

    def _cookie_header(self) -> str | None:
        if not self.new_session:
            return None
        secure = "; Secure" if COOKIE_SECURE else ""
        return f"waraq_session={self.session_id}; Path=/; HttpOnly; SameSite=Lax; Max-Age={SESSION_TTL_SECONDS}{secure}"

    def _security_headers(self) -> None:
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "strict-origin-when-cross-origin")
        self.send_header("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        self.send_header("Cross-Origin-Opener-Policy", "same-origin")
        self.send_header("Content-Security-Policy", "default-src 'self'; img-src 'self' data:; style-src 'self' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; script-src 'self'; connect-src 'self'; base-uri 'self'; form-action 'self'; frame-ancestors 'none'")

    def _send_html(self, html: str, status: int = 200) -> None:
        body = html.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self._security_headers()
        cookie = self._cookie_header()
        if cookie:
            self.send_header("Set-Cookie", cookie)
            self.new_session = False
        self.end_headers()
        self.wfile.write(body)

    def _send_json(self, payload: dict, status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self._security_headers()
        self.end_headers()
        self.wfile.write(body)

    def _redirect(self, location: str, status: int = 303) -> None:
        self.send_response(status)
        self.send_header("Location", location)
        self.send_header("Content-Length", "0")
        self._security_headers()
        cookie = self._cookie_header()
        if cookie:
            self.send_header("Set-Cookie", cookie)
            self.new_session = False
        self.end_headers()

    def _user(self):
        return self.session.get("user")

    def _flash(self, message: str, kind: str = "success") -> None:
        self.session["flash"] = (message, kind)

    def _take_flash(self):
        return self.session.pop("flash", None)

    def _page(self, title: str, content: str, active: str = "dashboard", status: int = 200) -> None:
        html = views.shell(title, content, self._user(), active, self.session["csrf"], self._take_flash())
        self._send_html(html, status)

    def _require_login(self) -> bool:
        if not self._user():
            self._flash("سجّل الدخول أولاً لمتابعة استخدام المكتبة.", "error")
            self._redirect("/login")
            return False
        return True

    def _require_manager(self) -> bool:
        if not self._require_login():
            return False
        if self._user()["role"] != "manager":
            self._page("غير مسموح", '<section class="error-state"><span>403</span><h1>هذه الصفحة للمدير فقط.</h1><a class="button button-dark" href="/dashboard">العودة إلى لوحة التحكم</a></section>', status=403)
            return False
        return True

    def _parse_form(self) -> dict[str, str]:
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            length = 0
        if length < 0 or length > MAX_FORM_BYTES:
            raise ValueError("حجم النموذج أكبر من الحد المسموح.")
        content_type = self.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
        if length and content_type != "application/x-www-form-urlencoded":
            raise ValueError("نوع النموذج غير مدعوم.")
        raw = self.rfile.read(length).decode("utf-8", errors="replace")
        parsed = parse_qs(raw, keep_blank_values=True, max_num_fields=80)
        return {key: values[-1] for key, values in parsed.items()}

    def _check_csrf(self, form: dict[str, str]) -> bool:
        supplied, expected = form.get("csrf", ""), self.session.get("csrf", "")
        return bool(supplied and expected and secrets.compare_digest(supplied, expected))

    @staticmethod
    def _login_key(ip: str, username: str) -> str:
        return f"{ip}:{username.strip().casefold()[:80]}"

    def _login_limited(self, key: str) -> bool:
        now = time.time()
        recent = [stamp for stamp in LOGIN_FAILURES.get(key, []) if now - stamp < LOGIN_WINDOW_SECONDS]
        LOGIN_FAILURES[key] = recent
        return len(recent) >= LOGIN_MAX_FAILURES

    def _record_login_failure(self, key: str) -> None:
        LOGIN_FAILURES.setdefault(key, []).append(time.time())

    def do_GET(self) -> None:
        self._load_session()
        parsed = urlsplit(self.path)
        path = unquote(parsed.path)
        query = parse_qs(parsed.query)

        if path.startswith("/static/"):
            self._serve_static(path)
            return
        if path == "/favicon.ico":
            self._redirect("/static/img/favicon.svg", 302)
            return
        if path == "/health":
            health = database_health()
            self._send_json({"status": "ok" if health["ok"] else "error", "application": "Waraq Library", "version": "2.0.0", "storage": "sqlite", "counts": {"items": health["items"], "members": health["members"]}}, 200 if health["ok"] else 503)
            return
        if path == "/":
            if self._user(): self._redirect("/dashboard")
            else: self._send_html(views.landing(self.session["csrf"]))
            return
        if path == "/login":
            if self._user(): self._redirect("/dashboard")
            else: self._send_html(views.login(self.session["csrf"], self._take_flash()))
            return
        if path == "/dashboard":
            if not self._require_login(): return
            user = self._user()
            data = library.get_dashboard(None if user["role"] == "manager" else user["member_id"])
            self._send_html(views.dashboard(user, data, self.session["csrf"], self._take_flash()))
            return
        if path == "/catalog":
            if not self._require_login(): return
            filters = {key: query.get(key, [""])[0] for key in ("q", "type", "specialization", "availability", "project_year")}
            items = library.get_items(filters["q"], filters["type"], filters["specialization"], filters["availability"], filters["project_year"])
            self._send_html(views.catalog(self._user(), items, self.session["csrf"], filters, self._take_flash()))
            return
        if path == "/members":
            if not self._require_manager(): return
            self._send_html(views.members(self._user(), library.get_members(), self.session["csrf"], self._take_flash()))
            return
        if path == "/account":
            if not self._require_login(): return
            self._send_html(views.account(self._user(), self.session["csrf"], self._take_flash()))
            return
        if path == "/loans":
            if not self._require_login(): return
            status = query.get("status", ["active"])[0]
            if status not in ("active", "overdue", "returned", "all"): status = "active"
            user = self._user()
            member_id = None if user["role"] == "manager" else user["member_id"]
            self._send_html(views.loans(user, library.get_loans(member_id, status), self.session["csrf"], status, self._take_flash()))
            return
        self._page("الصفحة غير موجودة", '<section class="error-state"><span>404</span><h1>يبدو أن هذه الصفحة ليست على الرف.</h1><a class="button button-dark" href="/">العودة للرئيسية</a></section>', status=404)

    def _serve_static(self, path: str) -> None:
        relative = path[len("/static/"):]
        target = (STATIC_ROOT / relative).resolve()
        if STATIC_ROOT.resolve() not in target.parents or not target.is_file():
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        data = target.read_bytes()
        content_type = mimetypes.guess_type(str(target))[0] or "application/octet-stream"
        if content_type.startswith("text/") or content_type in ("application/javascript", "image/svg+xml"):
            content_type += "; charset=utf-8"
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "public, max-age=3600")
        self._security_headers()
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self) -> None:
        self._load_session()
        path = unquote(urlsplit(self.path).path)
        try:
            form = self._parse_form()
        except Exception as exc:
            message = str(exc) if isinstance(exc, ValueError) else "تعذر قراءة الطلب. حدّث الصفحة وحاول مجدداً."
            self._page("طلب غير صالح", f'<section class="error-state"><h1>{views.esc(message)}</h1></section>', status=400)
            return
        if not self._check_csrf(form):
            self._page("انتهت صلاحية الصفحة", '<section class="error-state"><span>419</span><h1>انتهت صلاحية النموذج.</h1><p>حدّث الصفحة وحاول مرة أخرى.</p><a class="button button-dark" href="/login">متابعة</a></section>', status=403)
            return

        if path == "/login":
            username, password = form.get("username", ""), form.get("password", "")
            key = self._login_key(self.client_address[0], username)
            if self._login_limited(key):
                self._flash("محاولات كثيرة. انتظر بضع دقائق ثم حاول مرة أخرى.", "error")
                self._redirect("/login")
                return
            user = security.authenticate(username, password)
            if not user:
                self._record_login_failure(key)
                self._flash("اسم المستخدم أو كلمة المرور غير صحيحة.", "error")
                self._redirect("/login")
                return
            LOGIN_FAILURES.pop(key, None)
            self._rotate_session()
            self.session["user"] = user
            self._flash(f"أهلاً بك، {user['username']}.", "success")
            self._redirect("/dashboard")
            return

        if path == "/logout":
            self.session["user"] = None
            self.session["csrf"] = secrets.token_urlsafe(24)
            self._flash("تم تسجيل خروجك بنجاح.", "success")
            self._redirect("/login")
            return

        user = self._user()
        if not user:
            self._flash("سجّل الدخول أولاً.", "error")
            self._redirect("/login")
            return

        if path == "/account/password":
            new_password = form.get("new_password", "")
            if new_password != form.get("confirm_password", ""):
                self._flash("تأكيد كلمة المرور غير مطابق.", "error")
            else:
                try:
                    security.change_password(user["username"], form.get("current_password", ""), new_password)
                    self._flash("تم تحديث كلمة المرور بنجاح.")
                except ValueError as exc:
                    self._flash(str(exc), "error")
            self._redirect("/account")
            return

        if path == "/items/add":
            if user["role"] != "manager":
                self._page("غير مسموح", '<section class="error-state"><h1>هذه العملية للمدير فقط.</h1></section>', status=403); return
            try:
                item_id = library.add_item(form)
                self._flash(f"تمت إضافة المادة إلى الفهرس. رقمها #{item_id}.")
            except ValueError as exc:
                self._flash(str(exc), "error")
            self._redirect("/catalog#add-item")
            return

        if path == "/members/add":
            if user["role"] != "manager":
                self._page("غير مسموح", '<section class="error-state"><h1>هذه العملية للمدير فقط.</h1></section>', status=403); return
            try:
                member_id, username = library.add_member(form.get("name", ""), form.get("password", ""))
                self._flash(f"تم إنشاء العضو #{member_id}. اسم المستخدم: {username}.")
            except ValueError as exc:
                self._flash(str(exc), "error")
            self._redirect("/members")
            return

        if path.startswith("/items/") and path.endswith("/borrow"):
            parts = path.strip("/").split("/")
            if len(parts) == 3 and parts[1].isdigit() and user["role"] == "member":
                try:
                    library.borrow_item(int(parts[1]), int(user["member_id"]))
                    self._flash(f"تم تسجيل الاستعارة. موعد الإرجاع بعد {library.LOAN_PERIOD_DAYS} أيام.")
                except ValueError as exc:
                    self._flash(str(exc), "error")
                self._redirect("/loans"); return
            self._page("غير متاح", '<section class="error-state"><h1>الاستعارة متاحة لحسابات الأعضاء فقط.</h1></section>', status=403); return

        if path.startswith("/loans/") and path.endswith("/return"):
            parts = path.strip("/").split("/")
            if len(parts) == 3 and parts[1].isdigit():
                member_id = None if user["role"] == "manager" else int(user["member_id"])
                try:
                    library.return_loan(int(parts[1]), member_id)
                    self._flash("تم تأكيد إرجاع المادة بنجاح.")
                except ValueError as exc:
                    self._flash(str(exc), "error")
                self._redirect("/loans"); return

        if path.startswith("/items/") and path.endswith("/delete"):
            parts = path.strip("/").split("/")
            if len(parts) == 3 and parts[1].isdigit() and user["role"] == "manager":
                try:
                    library.delete_item(int(parts[1]))
                    self._flash("تم حذف المادة من الفهرس.")
                except ValueError as exc:
                    self._flash(str(exc), "error")
                self._redirect("/catalog"); return
            self._page("غير مسموح", '<section class="error-state"><h1>هذه العملية للمدير فقط.</h1></section>', status=403); return

        self._redirect("/dashboard")


def run_server(host: str = "127.0.0.1", port: int = 8000) -> None:
    init_db()
    server = ThreadingHTTPServer((host, port), LibraryHandler)
    server.daemon_threads = True
    print("\n  WARAQ · Library Studio")
    print("  ----------------------")
    print(f"  Open: http://{host}:{port}")
    print("  Stop: Ctrl + C\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nWaraq server stopped.")
    finally:
        server.server_close()
