from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel
from graph.build_graph import create_workflow
from schemas.project_spec import AgentState
import uuid
import os
from pathlib import Path

app = FastAPI(title="Text-to-Code Generator")

class GenerateRequest(BaseModel):
    query: str

class GenerateResponse(BaseModel):
    job_id: str
    message: str

# Store completed jobs
completed_jobs = {}

@app.post("/generate", response_model=GenerateResponse)
async def generate_code(request: GenerateRequest, background_tasks: BackgroundTasks):
    """Generate code from natural language description"""
    
    job_id = str(uuid.uuid4())
    
    # Run generation in background
    background_tasks.add_task(run_generation, job_id, request.query)
    
    return GenerateResponse(
        job_id=job_id,
        message="Code generation started. Use /download/{job_id} to get the result."
    )

@app.get("/download/{job_id}")
async def download_code(job_id: str):
    """Download generated code as zip file"""
    
    if job_id not in completed_jobs:
        raise HTTPException(status_code=404, detail="Job not found or still processing")
    
    zip_path = completed_jobs[job_id]
    
    if not os.path.exists(zip_path):
        raise HTTPException(status_code=404, detail="Generated file not found")
    
    return FileResponse(
        zip_path,
        media_type="application/zip",
        filename=f"generated_project_{job_id}.zip"
    )

@app.get("/status/{job_id}")
async def check_status(job_id: str):
    """Check generation status"""
    
    if job_id in completed_jobs:
        return {"status": "completed", "ready": True}
    return {"status": "processing", "ready": False}

def run_generation(job_id: str, query: str):
    """Background task to run the generation workflow"""
    
    try:
        workflow = create_workflow()
        
        initial_state = AgentState(user_query=query)
        final_state = workflow.invoke(initial_state)
        
        completed_jobs[job_id] = final_state.final_zip_path
        
    except Exception as e:
        print(f"Error in generation: {e}")
        completed_jobs[job_id] = None

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)