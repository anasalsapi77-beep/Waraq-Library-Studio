"""HTML rendering helpers. Dynamic user content is always HTML-escaped."""
from html import escape
from datetime import date
import os


def esc(value) -> str:
    return escape(str(value if value is not None else ""), quote=True)


def shell(title: str, content: str, user=None, active="dashboard", csrf="", flash=None) -> str:
    flash_html = ""
    if flash:
        kind = "success" if flash[1] == "success" else "error"
        flash_html = f'<div class="flash {kind}" role="status"><span>{esc(flash[0])}</span><button class="flash-close" type="button" aria-label="إغلاق">×</button></div>'
    if user:
        role_label = "مدير المكتبة" if user["role"] == "manager" else "عضو المكتبة"
        nav_items = [
            ("dashboard", "/dashboard", "◫", "نظرة عامة"),
            ("catalog", "/catalog", "▤", "استكشاف الكتب"),
            ("loans", "/loans", "↗", "الإعارات"),
        ]
        if user["role"] == "manager":
            nav_items.append(("members", "/members", "♙", "الأعضاء"))
        nav = "".join(f'<a class="side-link {"active" if active == key else ""}" href="{url}" {"aria-current=page" if active == key else ""}><span class="side-icon">{icon}</span><span>{label}</span></a>' for key, url, icon, label in nav_items)
        mobile_nav = "".join(f'<a class="mobile-nav-link {"active" if active == key else ""}" href="{url}" {"aria-current=page" if active == key else ""}><span>{icon}</span><small>{label}</small></a>' for key, url, icon, label in nav_items)
        mobile_nav += '<a class="mobile-nav-link" href="/account"><span>◉</span><small>حسابي</small></a>'
        main = f'''<div class="app-shell">
          <aside class="sidebar">
            <div class="side-caption">مساحة العمل</div>{nav}
            <div class="sidebar-note"><span class="note-mark">✳</span><strong>مساحة للمعرفة</strong><p>كتابٌ جديد، فكرةٌ جديدة، وبداية أخرى.</p></div>
            <div class="side-profile"><div class="avatar">{esc(user['username'][:1].upper())}</div><div><strong>{esc(user['username'])}</strong><small>{role_label}</small></div></div>
          </aside>
          <main class="main-content"><div class="mobile-page-head"><span>مساحة العمل</span><a href="/catalog">استكشف المكتبة ↗</a></div>{flash_html}{content}</main>
          <nav class="mobile-nav" aria-label="التنقل الرئيسي">{mobile_nav}</nav>
        </div>'''
        header_links = f'''<div class="header-actions"><a class="header-link" href="/catalog">الفهرس</a><a class="top-user" href="/account"><span class="online-dot"></span>{esc(user['username'])}</a><form method="post" action="/logout" class="inline-form"><input type="hidden" name="csrf" value="{esc(csrf)}"><button class="logout-btn" type="submit">خروج</button></form></div>'''
    else:
        main = f'<main class="public-main">{flash_html}{content}</main>'
        header_links = '<nav class="public-nav"><a href="/#about">عن ورق</a><a href="/#features">المزايا</a><a class="button button-small button-dark" href="/login">دخول المكتبة <span>↗</span></a></nav>'
    return f'''<!doctype html>
<html lang="ar" dir="rtl">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="theme-color" content="#18372f"><meta name="color-scheme" content="light"><meta name="description" content="وَرَق — مكتبة رقمية لإدارة الكتب والمشاريع والأعضاء والإعارات، بتجربة عربية أنيقة."><meta property="og:title" content="وَرَق | Waraq Library Studio"><meta property="og:description" content="مساحة رقمية للقراءة والتعلّم وإدارة المعرفة."><meta property="og:type" content="website">
<title>{esc(title)} · ورق</title><link rel="icon" href="/static/img/favicon.svg" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=IBM+Plex+Sans+Arabic:wght@400;500;600;700&family=Playfair+Display:wght@500;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/static/css/styles.css"><script defer src="/static/js/app.js"></script>
</head><body><div class="grain" aria-hidden="true"></div>
<header class="topbar"><a class="brand" href="/"><span class="brand-symbol"><i></i><i></i><i></i></span><span><strong>وَرَق</strong><small>مكتبةٌ تنبض بالحكايات</small></span></a>{header_links}</header>
{main}<footer class="site-footer"><span>وَرَق · مساحةٌ للقراءة والتعلّم</span><span>صُمّم ليجعل إدارة المعرفة أكثر هدوءاً.</span></footer>
</body></html>'''


