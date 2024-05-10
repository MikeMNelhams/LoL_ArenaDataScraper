from src.champ_placement_writer import ChampPlacementWriter


class ChampPlacementWriterTeam8(ChampPlacementWriter):
    def number_of_teams(self) -> int:
        return 8

    def validate_configuration(self) -> None:
        data = self.load()
        if data.shape[1] != self.champion_names_with_placements.shape[1] + 1:
            raise ValueError
        if data.shape[1] != self.champion_names.shape[1] * 8 + 1:
            raise ValueError
        if (data.values < 0).any():
            raise ValueError("Negative values in array detected")
        if data.columns.tolist()[1:] != self.champion_names_with_placements.columns.tolist():
            raise ValueError
        if data.index.tolist() != self.champion_names.columns.tolist():
            raise ValueError
        return None
