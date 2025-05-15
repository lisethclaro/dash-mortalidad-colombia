import pandas as pd
import dash
from dash import dcc, html, Input, Output
import plotly.express as px
import json
import calendar
from dash import dash_table
from typing import cast, List, Dict, Any


# Cargar archivos
df_mortalidad = pd.read_excel("datasets/Anexo1.NoFetal2019_CE_15-03-23.xlsx")
df_codigos = pd.read_excel("datasets/Anexo2.CodigosDeMuerte_CE_15-03-23.xlsx")
df_divipola = pd.read_excel("datasets/Anexo3.Divipola_CE_15-03-23.xlsx")

# Mostrar primeras filas
print(df_mortalidad.head())
print(df_codigos.head())
print(df_divipola.head())

# Verifica las columnas disponibles en df_codigos
print(df_codigos.columns.tolist())
print("Columnas en df_mortalidad:", df_mortalidad.columns.tolist())
# Unir descripción de causa básica de muerte
df_mortalidad = df_mortalidad.merge(
    df_codigos[['Código de la CIE-10 cuatro caracteres', 'Descripcion  de códigos mortalidad a cuatro caracteres']],
    left_on='COD_MUERTE', right_on='Código de la CIE-10 cuatro caracteres', how='left'
)

# Unir información DIVIPOLA (departamento y municipio)
df_mortalidad = df_mortalidad.merge(
    df_divipola[['COD_DEPARTAMENTO', 'DEPARTAMENTO', 'COD_MUNICIPIO', 'MUNICIPIO']],
    left_on=['COD_DEPARTAMENTO', 'COD_MUNICIPIO'],
    right_on=['COD_DEPARTAMENTO', 'COD_MUNICIPIO'],
    how='left'
)

# Agrupar muertes por departamento y limpiar nombres
muertes_por_departamento = df_mortalidad.groupby('DEPARTAMENTO').size().reset_index(name='Muertes')

# 3. Normalización de nombres (versión mejorada)
muertes_por_departamento['DEPARTAMENTO'] = muertes_por_departamento['DEPARTAMENTO'].str.upper().str.strip()

# 4. Diccionario de mapeo completo y actualizado
mapeo_departamentos = {
 # Mapeo PRINCIPAL (de datos a GeoJSON)
    'BOGOTÁ D.C.': 'SANTAFE DE BOGOTA D.C',
    'BOGOTÁ, D.C.': 'SANTAFE DE BOGOTA D.C',
    'BOGOTA D.C.': 'SANTAFE DE BOGOTA D.C',
    'BOGOTA': 'SANTAFE DE BOGOTA D.C',
    'BOGOTÁ': 'SANTAFE DE BOGOTA D.C',
    
    # Distritos especiales (asignar a departamentos)
    'BARRANQUILLA D.E.': 'ATLANTICO',
    'BUENAVENTURA D.E.': 'VALLE DEL CAUCA',
    'CARTAGENA D.T. Y C.': 'BOLIVAR',
    'SANTA MARTA D.T. Y C.': 'MAGDALENA',
    
    # Otros departamentos (de datos a GeoJSON)
    'ARCHIPIÉLAGO DE SAN ANDRÉS, PROVIDENCIA Y SANTA CATALINA': 'ARCHIPIELAGO DE SAN ANDRES PROVIDENCIA Y SANTA CATALINA',
    'ATLÁNTICO': 'ATLANTICO',
    'BOLÍVAR': 'BOLIVAR',
    'BOYACÁ': 'BOYACA',
    'CAQUETÁ': 'CAQUETA',
    'CHOCÓ': 'CHOCO',
    'CÓRDOBA': 'CORDOBA',
    'GUAINÍA': 'GUAINIA',
    'QUINDÍO': 'QUINDIO',
    'VAUPÉS': 'VAUPES',
    'NORTE DE SANTANDER': 'NORTE DE SANTANDER',  # Este parece coincidir
    
}

# Aplicar mapeo
muertes_por_departamento['DEPARTAMENTO'] = muertes_por_departamento['DEPARTAMENTO'].replace(mapeo_departamentos)

# Cargar GeoJSON
with open("departamentos_colombia.geo.json", encoding='utf-8') as f:
    geojson = json.load(f)

