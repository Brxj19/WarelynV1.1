from __future__ import annotations

from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "diagrams"


def cell_vertex(
    cell_id: int,
    value: str,
    x: int,
    y: int,
    w: int,
    h: int,
    style: str,
) -> str:
    return (
        f'<mxCell id="{cell_id}" value="{escape(value)}" style="{style}" '
        f'vertex="1" parent="1">'
        f'<mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry"/>'
        f'</mxCell>'
    )


def cell_edge(cell_id: int, source: int, target: int, value: str = "", style: str = "") -> str:
    value_attr = f' value="{escape(value)}"' if value else ""
    style_attr = style or (
        "edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;"
        "jettySize=auto;html=1;endArrow=block;strokeWidth=2;"
        "strokeColor=#2E6DA4;fontColor=#2E6DA4;"
    )
    return (
        f'<mxCell id="{cell_id}"{value_attr} style="{style_attr}" '
        f'edge="1" parent="1" source="{source}" target="{target}">'
        f'<mxGeometry relative="1" as="geometry"/>'
        f'</mxCell>'
    )


def mx_graph_model(width: int, height: int, cells: list[str]) -> str:
    return "".join(
        [
            f'<mxGraphModel dx="{width}" dy="{height}" grid="1" gridSize="10" guides="1" '
            f'tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" '
            f'pageWidth="{width}" pageHeight="{height}" math="0" shadow="0">',
            "<root>",
            '<mxCell id="0"/>',
            '<mxCell id="1" parent="0"/>',
            *cells,
            "</root>",
            "</mxGraphModel>",
        ]
    )


def drawio_xml(name: str, width: int, height: int, cells: list[str]) -> str:
    body = "".join(
        [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<mxfile host="app.diagrams.net" modified="2026-06-04T00:00:00.000Z" agent="Codex" version="24.7.17" type="device">',
            f'<diagram id="{escape(name)}" name="{escape(name)}">',
            mx_graph_model(width, height, cells),
            "</diagram>",
            "</mxfile>",
        ]
    )
    return body


def strip_drawio_wrapper(xml: str) -> str:
    start = xml.index("<mxGraphModel")
    end = xml.rindex("</mxGraphModel>") + len("</mxGraphModel>")
    return xml[start:end]


