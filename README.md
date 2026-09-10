# 📄 VM Document Generator — n8n + Ollama

An automated infrastructure documentation workflow built with **n8n** that connects to virtual machines via SSH, extracts system data, and generates a structured PDF report — scheduled to run automatically so documentation stays current without manual effort.

---

## 📌 The Problem

In telecom and IT deployment projects, infrastructure documentation is almost never done properly:

- It gets created once at go-live and never updated
- Configuration changes are rarely tracked
- Support and delivery teams work with outdated or missing documentation

This workflow solves that by **automating the entire documentation process** on a schedule.

---

## 💡 The Solution

A self-hosted n8n workflow that:

1. Connects to a VM via SSH on a schedule
2. Runs system commands to extract key infrastructure data
3. Builds a structured snapshot with metadata, system info, and network details
4. Generates a clean HTML report and converts it to PDF via Gotenberg
5. Sends the PDF report by email automatically

---

## 🧰 Tech Stack

| Tool | Purpose |
|------|---------|
| [n8n](https://n8n.io/) | Workflow automation (self-hosted) |
| [Ollama](https://ollama.com/) | Local LLM runner (future AI analysis) |
| [Gotenberg](https://gotenberg.dev/) | HTML to PDF conversion (self-hosted) |
| SSH | Remote command execution on VMs |
| Gmail | Email delivery of reports |
| Docker | Container platform for all services |

> ✅ **Runs 100% locally** — no external AI API required. All processing happens in your own infrastructure.

---

## 🔄 Workflow Architecture

```
[Schedule Trigger — runs every N hours]
        │
        ├──→ [SSH: hostname]
        ├──→ [SSH: uname -a]
        └──→ [SSH: ip addr]
                    │
            [Merge all outputs]
                    │
        [Build Snapshot JSON]
        metadata + system + network
                    │
            [Generate HTML Report]
                    │
        [Convert HTML → PDF via Gotenberg]
                    │
        [Send PDF by email]
```

---

## 📊 Report Output

Each execution generates a PDF with:

| Section | Data |
|---------|------|
| **Metadata** | Snapshot ID, timestamp, collector, status |
| **System Info** | Hostname, Host ID, OS version |
| **Network** | IP addresses (filtered, no loopback) |
| **Raw Commands** | Full stdout output for auditability |

---

## ⚙️ Requirements

- [n8n](https://docs.n8n.io/hosting/) self-hosted (Docker recommended)
- [Ollama](https://ollama.com/) installed locally
- [Gotenberg](https://gotenberg.dev/) running as Docker container
- SSH access to target VM
- Gmail account with OAuth2 configured in n8n

### Docker Compose (recommended)

Run all services together:

```yaml
services:
  n8n:
    image: n8nio/n8n
    ports:
      - "5678:5678"

  gotenberg:
    image: gotenberg/gotenberg:8
    ports:
      - "3000:3000"

  ollama:
    image: ollama/ollama
    ports:
      - "11434:11434"
```

---

## 🚀 How to Use

**1. Import the workflow**
- Open your n8n instance
- Go to **Workflows → Import**
- Upload `Document_Generator.json`

**2. Configure credentials**
- Set up **SSH Password** credentials with your VM connection details
- Set up **Ollama** connection (default: `http://localhost:11434`)
- Set up **Gmail OAuth2** credentials
- Update the email address in the `Send report as attachment` node

**3. Configure the schedule**
- Edit the `Schedule Trigger` node to set your preferred frequency
- Recommended: every 24 hours for change tracking

**4. Activate and run**
- Activate the workflow
- Trigger manually first to validate the full flow
- Check your inbox for the PDF report

---

## 📁 Repository Structure

```
vm-document-generator-n8n/
│
├── README.md                      ← You are here
└── Document_Generator.json        ← n8n workflow (import this)
```

---

## 🛣️ Roadmap

This is a **v1 prototype** focused on validating the core concept. Planned improvements:

- [ ] **AI-powered change detection** — use Ollama to compare current snapshot with previous version and generate a change summary automatically
- [ ] **Multi-VM support** — load connection list from a config file and iterate across all servers
- [ ] **Expanded data collection** — add commands for CPU, memory, disk, running services, open ports
- [ ] **Version history** — store snapshots in a database for long-term comparison
- [ ] **Change alerts** — send notifications only when changes are detected

---

## 💡 Use Cases

- Telecom delivery teams documenting network server state post-deployment
- Support teams validating configuration changes between maintenance windows
- Any team that needs automated, recurring infrastructure snapshots

---

## 🔒 Privacy & Security

- All processing runs **locally** — no VM data is sent to external services
- SSH credentials are managed within n8n and never exposed in the workflow JSON
- Gotenberg and Ollama run as local Docker containers

---

## 👤 Author

**Enzo Huanca**
Senior Enterprise Architect | Telecom & AI | Program Manager LATAM

[LinkedIn](https://www.linkedin.com/in/enzohuanca) · [GitHub](https://github.com/funk1090)

---

## 📄 License

MIT License — feel free to use, modify and share.
