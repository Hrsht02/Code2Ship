import os
import resource
import secrets
import subprocess
import tempfile
from pathlib import Path

from fastapi import FastAPI, Header, HTTPException

app = FastAPI(title="Cod2Ship Code Runner", version="1.0.0")

EXECUTOR_KEY = os.getenv("EXECUTOR_KEY", "")
TIMEOUT_SECONDS = 5
MAX_OUTPUT = 20000

STARTERS = {
    "python": 'print("Hello, Cod2Ship!")\n',
    "cpp": '#include <iostream>\nusing namespace std;\nint main() {\n    cout << "Hello, Cod2Ship!" << endl;\n    return 0;\n}\n',
    "java": 'public class Main {\n    public static void main(String[] args) {\n        System.out.println("Hello, Cod2Ship!");\n    }\n}\n',
    "javascript": 'console.log("Hello, Cod2Ship!");\n',
}

def limit_process():
    resource.setrlimit(resource.RLIMIT_CPU, (TIMEOUT_SECONDS, TIMEOUT_SECONDS))
    resource.setrlimit(resource.RLIMIT_FSIZE, (2 * 1024 * 1024, 2 * 1024 * 1024))
    resource.setrlimit(resource.RLIMIT_NOFILE, (64, 64))
    try:
        resource.setrlimit(resource.RLIMIT_AS, (512 * 1024 * 1024, 512 * 1024 * 1024))
    except (ValueError, OSError):
        pass

def execute(command, workdir, stdin):
    try:
        p = subprocess.run(
            command,
            cwd=workdir,
            input=stdin,
            text=True,
            capture_output=True,
            timeout=TIMEOUT_SECONDS,
            env={"PATH": "/usr/local/bin:/usr/bin:/bin", "HOME": workdir, "LANG": "C.UTF-8"},
            preexec_fn=limit_process,
        )
        output = (p.stdout + p.stderr)[:MAX_OUTPUT]
        return {"status": "accepted" if p.returncode == 0 else "runtime_error",
                "exit_code": p.returncode, "output": output}
    except subprocess.TimeoutExpired as exc:
        output = ((exc.stdout or "") + (exc.stderr or ""))[:MAX_OUTPUT]
        return {"status": "time_limit", "exit_code": None, "output": output + "\nTime limit exceeded."}

@app.get("/health")
def health():
    return {"status": "ok", "service": "cod2ship-code-runner"}

@app.get("/languages")
def languages():
    return {"languages": sorted(STARTERS)}

@app.post("/run")
def run(payload: dict, x_executor_key: str | None = Header(default=None)):
    if EXECUTOR_KEY and not secrets.compare_digest(x_executor_key or "", EXECUTOR_KEY):
        raise HTTPException(401, "Unauthorized runner request")

    language = str(payload.get("language", "")).lower()
    code = str(payload.get("code", ""))
    stdin = str(payload.get("stdin", ""))

    if language not in STARTERS:
        raise HTTPException(400, "Unsupported language")
    if not code.strip():
        raise HTTPException(400, "Code is empty")
    if len(code) > 50000 or len(stdin) > 10000:
        raise HTTPException(413, "Input too large")

    with tempfile.TemporaryDirectory(prefix="cod2ship-") as tmp:
        root = Path(tmp)
        if language == "python":
            source = root / "main.py"
            source.write_text(code)
            return execute(["python", str(source)], str(root), stdin)

        if language == "javascript":
            source = root / "main.js"
            source.write_text(code)
            return execute(["node", str(source)], str(root), stdin)

        if language == "cpp":
            source = root / "main.cpp"
            binary = root / "main"
            source.write_text(code)
            compile_result = execute(["g++", "-std=c++17", "-O2", "-pipe", str(source), "-o", str(binary)], str(root), "")
            if compile_result["exit_code"] != 0:
                compile_result["status"] = "compile_error"
                return compile_result
            return execute([str(binary)], str(root), stdin)

        source = root / "Main.java"
        source.write_text(code)
        compile_result = execute(["javac", str(source)], str(root), "")
        if compile_result["exit_code"] != 0:
            compile_result["status"] = "compile_error"
            return compile_result
        return execute(["java", "-cp", str(root), "Main"], str(root), stdin)
