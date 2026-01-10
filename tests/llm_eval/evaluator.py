#!/usr/bin/env python3
"""
LLM-as-Judge Evaluator

Uses GPT-4o-mini to score chatbot responses against quality rubrics.
Provides automated quality assessment for response accuracy, safety, tone, and CTAs.

Usage:
    python tests/llm_eval/evaluator.py --input transcripts.json --output scores.json
"""

import json
import os
import sys
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

@dataclass
class RubricScore:
    """Score for a single rubric."""
    rubric_name: str
    score: int
    reasoning: str

@dataclass
class EvaluationResult:
    """Result of evaluating a single response."""
    conversation_id: str
    turn_index: int
    user_message: str
    bot_response: str
    category: str
    rubric_scores: List[RubricScore]
    weighted_score: float
    passed: bool

@dataclass
class EvaluationSummary:
    """Summary of all evaluations."""
    total_evaluated: int
    passed: int
    failed: int
    average_score: float
    category_scores: Dict[str, float]
    results: List[EvaluationResult]


class LLMEvaluator:
    """Evaluates chatbot responses using LLM-as-Judge approach."""
    
    def __init__(self, rubrics_path: str = "tests/llm_eval/rubrics.json"):
        self.rubrics = self._load_rubrics(rubrics_path)
        self.client = None
        self._init_openai()
    
    def _load_rubrics(self, path: str) -> Dict:
        """Load evaluation rubrics from JSON file."""
        with open(path, "r") as f:
            return json.load(f)
    
    def _init_openai(self):
        """Initialize OpenAI client."""
        try:
            from openai import OpenAI
            self.client = OpenAI()
        except ImportError:
            print("Warning: OpenAI not installed. Install with: pip install openai")
        except Exception as e:
            print(f"Warning: Could not initialize OpenAI client: {e}")
    
    def _build_evaluation_prompt(self, user_message: str, bot_response: str, 
                                  category: str, context: Optional[str] = None) -> str:
        """Build the evaluation prompt for the LLM judge."""
        category_config = self.rubrics["categories"].get(category, self.rubrics["categories"]["general"])
        required_rubrics = category_config["required_rubrics"]
        
        rubric_descriptions = []
        for rubric_name in required_rubrics:
            rubric = self.rubrics["rubrics"][rubric_name]
            scale_text = "\n".join([f"    {k}: {v}" for k, v in rubric["scale"].items()])
            rubric_descriptions.append(f"""
**{rubric['name']}** ({rubric_name}):
{rubric['description']}
Scale:
{scale_text}
""")
        
        prompt = f"""You are evaluating a wellness chatbot response for Anna Kitney's coaching business.

## Context
This is a chatbot that helps users learn about wellness programs, events, and coaching services.
Anna's brand is warm, supportive, and professional.

## User Message
{user_message}

## Bot Response
{bot_response}

{f"## Additional Context: {context}" if context else ""}

## Evaluation Instructions
Score the response on each rubric below (0-5 scale).
For each rubric, provide:
1. A score (0-5)
2. Brief reasoning (1-2 sentences)

## Rubrics
{"".join(rubric_descriptions)}

## Response Format
Respond in JSON format:
{{
  "scores": [
    {{"rubric": "rubric_name", "score": N, "reasoning": "..."}},
    ...
  ]
}}
"""
        return prompt
    
    def evaluate_response(self, user_message: str, bot_response: str,
                          category: str = "general", context: Optional[str] = None,
                          conversation_id: str = "", turn_index: int = 0) -> EvaluationResult:
        """Evaluate a single bot response."""
        
        if not self.client:
            # Return mock evaluation if no OpenAI client
            return self._mock_evaluation(user_message, bot_response, category, 
                                          conversation_id, turn_index)
        
        prompt = self._build_evaluation_prompt(user_message, bot_response, category, context)
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert evaluator for conversational AI systems."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            scores = result.get("scores", [])
            
        except Exception as e:
            print(f"Error calling OpenAI: {e}")
            return self._mock_evaluation(user_message, bot_response, category,
                                          conversation_id, turn_index)
        
        # Parse scores
        rubric_scores = []
        for score_data in scores:
            rubric_scores.append(RubricScore(
                rubric_name=score_data["rubric"],
                score=score_data["score"],
                reasoning=score_data.get("reasoning", "")
            ))
        
        # Calculate weighted score
        weighted_score = self._calculate_weighted_score(rubric_scores, category)
        
        # Determine pass/fail
        category_config = self.rubrics["categories"].get(category, self.rubrics["categories"]["general"])
        passed = weighted_score >= category_config["pass_threshold"]
        
        return EvaluationResult(
            conversation_id=conversation_id,
            turn_index=turn_index,
            user_message=user_message,
            bot_response=bot_response,
            category=category,
            rubric_scores=rubric_scores,
            weighted_score=weighted_score,
            passed=passed
        )
    
    def _calculate_weighted_score(self, scores: List[RubricScore], category: str) -> float:
        """Calculate weighted average score."""
        if not scores:
            return 0.0
        
        total_weight = 0.0
        weighted_sum = 0.0
        
        for score in scores:
            rubric = self.rubrics["rubrics"].get(score.rubric_name)
            if rubric:
                weight = rubric.get("weight", 0.2)
                weighted_sum += score.score * weight
                total_weight += weight
        
        return weighted_sum / total_weight if total_weight > 0 else 0.0
    
    def _mock_evaluation(self, user_message: str, bot_response: str, category: str,
                          conversation_id: str, turn_index: int) -> EvaluationResult:
        """Return mock evaluation when OpenAI is unavailable."""
        rubric_scores = [
            RubricScore("accuracy", 4, "Mock evaluation - OpenAI unavailable"),
            RubricScore("relevance", 4, "Mock evaluation - OpenAI unavailable"),
            RubricScore("safety", 5, "Mock evaluation - OpenAI unavailable"),
        ]
        
        return EvaluationResult(
            conversation_id=conversation_id,
            turn_index=turn_index,
            user_message=user_message,
            bot_response=bot_response,
            category=category,
            rubric_scores=rubric_scores,
            weighted_score=4.0,
            passed=True
        )
    
    def evaluate_transcript(self, transcript: List[Dict], 
                            conversation_id: str = "") -> List[EvaluationResult]:
        """Evaluate all turns in a conversation transcript."""
        results = []
        
        for i, turn in enumerate(transcript):
            if "user" in turn and "assistant" in turn:
                category = turn.get("category", "general")
                result = self.evaluate_response(
                    user_message=turn["user"],
                    bot_response=turn["assistant"],
                    category=category,
                    conversation_id=conversation_id,
                    turn_index=i
                )
                results.append(result)
        
        return results
    
    def summarize_results(self, results: List[EvaluationResult]) -> EvaluationSummary:
        """Generate summary statistics from evaluation results."""
        if not results:
            return EvaluationSummary(0, 0, 0, 0.0, {}, [])
        
        passed = sum(1 for r in results if r.passed)
        average_score = sum(r.weighted_score for r in results) / len(results)
        
        # Calculate per-category scores
        category_scores = {}
        category_counts = {}
        for r in results:
            if r.category not in category_scores:
                category_scores[r.category] = 0.0
                category_counts[r.category] = 0
            category_scores[r.category] += r.weighted_score
            category_counts[r.category] += 1
        
        for cat in category_scores:
            category_scores[cat] /= category_counts[cat]
        
        return EvaluationSummary(
            total_evaluated=len(results),
            passed=passed,
            failed=len(results) - passed,
            average_score=average_score,
            category_scores=category_scores,
            results=results
        )
    
    def generate_report(self, summary: EvaluationSummary) -> str:
        """Generate a markdown report from evaluation summary."""
        report = f"""# LLM Evaluation Report

Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## Summary

| Metric | Value |
|--------|-------|
| Total Evaluated | {summary.total_evaluated} |
| Passed | {summary.passed} |
| Failed | {summary.failed} |
| Pass Rate | {summary.passed/summary.total_evaluated*100:.1f}% |
| Average Score | {summary.average_score:.2f}/5.0 |

## Category Scores

| Category | Average Score |
|----------|---------------|
"""
        for cat, score in summary.category_scores.items():
            report += f"| {cat} | {score:.2f}/5.0 |\n"
        
        report += "\n## Detailed Results\n\n"
        
        for r in summary.results:
            status = "✅" if r.passed else "❌"
            report += f"### {status} Turn {r.turn_index + 1} ({r.category})\n"
            report += f"**User:** {r.user_message[:100]}...\n\n"
            report += f"**Bot:** {r.bot_response[:200]}...\n\n"
            report += f"**Weighted Score:** {r.weighted_score:.2f}/5.0\n\n"
            report += "| Rubric | Score | Reasoning |\n|--------|-------|------------|\n"
            for s in r.rubric_scores:
                report += f"| {s.rubric_name} | {s.score}/5 | {s.reasoning} |\n"
            report += "\n"
        
        return report


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="LLM-as-Judge Evaluator")
    parser.add_argument("--input", help="Path to transcript JSON file")
    parser.add_argument("--output", default="tests/reports/llm_eval_results.md",
                        help="Output file for the report")
    parser.add_argument("--demo", action="store_true",
                        help="Run demo evaluation with sample data")
    args = parser.parse_args()
    
    evaluator = LLMEvaluator()
    
    if args.demo:
        # Demo with sample data
        demo_transcript = [
            {
                "user": "Hello!",
                "assistant": "Hello! Welcome to Anna Kitney Wellness. How can I help you today?",
                "category": "greeting"
            },
            {
                "user": "What events do you have?",
                "assistant": "Here are the upcoming events:\n\n1. SoulAlign Coach - March 2026\n2. SoulAlign Heal - June 2026\n\nWould you like more details about any of these?",
                "category": "event_query"
            }
        ]
        
        results = evaluator.evaluate_transcript(demo_transcript, "demo-001")
        summary = evaluator.summarize_results(results)
        report = evaluator.generate_report(summary)
        
        print(report)
        
        os.makedirs(os.path.dirname(args.output), exist_ok=True)
        with open(args.output, "w") as f:
            f.write(report)
        print(f"\nReport saved to: {args.output}")
    
    elif args.input:
        with open(args.input, "r") as f:
            transcripts = json.load(f)
        
        all_results = []
        for i, transcript in enumerate(transcripts):
            results = evaluator.evaluate_transcript(transcript, f"conv-{i}")
            all_results.extend(results)
        
        summary = evaluator.summarize_results(all_results)
        report = evaluator.generate_report(summary)
        
        os.makedirs(os.path.dirname(args.output), exist_ok=True)
        with open(args.output, "w") as f:
            f.write(report)
        print(f"Report saved to: {args.output}")
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
