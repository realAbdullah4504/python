import multiprocessing
import os

def cpu_task():
    # Heavy CPU-bound task (e.g., some pointless calculation)
    print(f"Process {os.getpid()} started.")
    x = 0
    for _ in range(10**10):
        x += 1
    print(f"Process {os.getpid()} finished.")

if __name__ == "__main__":
    total_cores = multiprocessing.cpu_count()
    target_cores = max(1, int(total_cores * 0.8))  # use at least 1 core

    print(f"Total cores: {total_cores}, using: {target_cores}")

    processes = []
    for _ in range(target_cores):
        p = multiprocessing.Process(target=cpu_task)
        p.start()
        processes.append(p)

    for p in processes:
        p.join()
