"""CLI entry point: ingest → generate → run-and-fix → submit for review."""
import typer
import httpx
from rich.console import Console
from rich.syntax import Syntax
from agent.rag.ingest import ingest
from agent.generator.generate import generate_tests
from agent.runner.loop import run_and_fix

app = typer.Typer(help="AI Test Generator Agent")
console = Console()


@app.command()
def run(
    spec_url: str = typer.Option("http://localhost:8000/openapi.json", help="OpenAPI spec URL"),
    base_url: str = typer.Option("http://localhost:8000", help="Base URL of the API under test"),
    chroma_path: str = typer.Option("./chroma_db", help="ChromaDB storage path"),
    review_url: str = typer.Option("http://localhost:9000", help="Review server URL"),
    suite_name: str = typer.Option("pizza_api_tests", help="Name for the generated test suite"),
):
    console.rule("[bold blue]Step 1: Ingest OpenAPI spec into ChromaDB")
    count = ingest(spec_url, chroma_path)
    console.print(f"[green]Ingested {count} endpoint(s).")

    console.rule("[bold blue]Step 2: Generate tests via Ollama + RAG")
    test_code = generate_tests(chroma_path, base_url)
    console.print(Syntax(test_code, "python", line_numbers=True))

    console.rule("[bold blue]Step 3: Run-and-fix loop")
    final_code, passed, logs = run_and_fix(test_code)
    for log in logs:
        console.print(log)
    status = "[green]All tests passed!" if passed else "[yellow]Some tests still failing after max iterations."
    console.print(status)

    console.rule("[bold blue]Step 4: Submit for human review")
    resp = httpx.post(f"{review_url}/submit", json={"name": suite_name, "code": final_code})
    resp.raise_for_status()
    console.print(f"[cyan]Submitted. Review at {review_url}/pending/{suite_name}")
    console.print(f"[dim]Approve: POST {review_url}/pending/{suite_name}/decision {{\"approved\": true}}")


if __name__ == "__main__":
    app()
