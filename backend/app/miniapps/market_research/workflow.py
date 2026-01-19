"""
Market Research Mini App Workflow.
"""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..base import BaseMiniApp, MiniAppMetadata, MiniAppResult


class MarketResearchWorkflow(BaseMiniApp):
    """
    Conducts market research on a given topic.

    Workflow:
    1. Generate search queries based on the topic.
    2. Execute web searches.
    3. Synthesize findings into a report.
    """

    def get_metadata(self) -> MiniAppMetadata:
        return MiniAppMetadata(
            id="market_research",
            name="Market Research Assistant",
            description="Deep dive research on companies, products, or trends.",
            version="1.0.0",
            tags=["research", "analysis", "business"],
            variants={
                1: "Standard Research",
            },
        )

    def run(
        self,
        input_data: str,
        variant: int = 1,
        options: Optional[Dict[str, Any]] = None,
    ) -> MiniAppResult:
        topic = input_data.strip()
        job = self.job_store.create(
            workflow_name=f"{self._metadata.id}",
            metadata={"topic": topic},
        )
        job_id = job.id

        logs = []
        artifacts = []
        start_time = time.time()

        try:
            # Step 1: Plan Research
            self._log(job_id, f"Planning research for: {topic}")
            logs.append("Planning research strategy...")

            plan_prompt = self._load_prompt("plan_research.txt", topic=topic)
            plan_response = self.llm_client.complete(
                prompt=plan_prompt, max_tokens=500, temperature=0.3
            )

            # Extract queries (handle JSON parsing)
            try:
                queries = json.loads(plan_response)
                if not isinstance(queries, list):
                    raise ValueError("LLM did not return a list")
            except Exception:
                # Fallback if JSON fails (try regex or split lines)
                import re

                json_match = re.search(r"\[.*\]", plan_response, re.DOTALL)
                if json_match:
                    try:
                        queries = json.loads(json_match.group(0))
                    except:
                        queries = [
                            f"{topic} market size",
                            f"{topic} competitors",
                            f"{topic} trends",
                        ]
                else:
                    queries = [
                        f"{topic} market size",
                        f"{topic} competitors",
                        f"{topic} trends",
                    ]

                logs.append(f"Using search queries: {queries}")

            self._log(job_id, f"Generated queries: {queries}")

            # Step 2: Execute Search
            search_results = []
            search_tool = self.tool_registry.get_tool("search_web")

            if not search_tool:
                raise RuntimeError("search_web tool not found")

            for query in queries[:3]:  # Limit to 3 queries to save time
                self._log(job_id, f"Searching: {query}")
                logs.append(f"Searching: {query}...")

                # Check search tool signature
                result = search_tool.execute({"query": query, "max_results": 3})

                if result.success and result.outputs and "results" in result.outputs:
                    search_results.extend(result.outputs["results"])

                time.sleep(1)  # Be polite

            # Deduplicate results
            seen_urls = set()
            unique_results = []
            for r in search_results:
                if r.get("href") not in seen_urls:
                    unique_results.append(r)
                    seen_urls.add(r.get("href"))

            self._log(job_id, f"Found {len(unique_results)} unique results")
            logs.append(f"Analyzed {len(unique_results)} sources")

            # Save raw data
            raw_data_path = self.artifact_manager.save_json(
                job_id,
                "research_data.json",
                {"queries": queries, "results": unique_results},
            )
            artifacts.append(
                {"type": "json", "label": "Raw Research Data", "path": raw_data_path}
            )

            # Step 3: Synthesize Report
            self._log(job_id, "Synthesizing report...")
            logs.append("Writing final report...")

            # Format context for LLM
            context_str = ""
            for r in unique_results[:8]:  # Limit context context window
                context_str += f"- Title: {r.get('title')}\n  URL: {r.get('href')}\n  Snippet: {r.get('body')}\n\n"

            if not context_str:
                context_str = "No search results found. Please try a different topic."

            report_prompt = self._load_prompt(
                "synthesize_report.txt", topic=topic, context=context_str
            )

            report = self.llm_client.complete(
                prompt=report_prompt, max_tokens=2000, temperature=0.5
            )

            # Save Report
            report_path = self.artifact_manager.save_text(job_id, "report.md", report)
            artifacts.append(
                {"type": "text", "label": "Market Research Report", "path": report_path}
            )

            self._log(job_id, "Workflow completed")
            logs.append("Research completed successfully!")

            return self._create_result(
                status="ok",
                logs=logs,
                artifacts=artifacts,
                result={"report_preview": report[:200] + "..."},
                execution_time=time.time() - start_time,
                completed_at=datetime.now(),
            )

        except Exception as e:
            self._log(job_id, f"Error: {str(e)}")
            # Log full stack trace for debugging
            import traceback

            traceback.print_exc()

            return self._create_result(
                status="error",
                logs=logs + [f"Error: {str(e)}"],
                artifacts=artifacts,
                result={},
                error=str(e),
                execution_time=time.time() - start_time,
                completed_at=datetime.now(),
            )

    def _load_prompt(self, filename: str, **kwargs) -> str:
        prompts_dir = Path(__file__).parent / "prompts"
        try:
            with open(prompts_dir / filename, "r", encoding="utf-8") as f:
                return f.read().format(**kwargs)
        except Exception as e:
            return f"Error loading prompt {filename}: {e}"
