# import threading
# import requests
# import time

# # Function to download a file
# def download_file(url, file_name):
#     print(f"Starting download of {file_name} from {url}")
#     response = requests.get(url)
#     # Simulate saving the file (not actually writing here for simplicity)
#     with open(file_name, 'wb') as f:
#         f.write(response.content)
#     print(f"Finished downloading {file_name}")

# # List of file URLs to download
# file_urls = [
#     {"url": "https://example.com/file1.zip", "name": "file1.zip"},
#     {"url": "https://example.com/file2.zip", "name": "file2.zip"},
#     {"url": "https://example.com/file3.zip", "name": "file3.zip"},
#     {"url": "https://example.com/file4.zip", "name": "file4.zip"}
# ]

# def download_files_concurrently():
#     threads = []
    
#     for file in file_urls:
#         # Create a thread for each download
#         thread = threading.Thread(target=download_file, args=(file["url"], file["name"]))
#         threads.append(thread)
#         thread.start()
    
#     # Wait for all threads to complete
#     for thread in threads:
#         thread.join()

# # Start the downloads
# start_time = time.time()
# download_files_concurrently()
# print(f"All downloads finished in {time.time() - start_time:.2f} seconds")


# Multithreading example
import threading

data = []  # This is the shared list across all threads

def add_item():
    data.append(1)  # Each thread adds 1 to the shared list

# Create 5 threads that will execute the add_item function
threads = [threading.Thread(target=add_item) for _ in range(5)]

# Start all threads
[t.start() for t in threads]

# Wait for all threads to finish
[t.join() for t in threads]

# Print the shared data list
print(data)  # Output: [1, 1, 1, 1, 1]

