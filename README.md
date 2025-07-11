# 📚 **AI Book Publisher — Multi-Agent Workflow with LangGraph, Gemini & Streamlit**

A production-ready, multi-agent AI system that automates the book publishing pipeline using:

- 🧠 Google Gemini (Vertex AI) for rewriting & review  
- 🔁 LangGraph for agent orchestration  
- 💾 ChromaDB for version tracking and memory  
- 📊 Streamlit UI for real-time human feedback  
- ☁️ Cloud Run for scalable, serverless deployment  

> Automatically rewrite, review, revise, and approve content with AI — just provide a URL.

---

## 📝 Blog Walkthrough

📖 Read the full implementation guide on Medium:  
🔗 [AI-Powered Book Publication Workflow with LangGraph and Google Gemini](https://medium.com/@hazrasayan201442/ai-powered-book-publication-workflow-with-langgraph-and-google-gemini-1df9f41e63bf)

---

## 🚀 Features

| Component        | Functionality                                            |
|------------------|----------------------------------------------------------|
| 🧠 **Gemini AI**     | Rewrite & review content using Google’s LLMs            |
| 🔁 **LangGraph**     | Multi-agent stateful flow with pause/resume capability |
| 💾 **ChromaDB**      | Store and search past versions by metadata             |
| 🧍 **Human Review**  | Streamlit UI lets users approve, revise, or reject     |
| ☁️ **Cloud Run**     | Fully serverless, autoscaling deployment               |



## 🗺️ System Architecture

```mermaid
flowchart TD
  _start_ --> writer_agent
  writer_agent --> reviewer_agent
  reviewer_agent --> manager_agent
  manager_agent -->|revision_needed| writer_agent
  manager_agent -->|approved| _end_
  manager_agent -->|quality_check| quality_check
  manager_agent -->|human_review| human_review
  human_review -->|approved| quality_check
  human_review -->|revision_needed| writer_agent
  human_review -->|rejected| _end_
  quality_check --> _end_
````

---

## 📥 How It Works

1. User inputs a **URL**
2. System **scrapes** content using Playwright
3. Writer agent rewrites the content (via Gemini)
4. Reviewer agent scores and comments
5. Manager agent routes it for:

   * ✅ approval
   * 🔁 revision
   * 🧍 human review
   * ✅ final quality check
6. Versioned outputs are saved in ChromaDB
7. System deployed via Docker + Cloud Run

---

## 🧑‍💻 Local Development

### 1. Clone the Repo

```bash
git clone https://github.com/your-username/ai-book-publisher.git
cd ai-book-publisher
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
playwright install chromium
```

### 3. Run the App

```bash
streamlit run main.py
```

---

## ☁️ Cloud Run Deployment

### Build and Push Docker Image

```bash
docker build -t gcr.io/YOUR_PROJECT_ID/ai-book-publisher .
docker push gcr.io/YOUR_PROJECT_ID/ai-book-publisher
```

### Deploy to Cloud Run

```bash
gcloud run deploy ai-book-publisher \
  --image gcr.io/YOUR_PROJECT_ID/ai-book-publisher \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --port 8080 \
  --cpu 2 \
  --memory 4Gi \
  --timeout 3600 \
  --max-instances 5
```

---

## 📂 Project Structure

```
.
├── main.py                  # Streamlit UI
├── book_workflow.py         # LangGraph stateful agent flow
├── agents/
│   ├── writer_agent.py
│   ├── reviewer_agent.py
│   └── manager_agent.py
├── chroma_manager.py       # Version storage
├── scraper.py              # Web content scraper (Playwright)
├── config.py               # Vertex AI + system settings
├── Dockerfile              # Cloud Run deployment
└── requirements.txt
```

---

## 🧪 Sample Workflow State

```json
{
  "original_content": "...",
  "writer_output": "...",
  "reviewer_feedback": "...",
  "manager_decision": "revision_needed",
  "status": "awaiting_human_feedback",
  "iteration_count": 2
}
```

---

## 📦 Roadmap

* [x] Vertex AI + LangGraph integration
* [x] Human-in-the-loop feedback
* [x] ChromaDB versioning
* [x] Streamlit interface
* [x] Cloud Run deployment
* [ ] Notion / Google Docs export
* [ ] Summarization + Chapter Planning agents

---

#### 📺 Live Demo (Streamlit)

Experience the full multi-agent AI publishing pipeline in action through a clean, interactive Streamlit UI:

![Streamlit UI](https://github.com/sayan0506/Multi-Agent-AI-Book-Publisher/blob/main/media/streamlit_ui.png)

#### 🔗 Try the Live Demo (replace with your URL)


#### ✨ What You Can Do:
 
- 📝 Enter any public URL to scrape article content
- ✍️ Watch it get rewritten by the Writer Agent
- 🧠 Review AI feedback and decisions from other agents
- 🧍 Interact with human-in-the-loop approval buttons
- 🧾 View reviewer feedback and final quality checks

The demo also logs agent decisions and stores versioned content in ChromaDB in real time.

## 📄 License

MIT License © 2025 [Sayan Hazra](https://github.com/hazrasayan)

---

