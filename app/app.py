from fastapi import FastAPI


app = FastAPI()

@app.get("/")
def hey_there():
    return {"message": "Hey there!"}