from markitdown import MarkItDown


class MarkItDownWrapper:
    def convert(self, filepath: str) -> str:
        md = MarkItDown()
        return md.convert(filepath).text_content