import http.cookiejar
import re
import tempfile
import threading
import unittest
import urllib.error
import urllib.parse
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

from waraq import web
from waraq import storage


class WebFlowTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.original_path = storage.DB_PATH
        storage.DB_PATH = Path(self.temp_dir.name) / "http-test.db"
        storage.init_db()
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), web.LibraryHandler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base = f"http://127.0.0.1:{self.server.server_port}"
        self.cookies = http.cookiejar.CookieJar()
        self.client = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.cookies))
        web.SESSIONS.clear()
        web.LOGIN_FAILURES.clear()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        storage.DB_PATH = self.original_path
        self.temp_dir.cleanup()
        web.SESSIONS.clear()
        web.LOGIN_FAILURES.clear()

    def csrf(self, path="/login"):
        page = self.client.open(self.base + path).read().decode("utf-8")
        token = re.search(r'name="csrf" value="([^"]+)"', page).group(1)
        return token, page

    def post(self, path, payload):
        request = urllib.request.Request(self.base + path,
            data=urllib.parse.urlencode(payload).encode("utf-8"), method="POST")
        return self.client.open(request)

    def login(self, username="admin", password="admin123"):
        token, _ = self.csrf("/login")
        return self.post("/login", {"csrf": token, "username": username, "password": password})

    def test_landing_health_and_static_assets(self):
        landing = self.client.open(self.base + "/").read().decode("utf-8")
        self.assertIn("لكل فكرةٍ", landing)
        health = self.client.open(self.base + "/health").read().decode("utf-8")
        self.assertIn('"status": "ok"', health)
        css = self.client.open(self.base + "/static/css/styles.css").read()
        self.assertIn(b"mobile-nav", css)

    def test_manager_can_login_and_open_dashboard(self):
        response = self.login()
        dashboard = response.read().decode("utf-8")
        self.assertTrue(response.url.endswith("/dashboard"))
        self.assertIn("لوحة المدير", dashboard)
        self.assertIn("إجمالي المواد", dashboard)

    def test_member_can_login_and_open_dashboard(self):
        response = self.login("saif_101", "saif123")
        dashboard = response.read().decode("utf-8")
        self.assertTrue(response.url.endswith("/dashboard"))
        self.assertIn("مساحتك الشخصية", dashboard)

    def test_failed_login_returns_clear_message(self):
        response = self.login("admin", "bad-password")
        self.assertTrue(response.url.endswith("/login"))
        self.assertIn("اسم المستخدم أو كلمة المرور غير صحيحة", response.read().decode("utf-8"))

    def test_member_is_forbidden_from_manager_pages(self):
        self.login("saif_101", "saif123")
        with self.assertRaises(urllib.error.HTTPError) as error:
            self.client.open(self.base + "/members")
        self.assertEqual(error.exception.code, 403)

    def test_manager_routes_render_and_manager_can_add_member(self):
        self.login()
        for route in ("/dashboard", "/catalog", "/members", "/loans", "/account"):
            response = self.client.open(self.base + route)
            self.assertEqual(response.status, 200, route)
        token, _ = self.csrf("/members")
        response = self.post("/members/add", {"csrf": token, "name": "Maya Reader", "password": "maya-pass-123"})
        self.assertTrue(response.url.endswith("/members"))
        from waraq.security import authenticate
        self.assertIsNotNone(authenticate("maya_reader_104", "maya-pass-123"))

    def test_member_borrow_and_return_flow(self):
        from waraq import library
        item_id = library.add_item({
            "item_type": "book", "title": "A New Reading Journey", "publication_year": "2024",
            "specialization": "Software", "author": "Test Author", "pages": "180", "publisher": "Waraq Press"
        })
        self.login("saif_101", "saif123")
        token, _ = self.csrf("/catalog")
        response = self.post(f"/items/{item_id}/borrow", {"csrf": token})
        self.assertTrue(response.url.endswith("/loans"))
        active = library.get_loans(101, "active")
        self.assertEqual(len(active), 1)
        token, _ = self.csrf("/loans")
        response = self.post(f"/loans/{active[0]['id']}/return", {"csrf": token})
        self.assertTrue(response.url.endswith("/loans"))
        self.assertEqual(library.get_loans(101, "active"), [])
        self.assertEqual(len(library.get_loans(101, "returned")), 1)

    def test_repeated_failed_logins_are_throttled(self):
        for _ in range(web.LOGIN_MAX_FAILURES):
            self.login("unknown-user", "wrong-password")
        response = self.login("unknown-user", "wrong-password")
        self.assertIn("محاولات كثيرة", response.read().decode("utf-8"))

    def test_post_without_csrf_is_rejected(self):
        request = urllib.request.Request(self.base + "/login", data=b"username=admin&password=admin123", method="POST")
        with self.assertRaises(urllib.error.HTTPError) as error:
            self.client.open(request)
        self.assertEqual(error.exception.code, 403)

    def test_login_rotates_session_identifier(self):
        self.csrf("/login")
        before = next(cookie.value for cookie in self.cookies if cookie.name == "waraq_session")
        self.login()
        after = next(cookie.value for cookie in self.cookies if cookie.name == "waraq_session")
        self.assertNotEqual(before, after)

    def test_logout_returns_to_login(self):
        self.login()
        token, _ = self.csrf("/dashboard")
        response = self.post("/logout", {"csrf": token})
        self.assertTrue(response.url.endswith("/login"))


if __name__ == "__main__":
    unittest.main()
