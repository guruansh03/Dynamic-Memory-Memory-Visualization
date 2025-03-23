# vizui.py
import pygame
import sys

# Initialize Pygame
pygame.init()

# Window dimensions
WIDTH, HEIGHT = 900, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Memory Management Visualizer - Pro Edition")

# Colors (Dark, minimal theme)
BG_COLOR = (30, 30, 30)
PANEL_COLOR = (40, 40, 40)
TEXT_COLOR = (220, 220, 220)
BORDER_COLOR = (60, 60, 60)
RED = (200, 50, 50)
GREEN = (50, 200, 50)
BUTTON_COLOR = (70, 70, 70)
BUTTON_HOVER = (90, 90, 90)
INPUT_COLOR = (50, 50, 50)
INPUT_ACTIVE = (80, 80, 80)

# Fonts
TITLE_FONT = pygame.font.SysFont("Arial", 32, bold=True)
LABEL_FONT = pygame.font.SysFont("Arial", 20)
TEXT_FONT = pygame.font.SysFont("Arial", 18)

# Mock Simulator (Simulates memory management operations)
class MockSimulator:
    def __init__(self):
        self.frames = [None] * 6
        self.page_table = {}
        self.page_faults = 0
        self.mode = "Paging"
        self.algorithm = "FIFO"

    def allocate_page(self, process_id, page_num, algorithm):
        """Allocate a page to a frame using the specified algorithm."""
        self.algorithm = algorithm
        print(f"Before allocation - Frames: {self.frames}, Process ID: {process_id}, Page Num: {page_num}, Algorithm: {algorithm}")
        for i in range(len(self.frames)):
            if self.frames[i] is None:
                self.frames[i] = (process_id, page_num)
                self.page_table[(process_id, page_num)] = i
                self.page_faults += 1
                print(f"After allocation - Frames: {self.frames}, Page Table: {self.page_table}, Page Faults: {self.page_faults}")
                return
        old_page = self.frames[0]
        if old_page:
            del self.page_table[old_page]
        self.frames.pop(0)
        self.frames.append((process_id, page_num))
        self.page_table[(process_id, page_num)] = len(self.frames) - 1
        self.page_faults += 1
        print(f"After replacement - Frames: {self.frames}, Page Table: {self.page_table}, Page Faults: {self.page_faults}")

    def reset(self):
        """Reset the simulator to its initial state."""
        self.frames = [None] * 6
        self.page_table = {}
        self.page_faults = 0

    def get_state(self):
        """Return the current state of the simulator."""
        used = len([f for f in self.frames if f is not None])
        total = len(self.frames)
        return {
            "frames": self.frames,
            "page_table": self.page_table,
            "page_faults": self.page_faults,
            "memory_used": (used * 100) // total,
            "mode": self.mode,
            "algorithm": self.algorithm
        }

# Button class (For interactive buttons like Start, Step, Reset)
class Button:
    def __init__(self, x, y, width, height, text, action=None):
        self.rect = pygame.Rect(x, y, width, height)
        self.label = text
        self.text = TEXT_FONT.render(text, True, TEXT_COLOR)
        self.text_rect = self.text.get_rect(center=self.rect.center)
        self.action = action

    def draw(self, screen):
        """Draw the button on the screen."""
        mouse_pos = pygame.mouse.get_pos()
        color = BUTTON_HOVER if self.rect.collidepoint(mouse_pos) else BUTTON_COLOR
        pygame.draw.rect(screen, color, self.rect, border_radius=5)
        pygame.draw.rect(screen, BORDER_COLOR, self.rect, 1, border_radius=5)
        screen.blit(self.text, self.text_rect)

    def check_click(self, event):
        """Check if the button is clicked and perform its action."""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                print(f"Button {self.label} clicked")
                if self.action:
                    self.action()
                return True
        return False

