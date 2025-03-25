# server.py (or main.py)
from flask import Flask, request, jsonify
import collections
import random
from collections import namedtuple

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

# Define a Segment named tuple for clarity
Segment = namedtuple('Segment', ['process_id', 'segment_id', 'size', 'base_address'])

# Define the SegmentationMemorySimulator class
class SegmentationMemorySimulator:
    def __init__(self, total_memory=32):
        """
        Initialize the segmentation memory simulator.
        
        Args:
            total_memory (int): Total memory available in KB (default: 32 KB).
        """
        self.total_memory = total_memory  # Total memory in KB
        self.memory = []  # List of (base_address, size, process_id, segment_id) tuples for allocated segments
        self.free_blocks = [(0, total_memory)]  # List of (base_address, size) tuples for free blocks
        self.segment_table = {}  # Maps process_id to list of segments: {process_id: [Segment, ...]}
        self.allocation_failures = 0  # Track allocation failures (e.g., no space available)
        self.last_allocation = None  # Track the last allocated segment for visualization

    def allocate_segmentation(self, process_id, segment_id, size):
        """
        Allocate a segment for a process using a first-fit strategy.
        
        Args:
            process_id (int): ID of the process.
            segment_id (int): ID of the segment (e.g., 0 for code, 1 for data).
            size (int): Size of the segment in KB.
        
        Returns:
            bool: True if allocation succeeded, False otherwise.
        """
        # Check if the process has a segment table entry
        if process_id not in self.segment_table:
            self.segment_table[process_id] = []

        # Find a free block using first-fit
        for i, (base, free_size) in enumerate(self.free_blocks):
            if free_size >= size:
                # Allocate the segment
                segment = Segment(process_id, segment_id, size, base)
                self.memory.append((base, size, process_id, segment_id))
                self.segment_table[process_id].append(segment)
                self.last_allocation = (base, size, process_id, segment_id)

                # Update the free block
                new_base = base + size
                new_size = free_size - size
                self.free_blocks[i] = (new_base, new_size)

                # If the remaining size is 0, remove the free block
                if new_size == 0:
                    self.free_blocks.pop(i)

                # Sort memory by base address for clarity
                self.memory.sort(key=lambda x: x[0])
                return True

        # If no suitable block is found, increment allocation failures
        self.allocation_failures += 1
        return False

    def deallocate_segment(self, process_id, segment_id):
        """
        Deallocate a segment for a process and merge free blocks.
        
        Args:
            process_id (int): ID of the process.
            segment_id (int): ID of the segment to deallocate.
        """
        if process_id not in self.segment_table:
            return

        # Find the segment in the segment table
        for i, segment in enumerate(self.segment_table[process_id]):
            if segment.segment_id == segment_id:
                base, size = segment.base_address, segment.size
                # Remove from memory
                self.memory = [entry for entry in self.memory if not (entry[2] == process_id and entry[3] == segment_id)]
                # Remove from segment table
                self.segment_table[process_id].pop(i)
                # Add to free blocks
                self.free_blocks.append((base, size))
                break

        # If the process has no more segments, remove its entry
        if not self.segment_table[process_id]:
            del self.segment_table[process_id]

        # Sort free blocks by base address
        self.free_blocks.sort(key=lambda x: x[0])

        # Merge contiguous free blocks
        i = 0
        while i < len(self.free_blocks) - 1:
            base1, size1 = self.free_blocks[i]
            base2, size2 = self.free_blocks[i + 1]
            if base1 + size1 == base2:
                # Merge the blocks
                self.free_blocks[i] = (base1, size1 + size2)
                self.free_blocks.pop(i + 1)
            else:
                i += 1

    def display_memory(self):
        """
        Return the current memory state for visualization.
        
        Returns:
            dict: A dictionary containing memory state, segment table, free blocks, and statistics.
        """
        # Convert memory and segment table to JSON-serializable format
        memory_state = [(base, size, pid, sid) for base, size, pid, sid in self.memory]
        segment_table = {
            str(pid): [(seg.process_id, seg.segment_id, seg.size, seg.base_address) for seg in segments]
            for pid, segments in self.segment_table.items()
        }
        free_blocks = [(base, size) for base, size in self.free_blocks]
        last_allocation = list(self.last_allocation) if self.last_allocation else None

        return {
            "Memory State": memory_state,  # List of (base_address, size, process_id, segment_id)
            "Segment Table": segment_table,  # {process_id: [(pid, sid, size, base), ...]}
            "Free Blocks": free_blocks,  # List of (base_address, size)
            "Allocation Failures": self.allocation_failures,
            "Last Allocation": last_allocation
        }

    def reset(self):
        """
        Reset the memory state to initial conditions.
        """
        self.memory = []
        self.free_blocks = [(0, self.total_memory)]
        self.segment_table = {}
        self.allocation_failures = 0
        self.last_allocation = None

# Initialize the memory simulator (indented 0 spaces, outside the class)
simulator = MemoryManagementSimulator()

# Initialize the segmentation simulator
segmentation_simulator = SegmentationMemorySimulator()

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

# Flask routes for segmentation
@app.route('/configure_segmentation', methods=['POST'])
def configure_segmentation():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON input."}), 400

    total_memory = data.get('total_memory', 32)

    global segmentation_simulator
    segmentation_simulator = SegmentationMemorySimulator(total_memory)
    return jsonify({"message": "Segmentation configuration updated successfully."})

@app.route('/allocate_segmentation', methods=['POST'])
def allocate_segmentation():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON input."}), 400

    process_id = data.get('process_id')
    segment_id = data.get('segment_id')
    size = data.get('size')

    if process_id is None or segment_id is None or size is None:
        return jsonify({"error": "Missing process_id, segment_id, or size."}), 400
    
    success = segmentation_simulator.allocate_segmentation(process_id, segment_id, size)
    if success:
        return jsonify({"message": "Segment allocated successfully."})
    else:
        return jsonify({"error": "Failed to allocate segment: insufficient memory."}), 400

@app.route('/deallocate_segment', methods=['POST'])
def deallocate_segment():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON input."}), 400

    process_id = data.get('process_id')
    segment_id = data.get('segment_id')

    if process_id is None or segment_id is None:
        return jsonify({"error": "Missing process_id or segment_id."}), 400
    
    segmentation_simulator.deallocate_segment(process_id, segment_id)
    return jsonify({"message": "Segment deallocated successfully."})

@app.route('/display_segmentation_memory', methods=['GET'])
def display_segmentation_memory():
    memory_state = segmentation_simulator.display_memory()
    return jsonify(memory_state)

@app.route('/reset_segmentation', methods=['POST'])
def reset_segmentation():
    global segmentation_simulator
    segmentation_simulator = SegmentationMemorySimulator(segmentation_simulator.total_memory)
    return jsonify({"message": "Segmentation memory state reset successfully."})

# Main block to run the Flask app (indented 0 spaces)
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)