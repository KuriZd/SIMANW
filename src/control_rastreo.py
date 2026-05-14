from __future__ import annotations

from collections import deque
from urllib.parse import urljoin, urlparse


class ControlRastreo:
    """Controla el alcance, límite y cola de URLs del rastreador."""

    def __init__(self, url_semilla: str, modo: str = "dominio", max_paginas: int = 50, delay: int = 2) -> None:
        self.url_semilla = url_semilla
        self.dominio = urlparse(url_semilla).netloc
        self.modo = modo
        self.max_paginas = max_paginas
        self.delay = delay
        self.visitadas: set[str] = set()
        self.en_cola: set[str] = {url_semilla}
        self.cola: deque[str] = deque([url_semilla])
        self.rechazadas: list[str] = []

    def url_permitida(self, url: str) -> bool:
        parsed = urlparse(url)

        if self.modo == "dominio":
            return parsed.netloc == self.dominio

        if self.modo == "directorio":
            base_path = urlparse(self.url_semilla).path.rstrip("/")
            return (
                parsed.netloc == self.dominio
                and (parsed.path == base_path or parsed.path.startswith(f"{base_path}/"))
            )

        if self.modo == "subdominio":
            return parsed.netloc == self.dominio or parsed.netloc.endswith(f".{self.dominio}")

        return False

    def agregar_enlaces(self, enlaces: list[str]) -> int:
        agregados = 0

        for enlace in enlaces:
            url_abs = urljoin(self.url_semilla, enlace)

            if self._puede_agregarse(url_abs):
                self.cola.append(url_abs)
                self.en_cola.add(url_abs)
                agregados += 1
            else:
                self.rechazadas.append(url_abs)

        return agregados

    def siguiente(self) -> str | None:
        if not self.cola or len(self.visitadas) >= self.max_paginas:
            return None

        url = self.cola.popleft()
        self.en_cola.discard(url)
        self.visitadas.add(url)
        return url

    def estado(self) -> dict:
        return {
            "visitadas": len(self.visitadas),
            "en_cola": len(self.cola),
            "rechazadas": len(self.rechazadas),
            "limite": self.max_paginas,
            "completado": len(self.visitadas) >= self.max_paginas or not self.cola,
        }

    def _puede_agregarse(self, url: str) -> bool:
        return (
            self.url_permitida(url)
            and url not in self.visitadas
            and url not in self.en_cola
            and len(self.visitadas) + len(self.cola) < self.max_paginas
        )
