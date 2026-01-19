"""
Real Estate Ad Generator Mini App.

This mini app generates compelling real estate advertisements from listing URLs.
It scrapes the listing data, analyzes it, and generates professional ad copy.

Workflow:
1. Scrape the provided listing URL
2. Analyze the HTML to extract structured data
3. Generate ad copy based on the selected variant
4. Save artifacts (extracted data, generated ad)

Variants:
1. Basic - Simple, concise ad (2-3 paragraphs)
2. Detailed - Comprehensive, sophisticated ad (4-5 paragraphs)
3. SEO-optimized - Search engine optimized ad with keywords
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional
from time import time

from ..base import BaseMiniApp, MiniAppMetadata, MiniAppResult


class RealEstateAdGenerator(BaseMiniApp):
    """
    Generates real estate advertisements from listing URLs.

    This mini app demonstrates the AI Suite workflow pattern:
    - Tool usage (scraping)
    - LLM prompting (analysis and generation)
    - Artifact management
    - Job tracking and logging
    """

    def get_metadata(self) -> MiniAppMetadata:
        """Return metadata for the real estate ad generator."""
        return MiniAppMetadata(
            id="realestate_ads",
            name="Real Estate Ad Generator",
            description="Generate compelling real estate advertisements from listing URLs",
            version="1.0.0",
            author="AI Suite",
            tags=["marketing", "real-estate", "copywriting"],
            variants={
                1: "Basic - Simple, concise ad",
                2: "Detailed - Comprehensive, sophisticated ad",
                3: "SEO-optimized - Search engine optimized ad with keywords",
            },
        )

    def run(
        self,
        input_data: str,
        variant: int = 1,
        options: Optional[Dict[str, Any]] = None,
    ) -> MiniAppResult:
        """
        Execute the real estate ad generation workflow.

        Args:
            input_data: URL of the real estate listing to process
            variant: Ad style (1=Basic, 2=Detailed, 3=SEO-optimized)
            options: Additional options (currently unused)

        Returns:
            MiniAppResult with status, logs, artifacts, and generated ad
        """
        started_at = datetime.now()
        start_time = time()

        # Validate variant
        try:
            self._validate_variant(variant)
        except ValueError as e:
            return self._create_result(
                status="error",
                logs=[str(e)],
                artifacts=[],
                result={},
                error=str(e),
            )

        # Validate input URL
        url = input_data.strip()
        if not url.startswith("http"):
            return self._create_result(
                status="error",
                logs=["Invalid URL: must start with http:// or https://"],
                artifacts=[],
                result={},
                error="Invalid URL format",
            )

        # Create job for tracking
        job = self.job_store.create(
            workflow_name=f"{self._metadata.id}_v{variant}",
            metadata={"url": url, "variant": variant},
        )
        job_id = job.id

        logs = []
        artifacts = []

        try:
            # Step 1: Scrape the listing URL
            self._log(job_id, f"Scraping URL: {url}")
            logs.append(f"Scraping URL: {url}")

            scrape_tool = self.tool_registry.get_tool("scrape_url")
            if not scrape_tool:
                raise RuntimeError("scrape_url tool not registered")

            scrape_result = scrape_tool.execute(url=url, timeout=10)
            if not scrape_result.success:
                raise RuntimeError(f"Scraping failed: {scrape_result.error}")

            html_content = scrape_result.data.get("content", "")
            self._log(job_id, f"Scraped {len(html_content)} characters of HTML")
            logs.append(f"Successfully scraped {len(html_content)} characters")

            # Step 2: Analyze the HTML to extract structured data
            self._log(job_id, "Analyzing listing data...")
            logs.append("Analyzing listing data...")

            analysis_prompt = self._load_prompt(
                "scrape_analyze.txt", context=html_content
            )

            # Use LLM to analyze
            analysis_response = self.llm_client.complete(
                prompt=analysis_prompt,
                max_tokens=1000,
                temperature=0.3,  # Lower temperature for factual extraction
            )

            # Parse JSON response
            try:
                extracted_data = json.loads(analysis_response)
            except json.JSONDecodeError:
                # If LLM didn't return valid JSON, wrap the response
                extracted_data = {
                    "raw_analysis": analysis_response,
                    "note": "Failed to parse structured JSON from LLM response",
                }

            self._log(job_id, f"Extracted data: {json.dumps(extracted_data, indent=2)}")
            logs.append("Successfully extracted property data")

            # Save extracted data as artifact
            data_artifact_path = self.artifact_manager.save_json(
                job_id=job_id,
                filename="extracted_data.json",
                data=extracted_data,
            )
            artifacts.append(
                {
                    "type": "json",
                    "label": "Extracted Property Data",
                    "path": data_artifact_path,
                }
            )

            # Step 3: Generate ad copy based on variant
            self._log(job_id, f"Generating ad (variant {variant})...")
            logs.append(
                f"Generating ad (variant {variant}: {self._metadata.variants[variant]})..."
            )

            # Select prompt based on variant
            variant_prompts = {
                1: "generate_ad_basic.txt",
                2: "generate_ad_detailed.txt",
                3: "generate_ad_seo.txt",
            }

            prompt_file = variant_prompts[variant]
            ad_prompt = self._load_prompt(
                prompt_file,
                context=json.dumps(extracted_data, indent=2),
            )

            # Generate ad with higher temperature for creativity
            ad_text = self.llm_client.complete(
                prompt=ad_prompt,
                max_tokens=1500,
                temperature=0.7,
            )

            self._log(job_id, f"Generated ad ({len(ad_text)} characters)")
            logs.append(f"Successfully generated ad ({len(ad_text)} characters)")

            # Save ad as artifact
            ad_artifact_path = self.artifact_manager.save_text(
                job_id=job_id,
                filename="generated_ad.txt",
                content=ad_text,
            )
            artifacts.append(
                {
                    "type": "text",
                    "label": "Generated Advertisement",
                    "path": ad_artifact_path,
                }
            )

            # Mark job as complete
            job.status = "COMPLETE"
            self.job_store.update(job_id, job)

            execution_time = time() - start_time
            completed_at = datetime.now()

            self._log(job_id, f"Workflow completed in {execution_time:.2f}s")
            logs.append(f"Workflow completed successfully in {execution_time:.2f}s")

            return self._create_result(
                status="ok",
                logs=logs,
                artifacts=artifacts,
                result={
                    "job_id": job_id,
                    "url": url,
                    "variant": variant,
                    "extracted_data": extracted_data,
                    "ad_text": ad_text,
                },
                execution_time=execution_time,
                started_at=started_at,
                completed_at=completed_at,
            )

        except Exception as e:
            # Handle errors
            error_msg = str(e)
            self._log(job_id, f"ERROR: {error_msg}")
            logs.append(f"Error: {error_msg}")

            # Mark job as failed
            job.status = "FAILED"
            job.error = error_msg
            self.job_store.update(job_id, job)

            execution_time = time() - start_time
            completed_at = datetime.now()

            return self._create_result(
                status="error",
                logs=logs,
                artifacts=artifacts,
                result={"job_id": job_id},
                error=error_msg,
                execution_time=execution_time,
                started_at=started_at,
                completed_at=completed_at,
            )

    def _load_prompt(self, filename: str, **kwargs) -> str:
        """
        Load a prompt template and format it with kwargs.

        Args:
            filename: Prompt file name (e.g., "generate_ad_basic.txt")
            **kwargs: Variables to inject into the template

        Returns:
            Formatted prompt string
        """
        prompts_dir = Path(__file__).parent / "prompts"
        prompt_path = prompts_dir / filename

        if not prompt_path.exists():
            raise FileNotFoundError(f"Prompt template not found: {prompt_path}")

        with open(prompt_path, "r", encoding="utf-8") as f:
            template = f.read()

        # Simple template substitution
        return template.format(**kwargs)
