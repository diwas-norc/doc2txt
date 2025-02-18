from docling.document_converter import DocumentConverter


class DoclingWrapper:
    def convert(self, filepath: str) -> str:
        dc = DocumentConverter()
        return dc.convert(filepath).document.export_to_markdown()