import json
import ssl
import socket
from datetime import datetime
from flask import Flask, render_template_string, request, redirect

app = Flask(__name__)
DATA_FILE = 'sites.json'


def carregar_sites():
    try:
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return []


def salvar_sites(sites):
    with open(DATA_FILE, 'w') as f:
        json.dump(sites, f, indent=2)


def verificar_ssl(hostname):
    try:
        hostname = hostname.replace("https://", "").replace("http://", "").strip("/")
        context = ssl.create_default_context()
        with socket.create_connection((hostname, 443), timeout=5) as sock:
            with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                cert = ssock.getpeercert()
                expira_em = datetime.strptime(cert['notAfter'], '%b %d %H:%M:%S %Y %Z')
                dias_restantes = (expira_em - datetime.utcnow()).days
                return dias_restantes, expira_em.strftime('%d/%m/%Y')
    except Exception:
        return None, None


def status_ssl(dias):
    if dias is None:
        return "Erro", "cinza"
    elif dias < 0:
        return "Expirado", "vermelho"
    elif dias <= 30:
        return "Próximo do vencimento", "laranja"
    else:
        return "Válido", "verde"


HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Monitor SSL</title>
    <style>
        body { font-family: Arial; max-width: 700px; margin: auto; padding: 20px; }
        .verde { color: green; }
        .laranja { color: orange; }
        .vermelho { color: red; }
        .cinza { color: gray; }
        table { width: 100%%; border-collapse: collapse; margin-top: 20px; }
        th, td { border: 1px solid #ccc; padding: 8px; text-align: left; }
    </style>
</head>
<body>
    <h2>Verificador de Certificado SSL</h2>
    <form method="POST" action="/">
        <input type="text" name="url" placeholder="Digite a URL do site" style="width: 70%%;" required>
        <button type="submit">Verificar</button>
    </form>
    <table>
        <thead>
            <tr>
                <th>Site</th>
                <th>Expira em</th>
                <th>Status</th>
            </tr>
        </thead>
        <tbody>
            {% for site in sites %}
            <tr>
                <td>{{ site.url }}</td>
                <td>{{ site.data_expiracao }}</td>
                <td class="{{ site.cor }}">{{ site.status }}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</body>
</html>
"""


@app.route("/", methods=["GET", "POST"])
def index():
    sites = carregar_sites()
    if request.method == "POST":
        url = request.form["url"]
        dias, data = verificar_ssl(url)
        status, cor = status_ssl(dias)
        sites.append({
            "url": url,
            "data_expiracao": data if data else "Erro ao verificar",
            "status": status,
            "cor": cor
        })
        salvar_sites(sites)
        return redirect("/")
    return render_template_string(HTML, sites=sites)


if __name__ == "__main__":
    app.run(debug=True)
