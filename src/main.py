import pandas
import pandas as pd
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Polygon, Rectangle
from matplotlib.gridspec import GridSpec
import matplotlib.image as mpimg
from scipy.ndimage import rotate  # for rotating the image
from matplotlib.lines import Line2D
import matplotlib.colors as mcolors
import os

result_color_map = {"StrikeSwinging" : "red" ,
                   "StrikeCalled" : "orange",
                   "BallCalled" : '#ADD8E6', # light blue
                   "Single" : "#56EB31",     # light green
                   "Double" : "#03940C", # dark green
                   "Triple" : "purple",
                   "HomeRun": "gold"}

color_map = {
    "Fastball": "darkred",
    "Slider": "darkorange",
    "Curveball": "#FFEE00",  # bright yellow
    "ChangeUp": "#88FF00",  # lime green
    "Splitter": "purple",
    "Sinker": "brown",
    "Cutter": "#FF00B3"  # bright pink
}

hit_color_map = {
                   "Single" : "#56EB31",     # light green
                   "Double" : "#03940C", # dark green
                   "Triple" : "purple",
                   "HomeRun": "gold"}

pitch_color_map = {
    "Fastball": "darkred",
    "Slider": "darkorange",
    "Curveball": "#FFEE00", # bright yellow
    "ChangeUp": "#88FF00", # lime green
    "Splitter": "purple",
    "Sinker": "brown",
    "Cutter": "#FF00B3" # bright pink
}

ab_map = {
    "Strikeout": "black",
    "Walk": "blue",
    "GroundBall" : "orange",
    "LineDrive" : "green",
    "FlyBall" : "yellow",
    "PopUp" : "red",
}



def draw_baseball_field(ax: matplotlib.axes.Axes, fence_radius=250, line_color="gray", alpha=0.2):
    """
    Draws a simple gray baseball field inside a given Axes.
    Coordinates: home at (0,0), +x toward 1B, +y toward 3B.
    """

    # Outfield fence arc (quarter circle)
    theta = np.linspace(0, np.pi/2, 200)
    xf = fence_radius * np.cos(theta)
    yf = fence_radius * np.sin(theta)
    ax.fill_between(xf, 0, yf, color=line_color, alpha=alpha, zorder=0)

    # Foul lines
    ax.plot([0, fence_radius], [0, 0], color=line_color, lw=1.5, zorder=1)
    ax.plot([0, 0], [0, fence_radius], color=line_color, lw=1.5, zorder=1)

    # Infield diamond
    base = 90
    home = (0, 0)
    first = (base, 0)
    second = (base, base)
    third = (0, base)
    diamond =  Polygon([home, first, second, third],
                              closed=True,
                              facecolor=line_color,
                              alpha=alpha,
                              edgecolor=None,
                              zorder=1)
    ax.add_patch(diamond)

    # Bases
    base_sz = 8
    for (bx, by) in [first, second, third]:
        ax.add_patch(Rectangle((bx - base_sz/2, by - base_sz/2),
                                       base_sz, base_sz,
                                       facecolor="white", edgecolor=line_color,
                                       lw=1, zorder=2))

    # Pitcher’s mound (rough placement along home→2B line)
    mound_dist = 60.5
    mound = (mound_dist / np.sqrt(2), mound_dist / np.sqrt(2))
    ax.add_patch(Circle(mound, radius=9, facecolor=line_color, alpha=alpha, zorder=2))

    ax.set_xlabel("")
    ax.set_ylabel("")
    ax.set_xticks([])
    ax.set_yticks([])

