import io
from datetime import datetime

import pandas as pd
import streamlit as st

# ------------------ CONFIG GENERAL ------------------ #
st.set_page_config(
    page_title="Stock",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS para mobile + estética
st.markdown("""
    <style>
    .block-container {
        padding-top: 0.8rem;
        padding-bottom: 0.8rem;
        padding-left: 0.6rem;
        padding-right: 0.6rem;
    }

    .stSelectbox > label,
    .stMultiSelect > label {
        font-size: 0.85rem;
    }
    .stSelectbox div[data-baseweb="select"] span,
    .stMultiSelect div[data-baseweb="select"] span {
        font-size: 0.85rem;
        white-space: normal;
    }
    .stSelectbox, .stMultiSelect {
        width: 100% !important;
    }

    td, th {
        white-space: normal;
    }

    .kpi-card {
        background-color: #f1f5f9;
        border-radius: 0.75rem;
        padding: 0.9rem 1rem;
        border: 1px solid #e2e8f0;
        box-shadow: 0 1px 3px rgba(15,23,42,0.08);
        text-align: center;
    }
    .kpi-label {
        font-size: 0.85rem;
        color: #64748b;
        margin-bottom: 0.25rem;
        font-weight: 600;
    }
    .kpi-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #0f172a;
    }
    </style>
""", unsafe_allow_html=True)


# ------------------ FUNCIONES AUXILIARES ------------------ #

@st.cache_data
def load_data():
    df = pd.read_excel("data/Stock.xlsx")

    col_map = {
        "Depósito": "Deposito",
        "Partida": "Partida",
        "Secuencia": "Secuencia",
        "Desde": "Desde",
        "Lote": "Lote",
        "Vencimiento": "Vencimiento",
        "Producto": "Producto",
        "Medida": "Medida",
        "Secuencia modif": "Secuencia_modif",
        "Partida completa": "Partida_completa",
        "Linea": "Linea",
        "Categoria": "Categoria"
    }
    df.rename(columns=col_map, inplace=True)

    df["Vencimiento"] = pd.to_datetime(df["Vencimiento"], dayfirst=True, errors="coerce")
    df["Desde"] = pd.to_datetime(df["Desde"], dayfirst=True, errors="coerce")

    hoy = pd.Timestamp(datetime.now().date())
    df["Dias_hasta_vto"] = (df["Vencimiento"] - hoy).dt.days
    df["Dias_en_deposito"] = (hoy - df["Desde"]).dt.days

    df["Cantidad"] = 1
    return df


def to_excel(df, sheet_name="Datos"):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name)
    return output.getvalue()


def kpi_card(label, value, help_text=None):
    tooltip = f" title='{help_text}' " if help_text else ""
    st.markdown(
        f"""
        <div class="kpi-card" {tooltip}>
            <div class="kpi-label">{label}</div>
            <div class="kpi-value">{value}</div>
        </div>
        """,
        unsafe_allow_html=True
    )


def aplicar_busqueda(df, texto):
    if not texto:
        return df

    texto = texto.strip().lower()
    cols_busqueda = [
        c for c in [
            "Partida", "Lote", "Producto", "Medida",
            "Partida_completa", "Secuencia", "Secuencia_modif"
        ] if c in df.columns
    ]
    if not cols_busqueda:
        return df

    mask = False
    for col in cols_busqueda:
        mask = mask | df[col].astype(str).str.lower().str.contains(texto, na=False)
    return df[mask]


def opciones_ordenadas(df, col):
    return sorted(df[col].dropna().astype(str).unique()) if col in df.columns else []


# ------------------ LOGIN ------------------ #

if "auth_ok" not in st.session_state:
    st.session_state.auth_ok = False

if not st.session_state.auth_ok:
    st.title("📦 Stock")
    st.subheader("Ingreso")

    with st.form("login_form"):
        user = st.text_input("Usuario")
        pwd = st.text_input("Contraseña", type="password")
        submitted = st.form_submit_button("Ingresar")

    if submitted:
        if user == "femani" and pwd == "stock2025":
            st.session_state.auth_ok = True
            st.success("Acceso concedido")
            st.rerun()
        else:
            st.error("Usuario o contraseña incorrectos")

    st.stop()


# ------------------ APP PRINCIPAL ------------------ #

df_raw = load_data()

st.title("📊 FemiBot Stock")
st.caption("Visualización de stock y vencimientos de materiales.")

