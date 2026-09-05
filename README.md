<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=0:0f2027,50:203a43,100:2c5364&height=220&section=header&text=Big%20Data%20Lab&fontSize=60&fontColor=ffffff&fontAlignY=38&desc=Distributed%20Kubernetes%20Cluster%20%E2%80%94%20NYC%20FHVHV%20Trip%20Duration%20Prediction&descSize=18&descAlignY=60&descColor=a8d8ea" width="100%"/>

<br/>

<!-- Tech Badges -->
![Kubernetes](https://img.shields.io/badge/Kubernetes-K3s-326CE5?style=for-the-badge&logo=kubernetes&logoColor=white)
![Apache Spark](https://img.shields.io/badge/Apache%20Spark-3.3.0-E25A1C?style=for-the-badge&logo=apachespark&logoColor=white)
![Apache Airflow](https://img.shields.io/badge/Apache%20Airflow-2.x-017CEE?style=for-the-badge&logo=apacheairflow&logoColor=white)
![Apache Kafka](https://img.shields.io/badge/Apache%20Kafka-Streaming-231F20?style=for-the-badge&logo=apachekafka&logoColor=white)

![MinIO](https://img.shields.io/badge/MinIO-Data%20Lake-C72E49?style=for-the-badge&logo=minio&logoColor=white)
![JupyterLab](https://img.shields.io/badge/JupyterLab-Notebooks-F37626?style=for-the-badge&logo=jupyter&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Metastore-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)
![Tailscale](https://img.shields.io/badge/Tailscale-Mesh%20VPN-242424?style=for-the-badge&logo=tailscale&logoColor=white)

![Docker](https://img.shields.io/badge/Docker-Containers-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.10-3776AB?style=for-the-badge&logo=python&logoColor=white)
![PySpark](https://img.shields.io/badge/PySpark-ML%20Pipeline-E25A1C?style=for-the-badge&logo=apachespark&logoColor=white)
![WSL2](https://img.shields.io/badge/WSL2-Ubuntu-E95420?style=for-the-badge&logo=ubuntu&logoColor=white)

<br/>

<!-- Cluster Stats -->
![Nodes](https://img.shields.io/badge/Cluster%20Nodes-4%20Devices-0D1117?style=flat-square&logo=server&logoColor=white&labelColor=203a43&color=2c5364)
![Workers](https://img.shields.io/badge/Spark%20Workers-3%20Nodes-0D1117?style=flat-square&logo=apachespark&logoColor=white&labelColor=E25A1C&color=c44a10)
![Cores](https://img.shields.io/badge/Total%20Cores-32%20CPU-0D1117?style=flat-square&logo=intel&logoColor=white&labelColor=0071C5&color=005a9e)
![RAM](https://img.shields.io/badge/Total%20RAM-~20%20GiB-0D1117?style=flat-square&logo=memory&logoColor=white&labelColor=2ecc71&color=27ae60)

</div>

---

## What is this project?

An **end-to-end Big Data & Machine Learning platform** for predicting NYC FHVHV (For-Hire Vehicle) trip durations.

The project runs on a **4-device Kubernetes (K3s) cluster** spanning physically separate Windows machines, connected privately through **Tailscale Mesh VPN**. It covers the full data engineering lifecycle: ingestion → transformation → ML training → orchestration → analytics.

---

## Architecture

```text
╔══════════════════════════════════════════════════════════════════════════╗
║              Tailscale Encrypted Mesh Network (100.x.x.x)               ║
╠══════════════════════╦═══════════════════════════════════════════════════╣
║   MASTER NODE        ║          3 × WORKER NODES                        ║
║   (moamen)           ║   ahmed-worker │ mohamostafa │ desktop-v7dh9ca   ║
║──────────────────────║───────────────────────────────────────────────────║
║  K3s Control Plane   ║  K3s Agents                                      ║
║  Spark Master        ║  Spark Workers (DaemonSet)                       ║
║  Apache Kafka        ║  Dynamic CPU + RAM auto-detection                ║
║  MinIO (S3 API)      ║  32 Total Cores │ ~20 GiB Total RAM              ║
║  PostgreSQL          ║                                                   ║
║  Airflow Scheduler   ║                                                   ║
║  JupyterLab          ║                                                   ║
╚══════════════════════╩═══════════════════════════════════════════════════╝
```

---

## Data Pipeline

```
NYC TLC Parquet  ──►  MinIO Bronze  ──►  Spark Clean+Engineer  ──►  MinIO Silver
                                                                          │
                                                                          ▼
Power BI / Thrift ◄── MinIO Gold  ◄──  Spark ML (Regression Models)  ◄──┘
                          ▲
                     Airflow DAG orchestrates all stages
```

---

## Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| **Cluster Orchestration** | Kubernetes K3s | Pod scheduling, auto-restart, DNS |
| **Network** | Tailscale Mesh VPN | Private cross-device connectivity |
| **Compute Engine** | Apache Spark 3.3.0 | Distributed parallel processing |
| **Data Lake** | MinIO (S3-compatible) | Bronze / Silver / Gold storage tiers |
| **Stream Bus** | Apache Kafka | Future real-time streaming layer |
| **Orchestration** | Apache Airflow 2.x | Pipeline DAG scheduling |
| **Notebooks** | JupyterLab + PySpark | Interactive exploration & ML |
| **Metastore** | PostgreSQL | Airflow metadata + Hive metastore |
| **BI Connectivity** | Spark Thrift Server | JDBC/ODBC for Power BI |
| **Containerization** | Docker → K3s Containerd | Image build, import, runtime |
| **Language** | Python 3.10 / PySpark | ETL, ML, pipeline code |

---

## Repository Layout

```text
bigdata-lab/
├── k8s/                  # Kubernetes manifests (namespace, services, deployments)
│   ├── 00-namespace.yaml
│   ├── 11-kafka.yaml
│   ├── 12-minio.yaml
│   ├── 20-spark-master.yaml
│   ├── 21-spark-workers.yaml
│   ├── 30-airflow.yaml
│   ├── 31-jupyter.yaml
│   └── 33-spark-thrift-server.yaml
├── airflow/              # Airflow DAGs and Dockerfile
│   └── dags/bigdata_fhvhv_pipeline.py
├── jupyter/              # Custom JupyterLab Docker image (PySpark + S3A)
├── notebooks/            # FHVHV processing and ML notebooks
├── spark/apps/           # Spark standalone job scripts
└── README.md
```

---

## Cluster Setup & Deployment Guide

### 1. Network & Prerequisites Setup (Master & Workers)

Install Tailscale on each physical node to establish a private encrypted mesh network:

```bash
# Install Tailscale on Ubuntu/WSL2
curl -fsSL https://tailscale.com/install.sh | sh

# Start Tailscale service
sudo tailscale up

# Get node Tailscale IP (e.g. 100.111.175.49)
tailscale ip -4
```

---

### 2. Master Node (Control Plane) Setup

Run on the Master device in Ubuntu/WSL2:

```bash
# 1. Install K3s Control Plane Server (replace <MASTER_TAILSCALE_IP> with your tailscale IP)
curl -sfL https://get.k3s.io | \
  INSTALL_K3S_EXEC="server \
    --node-ip=<MASTER_TAILSCALE_IP> \
    --advertise-address=<MASTER_TAILSCALE_IP> \
    --tls-san=<MASTER_TAILSCALE_IP> \
    --flannel-iface=tailscale0" sh -

# 2. Verify K3s server status
sudo k3s kubectl get nodes -o wide

# 3. Label Master node
sudo k3s kubectl label node "$(hostname)" node-role=master --overwrite

# 4. Get K3s join token for Worker nodes
sudo cat /var/lib/rancher/k3s/server/node-token
```

---

### 3. Worker Nodes Setup

Run on each of the 3 Worker devices in Ubuntu/WSL2:

```bash
# Join Worker node to K3s cluster (replace <MASTER_TAILSCALE_IP> and <K3S_TOKEN>)
TS_IP=$(tailscale ip -4)
curl -sfL https://get.k3s.io | \
  K3S_URL=https://<MASTER_TAILSCALE_IP>:6443 \
  K3S_TOKEN=<K3S_TOKEN> \
  INSTALL_K3S_EXEC="agent --node-ip=${TS_IP} --flannel-iface=tailscale0" sh -
```

Then, from the Master node terminal, label each joined worker node:

```bash
# Label Worker nodes to trigger Spark Worker DaemonSet deployment
sudo k3s kubectl label node <WORKER_NODE_NAME> node-role=worker --overwrite

# Verify all nodes status and labels
sudo k3s kubectl get nodes -L node-role -o wide
```

---

### 4. Custom Images & Deployment Manifests

From the repository root on the Master node:

```bash
# 1. Prepare secret configuration
cp k8s/02-secrets.example.yaml k8s/02-secrets.yaml
sudo k3s kubectl apply -f k8s/00-namespace.yaml
sudo k3s kubectl apply -f k8s/02-secrets.yaml

# 2. Build custom Docker images for Airflow & Jupyter
docker build -t bigdata-lab-airflow:k8s airflow/docker
docker build -t bigdata-lab-jupyter:s3a-v4 jupyter

# 3. Export & Import images into K3s containerd
docker save -o airflow-custom.tar bigdata-lab-airflow:k8s
docker save -o jupyter-custom.tar bigdata-lab-jupyter:s3a-v4

sudo k3s ctr images import airflow-custom.tar
sudo k3s ctr images import jupyter-custom.tar

# 4. Deploy all Kubernetes manifests
sudo k3s kubectl apply -k k8s/

# 5. Monitor all cluster pods
sudo k3s kubectl get pods -n bigdata -o wide
```

---

## Service Endpoints

| Service | NodePort URL | Description |
|---|---|---|
| **Spark Master UI** | `http://<MASTER_IP>:32081` | Spark Cluster & Worker management |
| **Airflow Web UI** | `http://<MASTER_IP>:32082` | DAG pipeline orchestration |
| **JupyterLab** | `http://<MASTER_IP>:32088/lab?token=lab` | PySpark interactive notebooks |
| **MinIO Console** | `http://<MASTER_IP>:32090` | Data Lake buckets management |
| **Kafka UI** | `http://<MASTER_IP>:32080` | Real-time stream topics management |
| **Spark Thrift Server** | `<MASTER_IP>:10001` | JDBC/ODBC endpoint for Power BI |

---

## Parallel Computing Results

With all 3 worker nodes active:

```
Worker: ahmed-worker    → 12 Cores, 6.7 GiB RAM  ✅ ALIVE
Worker: mohamostafa     → 8 Cores,  6.6 GiB RAM  ✅ ALIVE
Worker: desktop-v7dh9ca → 12 Cores, 6.6 GiB RAM  ✅ ALIVE
─────────────────────────────────────────────────
Total Cluster Capacity  → 32 Cores, ~20 GiB RAM
```

## Streamlit Dashboard

The repository includes a lightweight dashboard for the aggregated Spark results in
`data/nyc_taxi_analysis_results.csv`. It runs independently from the Kafka, Spark, and
Kubernetes services.

### Run locally

```bash
python -m pip install -r requirements-streamlit.txt
streamlit run streamlit_app.py
```

The dashboard opens on `http://localhost:8501`. You can also upload another CSV from the
sidebar as long as it contains the same six result columns.

### Deploy the dashboard to Streamlit Community Cloud

1. Push this repository to GitHub.
2. Create an app at `share.streamlit.io`.
3. Select the repository, branch, and `streamlit_app.py` as the main file.
4. Set the Python dependencies file to `requirements-streamlit.txt` if prompted.

The Big Data cluster itself should continue running on Docker/Kubernetes infrastructure;
Streamlit is the presentation layer for the generated results.

Spark automatically partitions datasets and distributes workload across all 3 worker nodes simultaneously, enabling scalable parallel processing.

---

## Security Notes

- Never commit `k8s/02-secrets.yaml`, K3s node tokens, or Tailscale auth keys.
- Share a K3s join token only privately with the owner of each worker device.
- Keep Tailscale ACLs limited to the project devices and required ports.

<div align="center">
<br/>
<img src="https://capsule-render.vercel.app/api?type=waving&color=0:2c5364,50:203a43,100:0f2027&height=100&section=footer" width="100%"/>
</div>
