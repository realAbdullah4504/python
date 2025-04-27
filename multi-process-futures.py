# from concurrent.futures import ThreadPoolExecutor, as_completed
# import time

# def task(x):
#     time.sleep(x)
#     return x * 10

# results = []
# with ThreadPoolExecutor(max_workers=3) as executor:
#     futures = [executor.submit(task, i) for i in range(5)]

#     for future in as_completed(futures):
#         print("Done?", future.done())  # True
#         print("Running?", future.running())  # False (already done)
#         print("Cancelled?", future.cancelled())
        
#         try:
#             res = future.result()
#             results.append(res)
#             print("Result:", res)
#         except Exception as e:
#             print("Error:", e)

# print("All results:", results)
# from concurrent.futures import ThreadPoolExecutor

# def add(x, y):
#     return x + y

# with ThreadPoolExecutor() as executor:
#     future1 = executor.submit(add, 5, 7)
#     future2 = executor.submit(add, 3, 4)
    
#     # Now you can track or get the results of each Future
#     print(future1)  # Output: 12
#     print(future2)  # Output: 7