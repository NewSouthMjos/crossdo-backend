import uvicorn


def serve():
    uvicorn.run("app.main:app", host="0.0.0.0", log_level="info")


if __name__ == "__main__":
    serve()
