#!/usr/bin/env python3

from datetime import datetime
from json import load
from os.path import splitext
from pprint import pformat
from sys import argv, stderr

from matplotlib.lines import Line2D
from matplotlib.patches import Circle, Rectangle
from matplotlib.pyplot import close, savefig, subplots, tight_layout
from numpy import arange, array, concatenate, cos, radians, sin
from pandas import DataFrame

RINK = {
    "goal": {
        "x": 87.0,
        "y": -3.0,
        "width": 2.0,
        "height": 6.0,
    },
    "faceoff": {
        "x": 69.0,
        "y": 22.0,
        "radius": 15.0,
    },
    "blue_line": {
        "x": 29.0,
    },
    "red_line": {
        "x": 0.0,
        "y": 0.0,
    },
    "goal_line": {
        "y": 43.0,
    },
    "boards": {
        "x": {
            "lower": 0.0,
            "upper": 100.0,
        },
        "y": {
            "upper": 45.0,
            "pad": -0.75,
        },
    },
    "pad": {
        "x": 12.0,
        "y": 5.0,
    },
}


def get_data(filename):
    with open(filename, "r") as file:
        blob = load(file)
    time = datetime.strptime(
        blob["gameData"]["datetime"]["dateTime"],
        "%Y-%m-%dT%H:%M:%SZ",
    )
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
        if "x" not in coordinates.keys():
            print(pformat(coordinates), file=stderr)
            continue
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
    shots.loc[shots.home & odd_periods, "x"] = \
        -shots.loc[shots.home & odd_periods, "x"]
    shots.loc[shots.home & ~odd_periods, "y"] = \
        -shots.loc[shots.home & ~odd_periods, "y"]
    shots.loc[~shots.home & ~odd_periods, "x"] = \
        -shots.loc[~shots.home & ~odd_periods, "x"]
    shots.loc[~shots.home & odd_periods, "y"] = \
        -shots.loc[~shots.home & odd_periods, "y"]
    if shots.x.mean() < 0:
        shots.x = -shots.x
        shots.y = -shots.y
    return {
        "time": time,
        "teams": teams,
        "players": players,
        "shots": shots,
    }


def get_curve(radius, degree):
    theta = radians(degree)
    return {
        "x": radius * sin(theta),
        "y": radius * cos(theta),
    }


def get_unit_boards():
    weight = 4.5
    lower = get_curve(1.0, arange(90.0, 180.0, 1.0))
    upper = get_curve(1.0, arange(0.0, 90.0, 1.0))
    return {
        "x": concatenate([
            array([0.0]),
            upper["x"] + weight - 1.0,
            array([weight]),
            lower["x"] + weight - 1.0,
            array([0.0]),
        ], axis=None) / weight,
        "y": concatenate([
            array([weight]),
            upper["y"] + weight - 1.0,
            array([(weight / 2.0)]),
            lower["y"] + 1.0,
            array([0.0]),
        ], axis=None) / weight,
    }


def set_rink(ax):
    boards = get_unit_boards()
    kwargs = {"alpha": 0.2, "zorder": 2}
    ax.plot(
        (boards["y"] * RINK["boards"]["y"]["upper"] * 2) -
        RINK["boards"]["y"]["upper"],
        boards["x"] * RINK["boards"]["x"]["upper"],
        lw=3.5,
        c="k",
        **kwargs,
    )
    ax.add_patch(Rectangle(
        (RINK["goal"]["y"], RINK["goal"]["x"]),
        RINK["goal"]["height"],
        RINK["goal"]["width"],
        facecolor="k",
        **kwargs,
    ))
    for y in [-RINK["faceoff"]["y"], RINK["faceoff"]["y"]]:
        ax.add_patch(Circle(
            (y, RINK["faceoff"]["x"]),
            RINK["faceoff"]["radius"],
            lw=2,
            fill=None,
            **kwargs,
        ))
    ax.add_line(Line2D(
        [RINK["goal_line"]["y"] * -1, RINK["goal_line"]["y"]],
        [RINK["goal"]["x"], RINK["goal"]["x"]],
        c="k",
        lw=2,
        **kwargs,
    ))
    ax.add_line(Line2D(
        [
            -RINK["boards"]["y"]["upper"] - RINK["boards"]["y"]["pad"],
            RINK["boards"]["y"]["upper"] + RINK["boards"]["y"]["pad"],
        ],
        [RINK["red_line"]["x"], RINK["red_line"]["x"]],
        c="r",
        lw=7,
        **kwargs,
    ))
    ax.add_line(Line2D(
        [
            -RINK["boards"]["y"]["upper"] - RINK["boards"]["y"]["pad"],
            RINK["boards"]["y"]["upper"] + RINK["boards"]["y"]["pad"],
        ],
        [RINK["blue_line"]["x"], RINK["blue_line"]["x"]],
        c="b",
        lw=7,
        **kwargs,
    ))
    ax.add_line(Line2D(
        [RINK["red_line"]["y"], RINK["red_line"]["y"]],
        [RINK["boards"]["x"]["lower"], RINK["boards"]["x"]["upper"]],
        c="k",
        lw=1.5,
        ls="--",
        **kwargs,
    ))
    ax.set_xlim([
        -RINK["boards"]["y"]["upper"] - RINK["pad"]["x"],
        RINK["boards"]["y"]["upper"] + RINK["pad"]["x"],
    ])
    ax.set_ylim([
        RINK["boards"]["x"]["lower"] - RINK["pad"]["y"],
        RINK["boards"]["x"]["upper"] + RINK["pad"]["y"],
    ])
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])
    for edge in ["top", "right", "left", "bottom"]:
        ax.spines[edge].set_visible(False)


def do_plot(data, filename):
    (fig, axs) = subplots(3, 2, sharex=True, sharey=True, figsize=(6, 9.75))
    kwargs = {"family": "monospace", "alpha": 0.775}
    for (i, (team_id, team)) in enumerate(data["teams"].items()):
        axs[0, i].set_title(team["name"], fontsize="x-large", **kwargs)
        for j in range(3):
            set_rink(axs[j, i])
            team_shots = data["shots"].loc[
                (data["shots"].team_id == team_id) &
                (data["shots"].period == j + 1) &
                (RINK["boards"]["x"]["lower"] < data["shots"].x) &
                (data["shots"].x < RINK["boards"]["x"]["upper"]) &
                (-RINK["boards"]["y"]["upper"] < data["shots"].y) &
                (data["shots"].y < RINK["boards"]["y"]["upper"]),
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
            for (_, row) in team_shots.iterrows():
                axs[j, i].text(
                    row.y,
                    row.x,
                    data["players"][row.player_id]["last_name"],
                    size="xx-small",
                    ha="center",
                    va="center",
                    zorder=2,
                    **kwargs,
                )
    for j in range(3):
        axs[j, 0].set_ylabel(j + 1, rotation=0, ha="right")
    fig.suptitle(
        data["time"].strftime("%Y-%m-%dT%H:%M:%SZ"),
        fontsize="medium",
    )
    tight_layout()
    savefig(filename)
    close()
    print(filename)


def main():
    filename = argv[1]
    do_plot(get_data(filename), "{}.png".format(splitext(filename)[0]))


if __name__ == "__main__":
    main()
