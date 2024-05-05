class Champion:
    def __init__(self, name: str):
        name_lower = name.lower()
        self.name = name_lower
        if name_lower == "nunu":
            self.name = "nunu&willump"  # The RIOT backend is bugged, they use 2 names for Nunu.

    def __repr__(self):
        return self.name

    @property
    def data(self) -> str:
        return self.name


class Team:
    def __init__(self, *champions: Champion):
        assert len(champions) == 2, TypeError
        self.champions: list[Champion] = [*champions]

    def __repr__(self):
        return str(self.champions)

    @property
    def data(self) -> dict:
        return {"champions": [champion.data for champion in self.champions]}
