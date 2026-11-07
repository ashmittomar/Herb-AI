
from pathlib import Path
import re

try:
    import pymupdf
except ImportError:
    pymupdf = None


PLANT_PARTS = [
    "leaves", "leaf", "roots", "root", "bark",
    "seeds", "seed", "flowers", "flower",
    "fruits", "fruit", "rhizome", "stem",
    "whole plant"
]

PREPARATIONS = [
    "decoction", "infusion", "powder",
    "paste", "extract", "oil", "juice", "tea"
]

USE_PATTERNS = [
    r"traditionally used for\s+([^.;\n]+)",
    r"used for\s+([^.;\n]+)",
    r"used to\s+([^.;\n]+)",
    r"used in the treatment of\s+([^.;\n]+)",
    r"used against\s+([^.;\n]+)",
    r"folk medicine(?:\s+for)?\s+([^.;\n]+)"
]


def extract_text(path):
    path = Path(path)

    if path.suffix.lower() == ".txt":
        return path.read_text(
            encoding="utf-8",
            errors="replace"
        ), 1

    if path.suffix.lower() == ".pdf":

        if pymupdf is None:
            raise RuntimeError(
                "PyMuPDF is not installed. "
                "Run: pip install PyMuPDF"
            )

        with pymupdf.open(path) as pdf:
            text = "\n".join(
                page.get_text("text")
                for page in pdf
            )

            return text, len(pdf)

    raise ValueError(
        "Unsupported document type. "
        "Upload a PDF or TXT file."
    )


def split_sentences(text):
    sentences = re.split(
        r"(?<=[.!?])\s+|\n+",
        text
    )

    return [
        sentence.strip()
        for sentence in sentences
        if sentence.strip()
    ]


def get_plant_aliases(plants_df):

    aliases = {}

    if plants_df is None or plants_df.empty:
        return aliases

    plants_df = plants_df.copy()
    plants_df.columns = [str(column).strip().lower() for column in plants_df.columns]

    for _, row in plants_df.iterrows():

        common_name = str(
            row.get("common_name", "")
        ).strip()

        if not common_name:
            continue

        columns = [
            "common_name",
            "scientific_name",
            "hindi_name",
            "sanskrit_name"
        ]

        for column in columns:

            value = str(
                row.get(column, "")
            ).strip()

            if value and value.lower() not in {
                "nan", "none"
            }:

                aliases[value.lower()] = common_name

    return aliases


def analyze_document(path, plants_df):

    text, pages = extract_text(path)

    sentences = split_sentences(text)

    aliases = get_plant_aliases(plants_df)

    found = {}
    knowledge_records = []

    for sentence in sentences:

        lower = sentence.lower()

        matched_plants = sorted({
            canonical
            for alias, canonical in aliases.items()
            if re.search(
                r"(?<!\w)" + re.escape(alias) + r"(?!\w)",
                lower
            )
        })

        for plant in matched_plants:

            found[plant] = found.get(plant, 0) + 1

            parts = [
                part.title()
                for part in PLANT_PARTS
                if re.search(
                    r"(?<!\w)" + re.escape(part) + r"(?!\w)",
                    lower
                )
            ]

            preparations = [
                prep.title()
                for prep in PREPARATIONS
                if re.search(
                    r"(?<!\w)" + re.escape(prep) + r"(?!\w)",
                    lower
                )
            ]

            uses = []

            for pattern in USE_PATTERNS:

                matches = re.finditer(
                    pattern,
                    sentence,
                    flags=re.IGNORECASE
                )

                for match in matches:

                    candidate = match.group(1).strip(
                        " ,:;"
                    )

                    if candidate:
                        uses.append(candidate)

            if parts or preparations or uses:

                knowledge_records.append({
                    "plant": plant,

                    "plant_parts": (
                        ", ".join(dict.fromkeys(parts))
                        or "Not identified"
                    ),

                    "preparations": (
                        ", ".join(dict.fromkeys(preparations))
                        or "Not identified"
                    ),

                    "traditional_use_candidates": (
                        "; ".join(dict.fromkeys(uses))
                        or "No matching use phrase found"
                    ),

                    "sentence": sentence,

                    "review_status": "Requires human verification"
                })

    plants = [
        {
            "name": name,
            "mentions": count
        }
        for name, count in sorted(found.items())
    ]

    return {
        "document_name": Path(path).name,
        "total_pages": pages,
        "total_characters": len(text),
        "plants": plants,
        "knowledge_records": knowledge_records,

        "transformer": {
            "available": False,
            "message": (
                "Rule-based extraction is active. "
                "No domain-trained NER model is configured."
            )
        }
    }
