# Cod2Ship Code Runner

This service is the execution engine behind Code Lab.

Supported languages:
- Python
- C++17
- Java
- JavaScript

## Local

Set a runner key and start:

```bash
docker build -t cod2ship-runner ./executor
docker run --rm -p 8080:8080 -e EXECUTOR_KEY=change-me cod2ship-runner
```

Then set the backend environment:

```
CODE_EXECUTOR_URL=http://localhost:8080
CODE_EXECUTOR_KEY=change-me
```

## Production security

Do **not** run arbitrary student code directly inside the main FastAPI process.

The runner should be deployed as a separate isolated workload/VM/container with:
- no outbound network access
- non-root execution
- CPU and memory limits
- process/PID limits
- short execution timeout
- ephemeral filesystem
- a private network or strong runner API key
- monitoring and rate limiting

The supplied runner applies process resource limits, but container/VM isolation is still required for a production public service.

The main FastAPI service only proxies authenticated users' code to this runner.
