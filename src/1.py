from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def read_root():
    return {"status": "Hello, World!"}

@app.post("/items/")
async def create_item(item: str):
    return {"item": item}

