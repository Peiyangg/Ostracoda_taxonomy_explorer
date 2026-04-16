# Ostracoda Taxonomy Explorer

Interactive D3.js visualization for exploring the taxonomy and nomenclatural change history of [Ostracoda](https://en.wikipedia.org/wiki/Ostracod) (seed shrimp), built on data from the [World Register of Marine Species (WoRMS)](https://www.marinespecies.org/).

## Live demo

Open `index.html` via GitHub Pages, or serve locally:

```bash
python3 -m http.server 8000
# then open http://localhost:8000
```

## Features

- **Interactive taxonomy tree** — expand/collapse nodes from Class down to Species level
- **Three visualization modes** — Tree, Radial, and Sunburst layouts
- **Change-type classification** — each non-accepted record is classified as:
  - **PHYLO** — phylogenetic reclassification (genus/family transfer, superseded combination)
  - **RANK** — rank change (e.g. subgenus raised to genus)
  - **NAMEFIX** — nomenclatural fix (synonym, misspelling, nomen oblitum, etc.)
- **Cross-tree arrows** — visualize where species were moved between genera
- **Search** — find any taxon by name and navigate to it in the tree
- **Status filters** — filter nodes by accepted/unaccepted status
- **Detail panel** — view full record info, classification, environment, and children summary

## Dataset

`data/ostracoda_all_records.json` contains 11,586 records fetched from the WoRMS REST API via recursive `AphiaChildrenByAphiaID` calls starting from Ostracoda (AphiaID: 1078).

To regenerate the data:

```bash
cd data
pip install requests
python download_all_statuses.py
```

This takes ~15-25 minutes due to API rate limiting.

## Data source

All taxonomic data is sourced from [WoRMS](https://www.marinespecies.org/):

> WoRMS Editorial Board (2026). World Register of Marine Species. Available from https://www.marinespecies.org at VLIZ. Accessed 2026-04-15.