def setup_plate_and_strike_zone(ax: matplotlib.axes.Axes):
    """
    Draws a plate and strike zone centered in the middle of a given Axes. The top of the
    plate corresponds to y = 0.
    """
    ax.set_xlim(-2.5, 2.5)
    ax.set_ylim(-0.5, 4)

    # Strike zone centered at x = 0, bottom at y = 1.5 ft, top at y = 3.5 ft, width of 1.66 ft (average strike zone)

    strike_zone = ax.plot(
        [-0.83, -0.83, 0.83, 0.83, -0.83],
        [1.5, 3.5, 3.5, 1.5, 1.5],
        color="grey", linewidth=2
    )

    # Home plate with the top at y = 0

    plate_width = 0.83
    plate_height = 0.43
    plate_coords = [
        (-plate_width, 0),  # left back
        (plate_width, 0),  # right back
        (plate_width, -plate_height / 2),  # right corner
        (0, -plate_height),  # front point
        (-plate_width, -plate_height / 2)  # left corner
    ]

    home_plate = Polygon(plate_coords, closed=True, facecolor="white", edgecolor="black")
    ax.add_patch(home_plate)

def setup_game_performance_table(only_aaron: pandas.DataFrame) -> pandas.DataFrame:
    """
    Calculates a game performance table based on the stats of a certain player. only_aaron is a
    pandas DataFrame of a single player's game stats (in this case Aaron Walton)
    """

    game_performance_table = pd.DataFrame([{
        "AB": 0, "H": 0, "HR": 0,
        "RBI": 0, "BB": 0, "SO": 0,
        "XB_HITS": 0
    }])

    # Runs Batted In
    game_performance_table["RBI"] = only_aaron[only_aaron["TaggedHitType"] != "Undefined"]["RunsScored"].sum()
    # Home Runs
    game_performance_table["HR"] = len(only_aaron[only_aaron["PlayResult"] == "HomeRun"])
    # Hits
    game_performance_table["H"] = only_aaron["PlayResult"].isin(["Single", "Double", "Triple", "HomeRun"]).sum()
    # Strikeouts (K and ꓘ)
    game_performance_table["SO"] = len(only_aaron[only_aaron["KorBB"] == "Strikeout"])
    # Bases on Balls
    game_performance_table["BB"] = len(only_aaron[only_aaron["PlayResult"] == "Walk"])
    # Extra Base Hits (Non-singles)
    game_performance_table["XB_HITS"] = only_aaron["PlayResult"].isin(["Double", "Triple", "HomeRun"]).sum()

    # At Bats
    AB = 0
    for index, row in only_aaron.iterrows():
        if row["KorBB"] not in ["Undefined", "Walk", "HitByPitch"]:
            AB += 1

        elif row["PlayResult"] not in ["Undefined", "StolenBase", "SacrificeFly", "SacrificeHit", "CatcherInteference"]:
            AB += 1

    game_performance_table["AB"] = AB

    return  game_performance_table

def darken(color, factor=0.8):
    """
    Darkens a given color.
    """
    r, g, b = mcolors.to_rgb(color)
    return (max(0, r * factor), max(0, g * factor), max(0, b * factor))

def landing_point(df: pandas.DataFrame):
        """
    Calculates the landing point of a baseball based on its direction and distance. Modifies
    the DataFrame in place to give new columns 'x_land' and 'y_land'
    """
        theta = np.deg2rad(df["Direction"].astype(float))
        x_land = df["Distance"].astype(float) * np.sin(theta)  # right = positive
        y_land = df["Distance"].astype(float) * np.cos(theta)  # center field = forward

        df["x_land"] = x_land
        df["y_land"] = y_land



