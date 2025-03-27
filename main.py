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

# Define the MemoryManagementSimulator class (Paging Mode)
class MemoryManagementSimulator:
    def __init__(self, total_memory=32, page_size=4):
        self.total_memory = total_memory
        self.page_size = page_size
        self.frames = total_memory // page_size
        self.memory = [None] * self.frames
        self.page_table = {}
        self.disk = {}
        self.page_replacement_algorithm = "FIFO"  # Default algorithm
        self.page_queue = collections.deque()  # For FIFO
        self.page_access = {}  # For LRU: tracks the last access time of each frame
        self.page_faults = 0
        self.last_page_fault = None
        self.access_counter = 0  # To track the order of accesses for LRU

    def set_algorithm(self, algorithm):
        if algorithm not in ["FIFO", "LRU"]:
            raise ValueError("Algorithm must be 'FIFO' or 'LRU'")
        self.page_replacement_algorithm = algorithm
        # Reset the page queue and access tracking when changing algorithms
        self.page_queue = collections.deque()
        self.page_access = {}
        self.access_counter = 0

    def allocate_paging(self, process_id, page_num):
        process_id = str(process_id)
        if process_id not in self.page_table:
            self.page_table[process_id] = []
        
        # Check if the page is already allocated
        for p_num, frame in self.page_table[process_id]:
            if p_num == page_num:
                return  # Page already allocated, no action needed
        
        # Add the page to the page table, initially on disk
        self.page_table[process_id].append((page_num, -1))
        
        # Try to place the page in memory if there's a free frame
        if None in self.memory:
            frame = self.memory.index(None)
            self.memory[frame] = (process_id, page_num)
            if self.page_replacement_algorithm == "FIFO":
                self.page_queue.append((process_id, page_num))
            elif self.page_replacement_algorithm == "LRU":
                self.access_counter += 1
                self.page_access[frame] = self.access_counter
            # Update the page table to reflect the frame
            self.page_table[process_id][-1] = (page_num, frame)

    def handle_page_fault(self, process_id, page_to_load):
        self.page_faults += 1
        frame = None
        old_page = None

        if self.page_replacement_algorithm == "FIFO":
            if not self.page_queue:
                for i, page in enumerate(self.memory):
                    if page is not None:
                        frame = i
                        old_page = page
                        break
                if frame is None:
                    raise ValueError("No pages in memory to evict")
            else:
                old_page = self.page_queue.popleft()
                for i, page in enumerate(self.memory):
                    if page == old_page:
                        frame = i
                        break
                if frame is None:
                    raise ValueError(f"Page {old_page} not found in memory")
        elif self.page_replacement_algorithm == "LRU":
            if not self.page_access:
                for i, page in enumerate(self.memory):
                    if page is not None:
                        frame = i
                        old_page = page
                        break
                if frame is None:
                    raise ValueError("No pages in memory to evict")
            else:
                # Find the frame with the oldest access time
                frame = min(self.page_access, key=self.page_access.get)
                old_page = self.memory[frame]
                del self.page_access[frame]

        # Evict the page
        self.disk[old_page] = old_page
        self.memory[frame] = None
        self.last_page_fault = frame
        old_pid, old_page_num = old_page
        for i, (page_num, frame_num) in enumerate(self.page_table[old_pid]):
            if frame_num == frame:
                self.page_table[old_pid][i] = (page_num, -1)
                break

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
                if self.page_replacement_algorithm == "FIFO":
                    self.page_queue.append(page)
                elif self.page_replacement_algorithm == "LRU":
                    self.access_counter += 1
                    self.page_access[frame] = self.access_counter
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
        else:
            if self.page_replacement_algorithm == "LRU":
                # Update the access time for the frame
                self.access_counter += 1
                self.page_access[frame] = self.access_counter

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

    def reset(self):
        self.memory = [None] * self.frames
        self.page_table = {}
        self.disk = {}
        self.page_queue = collections.deque()
        self.page_access = {}
        self.access_counter = 0
        self.page_faults = 0
        self.last_page_fault = None

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
        self.page_replacement_algorithm = "FIFO"  # Default algorithm
        self.segment_queue = collections.deque()  # For FIFO
        self.segment_access = {}  # For LRU: tracks the last access time of each segment
        self.access_counter = 0  # To track the order of accesses for LRU

    def set_algorithm(self, algorithm):
        if algorithm not in ["FIFO", "LRU"]:
            raise ValueError("Algorithm must be 'FIFO' or 'LRU'")
        self.page_replacement_algorithm = algorithm
        self.segment_queue = collections.deque()
        self.segment_access = {}
        self.access_counter = 0

    def allocate_segmentation(self, process_id, segment_id, size):
        process_id = str(process_id)  # Store as string
        if process_id not in self.segment_table:
            self.segment_table[process_id] = []

        # Check if we need to evict a segment to make space
        total_free_space = sum(size for _, size in self.free_blocks)
        if total_free_space < size:
            # Need to evict segments until we have enough space
            while total_free_space < size and (self.segment_queue or self.segment_access):
                if self.page_replacement_algorithm == "FIFO":
                    if not self.segment_queue:
                        return False
                    process_id_to_evict, segment_id_to_evict = self.segment_queue.popleft()
                elif self.page_replacement_algorithm == "LRU":
                    if not self.segment_access:
                        return False
                    # Find the least recently used segment
                    segment_key = min(self.segment_access, key=self.segment_access.get)
                    del self.segment_access[segment_key]
                    process_id_to_evict, segment_id_to_evict = segment_key

                # Deallocate the segment to free up space
                self.deallocate_segment(process_id_to_evict, segment_id_to_evict)
                total_free_space = sum(size for _, size in self.free_blocks)

        for i, (base, free_size) in enumerate(self.free_blocks):
            if free_size >= size:
                segment = Segment(process_id, segment_id, size, base)
                self.memory.append((base, size, process_id, segment_id))
                self.segment_table[process_id].append(segment)
                self.last_allocation = (base, size, process_id, segment_id)
                if self.page_replacement_algorithm == "FIFO":
                    self.segment_queue.append((process_id, segment_id))
                elif self.page_replacement_algorithm == "LRU":
                    self.access_counter += 1
                    self.segment_access[(process_id, segment_id)] = self.access_counter
                new_base = base + size
                new_size = free_size - size
                self.free_blocks[i] = (new_base, new_size)
                if new_size == 0:
                    self.free_blocks.pop(i)
                self.memory.sort(key=lambda x: x[0])
                return True

        self.allocation_failures += 1
        return False

    def access_segment(self, process_id, segment_id):
        process_id = str(process_id)
        if self.page_replacement_algorithm == "LRU":
            segment_key = (process_id, segment_id)
            if segment_key in self.segment_access:
                self.access_counter += 1
                self.segment_access[segment_key] = self.access_counter

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
                # Remove from FIFO queue or LRU access tracking
                if self.page_replacement_algorithm == "FIFO":
                    if (process_id, segment_id) in self.segment_queue:
                        self.segment_queue.remove((process_id, segment_id))
                elif self.page_replacement_algorithm == "LRU":
                    if (process_id, segment_id) in self.segment_access:
                        del self.segment_access[(process_id, segment_id)]
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
        self.segment_queue = collections.deque()
        self.segment_access = {}
        self.access_counter = 0

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
        self.page_replacement_algorithm = "FIFO"  # Default algorithm
        self.page_queue = collections.deque()  # For FIFO
        self.page_access = {}  # For LRU: tracks the last access time of each frame
        self.page_faults = 0
        self.swap_operations = 0
        self.last_page_fault = None
        self.access_counter = 0  # To track the order of accesses for LRU
        logger.info(f"Initialized VirtualMemorySimulator with page_table: {self.page_table}")

    def set_algorithm(self, algorithm):
        if algorithm not in ["FIFO", "LRU"]:
            raise ValueError("Algorithm must be 'FIFO' or 'LRU'")
        self.page_replacement_algorithm = algorithm
        self.page_queue = collections.deque()
        self.page_access = {}
        self.access_counter = 0

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

    def find_free_swap_frame(self):
        for i in range(len(self.swap)):
            if self.swap[i] is None:
                return i
        return None

    def load_page_into_memory(self, page, frame, swap_frame):
        self.memory[frame] = page
        self.swap[swap_frame] = None
        process_id, page_num = page
        for i, (p_num, f_num, in_mem) in enumerate(self.page_table[process_id]):
            if p_num == page_num:
                self.page_table[process_id][i] = (page_num, frame, True)
                break
        if self.page_replacement_algorithm == "FIFO":
            self.page_queue.append(frame)
        elif self.page_replacement_algorithm == "LRU":
            self.access_counter += 1
            self.page_access[frame] = self.access_counter

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
            self.last_page_fault = free_frame
        else:
            if self.page_replacement_algorithm == "FIFO":
                if not self.page_queue:
                    for i, page in enumerate(self.memory):
                        if page is not None:
                            free_frame = i
                            old_page = page
                            break
                    if free_frame is None:
                        raise ValueError("No pages in memory to evict")
                else:
                    free_frame = self.page_queue.popleft()
                    old_page = self.memory[free_frame]
            elif self.page_replacement_algorithm == "LRU":
                if not self.page_access:
                    for i, page in enumerate(self.memory):
                        if page is not None:
                            free_frame = i
                            old_page = page
                            break
                    if free_frame is None:
                        raise ValueError("No pages in memory to evict")
                else:
                    free_frame = min(self.page_access, key=self.page_access.get)
                    old_page = self.memory[free_frame]
                    del self.page_access[free_frame]

            # Swap out the old page
            old_swap_frame = self.find_free_swap_frame()
            if old_swap_frame is None:
                raise ValueError("No free swap space available for swapping out")
            self.swap[old_swap_frame] = old_page
            old_pid, old_page_num = old_page
            for i, (p_num, f_num, in_mem) in enumerate(self.page_table[old_pid]):
                if p_num == old_page_num and in_mem:
                    self.page_table[old_pid][i] = (p_num, old_swap_frame, False)
                    break
            self.swap_operations += 1
            self.memory[free_frame] = None
            self.load_page_into_memory(page, free_frame, swap_frame)
            self.last_page_fault = free_frame

    def simulate_virtual_page_request(self, process_id, page_num):
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
            self.handle_page_fault_with_swap(process_id, page_num)
        else:
            if self.page_replacement_algorithm == "LRU":
                self.access_counter += 1
                self.page_access[frame] = self.access_counter

    def display_memory(self):
        memory_frames = [list(frame) if frame is not None else None for frame in self.memory]
        swap_space = [list(frame) if frame is not None else None for frame in self.swap]
        page_table = {
            str(pid): [(p_num, f_num, in_mem) for p_num, f_num, in_mem in pages]
            for pid, pages in self.page_table.items()
        }
        return {
            "Memory Frames": memory_frames,
            "Swap Space": swap_space,
            "Page Table": page_table,
            "Total Page Faults": self.page_faults,
            "Swap Operations": self.swap_operations,
            "Last Page Fault": self.last_page_fault
        }

    def reset(self):
        self.memory = [None] * self.frames
        self.swap = [None] * self.swap_frames
        self.page_table = {}
        self.page_queue = collections.deque()
        self.page_access = {}
        self.access_counter = 0
        self.page_faults = 0
        self.swap_operations = 0
        self.last_page_fault = None