def landing(csrf="") -> str:
    content = '''<section class="editorial-hero" id="about">
      <div class="editorial-copy">
        <div class="eyebrow"><span class="eyebrow-line"></span> WARAQ LIBRARY · EST. FOR THE CURIOUS</div>
        <div class="hero-edition">مكتبة رقمية · أرشيف المعرفة</div>
        <h1>لكل فكرةٍ<br>رفّ، ولكل قارئٍ<br><em>عالمٌ كامل.</em></h1>
        <p class="hero-lead">اكتشف عناوين تستحق وقتك، استعر بسهولة، وتابع رحلتك بين الكتب والمشاريع في مساحة صُمّمت لتمنح المعرفة حضوراً يليق بها.</p>
        <div class="hero-ctas"><a class="button button-dark" href="/login">ادخل إلى المكتبة <span>←</span></a><a class="text-link" href="#features">اكتشف وَرَق <span>⌄</span></a></div>
        <div class="hero-proof"><span class="proof-line"></span><span>اقرأ بعمق. اكتشف بهدوء. عُد دائماً.</span><span class="proof-issue">VOL. 01 / 2026</span></div>
      </div>
      <div class="editorial-scene" role="img" aria-label="تكوين فني لأربعة كتب على رف مكتبة">
        <div class="scene-halo"></div><div class="scene-moon"></div><div class="scene-orbit scene-orbit-one"></div><div class="scene-orbit scene-orbit-two"></div>
        <div class="scene-arch"></div><div class="scene-shelf"></div>
        <div class="scene-book scene-book-a"><span>THE<br>ART OF<br>THINKING</span><small>W / 01</small></div>
        <div class="scene-book scene-book-b"><span>QUIET<br>WISDOM</span><small>W / 02</small></div>
        <div class="scene-book scene-book-c"><span>DESIGN<br>OF IDEAS</span><small>W / 03</small></div>
        <div class="scene-book scene-book-d"><span>THE<br>GARDEN<br>OF WORDS</span><small>W / 04</small></div>
        <div class="scene-stem stem-a">✳</div><div class="scene-stem stem-b">✧</div>
        <div class="scene-note note-top">A PLACE FOR<br>NEW PERSPECTIVES</div><div class="scene-note note-bottom">THE WARAQ COLLECTION <b>✳</b></div>
        <div class="scene-index">01 <i></i> 04</div>
      </div>
    </section>
    <section class="editorial-ribbon"><span>READ WITH CURIOSITY</span><i>✳</i><span>MAKE ROOM FOR IDEAS</span><i>✳</i><span>RETURN TO WHAT MATTERS</span><i>✳</i><span>READ WITH CURIOSITY</span></section>
    <section class="editorial-intro" id="features"><div class="section-kicker">01 / THE EXPERIENCE</div><div class="editorial-intro-grid"><h2>أكثر من فهرس.<br><em>مساحةٌ للمعرفة.</em></h2><div><p>يجمع وَرَق الكتب والمشاريع والأعضاء والإعارات في تجربة واحدة متوازنة. تفاصيل واضحة للمدير، ومساحة بسيطة للقارئ، وكل حركة محفوظة لتبقى المكتبة مرتبة.</p><a class="under-link" href="/login">ابدأ من هنا <span>←</span></a></div></div>
      <div class="editorial-features"><article class="editorial-feature feature-dark"><div class="feature-head"><span>01 / DISCOVER</span><b>↗</b></div><div class="feature-art feature-art-books"><i></i><i></i><i></i></div><h3>فهرسٌ يتّسع للفضول</h3><p>ابحث عن عنوان أو تخصص، واستكشف الكتب والمشاريع بحسب توفرها.</p></article><article class="editorial-feature feature-sage"><div class="feature-head"><span>02 / BORROW</span><b>↗</b></div><div class="feature-art feature-art-calendar"><strong>07</strong><small>DAYS</small><i>↗</i></div><h3>إعارة واضحة من البداية</h3><p>تابع موعد الإرجاع، واعرف ما استعرت وما يزال بانتظارك.</p></article><article class="editorial-feature feature-clay"><div class="feature-head"><span>03 / MANAGE</span><b>↗</b></div><div class="feature-art feature-art-mark"><span>W</span><i>✳</i></div><h3>إدارةٌ تحافظ على النظام</h3><p>لوحة للمدير لإدارة المواد والأعضاء ومتابعة حركة المكتبة.</p></article></div>
    </section>
    <section class="editorial-quote"><span class="quote-overline">A NOTE TO EVERY READER</span><div class="quote-symbol">“</div><p>في كل كتابٍ باب،<br>وفي كل مكتبةٍ <em>احتمال.</em></p><div class="quote-signature">WARAQ · A QUIET PLACE TO GROW</div><div class="quote-orbit"></div></section>
    <section class="editorial-cta"><div><div class="section-kicker">02 / YOUR NEXT CHAPTER</div><h2>اترك للفضول<br><em>أن يقودك.</em></h2></div><a class="button button-light" href="/login">الدخول إلى وَرَق <span>↗</span></a><span class="cta-seal">W<br><i>✳</i></span></section>'''
    return shell("مساحة للقراءة والتعلّم", content)


