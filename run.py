import uvicorn

if __name__ == "__main__":
    uvicorn.run("smart_code_analyzer.backend.main:app", host="127.0.0.1", port=8000, reload=True)
