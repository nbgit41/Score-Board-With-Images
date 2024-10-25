import pygame
import sys
import threading
import random
import time
import os
import numpy as np
import pygame.surfarray

# Initialize Pygame
print("initializing pygame")
pygame.init()
print("initialized pygame initializing pymixer")
pygame.mixer.init()
print("initialized pymixer")

# Constants
DEFAULT_RESOLUTION = (1280, 720)
print(f"Resolution set to {DEFAULT_RESOLUTION}")
ASPECT_RATIO = 16 / 9
LINE_WIDTH = 5

# Variables
resolution = DEFAULT_RESOLUTION
print(f"resolution = {resolution}")
sound_effects = True
print(f"sound effects = {sound_effects}")
boys_vs_girls_mode = False
print(f"boys vs girls mode = {boys_vs_girls_mode}")
teams_mode = False
print(f"teams mode = {teams_mode}")
line_enabled = False
print(f"line = {line_enabled}")
pipe_sounds_enabled = False #you can ignore this
baseball_mode = False
print(f"baseball mode = {baseball_mode}")

# Caps for baseball mode
balls_max = 3
print(f"Balls Max = {balls_max}")
strikes_max = 2
print(f"Strikes Max = {strikes_max}")
outs_max = 2
print(f"Outs Max = {outs_max}")

# Metal pipe sound timings, just ignore this
pipe_sound_min_time = 20    # seconds
pipe_sound_max_time = 1800  # 30 minutes in seconds

# Function to read the target score from MaxScore.txt
def read_target_score():
    try:
        with open('MaxScore.txt', 'r') as f:
            target = int(f.read().strip())
            if target < 1:
                target = 1  # Ensure target score is at least 1
            print(f"target score is set to {target}")
            return target
    except Exception as e:
        print(f"Error reading MaxScore.txt: {e}")
        return 10  # Default target score if file is missing or invalid

# Load images
def load_images():
    print("loading all images")
    images = {}
    score_images = {}
    image_folder = 'images'

    # Load team images
    print("loading boys.png")
    images['boys'] = pygame.image.load(os.path.join(image_folder, 'boys.png')).convert_alpha()
    print("loaded boys.png, loading girls.png")
    images['girls'] = pygame.image.load(os.path.join(image_folder, 'girls.png')).convert_alpha()
    print("loaded girls.png, loading team1.png")
    images['team1'] = pygame.image.load(os.path.join(image_folder, 'team1.png')).convert_alpha()
    print("loaded team1.png, loading team2.png")
    images['team2'] = pygame.image.load(os.path.join(image_folder, 'team2.png')).convert_alpha()
    print("loaded team2.png, loading scores")

    # Load score images
    for i in range(100):  # Assuming scores can go from 0 to 99
        image_path = os.path.join(image_folder, f'{i}.png')
        if os.path.exists(image_path):
            score_images[i] = pygame.image.load(image_path).convert_alpha()

    return images, score_images

# Load sounds
def load_sounds():
    print("loading sounds")
    sounds = {}
    print("loading point sound")
    sounds['point'] = pygame.mixer.Sound('FlappyPoint.mp3')
    print("loaded point")
    sounds['metal_pipe'] = pygame.mixer.Sound('MetalPipeClang.mp3') #ignore this
    sounds['metal_pipe_loud'] = pygame.mixer.Sound('MetalPipeClangLoud.mp3') #ignore this also
    print("loading ball")
    sounds['ball'] = pygame.mixer.Sound('WiiBaseballBall.mp3')
    print("loaded ball, loading strike")
    sounds['strike'] = pygame.mixer.Sound('WiiBaseballStrike.mp3')
    print("loaded strike, loading out")
    sounds['out'] = pygame.mixer.Sound('WiiBaseballOut.mp3')
    print("loaded out, loading batter out")
    sounds['BatterOut'] = pygame.mixer.Sound('WiiBaseballBatterOut.mp3')
    print("loaded batter out, loading your out")
    sounds['YourOut'] = pygame.mixer.Sound('WiiBaseballYourOut.mp3')
    print("sounds loaded")

    return sounds