def login(csrf: str, flash=None) -> str:
    demo_enabled = os.environ.get("WARAQ_DEMO_MODE", "1").strip().lower() not in ("0", "false", "no", "off")
    demo_panel = ""
    if demo_enabled:
        demo_panel = '''<details class="demo-access"><!-- Local evaluation helper; hide with WARAQ_DEMO_MODE=0 before public hosting. --><summary><span class="demo-key">✳</span><span><strong>تجربة الحسابات التجريبية</strong><small>للتشغيل المحلي ومراجعة المشروع</small></span><b>＋</b></summary>
          <div class="demo-accounts"><button type="button" class="demo-account" data-demo-username="admin" data-demo-password="admin123"><span class="demo-account-icon">A</span><span><strong>مدير المكتبة</strong><small>admin · admin123</small></span><b>استخدم الحساب ←</b></button>
          <button type="button" class="demo-account" data-demo-username="saif_101" data-demo-password="saif123"><span class="demo-account-icon member">S</span><span><strong>عضو المكتبة</strong><small>saif_101 · saif123</small></span><b>استخدم الحساب ←</b></button></div>
          <p class="demo-warning">حسابات للعرض المحلي فقط. عطّل WARAQ_DEMO_MODE قبل أي نشر عام.</p></details>'''
    content = f'''<section class="login-stage">
      <aside class="login-story"><div class="login-story-top"><span>WARAQ / PRIVATE READING ROOM</span><span>NO. 001</span></div><div class="login-story-art"><div class="login-story-glow"></div><div class="login-book login-book-one"><span>THE<br>QUIET<br>ART</span><i>W / 01</i></div><div class="login-book login-book-two"><span>WORDS<br>THAT<br>REMAIN</span><i>W / 02</i></div><div class="login-book login-book-three"><span>NEW<br>HORIZONS</span><i>W / 03</i></div><div class="login-story-orbit"></div></div><div class="login-story-bottom"><strong>هناك دائماً<br>صفحةٌ أولى.</strong><span>READ · DISCOVER · RETURN</span></div></aside>
      <div class="login-card"><div class="login-card-top"><a href="/" class="login-back">← الصفحة الرئيسية</a><span class="login-secure"><i></i> مساحة دخول آمنة</span></div><div class="login-heading"><div class="login-monogram">W<span>✳</span></div><div class="section-kicker">مرحباً بعودتك إلى المكتبة</div><h1>أهلاً بك في<br><em>وَرَق.</em></h1><p>سجّل دخولك لتتابع ما تقرأه، وما ينتظرك على الرف.</p></div>
        <form method="post" action="/login" class="login-form" id="loginForm"><input type="hidden" name="csrf" value="{esc(csrf)}"><label for="loginUsername">اسم المستخدم</label><div class="login-input-wrap"><span>⌁</span><input id="loginUsername" name="username" autocomplete="username" autocapitalize="none" spellcheck="false" required placeholder="اكتب اسم المستخدم"></div><label for="loginPassword">كلمة المرور</label><div class="login-input-wrap password-wrap"><span>◈</span><input id="loginPassword" name="password" type="password" autocomplete="current-password" required placeholder="اكتب كلمة المرور"><button type="button" id="togglePassword" aria-label="إظهار كلمة المرور">إظهار</button></div><button class="button button-dark login-submit" type="submit">دخول إلى المكتبة <span>←</span></button></form>
        {demo_panel}<div class="login-card-footer"><span>WARAQ LIBRARY STUDIO</span><span>مساحةٌ للقراءة والتعلّم</span></div>
      </div>
    </section>'''
    return shell("تسجيل الدخول", content, csrf=csrf, flash=flash)

