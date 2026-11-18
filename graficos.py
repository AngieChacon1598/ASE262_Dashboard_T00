import plotly.graph_objects as go

from analisis import (
    agrupar_por_producto,
    contar_ventas_por_estado,
    normalizar_texto,
    ventas_por_canal,
    ventas_por_categoria,
    ventas_por_ciudad,
    ventas_por_estado,
    ventas_por_fecha,
    ventas_por_producto,
    ventas_por_region,
    ventas_por_vendedor,
)


COLORES = ["#3157A4", "#438A76", "#D59B3D", "#755B9D", "#3B8A9B", "#B95D55"]
COLOR_ESTADOS = {
    "completada": "#438A76",
    "pendiente": "#D59B3D",
    "cancelada": "#B95D55",
}


def _estilo_base(figura, titulo, altura=370):
    figura.update_layout(
        title=dict(text=titulo, x=0.03, xanchor="left", font=dict(size=15, color="#172033")),
        template="plotly_white",
        autosize=True,
        height=altura,
        margin=dict(l=20, r=28, t=58, b=35),
        font=dict(family="Segoe UI, Arial, sans-serif", color="#526078", size=11),
        hoverlabel=dict(bgcolor="#14213D", font_color="#FFFFFF"),
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#FFFFFF",
    )
    figura.update_xaxes(showgrid=True, gridcolor="#EDF0F4", zeroline=False)
    figura.update_yaxes(showgrid=False, zeroline=False)
    if not figura.data:
        figura.add_annotation(
            text="No hay datos disponibles para mostrar.",
            x=0.5,
            y=0.48,
            xref="paper",
            yref="paper",
            showarrow=False,
            font=dict(size=13, color="#68738A"),
        )
    return figura


def _grafico_barras(resumen, titulo, entidad, monetario=False, color=COLORES[0]):
    figura = go.Figure()
    ordenados = sorted(resumen.items(), key=lambda item: item[1])
    if ordenados:
        etiquetas, valores = zip(*ordenados)
        formato = "S/ {:,.2f}".format if monetario else "{:,.0f}".format
        figura.add_trace(
            go.Bar(
                x=list(valores),
                y=list(etiquetas),
                orientation="h",
                marker_color=color,
                text=[formato(valor) for valor in valores],
                textposition="outside",
                cliponaxis=False,
                hovertemplate=(
                    f"{entidad}: %{{y}}<br>"
                    + ("Importe: S/ %{x:,.2f}" if monetario else "Unidades: %{x:,.0f}")
                    + "<extra></extra>"
                ),
            )
        )
    altura = max(350, min(600, 170 + 30 * len(resumen)))
    figura = _estilo_base(figura, titulo, altura)
    figura.update_layout(margin=dict(l=155, r=48, t=58, b=35), showlegend=False)
    figura.update_xaxes(
        title="Importe (S/)" if monetario else "Unidades",
        tickformat=",.2f" if monetario else ",.0f",
        separatethousands=True,
    )
    figura.update_yaxes(title=None)
    return figura


def _grafico_dona(resumen, titulo, entidad, monetario=False):
    figura = go.Figure()
    if resumen:
        etiquetas = list(resumen.keys())
        valores = list(resumen.values())
        colores = [
            COLOR_ESTADOS.get(normalizar_texto(etiqueta), COLORES[indice % len(COLORES)])
            for indice, etiqueta in enumerate(etiquetas)
        ]
        figura.add_trace(
            go.Pie(
                labels=etiquetas,
                values=valores,
                hole=0.62,
                marker=dict(colors=colores, line=dict(color="#FFFFFF", width=2)),
                textinfo="percent",
                textposition="inside",
                sort=False,
                hovertemplate=(
                    f"{entidad}: %{{label}}<br>"
                    + ("Importe: S/ %{value:,.2f}" if monetario else "Operaciones: %{value:,.0f}")
                    + "<br>Participación: %{percent}<extra></extra>"
                ),
            )
        )
    _estilo_base(figura, titulo, 380)
    figura.update_layout(
        showlegend=True,
        legend=dict(orientation="h", x=0.5, xanchor="center", y=-0.08, yanchor="top"),
        margin=dict(l=20, r=20, t=58, b=70),
    )
    return figura


