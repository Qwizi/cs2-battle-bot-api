from players.models import Player, Team


def create_default_teams(
    self, team1_name: str, team2_name: str, players_list: list[Player]
) -> tuple[Team, Team]:
    """
    Create two teams with the given players.

    Args:
    -----
        team1_name (str): Name of the first team.
        team2_name (str): Name of the second team.
        team1_players_list (list[Player]): List of players for the first team.
        team2_players_list (list[Player]): List of players for the second team.

    Returns:
    --------
        tuple[Team, Team]: Tuple with two teams.

    """
    team1 = Team.objects.get_or_create(name=team1_name)[0]
    team2 = Team.objects.get_or_create(name=team2_name)[0]
    team1_players_list, team2_players_list = self.__divide_players(players_list)

    team1.players.set(team1_players_list)
    team1.leader = team1_players_list[0]
    team1.save()

    team2.players.set(team2_players_list)
    team2.leader = team2_players_list[0]
    team2.save()
    return team1, team2
