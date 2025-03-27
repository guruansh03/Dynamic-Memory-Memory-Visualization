from flask import Flask, request, jsonify
import collections
from collections import namedtuple
import random
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create the Flask app
app = Flask(__name__)

# Define the MemoryManagementSimulator class
class MemoryManagementSimulator:
    def __init__(self, total_memory=32, page_size=4):
        self.total_memory = total_memory
        self.page_size = page_size
        self.frames = total_memory // page_size
        self.memory = [None] * self.frames
        self.page_table = {}
        self.disk = {}
        self.page_replacement_algorithm = "FIFO"
        self.page_queue = collections.deque()
        self.page_access = {}
        self.page_faults = 0
        self.last_page_fault = None

    def allocate_paging(self, process_id, num_pages):
        process_id = str(process_id)  # Store as string
        if process_id not in self.page_table:
            self.page_table[process_id] = []
        
        for page_num in range(num_pages):
            page = (process_id, page_num)
            self.page_table[process_id].append((page_num, -1))
            
            if None in self.memory:
                frame = self.memory.index(None)
                self.memory[frame] = page
                self.page_queue.append(page)
                self.page_table[process_id][-1] = (page_num, frame)
            else:
                self.handle_page_fault(process_id, page)
                frame = self.memory.index(None)
                self.memory[frame] = page
                self.page_queue.append(page)
                self.page_table[process_id][-1] = (page_num, frame)

    def handle_page_fault(self, process_id, page_to_load):
        self.page_faults += 1
        if not self.page_queue:
            return

        if self.page_replacement_algorithm == "FIFO":
            old_page = self.page_queue.popleft()
            frame = None
            for i, page in enumerate(self.memory):
                if page == old_page:
                    frame = i
                    break
            if frame is not None:
                self.disk[old_page] = old_page
                self.memory[frame] = None
                self.last_page_fault = frame
                old_pid, old_page_num = old_page
                for i, (page_num, frame_num) in enumerate(self.page_table[old_pid]):
                    if frame_num == frame:
                        self.page_table[old_pid][i] = (page_num, -1)
                        break
        elif self.page_replacement_algorithm == "LRU":
            old_page = min(self.page_access, key=self.page_access.get)
            pass

    def simulate_page_request(self, process_id, page_num):
        process_id = str(process_id)  # Ensure consistency
        page = (process_id, page_num)
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
            if None in self.memory:
                frame = self.memory.index(None)
                self.memory[frame] = page
                self.page_queue.append(page)
                if process_id not in self.page_table:
                    self.page_table[process_id] = []
                found = False
                for i, (p_num, f_num) in enumerate(self.page_table[process_id]):
                    if p_num == page_num:
                        self.page_table[process_id][i] = (page_num, frame)
                        found = True
                        break
                if not found:
                    self.page_table[process_id].append((page_num, frame))

    def display_memory(self):
        memory_frames = [list(frame) if frame is not None else None for frame in self.memory]
        disk_storage = {str(k): list(v) for k, v in self.disk.items()}
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
        self.total_memory = total_memory
        self.memory = []
        self.free_blocks = [(0, total_memory)]
        self.segment_table = {}
        self.allocation_failures = 0
        self.last_allocation = None

    def allocate_segmentation(self, process_id, segment_id, size):
        process_id = str(process_id)  # Store as string
        if process_id not in self.segment_table:
            self.segment_table[process_id] = []

        for i, (base, free_size) in enumerate(self.free_blocks):
            if free_size >= size:
                segment = Segment(process_id, segment_id, size, base)
                self.memory.append((base, size, process_id, segment_id))
                self.segment_table[process_id].append(segment)
                self.last_allocation = (base, size, process_id, segment_id)
                new_base = base + size
                new_size = free_size - size
                self.free_blocks[i] = (new_base, new_size)
                if new_size == 0:
                    self.free_blocks.pop(i)
                self.memory.sort(key=lambda x: x[0])
                return True

        self.allocation_failures += 1
        return False

    def deallocate_segment(self, process_id, segment_id):
        process_id = str(process_id)  # Ensure consistency
        if process_id not in self.segment_table:
            return

        for i, segment in enumerate(self.segment_table[process_id]):
            if segment.segment_id == segment_id:
                base, size = segment.base_address, segment.size
                self.memory = [entry for entry in self.memory if not (entry[2] == process_id and entry[3] == segment_id)]
                self.segment_table[process_id].pop(i)
                self.free_blocks.append((base, size))
                break

        if not self.segment_table[process_id]:
            del self.segment_table[process_id]

        self.free_blocks.sort(key=lambda x: x[0])
        i = 0
        while i < len(self.free_blocks) - 1:
            base1, size1 = self.free_blocks[i]
            base2, size2 = self.free_blocks[i + 1]
            if base1 + size1 == base2:
                self.free_blocks[i] = (base1, size1 + size2)
                self.free_blocks.pop(i + 1)
            else:
                i += 1

    def display_memory(self):
        memory_state = [(base, size, pid, sid) for base, size, pid, sid in self.memory]
        segment_table = {
            str(pid): [(seg.process_id, seg.segment_id, seg.size, seg.base_address) for seg in segments]
            for pid, segments in self.segment_table.items()
        }
        free_blocks = [(base, size) for base, size in self.free_blocks]
        last_allocation = list(self.last_allocation) if self.last_allocation else None
        return {
            "Memory State": memory_state,
            "Segment Table": segment_table,
            "Free Blocks": free_blocks,
            "Allocation Failures": self.allocation_failures,
            "Last Allocation": last_allocation
        }

    def reset(self):
        self.memory = []
        self.free_blocks = [(0, self.total_memory)]
        self.segment_table = {}
        self.allocation_failures = 0
        self.last_allocation = None

