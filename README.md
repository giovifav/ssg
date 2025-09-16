# Gio's Static Site Generator

Un generatore di siti statici moderno e potente scritto in Python con interfaccia terminale basata su Textual.

## Descrizione

Questo progetto permette di creare e gestire siti web statici utilizzando contenuto Markdown. Fornisce sia un'interfaccia a riga di comando che un'interfaccia utente grafica intuitiva per inizializzare nuovi siti, modificare contenuti e generare output HTML. Il generatore supporta temi, frontmatter, alberi di navigazione, breadcrumbs, gestione assets, gallerie di immagini e sistemi blog avanzati.

## Caratteristiche Principali

### Generazione Sito
- **Inizializzazione Sito**: Creazione rapida di progetti sito con struttura predefinita
- **Processamento Markdown**: Conversione da Markdown a HTML con supporto frontmatter (titolo, data, autore)
- **Template Engine**: Usa Jinja2 per templating flessibile con temi personalizzabili
- **Navigazione**: Generazione automatica sidebar navigazione e breadcrumbs
- **Gestione Assets**: Copia asset statici nella directory di output
- **Indice di Ricerca**: Generazione indice JSON per funzionalità di ricerca integrata

### Gallery e Media
- **Generazione Galleria**: Creazione automatica di gallerie da directory `_gallery/`
- **Thumbnails**: Generazione automatica thumbnails con supporto EXIF
- **Modal Viewer**: Visualizzatore immagini modal integrato
- **Lazy Loading**: Caricamento immagini ottimizzato in base alla visibilità

### Sistemi Blog
- **Organizzazione Blog**: Supporto cartelle `_blog/` con processamento dedicato
- **Frontmatter Avanzato**: Metadata estese per post (autore, categorie, tags)
- **Ordinamento**: Ordinamento cronologico automatico dei post
- **Template Dedicati**: Layout specifici per pagine blog

### Interfaccia Utente
- **TUI Moderna**: Interfaccia terminale ricca basata su Textual
- **Editor Integrato**: Modifica diretta di file Markdown e altri contenuti
- **Preview Live**: Anteprima generazione sito in tempo reale
- **Themes UI**: Molteplici temi (gruvbox, nord, tokyo-night, etc.)
- **Internazionalizzazione**: Supporto italiano e inglese
- **Strumenti Gestione**: Creazione gallerie, blog, pagine automaticamente

### Sicurezza e Performance
- **Pulizia Path**: Validazione percorsi file per evitare traversal
- **Gestione Memoria**: Processing efficiente per siti grandi
- **Fallback Sicuri**: Comportamenti sicuri in caso di errori
- **Ottimizzazioni**: Caching, lazy loading e ottimizzazioni varie

## Requisiti di Sistema

- Python 3.8 o superiore
- Dipendenze installate automaticamente via `requirements.txt`:
  - `textual[syntax]`: Per l'interfaccia terminale
  - `python-frontmatter`: Per parsing frontmatter Markdown
  - `markdown`: Per conversione Markdown → HTML con estensioni avanzate
  - `jinja2`: Per rendering template
  - `toml`: Per gestione file configurazione
  - `Pillow`: Per processamento immagini galleire (opzionale)

## Installazione

### Setup Automatico (Raccomandato)
```bash
# Clona o scarica il repository
git clone https://github.com/tuo-user/ssg.git
cd ssg

# Avvia il setup automatico
python run.py
```

Lo script `run.py` eseguirà:
- Creazione ambiente virtuale (se non esistente)
- Installazione/aggiornamento dipendenze Python
- Lancio applicazione

### Setup Manuale
```bash
# Crea ambiente virtuale
python -m venv .venv

# Attiva l'ambiente virtuale
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# Installa dipendenze
pip install -r requirements.txt

# Avvia l'applicazione
python main.py
```

## Utilizzo

### Avvio Applicazione

Usa `python run.py` per setup automatico o `python main.py` per avviamento manuale.

### Menu Principale

L'applicazione presenta tre opzioni principali:

1. **Inizializza Nuovo Sito**
   - Scegli directory base
   - Inserisci nome cartella sito
   - Imposta nome sito e autore
   - Creazione struttura base automatica

2. **Apri Sito Esistente**
   - Sfoglia e seleziona directory progetto esistente
   - Accesso a strumenti modifica e generazione

3. **Impostazioni**
   - Cambia tema interfaccia
   - Cambia lingua (Italiano/Inglese)

### Creazione Contenuto

I progetti sito hanno questa struttura:
```
mio-sito/
├── content/          # File Markdown qui
├── assets/           # File statici (immagini, CSS, etc.)
├── config.toml       # Configurazione sito
├── assets/theme.html # Template principale
└── assets/theme.css  # CSS sito
```

#### File Markdown Base
Crea file `.md` nella cartella `content/` usando frontmatter:

