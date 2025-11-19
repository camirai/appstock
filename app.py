import io
import pandas as pd
import streamlit as st

# ------------------ CONFIGURACIÓN GENERAL ------------------ #
st.set_page_config(
    page_title="FemiBot Stock",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Pequeño CSS para mejorar mobile
st.markdown("""
    <style>
    /* Achicar padding lateral en mobile */
    .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
        padding-left: 0.8rem;
        padding-right: 0.8rem;
    }

    /* Hacer que los select se vean a ancho completo */
    .stSelectbox, .stMultiSelect {
        width: 100% !important;
    }

    /* Evitar que los textos de las columnas se corten */
    td, th {
        white-space: nowrap;
        text-overflow: ellipsis;
    }
    </style>
""", unsafe_allow_html=True)

# ------------------ FUNCIONES AUXILIARES ------------------ #

@st.cache_data
def load_data():
    # Ajustá los nombres de archivo a los tuyos reales
    df_inv = pd.read_csv("data/inventario.csv")
    df_vto = pd.read_csv("data/vencimientos.csv")
    return df_inv, df_vto

def to_excel(df, sheet_name="Datos"):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name)
    processed_data = output.getvalue()
    return processed_data

def kpi_card(label, value, help_text=None):
    st.metric(label=label, value=value, help=help_text)

# ------------------ CARGA DE DATOS ------------------ #

df_inventario, df_vencimientos = load_data()

# Asegurá que estas columnas existan en tus CSV:
# Deposito, Material, Categoria, Stock, FechaVencimiento

# Si FechaVencimiento está en formato texto, la convertimos
if "FechaVencimiento" in df_vencimientos.columns:
    df_vencimientos["FechaVencimiento"] = pd.to_datetime(
        df_vencimientos["FechaVencimiento"], errors="coerce"
    )

# ------------------ SIDEBAR (FILTROS) ------------------ #

st.sidebar.title("Filtros")

# Filtros comunes
depositos = sorted(df_inventario["Deposito"].dropna().unique().tolist())
materiales = sorted(df_inventario["Material"].dropna().unique().tolist())
categorias = sorted(df_inventario["Categoria"].dropna().unique().tolist())

dep_sel = st.sidebar.multiselect("Depósito", options=depositos, default=depositos)
mat_sel = st.sidebar.multiselect("Material", options=materiales, default=materiales)
cat_sel = st.sidebar.multiselect("Categoría", options=categorias, default=categorias)

# Filtro de rango de vencimiento (solo para tab de vencimientos)
st.sidebar.markdown("---")
st.sidebar.subheader("Vencimientos")
if "FechaVencimiento" in df_vencimientos.columns:
    min_date = df_vencimientos["FechaVencimiento"].min()
    max_date = df_vencimientos["FechaVencimiento"].max()
    fecha_desde, fecha_hasta = st.sidebar.date_input(
        "Rango de fechas",
        value=(min_date, max_date)
    )
else:
    fecha_desde, fecha_hasta = None, None

# ------------------ APLICAR FILTROS ------------------ #

mask_inv = (
    df_inventario["Deposito"].isin(dep_sel) &
    df_inventario["Material"].isin(mat_sel) &
    df_inventario["Categoria"].isin(cat_sel)
)
df_inv_filtrado = df_inventario[mask_inv].copy()

mask_vto = (
    df_vencimientos["Deposito"].isin(dep_sel) &
    df_vencimientos["Material"].isin(mat_sel) &
    df_vencimientos["Categoria"].isin(cat_sel)
)

if fecha_desde and fecha_hasta and "FechaVencimiento" in df_vencimientos.columns:
    mask_vto = mask_vto & (
        (df_vencimientos["FechaVencimiento"] >= pd.to_datetime(fecha_desde)) &
        (df_vencimientos["FechaVencimiento"] <= pd.to_datetime(fecha_hasta))
    )

df_vto_filtrado = df_vencimientos[mask_vto].copy()

# ------------------ CONTENIDO PRINCIPAL ------------------ #

st.title("📊 FemiBot Stock")
st.caption("Visualización dinámica de inventario y vencimientos (válvulas, endoprótesis, etc.)")

tabs = st.tabs(["📦 Inventario", "⏰ Vencimientos"])

# ------------------ TAB INVENTARIO ------------------ #
with tabs[0]:
    st.subheader("Inventario actual")

    col1, col2, col3 = st.columns(3)
    with col1:
        kpi_card("Registros", len(df_inv_filtrado))
    with col2:
        if "Stock" in df_inv_filtrado.columns:
            kpi_card("Stock total", int(df_inv_filtrado["Stock"].sum()))
    with col3:
        kpi_card("Depósitos filtrados", len(dep_sel))

    st.markdown("### Detalle de inventario filtrado")

    st.dataframe(
        df_inv_filtrado,
        use_container_width=True
    )

    # Descarga en Excel
    excel_data = to_excel(df_inv_filtrado, sheet_name="Inventario")
    st.download_button(
        label="⬇️ Descargar inventario filtrado en Excel",
        data=excel_data,
        file_name="inventario_filtrado.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# ------------------ TAB VENCIMIENTOS ------------------ #
with tabs[1]:
    st.subheader("Materiales por vencimiento")

    col1, col2, col3 = st.columns(3)
    with col1:
        kpi_card("Registros", len(df_vto_filtrado))
    with col2:
        if "FechaVencimiento" in df_vto_filtrado.columns and not df_vto_filtrado.empty:
            prox = df_vto_filtrado["FechaVencimiento"].min().date()
            kpi_card("Próximo vencimiento", str(prox))
    with col3:
        if "Stock" in df_vto_filtrado.columns:
            kpi_card("Stock en riesgo", int(df_vto_filtrado["Stock"].sum()))

    st.markdown("### Detalle de vencimientos filtrados")

    st.dataframe(
        df_vto_filtrado,
        use_container_width=True
    )

    excel_data_vto = to_excel(df_vto_filtrado, sheet_name="Vencimientos")
    st.download_button(
        label="⬇️ Descargar vencimientos filtrados en Excel",
        data=excel_data_vto,
        file_name="vencimientos_filtrados.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
