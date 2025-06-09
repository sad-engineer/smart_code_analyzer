import uvicorn
import subprocess
import os

def start_prometheus():
    prometheus_config = os.path.abspath("prometheus.yml")
    subprocess.Popen([
        "docker", "run", "--rm", "-p", "9090:9090",
        "-v", f"{prometheus_config}:/etc/prometheus/prometheus.yml",
        "prom/prometheus"
    ])

def start_grafana():
    subprocess.Popen([
        "docker", "run", "--rm", "-p", "3000:3000", "grafana/grafana"
    ])

if __name__ == "__main__":
    start_prometheus()
    start_grafana()
    uvicorn.run("smart_code_analyzer.backend.main:app", host="127.0.0.1", port=8000, reload=True)
