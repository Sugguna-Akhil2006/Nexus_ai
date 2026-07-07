"""Quick-start example demonstrating core ADK agent construction."""

from sdk.adk.agent_builder import AgentBuilder
from sdk.adk.tool_builder import tool, ToolRegistry
from sdk.adk.workflow_builder import WorkflowBuilder
from sdk.adk.prompt_builder import PromptBuilder
from sdk.adk.agent_tester import AgentTester


# ─── Define Tools ────────────────────────────────────────────────────────────

@tool(description="Fetches a resume from the given URL")
def fetch_resume(context: dict) -> str:
    url = context.get("resume_url", "https://example.com/resume")
    return f"Resume content from {url}"


@tool(description="Scores resume against a job description")
def score_resume(context: dict) -> float:
    return 0.87


# ─── Define a Prompt Template ─────────────────────────────────────────────────

summary_prompt = (
    PromptBuilder()
    .name("resume_summary")
    .version("1.0.0")
    .template("Summarize this resume for the role of {job_title}:\n\n{resume_text}")
    .build()
)


# ─── Build Workflow ───────────────────────────────────────────────────────────

def fetch_fn(ctx: dict) -> str:
    return fetch_resume(ctx)

def score_fn(ctx: dict) -> float:
    return score_resume(ctx)

workflow = (
    WorkflowBuilder()
    .sequential("fetch", fetch_fn, timeout_seconds=10.0)
    .sequential("score", score_fn, timeout_seconds=10.0)
    .build()
)


# ─── Build Agent ──────────────────────────────────────────────────────────────

agent_config = (
    AgentBuilder()
    .name("Resume Agent")
    .description("Analyzes and scores resumes against job descriptions.")
    .model("gpt-4")
    .provider("openai")
    .tool("fetch_resume", fetch_resume, "Fetches a resume")
    .tool("score_resume", score_resume, "Scores a resume")
    .memory("in_memory")
    .system_prompt("resume_summary")
    .build()
)


# ─── Test Locally ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    tester = AgentTester(agent_config)
    tester.mock_provider(response="Score: 0.87 — Strong candidate")

    result = tester.run(context={
        "resume_url": "https://example.com/john_doe.pdf",
        "job_title": "Senior Python Engineer",
    })

    print("Agent:", result["agent"])
    print("Status:", result["status"])
    for tool_name, output in result["results"].items():
        print(f"  {tool_name}: {output}")
