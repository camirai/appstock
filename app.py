import io
from datetime import datetime

import pandas as pd
import streamlit as st

# ------------------ CONFIG GENERAL ------------------ #
st.set_page_config(
    page_title="FemiBot Stock",
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

    /* Selectbox más chico y con texto completo */
    .stSelectbox > label {
        font-size: 0.85rem;
    }
    .stSelectbox div[data-baseweb="select"] span {
        font-size: 0.85rem;
        white-space: normal;  /* que el texto se envuelva */
    }
    .stSelectbox {
        width: 100% !important;
    }

    /* Tablas: permitir varias líneas de texto */
    td, th {
        white-space: normal;
    }

    /* KPI cards más distintivas */
    .kpi-card {
        background-color: #f1f5f9;
        border-radius: 0.75rem;
        padding: 0.75rem 1rem;
        border: 1px solid #e2e8f0;
        box-shadow: 0 1px 3px rgba(15,23,42,0.08);
    }
    .kpi-label {
        font-size: 0.8rem;
        color: #64748b;
        margin-bottom: 0.25rem;
    }
    .kpi-value {
        font-size: 1.6rem;
        font-weight: 600;
        color: #0f172a;
    }
    </style>
""", unsafe_allow_html=True)


# ------------------ FUNCIONES AUXILIARES ------------------ #

@st.cache_data
def load_data():
    """
    Lee el archivo Stock.xlsx desde /data.
    Cada fila representa 1 material.
    """
    df = pd.read_excel("data/Stock.xlsx")

    # Normalizar nombres de columnas -> internos sin espacios/acentos
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

    # Conversión de fechas (día primero)
    df["Vencimiento"] = pd.to_datetime(df["Vencimiento"], dayfirst=True, errors="coerce")
    df["Desde"] = pd.to_datetime(df["Desde"], dayfirst=True, errors="coerce")

    # Cálculo de días
    hoy = pd.Timestamp(datetime.now().date())
    df["Dias_hasta_vto"] = (df["Vencimiento"] - hoy).dt.days
    df["Dias_en_deposito"] = (hoy - df["Desde"]).dt.days

    # Cada fila = 1 unidad de material
    df["Cantidad"] = 1

    return df


def to_excel(df, sheet_name="Datos"):
    """
    Devuelve un archivo Excel en memoria para descargar.
    """
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name)
    return output.getvalue()


def kpi_card(label, value, help_text=None):
    """
    KPI con estilo de card.
    """
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
    """
    Filtro libre por texto en varias columnas (partida, lote, producto, etc.).
    """
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
    """
    Devuelve opciones ordenadas alfabéticamente como texto,
    evitando errores de tipos mezclados.
    """
    return sorted(df[col].dropna().astype(str).unique()) if col in df.columns else []


# ------------------ CARGA DE DATOS ------------------ #

df_raw = load_data()

st.title("📊 FemiBot Stock")
st.caption("Visualización dinámica de inventario y vencimientos de materiales.")


# ------------------ SIDEBAR: BUSCADOR + FILTROS ------------------ #

st.sidebar.header("🔍 Buscador")
texto_busqueda = st.sidebar.text_input(
    "Buscar por producto, lote, partida, etc.",
    placeholder="Ej: ONYX, 0D737, 001259084..."
)

df_filtrado = aplicar_busqueda(df_raw, texto_busqueda)

st.sidebar.header("🎛️ Filtros")

# Filtro cascada 1: Depósito
dep_options = opciones_ordenadas(df_filtrado, "Deposito")
dep_sel = st.sidebar.selectbox(
    "Depósito",
    options=["Todos"] + dep_options,
    index=0
)
if dep_sel != "Todos":
    df_filtrado = df_filtrado[df_filtrado["Deposito"].astype(str) == dep_sel]

# Filtro cascada 2: Línea
linea_options = opciones_ordenadas(df_filtrado, "Linea")
linea_sel = st.sidebar.selectbox(
    "Línea",
    options=["Todos"] + linea_options,
    index=0
)
if linea_sel != "Todos":
    df_filtrado = df_filtrado[df_filtrado["Linea"].astype(str) == linea_sel]

# Filtro cascada 3: Categoría
cat_options = opciones_ordenadas(df_filtrado, "Categoria")
cat_sel = st.sidebar.selectbox(
    "Categoría",
    options=["Todos"] + cat_options,
    index=0
)
if cat_sel != "Todos":
    df_filtrado = df_filtrado[df_filtrado["Categoria"].astype(str) == cat_sel]

# Filtro cascada 4: Producto
prod_options = opciones_ordenadas(df_filtrado, "Producto")
prod_sel = st.sidebar.selectbox(
    "Producto",
    options=["Todos"] + prod_options,
    index=0
)
if prod_sel != "Todos":
    df_filtrado = df_filtrado[df_filtrado["Producto"].astype(str) == prod_sel]

# Filtro cascada 5: Medida
med_options = opciones_ordenadas(df_filtrado, "Medida")
med_sel = st.sidebar.selectbox(
    "Medida",
    options=["Todos"] + med_options,
    index=0
)
if med_sel != "Todos":
    df_filtrado = df_filtrado[df_filtrado["Medida"].astype(str) == med_sel]


# ------------------ PESTAÑAS PRINCIPALES ------------------ #

tab_inv, tab_vto = st.tabs(["📦 Inventario", "⏰ Vencimientos"])


# ------------------ TAB INVENTARIO ------------------ #

with tab_inv:
    st.subheader("Inventario actual")

    # KPIs: cada fila = 1 material
    total_materiales = int(df_filtrado["Cantidad"].sum()) if "Cantidad" in df_filtrado.columns else len(df_filtrado)
    depositos_unicos = df_filtrado["Deposito"].nunique() if "Deposito" in df_filtrado.columns else 0
    promedio_dias_deposito = (
        int(df_filtrado["Dias_en_deposito"].mean())
        if "Dias_en_deposito" in df_filtrado.columns and not df_filtrado["Dias_en_deposito"].isna().all()
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

    # Orden de columnas para mostrar
    cols_orden = [
        "Deposito", "Linea", "Categoria", "Producto", "Medida",
        "Partida", "Secuencia", "Partida_completa", "Secuencia_modif",
        "Lote", "Desde", "Dias_en_deposito",
        "Vencimiento", "Dias_hasta_vto"
    ]
    cols_existentes = [c for c in cols_orden if c in df_filtrado.columns]
    otros = [c for c in df_filtrado.columns if c not in cols_existentes]
    df_inv_view = df_filtrado[cols_existentes + otros]

    st.dataframe(df_inv_view, use_container_width=True)

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

    # Controles específicos de vencimiento SOLO acá
    st.markdown("#### ⏰ Configuración de vencimientos")
    col_cfg1, col_cfg2 = st.columns([1, 3])
    with col_cfg1:
        estado_vto = st.radio(
            "Estado de vencimiento",
            options=["Todos", "Solo próximos", "Solo vencidos"],
            help="Afecta la vista de esta pestaña."
        )
    with col_cfg2:
        max_dias_proximos = st.slider(
            "Días hasta vencimiento (para 'próximos')",
            min_value=1,
            max_value=180,
            value=30
        )

    df_vto = df_filtrado.copy()
    if "Vencimiento" in df_vto.columns:
        df_vto = df_vto[df_vto["Vencimiento"].notna()]

    # Aplicar estado de vencimiento
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

    # KPIs para vencimientos
    total_vto = len(df_vto)
    cant_vencidos = int((df_vto["Dias_hasta_vto"] < 0).sum()) if "Dias_hasta_vto" in df_vto.columns else 0
    cant_proximos = int(
        ((df_vto["Dias_hasta_vto"] >= 0) & (df_vto["Dias_hasta_vto"] <= max_dias_proximos)).sum()
    ) if "Dias_hasta_vto" in df_vto.columns else 0

    col1, col2, col3 = st.columns(3)
    with col1:
        kpi_card("Materiales (vista vencimientos)", total_vto)
    with col2:
        kpi_card("Vencidos", cant_vencidos)
    with col3:
        kpi_card(f"Próx. ≤ {max_dias_proximos} días", cant_proximos)

    st.markdown("### Detalle de vencimientos")

    cols_orden_vto = [
        "Deposito", "Linea", "Categoria", "Producto", "Medida",
        "Partida", "Secuencia", "Partida_completa", "Secuencia_modif",
        "Lote", "Desde", "Dias_en_deposito",
        "Vencimiento", "Dias_hasta_vto"
    ]
    cols_existentes_vto = [c for c in cols_orden_vto if c in df_vto.columns]
    otros_vto = [c for c in df_vto.columns if c not in cols_existentes_vto]
    df_vto_view = df_vto[cols_existentes_vto + otros_vto]

    st.dataframe(df_vto_view, use_container_width=True)

    excel_vto = to_excel(df_vto_view, sheet_name="Vencimientos")
    st.download_button(
        label="⬇️ Descargar vencimientos filtrados en Excel",
        data=excel_vto,
        file_name="vencimientos_filtrados.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