def grafico_barras(datos):
    return _grafico_barras(
        agrupar_por_producto(datos, solo_completadas=True),
        "Unidades vendidas por producto",
        "Producto",
        color=COLORES[0],
    )


def grafico_dona(datos):
    return _grafico_barras(
        ventas_por_producto(datos, solo_completadas=True),
        "Ventas completadas por producto",
        "Producto",
        monetario=True,
        color=COLORES[1],
    )


def grafico_vendedores(datos):
    return _grafico_barras(
        ventas_por_vendedor(datos, solo_completadas=True),
        "Ventas completadas por vendedor",
        "Vendedor",
        monetario=True,
        color=COLORES[1],
    )


def grafico_categorias(datos):
    return _grafico_dona(
        ventas_por_categoria(datos, solo_completadas=True),
        "Ventas completadas por categoría",
        "Categoría",
        monetario=True,
    )


def grafico_canales(datos):
    return _grafico_barras(
        ventas_por_canal(datos, solo_completadas=True),
        "Ventas completadas por canal",
        "Canal",
        monetario=True,
        color=COLORES[2],
    )


def grafico_ciudades(datos):
    return _grafico_barras(
        ventas_por_ciudad(datos, solo_completadas=True),
        "Ventas completadas por ciudad",
        "Ciudad",
        monetario=True,
        color=COLORES[3],
    )


def grafico_regiones(datos):
    return _grafico_dona(
        ventas_por_region(datos, solo_completadas=True),
        "Distribución de ventas completadas por región",
        "Región",
        monetario=True,
    )


def grafico_estados(datos):
    figura = go.Figure()
    resumen = ventas_por_estado(datos)
    for estado, importe in resumen.items():
        figura.add_trace(
            go.Bar(
                x=[importe],
                y=[estado],
                orientation="h",
                name=estado,
                marker_color=COLOR_ESTADOS.get(
                    normalizar_texto(estado), COLORES[len(figura.data) % len(COLORES)]
                ),
                text=[f"S/ {importe:,.2f}"],
                textposition="outside",
                cliponaxis=False,
                hovertemplate="Estado: %{y}<br>Importe: S/ %{x:,.2f}<extra></extra>",
            )
        )
    _estilo_base(figura, "Importe por estado de venta", 350)
    figura.update_layout(
        barmode="group",
        showlegend=True,
        legend=dict(orientation="h", x=0.5, xanchor="center", y=-0.1, yanchor="top"),
        margin=dict(l=110, r=48, t=58, b=70),
    )
    figura.update_xaxes(title="Importe (S/)", tickformat=",.2f", separatethousands=True)
    figura.update_yaxes(title=None)
    return figura


def grafico_evolucion_ventas(datos):
    resumen = ventas_por_fecha(datos, solo_completadas=True)
    fechas = sorted(resumen)
    figura = go.Figure()
    if fechas:
        figura.add_trace(
            go.Scatter(
                x=fechas,
                y=[resumen[fecha] for fecha in fechas],
                mode="lines+markers",
                line=dict(color=COLORES[0], width=2.5),
                marker=dict(size=7, color=COLORES[0]),
                fill="tozeroy",
                fillcolor="rgba(49, 87, 164, 0.08)",
                hovertemplate="Fecha: %{x|%d/%m/%Y}<br>Ventas: S/ %{y:,.2f}<extra></extra>",
            )
        )
    _estilo_base(figura, "Evolución de ventas completadas", 370)
    figura.update_xaxes(title="Fecha", type="date", tickformat="%d %b")
    figura.update_yaxes(title="Ventas (S/)", tickformat=",.2f", separatethousands=True)
    return figura


def grafico_cantidad_estados(datos):
    return _grafico_dona(
        contar_ventas_por_estado(datos),
        "Operaciones por estado",
        "Estado",
    )
