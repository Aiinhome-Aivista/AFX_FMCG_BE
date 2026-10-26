import requests, time

payload = {
    "model": "mistral:latest",
    "messages": [{"role": "user", "content": "Respond with JSON containing status ok"}],
    "format": "json",
    "stream": False
}

def call(primary_url, timeout=180):
    urls = [primary_url]
    if "localhost" not in primary_url and "127.0.0.1" not in primary_url:
        urls.append("http://localhost:11434/api/chat")
    
    for u in urls:
        t0 = time.time()
        try:
            print("Trying URL:", u)
            cur_timeout = min(15, timeout) if u != urls[-1] else timeout
            r = requests.post(u, timeout=cur_timeout, json=payload)
            if r.status_code == 200:
                print(f"Success on URL: {u} in {time.time() - t0:.2f}s")
                return r.json()
        except Exception as e:
            print(f"Failed on URL: {u} after {time.time() - t0:.2f}s. Error: {e}")
            continue
    raise Exception("All failed")

res = call("http://122.163.121.176:3041/api/chat")
print("Result content:", res.get("message", {}).get("content"))
