import collections

class MemoryManagementSimulator:
    def __init__(self, total_memory=4, page_size=1):
        self.total_memory = total_memory  # Total memory in KB
        self.page_size = page_size  # Page size in KB
        self.frames = total_memory // page_size  # Number of frames
        self.memory = [None] * self.frames  # Physical memory
        self.page_table = {}  # Page table mapping process pages to frames
        self.disk = {}  # Simulated disk storage
        self.page_replacement_algorithm = "FIFO"
        self.page_queue = collections.deque()
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

    def handle_page_fault(self, process_id):
        """Handle page faults by replacing a page using FIFO or LRU."""
        self.page_faults += 1  # Increment page fault count
        if self.page_replacement_algorithm == "FIFO":
            old_page = self.page_queue.popleft()
        else:
            old_page = min(self.page_table, key=lambda x: self.page_table[x])

        frame = self.memory.index(old_page)
        self.disk[old_page] = old_page  # Simulate writing to disk
        self.memory[frame] = (process_id, len(self.page_table.get(process_id, [])))
        self.page_queue.append((process_id, len(self.page_table.get(process_id, []))))
        self.page_table[process_id] = self.page_table.get(process_id, []) + [frame]

    def get_memory_state(self):
        """Return the current memory state and statistics."""
        return {
            "Memory Frames": self.memory,
            "Page Table": self.page_table,
            "Disk Storage": self.disk,
            "Total Page Faults": self.page_faults
        }