# Crear mapa
fig_mapa = px.choropleth_mapbox(
    muertes_por_departamento,
    geojson=geojson,
    locations='DEPARTAMENTO',
    featureidkey='properties.NOMBRE_DPT',
    color='Muertes',
    color_continuous_scale="Viridis",
    range_color=(0, muertes_por_departamento['Muertes'].max()),
    mapbox_style="carto-positron",
    zoom=4,
    center={"lat": 4.5709, "lon": -74.2973},
    opacity=0.7,
    title="Distribución de muertes por departamento - Colombia 2019",
    labels={'Muertes': 'Número de muertes'}
)
fig_mapa.update_layout(margin={"r":0,"t":40,"l":0,"b":0})


# Crear gráfico de líneas por mes
df_mortalidad['AÑO'] = df_mortalidad['AÑO'].astype(int)
df_mortalidad['MES'] = df_mortalidad['MES'].astype(int)

muertes_mes = df_mortalidad.groupby(['AÑO', 'MES']).size().reset_index(name='Muertes')
muertes_mes['Mes_nombre'] = muertes_mes['MES'].apply(lambda x: calendar.month_name[x])
muertes_mes = muertes_mes.sort_values(['AÑO', 'MES'])

fig_lineas = px.line(
    muertes_mes,
    x='Mes_nombre',
    y='Muertes',
    title='Total de muertes por mes - Colombia 2019',
    markers=True
)
fig_lineas.update_layout(
    xaxis_title='Mes',
    yaxis_title='Número de muertes',
    xaxis=dict(categoryorder='array', categoryarray=list(calendar.month_name)[1:])
)

# grafico de barras

# Filtrar homicidios con códigos X95 a X99 (agresiones con arma de fuego y otros)
codigos_homicidios = ['X95', 'X96', 'X97', 'X98', 'X99']
df_homicidios = df_mortalidad[df_mortalidad['COD_MUERTE'].str[:3].isin(codigos_homicidios)]

# Agrupar por municipio y contar homicidios
muertes_municipio = df_homicidios.groupby('MUNICIPIO').size().reset_index(name='Homicidios')

# Ordenar y quedarnos con el top 5
top5_municipios = muertes_municipio.sort_values(by='Homicidios', ascending=False).head(5)

fig_barras = px.bar(
    top5_municipios,
    x='MUNICIPIO',
    y='Homicidios',
    title='Top 5 ciudades más violentas por homicidios (Códigos X95–X99)',
    labels={'MUNICIPIO': 'Ciudad', 'Homicidios': 'Número de homicidios'},
    color='Homicidios',
    color_continuous_scale='Reds'
)

fig_barras.update_layout(xaxis_title='Ciudad', yaxis_title='Número de homicidios')

#Gráfico circular

# Contar número total de muertes por municipio
muertes_por_municipio = df_mortalidad.groupby('MUNICIPIO').size().reset_index(name='Muertes')

# Eliminar nulos o vacíos (opcional pero recomendado)
muertes_por_municipio = muertes_por_municipio[muertes_por_municipio['MUNICIPIO'].notna()]

# Obtener las 10 ciudades con menor número de muertes
top10_menor_mortalidad = muertes_por_municipio.sort_values(by='Muertes', ascending=True).head(10)

fig_pie = px.pie(
    top10_menor_mortalidad,
    names='MUNICIPIO',
    values='Muertes',
    title='Top 10 ciudades con menor mortalidad - Colombia 2019',
    color_discrete_sequence=px.colors.sequential.Teal
)

# Tabla

# 1. Preparamos los datos
principales_causas = df_mortalidad.groupby(
    ['COD_MUERTE', 'Descripcion  de códigos mortalidad a cuatro caracteres']
).size().reset_index(name='Total')

principales_causas = principales_causas.sort_values(by='Total', ascending=False).head(10)

# 2. Limpieza garantizada de columnas
principales_causas.columns = [str(col).strip() for col in principales_causas.columns]

