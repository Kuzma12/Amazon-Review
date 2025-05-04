import pandas as pd
import plotly.express as px
from dash import Dash, dcc, html, Input, Output

# Load and clean data
df = pd.read_csv("amazon.csv")
df.columns = df.columns.str.strip()

# Extract raw category (first part before "|")
df["raw_category"] = df["category"].astype(str).apply(lambda x: x.split("|")[0] if pd.notna(x) else "Unknown")

# Create a display version with better formatting
df["display_category"] = (
    df["raw_category"]
    .str.replace(r"([a-z])([A-Z])", r"\1 \2", regex=True)      # camelCase → spaced
    .str.replace(r"\s*&\s*", " & ", regex=True)                # clean up &
    .str.strip()
)

# Clean numeric columns
df["rating"] = pd.to_numeric(df["rating"], errors="coerce")
df["discount_percentage"] = pd.to_numeric(df["discount_percentage"].str.replace("%", ""), errors="coerce")
df["rating_count"] = pd.to_numeric(df["rating_count"], errors="coerce")
df["product_link"] = df["product_link"].fillna("No link")
df["img_link"] = df["img_link"].fillna("No image")

# Drop incomplete rows
df = df.dropna(subset=["rating", "discount_percentage", "rating_count"])

# Generate dropdown options
category_map = df[["raw_category", "display_category"]].drop_duplicates().sort_values("display_category")
categories = category_map.to_dict("records")

# Dash app setup
app = Dash(__name__)
app.title = "Amazon Product Review Dashboard"

app.layout = html.Div(style={
    "fontFamily": "'Segoe UI', sans-serif",
    "backgroundColor": "#f4f6f8",
    "padding": "2rem",
    "color": "#2c3e50"
}, children=[
    html.Div(style={"textAlign": "center", "marginBottom": "2rem"}, children=[
        html.H1("📦 Amazon Product Review Dashboard", style={
            "fontSize": "2.5rem",
            "fontWeight": "600",
            "color": "#2c3e50",
            "textShadow": "1px 1px #ddd"
        })
    ]),

    html.Div(style={
        "backgroundColor": "#ffffff",
        "padding": "1.5rem 2rem",
        "borderRadius": "12px",
        "boxShadow": "0 4px 12px rgba(0,0,0,0.05)",
        "marginBottom": "2rem",
        "maxWidth": "700px",
        "marginLeft": "auto",
        "marginRight": "auto"
    }, children=[
        html.Label("Select a Category:", style={"fontWeight": "bold", "marginBottom": "0.5rem"}),
        dcc.Dropdown(
            id="category-dropdown",
            options=[{"label": c["display_category"], "value": c["raw_category"]} for c in categories],
            value=categories[0]["raw_category"],
            style={
                "marginBottom": "1.5rem",
                "borderRadius": "6px",
                "padding": "0.4rem",
                "border": "1px solid #ccc"
            }
        ),
        html.Label("Minimum Rating Count:", style={"fontWeight": "bold", "marginBottom": "0.5rem"}),
        dcc.Slider(
            id="rating-count-slider",
            min=0,
            max=500,
            step=10,
            value=50,
            marks={0: '0', 100: '100', 200: '200', 500: '500'},
            tooltip={"placement": "bottom", "always_visible": True}
        ),
    ]),

    html.Div(style={"marginBottom": "2rem", "padding": "0 1rem"}, children=[
        html.H2("⭐ Top Rated Products", style={
            "color": "#34495e",
            "marginBottom": "1rem",
            "fontWeight": "600"
        }),
        dcc.Graph(id="rating-bar-chart", config={"displayModeBar": False})
    ]),

    html.Div(style={"padding": "0 1rem"}, children=[
        html.H2("📉 Discount % vs Rating", style={
            "color": "#34495e",
            "marginBottom": "1rem",
            "fontWeight": "600"
        }),
        dcc.Graph(id="discount-vs-rating", config={"displayModeBar": False})
    ])
])

@app.callback(
    Output("rating-bar-chart", "figure"),
    Output("discount-vs-rating", "figure"),
    Input("category-dropdown", "value"),
    Input("rating-count-slider", "value")
)
def update_graphs(selected_category, min_votes):
    filtered_df = df[(df["raw_category"] == selected_category) & (df["rating_count"] >= min_votes)]
    filtered_df["short_name"] = filtered_df["product_name"].str.slice(0, 50) + "..."

    # Bar chart
    bar_fig = px.bar(
        filtered_df.sort_values("rating", ascending=False).head(10),
        y="short_name",
        x="rating",
        orientation="h",
        labels={"short_name": "Product", "rating": "Rating"},
        height=400,
        color_discrete_sequence=["#3498db"]
    )
    bar_fig.update_layout(
        plot_bgcolor="#f9f9f9",
        paper_bgcolor="#f9f9f9",
        font_color="#333",
        yaxis=dict(autorange="reversed")
    )

    # Scatter plot
    scatter_fig = px.scatter(
        filtered_df,
        x="discount_percentage",
        y="rating",
        labels={"discount_percentage": "Discount %", "rating": "Rating"},
        hover_data={
            "product_name": True,
            "product_link": True,
            "img_link": True,
            "rating_count": True
        },
        height=400,
        color_discrete_sequence=["#e74c3c"]
    )
    scatter_fig.update_layout(
        plot_bgcolor="#f9f9f9",
        paper_bgcolor="#f9f9f9",
        font_color="#333"
    )

    return bar_fig, scatter_fig

if __name__ == "__main__":
    import os
port = int(os.environ.get("PORT", 8050))
app.run(host="0.0.0.0", port=port)