def dashboard(user: dict, data: dict, csrf: str, flash=None) -> str:
    stats = data["stats"]
    if user["role"] == "manager":
        stat_cards = [
            ("إجمالي المواد", stats["items"], "كتاباً ومشروعاً", "▤", "stat-ink"),
            ("أعضاء المكتبة", stats["members"], "قارئاً مسجّلاً", "♙", "stat-sage"),
            ("إعارات نشطة", stats["active"], "مادة خارج الرف", "↗", "stat-peach"),
            ("متأخرة", stats["overdue"], "تحتاج متابعة", "◷", "stat-alert"),
        ]
        greeting = "أهلاً بك في قلب المكتبة."
        sub = "من هنا تبدأ صورة واضحة عن كل ما يحدث بين الرفوف."
    else:
        stat_cards = [
            ("المواد في المكتبة", stats["items"], "كتاباً ومشروعاً", "▤", "stat-ink"),
            ("كتبي المستعارة", stats["active"], "مادة بحوزتك", "↗", "stat-sage"),
            ("المتاحة الآن", stats["available"], "بانتظار قارئ", "✳", "stat-peach"),
            ("تحتاج إرجاعاً", stats["overdue"], "إعارات متأخرة", "◷", "stat-alert"),
        ]
        greeting = f"مرحباً، {esc(user['username'])}."
        sub = "هذه مساحتك لمتابعة قراءتك واكتشاف ما يستحق وقتك."
    cards = "".join(f'<article class="stat-card {cls}"><div class="stat-top"><span>{label}</span><b>{icon}</b></div><strong class="stat-number">{value}</strong><small>{note}</small></article>' for label,value,note,icon,cls in stat_cards)
    recent_rows = "".join(f'''<tr><td><div class="table-title"><span class="type-dot {r['item_type']}"></span><strong>{esc(r['title'])}</strong></div></td><td>{esc(r['member_name']) if user['role']=='manager' else 'أنت'}</td><td>{esc(r['borrowed_at'])}</td><td><span class="status-pill {'returned' if r['returned_at'] else ('overdue' if r['due_at'] < date.today().isoformat() else 'active')}">{'أُعيدت' if r['returned_at'] else ('متأخرة' if r['due_at'] < date.today().isoformat() else 'نشطة')}</span></td></tr>''' for r in data["recent"])
    if not recent_rows:
        recent_rows = '<tr><td colspan="4"><div class="empty-inline">لا توجد حركة إعارة بعد. البداية تنتظرك.</div></td></tr>'
    quick = '<a class="quick-card" href="/catalog"><span class="quick-icon">⌕</span><span><strong>استكشف الفهرس</strong><small>اعثر على كتابك القادم</small></span><b>←</b></a>'
    if user["role"] == "manager":
        quick += '<a class="quick-card" href="/members"><span class="quick-icon">＋</span><span><strong>إضافة عضو</strong><small>أنشئ حساب قارئ جديد</small></span><b>←</b></a>'
        quick += '<a class="quick-card" href="/catalog#add-item"><span class="quick-icon">✳</span><span><strong>إضافة إلى الفهرس</strong><small>كتاب أو مشروع جديد</small></span><b>←</b></a>'
    else:
        quick += '<a class="quick-card" href="/loans"><span class="quick-icon">◷</span><span><strong>متابعة الإعارات</strong><small>اعرف مواعيد الإرجاع</small></span><b>←</b></a>'
        quick += '<a class="quick-card" href="/catalog?availability=available"><span class="quick-icon">✳</span><span><strong>مواد متاحة</strong><small>اختر ما تقرأ لاحقاً</small></span><b>←</b></a>'
    content = f'''<section class="welcome-banner"><div class="welcome-copy"><div class="eyebrow"><span class="eyebrow-line"></span> {"لوحة المدير" if user['role']=='manager' else "مساحتك الشخصية"}</div><h1>{greeting}</h1><p>{sub}</p><a href="/catalog" class="welcome-link">تصفّح الفهرس <span>←</span></a></div><div class="welcome-still"><div class="still-ring"></div><div class="still-book"><span>W</span></div><span class="still-caption">A QUIET PLACE<br>FOR BIG IDEAS</span><span class="still-star">✳</span></div></section>
    <div class="section-heading"><div><div class="section-kicker">01 / لمحة سريعة</div><h2>المكتبة <em>بالأرقام.</em></h2></div><span class="muted-meta">تحديث مباشر من قاعدة البيانات</span></div>
    <section class="stats-grid">{cards}</section>
    <section class="dashboard-lower"><div class="activity-panel"><div class="panel-heading"><div><div class="section-kicker">02 / آخر الحركة</div><h2>أحدث الإعارات</h2></div><a href="/loans" class="under-link">كل السجلات ←</a></div><div class="table-wrap"><table class="data-table"><thead><tr><th>المادة</th><th>{'العضو' if user['role']=='manager' else 'المستعير'}</th><th>تاريخ الاستعارة</th><th>الحالة</th></tr></thead><tbody>{recent_rows}</tbody></table></div></div><aside class="quick-panel"><div class="section-kicker">03 / اختصارات</div><h2>ماذا تريد <em>أن تفعل؟</em></h2>{quick}</aside></section>'''
    return shell("نظرة عامة", content, user, "dashboard", csrf, flash)