# Initialize the simulators
simulator = MemoryManagementSimulator()
segmentation_simulator = SegmentationMemorySimulator()
virtual_simulator = VirtualMemorySimulator()

# Flask routes for Paging Mode
@app.route('/set_algorithm', methods=['POST'])
def set_algorithm():
    data = request.get_json()
    algorithm = data.get('algorithm')
    try:
        simulator.set_algorithm(algorithm)
        return jsonify({"message": f"Algorithm set to {algorithm}."}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

@app.route('/allocate_paging', methods=['POST'])
def allocate_paging():
    data = request.get_json()
    process_id = data.get('process_id')
    page_num = int(data.get('page_num'))
    try:
        simulator.allocate_paging(process_id, page_num)
        return jsonify({"message": "Page allocated successfully."}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/simulate_page_request', methods=['POST'])
def simulate_page_request():
    data = request.get_json()
    process_id = data.get('process_id')
    page_num = int(data.get('page_num'))
    try:
        simulator.simulate_page_request(process_id, page_num)
        return jsonify({"message": "Page request simulated."}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/display_memory', methods=['GET'])
def display_memory():
    return jsonify(simulator.display_memory()), 200

@app.route('/reset', methods=['POST'])
def reset():
    simulator.reset()
    return jsonify({"message": "Memory state reset."}), 200

# Flask routes for Segmentation Mode
@app.route('/set_segmentation_algorithm', methods=['POST'])
def set_segmentation_algorithm():
    data = request.get_json()
    algorithm = data.get('algorithm')
    try:
        segmentation_simulator.set_algorithm(algorithm)
        return jsonify({"message": f"Segmentation algorithm set to {algorithm}."}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

@app.route('/allocate_segmentation', methods=['POST'])
def allocate_segmentation():
    data = request.get_json()
    process_id = data.get('process_id')
    segment_id = int(data.get('segment_id'))
    size = int(data.get('size'))
    try:
        if size <= 0:
            segmentation_simulator.access_segment(process_id, segment_id)
            return jsonify({"message": "Segment accessed (size 0, treated as access)."}), 200
        success = segmentation_simulator.allocate_segmentation(process_id, segment_id, size)
        if success:
            return jsonify({"message": "Segment allocated successfully."}), 200
        else:
            return jsonify({"error": "Failed to allocate segment: insufficient memory."}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/display_segmentation_memory', methods=['GET'])
def display_segmentation_memory():
    return jsonify(segmentation_simulator.display_memory()), 200

@app.route('/reset_segmentation', methods=['POST'])
def reset_segmentation():
    segmentation_simulator.reset()
    return jsonify({"message": "Segmentation memory state reset."}), 200

# Flask routes for Virtual Memory Mode
@app.route('/set_virtual_algorithm', methods=['POST'])
def set_virtual_algorithm():
    data = request.get_json()
    algorithm = data.get('algorithm')
    try:
        virtual_simulator.set_algorithm(algorithm)
        return jsonify({"message": f"Virtual memory algorithm set to {algorithm}."}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

@app.route('/allocate_virtual', methods=['POST'])
def allocate_virtual():
    data = request.get_json()
    process_id = data.get('process_id')
    num_pages = int(data.get('num_pages'))
    try:
        virtual_simulator.allocate_virtual(process_id, num_pages)
        return jsonify({"message": "Virtual pages allocated successfully."}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/simulate_virtual_page_request', methods=['POST'])
def simulate_virtual_page_request():
    data = request.get_json()
    process_id = data.get('process_id')
    page_num = int(data.get('page_num'))
    try:
        virtual_simulator.simulate_virtual_page_request(process_id, page_num)
        return jsonify({"message": "Virtual page request simulated."}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/display_virtual_memory', methods=['GET'])
def display_virtual_memory():
    return jsonify(virtual_simulator.display_memory()), 200

@app.route('/reset_virtual', methods=['POST'])
def reset_virtual():
    virtual_simulator.reset()
    return jsonify({"message": "Virtual memory state reset."}), 200

# Run the Flask app
if __name__ == "__main__":
    app.run(debug=True)