# Function to play random metal pipe sounds, you can ignore this whole thing
def metal_pipe_sound_thread():
    while True:
        if pipe_sounds_enabled:
            sleep_time = random.uniform(pipe_sound_min_time, pipe_sound_max_time)
            print(f"Waiting {sleep_time:.2f} seconds before next metal pipe sound.")
            time.sleep(sleep_time - 3)  # Subtract 3 seconds for warning
            print("Metal pipe sound in 3 seconds!")
            time.sleep(3)
            if random.randint(1, 100) == 1:
                sounds['metal_pipe_loud'].play()
                print("Playing loud metal pipe sound!")
            else:
                sounds['metal_pipe'].play()
                print("Playing metal pipe sound!")
        else:
            time.sleep(1)  # Check every second if pipe sounds are enabled

# Color interpolation function between green and red
def get_score_color(score, max_score):
    ratio = min(max(score / max_score, 0), 1)  # Normalize score between 0 and 1
    red = int(255 * ratio)
    green = int(255 * (1 - ratio))
    return (red, green, 0)

# Function to shift score image color based on proximity to target_score
def shift_score_color(score_image, score, target_score):
    # Get the color based on the score
    color = get_score_color(score, target_score)

    # Convert color to NumPy array
    color_array = np.array([[color]], dtype=np.uint8)

    # Get pixel array
    pixel_array = pygame.surfarray.pixels3d(score_image).copy()
    alpha_array = pygame.surfarray.pixels_alpha(score_image).copy()

    # Create a mask for near-white pixels
    tolerance = 50  # Adjust as needed
    mask = np.all(pixel_array >= 255 - tolerance, axis=2)

    # Apply the color to the masked areas
    pixel_array[mask] = color_array

    # Create a new surface from the modified arrays
    colored_image = pygame.Surface(score_image.get_size(), pygame.SRCALPHA)
    pygame.surfarray.blit_array(colored_image, pixel_array)
    pygame.surfarray.pixels_alpha(colored_image)[:] = alpha_array

    return colored_image