def main():

    # Read in table from res
    table = pd.read_csv("../res/UABaseballHitterData.csv")

        # Get Aaron Walton's data and drop all columns with no values
    only_aaron = table[table["Batter"] == "Walton, Aaron"]
    only_aaron = only_aaron.dropna(axis=1, how="all")

    # Take only rows with pitch data
    pitch_location_data = only_aaron.dropna(
        subset=["TaggedPitchType", "PitchCall", "TaggedHitType", "KorBB", "PlayResult", "PlateLocSide",
                "PlateLocHeight"]).copy()

    # Setup the figure and subplots/axes
    fig = plt.figure(figsize=(12, 8))
    fig.subplots_adjust(top=0.86)

    gs = GridSpec(3, 3, figure=fig, height_ratios=[1.5, 0.40, 1.5], wspace=0.1)

    # Initialize top axes
    ax_top_left = fig.add_subplot(gs[0, 0])
    ax_top_middle = fig.add_subplot(gs[0, 1])
    ax_top_right = fig.add_subplot(gs[0, 2])

            # Initialize middle axis
    ax_mid = fig.add_subplot(gs[1, :])
    ax_mid.axis("off")

    game_performance_table = setup_game_performance_table(only_aaron)

        # Display game performance table on middle axis
    table_display = ax_mid.table(
        cellText=game_performance_table.values,
        colLabels=game_performance_table.columns,
        cellLoc="center",
        loc="center"
    )

    table_display.auto_set_font_size(False)
    table_display.set_fontsize(12)
    table_display.scale(1, 2)

    # Color and bold the game performance table
    for (row, col), cell in table_display.get_celld().items():

        color = '#AB0520' if col % 2 else '#0C234B'
        if row == 0:
            cell.get_text().set_color("white")
            cell.get_text().set_fontsize(12)
            cell.get_text().set_fontweight("bold")
            cell.set_facecolor(color)

    # Initialize bottom axes
    axes = []
    for i in range(3):
        ax = fig.add_subplot(gs[2, i])

        # Remove x/y labels and ticks
        ax.set_xlabel("")
        ax.set_ylabel("")
        ax.set_xticks([])
        ax.set_yticks([])

        setup_plate_and_strike_zone(ax)

        # Flip x_axis (POV of batter)
        ax.invert_xaxis()

        axes.append(ax)

    # Write text at the top of the figure
    lines = ["Aaron Walton", "6/7/25 vs. North Carolina"]
    colors = ["#AB0520", "#0C234B"]  # red, blue

    for i, (line, color) in enumerate(zip(lines, colors)):
        fig.text(
            0.5,  # x-position
            0.95 - i * 0.04,  # y-position (top=0.95, decrement for each line)
            line,
            fontsize=16,
            fontweight="bold",
            color=color,
            ha="center"  # center horizontally
        )


    # Background axis

    img = mpimg.imread("../res/wildcat.png")

    img_rot = rotate(img, angle=35, reshape=True)

    if img_rot.dtype.kind == "f":
        img_rot = np.clip(img_rot, 0, 1)

    ax_bg = fig.add_subplot(111)  # one big axis
    ax_bg.imshow(img_rot, alpha=0.3, aspect="auto")  # draw image
    ax_bg.axis("off")  # hide ticks/labels
    ax_bg.set_zorder(-1)

    # Top left axis

    # Add background rectangle in axes coords (0,0)-(1,1)
    rect = Rectangle((0, 0), 1, 1,
                     transform=ax_top_left.transAxes,
                     facecolor='white',
                     edgecolor='black',
                     linewidth=2,
                     zorder=0)  # put it behind everything
    ax_top_left.add_patch(rect)

    strikes_data = pitch_location_data[pitch_location_data["PitchCall"].isin(["StrikeSwinging", "StrikeCalled"])]

    strike_pitch = {
        "Fastball": 0,
        "Slider": 0,
        "Curveball": 0,
        "ChangeUp": 0,
        "Splitter": 0,
        "Sinker": 0,
        "Cutter": 0
    }

    # Count labels, colors, and calculate percentages
    labels = []
    sizes = []
    colors = []
    for key in strike_pitch.keys():
        strike_pitch[key] = len(strikes_data[strikes_data["TaggedPitchType"] == key]) / len(strikes_data)
        if strike_pitch[key] != 0:
            labels.append(key)
            sizes.append(strike_pitch[key])
            colors.append(color_map[key])


    # Draw pie
    wedges, texts, autotexts = ax_top_left.pie(
        sizes,
        labels=None,
        colors=colors,
        autopct='%1.1f%%',
        startangle=90
    )

    # Apply slightly darker edges so the stroke is visible
    for wedge, color, t in zip(wedges, colors, autotexts):
        wedge.set_edgecolor(darken(color, 0.65))
        wedge.set_linewidth(3)
        wedge.set_antialiased(True)

        t.set_fontweight('bold')
        t.set_color(darken(color, 0.65))

    # Create a custom patch for the legend
    legend_list = [matplotlib.patches.Patch(color=color_map[label], label=label) for label in labels]

    ax_top_left.legend(handles=legend_list,
                       title="Pitch Type",
                       loc="lower right",
                       fontsize="small",
                       title_fontsize="small",
                       )

    ax_top_left.set_title("Strike Pie Chart", fontweight="bold", color="#0C234B")

    # Top middle axis

    # Add background rectangle in axes coords (0,0)-(1,1)
    rect = Rectangle((0, 0), 1, 1,
                     transform=ax_top_middle.transAxes,
                     facecolor='white',
                     edgecolor='black',
                     linewidth=2,
                     zorder=0)  # put it behind wedges
    ax_top_middle.add_patch(rect)

    ball_pitch = {
        "Fastball": 0,
        "Slider": 0,
        "Curveball": 0,
        "ChangeUp": 0,
        "Splitter": 0,
        "Sinker": 0,
        "Cutter": 0
    }

    ball_data = pitch_location_data[pitch_location_data["PitchCall"] == "BallCalled"]

    # Count labels, colors, and calculate percentages
    labels = []
    sizes = []
    colors = []
    for key in ball_pitch.keys():
        ball_pitch[key] = len(ball_data[ball_data["TaggedPitchType"] == key]) / len(ball_data)
        if ball_pitch[key] != 0:
            labels.append(key)
            sizes.append(ball_pitch[key])
            colors.append(color_map[key])

    # Draw pie
    wedges, texts, autotexts = ax_top_middle.pie(
        sizes,
        labels=None,
        colors=colors,
        autopct='%1.1f%%',
        startangle=90
    )

    # Apply slightly darker edges so the stroke is visible
    for wedge, color, t in zip(wedges, colors, autotexts):
        wedge.set_edgecolor(darken(color, 0.65))
        wedge.set_linewidth(3)
        wedge.set_antialiased(True)

        t.set_fontweight('bold')
        t.set_color(darken(color, 0.65))

    # Create a custom patch for the legend
    legend_list = [matplotlib.patches.Patch(color=color_map[label], label=label) for label in labels]

    ax_top_middle.legend(handles=legend_list,
                         title="Pitch Type",
                         loc="lower right",
                         fontsize="small",
                         title_fontsize="small",
                         )

    ax_top_middle.set_title("Ball Pie Chart", fontweight="bold", color="#AB0520")

    # Top right axis
    draw_baseball_field(ax_top_right)
    spray_chart_data = only_aaron.dropna(subset=["Distance", "Direction"]).copy()

    landing_point(spray_chart_data)

    # Rotate by 45 degrees (pi / 4) to the right (clockwise)
    x_land = spray_chart_data["x_land"].copy() # temp copy to do matrix multiplication
    spray_chart_data["x_land"] = spray_chart_data["x_land"] * np.cos(np.pi / 4) + spray_chart_data["y_land"] * np.sin(
        np.pi / 4)
    spray_chart_data["y_land"] = x_land * -np.sin(np.pi / 4) + spray_chart_data["y_land"] * np.cos(np.pi / 4)

    used_labels = set()

    # Iterate through each row of hits to make a circle to display on graph
    for index, row in spray_chart_data.iterrows():
        label = row["PlayResult"]

        circle = Circle(
            (row['x_land'], row['y_land']),
            radius=5,
            color=hit_color_map[label],
            alpha=0.8,
            zorder=6
        )
        ax_top_right.add_patch(circle)
        used_labels.add(label)

    # Create a custom patch for the legend
    legend_list = [matplotlib.patches.Patch(color=hit_color_map[label], label=label) for label in used_labels]

    ax_top_right.legend(
        handles=legend_list,
        title="Spray Legend",
        loc="upper right",
        fontsize="small",
        title_fontsize="small",
    )

    ax_top_right.set_title("Spray Chart", fontweight="bold", color="#0C234B")

    # Bottom left axis
    ax = axes[0]

    for index, row in pitch_location_data.iterrows():
        if row['PitchCall'] == "InPlay":
            label = row['PlayResult']
        else:
            label = row['PitchCall']

            # Skip if label not in colormap
        if label not in result_color_map:
            continue

        circle = Circle(
            (row['PlateLocSide'], row['PlateLocHeight']),
            radius=0.121,
            color=result_color_map[label],
            alpha=0.6,
            zorder=6
        )
        ax.add_patch(circle)
        used_labels.add(label)

    # Create a custom patch for the legend
    legend_list = [matplotlib.patches.Patch(color=result_color_map[label], label=label) for label in used_labels]

    ax.legend(
        handles=legend_list,
        title="Result Legend",
        loc="lower left",
        fontsize="x-small",
        title_fontsize="x-small",
    )

    ax.set_title("Pitch Result", fontweight="bold", color="#AB0520")

    # Bottom middle axis
    ax = axes[1]

    used_labels = set()

    for index, row in pitch_location_data.iterrows():
        label = row["TaggedPitchType"]

        circle = Circle(
            (row['PlateLocSide'], row['PlateLocHeight']),
            radius=0.121,
            color=pitch_color_map[label],
            alpha=0.6,
            zorder=6
        )
        ax.add_patch(circle)
        used_labels.add(label)

    # Create a custom patch for the legend
    legend_list = [matplotlib.patches.Patch(color=pitch_color_map[label], label=label) for label in used_labels]

    ax.legend(
        handles=legend_list,
        title="Pitch Legend",
        loc='lower left',
        ncols=1,
        fontsize="x-small",
        title_fontsize="x-small",
    )

    ax.set_title("Pitch Type", fontweight="bold", color="#0C234B")

    # Bottom left axis
    ax = axes[2]

    used_labels = set()
    max_velo = 0
    best_contact = (0, 0)

    for index, row in pitch_location_data.iterrows():
        if row["KorBB"] != "Undefined":
            label = row["KorBB"]
        elif row["PitchCall"] == "InPlay":
            label = row["TaggedHitType"]
        else:
            continue

        circle = Circle(
            (row['PlateLocSide'], row['PlateLocHeight']),
            radius=0.121,
            color=ab_map[label],
            alpha=0.6,
            zorder=6
        )

        if (float(row["ExitSpeed"]) > max_velo):
            max_velo = float(row["ExitSpeed"])
            best_contact = (row['PlateLocSide'], row['PlateLocHeight'], circle)

        ax.add_patch(circle)
        used_labels.add(label)

    if (best_contact != (0, 0)):
        ax.plot(best_contact[0], best_contact[1],
                marker="*", markersize=10,
                color="gold", markeredgecolor="black",
                zorder=7,
                alpha=0.5, label="Best Contact", )

    # Create a custom patch for the legend
    legend_list = [matplotlib.patches.Patch(color=ab_map[label], label=label) for label in used_labels]

    star_handle = Line2D([0], [0],
                         marker="*", color="gold", markeredgecolor="black",
                         markersize=10, linestyle="None", label="Best Contact")
    legend_list.append(star_handle)

    ax.legend(
        handles=legend_list,
        title="Result Legend",
        loc="lower left",
        fontsize="x-small",
        title_fontsize="x-small",
    )

    ax.set_title("At Bat Result", fontweight="bold", color="#AB0520")

    plt.savefig("res/AaronWaltonHittingReport_6_7_2025.png")
    plt.show()


main()




