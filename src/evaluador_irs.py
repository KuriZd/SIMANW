from __future__ import annotations


class EvaluadorIRS:
    """Evalua la efectividad del motor de busqueda del SIMANW."""

    @staticmethod
    def precision(recuperados: list[int], relevantes: list[int]) -> float:
        recuperados_set = set(recuperados)
        relevantes_set = set(relevantes)
        verdaderos_positivos = len(recuperados_set & relevantes_set)
        return verdaderos_positivos / len(recuperados_set) if recuperados_set else 0.0

    @staticmethod
    def recall(recuperados: list[int], relevantes: list[int]) -> float:
        recuperados_set = set(recuperados)
        relevantes_set = set(relevantes)
        verdaderos_positivos = len(recuperados_set & relevantes_set)
        return verdaderos_positivos / len(relevantes_set) if relevantes_set else 0.0

    @staticmethod
    def f1(precision: float, recall: float) -> float:
        if precision + recall == 0:
            return 0.0
        return 2 * precision * recall / (precision + recall)

    @staticmethod
    def precision_at_k(ranking: list[int], relevantes: list[int], k: int) -> float:
        if k <= 0:
            return 0.0
        top_k = set(ranking[:k])
        relevantes_set = set(relevantes)
        return len(top_k & relevantes_set) / k

    @staticmethod
    def average_precision(ranking: list[int], relevantes: list[int]) -> float:
        relevantes_set = set(relevantes)
        if not relevantes_set:
            return 0.0

        suma = 0.0
        relevantes_encontrados = 0

        for posicion, doc_id in enumerate(ranking, start=1):
            if doc_id in relevantes_set:
                relevantes_encontrados += 1
                suma += relevantes_encontrados / posicion

        return suma / len(relevantes_set)

    def evaluar_consulta(self, recuperados_ids: list[int], relevantes_ids: list[int], total_docs: int | None = None) -> dict:
        precision = self.precision(recuperados_ids, relevantes_ids)
        recall = self.recall(recuperados_ids, relevantes_ids)
        f1 = self.f1(precision, recall)
        ap = self.average_precision(recuperados_ids, relevantes_ids)

        return {
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "average_precision": ap,
        }

    def mean_average_precision(self, evaluaciones: list[dict]) -> float:
        if not evaluaciones:
            return 0.0
        total = sum(self.average_precision(ev["recuperados"], ev["relevantes"]) for ev in evaluaciones)
        return total / len(evaluaciones)
