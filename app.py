import os
import time
from flask import Flask, render_template, request
from dotenv import load_dotenv
import psycopg2

app = Flask(__name__)

load_dotenv()

DB_PARAMS = {
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT")
}

def search_docs(query_text):
    while True:
        try:
            conn = psycopg2.connect(**DB_PARAMS)
            break # Αν συνδεθεί, βγαίνει από το loop
        except psycopg2.OperationalError:
            print("Αναμονή για τη βάση δεδομένων...")
            time.sleep(2)
    cur = conn.cursor()
    
    # Προσθέτουμε το "id" στο SELECT
    sql = """
        SELECT id, title, abstract, ts_rank_cd(abstract_tsv, query) AS rank
        FROM docs, websearch_to_tsquery('english', %s) query
        WHERE abstract_tsv @@ query
        ORDER BY rank DESC
        LIMIT 10;
    """
    cur.execute(sql, (query_text,))
    results = cur.fetchall()
    cur.close()
    conn.close()
    return results

@app.route('/', methods=['GET', 'POST'])
def index():
    results = []
    search_term = ""
    if request.method == 'POST':
        search_term = request.form.get('q')
        if search_term:
            results = search_docs(search_term)
    return render_template('index.html', results=results, search_term=search_term)

@app.route('/article/<int:article_id>')
def article(article_id):
    conn = psycopg2.connect(**DB_PARAMS)
    cur = conn.cursor()
    # Φέρνουμε το συγκεκριμένο άρθρο με βάση το ID
    cur.execute("SELECT title, abstract FROM docs WHERE id = %s", (article_id,))
    article_data = cur.fetchone()
    cur.close()
    conn.close()
    
    if article_data:
        return render_template('article.html', title=article_data[0], abstract=article_data[1])
    return "Το άρθρο δεν βρέθηκε", 404

if __name__ == '__main__':
    # ΠΡΟΣΟΧΗ: Το host='0.0.0.0' είναι αυτό που επιτρέπει την επικοινωνία έξω από το container
    app.run(host='0.0.0.0', port=5000, debug=True)