```markdown
---
title: "Il Mio Titolo Pagina"
date: "2024-01-01"
author: "Nome Autore"
---

# Intestazione Principale

Il tuo contenuto qui... Supporta **Markdown** completo con:
- Liste ordinate e non ordinate
- [Link](https://esempio.com)
- `Codice inline` e blocchi codice

```python
# Esempio blocco codice
print("Hello, World!")
```
```

#### Creazione Galleria
Crea una directory `_gallery/` dentro `content/` e aggiungi immagini:

```
content/
├── index.md
└── foto/
    ├── index.md          # Pagina galleria
    └── _gallery/         # Immagini galleria
        ├── vacanza1.jpg
        ├── vacanza2.jpg
        └── ...
```

Il generatore creerà automaticamente:
- Pagina galleria HTML
- Thumbnails ottimizzati
- Modal viewer per visualizzazione ingrandita

#### Sistem Blog
Organizza contenuti blog in cartelle `_blog/`:

```
content/
├── index.md
└── articoli/
    ├── index.md          # Pagina blog principale
    └── _blog/            # Post articoli
        ├── primo-post.md
        ├── secondo-articolo.md
        └── ...
```

I post possono includere metadata avanzate:
```markdown
---
title: "Il Mio Primo Articolo"
date: "2024-12-25"
author: "Mario Rossi"
summary: "Riassunto dell'articolo per anteprima"
tags: ["tecnologia", "python"]
draft: false
---
```

### Generazione Sito

Dalla schermata editor sito:
1. Seleziona "Genera Sito"
2. Il generatore eseguirà:
   - Parsing tutti i file Markdown in `content/`
   - Applicazione template per creare HTML
   - Costruzione navigazione e breadcrumbs
   - Copia assets statici
   - Generazione indice ricerca JSON
   - Output nella directory configurata

Il processo è completamente statico, privo di dipendenze lato server.

## Struttura Progetto

```
.
├── assets/                   # Template e risorse predefinite
│   ├── theme.html           # Template principale sito
│   ├── theme.css            # CSS principale sito
│   ├── gallery.html         # Template gallerie
│   ├── gallery.css          # CSS gallerie
│   ├── blog.html            # Template pagine blog
│   └── 404.html             # Template errore 404
├── ui/                      # Componenti interfaccia Textual
│   ├── app.py              # Applicazione principale TUI
│   ├── editor.py           # Editor file integrato
│   ├── menu.py             # Menu di navigazione
│   └── ...                 # Altri componenti UI
├── languages/               # File traduzione interfaccia
│   ├── en.json             # Traduzioni inglese
│   └── it.json             # Traduzioni italiano
├── test_site/               # Sito esempio funzionante
├── unstable/                # Versione di sviluppo con esempio galleria
├── BUGS_IMPROVEMENTS.md    # Report completo bug e migliorie
├── site_generator.py        # Motore generazione core
├── nav_builder.py           # Costruttore navigazione
├── config.py               # Gestione configurazione sito
├── config_manager.py       # Gestione configurazione UI
├── main.py                 # Entry point applicazione
└── run.py                  # Script setup automatico
```

## Configurazione

### Configurazione Sito (config.toml)

Localizzato in ogni root directory sito:

```toml
# Configurazione base
site_name = "Il Mio Sito"
author = "Nome Autore"
footer = "© 2024 Tutti i diritti riservati"

# Directory e temi
output = "output"
base_theme = "assets/theme.html"
theme_css = "assets/theme.css"

# Opzioni avanzate (futuro)
# theme_js = "assets/theme.js"
# gallery_template = "assets/gallery.html"
# blog_template = "assets/blog.html"
```

### Configurazione UI

Impostazioni salvate in `config.json` nella directory script:
- Lingua preferita dell'interfaccia
- Tema interfaccia selezionato
- Ultime directory utilizzate

## API Core

### Funzioni Principali

#### `site_generator.generate_site(site_root: Path, log: UILog = None)`
Genera sito statico dalla directory progetto.
- **Parametri:**
  - `site_root`: Path alla root del progetto sito
  - `log`: Logger opzionale per output progresso
- **Risultato:** Sito HTML completo nella directory `output/`

#### `nav_builder.build_nav_tree(content_root: Path, output_root: Path)`
Costruisce albero navigazione da struttura content.
- **Parametri:**
  - `content_root`: Directory `content/` del sito
  - `output_root`: Directory output per calcolo percorsi
- **Risultato:** Oggetto `NavNode` root con gerarchia completa

#### `config.read_config(site_root: Path)`
Legge configurazione TOML del sito.
- **Parametri:**
  - `site_root`: Root directory progetto sito
- **Risultato:** Oggetto `SiteConfig` con configurazione valida

## Esempi Avanzati

