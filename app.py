from flask import Flask, render_template, request, jsonify, send_file
import os, requests
from bs4 import BeautifulSoup

app = Flask(__name__)
BASE_URL = "https://services.ecourts.gov.in/ecourtindia_v6/"

@app.route('/')
def index():
    states = fetch_states()
    return render_template('index.html', states=states)

@app.route('/get_districts', methods=['POST'])
def get_districts():
    state_code = request.json.get('state_code')
    districts = fetch_districts(state_code)
    return jsonify(districts)

@app.route('/get_complexes', methods=['POST'])
def get_complexes():
    district_code = request.json.get('district_code')
    complexes = fetch_complexes(district_code)
    return jsonify(complexes)

@app.route('/get_courts', methods=['POST'])
def get_courts():
    complex_code = request.json.get('complex_code')
    courts = fetch_courts(complex_code)
    return jsonify(courts)

@app.route('/download', methods=['POST'])
def download():
    state = request.form['state']
    district = request.form['district']
    complex_code = request.form['complex']
    court_code = request.form['court']
    date = request.form['date']

    pdf_path = download_single_causelist(state, district, complex_code, court_code, date)
    if not pdf_path:
        return "No cause list found for this court/date.", 404

    return send_file(pdf_path, as_attachment=True)

# --- Helper Functions ---
def fetch_states():
    url = BASE_URL + "get_state.php"
    r = requests.get(url)
    soup = BeautifulSoup(r.text, 'html.parser')
    return [{"code": opt['value'], "name": opt.text.strip()} for opt in soup.find_all('option') if opt.text.strip()]

def fetch_districts(state_code):
    url = BASE_URL + f"get_district.php?state_code={state_code}"
    r = requests.get(url)
    soup = BeautifulSoup(r.text, 'html.parser')
    return [{"code": opt['value'], "name": opt.text.strip()} for opt in soup.find_all('option') if opt.text.strip()]

def fetch_complexes(district_code):
    url = BASE_URL + f"get_complex.php?district_code={district_code}"
    r = requests.get(url)
    soup = BeautifulSoup(r.text, 'html.parser')
    return [{"code": opt['value'], "name": opt.text.strip()} for opt in soup.find_all('option') if opt.text.strip()]

def fetch_courts(complex_code):
    url = BASE_URL + f"get_court.php?complex_code={complex_code}"
    r = requests.get(url)
    soup = BeautifulSoup(r.text, 'html.parser')
    return [{"code": opt['value'], "name": opt.text.strip()} for opt in soup.find_all('option') if opt.text.strip()]

def download_single_causelist(state, district, complex_code, court_code, date):
    url = f"{BASE_URL}?p=cause_list&state_code={state}&dist_code={district}&court_code={court_code}&date={date}"
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(url, headers=headers)
    if r.status_code != 200:
        return None

    soup = BeautifulSoup(r.text, "html.parser")
    pdf_link = None
    for link in soup.find_all("a", href=True):
        if "cause_list_pdf" in link["href"]:
            pdf_link = BASE_URL + link["href"]
            break

    if not pdf_link:
        return None

    filename = f"cause_list_{court_code}_{date}.pdf"
    pdf_response = requests.get(pdf_link, stream=True)
    with open(filename, "wb") as f:
        for chunk in pdf_response.iter_content(1024):
            f.write(chunk)
    return filename

if __name__ == "__main__":
    app.run(debug=True)
