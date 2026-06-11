import os
import subprocess
import tempfile
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import google.generativeai as genai
import uvicorn

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

genai.configure(api_key="")

class CodeRequest(BaseModel):
    code: str
    language: str
    mode: str = "review"

@app.post("/analyze")
async def analyze_code(request: CodeRequest):
    try:
        model = genai.GenerativeModel('gemini-3-flash-preview')
        
       
        prompts = {
            "review": f"Review this {request.language} code for quality and best practices. Point out readability and maintainability issues.",
            "explain": f"Explain this {request.language} code step-by-step. What does each part do?",
            "refactor": f"Refactor this {request.language} code to be more idiomatic and cleaner. Provide the improved version in a code block.",
            "bugs": f"Find bugs, potential errors, and edge cases in this {request.language} code.",
            "tests": f"Write comprehensive unit tests for this {request.language} code using a common testing framework.",
            "optimize": f"Analyze this {request.language} code for performance bottlenecks and suggest optimizations."
        }
        
        system_prompt = prompts.get(request.mode, "Analyze this code.")
        full_content = f"{system_prompt}\n\n```{request.language.lower()}\n{request.code}\n```"
        
        response = model.generate_content(full_content)
        return {"response": response.text}
        
    except Exception as e:
        print(f"\n🔥 BACKEND ERROR in /analyze: {str(e)}\n")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/run")
async def run_code(request: CodeRequest):
    suffix = ".py" if request.language.lower() == "python" else ".cpp"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as f:
        f.write(request.code.encode())
        temp_path = f.name

    try:
        if request.language.lower() == "python":
            result = subprocess.run(["python", temp_path], capture_output=True, text=True, timeout=5)
            output = result.stdout + result.stderr
        elif request.language.lower() == "c++":
            exe_path = temp_path + ".exe"
            compile_res = subprocess.run(["g++", temp_path, "-o", exe_path], capture_output=True, text=True)
            if compile_res.returncode != 0:
                output = "Compile Error:\n" + compile_res.stderr
            else:
                run_res = subprocess.run([exe_path], capture_output=True, text=True, timeout=5)
                output = run_res.stdout + run_res.stderr
            if os.path.exists(exe_path): 
                os.remove(exe_path)
        else:
            output = f"Language '{request.language}' execution is not configured for local run."
            
        return {"output": output}
        
    except Exception as e:
        print(f"\n🔥 EXECUTION ERROR in /run: {str(e)}\n")
        return {"output": f"Execution Error: {str(e)}"}
        
    finally:
        if os.path.exists(temp_path): 
            os.remove(temp_path)

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
