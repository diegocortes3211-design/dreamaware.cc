import uvicorn
from fastapi import FastAPI
from .routes import router as action_router

# Create the main FastAPI application
app = FastAPI(
    title="Action Agent Service",
    description="Provides an endpoint to apply patches to code repositories.",
    version="0.1.0",
)

# Include the router from the routes module
app.include_router(action_router)

def serve():
    """
    Starts the Uvicorn server to serve the Action Agent's API.
    This function can be called by a script or a command-line runner.
    """
    # Note: In a production environment, you would typically use a process manager
    # like Gunicorn to run Uvicorn for better performance and reliability.
    # Example: gunicorn -w 4 -k uvicorn.workers.UvicornWorker services.action.main:app
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")

if __name__ == "__main__":
    print("INFO:     Starting Action Agent server...")
    serve()