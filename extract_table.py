"""
extract_table.py -- Extract tables from a PDF and save each as a CSV file.

Uses pdfplumber for table detection and extraction.

Usage:
    python extract_table.py <pdf_path> [options]

Examples:
    # Extract all tables from a PDF (outputs to current directory)
    python extract_table.py invoice.pdf

    # Specify output directory
    python extract_table.py invoice.pdf --output ./results

    # Extract tables only from pages 1-3
    python extract_table.py report.pdf --pages 1-3

    # Use first row as header
    python extract_table.py report.pdf --header-row 0

Requirements:
    pip install pdfplumber>=0.10.0
"""

import argparse
import csv
import os
import sys

import pdfplumber


def parse_page_range(page_range_str, total_pages):
    """Parse a page range string like '1-3' or '2' into a list of 0-based indices."""
    pages = []
    for part in page_range_str.split(","):
        part = part.strip()
        if "-" in part:
            start, end = part.split("-", 1)
            start = max(1, int(start))
            end = min(total_pages, int(end))
            pages.extend(range(start - 1, end))
        else:
            page_num = int(part)
            if 1 <= page_num <= total_pages:
                pages.append(page_num - 1)
    return sorted(set(pages))


def clean_cell(value):
    """Clean a single cell value.

    - Replace None with empty string
    - Strip leading/trailing whitespace
    - Collapse internal whitespace (handles multi-line cell content)
    """
    if value is None:
        return ""
    text = str(value).strip()
    # Collapse multiple whitespace characters (newlines, tabs, spaces) into a single space
    text = " ".join(text.split())
    return text


def clean_table(table):
    """Clean all cells in a table and remove completely empty rows."""
    cleaned = []
    for row in table:
        cleaned_row = [clean_cell(cell) for cell in row]
        # Skip rows where every cell is empty
        if any(cell != "" for cell in cleaned_row):
            cleaned.append(cleaned_row)
    return cleaned


def normalize_column_count(table):
    """Ensure all rows have the same number of columns.

    Pads shorter rows with empty strings to match the longest row.
    """
    if not table:
        return table
    max_cols = max(len(row) for row in table)
    return [row + [""] * (max_cols - len(row)) for row in table]


def write_csv(rows, output_path, header_row=None):
    """Write rows to a CSV file.

    Args:
        rows: List of lists (each inner list is a row).
        output_path: Path to the output CSV file.
        header_row: If set, use this 0-based row index as the CSV header.
    """
    if header_row is not None and 0 <= header_row < len(rows):
        header = rows[header_row]
        data = rows[:header_row] + rows[header_row + 1 :]
        rows_to_write = [header] + data

    else:
        rows_to_write = rows

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(rows_to_write)


def extract_tables(pdf_path, pages=None, header_row=None, output_dir="."):
    """Extract tables from a PDF and save each as a CSV.

    Args:
        pdf_path: Path to the input PDF file.
        pages: List of 0-based page indices to process, or None for all pages.
        header_row: 0-based row index to use as header, or None.
        output_dir: Directory to write CSV files into.

    Returns:
        Number of tables extracted.
    """
    if not os.path.isfile(pdf_path):
        print(f"Error: File not found: {pdf_path}", file=sys.stderr)
        sys.exit(1)

    os.makedirs(output_dir, exist_ok=True)

    base_name = os.path.splitext(os.path.basename(pdf_path))[0]
    table_count = 0

    with pdfplumber.open(pdf_path) as pdf:
        total_pages = len(pdf.pages)
        target_pages = pages if pages is not None else range(total_pages)

        print(f"Processing: {pdf_path}")
        print(f"Total pages in PDF: {total_pages}")
        print(f"Pages to scan: {len(list(target_pages))}")
        print()

        for page_idx in target_pages:
            if page_idx >= total_pages:
                continue

            page = pdf.pages[page_idx]
            tables = page.extract_tables()

            if not tables:
                continue

            for t_idx, table in enumerate(tables):
                # Clean and normalize the table
                cleaned = clean_table(table)
                if not cleaned:
                    print(f"  Page {page_idx + 1}, table {t_idx + 1}: empty after cleaning, skipped")
                    continue

                normalized = normalize_column_count(cleaned)

                # Build output filename
                table_count += 1
                filename = f"{base_name}_page{page_idx + 1}_table{t_idx + 1}.csv"
                output_path = os.path.join(output_dir, filename)

                write_csv(normalized, output_path, header_row=header_row)
                row_count = len(normalized)
                col_count = len(normalized[0]) if normalized else 0
                print(f"  Page {page_idx + 1}, table {t_idx + 1}: {row_count} rows x {col_count} cols -> {filename}")

    return table_count


def main():
    parser = argparse.ArgumentParser(
        description="Extract tables from a PDF and save each as a CSV file."
    )
    parser.add_argument("pdf", help="Path to the input PDF file")
    parser.add_argument(
        "--output", "-o", default=".", help="Output directory for CSV files (default: current directory)"
    )
    parser.add_argument(
        "--pages", "-p", default=None, help="Page range to extract, e.g. '1-3' or '1,3,5' (1-indexed, default: all)"
    )
    parser.add_argument(
        "--header-row", type=int, default=None, help="0-based row index to treat as the header (default: none)"
    )

    args = parser.parse_args()

    # Parse page range if provided
    pages = None
    if args.pages:
        with pdfplumber.open(args.pdf) as pdf:
            total = len(pdf.pages)
        pages = parse_page_range(args.pages, total)
        if not pages:
            print("Error: No valid pages in the specified range.", file=sys.stderr)
            sys.exit(1)

    count = extract_tables(
        pdf_path=args.pdf,
        pages=pages,
        header_row=args.header_row,
        output_dir=args.output,
    )

    print()
    if count == 0:
        print("No tables found in the specified pages.")
        print("Tip: If this is a scanned PDF, you need OCR preprocessing first.")
    else:
        print(f"Done. Extracted {count} table(s).")


if __name__ == "__main__":
    main()
