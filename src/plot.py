#!/usr/bin/env python3

from json import load
from os.path import splitext
from sys import argv

from matplotlib import lines, patches
from matplotlib.pyplot import close, savefig, subplots, tight_layout
from numpy import arange, array, concatenate, cos, radians, sin
from pandas import DataFrame


def get_shots(filename):
    with open(filename, "r") as file:
        blob = load(file)
    teams = {}
    for venue in ["home", "away"]:
        team = blob["gameData"]["teams"][venue]
        teams[team["id"]] = {
            "venue": venue,
            "name": team["name"],
        }
    players = {}
    for key in blob["gameData"]["players"].keys():
        player = blob["gameData"]["players"][key]
        players[player["id"]] = {
            "first_name": player["firstName"],
            "last_name": player["lastName"],
            "handedness": player["shootsCatches"],
        }
    shots = []
    for event in blob["liveData"]["plays"]["allPlays"]:
        event_result = event["result"]["event"]
        if event_result not in ["Goal", "Missed Shot", "Shot"]:
            continue
        about = event["about"]
        coordinates = event["coordinates"]
        team_id = event["team"]["id"]
        result = event["result"]
        player_id = None
        for player in event["players"]:
            if event_result == "Goal":
                if player["playerType"] == "Scorer":
                    player_id = player["player"]["id"]
                    break
            else:
                if player["playerType"] == "Shooter":
                    player_id = player["player"]["id"]
                    break
        shots.append({
            "id": about["eventId"],
            "period": about["period"],
            "time": about["periodTime"],
            "x": coordinates["x"],
            "y": coordinates["y"],
            "team_id": team_id,
            "home": teams[team_id]["venue"] == "home",
            "player_id": player_id,
            "type": result["event"],
            "secondary_type": result.get("secondaryType", ""),
            "goal": event_result == "Goal",
        })
    if len(shots) == 0:
        exit(1)
    shots = DataFrame(shots)
    odd_periods = (shots.period % 2) == 1
    shots.loc[shots.home & odd_periods, "x"] *= -1
    shots.loc[shots.home & ~odd_periods, "y"] *= -1
    shots.loc[~shots.home & ~odd_periods, "x"] *= -1
    shots.loc[~shots.home & odd_periods, "y"] *= -1
    if (len(shots) != 0) and (shots.x.mean() < 0):
        shots.x *= -1
        shots.y *= -1
    return (teams, players, shots)


def get_curve(r, degree):
    theta = radians(degree)
    return (r * sin(theta), r * cos(theta))


def get_unit_boards():
    min_y = 0
    max_y = 4.5
    min_x_array = array([-1])
    max_y_array = array([max_y])
    delta_y = max_y - min_y
    (lower_x, lower_y) = get_curve(1, arange(90, 180, 1))
    (upper_x, upper_y) = get_curve(1, arange(0, 90, 1))
    x = [
        min_x_array,
        upper_x + max_y - 1,
        max_y_array,
        lower_x + max_y - 1,
        min_x_array,
    ]
    y = [
        max_y_array,
        upper_y + max_y - 1,
        array([(delta_y / 2) + min_y]),
        lower_y + min_y + 1,
        array([min_y]),
    ]
    return (
        concatenate(x, axis=None) / delta_y,
        concatenate(y, axis=None) / delta_y
    )


def set_rink(ax, zorder=2):
    x_blue_line = 29
    max_y_boards = 45
    min_x_boards = -5
    max_x_boards = 100
    x_center_line = 0
    y_center_line = 0
    radius_faceoff = 15
    x_faceoff = 69
    y_faceoff = 22
    x_goal = 87
    y_goal = -3
    goal_width = 2
    goal_height = 6
    y_goal_line = 43
    pad = 1
    y_pad_boards = max_y_boards - (pad * 0.75)
    ax.set_xlim([(max_y_boards + pad) * -1, max_y_boards + pad])
    ax.set_ylim([min_x_boards - pad, max_x_boards + pad])
    (x_boards, y_boards) = get_unit_boards()
    kwargs = {"alpha": 0.2, "zorder": zorder}
    ax.plot(
        (y_boards * max_y_boards * 2) - max_y_boards,
        x_boards * max_x_boards,
        lw=3.5,
        c="k",
        **kwargs,
    )
    ax.add_patch(patches.Rectangle(
        (y_goal, x_goal),
        goal_height,
        goal_width,
        facecolor="k",
        **kwargs,
    ))
    for y in [-y_faceoff, y_faceoff]:
        ax.add_patch(patches.Circle(
            (y, x_faceoff),
            radius_faceoff,
            lw=2,
            fill=None,
            **kwargs,
        ))
    for x in [
        lines.Line2D(
            [y_goal_line * -1, y_goal_line],
            [x_goal, x_goal],
            c="k",
            lw=2,
            **kwargs,
        ),
        lines.Line2D(
            [y_pad_boards * -1, y_pad_boards],
            [x_center_line, x_center_line],
            c="r",
            lw=7,
            **kwargs,
        ),
        lines.Line2D(
            [y_pad_boards * -1, y_pad_boards],
            [x_blue_line, x_blue_line],
            c="b",
            lw=7,
            **kwargs,
        ),
        lines.Line2D(
            [y_center_line, y_center_line],
            [min_x_boards, max_x_boards],
            c="k",
            lw=1.5,
            ls="--",
            **kwargs,
        ),
    ]:
        ax.add_line(x)


def do_plot(teams, players, shots, filename):
    (_, axs) = subplots(3, 2, figsize=(6.75, 12))
    kwargs = {"family": "monospace", "alpha": 0.775}
    for (i, (team_id, team)) in enumerate(teams.items()):
        axs[0, i].set_title(team["name"], **kwargs)
        for j in range(3):
            axs[j, i].set_xticks([])
            axs[j, i].set_yticks([])
            for edge in ["top", "right", "left", "bottom"]:
                axs[j, i].spines[edge].set_visible(False)
            axs[j, i].set_aspect("equal")
            set_rink(axs[j, i])
            team_shots = shots.loc[
                (shots.team_id == team_id) & (shots.period == j + 1),
            ]
            axs[j, i].scatter(
                team_shots.y,
                team_shots.x,
                color=team_shots.goal.map({True: "coral", False: "c"}),
                marker="o",
                s=350,
                alpha=0.275,
                zorder=0,
            )
            (min_x, max_x) = axs[j, i].get_xlim()
            (min_y, max_y) = axs[j, i].get_ylim()
            for (_, row) in team_shots.iterrows():
                y = row.x
                x = row.y
                if (min_x < x) and (x < max_x) and (min_y < y) and (y < max_y):
                    axs[j, i].text(
                        x,
                        y,
                        players[row.player_id]["last_name"],
                        size="x-small",
                        ha="center",
                        va="center",
                        zorder=2,
                        **kwargs,
                    )
    for j in range(3):
        axs[j, 0].set_ylabel(j + 1, rotation=0, ha="right")
    tight_layout()
    savefig(filename)
    close()
    print(filename)


def main():
    filename = argv[1]
    do_plot(*get_shots(filename), "{}.png".format(splitext(filename)[0]))


if __name__ == "__main__":
    main()