# Define the VirtualMemorySimulator class
class VirtualMemorySimulator:
    def __init__(self, total_memory=32, page_size=4, swap_size=64):
        self.total_memory = total_memory
        self.page_size = page_size
        self.frames = total_memory // page_size
        self.memory = [None] * self.frames
        self.swap_size = swap_size
        self.swap_frames = swap_size // page_size
        self.swap = [None] * self.swap_frames
        self.page_table = {}
        self.page_replacement_algorithm = "FIFO"
        self.page_queue = collections.deque()
        self.page_faults = 0
        self.swap_operations = 0
        self.last_page_fault = None
        logger.info(f"Initialized VirtualMemorySimulator with page_table: {self.page_table}")

    def allocate_virtual(self, process_id, num_pages):
        process_id = str(process_id)  # Store as string
        if process_id not in self.page_table:
            self.page_table[process_id] = []

        for page_num in range(num_pages):
            swap_frame = self.find_free_swap_frame()
            if swap_frame is None:
                raise ValueError("No free swap space available for page allocation")
            self.page_table[process_id].append((page_num, swap_frame, False))
            self.swap[swap_frame] = (process_id, page_num)
        logger.info(f"After allocate_virtual for process {process_id}, page_table: {self.page_table}")

    def handle_page_fault_with_swap(self, process_id, page_num):
        process_id = str(process_id)  # Ensure consistency
        self.page_faults += 1
        page = (process_id, page_num)

        swap_frame = None
        for i, (p_num, f_num, in_mem) in enumerate(self.page_table.get(process_id, [])):
            if p_num == page_num and not in_mem:
                swap_frame = f_num
                break

        if swap_frame is None:
            raise ValueError(f"Page {page_num} for process {process_id} not found in swap space")

        free_frame = None
        for i in range(len(self.memory)):
            if self.memory[i] is None:
                free_frame = i
                break

        if free_frame is not None:
            self.load_page_into_memory(page, free_frame, swap_frame)
        else:
            if not self.page_queue:
                raise ValueError("No pages in memory to evict")

            old_frame = self.page_queue.popleft()
            old_page = self.memory[old_frame]
            if old_page is None:
                raise ValueError("Invalid page in FIFO queue")

            old_pid, old_pnum = old_page

            new_swap_frame = self.find_free_swap_frame()
            if new_swap_frame is None:
                raise ValueError("No free swap space available for eviction")

            self.swap[new_swap_frame] = old_page
            self.swap_operations += 1

            for i, (p_num, f_num, in_mem) in enumerate(self.page_table[old_pid]):
                if p_num == old_pnum and in_mem and f_num == old_frame:
                    self.page_table[old_pid][i] = (p_num, new_swap_frame, False)
                    break

            self.load_page_into_memory(page, old_frame, swap_frame)
            self.last_page_fault = old_frame

    def load_page_into_memory(self, page, frame, swap_frame):
        process_id, page_num = page
        self.memory[frame] = page
        self.page_queue.append(frame)

        for i, (p_num, f_num, in_mem) in enumerate(self.page_table[process_id]):
            if p_num == page_num:
                self.page_table[process_id][i] = (p_num, frame, True)
                break

        self.swap[swap_frame] = None

    def find_free_swap_frame(self):
        for i in range(self.swap_frames):
            if self.swap[i] is None:
                return i
        return None

    def simulate_page_request(self, process_id, page_num):
        process_id = str(process_id)  # Ensure consistency
        logger.info(f"Before simulate_page_request, page_table: {self.page_table}")
        if process_id not in self.page_table:
            raise ValueError(f"Process {process_id} not found in page table")
        
        page = (process_id, page_num)
        in_memory = False
        frame = None

        page_exists = False
        for p_num, f_num, in_mem in self.page_table[process_id]:
            if p_num == page_num:
                page_exists = True
                if in_mem:
                    in_memory = True
                    frame = f_num
                break

        if not page_exists:
            raise ValueError(f"Page {page_num} for process {process_id} does not exist in page table")

        if not in_memory:
            print(f"Page fault in virtual memory! Process {process_id} requested page {page_num}.")
            self.handle_page_fault_with_swap(process_id, page_num)
        else:
            if frame in self.page_queue:
                self.page_queue.remove(frame)
                self.page_queue.append(frame)
        logger.info(f"After simulate_page_request, page_table: {self.page_table}")

    def display_memory(self):
        memory_frames = [list(frame) if frame is not None else None for frame in self.memory]
        swap_space = [list(frame) if frame is not None else None for frame in self.swap]
        page_table = {
            str(pid): [(p_num, f_num, in_mem) for p_num, f_num, in_mem in pages]
            for pid, pages in self.page_table.items()
        }
        return {
            "Memory Frames": memory_frames,
            "Page Table": page_table,
            "Swap Space": swap_space,
            "Total Page Faults": self.page_faults,
            "Swap Operations": self.swap_operations,
            "Last Page Fault": self.last_page_fault
        }

    def reset(self):
        self.memory = [None] * self.frames
        self.swap = [None] * self.swap_frames
        self.page_table = {}
        self.page_queue = collections.deque()
        self.page_faults = 0
        self.swap_operations = 0
        self.last_page_fault = None
        logger.info(f"Reset VirtualMemorySimulator, page_table: {self.page_table}")

