class OdooConfig:
    def __init__(self, name: str, db_password: str):
        self.name = name
        self.db_password = db_password

    def to_dict(self) -> dict:
        return {
            'name': self.name,
            'db_password': self.db_password
        }

    @classmethod
    def from_dict(cls, db_dict: dict) -> 'OdooConfig':
        return cls(
            name=db_dict['name'],
            db_password=db_dict['db_password']
        )