# Text input field (For entering the sequence)
class TextInput:
    def __init__(self, x, y, width, height, label):
        self.rect = pygame.Rect(x, y, width, height)
        self.label = LABEL_FONT.render(label, True, TEXT_COLOR)
        self.label_rect = self.label.get_rect(topleft=(x, y - 30))
        self.text = ""
        self.active = False

    def draw(self, screen):
        """Draw the text input field on the screen."""
        screen.blit(self.label, self.label_rect)
        color = INPUT_ACTIVE if self.active else INPUT_COLOR
        pygame.draw.rect(screen, color, self.rect, border_radius=5)
        pygame.draw.rect(screen, BORDER_COLOR, self.rect, 1, border_radius=5)
        text_surface = TEXT_FONT.render(self.text, True, TEXT_COLOR)
        screen.blit(text_surface, (self.rect.x + 5, self.rect.y + 5))

    def handle_event(self, event):
        """Handle user input events for the text field."""
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.active = self.rect.collidepoint(event.pos)
            print(f"Input active: {self.active}")
        if self.active and event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                self.active = False
                print(f"Input deactivated, text: {self.text!r}")
            elif event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
                print(f"Backspace, text: {self.text!r}")
            else:
                self.text += event.unicode
                print(f"Key pressed, text: {self.text!r}")
        return self.text if not self.active and self.text else None

    def get_text(self):
        """Return the current text in the input field."""
        return self.text

    def reset(self):
        """Reset the text input field to its initial state."""
        self.text = ""
        self.active = False

# Visualization functions
def draw_memory(screen, frames, frame_counter):
    """Draw the memory frames on the screen."""
    if frame_counter % 60 == 0:  # Print once per second
        print(f"Drawing frames: {frames}")
    title = LABEL_FONT.render("Memory Frames", True, TEXT_COLOR)
    screen.blit(title, (20, 80))
    frame_count = len(frames)
    total_width = WIDTH - 200
    frame_width = total_width // frame_count
    for i, frame in enumerate(frames):
        color = GREEN if frame is None else RED
        x = 20 + i * frame_width
        pygame.draw.rect(screen, color, (x, 110, frame_width - 5, 80), border_radius=5)
        pygame.draw.rect(screen, BORDER_COLOR, (x, 110, frame_width - 5, 80), 1, border_radius=5)

def draw_table(screen, page_table, mode):
    """Draw the page/segment table on the screen."""
    title = LABEL_FONT.render("Page Table" if mode == "Paging" else "Segment Table", True, TEXT_COLOR)
    screen.blit(title, (20, 220))
    y = 250
    for (proc_id, page), frame in page_table.items():
        text = TEXT_FONT.render(f"P{proc_id} Page {page} -> Frame {frame}", True, TEXT_COLOR)
        screen.blit(text, (20, y))
        y += 30

def draw_stats(screen, page_faults, memory_used, mode, algorithm, status):
    """Draw the title, stats, and mode/algorithm/status on the right side."""
    title = TITLE_FONT.render("Memory Management Visualizer", True, TEXT_COLOR)
    screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 20))
    stats = TEXT_FONT.render(f"Page Faults: {page_faults} | Usage: {memory_used}%", True, TEXT_COLOR)
    screen.blit(stats, (20, 50))
    mode_font = pygame.font.SysFont("Arial", 20)
    mode_text = mode_font.render(f"Mode: {mode}", True, TEXT_COLOR)
    algo_text = mode_font.render(f"Algorithm: {algorithm}", True, TEXT_COLOR)
    status_text = mode_font.render(f"Status: {status}", True, TEXT_COLOR)
    screen.blit(mode_text, (WIDTH - 200, 220))
    screen.blit(algo_text, (WIDTH - 200, 250))
    screen.blit(status_text, (WIDTH - 200, 280))