def catalog(user: dict, items: list[dict], csrf: str, filters: dict, flash=None) -> str:
    options = ["Artificial Intelligence", "Networks", "Software", "Basic Sciences"]
    spec_options = '<option value="">كل التخصصات</option>' + ''.join(f'<option value="{esc(x)}" {"selected" if filters.get("specialization")==x else ""}>{esc(x)}</option>' for x in options)
    kind_options = ''.join(f'<option value="{v}" {"selected" if filters.get("type")==v else ""}>{label}</option>' for v,label in [("","كل المواد"),("book","كتب"),("project","مشاريع")])
    avail_options = ''.join(f'<option value="{v}" {"selected" if filters.get("availability")==v else ""}>{label}</option>' for v,label in [("","كل الحالات"),("available","متاحة"),("borrowed","مستعارة")])
    project_years = ''.join(f'<option value="{v}" {"selected" if filters.get("project_year")==v else ""}>{v}</option>' for v in ["Third","Fourth","Graduation"])
    filter_html = f'''<form class="filter-bar" method="get" action="/catalog"><label class="search-field"><span>⌕</span><input name="q" value="{esc(filters.get('q',''))}" placeholder="ابحث عن عنوان، مؤلف، تخصص أو رقم..."></label><select name="type" aria-label="نوع المادة">{kind_options}</select><select name="specialization" aria-label="التخصص">{spec_options}</select><select name="availability" aria-label="الحالة">{avail_options}</select><select name="project_year" aria-label="سنة المشروع"><option value="">كل السنوات</option>{project_years}</select><button class="button button-dark filter-submit">تصفية</button><a class="clear-filters" href="/catalog">إعادة ضبط</a></form>'''
    item_cards = []
    for item in items:
        is_book = item["item_type"] == "book"
        cover_cls = "cover-book" if is_book else "cover-project"
        cover_title = "BOOK / COLLECTION" if is_book else "STUDENT PROJECT"
        sub = f"{esc(item['author'])} · {esc(item['publisher'])}" if is_book else f"{esc(item['project_year'])} · فريق {esc(item['team'])}"
        details = f"{esc(item['pages'])} صفحة" if is_book and item.get("pages") else f"نُشر {esc(item['publication_year'])}"
        badge = '<span class="availability available">متاح للاستعارة</span>' if item["is_available"] else '<span class="availability borrowed">مستعار حالياً</span>'
        if user["role"] == "member":
            action = f'<form method="post" action="/items/{item["id"]}/borrow"><input type="hidden" name="csrf" value="{esc(csrf)}"><button class="borrow-btn" type="submit" {"disabled" if not item["is_available"] else ""}>{"استعر هذا الكتاب ←" if item["is_available"] else "غير متاح حالياً"}</button></form>'
        else:
            action = f'<form method="post" action="/items/{item["id"]}/delete" data-confirm="هل تريد حذف هذه المادة من الفهرس؟"><input type="hidden" name="csrf" value="{esc(csrf)}"><button class="delete-btn" type="submit">حذف المادة</button></form>'
        item_cards.append(f'''<article class="book-card"><div class="book-cover {cover_cls}"><span class="cover-top">WARAQ <i>✳</i></span><span class="cover-type">{cover_title}</span><strong>{esc(item['title'])}</strong><span class="cover-bottom">{esc(item['specialization'])} · {esc(item['publication_year'])}</span><i class="cover-stamp">W</i></div><div class="book-info"><div class="book-meta"><span class="type-label">{"كتاب" if is_book else "مشروع"} · #{item['id']}</span>{badge}</div><h3>{esc(item['title'])}</h3><p class="book-sub">{sub or esc(item['specialization'])}</p><div class="book-foot"><span>{details}</span>{action}</div></div></article>''')
    if not item_cards:
        item_cards = ['<div class="empty-state"><span>⌕</span><h3>لم نعثر على نتائج.</h3><p>جرّب كلمة بحث أخرى أو غيّر خيارات التصفية.</p><a class="under-link" href="/catalog">عرض كل المواد ←</a></div>']
    add_form = ""
    if user["role"] == "manager":
        add_form = '''<section class="add-item-panel" id="add-item"><div class="panel-heading"><div><div class="section-kicker">02 / توسيع المجموعة</div><h2>أضف مادة <em>جديدة.</em></h2><p>أدخل بيانات الكتاب أو المشروع ليظهر فوراً في الفهرس.</p></div><span class="add-panel-icon">＋</span></div><form method="post" action="/items/add" class="admin-form"><input type="hidden" name="csrf" value="'''+esc(csrf)+'''"><div class="form-grid"><label>نوع المادة<select name="item_type" id="itemType"><option value="book">كتاب</option><option value="project">مشروع</option></select></label><label class="span-two">العنوان<input name="title" required maxlength="120" placeholder="اسم الكتاب أو المشروع"></label><label>سنة النشر<input name="publication_year" type="number" min="1000" max="'''+str(date.today().year+2)+'''" required placeholder="2026"></label><label>التخصص<select name="specialization" required><option value="">اختر التخصص</option>'''+''.join(f'<option>{x}</option>' for x in options)+'''</select></label><label class="book-only">المؤلف<input name="author" placeholder="اسم المؤلف"></label><label class="book-only">عدد الصفحات<input name="pages" type="number" min="1" placeholder="عدد الصفحات"></label><label class="book-only">دار النشر<input name="publisher" placeholder="دار النشر"></label><label class="project-only hidden">السنة الدراسية<select name="project_year"><option value="Third">Third</option><option value="Fourth">Fourth</option><option value="Graduation">Graduation</option></select></label><label class="project-only hidden">الفريق<input name="team" placeholder="اسم الفريق"></label><label class="span-two">نبذة قصيرة<textarea name="description" rows="2" placeholder="ما الذي يميز هذه المادة؟"></textarea></label></div><div class="form-actions"><span>ستظهر المادة في الفهرس بعد الحفظ.</span><button class="button button-dark" type="submit">إضافة إلى المكتبة <span>←</span></button></div></form></section>'''
    heading = '<div class="section-kicker">01 / مجموعة المعرفة</div><h1>الفهرس <em>المفتوح.</em></h1><p class="page-lead">كل عنوان يقود إلى فكرة، وكل تخصص يفتح باباً جديداً.</p>'
    content = f'''<section class="page-heading-row"><div>{heading}</div><div class="catalog-count"><strong>{len(items):02d}</strong><span>نتيجة<br>في الفهرس</span></div></section>{filter_html}<section class="catalog-grid">{''.join(item_cards)}</section>{add_form}'''
    return shell("الفهرس", content, user, "catalog", csrf, flash)


