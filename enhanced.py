from flask import Flask, request, jsonify, render_template
from functools import wraps
import collections
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Global configuration
config = {
    "total_memory": 4,
    "page_size": 1,
    "authorized_users": {"admin": "password123"},
    "successful_allocations": 0,
    "page_faults": 0
}

# Authentication Decorator
def authenticate(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth = request.authorization
        if not auth or config["authorized_users"].get(auth.username) != auth.password:
            return jsonify({"error": "Unauthorized access"}), 401
        return f(*args, **kwargs)
    return decorated_function

class MemoryManagementSimulator:
    def __init__(self, total_memory=4, page_size=1):
        self.total_memory = total_memory
        self.page_size = page_size
        self.frames = total_memory // page_size
        self.memory = [None] * self.frames
        self.page_table = {}
        self.page_queue = collections.deque()
        self.page_faults = 0

    def allocate_paging(self, process_id, num_pages):
        if process_id is None or num_pages is None:
            return {"error": "Missing process_id or num_pages."}, 400
        
        allocated = []
        for _ in range(num_pages):
            if None in self.memory:
                frame = self.memory.index(None)
                self.memory[frame] = (process_id, len(self.page_table.get(process_id, [])))
                allocated.append(frame)
                config["successful_allocations"] += 1
            else:
                self.handle_page_fault(process_id)
                allocated.append(self.page_table[process_id][-1])
        self.page_table[process_id] = self.page_table.get(process_id, []) + allocated
        return {"message": f"Allocated {num_pages} pages to process {process_id}", "memory": self.memory}

    def handle_page_fault(self, process_id):
        self.page_faults += 1
        old_page = self.page_queue.popleft() if self.page_queue else None
        if old_page is not None:
            frame = self.memory.index(old_page)
            self.memory[frame] = (process_id, len(self.page_table.get(process_id, [])))
            self.page_table[process_id] = self.page_table.get(process_id, []) + [frame]
            self.page_queue.append((process_id, len(self.page_table.get(process_id, []))))

    def get_memory_state(self):
        return {
            "memory_frames": self.memory,
            "page_table": self.page_table,
            "total_page_faults": self.page_faults,
            "successful_allocations": config["successful_allocations"]
        }

    def deallocate_paging(self, process_id):
        if process_id not in self.page_table:
            return {"error": "Process not found."}, 404
        
        frames_to_free = self.page_table.pop(process_id)
        for frame in frames_to_free:
            self.memory[frame] = None
        self.page_queue = collections.deque(filter(lambda x: x[0] != process_id, self.page_queue))
        return {"message": f"Deallocated pages for process {process_id}", "memory": self.memory}

simulator = MemoryManagementSimulator()

@app.route("/configure", methods=["POST"])
@authenticate
def configure():
    data = request.json
    total_memory = data.get('total_memory', 4)
    page_size = data.get('page_size', 1)
    global simulator
    simulator = MemoryManagementSimulator(total_memory, page_size)
    return jsonify({"message": "Configuration updated successfully."})

@app.route("/allocate_paging", methods=["POST"])
@authenticate
def allocate_paging():
    data = request.json
    process_id = data.get("process_id")
    num_pages = data.get("num_pages")
    return jsonify(simulator.allocate_paging(process_id, num_pages))

@app.route("/memory_state", methods=["GET"])
def memory_state():
    return jsonify(simulator.get_memory_state())

@app.route("/deallocate_paging", methods=["POST"])
@authenticate
def deallocate_paging():
    data = request.json
    process_id = data.get("process_id")
    return jsonify(simulator.deallocate_paging(process_id))

@app.route("/shutdown", methods=["POST"])
@authenticate
def shutdown():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        return jsonify({"error": "Shutdown function not available"}), 500
    func()
    return jsonify({"message": "Server shutting down..."})

if __name__ == "__main__":
    app.run(debug=True)