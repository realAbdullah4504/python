import asyncio
import time

# Simulate downloading a file
async def download_file(file_number):
    print(f"Starting download {file_number}")
    await asyncio.sleep(10)  # Simulate I/O-bound task (e.g., downloading)
    print(f"Finished download {file_number}")

async def main():
    start_time = time.time()

    # Schedule multiple downloads to run concurrently
    tasks = [download_file(i) for i in range(1, 6)]
    
    # Run all tasks concurrently
    await asyncio.gather(*tasks)

    print(f"Total time taken: {time.time() - start_time:.2f} seconds")

# Run the async program
asyncio.run(main())