def members(user: dict, rows: list[dict], csrf: str, flash=None) -> str:
    cards = []
    for m in rows:
        cards.append(f'''<article class="member-card"><div class="member-avatar">{esc(m['name'][:1])}</div><div class="member-info"><h3>{esc(m['name'])}</h3><span>@{esc(m['username'] or '—')} · رقم العضوية {m['id']}</span></div><div class="member-stats"><strong>{m['active_loans']}</strong><small>إعارات نشطة</small></div><div class="member-stats"><strong>{m['total_loans']}</strong><small>إجمالي الإعارات</small></div></article>''')
    if not cards:
        cards = ['<div class="empty-state"><h3>لا يوجد أعضاء حتى الآن.</h3></div>']
    content = f'''<section class="page-heading-row"><div><div class="section-kicker">01 / مجتمع ورق</div><h1>وجوهٌ تقرأ، <em>وأفكارٌ تنمو.</em></h1><p class="page-lead">إدارة أعضاء المكتبة ومتابعة نشاط الاستعارة.</p></div><div class="catalog-count"><strong>{len(rows):02d}</strong><span>عضو<br>مسجّل</span></div></section>
    <section class="member-layout"><div class="member-list"><div class="panel-heading"><div><div class="section-kicker">قائمة القرّاء</div><h2>أعضاء المكتبة</h2></div><span class="muted-meta">{len(rows)} أعضاء</span></div>{''.join(cards)}</div>
    <aside class="member-create"><div class="section-kicker">إضافة قارئ</div><h2>وجهٌ جديد<br><em>في المكتبة.</em></h2><p>أنشئ حساباً للعضو حتى يتمكن من الدخول واستعارة المواد.</p><form method="post" action="/members/add" class="form-stack"><input type="hidden" name="csrf" value="{esc(csrf)}"><label>اسم العضو<input name="name" required minlength="2" placeholder="الاسم الكامل"></label><label>كلمة المرور المؤقتة<input name="password" type="password" required minlength="8" placeholder="8 أحرف على الأقل"></label><button class="button button-dark button-wide" type="submit">إنشاء حساب عضو <span>←</span></button></form></aside></section>'''
    return shell("الأعضاء", content, user, "members", csrf, flash)


