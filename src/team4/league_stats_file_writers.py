from src.champ_placement_writer import ChampPlacementWriter


class ChampPlacementWriterTeam4(ChampPlacementWriter):
    def number_of_teams(self) -> int:
        return 4

    def validate_configuration(self) -> None:
        pass
