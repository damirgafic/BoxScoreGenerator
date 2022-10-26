import argparse
import json
import requests  # pip install requests
from bs4 import BeautifulSoup  # pip install beautifulsoup4


def get_shooting(made, attempted):
    return "{}-{}".format(made, attempted)


def parse_mins(obj):
    mins = obj["statistics"]["minutes"]
    # for whatever reason live games are fmtted as PT24M07.00S
    # hacky script for now
    if mins[:2] != "PT":
        return mins
    # doesnt report subsec anyways, strip
    return mins.lstrip("PT").split(".", 1)[0].replace("M", ":")


# does python have macros?
statmapper = {
    "player": lambda obj: "*" + obj["nameI"]
                          + (
                              "^( " + obj["position"] + ")" if ("position" in obj and obj["position"]) else ""
                          ) + "*",
    "min": lambda obj: parse_mins(obj),
    "fg": lambda obj: get_shooting(
        obj["statistics"]["fieldGoalsMade"],
        obj["statistics"]["fieldGoalsAttempted"],
    ),
    "3pt": lambda obj: get_shooting(
        obj["statistics"]["threePointersMade"],
        obj["statistics"]["threePointersAttempted"],
    ),
    "ft": lambda obj: get_shooting(
        obj["statistics"]["freeThrowsMade"],
        obj["statistics"]["freeThrowsAttempted"],
    ),
    "or": lambda obj: obj["statistics"]["reboundsOffensive"],
    "reb": lambda obj: obj["statistics"]["reboundsTotal"],
    "ast": lambda obj: obj["statistics"]["assists"],
    "stl": lambda obj: obj["statistics"]["steals"],
    "blk": lambda obj: obj["statistics"]["blocks"],
    "to": lambda obj: obj["statistics"]["turnovers"],
    "pf": lambda obj: obj["statistics"]["foulsPersonal"],
    "pts": lambda obj: obj["statistics"]["points"],
    "+/-": lambda obj: obj["statistics"]["plusMinusPoints"]
    if "plusMinusPoints" in obj["statistics"] else "-",
}


def playerstats(team):
    table = []
    table.append(
        "### {} {} ({}-{})".format(
            team["teamCity"], team["teamName"], team["teamWins"], team["teamLosses"]
        )
    )  # title
    table.append("")
    # header
    table.append(
        " | ".join(["**{}**".format(field.upper()) for field in statmapper])
    )
    # barrier
    table.append(("--:|") + ((":--|" * (len(statmapper) - 1))[:-1]))

    # i feel like you was hooping, how many points you had?

    # accumulate numbers to bold top values
    nums = []
    for player in team["players"]:
        # skip bench
        if (player["statistics"]["minutes"]
                and player["statistics"]["minutes"] != "PT00M00.00S"):
            if ("status" in player and player["status"] == "INACTIVE"):
                continue
                # retain int for now
            nums.append([func(player) for (field, func) in statmapper.items()])

    # 2d mat: row players, value field
    # field idx 3-5 are shooting, so no top
    for field_idx in range(5, len(statmapper)):
        # poor man's argmax
        top_player_idx = max(
            [(j, i) for i, j in enumerate(list(zip(*nums))[field_idx])]
        )[1]
        # bold that b!
        nums[top_player_idx][field_idx] = (
                "**" + str(nums[top_player_idx][field_idx]) + "**"
        )

    for player_row in nums:  # now stringify
        table.append(" | ".join([str(x) for x in player_row]))

    # calculate total
    total = []
    for (field, func) in statmapper.items():
        if field in ["min", "player"]:  # skip
            total.append("")
            continue
        total.append("**{}**".format(str(func(team))))

    total[0] = "**TOTAL**"  # override 0th idx
    table.append(" | ".join(total))

    for x in table:
        print(x)

    print("\n\n***\n\n")
    return 0


def summary(away, home):
    table = []
    fields = ["team"]  # row-wise, so "header"
    fields += ["q{}".format(n) for n in range(1, 5)]

    # extend fields for potential overtime
    otcount = len(away["periods"]) - 4
    if otcount:  # normies start at index 1
        fields += ["ot{}".format(n) for n in range(1, otcount + 1)]
    fields.append("final")

    table.append(
        " | ".join(["**{}**".format(field.upper()) for field in fields])
    )  # header
    table.append((":--|" * len(fields))[:-1])  # barrier

    for team in [away, home]:
        out = []
        out.append("**{}**".format(team["teamTricode"]))
        out += [str(p["score"]) for p in team["periods"]]
        out.append("**{}**".format(team["score"]))
        table.append(" | ".join(out))

    for x in table:
        print(x)

    print("\n\n***\n\n")
    return 0


def boxscore(url):
    print("\n\n")

    html = requests.get(url)
    soup = BeautifulSoup(html.text, "html.parser")

    # extract json embedded in html doc
    data = soup.find("script", {"id": "__NEXT_DATA__"})
    json_data = json.loads(data.contents[0])["props"]["pageProps"]

    home = json_data["game"]["homeTeam"]
    away = json_data["game"]["awayTeam"]

    print(
        "# "
        + "{} @ {}, {}-{}".format(
            away["teamName"], home["teamName"], away["score"], home["score"]
        )
    )
    print("### {}\n".format(json_data["headline"]))

    summary(away, home)

    playerstats(away)
    playerstats(home)

    creds = (
            "\n||\n"
            "|:-|\n"
            "|data source: [nba.com](" + url + ")|\n"
    )
    print(creds)

    print("\n\n")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="boxscore formatter for r/nba")
    parser.add_argument("--url", type=str, help="url to nba.com game", required=True)
    args = parser.parse_args()

    boxscore(args.url)