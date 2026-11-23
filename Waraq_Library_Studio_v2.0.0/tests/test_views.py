import os
import unittest
from unittest.mock import patch

from waraq import views


class WaraqViewTests(unittest.TestCase):
    def test_login_demo_fill_and_password_visibility_controls(self):
        with patch.dict(os.environ, {"WARAQ_DEMO_MODE": "1"}):
            html = views.login("csrf-token")
        self.assertIn('data-demo-username="admin"', html)
        self.assertIn('data-demo-password="admin123"', html)
        self.assertIn('id="togglePassword"', html)
        self.assertIn('name="csrf" value="csrf-token"', html)

    def test_demo_credentials_can_be_hidden(self):
        with patch.dict(os.environ, {"WARAQ_DEMO_MODE": "0"}):
            html = views.login("csrf-token")
        self.assertNotIn('data-demo-username="admin"', html)
        self.assertNotIn("admin123", html)

    def test_workspace_includes_role_aware_navigation(self):
        manager_html = views.shell("Dashboard", "<h1>Ready</h1>", {"username": "admin", "role": "manager"}, "dashboard", "csrf")
        member_html = views.shell("Dashboard", "<h1>Ready</h1>", {"username": "reader", "role": "member"}, "dashboard", "csrf")
        self.assertIn('href="/members"', manager_html)
        self.assertIn('class="mobile-nav"', manager_html)
        self.assertNotIn('href="/members"', member_html)
        self.assertIn('href="/account"', member_html)

    def test_dynamic_text_is_html_escaped(self):
        html = views.shell("Title", "<p>Safe</p>", {"username": '<img src=x onerror=alert(1)>', "role": "member"}, csrf="token")
        self.assertNotIn('<img src=x onerror=alert(1)>', html)
        self.assertIn("&lt;img", html)


if __name__ == "__main__":
    unittest.main()