# Initialize the simulators
simulator = MemoryManagementSimulator()
segmentation_simulator = SegmentationMemorySimulator()
virtual_simulator = VirtualMemorySimulator()

# Flask routes for Paging
@app.route('/configure', methods=['POST'])
def configure():
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
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON input."}), 400

    process_id = data.get('process_id')
    page_num = data.get('page_num')

    if process_id is None or page_num is None:
        return jsonify({"error": "Missing process_id or page_num."}), 400
    
    try:
        simulator.simulate_page_request(process_id, page_num)
        return jsonify({"message": "Page request simulated."})
    except Exception as e:
        logger.error(f"Error in simulate_page_request: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route('/display_memory', methods=['GET'])
def display_memory():
    memory_state = simulator.display_memory()
    return jsonify(memory_state)

@app.route('/reset', methods=['POST'])
def reset():
    global simulator
    simulator = MemoryManagementSimulator(simulator.total_memory, simulator.page_size)
    return jsonify({"message": "Memory state reset successfully."})

# Flask routes for Segmentation
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

# Flask routes for Virtual Memory
@app.route('/configure_virtual', methods=['POST'])
def configure_virtual():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON input."}), 400

    total_memory = data.get('total_memory', 32)
    page_size = data.get('page_size', 4)
    swap_size = data.get('swap_size', 64)

    global virtual_simulator
    virtual_simulator = VirtualMemorySimulator(total_memory, page_size, swap_size)
    return jsonify({"message": "Virtual memory configuration updated successfully."})

@app.route('/allocate_virtual', methods=['POST'])
def allocate_virtual():
    data = request.get_json()
    if not data:
        logger.error("Invalid JSON input received in allocate_virtual")
        return jsonify({"error": "Invalid JSON input."}), 400

    process_id = data.get('process_id')
    num_pages = data.get('num_pages')

    logger.info(f"Received request to allocate virtual pages: process_id={process_id}, num_pages={num_pages}")

    if process_id is None or num_pages is None:
        logger.error("Missing process_id or num_pages in request")
        return jsonify({"error": "Missing process_id or num_pages."}), 400
    
    try:
        process_id = str(process_id)  # Store as string
        num_pages = int(num_pages)
        virtual_simulator.allocate_virtual(process_id, num_pages)
        logger.info(f"Successfully allocated {num_pages} virtual pages for process {process_id}")
        return jsonify({"message": "Virtual pages allocated successfully."})
    except ValueError as e:
        logger.error(f"ValueError in allocate_virtual: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 400

@app.route('/simulate_virtual_page_request', methods=['POST'])
def simulate_virtual_page_request():
    data = request.get_json()
    if not data:
        logger.error("Invalid JSON input received in simulate_virtual_page_request")
        return jsonify({"error": "Invalid JSON input."}), 400

    process_id = data.get('process_id')
    page_num = data.get('page_num')

    logger.info(f"Received request to simulate page request: process_id={process_id}, page_num={page_num}")

    if process_id is None or page_num is None:
        logger.error("Missing process_id or page_num in request")
        return jsonify({"error": "Missing process_id or page_num."}), 400
    
    try:
        process_id = str(process_id)  # Ensure consistency
        page_num = int(page_num)
        virtual_simulator.simulate_page_request(process_id, page_num)
        logger.info(f"Successfully simulated page request for process {process_id}, page {page_num}")
        return jsonify({"message": "Virtual page request simulated."})
    except ValueError as e:
        logger.error(f"ValueError in simulate_virtual_page_request: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 404  # Use 404 for "not found" errors
    except Exception as e:
        logger.error(f"Unexpected error in simulate_virtual_page_request: {str(e)}", exc_info=True)
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

@app.route('/display_virtual_memory', methods=['GET'])
def display_virtual_memory():
    memory_state = virtual_simulator.display_memory()
    return jsonify(memory_state)

@app.route('/reset_virtual', methods=['POST'])
def reset_virtual():
    global virtual_simulator
    virtual_simulator = VirtualMemorySimulator(virtual_simulator.total_memory, virtual_simulator.page_size, virtual_simulator.swap_size)
    logger.info("Virtual memory state reset via /reset_virtual")
    return jsonify({"message": "Virtual memory state reset successfully."})

# Main block to run the Flask app
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)  