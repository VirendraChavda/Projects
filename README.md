# 🚀 Deployment Workflow Guide  
### For Multi-App Projects with Docker Desktop + Kubernetes (Kustomize)

This document explains **what to do after finishing local development** of any app inside the `Applications/` folder — including how to build the Docker image, apply Kubernetes YAMLs, and promote across environments (`dev`, `test`, `prod`).

---

## 📁 Folder Structure Overview

```
D:\Projects
│
├── Applications/
│   ├── llm-app-frontend/
│   │   ├── app/
│   │   ├── Dockerfile
│   │   ├── pyproject.toml
│   │   ├── poetry.lock
│   │   └── tests/
│   │
│   └── llm-app-backend/
│       ├── app/
│       ├── Dockerfile
│       ├── pyproject.toml
│       ├── poetry.lock
│       └── tests/
│
└── Cluster/
    ├── llm-app-frontend/
    │   ├── base/
    │   │   ├── deployment.yaml
    │   │   ├── service.yaml
    │   │   └── kustomization.yaml
    │   └── overlays/
    │       ├── dev/kustomization.yaml
    │       ├── test/kustomization.yaml
    │       └── prod/kustomization.yaml
    │
    └── llm-app-backend/
        ├── base/
        │   ├── deployment.yaml
        │   ├── service.yaml
        │   └── kustomization.yaml
        └── overlays/
            ├── dev/kustomization.yaml
            ├── test/kustomization.yaml
            └── prod/kustomization.yaml
```

---

## 🧱 Step 1 — Verify App Works Locally

Each application (frontend or backend) is an independent Poetry project.

```bash
cd Applications\llm-app-backend
poetry install
poetry run pytest      # optional tests
poetry run python -m app
```

✅ If it runs correctly — proceed to containerization.

---

## 🧰 Step 2 — Build the Docker Image

Each project folder already contains a Dockerfile.  
Run the following inside your application folder:

```bash
docker build -t llm-app-backend:dev .
```

For frontend:
```bash
docker build -t llm-app-frontend:dev .
```

### Optional GPU check (PyTorch or CUDA)
```bash
docker run --rm -it --gpus all llm-app-backend:dev   python -c "import torch;print(torch.cuda.is_available(), torch.cuda.get_device_name(0))"
```

If you see your GPU name — CUDA works.

---

## ☸️ Step 3 — Confirm Kubernetes Is Running

Make sure Docker Desktop’s built-in Kubernetes cluster is active.

```bash
kubectl get nodes
```

You should see:
```
NAME             STATUS   ROLES           AGE   VERSION
docker-desktop   Ready    control-plane   2d    v1.30.x
```

If not, open Docker Desktop → Settings → Kubernetes → **Enable Kubernetes** → wait until “Kubernetes is running”.

---

## 🧩 Step 4 — Deploy to Kubernetes (Dev Environment)

Kubernetes manifests live under the `Cluster/` folder.  
Each app has its own **base** (common YAML) and **overlays** (per-environment configuration).

To deploy the **backend**:
```bash
kubectl apply -k Cluster/llm-app-backend/overlays/dev
```

To deploy the **frontend**:
```bash
kubectl apply -k Cluster/llm-app-frontend/overlays/dev
```

You can repeat the same command for `test` or `prod` overlays later.

---

## 🔍 Step 5 — Verify Deployment

Check namespaces and pods:

```bash
kubectl get ns
kubectl get pods -n dev
```

Expected output:
```
NAME                                 READY   STATUS    RESTARTS   AGE
llm-app-backend-5f9f56b4b9-b9dps     1/1     Running   0          30s
llm-app-frontend-6c9f4577d9-4f5lx    1/1     Running   0          28s
```

View logs:
```bash
kubectl logs -n dev deploy/llm-app-backend
```

---

## ⚙️ Step 6 — Update Image After Code Changes

When you modify code:

1. Rebuild your image:
   ```bash
   docker build -t llm-app-backend:dev .
   ```

2. Reapply the overlay:
   ```bash
   kubectl apply -k Cluster/llm-app-backend/overlays/dev
   ```