def loans(user: dict, rows: list[dict], csrf: str, status: str, flash=None) -> str:
    filters = ''.join(f'<a class="loan-filter {"active" if status==v else ""}" href="/loans?status={v}">{label}</a>' for v,label in [("active","النشطة"),("overdue","المتأخرة"),("returned","المُعادة"),("all","الكل")])
    trs = []
    for r in rows:
        overdue = not r["returned_at"] and r["due_at"] < date.today().isoformat()
        state = "مُعادة" if r["returned_at"] else ("متأخرة" if overdue else "نشطة")
        state_cls = "returned" if r["returned_at"] else ("overdue" if overdue else "active")
        return_btn = ""
        if not r["returned_at"]:
            return_btn = f'<form method="post" action="/loans/{r["id"]}/return"><input type="hidden" name="csrf" value="{esc(csrf)}"><button class="table-action" type="submit">تأكيد الإرجاع</button></form>'
        trs.append(f'''<tr><td><strong>{esc(r['title'])}</strong><small class="table-sub">{ 'كتاب' if r['item_type']=='book' else 'مشروع' } · #{r['item_id']}</small></td><td>{esc(r['member_name'])}</td><td>{esc(r['borrowed_at'])}</td><td>{esc(r['due_at'])}</td><td><span class="status-pill {state_cls}">{state}</span></td><td>{return_btn or '<span class="muted-meta">—</span>'}</td></tr>''')
    if not trs:
        trs = ['<tr><td colspan="6"><div class="empty-inline">لا توجد سجلات ضمن هذا التصنيف.</div></td></tr>']
    content = f'''<section class="page-heading-row"><div><div class="section-kicker">01 / حركة المكتبة</div><h1>لكل كتاب <em>موعد عودة.</em></h1><p class="page-lead">متابعة الاستعارات وتواريخ الإرجاع وحالة كل مادة.</p></div><div class="catalog-count"><strong>{len(rows):02d}</strong><span>سجل<br>معروض</span></div></section><div class="loan-tabs">{filters}</div><section class="activity-panel loans-panel"><div class="table-wrap"><table class="data-table loans-table"><thead><tr><th>المادة</th><th>العضو</th><th>تاريخ الاستعارة</th><th>موعد الإرجاع</th><th>الحالة</th><th>الإجراء</th></tr></thead><tbody>{''.join(trs)}</tbody></table></div></section><div class="loan-note"><span>◷</span><p>مدة الاستعارة الافتراضية <strong>7 أيام</strong>، ويمكن لكل عضو استعارة ما يصل إلى <strong>3 مواد</strong> في الوقت نفسه.</p></div>'''
    return shell("الإعارات", content, user, "loans", csrf, flash)


def account(user: dict, csrf: str, flash=None) -> str:
    content = f'''<section class="page-heading-row"><div><div class="section-kicker">مساحتك · إعدادات الحساب</div><h1>حسابك، <em>بأمان.</em></h1><p class="page-lead">حدّث كلمة المرور الخاصة بك متى احتجت.</p></div></section>
    <section class="account-panel"><div class="account-intro"><span class="account-avatar">{esc(user['username'][:1].upper())}</span><div><strong>{esc(user['username'])}</strong><small>{'مدير المكتبة' if user['role']=='manager' else 'عضو المكتبة'}</small></div></div><form method="post" action="/account/password" class="form-stack"><input type="hidden" name="csrf" value="{esc(csrf)}"><label>كلمة المرور الحالية<input name="current_password" type="password" autocomplete="current-password" required></label><label>كلمة المرور الجديدة<input name="new_password" type="password" minlength="8" autocomplete="new-password" required></label><label>تأكيد كلمة المرور الجديدة<input name="confirm_password" type="password" minlength="8" autocomplete="new-password" required></label><button class="button button-dark" type="submit">حفظ كلمة المرور <span>←</span></button></form></section>'''
    return shell("إعدادات الحساب", content, user, "account", csrf, flash)
