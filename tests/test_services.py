import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

from waraq import library, security, storage


class WaraqServiceTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.original_path = storage.DB_PATH
        storage.DB_PATH = Path(self.temp_dir.name) / "waraq-test.db"
        storage.init_db()

    def tearDown(self):
        storage.DB_PATH = self.original_path
        self.temp_dir.cleanup()

    def test_demo_manager_and_member_authentication(self):
        manager = security.authenticate("admin", "admin123")
        member = security.authenticate("saif_101", "saif123")
        self.assertEqual(manager["role"], "manager")
        self.assertEqual(member["member_id"], 101)
        self.assertIsNone(security.authenticate("admin", "wrong-password"))

    def test_password_hashes_are_salted_and_verified(self):
        first = security.hash_password("sample-password")
        second = security.hash_password("sample-password")
        self.assertNotEqual(first, second)
        self.assertTrue(security.verify_password("sample-password", first))
        self.assertFalse(security.verify_password("bad-password", first))

    def test_seeded_catalog_and_dashboard(self):
        items = library.get_items()
        self.assertEqual(len(items), 3)
        dashboard = library.get_dashboard()
        self.assertEqual(dashboard["stats"]["items"], 3)
        self.assertEqual(dashboard["stats"]["members"], 3)
        self.assertEqual(dashboard["stats"]["available"], 3)

    def test_search_matches_author_publisher_and_id(self):
        self.assertEqual(len(library.get_items(q="Ahmad")), 1)
        self.assertEqual(len(library.get_items(q="ACM")), 1)
        self.assertEqual(library.get_items(q="1")[0]["id"], 1)

    def test_borrow_return_and_duplicate_prevention(self):
        library.borrow_item(1, 101)
        with self.assertRaisesRegex(ValueError, "مستعارة"):
            library.borrow_item(1, 102)
        loans = library.get_loans(101, "active")
        self.assertEqual(len(loans), 1)
        self.assertEqual(loans[0]["due_at"], (date.today() + timedelta(days=7)).isoformat())
        library.return_loan(loans[0]["id"], 101)
        self.assertEqual(library.get_loans(101, "active"), [])
        self.assertEqual(len(library.get_loans(101, "returned")), 1)

    def test_member_cannot_return_another_members_loan(self):
        library.borrow_item(1, 101)
        loan = library.get_loans(101, "active")[0]
        with self.assertRaisesRegex(ValueError, "صلاحية"):
            library.return_loan(loan["id"], 102)
        self.assertEqual(len(library.get_loans(101, "active")), 1)

    def test_three_item_limit(self):
        for item_id in (1, 2, 3):
            library.borrow_item(item_id, 101)
        fourth = library.add_item({
            "item_type": "book", "title": "Fourth Title", "publication_year": "2024",
            "specialization": "Software", "author": "Test", "pages": "100", "publisher": "Test Press"
        })
        with self.assertRaisesRegex(ValueError, "3 مواد"):
            library.borrow_item(fourth, 101)
        self.assertEqual(len(library.get_loans(101, "active")), 3)

    def test_create_member_and_item(self):
        member_id, username = library.add_member("Lina Haddad", "strongpass123")
        self.assertTrue(username.startswith("lina_haddad_"))
        self.assertEqual(security.authenticate(username, "strongpass123")["member_id"], member_id)
        item_id = library.add_item({
            "item_type": "book", "title": "The Design of Everyday Things",
            "publication_year": "2013", "specialization": "Software",
            "author": "Don Norman", "pages": "368", "publisher": "Basic Books",
            "description": "A design classic."
        })
        self.assertEqual(library.get_items(q="Everyday")[0]["id"], item_id)

    def test_invalid_item_data_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "تخصصاً"):
            library.add_item({"item_type": "book", "title": "Nope", "publication_year": "2024", "specialization": "Bad"})
        with self.assertRaisesRegex(ValueError, "سنة النشر"):
            library.add_item({"item_type": "book", "title": "Okay Title", "publication_year": "abc", "specialization": "Software"})
        with self.assertRaises(ValueError):
            library.add_item({"item_type": "book", "title": "x", "publication_year": "2024", "specialization": "Software"})

    def test_delete_protects_loan_history(self):
        library.borrow_item(1, 101)
        with self.assertRaisesRegex(ValueError, "سجل إعارة"):
            library.delete_item(1)
        self.assertEqual(len(library.get_items(q="Deep Learning")), 1)

    def test_password_change_and_demo_reset_preserves_catalog(self):
        security.change_password("admin", "admin123", "my-private-password")
        self.assertIsNotNone(security.authenticate("admin", "my-private-password"))
        security.reset_demo_accounts()
        self.assertIsNotNone(security.authenticate("admin", "admin123"))
        self.assertIsNotNone(security.authenticate("saif_101", "saif123"))
        self.assertEqual(len(library.get_items()), 3)
        self.assertEqual(library.get_dashboard()["stats"]["members"], 3)

    def test_init_repairs_missing_member_login_without_resetting_others(self):
        security.change_password("admin", "admin123", "custom-admin-password")
        with storage.db() as connection:
            connection.execute("DELETE FROM users WHERE member_id=102")
        storage.init_db()
        self.assertIsNotNone(security.authenticate("admin", "custom-admin-password"))
        self.assertIsNotNone(security.authenticate("rida_102", "rida123"))

    def test_production_mode_creates_only_configured_manager(self):
        from unittest.mock import patch
        with patch.object(storage, "DEMO_MODE", False), \
             patch("waraq.config.ADMIN_USERNAME", "library-owner"), \
             patch("waraq.config.ADMIN_PASSWORD", "correct-horse-battery-staple-2026"):
            storage.init_db()
        manager = security.authenticate("library-owner", "correct-horse-battery-staple-2026")
        self.assertIsNotNone(manager)
        self.assertEqual(manager["role"], "manager")
        self.assertIsNone(security.authenticate("admin", "admin123"))
        self.assertIsNone(security.authenticate("saif_101", "saif123"))
        self.assertEqual(library.get_items(), [])
        self.assertEqual(library.get_members(), [])

    def test_production_mode_requires_secure_first_admin_credentials(self):
        from unittest.mock import patch
        with patch.object(storage, "DEMO_MODE", False), \
             patch("waraq.config.ADMIN_USERNAME", ""), \
             patch("waraq.config.ADMIN_PASSWORD", ""):
            with self.assertRaisesRegex(RuntimeError, "WARAQ_ADMIN_USERNAME"):
                storage.init_db()

    def test_demo_reset_is_disabled_outside_demo_mode(self):
        from unittest.mock import patch
        with patch.object(security, "DEMO_MODE", False):
            with self.assertRaisesRegex(RuntimeError, "disabled"):
                security.reset_demo_accounts()

    def test_database_health(self):
        health = storage.database_health()
        self.assertTrue(health["ok"])
        self.assertEqual(health["items"], 3)


if __name__ == "__main__":
    unittest.main()
