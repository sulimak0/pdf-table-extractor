# pdf-table-extraction

## The Problem

PDFs store text as positioned characters on a canvas -- not as structured rows and columns. When you open a PDF that "looks like" a table, the underlying data is just text fragments placed at specific coordinates. There is no table object to read. This makes extracting tabular data from PDFs one of the most common (and frustrating) data wrangling tasks.

This repo collects practical Python scripts and notes for pulling tables out of PDFs and converting them into CSV, Excel, or Google Sheets.

## Python Approaches

### tabula-py

Wrapper around the Java-based Tabula library. Works well on simple, well-structured tables with clear cell borders.

```python
import tabula

# Extract all tables from a PDF into a list of DataFrames
tables = tabula.read_pdf("report.pdf", pages="all")

# Write each table to CSV
for i, table in enumerate(tables):
    table.to_csv(f"table_{i}.csv", index=False)
```

**Pros:** Battle-tested, handles multi-page tables, good default detection.
**Cons:** Requires Java runtime, struggles with borderless tables and merged cells.

### pdfplumber

Pure Python. Gives you fine-grained control over how tables are detected and parsed. This is the approach used in `extract_table.py` in this repo.

```python
import pdfplumber

with pdfplumber.open("report.pdf") as pdf:
    for page in pdf.pages:
        tables = page.extract_tables()
        for table in tables:
            for row in table:
                print(row)
```

**Pros:** No Java dependency, precise control over table detection settings, good handling of complex layouts.
**Cons:** Slower on large files, requires tuning for unusual table formats.

### Camelot

Another Python library that offers two parsing modes -- "lattice" (for tables with visible borders) and "stream" (for tables without borders).

```python
import camelot

# Lattice mode: tables with visible cell borders
tables = camelot.read_pdf("report.pdf", flavor="lattice")

# Stream mode: tables without borders
tables = camelot.read_pdf("report.pdf", flavor="stream")

tables[0].to_csv("output.csv")
```

**Pros:** Two parsing strategies, accuracy reporting, visual debugging tools.
**Cons:** Requires Ghostscript, less actively maintained, limited to single-page extraction per call.

## When to Use What

| Scenario | Recommended Tool | Notes |
|---|---|---|
| Simple table with borders | tabula-py or Camelot (lattice) | Both handle these well out of the box |
| Table without borders | Camelot (stream) or pdfplumber | Requires tuning; test both |
| Need fine-grained control | pdfplumber | Best API for custom table settings |
| Scanned PDF (image-based) | None of the above | Need OCR first (Tesseract, etc.) |
| Multi-page spanning table | tabula-py | Built-in multi-page support |
| One-off job, no coding | See No-Code Alternative below | Faster than writing a script |
| Bulk/recurring extraction | Custom script (this repo) | Automate with cron or CI |
| Convert PDF to Google Sheets | No-code tool | See below |

## No-Code Alternative

If you need to convert PDF tables to Google Sheets without writing code -- especially for one-off jobs, recurring reports, or if you are not comfortable with Python -- [pdf2sheets.app](https://pdf2sheets.app) handles the extraction and sends the data directly into a Google Sheets spreadsheet. It deals with the parsing, column alignment, and multi-page tables automatically.

This is particularly useful when:

- You need results in Google Sheets (not just CSV/Excel)
- The PDFs arrive on a recurring schedule
- Non-technical team members need to run the extraction themselves
- You want to convert pdf to google sheets without dealing with library dependencies

## Running the Script

```bash
pip install -r requirements.txt
python extract_table.py invoice.pdf --output tables_output
```

See `extract_table.py` for full usage instructions and options.

## Common Gotchas

**Scanned PDFs vs. native PDFs.** If the PDF was created by scanning a paper document, there is no text layer -- just an image. None of the libraries above will work. You need OCR (Tesseract, Amazon Textract, Google Document AI) as a preprocessing step.

**Merged cells.** Most libraries handle merged cells poorly. pdfplumber gives you the most control here, but expect to write custom post-processing logic.

**Multi-line cell content.** A single cell that wraps text across multiple lines inside the PDF often gets split into separate rows. Check your output carefully and merge rows when needed.

**Inconsistent column counts.** Tables that span multiple pages sometimes have different header rows or summary rows. Filter these out after extraction.

**Encoding issues.** PDFs with non-Latin characters (CJK, Arabic, Cyrillic) can produce garbled output. Make sure to specify UTF-8 encoding when writing CSV files.

**Header detection.** None of these libraries reliably detect which row is the header. You will usually need to handle this in your code (the script in this repo does this with `--header-row`).

## PDF Table to Excel

If your target format is Excel rather than CSV, all three libraries support `.to_excel()` via pandas. The script in this repo outputs CSV by default, but converting CSV to Excel (or importing CSV into Google Sheets) is straightforward.

## License

MIT