# Main function
def run_vizui():
    """Main function to run the visualizer."""
    sim = MockSimulator()
    clock = pygame.time.Clock()
    running = True
    step = 0
    sequence = []
    mode = "Paging"
    algorithm = "FIFO"
    status = "Ready"
    input_active = True
    frame_counter = 0  # To reduce console clutter

    # UI Elements
    sequence_input = TextInput(20, 350, 300, 40, "Enter Sequence (e.g., 0,1,2):")
    start_button = Button(340, 350, 100, 40, "Start")
    step_button = Button(450, 350, 100, 40, "Step")
    reset_button = Button(560, 350, 100, 40, "Reset")
    paging_button = Button(20, 450, 120, 40, "Paging")
    seg_button = Button(150, 450, 120, 40, "Segmentation")
    vm_button = Button(280, 450, 120, 40, "Virtual Memory")
    fifo_button = Button(450, 450, 100, 40, "FIFO")
    lru_button = Button(560, 450, 100, 40, "LRU")

    def start_simulation():
        """Parse the input sequence and start the simulation."""
        nonlocal sequence, input_active, step, status
        try:
            raw_input = sequence_input.get_text()
            print(f"Raw input (before strip): {raw_input!r}")
            raw_input = raw_input.strip()
            print(f"Raw input (after strip): {raw_input!r}")
            raw_input = raw_input.replace(" ", ",")
            print(f"After replacing spaces: {raw_input!r}")
            if "," not in raw_input:
                raw_input = ",".join(list(raw_input))
                print(f"After adding commas: {raw_input!r}")
            split_input = raw_input.split(",")
            print(f"Split input: {split_input!r}")
            filtered_input = [x.strip() for x in split_input if x.strip()]
            print(f"Filtered input: {filtered_input!r}")
            if not filtered_input:
                raise ValueError("No valid numbers found in input!")
            sequence_numbers = [int(x) for x in filtered_input]
            print(f"Sequence numbers: {sequence_numbers}")
            sequence = [(1, num) for num in sequence_numbers]
            print(f"Sequence: {sequence}")
            if not sequence:
                raise ValueError("Sequence cannot be empty!")
            input_active = False
            step = 0
            status = "Running"
            print("start_simulation completed successfully")
        except ValueError as e:
            sequence_input.text = f"Invalid input! Use Wnumbers (e.g., 0,1,2). Error: {str(e)}"
            print(f"ValueError in start_simulation: {str(e)}")
            input_active = True
        except Exception as e:
            sequence_input.text = f"Error: {str(e)}"
            print(f"Exception in start_simulation: {str(e)}")
            input_active = True

    def step_simulation():
        """Process the next page in the sequence and update the simulator state."""
        nonlocal step, status, input_active
        try:
            print(f"Step: {step}, Sequence: {sequence}, Sequence length: {len(sequence)}")
            print(f"Current sim frames: {sim.frames}")
            if not sequence:
                sequence_input.text = "Error: No sequence to process. Please start a new simulation."
                status = "Ready"
                input_active = True
                return
            if step < len(sequence):
                print(f"Allocating page: {sequence[step]}")
                sim.allocate_page(sequence[step][0], sequence[step][1], algorithm)
                step += 1
            if step >= len(sequence):
                status = "Finished"
        except Exception as e:
            sequence_input.text = f"Error in step: {str(e)}"
            print(f"Exception in step_simulation: {str(e)}")

    def reset_simulation():
        """Reset the simulation to its initial state."""
        nonlocal step, sequence, input_active, status
        sim.reset()
        step = 0
        sequence = []
        input_active = True
        status = "Ready"
        sequence_input.reset()
        print("Reset complete")

    # Assign actions to buttons
    start_button.action = start_simulation
    step_button.action = step_simulation
    reset_button.action = reset_simulation
    paging_button.action = lambda: (setattr(sim, "mode", "Paging"), globals().update(mode="Paging"))
    seg_button.action = lambda: (setattr(sim, "mode", "Segmentation"), globals().update(mode="Segmentation"))
    vm_button.action = lambda: (setattr(sim, "mode", "Virtual Memory"), globals().update(mode="Virtual Memory"))
    fifo_button.action = lambda: (setattr(sim, "algorithm", "FIFO"), globals().update(algorithm="FIFO"))
    lru_button.action = lambda: (setattr(sim, "algorithm", "LRU"), globals().update(algorithm="LRU"))

    # Main loop
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            sequence_input.handle_event(event)
            if not input_active:
                print("Step button active")
                step_button.check_click(event)
            start_button.check_click(event)
            reset_button.check_click(event)
            paging_button.check_click(event)
            seg_button.check_click(event)
            vm_button.check_click(event)
            fifo_button.check_click(event)
            lru_button.check_click(event)

        # Redraw the screen once per frame
        screen.fill(BG_COLOR)
        state = sim.get_state()
        draw_memory(screen, state["frames"], frame_counter)
        draw_table(screen, state["page_table"], state["mode"])
        draw_stats(screen, state["page_faults"], state["memory_used"], state["mode"], state["algorithm"], status)
        sequence_input.draw(screen)
        start_button.draw(screen)
        if not input_active:
            step_button.draw(screen)
        reset_button.draw(screen)
        paging_button.draw(screen)
        seg_button.draw(screen)
        vm_button.draw(screen)
        fifo_button.draw(screen)
        lru_button.draw(screen)
        pygame.display.flip()
        frame_counter += 1
        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    run_vizui()