### Workflow Completo
```bash
# 1. Setup progetto
python run.py

# 2. Creazione nuovo sito
# Nel TUI: Initialize New Site → Inserisci dettagli

# 3. Aggiunta contenuti
echo '---
title: "Benvenuto"
date: "2024-12-25"
---
# Benvenuto nel Mio Sito

Questo è un esempio di pagina MD.' > mio-sito/content/index.md

# 4. Aggiunta galleria
mkdir -p mio-sito/content/foto/_gallery
cp immagini/*.jpg mio-sito/content/foto/_gallery/
echo '---
title: "Le Mie Foto"
---
# Galleria Personale

Le mie foto preferite.' > mio-sito/content/foto/index.md

# 5. Generazione sito
# Nel TUI: Apri sito → Genera Sito
```

### Template Personalizzato
Modifica `mio-sito/assets/theme.html`:

```html
<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="utf-8">
    <title>{{ page_title }} - {{ site_name }}</title>
    <link rel="stylesheet" href="{{ theme_css_url }}">
    <!-- Aggiungi meta tag personalizzati -->
    <meta name="description" content="Il mio sito personale">
</head>
<body>
    <header>
        <h1>{{ site_name }}</h1>
        <nav>{{ sidebar_html | safe }}</nav>
    </header>
    <main>
        <div class="breadcrumbs">{{ breadcrumbs | safe }}</div>
        <h1>{{ page_title }}</h1>
        <div class="content markdown-body">
            {{ content_html | safe }}
        </div>
    </main>
    <footer>{{ footer }}</footer>
    <script src="{{ common_js_url }}"></script>
</body>
</html>
```

## Risoluzione Problemi

### Problemi Comuni

#### Errore "No TOML reader available"
**Sintomo:** Errore parsing `config.toml`
**Soluzione:**
```bash
# Installa libreria TOML mancante
pip install toml

# Oppure aggiorna a Python 3.11+ per tomllib built-in
```

#### Galleria non appare
**Sintomo:** Immagini non visualizzate nella pagina galleria
**Soluzioni:**
- Verifica directory `_gallery/` con immagini `.jpg/.png/.webp`
- Controlla permessi file lettura
- Installa Pillow: `pip install Pillow`
- Verifica generazione thumbnails in `_thumbs/`

#### Template non trovato
**Sintomo:** Errore "Theme not found"
**Soluzioni:**
- Verifica esistenza file in `config.toml`
- Copia template da `assets/` del repository
- Controlla percorsi relativi corretti

### Debug Avanzato

Abilita logging dettagliato nel codice:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

Verifica generazione con output verboso:
```python
# In site_generator.py
if log:
    log.write(f"[DEBUG] Processing: {md_file}")
```

### Performance

Per siti grandi (>1000 pagine):
- Considera riduzione dimensione gallerie (<500 immagini ciascuna)
- Aumenta memoria RAM disponibile
- Usa SSD per storage temporaneo
- Monitora generazione con strumenti profiling

## Sviluppo e Contributi

### Setup Ambiente Sviluppo
```bash
# Fork e clone repository
git clone https://github.com/tuo-username/ssg.git
cd ssg

# Crea branch feature
git checkout -b feature/nome-feature

# Installa dipendenze sviluppo
pip install -r requirements.txt
pip install pytest black mypy  # Per testing e linting

# Esegui tests
pytest

# Controllo qualità codice
black .
mypy .
```

### Contributi Welcome
- Aggiunta nuove funzionalità template
- Migliorie UX interfaccia
- Ottimizzazioni performance
- Fix di sicurezza
- Documentazione aggiuntiva

### Test Cases
I test coprono attualmente:
- Generazione sito base
- Parsing frontmatter
- Costruzione navigazione
- Configurazione valida/invalida

Aggiungere test per:
- Sistema gallerie
- Sistema blog
- Gestione errori
- Sicurezza input

## Deployment e Hosting

Il progetto genera siti completamente statici, distribuibili su:

### GitHub Pages
```bash
# Configura per pubblicazione
echo "output/" >> .gitignore  # Non committare output generato

# Build automatico in GitHub Actions
# Aggiungi .github/workflows/deploy.yml
```

### Altri Provider
- **Netlify**: Drag & drop directory `output/`
- **Vercel**: Integrazione Git automatica
- **Surge**: `npx surge output/`
- **Servizi tradizionali**: Upload via FTP/S3

### CDN e Performance
- Abilita compressione GZip sui server
- Configura cache headers
- Usa CDN (Cloudflare, Fastly) per assets statici
- Valuta prerendering per ulteriori ottimizzazioni

## Licenza

Questo progetto è open source sotto licenza MIT. Vedere il file LICENSE per dettagli completi.

### Ringraziamenti
- [Textual](https://github.com/Textualize/textual) per il framework TUI
- [Jinja2](https://jinja.palletsprojects.com/) per il template engine
- [Python-Markdown](https://python-markdown.github.io/) per la conversione MD→HTML
- [Pillow](https://python-pillow.org/) per processamento immagini

---

Per ulteriore supporto o segnalazione bug, visitare il [repository GitHub](https://github.com/giovifav/ssg).
