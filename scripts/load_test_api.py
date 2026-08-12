import time
import requests
import concurrent.futures

API_URL = "http://localhost:8000/api/v1/screener?min_roe=15.0&sector=IT"
NUM_REQUESTS = 100
CONCURRENCY = 10

def fetch(url):
    start = time.time()
    try:
        r = requests.get(url)
        r.raise_for_status()
        success = True
    except Exception:
        success = False
    end = time.time()
    return end - start, success

def run_load_test():
    print(f"Starting load test on {API_URL}")
    print(f"Total Requests: {NUM_REQUESTS}, Concurrency: {CONCURRENCY}")
    
    start_time = time.time()
    times = []
    success_count = 0
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=CONCURRENCY) as executor:
        futures = [executor.submit(fetch, API_URL) for _ in range(NUM_REQUESTS)]
        for future in concurrent.futures.as_completed(futures):
            elapsed, success = future.result()
            times.append(elapsed)
            if success:
                success_count += 1
                
    total_time = time.time() - start_time
    avg_time = sum(times) / len(times)
    
    print("\n--- Load Test Results ---")
    print(f"Total time taken: {total_time:.2f} seconds")
    print(f"Successful requests: {success_count}/{NUM_REQUESTS}")
    print(f"Average response time: {avg_time*1000:.2f} ms")
    
if __name__ == '__main__':
    run_load_test()
