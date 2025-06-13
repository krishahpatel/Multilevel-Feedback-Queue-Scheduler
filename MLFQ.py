import tkinter as tk
from tkinter import ttk, messagebox
import queue
import time
import threading
import matplotlib.pyplot as plt

class Process:
    def __init__(self, pid, arrival_time, burst_time, priority):
        self.pid = pid
        self.arrival_time = arrival_time
        self.burst_time = burst_time
        self.priority = priority  
        self.remaining_time = burst_time
        self.queue_level = None  
        self.completion_time = 0
        self.turnaround_time = 0
        self.waiting_time = 0
        self.added_to_queue = False
        self.time_in_current_queue = 0
        self.last_queue_update = 0

class MLFQSimulator:
    def __init__(self, root):
        self.root = root
        self.root.title("MLFQ Scheduler")
        
        self.queues = [queue.Queue(), queue.Queue(), queue.Queue()] 
        self.time_quantum = [4, 8, 12]  
        self.promotion_threshold = {
            2: 10,  
            1: 8    
        }
        self.process_list = []
        self.gantt_chart_data = []
        self.current_time = 0
        
        self.show_main_screen()

    
    def show_main_screen(self):
        for widget in self.root.winfo_children():
            widget.destroy()
        
        ttk.Label(self.root, text="Multilevel Feedback Queue (MLFQ) CPU Scheduling", 
                 font=('Helvetica', 14, 'bold')).pack(pady=20)
        
        ttk.Button(self.root, text="Enter Process Data", 
                  command=self.show_input_screen).pack(pady=20)
    
    def show_input_screen(self):
        for widget in self.root.winfo_children():
            widget.destroy()
        
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        input_frame = ttk.Frame(main_frame)
        input_frame.pack(pady=10)
        
        ttk.Label(input_frame, text="Number of Processes:").pack(side=tk.LEFT)
        self.num_processes_entry = ttk.Entry(input_frame, width=5)
        self.num_processes_entry.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(input_frame, text="Generate Fields", 
                  command=self.generate_process_fields).pack(side=tk.LEFT)
        
        ttk.Button(main_frame, text="Back to Main", 
                  command=self.show_main_screen).pack(pady=5)
        
        self.process_fields_frame = ttk.Frame(main_frame)
        self.process_fields_frame.pack(fill=tk.X, pady=10)
        
        self.submit_button = ttk.Button(main_frame, text="Submit Processes", 
                                      command=self.submit_processes, state=tk.DISABLED)
        self.submit_button.pack(pady=10)
    
    def generate_process_fields(self):
        try:
            num_processes = int(self.num_processes_entry.get())
            if num_processes <= 0:
                raise ValueError("Number of processes must be positive")
        except ValueError as e:
            messagebox.showerror("Error", str(e))
            return
        
        for widget in self.process_fields_frame.winfo_children():
            widget.destroy()
        
        headers = ["PID", "Arrival Time", "Burst Time", "Priority (1-3)"]
        for col, header in enumerate(headers):
            ttk.Label(self.process_fields_frame, text=header).grid(row=0, column=col, padx=5, pady=2)
        
        self.process_entries = []
        for i in range(num_processes):
            ttk.Label(self.process_fields_frame, text=f"P{i+1}").grid(row=i+1, column=0, padx=5, pady=2)
            
            arrival_entry = ttk.Entry(self.process_fields_frame, width=8)
            arrival_entry.grid(row=i+1, column=1, padx=5, pady=2)
            
            burst_entry = ttk.Entry(self.process_fields_frame, width=8)
            burst_entry.grid(row=i+1, column=2, padx=5, pady=2)
            
            priority_entry = ttk.Entry(self.process_fields_frame, width=8)
            priority_entry.grid(row=i+1, column=3, padx=5, pady=2)
            
            self.process_entries.append((arrival_entry, burst_entry, priority_entry))
        
        self.submit_button.config(state=tk.NORMAL)
    
    def submit_processes(self):
        self.process_list = []
        valid_processes = 0
        
        for i, (arrival_entry, burst_entry, priority_entry) in enumerate(self.process_entries):
            pid = f"P{i+1}"
            
            try:
                arrival = int(arrival_entry.get())
                burst = int(burst_entry.get())
                priority = int(priority_entry.get())
                
                if priority not in [1, 2, 3]:
                    raise ValueError("Priority must be 1, 2, or 3")
                if arrival < 0 or burst <= 0:
                    raise ValueError("Times must be positive")
                
                self.process_list.append(Process(pid, arrival, burst, priority))
                valid_processes += 1
                
            except ValueError as e:
                messagebox.showerror("Input Error", f"Invalid input for {pid}: {str(e)}")
                return
        
        if valid_processes > 0:
            self.show_simulation_screen()
        else:
            messagebox.showwarning("Warning", "No valid processes submitted")
    
    def show_simulation_screen(self):
        for widget in self.root.winfo_children():
            widget.destroy()
        
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(control_frame, text="Back to Main", 
                  command=self.show_main_screen).pack(side=tk.LEFT)
        
        self.run_button = ttk.Button(control_frame, text="Run Simulation", 
                                   command=self.run_simulation)
        self.run_button.pack(side=tk.LEFT, padx=5)
        
        self.gantt_button = ttk.Button(control_frame, text="Show Gantt Chart", 
                                      command=self.show_gantt_chart, state=tk.DISABLED)
        self.gantt_button.pack(side=tk.LEFT, padx=5)
        
        output_frame = ttk.LabelFrame(main_frame, text="Simulation Output", padding="10")
        output_frame.pack(fill=tk.BOTH, expand=True)
        
        self.output_text = tk.Text(output_frame, height=10, wrap=tk.WORD)
        self.output_text.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(output_frame, command=self.output_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.output_text.config(yscrollcommand=scrollbar.set)
        
        self.output_text.insert(tk.END, "Submitted processes:\n")
        for process in self.process_list:
            self.output_text.insert(tk.END, 
                f"{process.pid}: Arrival={process.arrival_time}, Burst={process.burst_time}, Priority={process.priority}\n")
    
    def run_simulation(self):
        self.gantt_chart_data = []
        self.current_time = 0
        for q in self.queues:
            while not q.empty():
                q.get()
        
        for process in self.process_list:
            process.remaining_time = process.burst_time
            process.queue_level = 0
        
        self.run_button.config(state=tk.DISABLED)
        self.gantt_button.config(state=tk.NORMAL)
        
        threading.Thread(target=self.execute_mlfq, daemon=True).start()
    
    
    def execute_mlfq(self):
        self.output_text.insert(tk.END, "\n=== Simulation Started ===\n")

        while True:
            all_completed = all(p.remaining_time == 0 for p in self.process_list)
            if all_completed:
                break

            self.check_for_promotions()

            for process in self.process_list:
                if process.arrival_time <= self.current_time and process.remaining_time > 0 and not process.added_to_queue:
                    if process.priority == 3:  
                        queue_level = 0
                    elif process.priority == 2:  
                        queue_level = 1
                    else: 
                        queue_level = 2
                    
                    process.queue_level = queue_level
                    process.added_to_queue = True
                    process.last_queue_update = self.current_time
                    self.queues[queue_level].put(process)
                    self.output_text.insert(tk.END, 
                        f"Time {self.current_time}: {process.pid} (Priority {process.priority}) arrived and added to Q{queue_level}\n")
                    self.output_text.see(tk.END)

            executed = False

            for level in range(3):
                if not self.queues[level].empty():
                    process = self.queues[level].get()
                    tq = self.time_quantum[level]

                    start_time = self.current_time
                    execution_time = min(tq, process.remaining_time)
                    end_time = start_time + execution_time

                    self.gantt_chart_data.append((process.pid, start_time, end_time, level))
                    process.remaining_time -= execution_time

                    self.output_text.insert(tk.END, 
                        f"Time {start_time}-{end_time}: {process.pid} runs in Q{level} "
                        f"(Remaining: {process.remaining_time})\n")
                    self.output_text.see(tk.END)

                    self.current_time += execution_time
                    time.sleep(0.5)

                    if process.remaining_time > 0:
                        self.queues[level].put(process)
                        process.last_queue_update = self.current_time
                    else:
                        process.completion_time = self.current_time
                        process.turnaround_time = process.completion_time - process.arrival_time
                        process.waiting_time = process.turnaround_time - process.burst_time
                        self.output_text.insert(tk.END, 
                            f"Time {self.current_time}: Process {process.pid} completed!\n"
                            f"Turnaround Time: {process.turnaround_time}\n"
                            f"Waiting Time: {process.waiting_time}\n")
                        self.output_text.see(tk.END)

                    executed = True
                    break

            if not executed:
                self.current_time += 1
                time.sleep(0.1)

        avg_turnaround = sum(p.turnaround_time for p in self.process_list) / len(self.process_list)
        avg_waiting = sum(p.waiting_time for p in self.process_list) / len(self.process_list)

        self.output_text.insert(tk.END, "\n=== Simulation Completed ===\n")
        self.output_text.insert(tk.END, f"\nAverage Turnaround Time: {avg_turnaround:.2f}\n")
        self.output_text.insert(tk.END, f"Average Waiting Time: {avg_waiting:.2f}\n")
        self.output_text.see(tk.END)

    def check_for_promotions(self):
        for level in range(1, 3): 
            processes = []
            while not self.queues[level].empty():
                processes.append(self.queues[level].get())

            for process in processes:
                time_in_queue = self.current_time - process.last_queue_update
                threshold = self.promotion_threshold[level]

                if time_in_queue >= threshold:
                    new_level = level - 1
                    process.queue_level = new_level
                    process.last_queue_update = self.current_time
                    self.queues[new_level].put(process)
                    self.output_text.insert(tk.END, 
                        f"Time {self.current_time}: {process.pid} promoted to Q{new_level}\n")
                else:
                    self.queues[level].put(process)

    
    def show_gantt_chart(self):
        if not self.gantt_chart_data:
            self.output_text.insert(tk.END, "No data to plot.\n")
            self.output_text.see(tk.END)
            return

        fig, ax = plt.subplots(figsize=(12, 3))

        all_times = set()
        for _, start, end, _ in self.gantt_chart_data:
            all_times.add(start)
            all_times.add(end)
        sorted_times = sorted(all_times)

        for entry in self.gantt_chart_data:
            pid, start, end, _ = entry
            ax.broken_barh([(start, end - start)], (10, 9), facecolors='skyblue')
            ax.text(start + (end - start)/2, 14, f"{pid}", ha='center', va='center', fontsize=8)

        # Add vertical separator lines
        for t in sorted_times:
            ax.axvline(t, color='gray', linestyle='--', linewidth=0.5)
            ax.text(t, 8, f"{t}", ha='center', va='top', fontsize=7, rotation=90)

        ax.set_ylim(5, 25)
        ax.set_xlim(0, max(sorted_times) + 1)
        ax.set_xlabel('Time')
        ax.set_yticks([])
        ax.set_title('Gantt Chart')

        plt.tight_layout()
        plt.show()


if __name__ == "__main__":
    root = tk.Tk()
    app = MLFQSimulator(root)
    root.mainloop()