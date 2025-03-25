from flask import Flask, request, jsonify
import collections
import random

app = Flask(__name__)

class MemoryManagementSimulator:
    def __init__(self, total_memory=4, page_size=1):
        self.total_memory = total_memory  # Total memory in KB
        self.page_size = page_size        # Page size in KB
        self.frames = total_memory // page_size  # Number of frames
        self.memory = [None] * self.frames  # Physical memory (frames)
        self.page_table = {}  # Maps process pages to frames
        self.disk = {}  # Simulated disk storage
        self.page_replacement_algorithm = "FIFO"
        self.page_queue = collections.deque()
        self.page_access = {}
        self.page_faults = 0  # Track the number of page faults

    def allocate_paging(self, process_id, num_pages):
        """Allocate pages to a process using paging."""
        allocated = []
        for _ in range(num_pages):
            if None in self.memory:
                frame = self.memory.index(None)
                self.memory[frame] = (process_id, len(self.page_table.get(process_id, [])))
                allocated.append(frame)
            else:
                self.handle_page_fault(process_id)
                allocated.append(self.page_table[process_id][-1])
        self.page_table[process_id] = self.page_table.get(process_id, []) + allocated

    def allocate_segmentation(self, process_id, segment_size):
        """Allocate memory for a process using segmentation."""
        base_address = sum(seg[1] for seg in self.page_table.values()) if self.page_table else 0
        self.page_table[process_id] = (base_address, segment_size)
        return base_address

    def handle_page_fault(self, process_id):
        """Handle page faults by replacing a page using FIFO or LRU."""
        self.page_faults += 1  # Increment page fault count
        if self.page_replacement_algorithm == "FIFO":
            old_page = self.page_queue.popleft()
        elif self.page_replacement_algorithm == "LRU":
            old_page = min(self.page_access, key=self.page_access.get)
        else:
            return
        
        frame = self.memory.index(old_page)
        self.disk[old_page] = old_page  # Simulate writing to disk
        self.memory[frame] = (process_id, len(self.page_table.get(process_id, [])))
        self.page_queue.append((process_id, len(self.page_table.get(process_id, []))))
        self.page_table[process_id] = self.page_table.get(process_id, []) + [frame]

    def simulate_page_request(self, process_id, page_num):
        """Simulate a process requesting a page."""
        if (process_id, page_num) not in self.memory:
            print(f"Page fault! Process {process_id} requested page {page_num}.")
            self.handle_page_fault(process_id)
        self.page_access[(process_id, page_num)] = random.randint(1, 100)  # Simulate usage

    def display_memory(self):
        """Return the current memory state and statistics."""
        return {
            "Memory Frames": self.memory,
            "Page Table": self.page_table,
            "Disk Storage": self.disk,
            "Total Page Faults": self.page_faults
        }

simulator = MemoryManagementSimulator()

@app.route('/configure', methods=['POST'])
def configure():
    data = request.json
    total_memory = data.get('total_memory', 4)
    page_size = data.get('page_size', 1)
    global simulator
    simulator = MemoryManagementSimulator(total_memory, page_size)
    return jsonify({"message": "Configuration updated successfully."})

@app.route('/allocate_paging', methods=['POST'])
def allocate_paging():
    data = request.json
    process_id = data.get('process_id')
    num_pages = data.get('num_pages')
    
    if not process_id or num_pages is None:
        return jsonify({"error": "Missing process_id or num_pages."}), 400
    
    simulator.allocate_paging(process_id, num_pages)
    return jsonify({"message": "Pages allocated successfully."})

@app.route('/simulate_page_request', methods=['POST'])
def simulate_page_request():
    data = request.json
    process_id = data.get('process_id')
    page_num = data.get('page_num')
    
    if not process_id or page_num is None:
        return jsonify({"error": "Missing process_id or page_num."}), 400
    
    simulator.simulate_page_request(process_id, page_num)
    return jsonify({"message": "Page request simulated."})

@app.route('/display_memory', methods=['GET'])
def display_memory():
    memory_state = simulator.display_memory()
    return jsonify(memory_state)

if __name__ == '__main__':
    app.run(debug=True)
