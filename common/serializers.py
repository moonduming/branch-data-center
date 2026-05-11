class IgnoreExtraFieldsMixin:
    drop_empty_fields = set()
    empty_to_none_fields = set()

    def to_internal_value(self, data):
        if not hasattr(data, "items"):
            return super().to_internal_value(data)

        normalized_data = {}
        for key, value in data.items():
            if key not in self.fields:
                continue
            if value in ("", None):
                if key in self.drop_empty_fields:
                    continue
                if key in self.empty_to_none_fields:
                    normalized_data[key] = None
                    continue
            normalized_data[key] = value
        return super().to_internal_value(normalized_data)
