from pathlib import Path
from uuid import uuid4
import logging
import re
import os

import pandas as pd
from flask import Flask, render_template, request
from werkzeug.utils import secure_filename

from traditional_knowledge import analyze_document
from ml_model import MedicinalPlantML

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024
app.config["SECRET_KEY"] = "change-this-development-key-before-deployment"
logging.basicConfig(level=logging.INFO)

BASE_DIR = Path(__file__).resolve().parent

DATA_DIR = BASE_DIR / "dataset"

# Use writable temporary storage on Vercel
if os.environ.get("VERCEL"):
    UPLOAD_DIR = Path("/tmp/herb_ai_uploads")
else:
    UPLOAD_DIR = BASE_DIR / "uploads"

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
ALLOWED_EXTENSIONS = {"pdf", "txt"}

def load_csv(filename):
    """Load a CSV relative to this project, never relative to the shell's cwd."""
    path = DATA_DIR / filename
    if not path.is_file():
        app.logger.warning("Dataset not found: %s", path)
        return pd.DataFrame()
    try:
        df = pd.read_csv(path, encoding="utf-8-sig", dtype=object)
        df.columns = [str(c).strip().lower() for c in df.columns]
        df = df.fillna("")
        app.logger.info("Loaded %s (%s rows)", path.name, len(df))
        return df
    except Exception:
        app.logger.exception("Could not read dataset: %s", path)
        return pd.DataFrame()

plants_df = load_csv("medicinal_plants.csv")
compounds_df = load_csv("plant_compounds.csv")
research_df = load_csv("research_papers.csv")
plant_ml = MedicinalPlantML(plants_df, n_clusters=5)

print("\\n========== HERB-AI STATUS ==========")
print("Project directory:", BASE_DIR)
print("Plant CSV:", DATA_DIR / "medicinal_plants.csv")
print("Plant records:", len(plants_df))
print("ML model ready:", plant_ml.ready)
print("ML model error:", plant_ml.error)
print("===================================\\n")

def records(df):
    return [] if df is None or df.empty else df.to_dict(orient="records")

def search_dataframe(df, columns, query):
    if df is None or df.empty:
        return pd.DataFrame() if df is None else df.copy()
    query = str(query or "").strip()
    if not query:
        return df.copy()
    available = [c for c in columns if c in df.columns]
    if not available:
        return df.iloc[0:0].copy()
    mask = pd.Series(False, index=df.index)
    for column in available:
        mask |= df[column].astype(str).str.contains(query, case=False, na=False, regex=False)
    return df.loc[mask].copy()

@app.context_processor
def inject_globals():
    return {"current_year": 2026}

@app.route("/")
def home():
    return render_template(
        "index.html", page="Home", plant_count=len(plants_df),
        featured_plants=records(plants_df.head(4))
    )

@app.route("/plant-explorer")
def plant_explorer():
    query = request.args.get("q", "").strip()
    columns = [
        "common_name", "scientific_name", "hindi_name", "sanskrit_name",
        "botanical_family", "traditional_uses"
    ]
    filtered = search_dataframe(plants_df, columns, query)
    return render_template(
        "plant_explorer.html", page="Plant Explorer",
        plants=records(filtered), query=query
    )

@app.route("/plant-intelligence", methods=["GET", "POST"])
def plant_intelligence():
    selected_plant = request.values.get("plant", "").strip()
    result = plant_ml.analyze_plant(selected_plant, limit=5) if selected_plant and plant_ml.ready else None
    return render_template(
        "plant_intelligence.html", page="Plant Intelligence",
        plant_names=plant_ml.get_plant_names(), selected_plant=selected_plant,
        result=result, clusters=plant_ml.get_cluster_summary(),
        model_ready=plant_ml.ready
    )

@app.route("/traditional-knowledge", methods=["GET", "POST"])
def traditional_knowledge():
    result, error = None, None
    if request.method == "POST":
        uploaded = request.files.get("document")
        if not uploaded or not uploaded.filename:
            error = "Please choose a PDF or TXT document."
        else:
            filename = secure_filename(uploaded.filename)
            extension = Path(filename).suffix.lower().lstrip(".")
            if extension not in ALLOWED_EXTENSIONS:
                error = "Only PDF and TXT files are supported."
            else:
                temp_path = UPLOAD_DIR / f"{uuid4().hex}_{filename}"
                try:
                    uploaded.save(temp_path)
                    result = analyze_document(temp_path, plants_df)
                    if not result.get("total_characters"):
                        error = "No readable text was found. Scanned PDFs may require OCR."
                        result = None
                except Exception:
                    app.logger.exception("Document analysis failed")
                    error = "Could not analyze this document. Check that the PDF is text-based or try a TXT file."
                finally:
                    try:
                        temp_path.unlink(missing_ok=True)
                    except OSError:
                        app.logger.warning("Could not remove temporary upload: %s", temp_path)
    return render_template(
        "traditional_knowledge.html", page="Traditional Knowledge AI",
        result=result, error=error
    )

@app.route("/research")
def research():
    query = request.args.get("q", "").strip()
    columns = [
        "plant_common_name", "scientific_name", "publication_title",
        "authors", "study_summary", "evidence_type", "record_status"
    ]
    filtered = search_dataframe(research_df, columns, query)
    return render_template(
        "research.html", page="Research", query=query,
        research_records=records(filtered)
    )

@app.route("/analytics")
def analytics():
    coverage_labels, coverage_values = [], []
    if not plants_df.empty and "coverage_group" in plants_df.columns:
        counts = plants_df["coverage_group"].astype(str).str.strip()
        counts = counts[counts.ne("") & counts.str.lower().ne("nan")].value_counts()
        coverage_labels = counts.index.tolist()
        coverage_values = [int(v) for v in counts.values]

    compound_labels, compound_values = [], []
    if not compounds_df.empty and "plant_common_name" in compounds_df.columns:
        counts = compounds_df["plant_common_name"].astype(str).str.strip()
        counts = counts[counts.ne("") & counts.str.lower().ne("nan")].value_counts().head(15)
        compound_labels = counts.index.tolist()
        compound_values = [int(v) for v in counts.values]

    return render_template(
        "analytics.html", page="Analytics",
        plant_count=len(plants_df), compound_count=len(compounds_df),
        research_count=len(research_df), coverage_labels=coverage_labels,
        coverage_values=coverage_values, compound_labels=compound_labels,
        compound_values=compound_values
    )

@app.errorhandler(413)
def file_too_large(error):
    return render_template("error.html", page="Error", error_code=413,
                           error_message="The uploaded file exceeds the 10 MB limit."), 413

@app.errorhandler(404)
def page_not_found(error):
    return render_template("error.html", page="Error", error_code=404,
                           error_message="The page you requested could not be found."), 404

@app.errorhandler(500)
def internal_server_error(error):
    return render_template("error.html", page="Error", error_code=500,
                           error_message="An unexpected server error occurred. Please check the terminal for details."), 500

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
