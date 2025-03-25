# project.py
import pygame
import sys
import requests
from requests.auth import HTTPBasicAuth

# Initialize Pygame
pygame.init()

# Window dimensions
WIDTH, HEIGHT = 900, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Memory Management Visualizer - Pro Edition")

# Colors (Dark, minimal theme)
BG_COLOR = (30, 30, 30)
TEXT_COLOR = (220, 220, 220)
BORDER_COLOR = (60, 60, 60)
RED = (200, 50, 50)
GREEN = (50, 200, 50)
YELLOW = (255, 255, 0)  # For page fault flash
BUTTON_COLOR = (70, 70, 70)
BUTTON_HOVER = (90, 90, 90)
INPUT_COLOR = (50, 50, 50)
INPUT_ACTIVE = (80, 80, 80)

# Fonts
TITLE_FONT = pygame.font.SysFont("Arial", 32, bold=True)
LABEL_FONT = pygame.font.SysFont("Arial", 20)
TEXT_FONT = pygame.font.SysFont("Arial", 18)

# API Configuration
API_BASE_URL = "http://localhost:5000"
AUTH = HTTPBasicAuth("admin", "password123")

# Button class (For interactive buttons like Start, Step, Reset)
class Button:
    def __init__(self, x, y, width, height, text, action=None):
        self.rect = pygame.Rect(x, y, width, height)
        self.label = text
        self.text = TEXT_FONT.render(text, True, TEXT_COLOR)
        self.text_rect = self.text.get_rect(center=self.rect.center)
        self.action = action

    def draw(self, screen):
        mouse_pos = pygame.mouse.get_pos()
        color = BUTTON_HOVER if self.rect.collidepoint(mouse_pos) else BUTTON_COLOR
        pygame.draw.rect(screen, color, self.rect, border_radius=5)
        pygame.draw.rect(screen, BORDER_COLOR, self.rect, 1, border_radius=5)
        screen.blit(self.text, self.text_rect)

    def check_click(self, event):
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
        screen.blit(self.label, self.label_rect)
        color = INPUT_ACTIVE if self.active else INPUT_COLOR
        pygame.draw.rect(screen, color, self.rect, border_radius=5)
        pygame.draw.rect(screen, BORDER_COLOR, self.rect, 1, border_radius=5)
        text_surface = TEXT_FONT.render(self.text, True, TEXT_COLOR)
        screen.blit(text_surface, (self.rect.x + 5, self.rect.y + 5))

    def handle_event(self, event):
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
        return self.text

    def reset(self):
        self.text = ""
        self.active = False

# Visualization functions
def draw_memory(screen, frames, frame_counter, last_page_fault, flash_timer):
    if frame_counter % 60 == 0:  # Print once per second
        print(f"Drawing frames: {frames}")
    title = LABEL_FONT.render("Memory Frames", True, TEXT_COLOR)
    screen.blit(title, (20, 80))
    frame_count = len(frames)
    total_width = WIDTH - 200
    frame_width = total_width // frame_count
    for i, frame in enumerate(frames):
        # Flash the frame yellow if it was involved in a page fault
        if last_page_fault == i and flash_timer > 0:
            color = YELLOW
        else:
            color = GREEN if frame is None else RED
        x = 20 + i * frame_width
        pygame.draw.rect(screen, color, (x, 110, frame_width - 5, 80), border_radius=5)
        pygame.draw.rect(screen, BORDER_COLOR, (x, 110, frame_width - 5, 80), 1, border_radius=5)

def draw_table(screen, page_table, mode):
    title = LABEL_FONT.render("Page Table" if mode == "Paging" else "Segment Table", True, TEXT_COLOR)
    screen.blit(title, (20, 220))
    y = 250
    for process_id, frames in page_table.items():
        for i, frame in enumerate(frames):
            if frame is not None:
                text = TEXT_FONT.render(f"P{process_id} Page {i} -> Frame {frame}", True, TEXT_COLOR)
                screen.blit(text, (20, y))
                y += 30

def draw_stats(screen, page_faults, memory_used, mode, algorithm, status):
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

# API Interaction Functions
def get_memory_state():
    try:
        response = requests.get(f"{API_BASE_URL}/display_memory")
        response.raise_for_status()
        state = response.json()
        return {
            "frames": state["Memory Frames"],
            "page_table": state["Page Table"],
            "page_faults": state["Total Page Faults"],
            "memory_used": (sum(1 for f in state["Memory Frames"] if f is not None) * 100) // len(state["Memory Frames"]),
            "mode": "Paging",  # Hardcoded for now, as Module 1 only supports paging
            "algorithm": "FIFO",  # Hardcoded, as Module 1 uses FIFO
            "last_page_fault": state.get("Last Page Fault")  # Added for visualization
        }
    except requests.RequestException as e:
        print(f"Error fetching memory state: {e}")
        return {
            "frames": [None] * 4,
            "page_table": {},
            "page_faults": 0,
            "memory_used": 0,
            "mode": "Paging",
            "algorithm": "FIFO",
            "last_page_fault": None
        }

