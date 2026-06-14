from translations import t

try:
    import plotly.graph_objects as go
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False


def create_radar_chart(results, ssl_info, robots, lang="ar"):
    if not PLOTLY_AVAILABLE:
        return None

    cat_keys = [
        "radar_cat_title", "radar_cat_desc", "radar_cat_headings", "radar_cat_images",
        "radar_cat_links", "radar_cat_speed", "radar_cat_mobile", "radar_cat_https",
        "radar_cat_ssl", "radar_cat_content",
    ]
    categories = [t(k, lang) for k in cat_keys]

    status_keys = ["title", "description", "headings", "images", "links", "load_time", "mobile", "https"]
    statuses = [results.get(k, {}).get("status") for k in status_keys]
    statuses.append("good" if ssl_info.get("valid") else "bad")
    statuses.append(results.get("content", {}).get("status"))

    values = [100 if s == "good" else 50 if s == "warning" else 10 for s in statuses]
    values.append(values[0])
    categories.append(categories[0])

    fig = go.Figure(data=go.Scatterpolar(
        r=values, theta=categories,
        fill='toself', fillcolor='rgba(0,200,150,0.15)',
        line=dict(color='#00c896', width=2),
        marker=dict(size=6, color='#00c896'),
    ))
    font_family = "Cairo" if lang == "ar" else "Inter"
    fig.update_layout(
        polar=dict(
            bgcolor="#0a1525",
            radialaxis=dict(visible=True, range=[0, 100], gridcolor="#152236", tickfont=dict(color="#4a6080")),
            angularaxis=dict(gridcolor="#152236", tickfont=dict(size=11, family=font_family, color="#e2e8f0")),
        ),
        showlegend=False, paper_bgcolor="#060d1a", plot_bgcolor="#0a1525",
        margin=dict(t=30, b=30, l=60, r=60),
        height=400,
    )
    return fig


def create_scores_bar(results, ssl_info, lang="ar"):
    if not PLOTLY_AVAILABLE:
        return None

    item_keys = [
        ("radar_cat_title", "title"), ("radar_cat_desc", "description"),
        ("radar_cat_headings", "headings"), ("radar_cat_images", "images"),
        ("radar_cat_links", "links"), ("radar_cat_speed", "load_time"),
        ("radar_cat_mobile", "mobile"), ("radar_cat_https", "https"),
        ("radar_cat_canonical", "canonical"), ("radar_cat_og", "opengraph"),
        ("radar_cat_schema", "schema"), ("radar_cat_content", "content"),
    ]

    names = [t(label_key, lang) for label_key, _ in item_keys]
    statuses = [results.get(data_key, {}).get("status") for _, data_key in item_keys]
    values = [100 if s == "good" else 50 if s == "warning" else 10 for s in statuses]
    colors = ["#00c896" if s == "good" else "#f59e0b" if s == "warning" else "#ef4444" for s in statuses]

    font_family = "Cairo" if lang == "ar" else "Inter"
    fig = go.Figure(data=go.Bar(
        x=values, y=names, orientation='h',
        marker_color=colors, text=values, textposition='outside',
        textfont=dict(color="#e2e8f0", size=11),
    ))
    fig.update_layout(
        xaxis=dict(range=[0, 115], gridcolor="#152236", tickfont=dict(color="#4a6080"), showticklabels=False),
        yaxis=dict(tickfont=dict(size=12, family=font_family, color="#e2e8f0"), autorange="reversed"),
        paper_bgcolor="#060d1a", plot_bgcolor="#0a1525",
        margin=dict(t=10, b=10, l=100, r=40),
        height=400,
    )
    return fig


def create_comparison_radar(results1, results2, domain1, domain2, lang="ar"):
    if not PLOTLY_AVAILABLE:
        return None

    cat_keys = [
        "radar_cat_title", "radar_cat_desc", "radar_cat_headings", "radar_cat_images",
        "radar_cat_links", "radar_cat_speed", "radar_cat_mobile", "radar_cat_https", "radar_cat_content",
    ]
    categories = [t(k, lang) for k in cat_keys]
    data_keys = ["title", "description", "headings", "images", "links", "load_time", "mobile", "https", "content"]

    vals1 = [100 if results1.get(k, {}).get("status") == "good" else 50 if results1.get(k, {}).get("status") == "warning" else 10 for k in data_keys]
    vals2 = [100 if results2.get(k, {}).get("status") == "good" else 50 if results2.get(k, {}).get("status") == "warning" else 10 for k in data_keys]
    vals1.append(vals1[0])
    vals2.append(vals2[0])
    cats = categories + [categories[0]]

    font_family = "Cairo" if lang == "ar" else "Inter"
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(r=vals1, theta=cats, fill='toself', name=domain1,
        fillcolor='rgba(0,200,150,0.12)', line=dict(color='#00c896', width=2)))
    fig.add_trace(go.Scatterpolar(r=vals2, theta=cats, fill='toself', name=domain2,
        fillcolor='rgba(56,189,248,0.12)', line=dict(color='#38bdf8', width=2)))

    fig.update_layout(
        polar=dict(bgcolor="#0a1525",
            radialaxis=dict(visible=True, range=[0, 100], gridcolor="#152236"),
            angularaxis=dict(gridcolor="#152236", tickfont=dict(size=11, family=font_family, color="#e2e8f0"))),
        showlegend=True, legend=dict(font=dict(family=font_family, color="#e2e8f0", size=12)),
        paper_bgcolor="#060d1a", plot_bgcolor="#0a1525",
        margin=dict(t=30, b=30, l=60, r=60), height=420,
    )
    return fig
