class DatabaseConfig:
    def __init__(self, name: str, password: str, user: str):
        self.name = name
        self.password = password
        self.user = user

    def to_dict(self) -> dict:
        return {
            'password': self.password,
            'user': self.user,
            'name': self.name
        }

    @classmethod
    def from_dict(cls, db_dict: dict) -> 'DatabaseConfig':
        return cls(
            password=db_dict['password'],
            user=db_dict['user'],
            name=db_dict['name']
        )
