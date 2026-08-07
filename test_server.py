from fastapi import FastAPI
import uvicorn

from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ⭐ MUST be before uvicorn.run()
app.mount("/images", StaticFiles(directory="G:/images"), name="images")

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
