---
title: Gio's static site generator
date: 2025-09-17
---

# Gio's Static Site Generator

Un generatore di siti statici moderno e intuitivo scritto in Python con interfaccia terminale basata su Textual.

## Descrizione

Questo strumento permette di creare siti web statici partendo da file Markdown. Offre un'interfaccia grafica semplice per gestire contenuti, applicare temi e generare siti pronti alla pubblicazione. Supporta gallerie di immagini, sistemi blog, navigazione automatica e molto altro.

[Download](https://github.com/giovifav/ssg)

## Caratteristiche Principali

- **Processamento Markdown**: Converte file Markdown in pagine HTML utilizzando frontmatter per metadati.
- **Temi Personalizzabili**: Template flessibili con Jinja2 per personalizzare l'aspetto del sito.
- **Gallerie Automatiche**: Crea gallerie di immagini con thumbnails e visualizzatore integrato.
- **Sistemi Blog**: Organizza contenuti in articoli con ordinamento cronologico.
- **Interfaccia Utente**: TUI moderna per gestire siti senza comandi complessi.
- **Navigazione Automatica**: Sidebar e breadcrumbs generati automaticamente.
- **Multilingua**: Supporto italiano e inglese.

## Requisiti di Sistema

- Python 3.8 o superiore
- Dipendenze elencate in `requirements.txt`

## Installazione

```bash
git clone https://github.com/giovifav/ssg.git
cd ssg

# Crea ambiente virtuale
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # macOS/Linux

# Installa dipendenze
pip install -r requirements.txt

# Avvia l'applicazione
python main.py
```

## Utilizzo

Avvia l'applicazione con `python main.py`.

### Passi Base

1. **Inizializza un nuovo sito**: Scegli una cartella e configura nome e autore.
2. **Aggiungi contenuto**: Crea file `.md` nella cartella `content/` con frontmatter per titolo, data, autore.
3. **Aggiungi immagini e assets**: Metti file statici nella cartella `assets/`.
4. **Genera il sito**: L'applicazione crea automaticamente l'output HTML nella directory configurata.

### Struttura di Base di un Sito

```
mio-sito/
├── content/
│   └── index.md
├── assets/
│   ├── theme.html
│   └── theme.css
└── config.toml
```

## Licenza

Questo progetto è open source sotto licenza MIT.

Per supporto o segnalazioni, visita il [repository GitHub](https://github.com/giovifav/ssg).
