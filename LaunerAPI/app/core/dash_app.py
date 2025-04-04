from dash import Dash, dcc, html, Input, Output, State
import requests
import dash_bootstrap_components as dbc

FASTAPI_URL = "http://127.0.0.1:8000"

app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server

app.layout = html.Div([
    dcc.Location(id="url", refresh=False),
    html.Div(id="page-content")
])

login_layout = dbc.Container([
    html.Div([
        html.H1("Login", className="text-center mb-4"),

        dbc.Input(id="username", type="text", placeholder="Usuário", className="mb-2"),
        dbc.Input(id="password", type="password", placeholder="Senha", className="mb-2"),
        dbc.Button("Entrar", id="login-button", color="primary", className="w-100"),

        html.Div(id="login-message", className="mt-2"),
    ], style={
        "max-width": "400px",
        "margin": "auto",
        "padding": "20px",
        "border": "1px solid #ccc", 
        "border-radius": "5px", 
        "background-color": "#f9f9f9"
        }, className="mt-5"),
], fluid=True)

dashboard_layout = dbc.Container([
    html.H1("Dashboard", className="text-center mb-4"),
    html.P("Bem-vindo ao dashboard!"),
], fluid=True) 

@app.callback(
    Output("page-content", "children"),
    Input("url", "pathname")
)
def display_page(pathname):
    """Display the appropriate page based on the URL."""
    if pathname == "/dashboard":
        return dashboard_layout
    return login_layout

@app.callback(
    [Output("login-message", "children"), 
     Output("url", "pathname")],
    Input("login-button", "n_clicks"),
    [State("username", "value"),
     State("password", "value")],
    prevent_initial_call=True
)
def authenticate_user(n_clicks, username, password):
    """Authenticate user and return message."""
    if not all([username, password]):
        return dbc.Alert("Por favor, preencha todos os campos.", color="danger")
    
    try:
        response = requests.post(f"{FASTAPI_URL}/login", json={"username": username, "password": password})
        if response.status_code == 200:
            return None, "/dashboard"
        else:
            return dbc.Alert("Credenciais inválidas. Tente novamente.", color="danger"), None
    except requests.exceptions.ConnectionError as e:
        return dbc.Alert("Erro ao conectar ao servidor. Tente novamente mais tarde.", color="danger"), None
    
if __name__ == "__main__":
    app.run(debug=True, port=8050)