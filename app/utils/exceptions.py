class DataSourceNotFound(FileNotFoundError):
    def __init__(self, path: str) -> None:
        self.path = path
        super().__init__(f"Data source not found: {path}")


class InvalidDataset(ValueError):
    def __init__(self, source: str, detail: str) -> None:
        self.source = source
        self.detail = detail
        super().__init__(f"Invalid dataset [{source}]: {detail}")


class DuplicateRecord(ValueError):
    def __init__(self, source: str, key: str) -> None:
        self.source = source
        self.key = key
        super().__init__(f"Duplicate record in [{source}]: {key}")


class ValidationError(Exception):
    def __init__(self, source: str, record_index: int, detail: str) -> None:
        self.source = source
        self.record_index = record_index
        self.detail = detail
        super().__init__(f"Validation error in [{source}] record {record_index}: {detail}")
