import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from sklearn.metrics.pairwise import cosine_similarity


class MedicinalPlantML:
    def __init__(self, plants_df, n_clusters=5):
        self.df = plants_df.copy() if plants_df is not None else pd.DataFrame()
        self.df.columns = [str(column).strip().lower() for column in self.df.columns]
        self.df = self.df.fillna("").reset_index(drop=True)
        self.n_clusters = max(1, int(n_clusters))
        self.vectorizer = None
        self.tfidf_matrix = None
        self.kmeans = None
        self.ready = False
        self.error = None
        self.text_columns = [
            "common_name", "scientific_name", "botanical_family",
            "hindi_name", "sanskrit_name", "plant_parts_used",
            "traditional_uses", "known_compounds",
            "research_evidence_summary", "coverage_group"
        ]
        self.prepare_model()

    @staticmethod
    def clean_text(value):
        if value is None:
            return ""
        try:
            if pd.isna(value):
                return ""
        except (TypeError, ValueError):
            pass
        value = str(value).strip()
        return "" if value.lower() in {"nan", "none", "null", "n/a"} else value

    def get_value(self, plant, column):
        return self.clean_text(plant[column]) if column in plant.index else ""

    def prepare_model(self):
        self.ready = False
        if self.df.empty:
            self.error = "No plant records available. Check dataset/medicinal_plants.csv."
            return

        available_columns = [c for c in self.text_columns if c in self.df.columns]
        if not available_columns:
            self.error = "No supported plant description columns were found."
            return
        if "common_name" not in self.df.columns:
            self.error = "The dataset must contain a common_name column."
            return

        self.df["_ml_text"] = self.df[available_columns].apply(
            lambda row: " ".join(
                text for text in (self.clean_text(value) for value in row) if text
            ), axis=1
        )
        self.df = self.df[self.df["_ml_text"].str.strip().ne("")].reset_index(drop=True)
        if self.df.empty:
            self.error = "No usable plant descriptions were found in the dataset."
            return

        try:
            self.vectorizer = TfidfVectorizer(
                stop_words="english", ngram_range=(1, 2),
                max_features=3000, min_df=1
            )
            self.tfidf_matrix = self.vectorizer.fit_transform(self.df["_ml_text"])
            actual_clusters = min(self.n_clusters, len(self.df))
            if actual_clusters == 1:
                self.df["cluster"] = 0
            else:
                self.kmeans = KMeans(
                    n_clusters=actual_clusters, random_state=42, n_init=10
                )
                self.df["cluster"] = self.kmeans.fit_predict(self.tfidf_matrix)
            self.ready = True
            self.error = None
        except Exception as exc:
            self.error = f"{type(exc).__name__}: {exc}"
            self.ready = False

    def get_plant_names(self):
        if not self.ready or "common_name" not in self.df.columns:
            return []
        names = [self.clean_text(v) for v in self.df["common_name"]]
        return sorted({v for v in names if v}, key=str.casefold)

    def get_plant_details(self, plant):
        return {
            "name": self.get_value(plant, "common_name") or "Unknown Plant",
            "scientific_name": self.get_value(plant, "scientific_name"),
            "family": self.get_value(plant, "botanical_family"),
            "hindi_name": self.get_value(plant, "hindi_name"),
            "sanskrit_name": self.get_value(plant, "sanskrit_name"),
            "plant_parts_used": self.get_value(plant, "plant_parts_used"),
            "traditional_uses": self.get_value(plant, "traditional_uses"),
            "known_compounds": self.get_value(plant, "known_compounds"),
            "research_evidence_summary": self.get_value(plant, "research_evidence_summary"),
            "evidence_type": self.get_value(plant, "evidence_type"),
            "data_status": self.get_value(plant, "data_status")
        }

    def analyze_plant(self, plant_name, limit=5):
        if not self.ready or "common_name" not in self.df.columns:
            return None
        plant_name = self.clean_text(plant_name)
        if not plant_name:
            return None
        matches = self.df[
            self.df["common_name"].apply(self.clean_text).str.casefold()
            == plant_name.casefold()
        ]
        if matches.empty:
            return None

        selected_index = int(matches.index[0])
        scores = cosine_similarity(
            self.tfidf_matrix[selected_index], self.tfidf_matrix
        ).flatten()
        ranked_indices = np.argsort(scores)[::-1]
        similar_plants = []
        for index in ranked_indices:
            if int(index) == selected_index:
                continue
            plant = self.df.iloc[int(index)]
            item = self.get_plant_details(plant)
            item.update({
                "similarity": round(float(scores[index]) * 100, 2),
                "cluster": int(plant["cluster"]) + 1
            })
            similar_plants.append(item)
            if len(similar_plants) >= max(0, int(limit)):
                break

        selected = self.df.iloc[selected_index]
        cluster_id = int(selected["cluster"])
        return {
            "selected_plant": self.get_plant_details(selected),
            "cluster": cluster_id + 1,
            "cluster_size": int((self.df["cluster"] == cluster_id).sum()),
            "similar_plants": similar_plants,
            "total_plants": len(self.df),
            "total_clusters": int(self.df["cluster"].nunique())
        }

    def get_cluster_summary(self):
        if not self.ready:
            return []
        summaries = []
        for cluster_id in sorted(self.df["cluster"].unique()):
            group = self.df[self.df["cluster"] == cluster_id]
            names = [self.clean_text(v) for v in group["common_name"]]
            names = [v for v in names if v]
            summaries.append({
                "cluster": int(cluster_id) + 1,
                "count": len(group),
                "plants": names[:6]
            })
        return summaries

    def get_model_information(self):
        return {
            "model_ready": self.ready,
            "total_plants": len(self.df),
            "total_clusters": int(self.df["cluster"].nunique()) if self.ready else 0,
            "features_used": [c for c in self.text_columns if c in self.df.columns],
            "error": self.error
        }
