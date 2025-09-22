---
title: LuaPyDoc
date: 2025-01-01
---

Luapydoc è un generatore di documentazione basato su Python per codebase Lua. Analizza commenti di documentazione in stile LDoc nei file sorgente Lua e genera un sito web di documentazione HTML completo, navigabile, con evidenziazione della sintassi, funzionalità di ricerca e molto altro.

[Repository](https://github.com/giovifav/luapydoc)
[Esempio output](docs)

## Caratteristiche

- Analizza commenti di documentazione LDoc (@param, @return, @usage, ecc.)
- Supporta funzioni, variabili, tabelle e tipi
- Genera pagine HTML responsive con tema scuro
- Evidenziazione della sintassi per codice Lua usando Pygments
- Navigazione a barra laterale basata su albero per moduli, classi e funzioni
- Ricerca a testo completo con indice
- Design responsive per mobile e desktop

## Requisiti

- Python 3.x
- jinja2
- pygments

## Installazione

1. Clona questo repository.
2. Installa le dipendenze: `pip install -r requirements.txt`

## Utilizzo

1. Inserisci i tuoi file sorgente Lua in una directory (es. `lua_src`), organizzati in sottodirectory se necessario.
2. Esegui il generatore con le opzioni desiderate (vedi esempi sotto).
3. Apri il file `index.html` nella directory di output nel tuo browser per visualizzare la documentazione.

### Opzioni riga di comando

```bash
# Utilizzo di base con le directory di default
python docs_generator.py

# Specifica directory sorgente e output personalizzate
python docs_generator.py --src-dir ./my_lua_code --output-dir ./my_docs

# Utilizzo delle forme brevi
python docs_generator.py -s ./src -o ./docs

# Specifica solo la directory sorgente (output di default 'docs')
python docs_generator.py --src-dir ./lua_src
```

**Parametri disponibili:**
- `-s, --src-dir`: Directory contenente i file sorgente Lua (default: `lua_src`)
- `-o, --output-dir`: Directory dove generare la documentazione (default: `docs`)

**Aiuto completo:**
```bash
python docs_generator.py --help
```

## Struttura del progetto

- `docs_generator.py`: Script principale che analizza i file Lua e genera documentazione
- `docs_template.html`: Template Jinja2 per pagine HTML
- `docs_style.css`: Stili CSS per il sito web di documentazione
- `requirements.txt`: Dipendenze Python
- `lua_src/`: Directory per file sorgente Lua (creala)
- `docs/`: Directory di output per file HTML generati

## Come funziona

Il generatore lavora in due fasi:
1. Analizza commenti di documentazione (es. --- @param name desc)
2. Li associa a definizioni di funzioni o assegnazioni di variabili
3. Costruisce un albero gerarchico per la navigazione
4. Genera pagine HTML usando template Jinja2
5. Include codice Lua con sintassi evidenziata

## Personalizzazione

Puoi personalizzare l'aspetto modificando `docs_style.css` e il layout modificando `docs_template.html`.