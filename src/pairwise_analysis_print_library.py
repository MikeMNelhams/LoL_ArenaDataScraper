from src.league_library import Champion
from src.pairwise_analysis_library import PairwiseChampionData
from src.print_library import colour_print_string_header, print_row


def print_number_of_matches(pairwise_data: PairwiseChampionData) -> None:
    print(f"Total number of matches recorded: {pairwise_data.total_matches()}")
    print_row()
    return None


def print_best_stats(pairwise_data: PairwiseChampionData, display_number: int) -> None:
    print(colour_print_string_header("Best overall stats:"))
    best_stats = pairwise_data.best_champs(display_number)
    print(best_stats.to_string())
    return None


def print_best_champ_pairs(pairwise_data: PairwiseChampionData, display_number: int) -> None:
    print(f"\n{colour_print_string_header('Best champ pairs:')}")
    best_pairs = pairwise_data.best_pairs(display_number)
    print(best_pairs.to_string())
    return None


def print_champ_placement_stats(champ_input: Champion, pairwise_data: PairwiseChampionData) -> None:
    placements = pairwise_data.total_placements(champ_input)
    placement_average = pairwise_data.average_placement(champ_input)
    print(colour_print_string_header(f"Placement Statistics for: \'{champ_input}\'"))
    print(placements)
    print(placement_average)
    print_row()
    return None


def print_champ_average_pairwise_best(champ_input: Champion, pairwise_data: PairwiseChampionData, display_number: int=10) -> None:
    print(colour_print_string_header(f"Best average placements by champ for \'{champ_input}\'"))
    print(pairwise_data.best_teammates_for(champ_input, display_number).to_string())
    print_row()
    return None


def print_champ_average_pairwise_all(champ_input: Champion, pairwise_data: PairwiseChampionData) -> None:
    print(colour_print_string_header(f"Average placements by champ for \'{champ_input}\'"))
    print(pairwise_data.average_placement_by_teammate(champ_input).to_string())
    return None


def print_champ_stats(champ_input: Champion, pairwise_data: PairwiseChampionData, display_number: int = 10) -> None:
    print_champ_placement_stats(champ_input, pairwise_data)
    print_champ_average_pairwise_all(champ_input, pairwise_data)
    print_champ_average_pairwise_best(champ_input, pairwise_data, display_number)
    return None


def print_pairwise_stats_best(pairwise_data: PairwiseChampionData, display_number: int) -> None:
    print_best_stats(pairwise_data, display_number)
    print_best_champ_pairs(pairwise_data, display_number)
    print_row()
    return None