Kubernetes will detect the new image and roll out a fresh pod automatically.

---

## 🚀 Step 7 — Promote Between Environments

When your app works well in **dev**, promote it to higher environments.

| Environment | Command | Description |
|--------------|----------|-------------|
| Dev | `kubectl apply -k overlays/dev` | Default testing setup |
| Test | `kubectl apply -k overlays/test` | Uses different namespace / tag |
| Prod | `kubectl apply -k overlays/prod` | Production deployment |

Each overlay file sets:
- the correct **namespace** (`dev`, `test`, `prod`)
- the **Docker image tag** (`:dev`, `:test`, `:prod`)
- optional replica count or limits

---

## 🧠 Step 8 — Check GPU Inside Pod (Optional)

```bash
kubectl -n dev exec -it deploy/llm-app-backend --   python -c "import torch;print(torch.cuda.is_available(), torch.cuda.get_device_name(0))"
```

If it returns your GPU name → GPU plugin and image are configured correctly.

---

## 🧹 Step 9 — Cleanup or Redeploy

Remove a deployment:
```bash
kubectl delete -k Cluster/llm-app-backend/overlays/dev
```

Remove the namespace (optional):
```bash
kubectl delete namespace dev
```

Recreate later with:
```bash
kubectl create namespace dev
```

---

## 🧩 Step 10 — Troubleshooting

| Problem | Cause | Fix |
|----------|--------|-----|
| `ImagePullBackOff` | Image tag mismatch or not built | Ensure `docker build -t <name>:<tag> .` matches overlay image tag |
| `namespace not found` | Namespace deleted or missing | Recreate with `kubectl create namespace dev` |
| Pod stuck in `Pending` | GPU resource requested but plugin missing | Either install NVIDIA device plugin or remove GPU limit |
| `Kubernetes not running` | Docker Desktop setting off | Enable it under Docker Desktop → Settings → Kubernetes |

---

## 📦 Common Commands Reference

```bash
# List all namespaces
kubectl get ns

# List pods in a namespace
kubectl get pods -n dev

# Check logs of a pod
kubectl logs -n dev deploy/llm-app-backend

# Describe a pod in detail
kubectl describe pod <pod-name> -n dev

# Reapply configuration
kubectl apply -k Cluster/llm-app-backend/overlays/dev

# Delete deployment
kubectl delete -k Cluster/llm-app-backend/overlays/dev
```

---

## 🧭 Summary Workflow

| Step | Action | Tool |
|------|---------|------|
| 1 | Develop & test locally with Poetry | Python / Poetry |
| 2 | Build Docker image | Docker |
| 3 | Ensure Kubernetes is running | Docker Desktop |
| 4 | Apply Kustomize overlay (dev/test/prod) | kubectl |
| 5 | Check pods & logs | kubectl |
| 6 | Promote image tags to higher environments | kubectl / CI/CD |

---

## 🧱 How Base & Overlays Work (Quick Reminder)

- **`base/`** → Common YAML files (Deployment + Service) shared by all environments  
- **`overlays/`** → Environment-specific tweaks  
  - `namespace` (`dev`, `test`, `prod`)  
  - `image tag` (e.g., `myapp:dev`, `myapp:test`)  
  - optional replica counts or resource limits  

You deploy using overlays, e.g.:

```bash
kubectl apply -k Cluster/llm-app-backend/overlays/dev
```

Kustomize automatically merges your base + overlay YAMLs and applies the final configuration to the cluster.

---

## ✅ Final Notes

- All applications (`frontend`, `backend`, etc.) can share the **same Kubernetes cluster** and namespaces.
- Namespaces are persistent — they survive PC and Docker restarts.
- You only rebuild images when app code changes.
- You only modify YAMLs when deployment structure or resources change.

---

**Author’s Note:**  
This README covers a self-contained, multi-application workflow for local or single-node clusters using **Docker Desktop + Kubernetes + Kustomize**.  
It ensures reproducible, GPU-aware deployments without needing Helm or cloud infrastructure.

---