# 3. Conversión manual segura de los datos
def convert_to_valid_format(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Convierte el DataFrame al formato exacto que necesita Dash"""
    valid_data = []
    for _, row in df.iterrows():
        valid_row = {}
        for col in df.columns:
            # Aseguramos que la clave sea string y el valor sea compatible
            valid_row[str(col)] = row[col]
        valid_data.append(valid_row)
    return valid_data

data = convert_to_valid_format(principales_causas)

# 4. Creamos la tabla con tipos correctos
tabla_causas = dash_table.DataTable(
    columns=[{'name': col, 'id': col} for col in principales_causas.columns],
    data=data,
    style_table={'overflowX': 'auto'},
    style_cell={
        'textAlign': 'left',
        'padding': '5px',
        'fontFamily': 'Arial',
        'fontSize': '14px'
    },
    style_header={
        'backgroundColor': 'lightgrey',
        'fontWeight': 'bold'
    },
    page_size=10
)

# Histograma

# Asegúrate de que la columna de edad sea numérica
df_mortalidad['GRUPO_EDAD1'] = pd.to_numeric(df_mortalidad['GRUPO_EDAD1'], errors='coerce')

# Crear rangos quinquenales (0–4, 5–9, ..., 85+)
bins = list(range(0, 90, 5)) + [999]  # 0, 5, 10, ..., 85, 999 para 85+
labels = [f"{i}-{i+4}" for i in range(0, 85, 5)] + ["85+"]

df_mortalidad['rango_edad'] = pd.cut(df_mortalidad['GRUPO_EDAD1'], bins=bins, labels=labels, right=False)

# Contar muertes por rango de edad
muertes_por_edad = df_mortalidad['rango_edad'].value_counts().sort_index().reset_index()
muertes_por_edad.columns = ['Rango de Edad', 'Muertes']

fig_histograma_edad = px.bar(
    muertes_por_edad,
    x='Rango de Edad',
    y='Muertes',
    title='Distribución de muertes por rangos de edad quinquenales (Colombia 2019)',
    labels={'Muertes': 'Número de muertes', 'Rango de Edad': 'Edad'},
    color='Muertes',
    color_continuous_scale='plasma'
)

# Gráfico de barras apiladas

# Agrupar número de muertes por departamento y sexo
muertes_dep_sexo = df_mortalidad.groupby(['DEPARTAMENTO', 'SEXO']).size().reset_index(name='Muertes')

# Limpieza de nombres de departamento (igual que antes)
muertes_dep_sexo['DEPARTAMENTO'] = muertes_dep_sexo['DEPARTAMENTO'].str.upper().str.strip()
muertes_dep_sexo['DEPARTAMENTO'] = muertes_dep_sexo['DEPARTAMENTO'].replace(mapeo_departamentos)

fig_barras_apiladas = px.bar(
    muertes_dep_sexo,
    x="DEPARTAMENTO",
    y="Muertes",
    color="SEXO",
    title="Muertes por Sexo en cada Departamento - Colombia 2019",
    labels={"DEPARTAMENTO": "Departamento", "Muertes": "Número de muertes", "SEXO": "Sexo"},
    barmode="stack"
)

# Mejora visual: ordenar departamentos por total de muertes
total_muertes_por_dep = muertes_dep_sexo.groupby("DEPARTAMENTO")["Muertes"].sum().sort_values(ascending=False).index
fig_barras_apiladas.update_layout(
    xaxis={'categoryorder':'array', 'categoryarray':total_muertes_por_dep},
    xaxis_tickangle=-45,
    margin={"t":60, "b":100},
    height=600
)

# Crear app Dash
dash_app = dash.Dash(__name__)
app = dash_app.server  # Esto es lo que Gunicorn necesita
dash_app.title = "Mortalidad Colombia 2019"

dash_app.layout  = html.Div([
    html.H1("Análisis de Mortalidad en Colombia (2019)"),
    
    dcc.Tabs([
        dcc.Tab(label="Mapa por Departamento", children=[
            dcc.Graph(figure=fig_mapa)
        ]),
        dcc.Tab(label="Muertes por Mes", children=[
            dcc.Graph(figure=fig_lineas)
        ]),
        dcc.Tab(label="Ciudades más violentas", children=[
            dcc.Graph(figure=fig_barras)
        ]),
        dcc.Tab(label="Ciudades con menor mortalidad", children=[
            dcc.Graph(figure=fig_pie)
        ]),
        dcc.Tab(label="Top 10 causas de muerte", children=[
            html.Div([
                html.H4("Top 10 causas de muerte en Colombia (2019)"),
                tabla_causas
            ])
        ]),
        dcc.Tab(label="Histograma por Rango de Edad", children=[
            html.Div([
                dcc.Graph(figure=fig_histograma_edad)
            ])
        ]),

        dcc.Tab(label="Muertes por Sexo y Departamento", children=[
            html.Div([
                dcc.Graph(figure=fig_barras_apiladas)
            ])
        ])

    ])
])

if __name__ == "__main__":
    dash_app.run_server(host="0.0.0.0", port=8080, debug=False)
