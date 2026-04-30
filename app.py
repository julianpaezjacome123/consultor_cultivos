import streamlit as st
import pandas as pd

# 1. Configuración de la página (para que se vea presentable, no como un bloc de notas)
st.set_page_config(
    page_title="Consulta Agrícola Colombia",
    page_icon="🌾",
    layout="wide"
)

# 2. CACHÉ DE DATOS: Esto es de vida o muerte. 
# @st.cache_data le dice a Streamlit: "Lee esto una vez y no me vuelvas a joder con el Excel a menos que cambie".
@st.cache_data
def cargar_datos():
    archivo_excel = '20250617_BaseAgricola20192024.xlsx'
    try:
        # Cargamos el Excel. openpyxl es obligatorio, recuerda ponerlo en tus requirements.txt
        df = pd.read_excel(archivo_excel)
        
        # Limpieza rápida: asegurar que las métricas numéricas sean realmente numéricas desde el inicio
        columnas_metricas = ['Área sembrada (ha)', 'Área cosechada (ha)', 'Producción (t)']
        for col in columnas_metricas:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
                
        return df
    except FileNotFoundError:
        return None

# Título y encabezado
st.title("🌾 Consulta de Desempeño Agrícola (2019 - 2024)")
st.markdown("""
Esta herramienta te permite explorar la producción agrícola por departamento y cultivo. 
*Usa los filtros de la barra lateral para comenzar la magia.*
""")

# Intentamos cargar los datos
with st.spinner('Cargando la bestia de Excel... aguanta un segundo.'):
    df = cargar_datos()

if df is None:
    # Si el archivo no está, mostramos un error rojo sangre y detenemos todo.
    st.error("🚨 ¡Houston, tenemos un problema! No se encontró el archivo Excel `20250617_BaseAgricola20192024.xlsx`.")
    st.stop()

# 3. INTERFAZ DE USUARIO: BARRA LATERAL (Sidebar)
st.sidebar.header("Filtros de Búsqueda 🔍")

# En lugar de dejar que el usuario escriba, le damos una lista de los que sí existen en el Excel.
# Limpiamos los NA por si acaso tu Excel viene con celdas vacías.
lista_deptos = sorted(df['Departamento'].dropna().unique().tolist())
depto_seleccionado = st.sidebar.selectbox("1. Selecciona el Departamento:", ["Todos"] + lista_deptos)

# Filtramos los cultivos dependiendo del departamento seleccionado para no mostrar cultivos que no crecen ahí.
if depto_seleccionado != "Todos":
    df_temp = df[df['Departamento'] == depto_seleccionado]
else:
    df_temp = df

lista_cultivos = sorted(df_temp['Cultivo'].dropna().unique().tolist())
cultivo_seleccionado = st.sidebar.selectbox("2. Selecciona el Cultivo:", ["Todos"] + lista_cultivos)

# 4. APLICAR FILTROS A LA BASE DE DATOS
df_filtrado = df.copy()

if depto_seleccionado != "Todos":
    df_filtrado = df_filtrado[df_filtrado['Departamento'] == depto_seleccionado]

if cultivo_seleccionado != "Todos":
    df_filtrado = df_filtrado[df_filtrado['Cultivo'] == cultivo_seleccionado]

# 5. MOSTRAR RESULTADOS
if df_filtrado.empty:
    st.warning("🤷‍♂️ No se encontraron registros para esta combinación. Quizás ahí no siembran eso.")
else:
    st.success(f"¡Bingo! Encontramos **{len(df_filtrado)}** registros.")
    
    # --- MÉTRICAS GLOBALES ---
    st.subheader("Resumen General de la Selección")
    col1, col2, col3 = st.columns(3)
    
    total_sembrada = df_filtrado['Área sembrada (ha)'].sum()
    total_cosechada = df_filtrado['Área cosechada (ha)'].sum()
    total_produccion = df_filtrado['Producción (t)'].sum()
    
    # Le metemos formato con separador de miles para que no sea un bloque de números ilegible
    col1.metric("Total Área Sembrada (ha)", f"{total_sembrada:,.2f}")
    col2.metric("Total Área Cosechada (ha)", f"{total_cosechada:,.2f}")
    col3.metric("Total Producción (t)", f"{total_produccion:,.2f}")
    
    st.divider() # Una línea separadora visual

    # --- RESUMEN ANUAL ---
    st.subheader("📈 Resumen Departamental por Año")
    if 'Año' in df_filtrado.columns:
        resumen_anual = df_filtrado.groupby('Año')[['Área sembrada (ha)', 'Área cosechada (ha)', 'Producción (t)']].sum().reset_index()
        
        # Mostramos la tabla. use_container_width hace que ocupe todo el ancho disponible.
        st.dataframe(resumen_anual, use_container_width=True, hide_index=True)
        
        # Ya que estamos en Streamlit, ¿por qué no un gráfico? Es gratis y se ve pro.
        st.write("**Tendencia de Producción (t) por Año**")
        st.bar_chart(data=resumen_anual, x='Año', y='Producción (t)')
    else:
        st.info("La columna 'Año' no está disponible para hacer el resumen temporal.")

    st.divider()

    # --- DETALLE MUNICIPAL ---
    # En lugar de un input 's/n', usamos un "Expander" (un acordeón que se despliega). 
    # Mantiene la interfaz limpia y solo muestra la megatabla si el usuario quiere.
    with st.expander("Ver detalle completo por Municipio y Periodo 🔎"):
        columnas_detalle = ['Año', 'Municipio', 'Cultivo', 'Área sembrada (ha)', 
                            'Área cosechada (ha)', 'Producción (t)', 'Rendimiento (t/ha)']
        
        # Filtramos solo las que existen para que Pandas no explote
        columnas_presentes = [col for col in columnas_detalle if col in df_filtrado.columns]
        
        st.dataframe(df_filtrado[columnas_presentes], use_container_width=True, hide_index=True)
        
        # Opcional: Un botoncito para que el usuario descargue ese detalle filtrado en CSV
        csv = df_filtrado[columnas_presentes].to_csv(index=False).encode('utf-8')
        st.download_button(
            label="⬇️ Descargar esta tabla en CSV",
            data=csv,
            file_name=f'detalle_{depto_seleccionado}_{cultivo_seleccionado}.csv',
            mime='text/csv',
        )