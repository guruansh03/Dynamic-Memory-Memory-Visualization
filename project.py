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
GRAY = (150, 150, 150)
WHITE = (255, 255, 255)
SCROLLBAR_BG_COLOR = (40, 40, 40)

# Fonts
TITLE_FONT = pygame.font.SysFont("Arial", 32, bold=True)
LABEL_FONT = pygame.font.SysFont("Arial", 20)
TEXT_FONT = pygame.font.SysFont("Arial", 18)

# API Configuration
API_BASE_URL = "http://localhost:5000"
AUTH = HTTPBasicAuth("admin", "password123")

# Button class
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

# Text input field
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
    if frame_counter % 60 == 0:
        print(f"Drawing frames: {frames}")
    title = LABEL_FONT.render("Memory Frames", True, TEXT_COLOR)
    screen.blit(title, (20, 80))
    frame_count = len(frames)
    total_width = WIDTH - 40
    frame_width = total_width // frame_count
    frame_height = 60
    for i, frame in enumerate(frames):
        if last_page_fault == i and flash_timer > 0:
            color = YELLOW
        else:
            color = GREEN if frame is None else RED
        x = 20 + i * frame_width
        pygame.draw.rect(screen, color, (x, 110, frame_width - 5, frame_height), border_radius=5)
        pygame.draw.rect(screen, BORDER_COLOR, (x, 110, frame_width - 5, frame_height), 1, border_radius=5)
        if frame is not None:
            label = TEXT_FONT.render(f"P{frame[0]} Pg{frame[1]}", True, TEXT_COLOR)
            screen.blit(label, (x + 5, 110 + frame_height // 2 - 10))

def draw_segmentation_memory(screen, memory_state, free_blocks, frame_counter, last_allocation, flash_timer):
    if frame_counter % 60 == 0:
        print(f"Drawing segmentation memory: {memory_state}, Free blocks: {free_blocks}")
    title = LABEL_FONT.render("Memory Segments", True, TEXT_COLOR)
    screen.blit(title, (20, 80))
    total_memory = 32
    total_width = WIDTH - 40
    pixel_per_kb = total_width / total_memory
    frame_height = 60
    for base, size, pid, sid in memory_state:
        x = 20 + base * pixel_per_kb
        width = size * pixel_per_kb
        if last_allocation and last_allocation[0] == base and flash_timer > 0:
            color = YELLOW
        else:
            color = RED
        pygame.draw.rect(screen, color, (x, 110, width - 5, frame_height), border_radius=5)
        pygame.draw.rect(screen, BORDER_COLOR, (x, 110, width - 5, frame_height), 1, border_radius=5)
        label = TEXT_FONT.render(f"P{pid} S{sid}", True, TEXT_COLOR)
        screen.blit(label, (x + 5, 110 + frame_height // 2 - 10))
    for base, size in free_blocks:
        x = 20 + base * pixel_per_kb
        width = size * pixel_per_kb
        pygame.draw.rect(screen, GREEN, (x, 110, width - 5, frame_height), border_radius=5)
        pygame.draw.rect(screen, BORDER_COLOR, (x, 110, width - 5, frame_height), 1, border_radius=5)

def draw_virtual_memory(screen, memory_frames, swap_space, frame_counter, last_page_fault, flash_timer):
    if frame_counter % 60 == 0:
        print(f"Drawing virtual memory - Frames: {memory_frames}, Swap: {swap_space}")
    title = LABEL_FONT.render("Physical Memory", True, TEXT_COLOR)
    screen.blit(title, (20, 80))
    frame_count = len(memory_frames)
    total_width = WIDTH - 40
    frame_width = total_width // frame_count
    frame_height = 40
    for i, frame in enumerate(memory_frames):
        if last_page_fault == i and flash_timer > 0:
            color = YELLOW
        else:
            color = GREEN if frame is None else RED
        x = 20 + i * frame_width
        pygame.draw.rect(screen, color, (x, 110, frame_width - 5, frame_height), border_radius=5)
        pygame.draw.rect(screen, BORDER_COLOR, (x, 110, frame_width - 5, frame_height), 1, border_radius=5)
        if frame is not None:
            label = TEXT_FONT.render(f"P{frame[0]} Pg{frame[1]}", True, TEXT_COLOR)
            screen.blit(label, (x + 5, 110 + frame_height // 2 - 10))
    title = LABEL_FONT.render("Swap Space", True, TEXT_COLOR)
    screen.blit(title, (20, 160))
    swap_count = len(swap_space)
    swap_width = total_width // swap_count
    for i, frame in enumerate(swap_space):
        color = GREEN if frame is None else RED
        x = 20 + i * swap_width
        pygame.draw.rect(screen, color, (x, 190, swap_width - 5, frame_height), border_radius=5)
        pygame.draw.rect(screen, BORDER_COLOR, (x, 190, swap_width - 5, frame_height), 1, border_radius=5)
        if frame is not None:
            label = TEXT_FONT.render(f"P{frame[0]} Pg{frame[1]}", True, TEXT_COLOR)
            screen.blit(label, (x + 5, 190 + frame_height // 2 - 10))

def draw_table(screen, page_table, mode, scroll_offset=0, max_visible_entries=5, up_button_rect=None, down_button_rect=None):
    title = LABEL_FONT.render("Page Table" if mode in ["Paging", "Virtual Memory"] else "Segment Table", True, TEXT_COLOR)
    screen.blit(title, (20, 220))
    y = 250
    entry_height = 30
    if mode == "Virtual Memory":
        total_entries = sum(len(pages) for pid, pages in page_table.items())
        if total_entries <= max_visible_entries:
            scroll_offset = 0
        else:
            max_offset = total_entries - max_visible_entries
            scroll_offset = max(0, min(scroll_offset, max_offset))
        max_height = entry_height * max_visible_entries
        clip_rect = pygame.Rect(20, y, 250, max_height)
        screen.set_clip(clip_rect)
        all_entries = []
        for process_id, pages in page_table.items():
            for page_num, frame, in_memory in pages:
                location = f"Frame {frame}" if in_memory else f"Swap {frame}"
                text = f"P{process_id} Page {page_num} -> {location}"
                all_entries.append(text)
        for i in range(scroll_offset, min(scroll_offset + max_visible_entries, len(all_entries))):
            text = TEXT_FONT.render(all_entries[i], True, TEXT_COLOR)
            screen.blit(text, (20, y + (i - scroll_offset) * entry_height))
        screen.set_clip(None)
        scrollbar_rect = pygame.Rect(280, y, 20, max_height)
        pygame.draw.rect(screen, SCROLLBAR_BG_COLOR, scrollbar_rect, border_radius=5)
        pygame.draw.rect(screen, BORDER_COLOR, scrollbar_rect, 1, border_radius=5)
        if up_button_rect and down_button_rect:
            up_color = GRAY if scroll_offset == 0 else WHITE
            down_color = GRAY if scroll_offset >= total_entries - max_visible_entries else WHITE
            pygame.draw.rect(screen, up_color, up_button_rect, border_radius=5)
            pygame.draw.rect(screen, BORDER_COLOR, up_button_rect, 1, border_radius=5)
            pygame.draw.rect(screen, down_color, down_button_rect, border_radius=5)
            pygame.draw.rect(screen, BORDER_COLOR, down_button_rect, 1, border_radius=5)
            pygame.draw.polygon(screen, TEXT_COLOR, [
                (up_button_rect.centerx, up_button_rect.centery - 5),
                (up_button_rect.centerx - 5, up_button_rect.centery + 5),
                (up_button_rect.centerx + 5, up_button_rect.centery + 5)
            ])
            pygame.draw.polygon(screen, TEXT_COLOR, [
                (down_button_rect.centerx, down_button_rect.centery + 5),
                (down_button_rect.centerx - 5, down_button_rect.centery - 5),
                (down_button_rect.centerx + 5, down_button_rect.centery - 5)
            ])
    else:
        for process_id, pages in page_table.items():
            for i, page in enumerate(pages):
                if page is not None:
                    text = TEXT_FONT.render(f"P{process_id} Page {i} -> Frame {page}", True, TEXT_COLOR)
                    screen.blit(text, (20, y))
                    y += 30
                    if y > 400:
                        break
            if y > 400:
                break
    return scroll_offset

def draw_stats(screen, faults, memory_used, mode, algorithm, status, swap_operations=None):
    title = TITLE_FONT.render("Memory Management Visualizer", True, TEXT_COLOR)
    screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 20))
    fault_label = "Page Faults" if mode in ["Paging", "Virtual Memory"] else "Allocation Failures"
    stats_text = f"{fault_label}: {faults} | Usage: {memory_used}%"
    if mode == "Virtual Memory" and swap_operations is not None:
        stats_text += f" | Swaps: {swap_operations}"
    stats = TEXT_FONT.render(stats_text, True, TEXT_COLOR)
    screen.blit(stats, (20, 50))
    mode_font = pygame.font.SysFont("Arial", 20)
    mode_text = mode_font.render(f"Mode: {mode}", True, TEXT_COLOR)
    algo_text = mode_font.render(f"Algorithm: {algorithm}", True, TEXT_COLOR)
    status_text = mode_font.render(f"Status: {status}", True, TEXT_COLOR)
    screen.blit(mode_text, (WIDTH - 200, 220))
    screen.blit(algo_text, (WIDTH - 200, 250))
    screen.blit(status_text, (WIDTH - 200, 280))

# API Interaction Functions
def check_api_availability():
    try:
        response = requests.get(f"{API_BASE_URL}/display_memory", auth=AUTH, timeout=2)
        response.raise_for_status()
        return True
    except requests.RequestException as e:
        print(f"API check failed: {e}")
        return False

def get_memory_state():
    try:
        response = requests.get(f"{API_BASE_URL}/display_memory", auth=AUTH)
        response.raise_for_status()
        state = response.json()
        return {
            "frames": state["Memory Frames"],
            "page_table": state["Page Table"],
            "page_faults": state["Total Page Faults"],
            "memory_used": (sum(1 for f in state["Memory Frames"] if f is not None) * 100) // len(state["Memory Frames"]),
            "mode": "Paging",
            "algorithm": "FIFO",
            "last_page_fault": state.get("Last Page Fault")
        }
    except requests.RequestException as e:
        print(f"Error fetching memory state: {e}")
        return {
            "frames": [None] * 8,
            "page_table": {},
            "page_faults": 0,
            "memory_used": 0,
            "mode": "Paging",
            "algorithm": "FIFO",
            "last_page_fault": None
        }

def allocate_page(process_id, page_num):
    try:
        payload = {"process_id": str(process_id), "num_pages": 1}  # Send as string
        print(f"Sending allocate_paging request with payload: {payload}")
        response = requests.post(f"{API_BASE_URL}/allocate_paging", json=payload, auth=AUTH)
        response.raise_for_status()
        print(f"Page allocated: {response.json()}")
    except requests.RequestException as e:
        error_msg = str(e)
        if hasattr(e, 'response') and e.response is not None:
            error_msg += f" (Response: {e.response.text})"
        print(f"Error allocating page: {error_msg}")
        raise Exception(f"Failed to allocate page: {error_msg}")

def simulate_page_request(process_id, page_num):
    try:
        payload = {"process_id": str(process_id), "page_num": str(page_num)}  # Send as string
        print(f"Sending simulate_page_request with payload: {payload}")
        response = requests.post(f"{API_BASE_URL}/simulate_page_request", json=payload, auth=AUTH)
        response.raise_for_status()
        print(f"Page request simulated: {response.json()}")
    except requests.RequestException as e:
        error_msg = str(e)
        if hasattr(e, 'response') and e.response is not None:
            error_msg += f" (Response: {e.response.text})"
        print(f"Error simulating page request: {error_msg}")
        raise Exception(f"Failed to simulate page request: {error_msg}")

def reset_memory():
    try:
        response = requests.post(f"{API_BASE_URL}/reset", auth=AUTH)
        response.raise_for_status()
        print(f"Reset response: {response.json()}")
    except requests.RequestException as e:
        print(f"Error resetting memory state: {e}")

def get_segmentation_memory_state():
    try:
        response = requests.get(f"{API_BASE_URL}/display_segmentation_memory", auth=AUTH)
        response.raise_for_status()
        state = response.json()
        total_memory = 32
        memory_used = sum(size for base, size, pid, sid in state["Memory State"])
        memory_used_percent = (memory_used * 100) // total_memory
        return {
            "memory_state": state["Memory State"],
            "segment_table": state["Segment Table"],
            "free_blocks": state["Free Blocks"],
            "allocation_failures": state["Allocation Failures"],
            "memory_used": memory_used_percent,
            "mode": "Segmentation",
            "algorithm": "First-Fit",
            "last_allocation": state.get("Last Allocation")
        }
    except requests.RequestException as e:
        print(f"Error fetching segmentation memory state: {e}")
        return {
            "memory_state": [],
            "segment_table": {},
            "free_blocks": [(0, 32)],
            "allocation_failures": 0,
            "memory_used": 0,
            "mode": "Segmentation",
            "algorithm": "First-Fit",
            "last_allocation": None
        }

def allocate_segment(process_id, segment_id, size):
    try:
        payload = {"process_id": str(process_id), "segment_id": str(segment_id), "size": size}  # Send as string
        print(f"Sending allocate_segmentation request with payload: {payload}")
        response = requests.post(f"{API_BASE_URL}/allocate_segmentation", json=payload, auth=AUTH)
        response.raise_for_status()
        print(f"Segment allocated: {response.json()}")
    except requests.RequestException as e:
        error_msg = str(e)
        if hasattr(e, 'response') and e.response is not None:
            error_msg += f" (Response: {e.response.text})"
        print(f"Error allocating segment: {error_msg}")
        raise Exception(f"Failed to allocate segment: {error_msg}")

def reset_segmentation_memory():
    try:
        response = requests.post(f"{API_BASE_URL}/reset_segmentation", auth=AUTH)
        response.raise_for_status()
        print(f"Segmentation reset response: {response.json()}")
    except requests.RequestException as e:
        print(f"Error resetting segmentation memory state: {e}")

def get_virtual_memory_state():
    try:
        response = requests.get(f"{API_BASE_URL}/display_virtual_memory", auth=AUTH)
        response.raise_for_status()
        state = response.json()
        return {
            "memory_frames": state["Memory Frames"],
            "page_table": state["Page Table"],
            "swap_space": state["Swap Space"],
            "page_faults": state["Total Page Faults"],
            "swap_operations": state["Swap Operations"],
            "memory_used": (sum(1 for f in state["Memory Frames"] if f is not None) * 100) // len(state["Memory Frames"]),
            "mode": "Virtual Memory",
            "algorithm": "FIFO",
            "last_page_fault": state.get("Last Page Fault")
        }
    except requests.RequestException as e:
        print(f"Error fetching virtual memory state: {e}")
        return {
            "memory_frames": [None] * 8,
            "page_table": {},
            "swap_space": [None] * 16,
            "page_faults": 0,
            "swap_operations": 0,
            "memory_used": 0,
            "mode": "Virtual Memory",
            "algorithm": "FIFO",
            "last_page_fault": None
        }

def allocate_virtual_pages(process_id, num_pages):
    try:
        payload = {"process_id": str(process_id), "num_pages": num_pages}  # Send as string
        print(f"Sending allocate_virtual request with payload: {payload}")
        response = requests.post(f"{API_BASE_URL}/allocate_virtual", json=payload, auth=AUTH)
        response.raise_for_status()
        print(f"Virtual pages allocated: {response.json()}")
    except requests.RequestException as e:
        error_msg = str(e)
        if hasattr(e, 'response') and e.response is not None:
            error_msg += f" (Response: {e.response.text})"
        print(f"Error allocating virtual pages: {error_msg}")
        raise Exception(f"Failed to allocate virtual pages: {error_msg}")

def simulate_virtual_page_request(process_id, page_num, max_page_num=None):
    try:
        # Send process_id and page_num as strings to match server expectations
        payload = {"process_id": str(process_id), "page_num": str(page_num)}
        print(f"Sending simulate_virtual_page_request with payload: {payload}")
        response = requests.post(f"{API_BASE_URL}/simulate_virtual_page_request", json=payload, auth=AUTH)
        response.raise_for_status()
        print(f"Virtual page request simulated: {response.json()}")
    except requests.RequestException as e:
        error_msg = str(e)
        if hasattr(e, 'response') and e.response is not None:
            error_msg += f" (Response: {e.response.text})"
            # Handle "not found" error by re-allocating pages
            if e.response.status_code == 404 and "not found in page table" in e.response.text.lower() and max_page_num is not None:
                print(f"Process {process_id} not found in page table. Reallocating pages...")
                allocate_virtual_pages(process_id, max_page_num + 1)
                # Retry the request
                response = requests.post(f"{API_BASE_URL}/simulate_virtual_page_request", json=payload, auth=AUTH)
                response.raise_for_status()
                print(f"Virtual page request simulated after reallocation: {response.json()}")
            else:
                raise Exception(f"Failed to simulate virtual page request: {error_msg}")
        else:
            raise Exception(f"Failed to simulate virtual page request: {error_msg}")

def reset_virtual_memory():
    try:
        response = requests.post(f"{API_BASE_URL}/reset_virtual", auth=AUTH)
        response.raise_for_status()
        print(f"Virtual memory reset response: {response.json()}")
    except requests.RequestException as e:
        print(f"Error resetting virtual memory state: {e}")

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
    memory_state = get_memory_state()
    segmentation_memory_state = get_segmentation_memory_state()
    virtual_memory_state = get_virtual_memory_state()
    flash_timer = 0
    scroll_offset = 0
    max_visible_entries = 5
    scroll_speed = 1
    max_page_num = None

    # UI Elements
    sequence_input = TextInput(20, 450, 300, 40, "Enter Sequence (e.g., 0,1,2):")
    start_button = Button(340, 450, 100, 40, "Start")
    step_button = Button(450, 450, 100, 40, "Step")
    reset_button = Button(560, 450, 100, 40, "Reset")
    paging_button = Button(20, 500, 120, 40, "Paging")
    seg_button = Button(150, 500, 120, 40, "Segmentation")
    vm_button = Button(280, 500, 120, 40, "Virtual Memory")
    fifo_button = Button(450, 500, 100, 40, "FIFO")
    lru_button = Button(560, 500, 100, 40, "LRU")
    up_button_rect = pygame.Rect(280, 250, 20, 20)
    down_button_rect = pygame.Rect(280, 370, 20, 20)

    def start_simulation():
        nonlocal sequence, input_active, step, status, max_page_num
        try:
            if not check_api_availability():
                raise Exception(f"API at {API_BASE_URL} is not responding. Start the server.")
            raw_input = sequence_input.get_text().strip().replace(" ", ",")
            if "," not in raw_input:
                raw_input = ",".join(list(raw_input))
            split_input = [x.strip() for x in raw_input.split(",") if x.strip()]
            if not split_input:
                raise ValueError("No valid input provided")
            if mode == "Paging" or mode == "Virtual Memory":
                sequence_numbers = [int(x) for x in split_input]
                sequence = [(1, num) for num in sequence_numbers]
                if mode == "Virtual Memory":
                    max_page_num = max(sequence_numbers)
                    allocate_virtual_pages(1, max_page_num + 1)
            else:  # Segmentation
                sequence = []
                for item in split_input:
                    seg_id, size = map(int, item.split(":"))
                    sequence.append((1, seg_id, size))
            input_active = False
            step = 0
            status = "Running"
            print(f"Simulation started with sequence: {sequence}")
        except ValueError as e:
            sequence_input.text = f"Invalid input: {e}. Use 0,1,2 or 0:4,1:8"
            input_active = True
        except Exception as e:
            sequence_input.text = f"Error: {e}"
            input_active = True

    def step_simulation():
        nonlocal step, status, input_active, memory_state, segmentation_memory_state, virtual_memory_state, flash_timer
        try:
            if not check_api_availability():
                sequence_input.text = f"API at {API_BASE_URL} is not responding. Start the server."
                status = "Error - API Down"
                return
            if not sequence or step >= len(sequence):
                sequence_input.text = "No sequence or simulation finished. Start a new one."
                status = "Ready"
                input_active = True
                return
            print(f"Stepping: {step}/{len(sequence)}, Data: {sequence[step]}")
            if mode == "Paging":
                process_id, page_num = sequence[step]
                allocate_page(process_id, page_num)
                simulate_page_request(process_id, page_num)
                memory_state = get_memory_state()
                if memory_state["last_page_fault"] is not None:
                    flash_timer = 30
            elif mode == "Segmentation":
                process_id, segment_id, size = sequence[step]
                allocate_segment(process_id, segment_id, size)
                segmentation_memory_state = get_segmentation_memory_state()
                if segmentation_memory_state["last_allocation"] is not None:
                    flash_timer = 30
            else:  # Virtual Memory
                process_id, page_num = sequence[step]
                simulate_virtual_page_request(process_id, page_num, max_page_num)
                virtual_memory_state = get_virtual_memory_state()
                if virtual_memory_state["last_page_fault"] is not None:
                    flash_timer = 30
            step += 1
            if step >= len(sequence):
                status = "Finished"
        except Exception as e:
            sequence_input.text = f"Step error: {e}. Check server logs."
            status = "Paused - Error"
            print(f"Step simulation failed: {e}")

    def reset_simulation():
        nonlocal step, sequence, input_active, status, memory_state, segmentation_memory_state, virtual_memory_state, flash_timer, scroll_offset, max_page_num
        if mode == "Paging":
            reset_memory()
        elif mode == "Segmentation":
            reset_segmentation_memory()
        else:
            reset_virtual_memory()
        step = 0
        sequence = []
        input_active = True
        status = "Ready"
        sequence_input.reset()
        memory_state = get_memory_state()
        segmentation_memory_state = get_segmentation_memory_state()
        virtual_memory_state = get_virtual_memory_state()
        flash_timer = 0
        scroll_offset = 0
        max_page_num = None
        print("Simulation reset")

    def switch_to_paging():
        nonlocal mode, algorithm
        mode = "Paging"
        algorithm = "FIFO"
        sequence_input.label = LABEL_FONT.render("Enter Sequence (e.g., 0,1,2):", True, TEXT_COLOR)
        reset_simulation()

    def switch_to_segmentation():
        nonlocal mode, algorithm
        mode = "Segmentation"
        algorithm = "First-Fit"
        sequence_input.label = LABEL_FONT.render("Enter Sequence (e.g., 0:4,1:8):", True, TEXT_COLOR)
        reset_simulation()

    def switch_to_virtual_memory():
        nonlocal mode, algorithm
        mode = "Virtual Memory"
        algorithm = "FIFO"
        sequence_input.label = LABEL_FONT.render("Enter Sequence (e.g., 0,1,2):", True, TEXT_COLOR)
        reset_simulation()

    # Assign actions
    start_button.action = start_simulation
    step_button.action = step_simulation
    reset_button.action = reset_simulation
    paging_button.action = switch_to_paging
    seg_button.action = switch_to_segmentation
    vm_button.action = switch_to_virtual_memory
    fifo_button.action = lambda: None  # Placeholder
    lru_button.action = lambda: None  # Placeholder

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
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and mode == "Virtual Memory":
                mouse_pos = event.pos
                if up_button_rect.collidepoint(mouse_pos) and scroll_offset > 0:
                    scroll_offset -= scroll_speed
                elif down_button_rect.collidepoint(mouse_pos):
                    total_entries = sum(len(pages) for pid, pages in virtual_memory_state["page_table"].items())
                    if scroll_offset < total_entries - max_visible_entries:
                        scroll_offset += scroll_speed

        if flash_timer > 0:
            flash_timer -= 1

        screen.fill(BG_COLOR)
        if mode == "Paging":
            draw_memory(screen, memory_state["frames"], frame_counter, memory_state["last_page_fault"], flash_timer)
            draw_table(screen, memory_state["page_table"], mode)
            draw_stats(screen, memory_state["page_faults"], memory_state["memory_used"], mode, algorithm, status)
        elif mode == "Segmentation":
            draw_segmentation_memory(screen, segmentation_memory_state["memory_state"], segmentation_memory_state["free_blocks"], frame_counter, segmentation_memory_state["last_allocation"], flash_timer)
            draw_table(screen, segmentation_memory_state["segment_table"], mode)
            draw_stats(screen, segmentation_memory_state["allocation_failures"], segmentation_memory_state["memory_used"], mode, algorithm, status)
        else:
            draw_virtual_memory(screen, virtual_memory_state["memory_frames"], virtual_memory_state["swap_space"], frame_counter, virtual_memory_state["last_page_fault"], flash_timer)
            scroll_offset = draw_table(screen, virtual_memory_state["page_table"], mode, scroll_offset, max_visible_entries, up_button_rect, down_button_rect)
            draw_stats(screen, virtual_memory_state["page_faults"], virtual_memory_state["memory_used"], mode, algorithm, status, virtual_memory_state["swap_operations"])

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