# Flags para limpiar filtros (se ejecutan al comienzo del script)
if "clear_inv" not in st.session_state:
    st.session_state.clear_inv = False
if "clear_vto" not in st.session_state:
    st.session_state.clear_vto = False

if st.session_state.clear_inv:
    for key in ["search_inv", "dep_inv", "linea_inv", "cat_inv",
                "prod_inv", "med_inv", "mes_desde_inv"]:
        if key in st.session_state:
            del st.session_state[key]
    st.session_state.clear_inv = False
    st.rerun()

if st.session_state.clear_vto:
    for key in [
        "search_vto", "dep_vto", "linea_vto", "cat_vto",
        "prod_vto", "med_vto", "mes_vto",
        "estado_vto_radio", "slider_dias_vto"
    ]:
        if key in st.session_state:
            del st.session_state[key]
    st.session_state.clear_vto = False
    st.rerun()

tab_inv, tab_vto = st.tabs(["📦 Inventario", "⏰ Vencimientos"])


# ------------------ TAB INVENTARIO ------------------ #

with tab_inv:
    st.subheader("Inventario actual")

    # Botón: solo setea el flag, el borrado real se hace arriba
    if st.button("🧹 Limpiar filtros de inventario"):
        st.session_state.clear_inv = True
        st.rerun()

    st.markdown("#### 🔍 Buscador (inventario)")
    texto_busqueda_inv = st.text_input(
        "Buscar por producto, lote, partida, etc.",
        placeholder="Ej: ONYX, 0D737, 001259084...",
        key="search_inv"
    )
    df_inv = aplicar_busqueda(df_raw, texto_busqueda_inv)

    st.markdown("#### 🎛️ Filtros (inventario)")
    col_f1, col_f2, col_f3 = st.columns(3)

    with col_f1:
        dep_options_inv = opciones_ordenadas(df_inv, "Deposito")
        dep_sel_inv = st.multiselect(
            "Depósito",
            options=["Todos"] + dep_options_inv,
            default=[],
            key="dep_inv"
        )
        if dep_sel_inv and "Todos" not in dep_sel_inv:
            df_inv = df_inv[df_inv["Deposito"].astype(str).isin(dep_sel_inv)]

    with col_f2:
        linea_options_inv = opciones_ordenadas(df_inv, "Linea")
        linea_sel_inv = st.multiselect(
            "Línea",
            options=["Todos"] + linea_options_inv,
            default=[],
            key="linea_inv"
        )
        if linea_sel_inv and "Todos" not in linea_sel_inv:
            df_inv = df_inv[df_inv["Linea"].astype(str).isin(linea_sel_inv)]

    with col_f3:
        cat_options_inv = opciones_ordenadas(df_inv, "Categoria")
        cat_sel_inv = st.multiselect(
            "Categoría",
            options=["Todos"] + cat_options_inv,
            default=[],
            key="cat_inv"
        )
        if cat_sel_inv and "Todos" not in cat_sel_inv:
            df_inv = df_inv[df_inv["Categoria"].astype(str).isin(cat_sel_inv)]

    col_f4, col_f5 = st.columns(2)
    with col_f4:
        prod_options_inv = opciones_ordenadas(df_inv, "Producto")
        prod_sel_inv = st.multiselect(
            "Producto",
            options=["Todos"] + prod_options_inv,
            default=[],
            key="prod_inv"
        )
        if prod_sel_inv and "Todos" not in prod_sel_inv:
            df_inv = df_inv[df_inv["Producto"].astype(str).isin(prod_sel_inv)]

    with col_f5:
        med_options_inv = opciones_ordenadas(df_inv, "Medida")
        med_sel_inv = st.multiselect(
            "Medida",
            options=["Todos"] + med_options_inv,
            default=[],
            key="med_inv"
        )
        if med_sel_inv and "Todos" not in med_sel_inv:
            df_inv = df_inv[df_inv["Medida"].astype(str).isin(med_sel_inv)]

    # Mes-año de ingreso
    if "Desde" in df_inv.columns:
        df_inv["MesDesde"] = df_inv["Desde"].dt.to_period("M").astype(str)
        mes_options_inv = sorted(df_inv["MesDesde"].dropna().unique())
        mes_sel_inv = st.multiselect(
            "Mes de ingreso (columna 'Desde')",
            options=["Todos"] + mes_options_inv,
            default=[],
            key="mes_desde_inv"
        )
        if mes_sel_inv and "Todos" not in mes_sel_inv:
            df_inv = df_inv[df_inv["MesDesde"].isin(mes_sel_inv)]

    total_materiales = int(df_inv["Cantidad"].sum()) if "Cantidad" in df_inv.columns else len(df_inv)
    depositos_unicos = df_inv["Deposito"].nunique() if "Deposito" in df_inv.columns else 0
    promedio_dias_deposito = (
        int(df_inv["Dias_en_deposito"].mean())
        if "Dias_en_deposito" in df_inv.columns and not df_inv["Dias_en_deposito"].isna().all()
        else None
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        kpi_card("Materiales (filtrados)", total_materiales)
    with col2:
        kpi_card("Depósitos involucrados", depositos_unicos)
    with col3:
        if promedio_dias_deposito is not None:
            kpi_card("Promedio días en depósito", promedio_dias_deposito)

    st.markdown("### Detalle de inventario")

    cols_orden_inv = [
        "Deposito", "Linea", "Categoria", "Producto", "Medida",
        "Partida", "Secuencia", "Partida_completa", "Secuencia_modif",
        "Lote", "Desde", "Dias_en_deposito",
        "Vencimiento", "Dias_hasta_vto"
    ]
    cols_existentes_inv = [c for c in cols_orden_inv if c in df_inv.columns]
    otros_inv = [c for c in df_inv.columns if c not in cols_existentes_inv + ["MesDesde"]]
    df_inv_view = df_inv[cols_existentes_inv + otros_inv]

    st.dataframe(
        df_inv_view,
        use_container_width=True,
        column_config={
            "Deposito": st.column_config.Column("Depósito", width="large"),
            "Producto": st.column_config.Column("Producto", width="large"),
            "Categoria": st.column_config.Column("Categoría", width="medium"),
            "Linea": st.column_config.Column("Línea", width="medium"),
        },
    )

    excel_inv = to_excel(df_inv_view, sheet_name="Inventario")
    st.download_button(
        label="⬇️ Descargar inventario filtrado en Excel",
        data=excel_inv,
        file_name="inventario_filtrado.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


# ------------------ TAB VENCIMIENTOS ------------------ #

with tab_vto:
    st.subheader("Materiales por vencimiento")

    df_vto = df_raw[df_raw["Vencimiento"].notna()].copy()

    if st.button("🧹 Limpiar filtros de vencimientos"):
        st.session_state.clear_vto = True
        st.rerun()

    st.markdown("#### 🔍 Buscador (vencimientos)")
    texto_busqueda_vto = st.text_input(
        "Buscar por producto, lote, partida, etc.",
        placeholder="Ej: ONYX, 0D737, 001259084...",
        key="search_vto"
    )
    df_vto = aplicar_busqueda(df_vto, texto_busqueda_vto)

    st.markdown("#### 🎛️ Filtros (vencimientos)")
    col_v1, col_v2, col_v3 = st.columns(3)

    with col_v1:
        dep_options_vto = opciones_ordenadas(df_vto, "Deposito")
        dep_sel_vto = st.multiselect(
            "Depósito",
            options=["Todos"] + dep_options_vto,
            default=[],
            key="dep_vto"
        )
        if dep_sel_vto and "Todos" not in dep_sel_vto:
            df_vto = df_vto[df_vto["Deposito"].astype(str).isin(dep_sel_vto)]

    with col_v2:
        linea_options_vto = opciones_ordenadas(df_vto, "Linea")
        linea_sel_vto = st.multiselect(
            "Línea",
            options=["Todos"] + linea_options_vto,
            default=[],
            key="linea_vto"
        )
        if linea_sel_vto and "Todos" not in linea_sel_vto:
            df_vto = df_vto[df_vto["Linea"].astype(str).isin(linea_sel_vto)]

    with col_v3:
        cat_options_vto = opciones_ordenadas(df_vto, "Categoria")
        cat_sel_vto = st.multiselect(
            "Categoría",
            options=["Todos"] + cat_options_vto,
            default=[],
            key="cat_vto"
        )
        if cat_sel_vto and "Todos" not in cat_sel_vto:
            df_vto = df_vto[df_vto["Categoria"].astype(str).isin(cat_sel_vto)]

    col_v4, col_v5 = st.columns(2)
    with col_v4:
        prod_options_vto = opciones_ordenadas(df_vto, "Producto")
        prod_sel_vto = st.multiselect(
            "Producto",
            options=["Todos"] + prod_options_vto,
            default=[],
            key="prod_vto"
        )
        if prod_sel_vto and "Todos" not in prod_sel_vto:
            df_vto = df_vto[df_vto["Producto"].astype(str).isin(prod_sel_vto)]

    with col_v5:
        med_options_vto = opciones_ordenadas(df_vto, "Medida")
        med_sel_vto = st.multiselect(
            "Medida",
            options=["Todos"] + med_options_vto,
            default=[],
            key="med_vto"
        )
        if med_sel_vto and "Todos" not in med_sel_vto:
            df_vto = df_vto[df_vto["Medida"].astype(str).isin(med_sel_vto)]

    df_vto["MesVto"] = df_vto["Vencimiento"].dt.to_period("M").astype(str)
    mes_options_vto = sorted(df_vto["MesVto"].dropna().unique())
    mes_sel_vto = st.multiselect(
        "Mes de vencimiento",
        options=["Todos"] + mes_options_vto,
        default=[],
        key="mes_vto"
    )
    if mes_sel_vto and "Todos" not in mes_sel_vto:
        df_vto = df_vto[df_vto["MesVto"].isin(mes_sel_vto)]

    st.markdown("#### ⏰ Configuración de vencimientos")
    col_cfg1, col_cfg2 = st.columns([1, 3])
    with col_cfg1:
        estado_vto = st.radio(
            "Estado de vencimiento",
            options=["Todos", "Solo próximos", "Solo vencidos"],
            help="Afecta la vista de esta pestaña.",
            key="estado_vto_radio"
        )
    with col_cfg2:
        max_dias_proximos = st.slider(
            "Días hasta vencimiento (para 'próximos')",
            min_value=1,
            max_value=180,
            value=30,
            key="slider_dias_vto"
        )

    if "Dias_hasta_vto" in df_vto.columns:
        if estado_vto == "Solo vencidos":
            df_vto = df_vto[df_vto["Dias_hasta_vto"] < 0]
        elif estado_vto == "Solo próximos":
            df_vto = df_vto[
                (df_vto["Dias_hasta_vto"] >= 0) &
                (df_vto["Dias_hasta_vto"] <= max_dias_proximos)
            ]
        else:
            df_vto = df_vto[df_vto["Dias_hasta_vto"].notna()]

    total_vto = len(df_vto)
    cant_vencidos = int((df_vto["Dias_hasta_vto"] < 0).sum()) if "Dias_hasta_vto" in df_vto.columns else 0
    cant_proximos = int(
        ((df_vto["Dias_hasta_vto"] >= 0) & (df_vto["Dias_hasta_vto"] <= max_dias_proximos)).sum()
    ) if "Dias_hasta_vto" in df_vto.columns else 0

    col1v, col2v, col3v = st.columns(3)
    with col1v:
        kpi_card("Materiales (vista vencimientos)", total_vto)
    with col2v:
        kpi_card("Vencidos", cant_vencidos)
    with col3v:
        kpi_card(f"Próx. ≤ {max_dias_proximos} días", cant_proximos)

    st.markdown("### Detalle de vencimientos")

    cols_orden_vto = [
        "Deposito", "Linea", "Categoria", "Producto", "Medida",
        "Partida", "Secuencia", "Partida_completa", "Secuencia_modif",
        "Lote", "Desde", "Dias_en_deposito",
        "Vencimiento", "Dias_hasta_vto"
    ]
    cols_existentes_vto = [c for c in cols_orden_vto if c in df_vto.columns]
    otros_vto = [c for c in df_vto.columns if c not in cols_existentes_vto + ["MesVto"]]
    df_vto_view = df_vto[cols_existentes_vto + otros_vto]

    st.dataframe(
        df_vto_view,
        use_container_width=True,
        column_config={
            "Deposito": st.column_config.Column("Depósito", width="large"),
            "Producto": st.column_config.Column("Producto", width="large"),
            "Categoria": st.column_config.Column("Categoría", width="medium"),
            "Linea": st.column_config.Column("Línea", width="medium"),
        },
    )

    excel_vto = to_excel(df_vto_view, sheet_name="Vencimientos")
    st.download_button(
        label="⬇️ Descargar vencimientos filtrados en Excel",
        data=excel_vto,
        file_name="vencimientos_filtrados.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
