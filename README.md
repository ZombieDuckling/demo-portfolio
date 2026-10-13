# Josh Sack — Demo Portfolio

A small GitHub Pages portfolio of high-polish interface demos built as standalone static HTML artifacts.

## Demos

- **Claymorphic Spatial UI** — tactile, warm, sellable product-interface concept with inflated panels and soft spatial depth.
- **Neumorphic Orbital UI** — a different spatial language: cool monochrome material, inset controls, rotating orbital elements, and precision dashboard feel.

## Local preview

```bash
python3 -m http.server 8080
```

Then open `http://localhost:8080`.

## Validation

Run the no-dependency static smoke test before publishing changes:

```bash
python3 scripts/validate_static.py
```

The check parses every HTML file, verifies basic document metadata, and ensures local portfolio links resolve.
