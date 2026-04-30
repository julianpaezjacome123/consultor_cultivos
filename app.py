import streamlit as st
import pandas as pd

# 1. Configuración de la página (Para que se vea profesional)
st.set_page_config(
    page_title="Consulta Agrícola Colombia",
    page_icon="🌾",
    layout="wide"
)

# 2. CACHÉ DE DATOS ADAPTADO PARA ARCHIVOS SUBIDOS
# Aquí está la diferencia clave. Ya no leemos un archivo quemado, 
# leemos el archivo que el usuario sube a la web.
@st.cache_data
def cargar_datos(archivo_cargado):
    try:
        # Leemos directamente el archivo que se subió
        df = pd.read_excel(archivo_cargado)
        
        # Limpieza para que no revienten las sumas matemáticas
        columnas_metricas = ['Área sembrada (ha)', 'Área cosechada (ha)', 'Producción (t)']
        for col in columnas_metricas:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
                
        return df
    except Exception as e:
        st.error(f"Pifiaste al leer el archivo. Detalle: {e}")
        return None

# Título y encabezado
st.title("🌾 Consulta de Desempeño Agrícola (2019 - 2024)")
st.markdown("""
Bienvenido al oráculo agrícola. Para empezar la magia, **sube tu base de datos (.xlsx)** en el menú de la izquierda y luego juega con los filtros.
""")

# 3. INTERFAZ DE USUARIO: BARRA LATERAL (Sidebar)
st.sidebar.header("📁 1. Carga de Datos")

# ESTA ES LA MAGIA DEL CÓDIGO ACTUALIZADO: El botón para subir el archivo
archivo_subido = st.sidebar.file_uploader("Sube tu archivo Excel (.xlsx)", type=["xlsx"])

# Si no han subido nada, frenamos todo para que no salgan errores rojos horribles
if archivo_subido is None:
    st.info("👈 Sube un archivo Excel en la barra lateral para arrancar el análisis.")
    st.stop() # Frena la ejecución aquí. ¡Clave!

# Si llegamos aquí, es porque ya subieron el Excel
with st.spinner('Masticando los datos del Excel... aguanta un segundo.'):
    df = cargar_datos(archivo_subido)

if df is None:
    st.stop()

st.sidebar.divider()

st.sidebar.header("🔍 2. Filtros de Búsqueda")

# Sacamos los departamentos dinámicamente
lista_deptos = sorted(df['Departamento'].dropna().unique().tolist())
depto_seleccionado = st.sidebar.selectbox("Selecciona el Departamento:", ["Todos"] + lista_deptos)

# Filtro en cascada para los cultivos
if depto_seleccionado != "Todos":
    df_temp = df[df['Departamento'] == depto_seleccionado]
else:
    df_temp = df

lista_cultivos = sorted(df_temp['Cultivo'].dropna().unique().tolist())
cultivo_seleccionado = st.sidebar.selectbox("Selecciona el Cultivo:", ["Todos"] + lista_cultivos)

# 4. APLICAR FILTROS
df_filtrado = df.copy()

if depto_seleccionado != "Todos":
    df_filtrado = df_filtrado[df_filtrado['Departamento'] == depto_seleccionado]

if cultivo_seleccionado != "Todos":
    df_filtrado = df_filtrado[df_filtrado['Cultivo'] == cultivo_seleccionado]

# 5. MOSTRAR RESULTADOS
if df_filtrado.empty:
    st.warning("🤷‍♂️ No se encontraron registros para esta combinación. Quizás el clima no ayuda ahí.")
else:
    st.success(f"¡Bingo! Encontramos **{len(df_filtrado)}** registros.")
    
    # --- MÉTRICAS GLOBALES ---
    st.subheader("Resumen General de tu Selección")
    col1, col2, col3 = st.columns(3)
    
    total_sembrada = df_filtrado['Área sembrada (ha)'].sum()
    total_cosechada = df_filtrado['Área cosechada (ha)'].sum()
    total_produccion = df_filtrado['Producción (t)'].sum()
    
    col1.metric("Total Área Sembrada (ha)", f"{total_sembrada:,.2f}")
    col2.metric("Total Área Cosechada (ha)", f"{total_cosechada:,.2f}")
    col3.metric("Total Producción (t)", f"{total_produccion:,.2f}")
    
    st.divider()

    # --- RESUMEN ANUAL ---
    st.subheader("📈 Resumen Departamental por Año")
    if 'Año' in df_filtrado.columns:
        resumen_anual = df_filtrado.groupby('Año')[['Área sembrada (ha)', 'Área cosechada (ha)', 'Producción (t)']].sum().reset_index()
        
        st.dataframe(resumen_anual, use_container_width=True, hide_index=True)
        
        st.write("**Tendencia de Producción (t) por Año**")
        st.bar_chart(data=resumen_anual, x='Año', y='Producción (t)')
    else:
        st.info("La columna 'Año' no está disponible en este archivo.")

    st.divider()

    # --- DETALLE MUNICIPAL ---
    with st.expander("Ver detalle completo por Municipio y Periodo 🔎"):
        columnas_detalle = ['Año', 'Municipio', 'Cultivo', 'Área sembrada (ha)', 
                            'Área cosechada (ha)', 'Producción (t)', 'Rendimiento (t/ha)']
        
        columnas_presentes = [col for col in columnas_detalle if col in df_filtrado.columns]
        
        st.dataframe(df_filtrado[columnas_presentes], use_container_width=True, hide_index=True)
        
        csv = df_filtrado[columnas_presentes].to_csv(index=False).encode('utf-8')
        st.download_button(
            label="⬇️ Descargar esta tabla en CSV",
            data=csv,
            file_name=f'detalle_{depto_seleccionado}_{cultivo_seleccionado}.csv',
            mime='text/csv',
        )
