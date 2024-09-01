import epd2in13b_V4 as epd
from PIL import Image, ImageDraw, ImageFont
import re, math, os
from datetime import datetime
import time

try:
    # Change working dir
    abspath = os.path.abspath(__file__)
    dname = os.path.dirname(abspath)
    os.chdir(dname)

    import rocket_data  # Now import the custom module

    rocket_data.wait_for_internet()  # Wait for working internet connection

    # Some functions used later
    def truncate(string):
        return re.sub(r"\([^)]*\)", "", string)

    def seconds_to_hms(seconds):
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        seconds = seconds % 60
        return f"{hours:02}:{minutes:02}:{seconds:02}"

    got_data = False
    while not got_data:
        launches = rocket_data.Launches()  # Get Launches
        try:
            launches.get_data()  # Request data from API
            data = launches.parse_data(0)  # Get next launching rocket data
            got_data = True
        except Exception as e:
            print(f"Failed to get launch data: {e}")
            quit()

    next_rocket_name = launches.parse_data(1).get("rocket_name", "Unknown Rocket")

    # Loading fonts
    try:
        font_12 = ImageFont.truetype("font.ttf", size=12)
        font_20 = ImageFont.truetype("font.ttf", size=20)
    except IOError:
        print("Font file not found. Using default font.")
        font_12 = ImageFont.load_default()
        font_20 = ImageFont.load_default()

    color_image = Image.new(
        mode="1", size=(250, 122), color=255
    )  # Image for drawing with color
    color = ImageDraw.Draw(color_image)

    black_image = Image.new(
        mode="1", size=(250, 122), color=255
    )  # And the one where we draw the black image
    black = ImageDraw.Draw(black_image)

    # Drawing the text on the image
    color.text((0, 0), data.get("rocket_name", ""), font=font_20, fill="black")  # Name of rocket
    black.text((0, 20), truncate(data.get("mission_name", "")), font=font_12, fill="black")  # Mission name
    black.text((0, 35), data.get("agency", ""), font=font_12, fill="black")  # Agency name
    color.text(
        (0, 48), "T-" + seconds_to_hms(data.get("countdown", 0)), font=font_20, fill="black"
    )  # Create countdown (T-H:M:S)
    black.text(
        (0, 69), f"Next: {next_rocket_name}", font=font_12, fill="black"
    )  # And here the next rocket name

    black.text((0, 84), f"Updated: {datetime.now().strftime('%H:%M:%S')}", font=font_12, fill="black")

    # Add launch status in the center of the screen
    margin = 3
    bbox = font_20.getbbox(data.get("abbrev", ""))
    abbrev_width = bbox[2] - bbox[0]  # right - left
    abbrev_height = bbox[3] - bbox[1]  # bottom - top
    abbrev_x = 250 - abbrev_width - margin
    abbrev_y = round(122 / 2) - round(abbrev_height / 2)
    abbrev_rectangle_top = abbrev_y - margin
    abbrev_rectangle_left = abbrev_x - margin
    abbrev_rectangle_bottom = abbrev_y + abbrev_height + margin
    abbrev_rectangle_right = abbrev_x + abbrev_width + margin
    color.rectangle(
        (
            abbrev_rectangle_left,
            abbrev_rectangle_top,
            abbrev_rectangle_right,
            abbrev_rectangle_bottom,
        ),
        fill="black",
    )
    color.text((abbrev_x, abbrev_y), data.get("abbrev", ""), font=font_20, fill="white")

    # Percentage Rectangle
    height = 8  # 20
    black_width = 2  # 4
    black_rectangle_top = 122 - (math.ceil(height / 2) - math.ceil(black_width / 2))
    black_rectangle_left = 0
    black_rectangle_bottom = 122 - (
        math.floor(height / 2) + math.floor(black_width / 2)
    )
    black_rectangle_right = 250
    black.rectangle(
        (
            black_rectangle_left,
            black_rectangle_top,
            black_rectangle_right,
            black_rectangle_bottom,
        ),
        fill="black",
    )  # The black, thin line

    color_rectangle_top = 122 - height
    color_rectangle_left = 0
    color_rectangle_bottom = 122
    color_rectangle_right = round(250 * data.get("launch_percent", 0))
    color.rectangle(
        (
            color_rectangle_left,
            color_rectangle_top,
            color_rectangle_right,
            color_rectangle_bottom,
        ),
        fill="black",
    )  # and the colored one

    # Rotate images - uncomment if you want the power port on the top
    #color_image = color_image.rotate(angle=180)
    #black_image = black_image.rotate(angle=180)

    # Display images
    # Initialize display (Important: Enable SPI via raspi-config!)
    display = epd.EPD()
    display.init()
    display.Clear()
    display.display(
        display.getbuffer(image=black_image), display.getbuffer(image=color_image)
    )

except Exception as e:
    print(f"An error occurred: {e}")
    quit()
