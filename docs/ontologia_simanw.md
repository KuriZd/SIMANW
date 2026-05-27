# Ontologia SIMANW

## Prefijos

- `simanw`: `http://simanw.org/ontology/`
- `data`: `http://simanw.org/data/`
- `dc`: `http://purl.org/dc/elements/1.1/`
- `foaf`: `http://xmlns.com/foaf/0.1/`
- `schema`: `https://schema.org/`
- `wd`: `http://www.wikidata.org/entity/`
- `dbpedia`: `http://dbpedia.org/resource/`
- `skos`: `http://www.w3.org/2004/02/skos/core#`
- `owl`: `http://www.w3.org/2002/07/owl#`
- `rdfs`: `http://www.w3.org/2000/01/rdf-schema#`
- `xsd`: `http://www.w3.org/2001/XMLSchema#`

## Clases

- `simanw:Noticia`: Documento periodistico monitoreado por el sistema.
- `simanw:Autor`: Persona o entidad que firma una noticia.
- `simanw:Categoria`: Tema asignado por clasificacion o por la fuente original.
- `simanw:Fuente`: Medio o sitio desde donde se obtuvo la noticia.

## Propiedades

- `simanw:tieneAutor`: Relacion entre noticia y autor.
- `simanw:tieneCategoria`: Relacion entre noticia y categoria tematica.
- `simanw:provieneDe`: Relacion entre noticia y fuente.
- `simanw:sentimientoScore`: Valor numerico del sentimiento calculado (xsd:float).
- `simanw:sentimientoEtiqueta`: Etiqueta textual del sentimiento (positivo, negativo, neutro).
- `simanw:urlOriginal`: URL original de la noticia rastreada (xsd:anyURI).

## Ejemplo de triples

```turtle
@prefix data: <http://simanw.org/data/> .
@prefix dc: <http://purl.org/dc/elements/1.1/> .
@prefix dcat: <http://www.w3.org/ns/dcat#> .
@prefix foaf: <http://xmlns.com/foaf/0.1/> .
@prefix gob: <http://datos.gob.mx/> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix schema: <https://schema.org/> .
@prefix simanw: <http://simanw.org/ontology/> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
<http://datos.gob.mx/dataset/emisiones_co2_por_sector_2025> a dcat:Dataset ;
    gob:tema "ciencia" ;
    gob:tieneRegistro <http://datos.gob.mx/registro/emisiones_co2_por_sector_2025_0>,
        <http://datos.gob.mx/registro/emisiones_co2_por_sector_2025_1>,
        <http://datos.gob.mx/registro/emisiones_co2_por_sector_2025_2> ;
    dc:publisher "SEMARNAT" ;
    dc:title "Emisiones CO2 por Sector 2025"@es .
<http://datos.gob.mx/dataset/indicadores_economicos_mayo_2026> a dcat:Dataset ;
    gob:tema "economia" ;
    gob:tieneRegistro <http://datos.gob.mx/registro/indicadores_economicos_mayo_2026_0>,
```

## Consultas SPARQL

### Noticias con metadatos

```sparql
PREFIX simanw: <http://simanw.org/ontology/>
PREFIX dc: <http://purl.org/dc/elements/1.1/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?titulo ?autor ?categoria ?fecha
WHERE {
    ?noticia a simanw:Noticia ;
             dc:title ?titulo ;
             dc:date ?fecha ;
             simanw:tieneAutor ?autorURI ;
             simanw:tieneCategoria ?catURI .
    ?autorURI foaf:name ?autor .
    ?catURI rdfs:label ?categoria .
}
ORDER BY DESC(?fecha)
```

### Conteo por categoria

```sparql
PREFIX simanw: <http://simanw.org/ontology/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?categoria (COUNT(?noticia) as ?total)
WHERE {
    ?noticia a simanw:Noticia ;
             simanw:tieneCategoria ?catURI .
    ?catURI rdfs:label ?categoria .
}
GROUP BY ?categoria
ORDER BY DESC(?total)
```

### Sentimiento por categoria

```sparql
PREFIX simanw: <http://simanw.org/ontology/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?categoria (AVG(?score) AS ?sentimiento_promedio) (COUNT(?noticia) AS ?total)
WHERE {
    ?noticia a simanw:Noticia ;
             simanw:tieneCategoria ?cat ;
             simanw:sentimientoScore ?score .
    ?cat rdfs:label ?categoria .
}
GROUP BY ?categoria
ORDER BY ?categoria
```

## Validacion

El proyecto incluye validacion estructural equivalente en `KnowledgeGraphSIMANW.validar_formas()` y validacion SHACL formal con `pyshacl` mediante `KnowledgeGraphSIMANW.validar_con_shacl()` usando `shapes/simanw_shapes.ttl`.