import os
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["OMP_NUM_THREADS"] = "1"

import streamlit as st
import sqlite3
import hashlib
import base64
import math
from datetime import datetime
import streamlit.components.v1 as components

# -----------------------------------------------------------------------------
# PAGE CONFIGURATION
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="PLOTLINE | Verified Land Marketplace",
    page_icon="🛰️",
    layout="wide",
    initial_sidebar_state="expanded",
)


def render_html(html_str: str):
    """Renders HTML cleanly without Markdown indentation code-block bugs."""
    cleaned = "\n".join(line.strip() for line in html_str.splitlines() if line.strip())
    st.markdown(cleaned, unsafe_allow_html=True)


def get_satellite_tile_url(lat: float, lon: float, zoom: int = 16) -> str:
    """Generates a real Esri World Imagery satellite tile URL for any lat/lon."""
    lat_rad = math.radians(lat)
    n = 2.0 ** zoom
    xtile = int((lon + 180.0) / 360.0 * n)
    ytile = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
    return f"https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{zoom}/{ytile}/{xtile}"


# -----------------------------------------------------------------------------
# CLEAN, MINIMAL DARK THEME CSS
# -----------------------------------------------------------------------------
def inject_custom_css():
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@500;600&display=swap');

        :root {
            --bg-main: #0a0e14;
            --bg-card: #111722;
            --bg-subtle: #161e2c;
            --border-color: rgba(255, 255, 255, 0.08);
            --border-hover: rgba(16, 185, 129, 0.4);
            --text-main: #f1f5f9;
            --text-muted: #94a3b8;
            --text-dim: #64748b;
            --accent: #10b981;
        }

        html, body, [class*="css"] {
            font-family: 'Inter', -apple-system, sans-serif;
            background-color: var(--bg-main);
            color: var(--text-main);
        }

        #MainMenu, footer {visibility: hidden;}
        header {background: transparent !important;}

        .stApp {
            background-color: var(--bg-main);
        }

        section[data-testid="stSidebar"] {
            background-color: #0d121b !important;
            border-right: 1px solid var(--border-color);
        }

        /* Top Navigation Header */
        .brand-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 1.1rem 1.5rem;
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            margin-bottom: 1.25rem;
        }
        .brand-title {
            font-size: 1.35rem;
            font-weight: 700;
            letter-spacing: -0.02em;
            color: #ffffff;
            display: flex;
            align-items: center;
            gap: 0.55rem;
        }
        .brand-dot {
            width: 9px;
            height: 9px;
            background-color: var(--accent);
            border-radius: 50%;
            display: inline-block;
        }
        .brand-subtitle {
            font-size: 0.82rem;
            color: var(--text-muted);
            margin-top: 0.15rem;
        }
        .role-pill {
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.74rem;
            padding: 0.35rem 0.75rem;
            border-radius: 6px;
            background: rgba(16, 185, 129, 0.12);
            color: #34d399;
            border: 1px solid rgba(16, 185, 129, 0.25);
        }

        /* Summary Metric Bar */
        .metric-strip {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 0.85rem;
            margin-bottom: 1.25rem;
        }
        .metric-box {
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 10px;
            padding: 0.9rem 1.1rem;
        }
        .metric-label {
            font-size: 0.72rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: var(--text-muted);
            margin-bottom: 0.25rem;
        }
        .metric-value {
            font-family: 'JetBrains Mono', monospace;
            font-size: 1.25rem;
            font-weight: 600;
            color: var(--text-main);
        }

        /* Unified Well-Mannered Property Card */
        .listing-card {
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            overflow: hidden;
            transition: border-color 0.2s ease;
            margin-bottom: 0.35rem;
        }
        .listing-card:hover {
            border-color: var(--border-hover);
        }

        /* Dual Fixed-Height Media Header (Satellite + Ground) */
        .media-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 2px;
            background: #0a0e14;
            border-bottom: 1px solid var(--border-color);
        }
        .media-item {
            position: relative;
            height: 165px;
            overflow: hidden;
        }
        .media-item img {
            width: 100%;
            height: 100%;
            object-fit: cover;
            display: block;
        }
        .media-tag {
            position: absolute;
            bottom: 8px;
            left: 8px;
            background: rgba(10, 14, 20, 0.82);
            color: #e2e8f0;
            font-size: 0.68rem;
            font-weight: 600;
            padding: 3px 8px;
            border-radius: 4px;
            letter-spacing: 0.04em;
            border: 1px solid rgba(255, 255, 255, 0.12);
            backdrop-filter: blur(4px);
        }

        /* Card Content Body */
        .card-body {
            padding: 1.1rem 1.2rem;
        }
        .card-top-row {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            gap: 0.75rem;
        }
        .card-title {
            font-size: 1.05rem;
            font-weight: 600;
            color: #ffffff;
            margin: 0;
            line-height: 1.35;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        .card-price {
            font-family: 'JetBrains Mono', monospace;
            font-size: 1.08rem;
            font-weight: 700;
            color: #34d399;
            white-space: nowrap;
        }
        .card-location {
            font-size: 0.82rem;
            color: var(--text-muted);
            margin-top: 0.25rem;
            margin-bottom: 0.85rem;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        /* Clean 3-Column Spec Strip */
        .spec-strip {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 0.5rem;
            background: var(--bg-subtle);
            border: 1px solid rgba(255, 255, 255, 0.05);
            border-radius: 8px;
            padding: 0.65rem 0.75rem;
            margin-bottom: 0.8rem;
        }
        .spec-cell-label {
            font-size: 0.68rem;
            color: var(--text-dim);
            text-transform: uppercase;
            letter-spacing: 0.04em;
        }
        .spec-cell-val {
            font-size: 0.82rem;
            font-weight: 600;
            color: var(--text-main);
            margin-top: 2px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        /* Card Footer Row */
        .card-footer {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding-top: 0.65rem;
            border-top: 1px solid rgba(255, 255, 255, 0.06);
            font-size: 0.76rem;
            color: var(--text-muted);
        }
        .status-pill {
            color: #34d399;
            font-weight: 500;
        }
        .featured-tag {
            color: #fbbf24;
            font-weight: 600;
            margin-right: 6px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


# -----------------------------------------------------------------------------
# LAND UNIT CONVERSION UTILITIES
# -----------------------------------------------------------------------------
UNIT_TO_SQFT = {
    "Sq. Ft.": 1.0,
    "Sq. Yd. (Gaj)": 9.0,
    "Bigha (Pucca - RJ/NCR)": 27225.0,
    "Acre": 43560.0,
    "Hectare": 107639.0,
}


def to_sqft(value: float, unit: str) -> float:
    return float(value) * UNIT_TO_SQFT.get(unit, 1.0)


def convert_from_sqft(sqft_val: float, target_unit: str) -> float:
    return sqft_val / UNIT_TO_SQFT.get(target_unit, 1.0)


def format_inr_lakhs(lakhs: float) -> str:
    if lakhs >= 100:
        return f"₹{lakhs / 100:.2f} Cr"
    return f"₹{lakhs:.0f} Lakhs"


def get_price_bracket(lakhs: float) -> str:
    if lakhs < 50:
        return "Under ₹50 Lakhs"
    elif lakhs <= 100:
        return "₹50 Lakhs – ₹1 Cr"
    elif lakhs <= 200:
        return "₹1 Cr – ₹2 Cr"
    else:
        return "Above ₹2 Cr"


# -----------------------------------------------------------------------------
# DATABASE LAYER (SQLite3)
# -----------------------------------------------------------------------------
DB_FILE = "plotline_core.db"


def get_conn():
    return sqlite3.connect(DB_FILE, check_same_thread=False)


def hash_pw(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def init_db():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL,
            agency_name TEXT,
            rera_id TEXT,
            created_at TEXT NOT NULL
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS properties (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agent_id INTEGER NOT NULL,
            agent_name TEXT NOT NULL,
            agent_phone TEXT NOT NULL,
            agent_rera TEXT,
            title TEXT NOT NULL,
            state TEXT NOT NULL,
            district TEXT NOT NULL,
            neighbourhood TEXT NOT NULL,
            exact_location TEXT NOT NULL,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            land_type TEXT NOT NULL,
            area_value REAL NOT NULL,
            area_unit TEXT NOT NULL,
            area_sqft REAL NOT NULL,
            price_lakhs REAL NOT NULL,
            price_range TEXT NOT NULL,
            title_status TEXT NOT NULL,
            is_featured INTEGER DEFAULT 0,
            satellite_img TEXT NOT NULL,
            ground_img TEXT NOT NULL,
            description TEXT,
            created_at TEXT NOT NULL
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS inquiries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            property_id INTEGER NOT NULL,
            property_title TEXT NOT NULL,
            agent_id INTEGER NOT NULL,
            buyer_name TEXT NOT NULL,
            buyer_email TEXT NOT NULL,
            buyer_phone TEXT NOT NULL,
            message TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )

    cur.execute("SELECT COUNT(*) FROM users")
    if cur.fetchone()[0] == 0:
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        demo_users = [
            (
                "Vikramaditya Rathore",
                "agent@plotline.in",
                "+91 98290 44112",
                hash_pw("agent123"),
                "Estate Agent",
                "Aravalli Land Advisory",
                "RAJ/RERA/2025/A-4821",
                now,
            ),
            (
                "Rao Devendra Singh",
                "ncr.dealer@plotline.in",
                "+91 98112 77890",
                hash_pw("agent123"),
                "Estate Agent",
                "Sohna Corridor Estates",
                "HR/RERA/GGM/2025/901",
                now,
            ),
            (
                "Aarav Sharma",
                "buyer@plotline.in",
                "+91 97991 23001",
                hash_pw("buyer123"),
                "Buyer",
                "",
                "",
                now,
            ),
        ]
        cur.executemany(
            """
            INSERT INTO users (name, email, phone, password_hash, role, agency_name, rera_id, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            demo_users,
        )

    cur.execute("SELECT COUNT(*) FROM properties")
    if cur.fetchone()[0] == 0:
        now = datetime.now().strftime("%Y-%m-%d")
        seed_listings = [
            (
                1,
                "Vikramaditya Rathore",
                "+91 98290 44112",
                "RAJ/RERA/2025/A-4821",
                "Corner NA Commercial Plot near Ring Road",
                "Rajasthan",
                "Jaipur",
                "Jagatpura",
                "200 Ft Mahal Road Extension, Near Bombay Hospital, Jagatpura",
                26.8035,
                75.8622,
                "NA Residential / Plotted",
                1200.0,
                "Sq. Yd. (Gaj)",
                to_sqft(1200.0, "Sq. Yd. (Gaj)"),
                92.0,
                get_price_bracket(92.0),
                "100% RERA & JDA Patta",
                1,
                get_satellite_tile_url(26.8035, 75.8622, 16),
                "https://images.unsplash.com/photo-1500382017468-9049fed747ef?auto=format&fit=crop&w=800&q=80",
                "Direct 60-ft sector road frontage with clear demarcation pillars and verified JDA 90-A conversion.",
                now,
            ),
            (
                1,
                "Vikramaditya Rathore",
                "+91 98290 44112",
                "RAJ/RERA/2025/A-4821",
                "Institutional & Logistics Highway Parcel",
                "Rajasthan",
                "Jaipur",
                "Tonk Road",
                "NH-52 Corridor, 2.4 km ahead of Chokhi Dhani, Tonk Road",
                26.7465,
                75.8390,
                "Commercial / Industrial",
                3.5,
                "Bigha (Pucca - RJ/NCR)",
                to_sqft(3.5, "Bigha (Pucca - RJ/NCR)"),
                165.0,
                get_price_bracket(165.0),
                "100% RERA & NA Cleared",
                1,
                get_satellite_tile_url(26.7465, 75.8390, 16),
                "https://images.unsplash.com/photo-1500076656116-558758c991c1?auto=format&fit=crop&w=800&q=80",
                "High-visibility rectangular parcel on Tonk Road service lane. Zero litigation history, immediate registry readiness.",
                now,
            ),
            (
                2,
                "Rao Devendra Singh",
                "+91 98112 77890",
                "HR/RERA/GGM/2025/901",
                "Aravalli Foothills Gated Farm Land",
                "Haryana",
                "Gurugram",
                "Sohna Road",
                "Sector 33 South of Gurgaon, Near Mumbai Expressway Interchange",
                28.2740,
                77.0680,
                "Farmhouse / Estate",
                1.5,
                "Acre",
                to_sqft(1.5, "Acre"),
                240.0,
                get_price_bracket(240.0),
                "CLU & Mutation Verified",
                1,
                get_satellite_tile_url(28.2740, 77.0680, 16),
                "https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?auto=format&fit=crop&w=800&q=80",
                "Surrounded by operational luxury farmhouses with sweet groundwater table and completed boundary wall.",
                now,
            ),
            (
                1,
                "Vikramaditya Rathore",
                "+91 98290 44112",
                "RAJ/RERA/2025/A-4821",
                "Irrigated Commercial Agri-Block",
                "Rajasthan",
                "Jaipur",
                "Chaksu / Kothun",
                "Bassi-Chaksu State Highway, 800m from Expressway Slip Road",
                26.6051,
                75.9472,
                "Agricultural Land",
                6.0,
                "Bigha (Pucca - RJ/NCR)",
                to_sqft(6.0, "Bigha (Pucca - RJ/NCR)"),
                44.0,
                get_price_bracket(44.0),
                "Khatedari Title Verified",
                0,
                get_satellite_tile_url(26.6051, 75.9472, 16),
                "https://images.unsplash.com/photo-1625246333195-78d9c38ad449?auto=format&fit=crop&w=800&q=80",
                "Fertile loamy soil with two solar borewells, 3-phase feeder line, and tarred approach road.",
                now,
            ),
            (
                2,
                "Rao Devendra Singh",
                "+91 98112 77890",
                "HR/RERA/GGM/2025/901",
                "KMP Expressway Industrial Zone Plot",
                "Haryana",
                "Palwal",
                "KMP Corridor",
                "HSIIDC Industrial Belt, 1.2 km from Palwal-Sohna Cloverleaf",
                28.1487,
                77.3320,
                "Commercial / Industrial",
                2500.0,
                "Sq. Yd. (Gaj)",
                to_sqft(2500.0, "Sq. Yd. (Gaj)"),
                135.0,
                get_price_bracket(135.0),
                "100% RERA & NA Cleared",
                0,
                get_satellite_tile_url(28.1487, 77.3320, 16),
                "https://images.unsplash.com/photo-1513836279014-a89f7a76ae86?auto=format&fit=crop&w=800&q=80",
                "Approved industrial zoning with wide turning radius for 40-ft containers and digital mutation record.",
                now,
            ),
            (
                1,
                "Vikramaditya Rathore",
                "+91 98290 44112",
                "RAJ/RERA/2025/A-4821",
                "SEZ Corridor Villa Plot",
                "Rajasthan",
                "Jaipur",
                "Ajmer Road (Mahindra SEZ)",
                "250 Ft SEZ Road, Nevta Dam Link Corridor, Ajmer Road",
                26.8240,
                75.6731,
                "NA Residential / Plotted",
                500.0,
                "Sq. Yd. (Gaj)",
                to_sqft(500.0, "Sq. Yd. (Gaj)"),
                38.0,
                get_price_bracket(38.0),
                "100% RERA & JDA Patta",
                0,
                get_satellite_tile_url(26.8240, 75.6731, 16),
                "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?auto=format&fit=crop&w=800&q=80",
                "East-facing plot inside a RERA-registered gated township near Mahindra World City.",
                now,
            ),
        ]
        cur.executemany(
            """
            INSERT INTO properties (
                agent_id, agent_name, agent_phone, agent_rera, title,
                state, district, neighbourhood, exact_location,
                latitude, longitude, land_type, area_value, area_unit,
                area_sqft, price_lakhs, price_range, title_status,
                is_featured, satellite_img, ground_img, description, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            seed_listings,
        )

    # Upgrade any existing Unsplash space/map placeholder URLs in existing DB to real Esri satellite tiles
    cur.execute("SELECT id, latitude, longitude, satellite_img FROM properties")
    for row_id, lat, lon, sat_url in cur.fetchall():
        if "unsplash.com" in sat_url:
            cur.execute(
                "UPDATE properties SET satellite_img = ? WHERE id = ?",
                (get_satellite_tile_url(lat, lon, 16), row_id),
            )

    conn.commit()
    conn.close()


# -----------------------------------------------------------------------------
# SATELLITE & BOUNDARY MAP RENDERER
# -----------------------------------------------------------------------------
def render_satellite_map(listings, height=360, zoom=7):
    if not listings:
        st.info("No parcels match the current filter criteria.")
        return

    avg_lat = sum(item["latitude"] for item in listings) / len(listings)
    avg_lon = sum(item["longitude"] for item in listings) / len(listings)
    if len(listings) == 1:
        zoom = 16

    markers_js = []
    for item in listings:
        lat = item["latitude"]
        lon = item["longitude"]
        side_meters = max(math.sqrt(item["area_sqft"] * 0.092903), 35)
        d_lat = (side_meters / 2.0) / 111320.0
        d_lon = (side_meters / 2.0) / (111320.0 * math.cos(math.radians(lat)))

        poly_coords = [
            [lat + d_lat, lon - d_lon],
            [lat + d_lat, lon + d_lon],
            [lat - d_lat, lon + d_lon],
            [lat - d_lat, lon - d_lon],
        ]
        price_str = format_inr_lakhs(item["price_lakhs"])
        popup_html = (
            f"<div style='font-family:Inter,sans-serif;color:#0f172a;min-width:190px;'>"
            f"<div style='font-weight:700;font-size:13px;'>{item['title']}</div>"
            f"<div style='font-size:12px;color:#047857;font-weight:700;margin-top:2px;'>{price_str} • {item['area_value']:g} {item['area_unit']}</div>"
            f"<div style='font-size:11px;color:#475569;margin-top:2px;'>📍 {item['neighbourhood']}, {item['district']}</div>"
            f"</div>"
        )
        markers_js.append(
            f"""
            L.polygon({poly_coords}, {{
                color: '#f59e0b',
                weight: 2,
                fillColor: '#10b981',
                fillOpacity: 0.25
            }}).addTo(map).bindPopup({repr(popup_html)});

            L.circleMarker([{lat}, {lon}], {{
                radius: 6,
                fillColor: '#10b981',
                color: '#ffffff',
                weight: 2,
                fillOpacity: 0.95
            }}).addTo(map).bindPopup({repr(popup_html)});
            """
        )

    joined_markers = "\n".join(markers_js)

    map_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8" />
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
        <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
        <style>
            body {{ margin: 0; padding: 0; background: #0a0e14; }}
            #map {{
                width: 100%;
                height: {height}px;
                border-radius: 10px;
                border: 1px solid rgba(255,255,255,0.08);
            }}
        </style>
    </head>
    <body>
        <div id="map"></div>
        <script>
            var map = L.map('map').setView([{avg_lat}, {avg_lon}], {zoom});
            L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{{z}}/{{y}}/{{x}}', {{
                maxZoom: 19
            }}).addTo(map);
            L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{{z}}/{{y}}/{{x}}', {{
                maxZoom: 19
            }}).addTo(map);
            {joined_markers}
        </script>
    </body>
    </html>
    """
    components.html(map_html, height=height + 6)


# -----------------------------------------------------------------------------
# HELPER FUNCTIONS
# -----------------------------------------------------------------------------
def encode_uploaded_file(uploaded_file) -> str:
    if uploaded_file is None:
        return ""
    mime = uploaded_file.type or "image/jpeg"
    b64 = base64.b64encode(uploaded_file.getvalue()).decode("utf-8")
    return f"data:{mime};base64,{b64}"


def fetch_all_properties():
    conn = get_conn()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM properties ORDER BY is_featured DESC, id DESC")
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def fetch_agent_inquiries(agent_id: int):
    conn = get_conn()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM inquiries WHERE agent_id = ? ORDER BY id DESC", (agent_id,))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


# -----------------------------------------------------------------------------
# AUTHENTICATION VIEW
# -----------------------------------------------------------------------------
def render_auth_screen():
    render_html(
        """
        <div class="brand-header">
            <div>
                <div class="brand-title"><span class="brand-dot"></span> PLOTLINE</div>
                <div class="brand-subtitle">Visualizing Stories, Analyzing Progress — Data-Driven Land Discovery</div>
            </div>
            <div class="role-pill">VERIFIED LAND MARKETPLACE</div>
        </div>
        """
    )

    col_left, col_right = st.columns([1.1, 1], gap="large")

    with col_left:
        st.markdown("### Why Plotline?")
        st.markdown(
            "High-value land transactions need clarity. **Plotline** connects investors and agri-buyers "
            "directly with verified local estate agents:"
        )
        st.markdown(
            """
            - **🛰️ Side-by-Side Satellite & Ground Imagery**: View real satellite tiles and on-ground photos on every card.
            - **🛡️ 100% RERA & NA Cleared Titles**: Transparent verification for JDA Patta, CLU, and Khatedari titles.
            - **📐 Local Unit Conversions**: Switch seamlessly between Bigha, Gaj (Sq. Yd.), Acre, and Sq. Ft.
            """
        )

        st.markdown("#### Quick Demo Login")
        d1, d2 = st.columns(2)
        with d1:
            if st.button("🔓 Demo Login as Buyer", width="stretch"):
                conn = get_conn()
                conn.row_factory = sqlite3.Row
                cur = conn.cursor()
                cur.execute("SELECT * FROM users WHERE email = 'buyer@plotline.in'")
                st.session_state["user"] = dict(cur.fetchone())
                conn.close()
                st.rerun()
        with d2:
            if st.button("🏗️ Demo Login as Estate Agent", width="stretch"):
                conn = get_conn()
                conn.row_factory = sqlite3.Row
                cur = conn.cursor()
                cur.execute("SELECT * FROM users WHERE email = 'agent@plotline.in'")
                st.session_state["user"] = dict(cur.fetchone())
                conn.close()
                st.rerun()

    with col_right:
        tab_login, tab_signup = st.tabs(["Sign In", "Create Account (Buyer / Agent)"])

        with tab_login:
            with st.form("login_form"):
                email = st.text_input("Email Address", placeholder="you@domain.com")
                password = st.text_input("Password", type="password", placeholder="••••••••")
                if st.form_submit_button("Sign In", width="stretch"):
                    conn = get_conn()
                    conn.row_factory = sqlite3.Row
                    cur = conn.cursor()
                    cur.execute(
                        "SELECT * FROM users WHERE email = ? AND password_hash = ?",
                        (email.strip().lower(), hash_pw(password)),
                    )
                    user = cur.fetchone()
                    conn.close()
                    if user:
                        st.session_state["user"] = dict(user)
                        st.rerun()
                    else:
                        st.error("Invalid credentials. Use the Demo Login buttons or create an account.")

        with tab_signup:
            with st.form("signup_form"):
                account_role = st.radio("Account Type", ["Buyer", "Estate Agent"], horizontal=True)
                full_name = st.text_input("Full Name *", placeholder="e.g., Mohit Nimiwal")
                reg_email = st.text_input("Email Address *", placeholder="name@example.com")
                phone = st.text_input("Phone Number *", placeholder="+91 98290 XXXXX")
                reg_pw = st.text_input("Password *", type="password")
                agency_name = st.text_input("Agency Name (For Agents)", placeholder="Optional")
                rera_id = st.text_input("RERA ID (For Agents)", placeholder="Optional")

                if st.form_submit_button("Create Account", width="stretch"):
                    if not (full_name and reg_email and phone and reg_pw):
                        st.warning("Please complete all required fields (*).")
                    else:
                        try:
                            conn = get_conn()
                            cur = conn.cursor()
                            now = datetime.now().strftime("%Y-%m-%d %H:%M")
                            cur.execute(
                                """
                                INSERT INTO users (name, email, phone, password_hash, role, agency_name, rera_id, created_at)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                                """,
                                (
                                    full_name.strip(),
                                    reg_email.strip().lower(),
                                    phone.strip(),
                                    hash_pw(reg_pw),
                                    account_role,
                                    agency_name.strip(),
                                    rera_id.strip(),
                                    now,
                                ),
                            )
                            conn.commit()
                            new_id = cur.lastrowid
                            conn.row_factory = sqlite3.Row
                            cur = conn.cursor()
                            cur.execute("SELECT * FROM users WHERE id = ?", (new_id,))
                            st.session_state["user"] = dict(cur.fetchone())
                            conn.close()
                            st.rerun()
                        except sqlite3.IntegrityError:
                            st.error("This email is already registered.")


# -----------------------------------------------------------------------------
# BUYER DASHBOARD VIEW (CLEAN & WELL-MANNERED GRID)
# -----------------------------------------------------------------------------
def render_buyer_dashboard(user):
    all_props = fetch_all_properties()

    with st.sidebar:
        st.markdown(f"### 👤 {user['name']}")
        st.caption(f"Verified Buyer • `{user['email']}`")
        if st.button("Sign Out", width="stretch"):
            del st.session_state["user"]
            st.rerun()

        st.markdown("---")
        st.markdown("#### 🔍 Filter Land Parcels")

        available_states = sorted(list({p["state"] for p in all_props}))
        selected_states = st.multiselect("State", options=available_states, placeholder="All States")

        if selected_states:
            available_districts = sorted(list({p["district"] for p in all_props if p["state"] in selected_states}))
        else:
            available_districts = sorted(list({p["district"] for p in all_props}))

        selected_districts = st.multiselect("District", options=available_districts, placeholder="All Districts")

        land_types = sorted(list({p["land_type"] for p in all_props}))
        selected_land_types = st.multiselect("Land Type", options=land_types, placeholder="All Land Types")

        price_bracket_choice = st.selectbox(
            "Price Range",
            ["All Price Ranges", "Under ₹50 Lakhs", "₹50 Lakhs – ₹1 Cr", "₹1 Cr – ₹2 Cr", "Above ₹2 Cr"],
        )

        max_price_in_db = max([int(p["price_lakhs"]) for p in all_props] + [300])
        price_slider = st.slider(
            "Budget Slider (₹ Lakhs)",
            min_value=10,
            max_value=max_price_in_db,
            value=(10, max_price_in_db),
            step=5,
        )

        neighbourhood_query = st.text_input("Neighbourhood", placeholder="e.g., Jagatpura, Sohna...")

        st.markdown("---")
        display_unit = st.selectbox(
            "📐 Area Unit Display",
            options=["Original Listing Unit"] + list(UNIT_TO_SQFT.keys()),
        )

    filtered = []
    for p in all_props:
        if selected_states and p["state"] not in selected_states:
            continue
        if selected_districts and p["district"] not in selected_districts:
            continue
        if selected_land_types and p["land_type"] not in selected_land_types:
            continue
        if price_bracket_choice != "All Price Ranges" and p["price_range"] != price_bracket_choice:
            continue
        if not (price_slider[0] <= p["price_lakhs"] <= price_slider[1]):
            continue
        if neighbourhood_query:
            q = neighbourhood_query.strip().lower()
            if q not in f"{p['neighbourhood']} {p['exact_location']} {p['title']}".lower():
                continue
        filtered.append(p)

    total_acres = sum(p["area_sqft"] for p in filtered) / 43560.0
    avg_price = (sum(p["price_lakhs"] for p in filtered) / len(filtered)) if filtered else 0

    render_html(
        f"""
        <div class="metric-strip">
            <div class="metric-box">
                <div class="metric-label">Matching Parcels</div>
                <div class="metric-value">{len(filtered)}</div>
            </div>
            <div class="metric-box">
                <div class="metric-label">Total Land Area</div>
                <div class="metric-value">{total_acres:.1f} Acres</div>
            </div>
            <div class="metric-box">
                <div class="metric-label">Average Price</div>
                <div class="metric-value">{format_inr_lakhs(avg_price) if filtered else '—'}</div>
            </div>
            <div class="metric-box">
                <div class="metric-label">Title Status</div>
                <div class="metric-value" style="color:#34d399;">RERA / NA</div>
            </div>
        </div>
        """
    )

    with st.expander("🗺️ Open Overview Satellite Map (All Filtered Parcels)", expanded=False):
        render_satellite_map(filtered, height=350)

    st.markdown(f"#### Available Land Parcels ({len(filtered)})")

    if not filtered:
        st.info("No land parcels match your filters. Try adjusting the price range or state filter.")
        return

    # Render clean 2-column grid row-by-row so horizontal alignment is always locked
    for row_start in range(0, len(filtered), 2):
        row_items = filtered[row_start : row_start + 2]
        cols = st.columns(2, gap="medium")

        for col_idx, prop in enumerate(row_items):
            with cols[col_idx]:
                if display_unit == "Original Listing Unit":
                    area_display = f"{prop['area_value']:g} {prop['area_unit']}"
                else:
                    converted_val = convert_from_sqft(prop["area_sqft"], display_unit)
                    area_display = f"{converted_val:,.2f} {display_unit}"

                price_per_sqft = (prop["price_lakhs"] * 100000.0) / max(prop["area_sqft"], 1.0)
                featured_tag = '<span class="featured-tag">★ FEATURED</span>' if prop["is_featured"] else ""

                # Self-contained, fixed-height card with side-by-side Satellite & Ground photos
                render_html(
                    f"""
                    <div class="listing-card">
                        <div class="media-grid">
                            <div class="media-item">
                                <img src="{prop['satellite_img']}" alt="Satellite View" />
                                <span class="media-tag">🛰️ SATELLITE</span>
                            </div>
                            <div class="media-item">
                                <img src="{prop['ground_img']}" alt="Ground Photo" />
                                <span class="media-tag">📷 GROUND</span>
                            </div>
                        </div>
                        <div class="card-body">
                            <div class="card-top-row">
                                <h4 class="card-title" title="{prop['title']}">{prop['title']}</h4>
                                <div class="card-price">{format_inr_lakhs(prop['price_lakhs'])}</div>
                            </div>
                            <div class="card-location" title="{prop['exact_location']}">
                                📍 {prop['neighbourhood']}, {prop['district']} ({prop['state']}) — {prop['exact_location']}
                            </div>
                            <div class="spec-strip">
                                <div>
                                    <div class="spec-cell-label">Total Area</div>
                                    <div class="spec-cell-val">{area_display}</div>
                                </div>
                                <div>
                                    <div class="spec-cell-label">Land Type</div>
                                    <div class="spec-cell-val">{prop['land_type']}</div>
                                </div>
                                <div>
                                    <div class="spec-cell-label">Rate & Range</div>
                                    <div class="spec-cell-val">₹{price_per_sqft:,.0f}/sq.ft</div>
                                </div>
                            </div>
                            <div class="card-footer">
                                <div>{featured_tag}<span class="status-pill">✓ {prop['title_status']}</span></div>
                                <div>Agent: {prop['agent_name']}</div>
                            </div>
                        </div>
                    </div>
                    """
                )

                # Single neat drawer under each card so the grid stays compact and aligned
                with st.expander("📐 View Boundary Map & Contact Dealer"):
                    if prop["description"]:
                        st.caption(prop["description"])
                    st.caption(
                        f"**Exact Location:** {prop['exact_location']}  \n"
                        f"**Coordinates:** `{prop['latitude']:.4f}° N, {prop['longitude']:.4f}° E` • "
                        f"**Price Bracket:** `{prop['price_range']}`"
                    )
                    render_satellite_map([prop], height=210, zoom=16)

                    st.markdown(
                        f"**Estate Agent:** {prop['agent_name']} (`{prop['agent_phone']}`) • "
                        f"**RERA:** `{prop['agent_rera'] or 'Verified'}`"
                    )
                    with st.form(f"inq_{prop['id']}"):
                        msg = st.text_input(
                            "Quick Message to Agent",
                            value=f"Interested in {prop['title']} ({area_display}) at {prop['neighbourhood']}. Please share Khasra/site details.",
                        )
                        if st.form_submit_button("Send Inquiry", width="stretch"):
                            conn = get_conn()
                            cur = conn.cursor()
                            cur.execute(
                                """
                                INSERT INTO inquiries (
                                    property_id, property_title, agent_id,
                                    buyer_name, buyer_email, buyer_phone, message, created_at
                                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                                """,
                                (
                                    prop["id"],
                                    prop["title"],
                                    prop["agent_id"],
                                    user["name"],
                                    user["email"],
                                    user["phone"],
                                    msg,
                                    datetime.now().strftime("%Y-%m-%d %H:%M"),
                                ),
                            )
                            conn.commit()
                            conn.close()
                            st.success("Inquiry sent to the Estate Agent!")


# -----------------------------------------------------------------------------
# ESTATE AGENT DASHBOARD VIEW
# -----------------------------------------------------------------------------
def render_agent_dashboard(user):
    all_props = fetch_all_properties()
    my_props = [p for p in all_props if p["agent_id"] == user["id"]]
    my_inquiries = fetch_agent_inquiries(user["id"])

    with st.sidebar:
        st.markdown(f"### 🏗️ {user['name']}")
        st.caption(f"Estate Agent • `{user.get('agency_name') or 'Verified Dealer'}`")
        if st.button("Sign Out", width="stretch"):
            del st.session_state["user"]
            st.rerun()

        st.markdown("---")
        agent_nav = st.radio(
            "Agent Menu",
            [
                "➕ Add Land / Property",
                f"📋 My Listings ({len(my_props)})",
                f"📨 Buyer Inquiries ({len(my_inquiries)})",
                "🌐 All Marketplace Listings",
            ],
        )

    if agent_nav == "➕ Add Land / Property":
        st.markdown("#### Publish New Land Parcel")
        st.caption("Add property details along with satellite and normal ground photos.")

        with st.form("add_property_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                title = st.text_input("Property Title *", placeholder="e.g., 2 Bigha Highway Commercial Plot")
                land_type = st.selectbox(
                    "Type of Land *",
                    [
                        "NA Residential / Plotted",
                        "Commercial / Industrial",
                        "Agricultural Land",
                        "Farmhouse / Estate",
                        "Institutional / Warehousing",
                    ],
                )
                state = st.selectbox(
                    "State *",
                    ["Rajasthan", "Haryana", "Delhi NCR", "Uttar Pradesh", "Gujarat", "Maharashtra", "Punjab", "Madhya Pradesh"],
                )
                district = st.text_input("District *", placeholder="e.g., Jaipur, Gurugram")
                neighbourhood = st.text_input("Neighbourhood *", placeholder="e.g., Jagatpura, Tonk Road, Sohna Road")

            with c2:
                a1, a2 = st.columns([1.2, 1])
                with a1:
                    area_value = st.number_input("Total Land Area *", min_value=0.1, value=1000.0, step=10.0)
                with a2:
                    area_unit = st.selectbox("Unit *", list(UNIT_TO_SQFT.keys()))

                price_lakhs = st.number_input(
                    "Price (in ₹ Lakhs) * [100 Lakhs = ₹1 Cr]", min_value=1.0, value=85.0, step=5.0
                )
                title_status = st.selectbox(
                    "Title Status *",
                    [
                        "100% RERA & NA Cleared",
                        "100% RERA & JDA Patta",
                        "CLU & Mutation Verified",
                        "Khatedari Title Verified",
                    ],
                )
                exact_location = st.text_input(
                    "Exact Location / Landmark *",
                    placeholder="e.g., 200 Ft Mahal Road Extension, Jagatpura",
                )

            g1, g2, g3 = st.columns([1, 1, 1.2])
            with g1:
                latitude = st.number_input("Latitude", value=26.8035, format="%.5f")
            with g2:
                longitude = st.number_input("Longitude", value=75.8622, format="%.5f")
            with g3:
                is_featured = st.checkbox("Featured Top-Feed Listing", value=True)

            img_col1, img_col2 = st.columns(2)
            with img_col1:
                sat_file = st.file_uploader("Upload Satellite Photo (Optional — Auto-fetched if blank)", type=["jpg", "jpeg", "png", "webp"])
                sat_url = st.text_input("Or Satellite Photo URL")
            with img_col2:
                ground_file = st.file_uploader("Upload Ground Photo", type=["jpg", "jpeg", "png", "webp"])
                ground_url = st.text_input("Or Ground Photo URL")

            description = st.text_area("Property Notes", placeholder="Road approach, boundary wall, water/electricity...")

            if st.form_submit_button("🚀 Publish Listing", width="stretch"):
                if not (title and district and neighbourhood and exact_location):
                    st.error("Please fill in Title, District, Neighbourhood, and Exact Location.")
                else:
                    sat_img_final = (
                        encode_uploaded_file(sat_file)
                        or sat_url.strip()
                        or get_satellite_tile_url(float(latitude), float(longitude), 16)
                    )
                    ground_img_final = (
                        encode_uploaded_file(ground_file)
                        or ground_url.strip()
                        or "https://images.unsplash.com/photo-1500382017468-9049fed747ef?auto=format&fit=crop&w=800&q=80"
                    )
                    computed_sqft = to_sqft(area_value, area_unit)
                    computed_bracket = get_price_bracket(price_lakhs)

                    conn = get_conn()
                    cur = conn.cursor()
                    cur.execute(
                        """
                        INSERT INTO properties (
                            agent_id, agent_name, agent_phone, agent_rera, title,
                            state, district, neighbourhood, exact_location,
                            latitude, longitude, land_type, area_value, area_unit,
                            area_sqft, price_lakhs, price_range, title_status,
                            is_featured, satellite_img, ground_img, description, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            user["id"],
                            user["name"],
                            user["phone"],
                            user.get("rera_id", ""),
                            title.strip(),
                            state,
                            district.strip(),
                            neighbourhood.strip(),
                            exact_location.strip(),
                            float(latitude),
                            float(longitude),
                            land_type,
                            float(area_value),
                            area_unit,
                            computed_sqft,
                            float(price_lakhs),
                            computed_bracket,
                            title_status,
                            1 if is_featured else 0,
                            sat_img_final,
                            ground_img_final,
                            description.strip(),
                            datetime.now().strftime("%Y-%m-%d"),
                        ),
                    )
                    conn.commit()
                    conn.close()
                    st.success(f"'{title}' has been added to Plotline!")

    elif agent_nav.startswith("📋 My Listings"):
        st.markdown(f"#### My Listed Properties ({len(my_props)})")
        if not my_props:
            st.info("You haven't added any listings yet.")
        else:
            for row_start in range(0, len(my_props), 2):
                row_items = my_props[row_start : row_start + 2]
                cols = st.columns(2, gap="medium")
                for col_idx, p in enumerate(row_items):
                    with cols[col_idx]:
                        render_html(
                            f"""
                            <div class="listing-card">
                                <div class="media-grid">
                                    <div class="media-item">
                                        <img src="{p['satellite_img']}" alt="Satellite" />
                                        <span class="media-tag">🛰️ SATELLITE</span>
                                    </div>
                                    <div class="media-item">
                                        <img src="{p['ground_img']}" alt="Ground" />
                                        <span class="media-tag">📷 GROUND</span>
                                    </div>
                                </div>
                                <div class="card-body">
                                    <div class="card-top-row">
                                        <h4 class="card-title">{p['title']}</h4>
                                        <div class="card-price">{format_inr_lakhs(p['price_lakhs'])}</div>
                                    </div>
                                    <div class="card-location">📍 {p['neighbourhood']}, {p['district']} ({p['state']})</div>
                                    <div class="card-footer">
                                        <span>{p['area_value']:g} {p['area_unit']} • {p['land_type']}</span>
                                        <span class="status-pill">{p['price_range']}</span>
                                    </div>
                                </div>
                            </div>
                            """
                        )
                        if st.button("🗑️ Delete Listing", key=f"del_{p['id']}", width="stretch"):
                            conn = get_conn()
                            cur = conn.cursor()
                            cur.execute("DELETE FROM properties WHERE id = ? AND agent_id = ?", (p["id"], user["id"]))
                            conn.commit()
                            conn.close()
                            st.rerun()

    elif agent_nav.startswith("📨 Buyer Inquiries"):
        st.markdown(f"#### Buyer Inquiries ({len(my_inquiries)})")
        if not my_inquiries:
            st.info("No buyer inquiries yet.")
        else:
            for inq in my_inquiries:
                render_html(
                    f"""
                    <div class="listing-card" style="padding:1rem 1.2rem;margin-bottom:0.75rem;">
                        <div class="card-top-row">
                            <h4 class="card-title">{inq['property_title']}</h4>
                            <span class="status-pill">{inq['created_at']}</span>
                        </div>
                        <div style="font-size:0.84rem;color:#cbd5e1;margin:0.4rem 0;">
                            <strong>Buyer:</strong> {inq['buyer_name']} • 📞 <code>{inq['buyer_phone']}</code> • ✉️ <code>{inq['buyer_email']}</code>
                        </div>
                        <div style="font-size:0.84rem;color:#94a3b8;background:#161e2c;padding:0.65rem;border-radius:6px;">
                            "{inq['message']}"
                        </div>
                    </div>
                    """
                )
    else:
        render_buyer_dashboard(user)


# -----------------------------------------------------------------------------
# MAIN ROUTER
# -----------------------------------------------------------------------------
def main():
    inject_custom_css()
    init_db()

    if "user" not in st.session_state or st.session_state["user"] is None:
        render_auth_screen()
    else:
        user = st.session_state["user"]
        render_html(
            f"""
            <div class="brand-header">
                <div>
                    <div class="brand-title"><span class="brand-dot"></span> PLOTLINE</div>
                    <div class="brand-subtitle">Verified Land Discovery & Satellite Boundary Marketplace</div>
                </div>
                <div class="role-pill">{user['role'].upper()} • {user['name']}</div>
            </div>
            """
        )

        if user["role"] == "Estate Agent":
            render_agent_dashboard(user)
        else:
            render_buyer_dashboard(user)


if __name__ == "__main__":
    main()