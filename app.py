import debugpy
import time

# Start Debugpy server (optional)
debugpy.listen(("0.0.0.0", 5678))
print("Waiting for debugger to attach...")
debugpy.wait_for_client()  # Optional: Forces the app to wait for debugger attachment

def slow_function():
    for i in range(5):
        print(f"Processing step {i + 1}...")
        time.sleep(1)  # Simulate a slow operation
    return "Done!"

def main():
    print("Starting the application...")
    
    # Debugging breakpoint
    debugpy.breakpoint()

    result = slow_function()
    print("Result:", result)

if __name__ == "__main__":
    main()
