import os
import sys
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            super().showPage()
        super().save()

    def draw_page_number(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748b"))
        
        # Header rule & text (on all pages)
        self.setStrokeColor(colors.HexColor("#e2e8f0"))
        self.setLineWidth(0.75)
        self.line(40, 755, 612 - 40, 755)
        self.drawString(40, 760, "LinkVault · 3-Member Mentor Presentation & Technical Defense Guide")
        
        # Footer rule & text
        self.line(40, 38, 612 - 40, 38)
        self.drawString(40, 26, "LinkVault Platform Architecture · Screen-by-Screen Walkthrough")
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(612 - 40, 26, page_str)
        self.restoreState()


def build_roadmap_pdf(filename="LinkVault_Mentor_Presentation_Roadmap.pdf"):
    # 40pt margins give 532pt usable width and 710pt usable height
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        leftMargin=40,
        rightMargin=40,
        topMargin=46,
        bottomMargin=46
    )

    styles = getSampleStyleSheet()

    # Typography styles tailored for executive readability
    title_style = ParagraphStyle(
        "CoverTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#0f172a"),
        spaceAfter=4
    )

    subtitle_style = ParagraphStyle(
        "CoverSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=15,
        textColor=colors.HexColor("#2563eb"),
        spaceAfter=8
    )

    meta_style = ParagraphStyle(
        "CoverMeta",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=13,
        textColor=colors.HexColor("#475569"),
        spaceAfter=8
    )

    sec_title = ParagraphStyle(
        "SectionTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=16,
        textColor=colors.HexColor("#0f172a"),
        spaceBefore=8,
        spaceAfter=4,
        keepWithNext=True
    )

    role_badge = ParagraphStyle(
        "RoleBadge",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9.5,
        leading=13,
        textColor=colors.HexColor("#1d4ed8"),
        spaceAfter=6
    )

    h3_style = ParagraphStyle(
        "Heading3_Custom",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#1e293b"),
        spaceBefore=5,
        spaceAfter=3,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        "Body_Custom",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor("#334155"),
        spaceAfter=4
    )

    bullet_style = ParagraphStyle(
        "Bullet_Custom",
        parent=body_style,
        leftIndent=12,
        firstLineIndent=-8,
        spaceAfter=3
    )

    script_box_header = ParagraphStyle(
        "ScriptBoxHeader",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#1e40af"),
        spaceAfter=4
    )

    script_text = ParagraphStyle(
        "ScriptText",
        parent=styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=8.2,
        leading=11.8,
        textColor=colors.HexColor("#1e3a8a"),
        spaceAfter=3
    )

    table_header = ParagraphStyle(
        "TableHeader",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=10,
        textColor=colors.white
    )

    table_cell = ParagraphStyle(
        "TableCell",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=7.8,
        leading=10.5,
        textColor=colors.HexColor("#1e293b")
    )

    table_cell_bold = ParagraphStyle(
        "TableCellBold",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=7.8,
        leading=10.5,
        textColor=colors.HexColor("#0f172a")
    )

    def make_box(title, text_paragraphs, bg="#f8fafc", border="#cbd5e1"):
        items = [Paragraph(title, script_box_header)]
        for p in text_paragraphs:
            if isinstance(p, str):
                items.append(Paragraph(p, script_text))
            else:
                items.append(p)
        t = Table([[items]], colWidths=[532])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(bg)),
            ("BOX", (0, 0), (-1, -1), 1, colors.HexColor(border)),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ]))
        return t

    story = []

    # ═══════════════════════════════════════════════════════════════════════════
    # PAGE 1: OVERVIEW & MEMBER 1 (ENTRYWAY: LANDING & AUTH)
    # ═══════════════════════════════════════════════════════════════════════════
    story.append(Paragraph("LinkVault · Technical Presentation Roadmap", title_style))
    story.append(Paragraph("3-Member Screen-by-Screen Walkthrough & Mentor Defense Guide", subtitle_style))
    story.append(Paragraph(
        "<b>Stack:</b> Flask 3.1 · Python 3.12 · PostgreSQL · SQLAlchemy 2.0 · Gunicorn · Render Cloud<br/>"
        "<b>Structure:</b> Member 1 (The Entryway) ➔ Member 2 (The Core Product) ➔ Member 3 (The Engine & Cloud)",
        meta_style
    ))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#2563eb"), spaceAfter=8))

    # Summary table
    sum_data = [
        [
            Paragraph("Member / Speaker", table_header),
            Paragraph("Presentation Domain", table_header),
            Paragraph("Live Screens & Components Demonstrated", table_header),
            Paragraph("Time", table_header),
        ],
        [
            Paragraph("<b>Member 1</b><br/>The Entryway", table_cell),
            Paragraph("Frontend UI/UX, Onboarding & Auth Security", table_cell),
            Paragraph("• Landing Page (<code>landing.html</code>)<br/>• Register & Login Pages (<code>login.html</code>)<br/>• Password hashing (PBKDF2-SHA256) & sessions", table_cell),
            Paragraph("2.0 min", table_cell_bold),
        ],
        [
            Paragraph("<b>Member 2</b><br/>The Core Product", table_cell),
            Paragraph("Dashboard System, Search & Team Hub", table_cell),
            Paragraph("• Home Dashboard & Categories (<code>index.html</code>)<br/>• Instant Search (inline ✕ clear & Escape reset)<br/>• Team Hub Sidebar & Workspaces (<code>workspace.html</code>)", table_cell),
            Paragraph("2.5 min", table_cell_bold),
        ],
        [
            Paragraph("<b>Member 3</b><br/>The Engine & Cloud", table_cell),
            Paragraph("Backend APIs, ORM Schema & Cloud Hosting", table_cell),
            Paragraph("• Flask Application Factory (<code>app.py</code>)<br/>• Relational Models & Cascades (<code>models.py</code>)<br/>• PostgreSQL Pooling & Live Render Deployment", table_cell),
            Paragraph("2.5 min", table_cell_bold),
        ],
    ]
    sum_table = Table(sum_data, colWidths=[90, 145, 245, 52])
    sum_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#ffffff"), colors.HexColor("#f8fafc")]),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(sum_table)
    story.append(Spacer(1, 8))

    # Member 1 Content
    story.append(Paragraph("1. MEMBER 1: The Entryway (Landing Page & Authentication)", sec_title))
    story.append(Paragraph("Role: Frontend UI/UX Architect & Authentication Specialist", role_badge))
    story.append(Paragraph("<b>Live Screens to Show:</b>", h3_style))
    story.append(Paragraph("• <b>Landing Page (<code>/</code> logged out):</b> Clean hero section, feature grid, and zero-framework design tokens in <code>templates/landing.html</code>.", bullet_style))
    story.append(Paragraph("• <b>Register Page (<code>/register</code>):</b> Input fields, client-side validation, error handling for duplicate emails in <code>templates/register.html</code>.", bullet_style))
    story.append(Paragraph("• <b>Login Page (<code>/login</code>):</b> Form submission, flash feedback, and seamless redirect to authenticated dashboard in <code>templates/login.html</code>.", bullet_style))

    story.append(Paragraph("<b>Key Technical Explanations:</b>", h3_style))
    story.append(Paragraph("• <b>Design System:</b> Vanilla CSS variables (<code>--bg-primary</code>, <code>--accent-primary</code>) and Google Fonts (Inter) providing high contrast with zero CSS framework bloat.", bullet_style))
    story.append(Paragraph("• <b>PBKDF2-SHA256 Password Hashing:</b> Passwords hashed in <code>models.py</code> via Werkzeug; raw passwords are never stored.", bullet_style))
    story.append(Paragraph("• <b>Flask-Login Session Model:</b> Signed HTTP-only session cookies with <code>@login_required</code> route authorization.", bullet_style))

    m1_box = [
        "\"Good morning, Sir/Madam. I will be introducing LinkVault and walking you through our user onboarding and authentication architecture.",
        "LinkVault is designed to eliminate bookmark clutter and empower team resource sharing. When visitors first arrive, they see our responsive <b>Landing Page</b> (<code>landing.html</code>), built using custom CSS tokens and Inter typography for optimal contrast and zero library overhead.",
        "From here, users can create an account or sign in. Behind our <b>Login and Registration forms</b> (<code>login.html</code>), security is strictly enforced. We hash all passwords using salted PBKDF2-SHA256 in <code>models.py</code> before they touch the database. Once authenticated, <code>Flask-Login</code> creates a secure session cookie protecting our internal routes.",
        "Now that we have successfully logged in, I will hand over to [Member 2] to demonstrate our core dashboard, search engine, and team collaboration system.\""
    ]
    story.append(make_box("🎙️ MEMBER 1 SPEAKING SCRIPT (Word-for-Word Walkthrough)", m1_box, bg="#f0fdf4", border="#86efac"))

    story.append(PageBreak())

    # ═══════════════════════════════════════════════════════════════════════════
    # PAGE 2: MEMBER 2 (CORE PRODUCT: DASHBOARD, SEARCH & TEAMS)
    # ═══════════════════════════════════════════════════════════════════════════
    story.append(Paragraph("2. MEMBER 2: The Core Product (Home Dashboard & Team Workspaces)", sec_title))
    story.append(Paragraph("Role: Product Experience Architect & Team Collaboration Engineer", role_badge))
    story.append(Paragraph(
        "Member 2 takes over immediately upon login to demonstrate the main user workspace, real-time search, and multi-tenant team collaboration.",
        body_style
    ))

    story.append(Paragraph("<b>Live Screens & Actions to Demonstrate:</b>", h3_style))
    story.append(Paragraph("• <b>Home Page Dashboard (<code>/</code> logged in):</b> Link cards, category pills (Work, Dev, Study, Personal), pinned/starred toggles in <code>templates/index.html</code>.", bullet_style))
    story.append(Paragraph("• <b>Add Link Modal:</b> Click <code>+ Add Link</code>, input a title and URL, and observe instant card rendering without page reload.", bullet_style))
    story.append(Paragraph("• <b>Instant Search & Reset:</b> Type in search box ➔ show real-time filtering ➔ click the <code>✕</code> clear button or press <code>Escape</code> key to reset instantly.", bullet_style))
    story.append(Paragraph("• <b>Team Workspace Hub (<code>/teams</code> & <code>/teams/&lt;id&gt;</code>):</b> Click the dedicated <b>Team Workspace button</b> in the left sidebar (above Categories), view team cards, copy invite codes, and see shared team links.", bullet_style))

    story.append(Paragraph("<b>Key Technical Explanations:</b>", h3_style))
    story.append(Paragraph("• <b>DOM Filtering with <code>replaceState</code>:</b> Search query updates the URL with <code>window.history.replaceState</code> so browser refreshes keep state, eliminating full-page reload flickers.", bullet_style))
    story.append(Paragraph("• <b>Sidebar Navigation UX:</b> Prominent Team Workspace button placed in the sidebar directly above Categories for 1-click context switching between personal and team links.", bullet_style))
    story.append(Paragraph("• <b>Cryptographic Invite Tokens:</b> Teams generate 8-character hex codes (<code>secrets.token_hex(4).upper()</code>) allowing instantaneous joining with role verification (Owner, Admin, Member).", bullet_style))

    m2_box = [
        "\"Thank you [Member 1]. I will now demonstrate our <b>Home Dashboard and Team Collaboration Hub</b>.",
        "Upon authentication, the user is redirected to the <b>Home Dashboard</b> (<code>templates/index.html</code>). Here, links are organized visually with favicons, categories, and quick toggles for starring and pinning.",
        "We implemented two major architectural features here:",
        "<b>1. Real-Time Search & History Synchronization:</b> Users can instantly search across titles, URLs, and categories. We added an inline clear button (✕) and Escape key listener. Crucially, we use <code>history.replaceState</code> so query parameters stay updated in the browser without causing page reloads or broken back-button states.",
        "<b>2. Team Workspaces:</b> In the left sidebar, right above our category list, we built a dedicated <b>Team Workspace</b> button. When clicked, it takes us to <code>templates/teams/workspace.html</code>. In this workspace, members share resources collaboratively, generate 8-character cryptographic invite codes, and manage permissions with Role-Based Access Control.",
        "Now, [Member 3] will explain the backend routing logic, relational database models, and our live production deployment on Render.\""
    ]
    story.append(make_box("🎙️ MEMBER 2 SPEAKING SCRIPT (Word-for-Word Walkthrough)", m2_box, bg="#f5f3ff", border="#c4b5fd"))

    story.append(PageBreak())

    # ═══════════════════════════════════════════════════════════════════════════
    # PAGE 3: MEMBER 3 (THE ENGINE: LOGIC, DATABASE & CLOUD RUNNING)
    # ═══════════════════════════════════════════════════════════════════════════
    story.append(Paragraph("3. MEMBER 3: The Engine & Cloud (Backend Logic, Database & Live Running)", sec_title))
    story.append(Paragraph("Role: Systems Architect, Database Administrator & Cloud DevOps Engineer", role_badge))
    story.append(Paragraph(
        "Member 3 shows what happens behind the scenes: request orchestration in Flask, relational database schema in PostgreSQL, and live production deployment on Render.",
        body_style
    ))

    story.append(Paragraph("<b>Exact Files & Infrastructure to Show On-Screen:</b>", h3_style))
    story.append(Paragraph("• <b>Relational Schema (<code>models.py</code>):</b> 4 core models: <code>User</code>, <code>Team</code>, <code>TeamMember</code>, and <code>Link</code> with cascade foreign keys.", bullet_style))
    story.append(Paragraph("• <b>Database Engine & Pooling (<code>app.py</code> L55–125):</b> Normalization (<code>postgresql+psycopg://</code>), SSL enforcement (<code>sslmode=require</code>), and pool settings (<code>pool_pre_ping=True</code>, <code>pool_recycle=1800</code>).", bullet_style))
    story.append(Paragraph("• <b>Cold-Start Recovery Hook (<code>app.py</code> L105–128):</b> Lazy table initialization in <code>_ensure_db_ready</code> and <code>@app.before_request</code>.", bullet_style))
    story.append(Paragraph("• <b>Live Cloud Deployment:</b> Live production URL on <b>Render</b>, <code>Procfile</code> (Gunicorn multi-worker configuration), and Admin Dashboard (<code>/admin</code>) tracking active metrics.", bullet_style))

    story.append(Paragraph("<b>Key Technical Explanations:</b>", h3_style))
    story.append(Paragraph("• <b>Referential Integrity:</b> <code>ondelete='CASCADE'</code> guarantees no orphaned links exist when users or teams are deleted.", bullet_style))
    story.append(Paragraph("• <b>Production Connection Pooling:</b> <code>pool_size=10</code>, <code>max_overflow=20</code>, and <code>pool_pre_ping=True</code> test connections before queries to prevent cloud timeout drops.", bullet_style))
    story.append(Paragraph("• <b>Cold-Start Resilience:</b> Catches sleeping database instances on Render free tier and retries initialization during the first HTTP request instead of crashing the container.", bullet_style))

    m3_box = [
        "\"Thank you [Member 2]. I will explain the <b>Backend Route Architecture, Relational Database Layer, and Production Deployment Pipeline</b>.",
        "Under the hood, all incoming requests are orchestrated in <code>app.py</code> using Flask's Application Factory pattern. Here is how our data layer and hosting infrastructure operate:",
        "<b>1. Relational Schema & Integrity (<code>models.py</code>):</b> We designed 4 interconnected models: User, Link, Team, and TeamMember. Relationships use <code>ondelete='CASCADE'</code> so deleting a user or team cleanly purges dependent records without orphan data.",
        "<b>2. PostgreSQL Engine & Connection Pooling:</b> On our cloud server, we run PostgreSQL with SQLAlchemy 2.0 and the high-performance <code>psycopg</code> (v3) C-binary driver. We configured connection pooling with <code>pool_pre_ping=True</code> and <code>pool_recycle=1800</code> to prevent stale dropped connections common in cloud hosting.",
        "<b>3. Cold-Start Resilience:</b> In cloud PaaS environments like Render, managed databases may sleep when idle. Rather than allowing the app container to crash on boot, our <code>_ensure_db_ready</code> hook lazily verifies table schemas on the first incoming request.",
        "<b>4. Live Cloud Production:</b> LinkVault is deployed live on Render from our GitHub repository using Gunicorn as our WSGI HTTP server with multi-worker pre-fork concurrency (<code>Procfile</code>).",
        "This concludes our technical presentation. We would be glad to answer any questions or perform a live code inspection.\""
    ]
    story.append(make_box("🎙️ MEMBER 3 SPEAKING SCRIPT (Word-for-Word Walkthrough)", m3_box, bg="#fffbeb", border="#fde68a"))

    story.append(PageBreak())

    # ═══════════════════════════════════════════════════════════════════════════
    # PAGE 4: MENTOR Q&A DEFENSE MATRIX & CHECKLIST
    # ═══════════════════════════════════════════════════════════════════════════
    story.append(Paragraph("4. Mentor Q&A Defense Matrix & Setup Checklist", sec_title))
    story.append(Paragraph("Direct answers for common questions asked by project guides and evaluators:", body_style))
    story.append(Spacer(1, 4))

    qa_data = [
        [
            Paragraph("Mentor Question", table_header),
            Paragraph("Speaker", table_header),
            Paragraph("Recommended Direct Technical Answer", table_header),
        ],
        [
            Paragraph("<b>\"How does your project prevent SQL Injection?\"</b>", table_cell),
            Paragraph("<b>Member 2</b><br/>(Backend)", table_cell_bold),
            Paragraph("We use SQLAlchemy ORM which uses parameterized queries across all endpoints. User parameters are never concatenated into raw SQL strings; they are bound as variables by the database driver.", table_cell),
        ],
        [
            Paragraph("<b>\"Why doesn't the search reload the page?\"</b>", table_cell),
            Paragraph("<b>Member 1</b><br/>(Frontend)", table_cell_bold),
            Paragraph("We filter existing DOM card elements client-side in JavaScript. We use <code>window.history.replaceState</code> to reflect the search query in the browser URL without triggering a GET reload.", table_cell),
        ],
        [
            Paragraph("<b>\"What happens if the cloud database connection drops?\"</b>", table_cell),
            Paragraph("<b>Member 3</b><br/>(DevOps/DB)", table_cell_bold),
            Paragraph("We configured <code>pool_pre_ping=True</code> and <code>pool_recycle=1800</code> in SQLAlchemy engine options. It tests connection liveness before executing queries and recycles connections before cloud timeouts.", table_cell),
        ],
        [
            Paragraph("<b>\"How do you separate Admin access from regular users?\"</b>", table_cell),
            Paragraph("<b>Member 2</b><br/>(Backend)", table_cell_bold),
            Paragraph("The User model contains a <code>role</code> field ('admin' | 'user'). We use custom view decorators checking <code>current_user.is_admin</code> before serving routes under <code>/admin</code>.", table_cell),
        ],
        [
            Paragraph("<b>\"How is the app deployed and kept running?\"</b>", table_cell),
            Paragraph("<b>Member 3</b><br/>(DevOps/DB)", table_cell_bold),
            Paragraph("It is hosted on Render PaaS using Gunicorn WSGI server with 2 workers and 4 threads defined in our <code>Procfile</code>, connected via continuous deployment directly to our GitHub repository.", table_cell),
        ],
        [
            Paragraph("<b>\"Can a member access another team's private links?\"</b>", table_cell),
            Paragraph("<b>Member 2</b><br/>(Backend)", table_cell_bold),
            Paragraph("No. Every team endpoint verifies membership in the <code>team_members</code> join table. If <code>is_member(current_user.id)</code> returns False, the endpoint immediately aborts with HTTP 403 Forbidden.", table_cell),
        ]
    ]

    qa_table = Table(qa_data, colWidths=[140, 72, 320])
    qa_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#ffffff"), colors.HexColor("#f8fafc")]),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(qa_table)
    story.append(Spacer(1, 10))

    checklist_items = [
        Paragraph("• <b>Browser Tab 1 (Main Demo):</b> Open live Render URL. Start on the public Landing Page in logged-out mode.", bullet_style),
        Paragraph("• <b>Browser Tab 2 (Incognito):</b> Open a private window to demonstrate joining a team workspace via invite code.", bullet_style),
        Paragraph("• <b>VS Code Tabs to Open:</b> <code>templates/landing.html</code> (M1), <code>templates/index.html</code> (M2), <code>models.py</code> & <code>app.py</code> L55–125 (M2 & M3), <code>Procfile</code> (M3).", bullet_style),
        Paragraph("• <b>Target Time:</b> Member 1 (2 min) + Member 2 (2.5 min) + Member 3 (2.5 min) = ~7 minutes total.", bullet_style),
    ]
    story.append(make_box("✅ PRE-PRESENTATION 5-MINUTE READINESS CHECKLIST", checklist_items, bg="#f8fafc", border="#94a3b8"))

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"[SUCCESS] Exactly 4-page PDF generated at {filename}")

if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "LinkVault_Mentor_Presentation_Roadmap.pdf"
    build_roadmap_pdf(out)
