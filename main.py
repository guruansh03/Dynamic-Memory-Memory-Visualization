# server.py (or main.py)
from flask import Flask, request, jsonify
import collections
import random

# Create the Flask app
app = Flask(__name__)

# Define the MemoryManagementSimulator class
class MemoryManagementSimulator:
    # Constructor method (indented 4 spaces under the class)
    def __init__(self, total_memory=32, page_size=4):
        # All lines inside __init__ are indented 8 spaces (4 for class, 4 for method)
        self.total_memory = total_memory  # Total memory in KB
        self.page_size = page_size        # Page size in KB
        self.frames = total_memory // page_size  # Number of frames (32 ÷ 4 = 8)
        self.memory = [None] * self.frames  # Physical memory (frames)
        self.page_table = {}  # Maps process pages to frames (process_id -> list of (page_num, frame) tuples)
        self.disk = {}  # Simulated disk storage
        self.page_replacement_algorithm = "FIFO"
        self.page_queue = collections.deque()  # Track pages for FIFO
        self.page_access = {}  # For LRU (not implemented)
        self.page_faults = 0  # Track the number of page faults
        self.last_page_fault = None  # Track the last page fault for visualization

    # Method to allocate pages (indented 4 spaces under the class)
    def allocate_paging(self, process_id, num_pages):
        """Allocate pages to a process using paging."""
        # All lines inside this method are indented 8 spaces
        if process_id not in self.page_table:
            self.page_table[process_id] = []
        
        for page_num in range(num_pages):
            page = (process_id, page_num)
            # Add the page to the page table with frame -1 (not in memory yet)
            self.page_table[process_id].append((page_num, -1))
            
            if None in self.memory:
                frame = self.memory.index(None)
                self.memory[frame] = page
                self.page_queue.append(page)  # Add to FIFO queue
                # Update the page table with the frame number
                self.page_table[process_id][-1] = (page_num, frame)
            else:
                self.handle_page_fault(process_id, page)
                frame = self.memory.index(None)  # After page fault, a frame should be free
                self.memory[frame] = page
                self.page_queue.append(page)  # Add to FIFO queue
                # Update the page table with the frame number
                self.page_table[process_id][-1] = (page_num, frame)

    # Method to handle page faults (indented 4 spaces under the class)
    def handle_page_fault(self, process_id, page_to_load):
        """Handle page faults by replacing a page using FIFO or LRU."""
        # All lines inside this method are indented 8 spaces
        self.page_faults += 1  # Increment page fault count
        if not self.page_queue:
            return

        if self.page_replacement_algorithm == "FIFO":
            old_page = self.page_queue.popleft()  # Remove the oldest page
            # Find the frame containing the old page
            frame = None
            for i, page in enumerate(self.memory):
                if page == old_page:
                    frame = i
                    break
            if frame is not None:
                self.disk[old_page] = old_page  # Simulate writing to disk
                self.memory[frame] = None  # Free the frame
                self.last_page_fault = frame  # Track the frame for visualization
                # Update the page table: mark the old page as not in memory
                old_pid, old_page_num = old_page
                for i, (page_num, frame_num) in enumerate(self.page_table[old_pid]):
                    if frame_num == frame:
                        self.page_table[old_pid][i] = (page_num, -1)  # Mark as not in memory
                        break
        elif self.page_replacement_algorithm == "LRU":
            old_page = min(self.page_access, key=self.page_access.get)
            # LRU not implemented
            pass

    # Method to simulate a page request (indented 4 spaces under the class)
    def simulate_page_request(self, process_id, page_num):
        """Simulate a process requesting a page."""
        # All lines inside this method are indented 8 spaces
        page = (process_id, page_num)
        # Check if the page is in memory
        in_memory = False
        frame = None
        for i, mem_page in enumerate(self.memory):
            if mem_page == page:
                in_memory = True
                frame = i
                break
        
        if not in_memory:
            print(f"Page fault! Process {process_id} requested page {page_num}.")
            self.handle_page_fault(process_id, page)
            # After handling the page fault, load the requested page
            if None in self.memory:
                frame = self.memory.index(None)
                self.memory[frame] = page
                self.page_queue.append(page)
                # Update the page table
                if process_id not in self.page_table:
                    self.page_table[process_id] = []
                # Find the page in the page table and update its frame
                found = False
                for i, (p_num, f_num) in enumerate(self.page_table[process_id]):
                    if p_num == page_num:
                        self.page_table[process_id][i] = (page_num, frame)
                        found = True
                        break
                if not found:
                    self.page_table[process_id].append((page_num, frame))
        
        self.page_access[page] = random.randint(1, 100)  # Simulate usage

    # Method to display memory state (indented 4 spaces under the class)
    def display_memory(self):
        """Return the current memory state and statistics."""
        # All lines inside this method are indented 8 spaces
        # Convert tuples to lists for JSON serialization
        memory_frames = [list(frame) if frame is not None else None for frame in self.memory]
        disk_storage = {str(k): list(v) for k, v in self.disk.items()}  # Convert keys and values
        # Convert page table to a JSON-serializable format
        page_table = {str(k): [(p_num, f_num) for p_num, f_num in v] for k, v in self.page_table.items()}
        return {
            "Memory Frames": memory_frames,
            "Page Table": page_table,
            "Disk Storage": disk_storage,
            "Total Page Faults": self.page_faults,
            "Last Page Fault": self.last_page_fault
        }

# Initialize the memory simulator (indented 0 spaces, outside the class)
simulator = MemoryManagementSimulator()

# Flask routes (indented 0 spaces, outside the class)
@app.route('/configure', methods=['POST'])
def configure():
    # All lines inside this function are indented 4 spaces
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON input."}), 400

    total_memory = data.get('total_memory', 32)
    page_size = data.get('page_size', 4)

    global simulator
    simulator = MemoryManagementSimulator(total_memory, page_size)
    return jsonify({"message": "Configuration updated successfully."})

@app.route('/allocate_paging', methods=['POST'])
def allocate_paging():
    # All lines inside this function are indented 4 spaces
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON input."}), 400

    process_id = data.get('process_id')
    num_pages = data.get('num_pages')

    if process_id is None or num_pages is None:
        return jsonify({"error": "Missing process_id or num_pages."}), 400
    
    simulator.allocate_paging(process_id, num_pages)
    return jsonify({"message": "Pages allocated successfully."})

@app.route('/simulate_page_request', methods=['POST'])
def simulate_page_request():
    # All lines inside this function are indented 4 spaces
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON input."}), 400

    process_id = data.get('process_id')
    page_num = data.get('page_num')

    if process_id is None or page_num is None:
        return jsonify({"error": "Missing process_id or page_num."}), 400
    
    simulator.simulate_page_request(process_id, page_num)
    return jsonify({"message": "Page request simulated."})

@app.route('/display_memory', methods=['GET'])
def display_memory():
    # All lines inside this function are indented 4 spaces
    memory_state = simulator.display_memory()
    return jsonify(memory_state)

@app.route('/reset', methods=['POST'])
def reset():
    # All lines inside this function are indented 4 spaces
    global simulator
    simulator = MemoryManagementSimulator(simulator.total_memory, simulator.page_size)
    return jsonify({"message": "Memory state reset successfully."})

# Main block to run the Flask app (indented 0 spaces)
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)