# Main game loop
def main():
    print("entered main loop")
    global resolution, sound_effects, boys_vs_girls_mode
    global teams_mode, line_enabled, pipe_sounds_enabled, baseball_mode, sounds #ignore the fact that there is pipe sounds

    screen = pygame.display.set_mode(resolution, pygame.RESIZABLE)
    pygame.display.set_caption('Scoreboard')

    images, score_images = load_images()
    sounds = load_sounds()

    # Start metal pipe sound thread, you can also ignore this
    threading.Thread(target=metal_pipe_sound_thread, daemon=True).start()

    # Variables to store scores
    left_score = 0
    right_score = 0
    prev_left_score = None
    prev_right_score = None
    print("scores set")

    # Variables to store baseball counts
    balls = 0
    strikes = 0
    outs = 0
    prev_balls = None
    prev_strikes = None
    prev_outs = None
    print("baseball counts set")

    # Variables to track when to update images
    need_update_team_images = True
    need_update_score_images = True
    print("update images variables set")

    # Scaled images
    left_scaled_image = None
    right_scaled_image = None
    left_score_scaled_image = None
    right_score_scaled_image = None
    print("variables set for scaling images")

    # Line surface
    line_surface = pygame.Surface(resolution, pygame.SRCALPHA)
    need_update_line = True

    # Read initial target score
    target_score = read_target_score()
    prev_target_score = target_score

    # Time when MaxScore.txt was last read
    last_target_score_read_time = time.time()

    # Flag to control when to redraw the screen
    need_redraw = True

    # Font for displaying baseball counts
    font = pygame.font.SysFont(None, 100)  # Adjust font size as needed

    clock = pygame.time.Clock()

    while True:
        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            elif event.type == pygame.VIDEORESIZE:
                # Lock aspect ratio
                width = event.w
                height = int(width / ASPECT_RATIO)
                resolution = (width, height)
                screen = pygame.display.set_mode(resolution, pygame.RESIZABLE)
                print(f"Window resized to {resolution}")
                need_update_team_images = True
                need_update_score_images = True  # Update score images as well
                need_update_line = True
                need_redraw = True
                # Update line surface
                line_surface = pygame.Surface(resolution, pygame.SRCALPHA)
                # Update font size based on new resolution
                font = pygame.font.SysFont(None, int(resolution[1] * 0.05))

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_y:
                    print("pressed y")
                    resolution = DEFAULT_RESOLUTION
                    screen = pygame.display.set_mode(resolution, pygame.RESIZABLE)
                    print("Resolution reset to default.")
                    need_update_team_images = True
                    need_update_score_images = True  # Update score images as well
                    need_update_line = True
                    need_redraw = True
                    # Update line surface
                    line_surface = pygame.Surface(resolution, pygame.SRCALPHA)
                    # Update font size based on new resolution
                    font = pygame.font.SysFont(None, int(resolution[1] * 0.05))


                elif event.key == pygame.K_s:
                    print("pressed s")
                    sound_effects = not sound_effects
                    print(f"Sound effects toggled to {sound_effects}")

                elif event.key == pygame.K_v:
                    print("pressed v")
                    boys_vs_girls_mode = not boys_vs_girls_mode
                    print(f"Boys vs Girls mode toggled to {boys_vs_girls_mode}")
                    need_update_team_images = True
                    need_redraw = True

                elif event.key == pygame.K_t:
                    print("pressed t")
                    teams_mode = not teams_mode
                    print(f"Teams mode toggled to {teams_mode}")
                    need_update_team_images = True
                    need_redraw = True

                elif event.key == pygame.K_r:
                    print("pressed r")
                    images, score_images = load_images()
                    print("Images reloaded.")
                    need_update_team_images = True
                    need_update_score_images = True
                    need_redraw = True

                elif event.key == pygame.K_l:
                    print("pressed l")
                    line_enabled = not line_enabled
                    print(f"Line down the middle toggled to {line_enabled}")
                    need_update_line = True
                    need_redraw = True

                elif event.key == pygame.K_p: #you can ignore this keybinding too
                    print("pressed p")
                    pipe_sounds_enabled = not pipe_sounds_enabled
                    print(f"Pipe sounds toggled to {pipe_sounds_enabled}")

                elif event.key == pygame.K_b:
                    print("pressed b")
                    baseball_mode = not baseball_mode
                    print(f"Baseball mode toggled to {baseball_mode}")
                    need_redraw = True  # Need to redraw when toggling baseball mode


        # Read scores from files
        try:
            with open('Left.txt', 'r') as f:
                left_score = int(f.read().strip())
            with open('Right.txt', 'r') as f:
                right_score = int(f.read().strip())
        except Exception as e:
            print(f"Error reading score files: {e}")

        # Read baseball counts from files
        try:
            with open('Balls.txt', 'r') as f:
                balls = int(f.read().strip())
            with open('Strikes.txt', 'r') as f:
                strikes = int(f.read().strip())
            with open('Outs.txt', 'r') as f:
                outs = int(f.read().strip())
        except Exception as e:
            print(f"Error reading baseball count files: {e}")

        # Initialize previous scores if None
        if prev_left_score is None:
            prev_left_score = left_score
        if prev_right_score is None:
            prev_right_score = right_score

        # Initialize previous baseball counts if None
        if prev_balls is None:
            prev_balls = balls
        if prev_strikes is None:
            prev_strikes = strikes
        if prev_outs is None:
            prev_outs = outs

        # Read target score from MaxScore.txt every 10 seconds
        current_time = time.time()
        if current_time - last_target_score_read_time >= 10:
            target_score = read_target_score()
            last_target_score_read_time = current_time
            if target_score != prev_target_score:
                need_update_score_images = True
                need_redraw = True
                print(f"Target score updated to {target_score}")
                prev_target_score = target_score

        # Check if scores have changed
        if left_score != prev_left_score or right_score != prev_right_score:
            if sound_effects:
                # Play sound only if score increased
                if (left_score > prev_left_score) or (right_score > prev_right_score):
                    sounds['point'].play()
                    print("Point scored! Playing sound effect.")
            need_update_score_images = True
            need_redraw = True
            prev_left_score = left_score
            prev_right_score = right_score

        # Check if baseball counts have increased
        if baseball_mode and sound_effects:
            # Balls
            if balls > prev_balls:
                # Play ball sound
                sounds['ball'].play()
                print("Ball count increased! Playing ball sound.")
            # Strikes
            if strikes > prev_strikes:
                # Play strike sound
                sounds['strike'].play()
                print("Strike count increased! Playing strike sound.")
            # Outs
            if outs > prev_outs:
                # Play random out sound
                random_out_sound = random.randint(1,3)
                if random_out_sound == 1:
                    sounds['out'].play()
                    print("Out count increased! Playing out sound.")
                elif random_out_sound == 2:
                    sounds['BatterOut'].play()
                    print("Out count increased! Playing batter out sound.")
                else:
                    sounds['YourOut'].play()
                    print("Out count increased! Playing your out sound")

            if balls != prev_balls or strikes != prev_strikes or outs != prev_outs:
                need_redraw = True  # Need to redraw to update counts

            prev_balls = balls
            prev_strikes = strikes
            prev_outs = outs

        # Update team images if needed
        if need_update_team_images:
            print("updating team images")
            left_image = None
            right_image = None

            if boys_vs_girls_mode:
                left_image = images.get('boys')
                right_image = images.get('girls')
            elif teams_mode:
                left_image = images.get('team1')
                right_image = images.get('team2')

            if left_image:
                # Scale image to fit window height while maintaining aspect ratio
                img_rect = left_image.get_rect()
                scaling_factor = resolution[1] / img_rect.height
                new_width = int(img_rect.width * scaling_factor)
                left_scaled_image = pygame.transform.scale(left_image, (new_width, resolution[1]))
                print(f"Left image scaled to {left_scaled_image.get_size()}")
            else:
                left_scaled_image = None

            if right_image:
                img_rect = right_image.get_rect()
                scaling_factor = resolution[1] / img_rect.height
                new_width = int(img_rect.width * scaling_factor)
                right_scaled_image = pygame.transform.scale(right_image, (new_width, resolution[1]))
                print(f"Right image scaled to {right_scaled_image.get_size()}")
            else:
                right_scaled_image = None

            need_update_team_images = False

        # Update score images if needed
        if need_update_score_images:
            print("updating score images")
            if left_score in score_images:
                img = score_images[left_score]
                # Shift color based on proximity to target_score
                img_colored = shift_score_color(img, left_score, target_score)
                # Scale image
                img_rect = img_colored.get_rect()
                scaling_factor = resolution[1] / img_rect.height
                new_width = int(img_rect.width * scaling_factor)
                left_score_scaled_image = pygame.transform.scale(img_colored, (new_width, resolution[1]))
                print(f"Left score image scaled to {left_score_scaled_image.get_size()}")
            else:
                left_score_scaled_image = None

            if right_score in score_images:
                img = score_images[right_score]
                # Shift color based on proximity to target_score
                img_colored = shift_score_color(img, right_score, target_score)
                # Scale image
                img_rect = img_colored.get_rect()
                scaling_factor = resolution[1] / img_rect.height
                new_width = int(img_rect.width * scaling_factor)
                right_score_scaled_image = pygame.transform.scale(img_colored, (new_width, resolution[1]))
                print(f"Right score image scaled to {right_score_scaled_image.get_size()}")
            else:
                right_score_scaled_image = None

            need_update_score_images = False

        # Update line if needed
        if need_update_line:
            print("updating line")
            line_surface.fill((0, 0, 0, 0))  # Clear line_surface
            if line_enabled:
                pygame.draw.line(line_surface, (255, 255, 255),  # Line color is white
                                 (resolution[0] // 2, 0),
                                 (resolution[0] // 2, resolution[1]),
                                 LINE_WIDTH)
                print("Updated line on line_surface.")
            need_update_line = False

        # Redraw the screen only if needed
        if need_redraw:
            print("Redrawing screen")
            # Clear screen
            screen.fill((0, 0, 0))

            # Blit the team images
            if left_scaled_image:
                print("blitting left team image")
                screen.blit(left_scaled_image, (0, 0))

            if right_scaled_image:
                print("blitting right team image")
                right_x = resolution[0] - right_scaled_image.get_width()
                screen.blit(right_scaled_image, (right_x, 0))

            # Blit the score images
            if left_score_scaled_image:
                print("blitting left score image")
                screen.blit(left_score_scaled_image, (0, 0))

            if right_score_scaled_image:
                print("blitting right score image")
                right_x = resolution[0] - right_score_scaled_image.get_width()
                screen.blit(right_score_scaled_image, (right_x, 0))

            # Blit the line_surface onto the screen
            if line_enabled:
                print("blitting line")
                screen.blit(line_surface, (0, 0))

            # Display baseball counts if in baseball mode
            if baseball_mode:
                print("Displaying baseball counts")
                # Prepare text surfaces with drop shadow
                text_color = (255, 255, 255)  # Original text color (white)
                shadow_color = (0, 0, 0)      # Shadow color (black)
                shadow_offset = (2, 2)        # Shadow offset in pixels

                # Render texts
                balls_text = font.render(f"Balls: {balls}", True, text_color)
                balls_shadow = font.render(f"Balls: {balls}", True, shadow_color)
                strikes_text = font.render(f"Strikes: {strikes}", True, text_color)
                strikes_shadow = font.render(f"Strikes: {strikes}", True, shadow_color)
                outs_text = font.render(f"Outs: {outs}", True, text_color)
                outs_shadow = font.render(f"Outs: {outs}", True, shadow_color)

                # Position the texts along the bottom
                screen_width, screen_height = screen.get_size()
                text_margin = int(screen_width * 0.02)  # Horizontal margin between texts

                balls_width = balls_text.get_width()
                strikes_width = strikes_text.get_width()
                outs_width = outs_text.get_width()
                text_height = balls_text.get_height()  # Assuming all texts have similar height

                total_text_width = balls_width + strikes_width + outs_width + text_margin * 2  # Margins between texts

                start_x = (screen_width - total_text_width) // 2
                y_position = screen_height - text_margin - text_height

                current_x = start_x

                # Blit 'balls' shadow
                screen.blit(balls_shadow, (current_x + shadow_offset[0], y_position + shadow_offset[1]))
                # Blit 'balls' text
                screen.blit(balls_text, (current_x, y_position))
                current_x += balls_width + text_margin

                # Blit 'strikes' shadow
                screen.blit(strikes_shadow, (current_x + shadow_offset[0], y_position + shadow_offset[1]))
                # Blit 'strikes' text
                screen.blit(strikes_text, (current_x, y_position))
                current_x += strikes_width + text_margin

                # Blit 'outs' shadow
                screen.blit(outs_shadow, (current_x + shadow_offset[0], y_position + shadow_offset[1]))
                # Blit 'outs' text
                screen.blit(outs_text, (current_x, y_position))


            # Update display
            pygame.display.flip()
            need_redraw = False

        clock.tick(60)  # Limit to 60 FPS

if __name__ == "__main__":
    main()
