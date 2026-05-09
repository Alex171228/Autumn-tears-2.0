import itertools


class FakeInsertResult:
    def __init__(self, inserted_id):
        self.inserted_id = inserted_id


class FakeDeleteResult:
    def __init__(self, deleted_count):
        self.deleted_count = deleted_count


class FakeCursor(list):
    def sort(self, field, direction):
        reverse = direction == -1
        return FakeCursor(sorted(self, key=lambda item: item.get(field), reverse=reverse))


class FakeCollection:
    _ids = itertools.count(1)

    def __init__(self, initial=None):
        self.items = list(initial or [])

    @staticmethod
    def _normalize(value):
        return str(value) if hasattr(value, "binary") else value

    def _matches(self, item, query):
        return all(self._normalize(item.get(key)) == self._normalize(value) for key, value in query.items())

    def create_index(self, *args, **kwargs):
        return None

    def find_one(self, query):
        for item in self.items:
            if self._matches(item, query):
                return item
        return None

    def find(self, query=None):
        query = query or {}
        return FakeCursor([item for item in self.items if self._matches(item, query)])

    def insert_one(self, document):
        document = dict(document)
        document.setdefault("_id", str(next(self._ids)))
        self.items.append(document)
        return FakeInsertResult(document["_id"])

    def update_one(self, query, update):
        item = self.find_one(query)
        if item and "$set" in update:
            item.update(update["$set"])

    def delete_one(self, query):
        before = len(self.items)
        self.items = [item for item in self.items if not self._matches(item, query)]
        return FakeDeleteResult(before - len(self.items))

    def delete_many(self, query):
        return self.delete_one(query)

    def count_documents(self, query):
        return len([item for item in self.items if self._matches(item, query)])


class FakeDB:
    def __init__(self, users=None, saved_configs=None):
        self.users = FakeCollection(users)
        self.saved_configs = FakeCollection(saved_configs)
