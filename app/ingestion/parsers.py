"""Parsers for DOCX, PDF, XLSX, EML, and TXT files."""
import email
from email import policy
from pathlib import Path
from typing import Any, Dict, List, Tuple
import docx
import openpyxl
import pypdf


class DocxParser:
    @staticmethod
    def parse(file_path: Path) -> List[Dict[str, Any]]:
        doc = docx.Document(file_path)
        blocks = []
        for p_idx, p in enumerate(doc.paragraphs):
            text = p.text.strip()
            if text:
                blocks.append({
                    "locator": f"para_{p_idx + 1}",
                    "style": p.style.name if p.style else "Normal",
                    "text": text,
                })
        for t_idx, table in enumerate(doc.tables):
            for r_idx, row in enumerate(table.rows):
                row_vals = [cell.text.strip() for cell in row.cells]
                if any(row_vals):
                    blocks.append({
                        "locator": f"table_{t_idx + 1}_row_{r_idx + 1}",
                        "style": "Table",
                        "text": " | ".join(row_vals),
                        "row_values": row_vals,
                    })
        return blocks


class PdfParser:
    @staticmethod
    def parse(file_path: Path) -> List[Dict[str, Any]]:
        reader = pypdf.PdfReader(file_path)
        pages = []
        for idx, page in enumerate(reader.pages):
            text = page.extract_text()
            if text:
                pages.append({
                    "locator": f"page_{idx + 1}",
                    "page_number": idx + 1,
                    "text": text.strip(),
                })
        return pages


class XlsxParser:
    @staticmethod
    def parse(file_path: Path) -> Dict[str, List[Dict[str, Any]]]:
        wb = openpyxl.load_workbook(file_path, data_only=True)
        sheets_data = {}
        for sheetname in wb.sheetnames:
            sheet = wb[sheetname]
            rows_data = []
            for r in range(1, sheet.max_row + 1):
                row_vals = [sheet.cell(r, c).value for c in range(1, sheet.max_column + 1)]
                if any(v is not None for v in row_vals):
                    rows_data.append({
                        "row_num": r,
                        "locator": f"Sheet:{sheetname}:Row:{r}",
                        "values": row_vals,
                    })
            sheets_data[sheetname] = rows_data
        return sheets_data


class EmlParser:
    @staticmethod
    def parse(file_path: Path) -> Dict[str, Any]:
        with open(file_path, "rb") as f:
            msg = email.message_from_binary_file(f, policy=policy.default)
        body = ""
        plain_part = msg.get_body(preferencelist=("plain",))
        if plain_part:
            body = plain_part.get_content().strip()
        else:
            payload = msg.get_payload()
            if isinstance(payload, str):
                body = payload.strip()
            elif isinstance(payload, list) and len(payload) > 0:
                body = str(payload[0])

        return {
            "from": msg.get("from", ""),
            "to": msg.get("to", ""),
            "date": msg.get("date", ""),
            "subject": msg.get("subject", ""),
            "message_id": msg.get("message-id", ""),
            "body": body,
            "locator": f"Message-ID:{msg.get('message-id', file_path.name)}",
        }


class TxtParser:
    @staticmethod
    def parse(file_path: Path) -> List[Dict[str, Any]]:
        lines = []
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            for l_idx, line in enumerate(f):
                t = line.strip()
                if t:
                    lines.append({
                        "locator": f"line_{l_idx + 1}",
                        "text": t,
                    })
        return lines