def allocate_page(process_id, page_num):
    try:
        response = requests.post(
            f"{API_BASE_URL}/allocate_paging",
            json={"process_id": str(process_id), "num_pages": 1},
            auth=AUTH
        )
        response.raise_for_status()
        print(f"Page allocated: {response.json()}")
    except requests.RequestException as e:
        print(f"Error allocating page: {e}")

def simulate_page_request(process_id, page_num):
    try:
        response = requests.post(
            f"{API_BASE_URL}/simulate_page_request",
            json={"process_id": process_id, "page_num": page_num},
            auth=AUTH
        )
        response.raise_for_status()
        print(f"Page request simulated: {response.json()}")
    except requests.RequestException as e:
        print(f"Error simulating page request: {e}")

def reset_memory():
    try:
        response = requests.post(f"{API_BASE_URL}/reset")
        response.raise_for_status()
        print(f"Reset response: {response.json()}")
    except requests.RequestException as e:
        print(f"Error resetting memory state: {e}")

# Main function
def run_project():
    clock = pygame.time.Clock()
    running = True
    step = 0
    sequence = []
    mode = "Paging"
    algorithm = "FIFO"
    status = "Ready"
    input_active = True
    frame_counter = 0
    memory_state = get_memory_state()  # Cache the initial memory state
    flash_timer = 0  # Timer for flashing page fault frames

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
            sequence_input.text = f"Invalid input! Use numbers (e.g., 0,1,2). Error: {str(e)}"
            print(f"ValueError in start_simulation: {str(e)}")
            input_active = True
        except Exception as e:
            sequence_input.text = f"Error: {str(e)}"
            print(f"Exception in start_simulation: {str(e)}")
            input_active = True

    def step_simulation():
        nonlocal step, status, input_active, memory_state, flash_timer
        try:
            print(f"Step: {step}, Sequence: {sequence}, Sequence length: {len(sequence)}")
            if not sequence:
                sequence_input.text = "Error: No sequence to process. Please start a new simulation."
                status = "Ready"
                input_active = True
                return
            if step < len(sequence):
                process_id, page_num = sequence[step]
                print(f"Allocating page: Process {process_id}, Page {page_num}")
                allocate_page(process_id, page_num)
                print(f"Simulating page request: Process {process_id}, Page {page_num}")
                simulate_page_request(process_id, page_num)
                step += 1
                memory_state = get_memory_state()  # Update memory state after stepping
                if memory_state["last_page_fault"] is not None:
                    flash_timer = 30  # Flash for 30 frames (0.5 seconds at 60 FPS)
            if step >= len(sequence):
                status = "Finished"
        except Exception as e:
            sequence_input.text = f"Error in step: {str(e)}"
            print(f"Exception in step_simulation: {str(e)}")

    def reset_simulation():
        nonlocal step, sequence, input_active, status, memory_state, flash_timer
        reset_memory()
        step = 0
        sequence = []
        input_active = True
        status = "Ready"
        sequence_input.reset()
        memory_state = get_memory_state()  # Update memory state after reset
        flash_timer = 0
        print("Reset complete")

    # Assign actions to buttons
    start_button.action = start_simulation
    step_button.action = step_simulation
    reset_button.action = reset_simulation
    paging_button.action = lambda: None  # Not implemented in Module 1
    seg_button.action = lambda: None  # Not implemented in Module 1
    vm_button.action = lambda: None  # Not implemented in Module 1
    fifo_button.action = lambda: None  # Hardcoded in Module 1
    lru_button.action = lambda: None  # Not implemented in Module 1

    # Main loop
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            sequence_input.handle_event(event)
            start_button.check_click(event)
            if not input_active:
                step_button.check_click(event)
            reset_button.check_click(event)
            paging_button.check_click(event)
            seg_button.check_click(event)
            vm_button.check_click(event)
            fifo_button.check_click(event)
            lru_button.check_click(event)

        # Update flash timer
        if flash_timer > 0:
            flash_timer -= 1

        # Redraw the screen once per frame
        screen.fill(BG_COLOR)
        draw_memory(screen, memory_state["frames"], frame_counter, memory_state["last_page_fault"], flash_timer)
        draw_table(screen, memory_state["page_table"], memory_state["mode"])
        draw_stats(screen, memory_state["page_faults"], memory_state["memory_used"], memory_state["mode"], memory_state["algorithm"], status)
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
    run_project()