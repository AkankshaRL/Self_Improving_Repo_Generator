from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from graph.build_graph import create_workflow
from schemas.project_spec import AgentState

app = FastAPI(title="Text-to-Code Generator")

class GenerateRequest(BaseModel):
    query: str

@app.get("/")
async def root():
    """Health check"""
    return {"status": "online", "message": "Text-to-Code Generator API"}

@app.post("/generate")
async def generate_code(request: GenerateRequest):
    """
    Generate code and return ZIP file directly
    
    This is a synchronous endpoint - it will take 30s-2min to respond
    """
    
    if not request.query or not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    
    try:
        print(f"\n{'='*60}")
        print(f"📝 Received query: {request.query}")
        print(f"{'='*60}")
        
        # Create workflow
        print("⚙️  Creating workflow...")
        workflow = create_workflow()
        
        # Create initial state
        initial_state = AgentState(user_query=request.query)
        
        # Run workflow (this blocks until complete)
        print("🔄 Running workflow...")
        final_state = workflow.invoke(initial_state)
        
        # Get the zip file path
        zip_path = final_state.get('final_zip_path')
        
        if not zip_path or not os.path.exists(zip_path):
            raise HTTPException(
                status_code=500, 
                detail="Generation completed but output file not created"
            )
        
        print(f"✅ Generation complete!")
        print(f"📦 Zip file: {zip_path}")
        print(f"{'='*60}\n")
        
        # Return the zip file
        filename = os.path.basename(zip_path)
        
        return FileResponse(
            path=zip_path,
            media_type='application/zip',
            filename=filename
        )
    
    except Exception as e:
        print(f"\n❌ Error during generation:")
        print(f"   {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        
        raise HTTPException(
            status_code=500,
            detail=f"Generation failed: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Simple Text-to-Code Generator API")
    print("📚 Endpoint: POST http://localhost:8000/generate")
    print("🏥 Health: GET http://localhost:8000/")
    print("\nNote: /generate endpoint may take 30s-2min to respond")
    uvicorn.run(app, host="0.0.0.0", port=8000)