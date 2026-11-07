# Herb-AI

Flask application for medicinal-plant exploration, TF-IDF/K-Means plant text analysis, rule-based extraction from ethnobotanical documents, research records, and dataset analytics.

## Project structure

```text
Herb-AI/
├── app.py
├── ml_model.py
├── traditional_knowledge.py
├── check_dataset.py
├── requirements.txt
├── dataset/
│   ├── medicinal_plants.csv
│   ├── plant_compounds.csv
│   └── research_papers.csv
├── templates/
└── static/
    ├── style.css
    └── script.js
```

## Run on Windows

Open a terminal in the `Herb-AI` folder:

```powershell
py -m venv venv
venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5000

## Dataset location and filenames

The app reads CSV files relative to `app.py`, not relative to the terminal's current directory. Keep these exact paths and names:

- `dataset/medicinal_plants.csv`
- `dataset/plant_compounds.csv`
- `dataset/research_papers.csv`

If you replace a dataset, keep the filename and its column headers. The plant dataset needs at least `common_name`; the ML feature columns are used when present. Research and analytics pages show empty states/counts if their optional CSV files are missing.

To inspect plant dataset completeness:

```powershell
python check_dataset.py
```

## Notes

- `venv` is intentionally not included. It is recreated on your computer using the commands above.
- PDF extraction supports text-based PDFs. Scanned PDFs need OCR, which is not included.
- Traditional Knowledge AI currently uses dictionary/phrase-based extraction. It produces candidate text matches that require human verification; it is not a trained medical NLP model and does not validate medical claims.
- TF-IDF similarity and K-Means clusters represent textual relationships only, not medicinal effectiveness or clinical evidence.
- The research CSV can contain PubMed search records. A search link is not itself a verified individual paper.
- Before public deployment, set a secure environment-based Flask secret key and turn off debug mode.
