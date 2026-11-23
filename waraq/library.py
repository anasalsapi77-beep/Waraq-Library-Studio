"""Library catalogue, member, dashboard and lending services."""
from __future__ import annotations

import re
from datetime import date, timedelta
from typing import Any

from .storage import db

LOAN_PERIOD_DAYS = 7
MAX_ACTIVE_LOANS = 3
SPECIALIZATIONS = ("Artificial Intelligence", "Networks", "Software", "Basic Sciences")
PROJECT_YEARS = ("Third", "Fourth", "Graduation")


def get_dashboard(member_id: int | None = None) -> dict[str, Any]:
    today = date.today().isoformat()
    with db() as connection:
        common = {
            "items": connection.execute("SELECT COUNT(*) FROM items").fetchone()[0],
            "books": connection.execute("SELECT COUNT(*) FROM items WHERE item_type='book'").fetchone()[0],
            "projects": connection.execute("SELECT COUNT(*) FROM items WHERE item_type='project'").fetchone()[0],
            "available": connection.execute("""SELECT COUNT(*) FROM items i
                WHERE NOT EXISTS (SELECT 1 FROM loans l WHERE l.item_id=i.id AND l.returned_at IS NULL)""").fetchone()[0],
        }
        if member_id is None:
            stats = {
                **common,
                "members": connection.execute("SELECT COUNT(*) FROM members").fetchone()[0],
                "active": connection.execute("SELECT COUNT(*) FROM loans WHERE returned_at IS NULL").fetchone()[0],
                "overdue": connection.execute("SELECT COUNT(*) FROM loans WHERE returned_at IS NULL AND due_at < ?", (today,)).fetchone()[0],
            }
            recent = connection.execute("""SELECT l.*, i.title, i.item_type, m.name AS member_name
                FROM loans l JOIN items i ON i.id=l.item_id JOIN members m ON m.id=l.member_id
                ORDER BY l.id DESC LIMIT 8""").fetchall()
        else:
            stats = {
                **common,
                "active": connection.execute("SELECT COUNT(*) FROM loans WHERE member_id=? AND returned_at IS NULL", (member_id,)).fetchone()[0],
                "overdue": connection.execute("SELECT COUNT(*) FROM loans WHERE member_id=? AND returned_at IS NULL AND due_at < ?", (member_id, today)).fetchone()[0],
            }
            recent = connection.execute("""SELECT l.*, i.title, i.item_type, m.name AS member_name
                FROM loans l JOIN items i ON i.id=l.item_id JOIN members m ON m.id=l.member_id
                WHERE l.member_id=? ORDER BY l.id DESC LIMIT 8""", (member_id,)).fetchall()
    return {"stats": stats, "recent": [dict(row) for row in recent]}


def get_items(q: str = "", item_type: str = "", specialization: str = "", availability: str = "", project_year: str = "") -> list[dict]:
    sql = """SELECT i.*,
        CASE WHEN EXISTS(SELECT 1 FROM loans l WHERE l.item_id=i.id AND l.returned_at IS NULL) THEN 0 ELSE 1 END AS is_available,
        (SELECT l.member_id FROM loans l WHERE l.item_id=i.id AND l.returned_at IS NULL LIMIT 1) AS borrower_id
        FROM items i WHERE 1=1"""
    params: list[Any] = []
    query = q.strip()[:100]
    if query:
        sql += " AND (i.title LIKE ? OR i.specialization LIKE ? OR i.author LIKE ? OR i.publisher LIKE ? OR i.team LIKE ? OR CAST(i.id AS TEXT)=?)"
        params.extend([f"%{query}%"] * 5 + [query])
    if item_type in ("book", "project"):
        sql += " AND i.item_type=?"; params.append(item_type)
    if specialization in SPECIALIZATIONS:
        sql += " AND i.specialization=?"; params.append(specialization)
    if availability == "available":
        sql += " AND NOT EXISTS(SELECT 1 FROM loans l WHERE l.item_id=i.id AND l.returned_at IS NULL)"
    elif availability == "borrowed":
        sql += " AND EXISTS(SELECT 1 FROM loans l WHERE l.item_id=i.id AND l.returned_at IS NULL)"
    if project_year in PROJECT_YEARS:
        sql += " AND i.item_type='project' AND i.project_year=?"; params.append(project_year)
    sql += " ORDER BY i.id DESC"
    with db() as connection:
        return [dict(row) for row in connection.execute(sql, params).fetchall()]


def add_item(data: dict[str, str]) -> int:
    item_type = data.get("item_type", "book").strip()
    title = data.get("title", "").strip()
    specialization = data.get("specialization", "").strip()
    if item_type not in ("book", "project"):
        raise ValueError("اختر نوع مادة صالحاً.")
    if not 2 <= len(title) <= 120:
        raise ValueError("عنوان المادة يجب أن يكون بين حرفين و120 حرفاً.")
    if specialization not in SPECIALIZATIONS:
        raise ValueError("اختر تخصصاً من القائمة.")
    try:
        year = int(data.get("publication_year", ""))
    except (TypeError, ValueError):
        raise ValueError("سنة النشر يجب أن تكون رقماً.")
    if year < 1000 or year > date.today().year + 2:
        raise ValueError("سنة النشر خارج النطاق المقبول.")
    pages = None
    if item_type == "book" and data.get("pages", "").strip():
        try:
            pages = int(data["pages"])
        except ValueError:
            raise ValueError("عدد الصفحات يجب أن يكون رقماً.")
        if not 1 <= pages <= 100_000:
            raise ValueError("عدد الصفحات يجب أن يكون بين 1 و100000.")
    project_year = data.get("project_year", "") if item_type == "project" else ""
    if item_type == "project" and project_year not in PROJECT_YEARS:
        raise ValueError("اختر السنة الدراسية للمشروع.")
    values = (
        item_type, title, year, specialization, data.get("description", "").strip()[:1200],
        data.get("author", "").strip()[:120], pages, data.get("publisher", "").strip()[:120],
        project_year, data.get("team", "").strip()[:120] if item_type == "project" else "",
    )
    with db() as connection:
        cursor = connection.execute("""INSERT INTO items
            (item_type,title,publication_year,specialization,description,author,pages,publisher,project_year,team)
            VALUES (?,?,?,?,?,?,?,?,?,?)""", values)
        return int(cursor.lastrowid)