def save(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def architecture_diagram() -> str:
    cells: list[str] = []
    cid = 2

    def add_box(value, x, y, w, h, style):
        nonlocal cid
        cells.append(cell_vertex(cid, value, x, y, w, h, style))
        cid += 1
        return cid - 1

    def add_edge(source, target, value=""):
        nonlocal cid
        cells.append(cell_edge(cid, source, target, value))
        cid += 1

    bg_style = "rounded=1;whiteSpace=wrap;html=1;fillColor=#F8FAFC;strokeColor=#CBD5E1;fontColor=#0F172A;"
    frame_style = "rounded=1;whiteSpace=wrap;html=1;dashed=1;dashPattern=6 6;fillColor=none;strokeColor=#A1A1AA;strokeWidth=2;"
    title_style = "rounded=1;whiteSpace=wrap;html=1;shadow=1;fillColor=#D6E4F0;strokeColor=#2E6DA4;strokeWidth=2;fontColor=#1F3A5F;fontStyle=1;"
    user_style = "rounded=1;whiteSpace=wrap;html=1;shadow=1;fillColor=#1F3A5F;strokeColor=#1F3A5F;strokeWidth=2;fontColor=#FFFFFF;fontStyle=1;"
    client_style = "rounded=1;whiteSpace=wrap;html=1;shadow=1;fillColor=#EAF2FB;strokeColor=#2E6DA4;strokeWidth=2;fontColor=#1F3A5F;"
    gateway_style = "rounded=1;whiteSpace=wrap;html=1;shadow=1;fillColor=#1A7F5A;strokeColor=#1A7F5A;strokeWidth=2;fontColor=#FFFFFF;"
    service_style = "rounded=1;whiteSpace=wrap;html=1;shadow=1;fillColor=#2E6DA4;strokeColor=#1F3A5F;strokeWidth=2;fontColor=#FFFFFF;"
    data_style = "rounded=1;whiteSpace=wrap;html=1;shadow=1;fillColor=#F8FAFC;strokeColor=#CBD5E1;strokeWidth=2;fontColor=#334155;"
    ext_style = "rounded=1;whiteSpace=wrap;html=1;shadow=1;fillColor=#FEF3C7;strokeColor=#F59E0B;strokeWidth=2;fontColor=#92400E;"

    add_box(" ", 0, 0, 1740, 980, frame_style)
    add_box("Users and Roles", 20, 20, 240, 920, title_style)
    users = [
        ("Super Admin", 40, 70),
        ("Tenant Admin", 40, 190),
        ("Inventory Manager", 40, 310),
        ("Sales Staff", 40, 430),
        ("Purchase Staff", 40, 550),
        ("Viewer", 40, 670),
    ]
    user_ids = [add_box(name, x, y, 200, 70, user_style) for name, x, y in users]

    add_box("Client Layer", 280, 20, 260, 920, title_style)
    react = add_box("React SPA", 310, 120, 200, 90, client_style)
    admin = add_box("Admin Panel", 310, 300, 200, 90, client_style)
    mobile = add_box("Auth / Loading / Dashboard UI", 310, 480, 200, 90, client_style)

    add_box("API Gateway", 580, 20, 280, 920, title_style)
    mw = add_box("Middleware", 610, 120, 220, 90, gateway_style)
    auth_dep = add_box("JWT + require_roles()", 610, 300, 220, 90, gateway_style)
    router = add_box("FastAPI Routers", 610, 480, 220, 90, gateway_style)

    add_box("Backend Services", 880, 20, 420, 920, title_style)
    auth = add_box("Auth Service", 900, 90, 170, 70, service_style)
    inv = add_box("Inventory Engine", 1090, 90, 190, 70, service_style)
    sales = add_box("Sales Service", 900, 200, 170, 70, service_style)
    purchases = add_box("Purchase Service", 1090, 200, 190, 70, service_style)
    returns = add_box("Returns Service", 900, 310, 170, 70, service_style)
    workflow = add_box("Workflow Service", 1090, 310, 190, 70, service_style)
    notif = add_box("Notification Service", 900, 420, 170, 70, service_style)
    ai = add_box("AI / RAG Service", 1090, 420, 190, 70, service_style)

    add_box("Data & External", 1330, 20, 330, 920, title_style)
    mysql = add_box("MySQL", 1360, 120, 120, 70, data_style)
    mongo = add_box("MongoDB", 1500, 120, 120, 70, data_style)
    email = add_box("MailHog / SMTP", 1360, 250, 260, 70, data_style)
    gemini = add_box("Google Gemini", 1360, 390, 120, 70, ext_style)
    embed = add_box("Gemini Embeddings", 1500, 390, 120, 70, ext_style)

    add_edge(user_ids[0], admin, "browser")
    add_edge(user_ids[1], react, "browser")
    add_edge(user_ids[2], react, "browser")
    add_edge(user_ids[3], react, "browser")
    add_edge(user_ids[4], react, "browser")
    add_edge(user_ids[5], react, "browser")
    add_edge(react, mw, "HTTPS REST")
    add_edge(admin, mw, "HTTPS REST")
    add_edge(mw, auth_dep, "security")
    add_edge(auth_dep, router, "UserContext")
    add_edge(router, auth, "auth")
    add_edge(router, sales, "sales")
    add_edge(router, purchases, "purchase")
    add_edge(router, returns, "returns")
    add_edge(router, workflow, "workflow")
    add_edge(router, notif, "notifications")
    add_edge(router, ai, "RAG")
    add_edge(auth, mysql)
    add_edge(sales, mysql)
    add_edge(purchases, mysql)
    add_edge(returns, mysql)
    add_edge(workflow, mysql)
    add_edge(notif, mysql)
    add_edge(inv, mysql)
    add_edge(ai, mongo)
    add_edge(ai, gemini, "LLM")
    add_edge(ai, embed, "embeddings")
    add_edge(notif, email, "email")
    add_edge(workflow, notif, "side effect")

    return drawio_xml("architecture", 1760, 980, cells)


def request_flow_diagram() -> str:
    cells: list[str] = []
    cid = 2

    def add_box(value, x, y, w, h, style):
        nonlocal cid
        cells.append(cell_vertex(cid, value, x, y, w, h, style))
        cid += 1
        return cid - 1

    def add_edge(source, target, value=""):
        nonlocal cid
        cells.append(cell_edge(cid, source, target, value))
        cid += 1

    frame_style = "rounded=1;whiteSpace=wrap;html=1;dashed=1;dashPattern=6 6;fillColor=none;strokeColor=#A1A1AA;strokeWidth=2;"
    title_style = "rounded=1;whiteSpace=wrap;html=1;shadow=1;fillColor=#D6E4F0;strokeColor=#2E6DA4;strokeWidth=2;fontColor=#1F3A5F;fontStyle=1;"
    step_style = "rounded=1;whiteSpace=wrap;html=1;shadow=1;fillColor=#FFFFFF;strokeColor=#CBD5E1;strokeWidth=2;fontColor=#0F172A;"
    success_style = "rounded=1;whiteSpace=wrap;html=1;shadow=1;fillColor=#D4EDDA;strokeColor=#1A7F5A;strokeWidth=2;fontColor=#166534;"

    add_box(" ", 20, 60, 2080, 400, frame_style)

    steps = [
        ("1. User clicks Confirm Order", 70, 100),
        ("2. React SPA sends POST /sales-orders/{id}/confirm", 280, 100),
        ("3. Middleware adds request id / headers", 490, 100),
        ("4. JWT + role check validates SALES_STAFF", 700, 100),
        ("5. Sales Service locks order", 910, 100),
        ("6. Reservations + status update", 1120, 100),
        ("7. Commit transaction", 1330, 100),
        ("8. Workflow task + notification side effects", 1540, 100),
        ("9. Response returns CONFIRMED", 1750, 100),
    ]

    ids = [add_box(text, x, y, 180, 90, step_style) for text, x, y in steps]
    for a, b in zip(ids, ids[1:]):
        add_edge(a, b)

    lane_user = add_box("User / Browser", 70, 220, 180, 70, title_style)
    lane_fe = add_box("Frontend", 280, 220, 180, 70, title_style)
    lane_mw = add_box("Middleware", 490, 220, 180, 70, title_style)
    lane_dep = add_box("Auth Dependency", 700, 220, 180, 70, title_style)
    lane_svc = add_box("Sales Service", 910, 220, 180, 70, title_style)
    lane_repo = add_box("Repository / DB", 1120, 220, 180, 70, title_style)
    lane_wf = add_box("Workflow Service", 1330, 220, 180, 70, title_style)
    lane_notif = add_box("Notification Service", 1540, 220, 180, 70, title_style)

    add_edge(lane_user, lane_fe, "browser")
    add_edge(lane_fe, lane_mw, "request")
    add_edge(lane_mw, lane_dep, "token")
    add_edge(lane_dep, lane_svc, "UserContext")
    add_edge(lane_svc, lane_repo, "SQL")
    add_edge(lane_repo, lane_wf, "task")
    add_edge(lane_wf, lane_notif, "notify")

    confirm = add_box("Sales order confirmed", 70, 340, 300, 90, success_style)
    task = add_box("PICK_ORDER task created for Inventory Manager", 420, 340, 360, 90, success_style)
    note = add_box("Notifications stay in try/except and never break the operation", 830, 340, 480, 90, success_style)
    ui = add_box("Green confirmation badge + task in queue", 1360, 340, 340, 90, success_style)

    add_edge(confirm, task)
    add_edge(task, note)
    add_edge(note, ui)

    return drawio_xml("request_flow", 2140, 500, cells)


def workflow_routing_diagram() -> str:
    cells: list[str] = []
    cid = 2

    def add_box(value, x, y, w, h, style):
        nonlocal cid
        cells.append(cell_vertex(cid, value, x, y, w, h, style))
        cid += 1
        return cid - 1

    def add_edge(source, target, value=""):
        nonlocal cid
        cells.append(cell_edge(cid, source, target, value))
        cid += 1

    frame_style = "rounded=1;whiteSpace=wrap;html=1;dashed=1;dashPattern=6 6;fillColor=none;strokeColor=#A1A1AA;strokeWidth=2;"
    title_style = "rounded=1;whiteSpace=wrap;html=1;shadow=1;fillColor=#D6E4F0;strokeColor=#2E6DA4;strokeWidth=2;fontColor=#1F3A5F;fontStyle=1;"
    sales_style = "rounded=1;whiteSpace=wrap;html=1;shadow=1;fillColor=#E8F0FA;strokeColor=#2E6DA4;strokeWidth=2;fontColor=#1F3A5F;"
    purchase_style = "rounded=1;whiteSpace=wrap;html=1;shadow=1;fillColor=#D4EDDA;strokeColor=#1A7F5A;strokeWidth=2;fontColor=#166534;"
    returns_style = "rounded=1;whiteSpace=wrap;html=1;shadow=1;fillColor=#FEF3C7;strokeColor=#F59E0B;strokeWidth=2;fontColor=#92400E;"
    reorder_style = "rounded=1;whiteSpace=wrap;html=1;shadow=1;fillColor=#F3E8FF;strokeColor=#8B5CF6;strokeWidth=2;fontColor=#5B21B6;"

    add_box(" ", 20, 60, 1940, 190, frame_style)

    sales_title = add_box("Sales Order Workflow", 40, 20, 420, 50, title_style)
    purchase_title = add_box("Purchase Order Workflow", 520, 20, 420, 50, title_style)
    returns_title = add_box("Returns Workflow", 1000, 20, 340, 50, title_style)
    reorder_title = add_box("Low Stock Reorder", 1380, 20, 300, 50, title_style)

    sales_nodes = [
        add_box("SO confirmed by SALES_STAFF", 40, 90, 190, 70, sales_style),
        add_box("PICK_ORDER task → INVENTORY_MANAGER", 250, 90, 210, 70, sales_style),
        add_box("Picking complete", 480, 90, 150, 70, sales_style),
        add_box("Packing complete", 650, 90, 150, 70, sales_style),
        add_box("Fulfillment committed", 820, 90, 170, 70, sales_style),
        add_box("CREATE_INVOICE task → SALES_STAFF", 1010, 90, 220, 70, sales_style),
        add_box("Invoice sent", 1250, 90, 140, 70, sales_style),
    ]
    for a, b in zip(sales_nodes, sales_nodes[1:]):
        add_edge(a, b)

    purchase_nodes = [
        add_box("PO submitted by PURCHASE_STAFF", 520, 90, 200, 70, purchase_style),
        add_box("High value?", 740, 90, 110, 70, purchase_style),
        add_box("APPROVE_PO task → TENANT_ADMIN", 870, 90, 220, 70, purchase_style),
        add_box("Receipt committed", 1110, 90, 160, 70, purchase_style),
        add_box("PUTAWAY_STOCK task → INVENTORY_MANAGER", 1290, 90, 230, 70, purchase_style),
        add_box("Putaway complete", 1540, 90, 160, 70, purchase_style),
        add_box("RECORD_BILL task → PURCHASE_STAFF", 1720, 90, 220, 70, purchase_style),
    ]
    add_edge(purchase_nodes[0], purchase_nodes[1])
    add_edge(purchase_nodes[1], purchase_nodes[2], "yes")
    add_edge(purchase_nodes[1], purchase_nodes[3], "no")
    add_edge(purchase_nodes[2], purchase_nodes[3])
    add_edge(purchase_nodes[3], purchase_nodes[4])
    add_edge(purchase_nodes[4], purchase_nodes[5])
    add_edge(purchase_nodes[5], purchase_nodes[6])

    return_nodes = [
        add_box("Return submitted by SALES_STAFF", 1000, 90, 180, 70, returns_style),
        add_box("RETURN_QC task → INVENTORY_MANAGER", 1200, 90, 220, 70, returns_style),
        add_box("QC inspection", 1440, 90, 140, 70, returns_style),
        add_box("Return processed", 1600, 90, 150, 70, returns_style),
    ]
    for a, b in zip(return_nodes, return_nodes[1:]):
        add_edge(a, b)

    reorder_nodes = [
        add_box("Low stock detected", 1380, 90, 150, 70, reorder_style),
        add_box("REORDER_STOCK task → PURCHASE_STAFF", 1540, 90, 220, 70, reorder_style),
    ]
    add_edge(reorder_nodes[0], reorder_nodes[1])

    return drawio_xml("workflow_routing", 1980, 230, cells)


def techstack_diagram() -> str:
    cells: list[str] = []
    cid = 2

    def add_box(value, x, y, w, h, style):
        nonlocal cid
        cells.append(cell_vertex(cid, value, x, y, w, h, style))
        cid += 1
        return cid - 1

    header_style = "rounded=1;whiteSpace=wrap;html=1;shadow=1;fillColor=#1F3A5F;strokeColor=#1F3A5F;strokeWidth=2;fontColor=#FFFFFF;fontStyle=1;"
    band_style = "rounded=1;whiteSpace=wrap;html=1;shadow=1;fillColor=#F8FAFC;strokeColor=#CBD5E1;strokeWidth=2;fontColor=#0F172A;"
    pill_client = "rounded=1;whiteSpace=wrap;html=1;shadow=1;fillColor=#D6E4F0;strokeColor=#2E6DA4;strokeWidth=2;fontColor=#1F3A5F;"
    pill_api = "rounded=1;whiteSpace=wrap;html=1;shadow=1;fillColor=#E8F0FA;strokeColor=#2E6DA4;strokeWidth=2;fontColor=#1F3A5F;"
    pill_service = "rounded=1;whiteSpace=wrap;html=1;shadow=1;fillColor=#D4EDDA;strokeColor=#1A7F5A;strokeWidth=2;fontColor=#166534;"
    pill_data = "rounded=1;whiteSpace=wrap;html=1;shadow=1;fillColor=#FEF3C7;strokeColor=#F59E0B;strokeWidth=2;fontColor=#92400E;"
    pill_infra = "rounded=1;whiteSpace=wrap;html=1;shadow=1;fillColor=#F3E8FF;strokeColor=#8B5CF6;strokeWidth=2;fontColor=#5B21B6;"

    add_box("Warelyn Inventory — Actual Tech Stack", 40, 20, 1720, 60, header_style)

    bands = [
        ("Frontend", 40, 110, 1720, 120, [
            ("React", 70, 155, 120, 45, pill_client),
            ("Vite", 210, 155, 100, 45, pill_client),
            ("Tailwind CSS 3.4.17", 330, 155, 180, 45, pill_client),
            ("React Router", 530, 155, 140, 45, pill_client),
            ("Recharts 2.15.3", 690, 155, 160, 45, pill_client),
            ("Lucide React 1.16.0", 870, 155, 180, 45, pill_client),
            ("Lottie / dotLottie", 1070, 155, 170, 45, pill_client),
            ("Frontend build with Vite", 1260, 155, 220, 45, pill_client),
        ]),
        ("API + Auth", 40, 250, 1720, 120, [
            ("FastAPI 0.115.6", 70, 295, 150, 45, pill_api),
            ("Uvicorn 0.34", 240, 295, 140, 45, pill_api),
            ("Pydantic Settings 2.7.1", 400, 295, 210, 45, pill_api),
            ("JWT / PyJWT 2.10.1", 630, 295, 170, 45, pill_api),
            ("bcrypt 5.0.0", 820, 295, 120, 45, pill_api),
            ("SlowAPI 0.1.9", 960, 295, 130, 45, pill_api),
            ("HTTPX 0.27.2", 1110, 295, 130, 45, pill_api),
            ("python-multipart", 1260, 295, 150, 45, pill_api),
        ]),
        ("Services + Documents", 40, 390, 1720, 140, [
            ("SQLAlchemy 2.0.45", 70, 445, 170, 45, pill_service),
            ("Alembic 1.13.3", 260, 445, 150, 45, pill_service),
            ("WeasyPrint 68.1", 430, 445, 150, 45, pill_service),
            ("Jinja2 3.1.4+", 600, 445, 140, 45, pill_service),
            ("openpyxl 3.1.3", 760, 445, 150, 45, pill_service),
            ("qrcode 8.2", 930, 445, 120, 45, pill_service),
            ("Inventory Engine", 1070, 445, 160, 45, pill_service),
            ("Workflow / Notification", 1250, 445, 200, 45, pill_service),
        ]),
        ("Data Stores", 40, 550, 1720, 120, [
            ("MySQL / PyMySQL 1.1.1", 70, 595, 220, 45, pill_data),
            ("MongoDB / pymongo 4.10.1", 310, 595, 230, 45, pill_data),
            ("SMTP / MailHog", 560, 595, 150, 45, pill_data),
            ("Tenant-scoped data model", 730, 595, 210, 45, pill_data),
            ("PDF templates and exports", 960, 595, 230, 45, pill_data),
            ("CSV imports / reports", 1210, 595, 190, 45, pill_data),
        ]),
        ("Infra / AI", 40, 700, 1720, 120, [
            ("Docker Compose", 70, 745, 150, 45, pill_infra),
            ("Google Gemini API", 240, 745, 170, 45, pill_infra),
            ("Gemini embeddings", 430, 745, 170, 45, pill_infra),
            ("pytest 8.3.4", 620, 745, 120, 45, pill_infra),
            ("GitHub Actions / CI", 760, 745, 180, 45, pill_infra),
            ("Mailhog dev mail", 960, 745, 150, 45, pill_infra),
            ("MongoDB RAG cache", 1130, 745, 170, 45, pill_infra),
            ("Charts + dashboards", 1320, 745, 170, 45, pill_infra),
        ]),
    ]

    for title, x, y, w, h, badges in bands:
        add_box(title, x, y, w, 28, header_style)
        add_box("", x, y + 28, w, h - 28, band_style)
        for badge in badges:
            add_box(*badge)

    return drawio_xml("techstack", 1800, 900, cells)


def rag_architecture_diagram() -> str:
    cells: list[str] = []
    cid = 2

    def add_box(value, x, y, w, h, style):
        nonlocal cid
        cells.append(cell_vertex(cid, value, x, y, w, h, style))
        cid += 1
        return cid - 1

    def add_edge(source, target, value=""):
        nonlocal cid
        cells.append(cell_edge(cid, source, target, value))
        cid += 1

    frame_style = "rounded=1;whiteSpace=wrap;html=1;dashed=1;dashPattern=6 6;fillColor=none;strokeColor=#A1A1AA;strokeWidth=2;"
    title_style = "rounded=1;whiteSpace=wrap;html=1;shadow=1;fillColor=#D6E4F0;strokeColor=#2E6DA4;strokeWidth=2;fontColor=#1F3A5F;fontStyle=1;"
    user_style = "rounded=1;whiteSpace=wrap;html=1;shadow=1;fillColor=#1F3A5F;strokeColor=#1F3A5F;strokeWidth=2;fontColor=#FFFFFF;fontStyle=1;"
    fe_style = "rounded=1;whiteSpace=wrap;html=1;shadow=1;fillColor=#EAF2FB;strokeColor=#2E6DA4;strokeWidth=2;fontColor=#1F3A5F;"
    svc_style = "rounded=1;whiteSpace=wrap;html=1;shadow=1;fillColor=#D4EDDA;strokeColor=#1A7F5A;strokeWidth=2;fontColor=#166534;"
    data_style = "rounded=1;whiteSpace=wrap;html=1;shadow=1;fillColor=#F8FAFC;strokeColor=#CBD5E1;strokeWidth=2;fontColor=#334155;"
    gemini_style = "rounded=1;whiteSpace=wrap;html=1;shadow=1;fillColor=#F3E8FF;strokeColor=#8B5CF6;strokeWidth=2;fontColor=#5B21B6;"
    note_style = "rounded=1;whiteSpace=wrap;html=1;shadow=1;fillColor=#FEF3C7;strokeColor=#F59E0B;strokeWidth=2;fontColor=#92400E;"

    add_box(" ", 20, 20, 1880, 760, frame_style)
    add_box("Warelyn RAG Architecture", 40, 20, 320, 54, title_style)

    user = add_box("FAQ Widget\nor Admin Copilot", 60, 120, 190, 92, user_style)
    fe = add_box("Frontend Chat UI", 300, 120, 190, 92, fe_style)
    svc = add_box("AssistantService", 540, 120, 210, 92, svc_style)
    retr = add_box("Hybrid Retrieval\nBM25 + semantic cosine", 800, 120, 240, 92, svc_style)
    gemini_llm = add_box("Gemini Chat Model", 1090, 120, 190, 92, gemini_style)

    src_frame = add_box("Knowledge Sources", 60, 270, 410, 200, title_style)
    src1 = add_box("docs/knowledge/*.md\n+ docs/knowledge_v2/*.md", 90, 335, 150, 82, data_style)
    src2 = add_box("Workflow + reports\n+ tenant docs", 260, 335, 180, 82, data_style)

    mysql_frame = add_box("MySQL Knowledge Store", 540, 270, 510, 200, title_style)
    docs_tbl = add_box("faq_documents", 575, 335, 160, 82, data_style)
    chunks_tbl = add_box("faq_chunks\ncontent + searchable_text\nembedding JSON", 760, 325, 240, 102, data_style)
    embedded_note = add_box("Embedded vectors are stored here:\nfaq_chunks.embedding (JSON column)", 1030, 335, 240, 82, note_style)

    mongo_frame = add_box("MongoDB Conversation Store", 1090, 270, 400, 200, title_style)
    sess = add_box("assistant_sessions", 1120, 335, 150, 82, data_style)
    msgs = add_box("assistant_messages", 1290, 335, 160, 82, data_style)
    fb = add_box("assistant_feedback", 1470, 335, 150, 82, data_style)

    out_frame = add_box("Response Assembly", 60, 510, 1500, 170, title_style)
    out1 = add_box("Confidence gate", 90, 565, 140, 72, note_style)
    out2 = add_box("Citations", 250, 565, 120, 72, note_style)
    out3 = add_box("Suggested actions", 390, 565, 170, 72, note_style)
    out4 = add_box("Tables / insights\n(for reports)", 580, 565, 180, 72, note_style)
    out5 = add_box("Session history\nstored in MongoDB", 780, 565, 190, 72, note_style)
    out6 = add_box("Telemetry + audit log", 990, 565, 170, 72, note_style)
    out7 = add_box("Return answer to UI", 1180, 565, 170, 72, note_style)

    add_edge(user, fe, "question")
    add_edge(fe, svc, "POST /faq/ask\nor /assistant/sessions/{id}/ask")
    add_edge(svc, retr, "retrieve chunks")
    add_edge(retr, docs_tbl, "keyword search")
    add_edge(retr, chunks_tbl, "semantic score")
    add_edge(src1, docs_tbl, "ingest")
    add_edge(src2, docs_tbl, "ingest")
    add_edge(svc, gemini_llm, "chat prompt")
    add_edge(svc, chunks_tbl, "save embeddings")
    add_edge(svc, sess, "create session")
    add_edge(svc, msgs, "save messages")
    add_edge(svc, fb, "feedback")
    add_edge(svc, out1, "LOW/HIGH")
    add_edge(out1, out2)
    add_edge(out2, out3)
    add_edge(out3, out4)
    add_edge(out4, out5)
    add_edge(out5, out6)
    add_edge(out6, out7)
    add_edge(out7, fe, "answer + citations")
    add_edge(chunks_tbl, embedded_note, "JSON vectors")
    add_edge(sess, out5, "history")

    return drawio_xml("rag_architecture", 1940, 760, cells)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    architecture = architecture_diagram()
    rag_architecture = rag_architecture_diagram()
    request_flow = request_flow_diagram()
    workflow_routing = workflow_routing_diagram()
    techstack = techstack_diagram()

    files = {
        "architecture.drawio.xml": architecture,
        "architecture.paste.xml": strip_drawio_wrapper(architecture),
        "rag_architecture.drawio.xml": rag_architecture,
        "rag_architecture.paste.xml": strip_drawio_wrapper(rag_architecture),
        "request_flow.drawio.xml": request_flow,
        "request_flow.paste.xml": strip_drawio_wrapper(request_flow),
        "workflow_routing.drawio.xml": workflow_routing,
        "workflow_routing.paste.xml": strip_drawio_wrapper(workflow_routing),
        "techstack.drawio.xml": techstack,
        "techstack.paste.xml": strip_drawio_wrapper(techstack),
    }
    for filename, content in files.items():
        path = OUT / filename
        save(path, content)
        print(f"Generated: {path}")


if __name__ == "__main__":
    main()