def add_member(name: str, password: str) -> tuple[int, str]:
    from .security import hash_password

    name = (name or "").strip()
    if not 2 <= len(name) <= 100:
        raise ValueError("اسم العضو يجب أن يكون بين حرفين و100 حرف.")
    if len(password or "") < 8 or len(password) > 128:
        raise ValueError("كلمة المرور يجب أن تكون بين 8 و128 حرفاً.")
    slug = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_") or "member"
    with db() as connection:
        cursor = connection.execute("INSERT INTO members(name) VALUES (?)", (name,))
        member_id = int(cursor.lastrowid)
        username = f"{slug[:40]}_{member_id}"
        connection.execute("INSERT INTO users(username,password_hash,role,member_id) VALUES (?,?,'member',?)",
                           (username, hash_password(password), member_id))
    return member_id, username


def get_members() -> list[dict]:
    with db() as connection:
        rows = connection.execute("""SELECT m.id,m.name,m.created_at,u.username,
            COUNT(CASE WHEN l.returned_at IS NULL THEN 1 END) AS active_loans,
            COUNT(l.id) AS total_loans
            FROM members m LEFT JOIN users u ON u.member_id=m.id
            LEFT JOIN loans l ON l.member_id=m.id
            GROUP BY m.id ORDER BY m.id DESC""").fetchall()
    return [dict(row) for row in rows]


def borrow_item(item_id: int, member_id: int) -> None:
    with db() as connection:
        connection.execute("BEGIN IMMEDIATE")
        if not connection.execute("SELECT 1 FROM items WHERE id=?", (item_id,)).fetchone():
            raise ValueError("لم يتم العثور على المادة المطلوبة.")
        if not connection.execute("SELECT 1 FROM members WHERE id=?", (member_id,)).fetchone():
            raise ValueError("لم يتم العثور على العضو.")
        if connection.execute("SELECT 1 FROM loans WHERE item_id=? AND returned_at IS NULL", (item_id,)).fetchone():
            raise ValueError("هذه المادة مستعارة حالياً.")
        active = connection.execute("SELECT COUNT(*) FROM loans WHERE member_id=? AND returned_at IS NULL", (member_id,)).fetchone()[0]
        if active >= MAX_ACTIVE_LOANS:
            raise ValueError(f"وصلت إلى الحد الأقصى للاستعارة ({MAX_ACTIVE_LOANS} مواد).")
        today = date.today()
        connection.execute("INSERT INTO loans(item_id,member_id,borrowed_at,due_at) VALUES (?,?,?,?)",
                           (item_id, member_id, today.isoformat(), (today + timedelta(days=LOAN_PERIOD_DAYS)).isoformat()))


def return_loan(loan_id: int, member_id: int | None = None) -> None:
    with db() as connection:
        connection.execute("BEGIN IMMEDIATE")
        sql = "SELECT id FROM loans WHERE id=? AND returned_at IS NULL"
        params: list[Any] = [loan_id]
        if member_id is not None:
            sql += " AND member_id=?"; params.append(member_id)
        if not connection.execute(sql, params).fetchone():
            raise ValueError("سجل الإعارة غير موجود أو لا تملك صلاحية إرجاعه.")
        connection.execute("UPDATE loans SET returned_at=? WHERE id=?", (date.today().isoformat(), loan_id))


def get_loans(member_id: int | None = None, status: str = "active") -> list[dict]:
    sql = """SELECT l.*,i.title,i.item_type,i.specialization,m.name AS member_name,m.id AS member_number
        FROM loans l JOIN items i ON i.id=l.item_id JOIN members m ON m.id=l.member_id WHERE 1=1"""
    params: list[Any] = []
    if member_id is not None:
        sql += " AND l.member_id=?"; params.append(member_id)
    if status == "active": sql += " AND l.returned_at IS NULL"
    elif status == "returned": sql += " AND l.returned_at IS NOT NULL"
    elif status == "overdue": sql += " AND l.returned_at IS NULL AND l.due_at < ?"; params.append(date.today().isoformat())
    elif status not in ("all", "active", "returned", "overdue"):
        raise ValueError("حالة الإعارة غير صالحة.")
    sql += " ORDER BY CASE WHEN l.returned_at IS NULL THEN 0 ELSE 1 END, l.due_at ASC, l.id DESC"
    with db() as connection:
        return [dict(row) for row in connection.execute(sql, params).fetchall()]


def delete_item(item_id: int) -> None:
    with db() as connection:
        if connection.execute("SELECT 1 FROM loans WHERE item_id=?", (item_id,)).fetchone():
            raise ValueError("لا يمكن حذف مادة لها سجل إعارة؛ احتفظ بها للحفاظ على سجل المكتبة.")
        cursor = connection.execute("DELETE FROM items WHERE id=?", (item_id,))
        if cursor.rowcount == 0:
            raise ValueError("المادة غير موجودة.")
