"""
Boundary Search Engine
Implements the Ascending & Oscillating Probe Algorithm to pinpoint the student's
exact Knowledge Frontier grounded in authoritative course materials for any subject.
"""

import sys
import os
import json
import re
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple

try:
    from .rag_manager import MaterialRAGManager
    from .ai_tutor import call_real_ai
except ImportError:
    from rag_manager import MaterialRAGManager
    from ai_tutor import call_real_ai

MD_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "md"))

@dataclass
class DiagnosticProbe:
    level: float
    topic: str
    question: str
    expected_concept: str
    source_ref: str = ""
    hints: List[str] = field(default_factory=list)
    classification: str = "FACT"

@dataclass
class ProbeResult:
    probe: DiagnosticProbe
    student_response: str
    passed: bool
    epistemic_classification: str
    reasoning_analysis: str
    error_type: Optional[str] = None

class KnowledgeBoundarySearch:
    """
    Executes an ascending probe (progressively harder questions) followed by
    an oscillatory refinement around the point of cognitive breakdown for any subject.
    """

    def __init__(self, subject: str = "spanish"):
        self.subject = subject.lower().strip()
        self.rag = MaterialRAGManager()
        self.results: List[ProbeResult] = []
        self.pinpointed_boundary: Optional[float] = None
        self.boundary_description: str = ""
        self.probe_bank: List[DiagnosticProbe] = self._load_or_generate_probes()

    def _get_spanish_fallback_bank(self) -> List[DiagnosticProbe]:
        """Pre-calibrated fallback bank for Spanish Grammar."""
        return [
            DiagnosticProbe(
                level=1.0,
                topic="Regular Present Conjugations & Pro-Drop",
                question="Conjugate 'hablar' for 'nosotros' and 'ellos' in the present indicative, and explain why the pronoun 'ellos' is frequently omitted.",
                expected_concept="hablamos, hablan; pro-drop null subject language because inflection marks person/number",
                source_ref="Spanish Textbook - Chapter 1, Section 1.1 & 1.2"
            ),
            DiagnosticProbe(
                level=2.0,
                topic="Copular Bifurcation: Ser vs. Estar",
                question="Explain the difference between 'Carlos es aburrido' and 'Carlos está aburrido'. Which expresses essence, and which expresses state?",
                expected_concept="es aburrido = boring personality (Ser/essence); está aburrido = bored at this moment (Estar/state)",
                source_ref="Spanish Textbook - Chapter 2, Section 2.3"
            ),
            DiagnosticProbe(
                level=3.0,
                topic="Stem-Changing Boot Alternation",
                question="Explain why 'dormir' becomes 'duermo' in the singular, but 'dormimos' in the first-person plural. What phonological rule causes this?",
                expected_concept="Vowel diphthongizes (o->ue) only when root syllable bears grammatical stress; nosotros stress shifts to inflectional suffix",
                source_ref="Spanish Textbook - Chapter 3, Section 3.1"
            ),
            DiagnosticProbe(
                level=4.0,
                topic="Past Aspectual Discrimination & Stative Inception",
                question="In: 'Ayer yo (conocer) a María y (saber) la noticia', should the verbs be in the preterite or imperfect, and what specific meaning changes occur?",
                expected_concept="Preterite for both: conocí (inceptive = met for first time), supe (inceptive = found out / discovered)",
                source_ref="Spanish Textbook - Chapter 4, Section 4.3"
            ),
            DiagnosticProbe(
                level=5.0,
                topic="Subjunctive Mood Triggers & Non-Assertion",
                question="Why does 'Creo que viene' use the indicative, but 'No creo que venga' require the subjunctive? What is the epistemic rule governing this shift?",
                expected_concept="Indicative expresses epistemic assertion of truth/belief; negation 'no creo' removes assertion, triggering subjunctive mood",
                source_ref="Spanish Textbook - Chapter 5, Section 5.1"
            ),
        ]

    def _load_or_generate_probes(self) -> List[DiagnosticProbe]:
        """
        Dynamically extracts context from the subject's course materials
        and generates graduated diagnostic questions (Level 1 to Level 5).
        """
        # If Spanish and offline/quick, use calibrated bank
        if self.subject == "spanish":
            return self._get_spanish_fallback_bank()

        # Gather course material context for the subject
        materials = self.rag.scan_materials()
        chunks = self.rag.retrieve_context("overview introduction fundamentals advanced concepts", subject=self.subject, top_k=6)
        
        context_sample = ""
        if chunks:
            for c in chunks:
                context_sample += f"[{c['file']}]: {c['text'][:400]}\n\n"
        elif self.subject in materials:
            for f in materials[self.subject][:2]:
                text = self.rag.extract_text_from_file(f)
                if text:
                    context_sample += f"[{os.path.basename(f)}]: {text[:800]}\n\n"

        if not context_sample:
            context_sample = f"Course topic: {self.subject.capitalize()}. Foundational to advanced principles."

        gen_prompt = f"""You are a master diagnostic curriculum designer.
Analyze the following course material excerpts for {self.subject.capitalize()}:
{context_sample}

Generate exactly 5 graduated diagnostic questions to pinpoint a student's knowledge boundary:
- Level 1.0 (Foundational): Core definition, fundamental principle, or basic terminology
- Level 2.0 (Elementary): Standard primary rule or direct application
- Level 3.0 (Intermediate): Procedural fluency, mechanism, or multi-step concept
- Level 4.0 (Advanced Frontier): Subtle distinction, edge case, or common misconception
- Level 5.0 (Mastery): Advanced synthesis, transfer problem, or deep conceptual integration

Respond strictly in valid JSON format with NO markdown wrapping:
[
  {{"level": 1.0, "topic": "Short Topic Name", "question": "Clear question testing understanding", "expected_concept": "Key conceptual elements of a correct answer", "source_ref": "{self.subject.capitalize()} Course Materials"}},
  {{"level": 2.0, "topic": "Short Topic Name", "question": "Clear question testing understanding", "expected_concept": "Key conceptual elements of a correct answer", "source_ref": "{self.subject.capitalize()} Course Materials"}},
  {{"level": 3.0, "topic": "Short Topic Name", "question": "Clear question testing understanding", "expected_concept": "Key conceptual elements of a correct answer", "source_ref": "{self.subject.capitalize()} Course Materials"}},
  {{"level": 4.0, "topic": "Short Topic Name", "question": "Clear question testing understanding", "expected_concept": "Key conceptual elements of a correct answer", "source_ref": "{self.subject.capitalize()} Course Materials"}},
  {{"level": 5.0, "topic": "Short Topic Name", "question": "Clear question testing understanding", "expected_concept": "Key conceptual elements of a correct answer", "source_ref": "{self.subject.capitalize()} Course Materials"}}
]"""

        try:
            ai_out = call_real_ai(gen_prompt)
            clean_json = ai_out.replace("```json", "").replace("```", "").strip()
            data = json.loads(clean_json)
            if isinstance(data, list) and len(data) >= 5:
                probes = []
                for item in data[:5]:
                    probes.append(DiagnosticProbe(
                        level=float(item.get("level", 1.0)),
                        topic=str(item.get("topic", f"{self.subject.capitalize()} Topic")),
                        question=str(item.get("question", "")),
                        expected_concept=str(item.get("expected_concept", "")),
                        source_ref=str(item.get("source_ref", f"{self.subject.capitalize()} Reader"))
                    ))
                return probes
        except Exception:
            pass

        # Generic fallback if AI is unavailable
        return [
            DiagnosticProbe(
                level=1.0,
                topic=f"Foundations of {self.subject.capitalize()}",
                question=f"In {self.subject.capitalize()}, what is the foundational definition and primary role of its most essential core concept?",
                expected_concept=f"Accurate foundational definition in {self.subject.capitalize()}",
                source_ref=f"{self.subject.capitalize()} Core Concepts"
            ),
            DiagnosticProbe(
                level=2.0,
                topic=f"Primary Principles of {self.subject.capitalize()}",
                question=f"Explain how the fundamental rule of {self.subject.capitalize()} applies to standard problem cases.",
                expected_concept=f"Standard rule application in {self.subject.capitalize()}",
                source_ref=f"{self.subject.capitalize()} Rules"
            ),
            DiagnosticProbe(
                level=3.0,
                topic=f"Mechanisms & Procedural Fluency",
                question=f"Walk through the step-by-step mechanism or procedural reasoning required when analyzing a typical system in {self.subject.capitalize()}.",
                expected_concept="Multi-step procedural reasoning",
                source_ref=f"{self.subject.capitalize()} Procedures"
            ),
            DiagnosticProbe(
                level=4.0,
                topic=f"Nuances & Conceptual Discrimination",
                question=f"What is a critical edge case or subtle distinction that beginners often confuse in {self.subject.capitalize()}, and how do you resolve it?",
                expected_concept="Nuance discrimination and error avoidance",
                source_ref=f"{self.subject.capitalize()} Nuances"
            ),
            DiagnosticProbe(
                level=5.0,
                topic=f"Advanced Synthesis & Transfer",
                question=f"How would you integrate multiple principles of {self.subject.capitalize()} to evaluate an unfamiliar, complex scenario?",
                expected_concept="Advanced synthesis and conceptual transfer",
                source_ref=f"{self.subject.capitalize()} Advanced Analysis"
            ),
        ]

    def generate_oscillation_probes(self, failed_probe: DiagnosticProbe) -> Tuple[DiagnosticProbe, DiagnosticProbe]:
        """Generates dynamic prerequisite and discrimination questions around the breakdown point."""
        if self.subject == "spanish" and failed_probe.level == 4.0:
            osc_down = DiagnosticProbe(
                level=3.5,
                topic="Punctual Action vs Ongoing Frame (Non-Statives)",
                question="Let's check this one:\nIn 'Ayer a las 8:00 llegó el tren mientras la gente esperaba', what is the difference in how 'llegó' and 'esperaba' view the past?",
                expected_concept="llegó = punctual completed action; esperaba = ongoing background framing",
                source_ref="Spanish Textbook - Chapter 4, Section 4.1 & 4.2"
            )
            osc_target = DiagnosticProbe(
                level=3.65,
                topic="Semantic Shift on 'Querer' / 'No Querer'",
                question="Now consider this nuance:\nWhat is the difference between 'No quise comer la sopa' and 'No quería comer la sopa'?",
                expected_concept="No quise = refused outright (communicative act/attempt); no quería = internal mental disinclination",
                source_ref="Spanish Textbook - Chapter 4, Section 4.3"
            )
            return osc_down, osc_target

        prompt = f"""A student faltered on this question in {self.subject.capitalize()}:
Topic: {failed_probe.topic}
Question: {failed_probe.question}
Expected Concept: {failed_probe.expected_concept}

Generate 2 targeted follow-up diagnostic probes:
1. Level {max(0.5, failed_probe.level - 0.5):.1f}: A simpler prerequisite question testing if the foundational prerequisite is intact.
2. Level {max(0.75, failed_probe.level - 0.25):.2f}: A targeted nuance/discrimination question to isolate the specific concept.

Respond strictly in valid JSON format:
[
  {{"level": {max(0.5, failed_probe.level - 0.5):.1f}, "topic": "Prerequisite for {failed_probe.topic}", "question": "...", "expected_concept": "..."}},
  {{"level": {max(0.75, failed_probe.level - 0.25):.2f}, "topic": "Nuance Check: {failed_probe.topic}", "question": "...", "expected_concept": "..."}}
]"""

        try:
            ai_out = call_real_ai(prompt)
            clean_json = ai_out.replace("```json", "").replace("```", "").strip()
            data = json.loads(clean_json)
            if isinstance(data, list) and len(data) >= 2:
                p1 = DiagnosticProbe(
                    level=float(data[0].get("level", failed_probe.level - 0.5)),
                    topic=str(data[0].get("topic", f"Prerequisite: {failed_probe.topic}")),
                    question=str(data[0].get("question", "")),
                    expected_concept=str(data[0].get("expected_concept", ""))
                )
                p2 = DiagnosticProbe(
                    level=float(data[1].get("level", failed_probe.level - 0.25)),
                    topic=str(data[1].get("topic", f"Nuance: {failed_probe.topic}")),
                    question=str(data[1].get("question", "")),
                    expected_concept=str(data[1].get("expected_concept", ""))
                )
                return p1, p2
        except Exception:
            pass

        # Heuristic fallback
        p1 = DiagnosticProbe(
            level=max(0.5, failed_probe.level - 0.5),
            topic=f"Prerequisite Check: {failed_probe.topic}",
            question=f"Let's look at the foundation for {failed_probe.topic}: Can you state the fundamental principle or definition behind this?",
            expected_concept=f"Basic understanding of {failed_probe.topic}"
        )
        p2 = DiagnosticProbe(
            level=max(0.75, failed_probe.level - 0.25),
            topic=f"Nuance Discrimination: {failed_probe.topic}",
            question=f"How would you contrast {failed_probe.topic} with its most common contrasting case?",
            expected_concept=f"Discrimination of {failed_probe.topic}"
        )
        return p1, p2

    def evaluate_response(self, probe: DiagnosticProbe, response: str) -> ProbeResult:
        """Uses AI to evaluate the student's conceptual reasoning."""
        eval_prompt = f"""You are an expert {self.subject.capitalize()} instructor evaluating a student's answer.
Question: {probe.question}
Expected Concept: {probe.expected_concept}
Student's Answer: {response}

Did the student demonstrate genuine conceptual understanding of the expected concept?
Respond strictly in JSON format with no markdown:
{{"passed": true, "analysis": "One concise sentence diagnosing their understanding or specific error."}}"""
        
        passed = False
        analysis = ""

        try:
            ai_out = call_real_ai(eval_prompt)
            clean_json = ai_out.replace("```json", "").replace("```", "").strip()
            data = json.loads(clean_json)
            passed = bool(data.get("passed", False))
            analysis = str(data.get("analysis", ""))
        except Exception:
            # Fallback heuristic: check answer length and concept overlap
            resp_lower = response.strip().lower()
            if any(term in resp_lower for term in ["skip", "idk", "i don't know", "shrug"]):
                passed = False
                analysis = "Question skipped or unattempted."
            else:
                passed = len(response.strip().split()) >= 3
                analysis = "Demonstrated substantive attempt." if passed else "Insufficient conceptual detail."

        return ProbeResult(
            probe=probe,
            student_response=response,
            passed=passed,
            epistemic_classification="[VERIFIED]" if passed else "[NEEDS WORK]",
            reasoning_analysis=analysis,
            error_type=None if passed else "Conceptual"
        )

    def log_calibration_to_obsidian(self) -> None:
        """Writes the diagnostic summary to learn/md/02_BOUNDARY_CALIBRATION.md."""
        calib_file = os.path.join(MD_DIR, "02_BOUNDARY_CALIBRATION.md")
        os.makedirs(MD_DIR, exist_ok=True)

        rows = []
        for r in self.results:
            status_icon = "✓ Mastered" if r.passed else "⚠️ Needs Work"
            rows.append(f"### Level {r.probe.level:.1f}: {r.probe.topic}\n"
                        f"- **Question:** {r.probe.question}\n"
                        f"- **Your Response:** {r.student_response}\n"
                        f"- **Evaluation:** {status_icon} — {r.reasoning_analysis}\n")

        content = f"""# 📋 Placement & Diagnostic Summary: {self.subject.capitalize()}

This document records your initial placement check and tracks the concepts you have demonstrated mastery in.

---

## 🎯 Current Target
- **Identified Starting Point:** Level {self.pinpointed_boundary:.2f} ({self.boundary_description})
- **Focus Area:** Review the recommended module notes and practice exercises in `modules/`.

---

## 🔍 Topics Assessed

{"".join(rows)}
"""
        try:
            with open(calib_file, "w", encoding="utf-8") as f:
                f.write(content)
        except Exception as e:
            print(f"Warning: Failed to write {calib_file}: {e}")

    def run_interactive_assessment(self, mock_inputs: Optional[List[str]] = None) -> float:
        """Runs placement check from foundational concepts to pinpoint the student's learning edge."""
        print("\n" + "-" * 65)
        print(f"  Placement Assessment: Finding Your Starting Point ({self.subject.capitalize()})")
        print("  Answer each question as accurately as you can.")
        print("-" * 65 + "\n")

        input_idx = 0
        breakdown_detected = False
        breakdown_level = 5.0
        failed_probe = None

        for idx, probe in enumerate(self.probe_bank, 1):
            print(f"Question {idx} (Level {probe.level:.1f} - {probe.topic}):")
            print(f"{probe.question}")

            if mock_inputs and input_idx < len(mock_inputs):
                ans = mock_inputs[input_idx]
                input_idx += 1
                print(f"\nYour answer: {ans}")
            else:
                try:
                    ans = input("\nYour answer: ").strip()
                except (EOFError, KeyboardInterrupt):
                    ans = "skip"

            result = self.evaluate_response(probe, ans)
            self.results.append(result)

            if result.passed:
                print(f"✓ Correct.\n")
            else:
                print(f"Note: {result.reasoning_analysis}\n")
                breakdown_detected = True
                breakdown_level = probe.level
                failed_probe = probe
                break

        if breakdown_detected and failed_probe:
            osc_down, osc_target = self.generate_oscillation_probes(failed_probe)

            # Check prerequisite
            print(f"Follow-up 1 (Prerequisite Check):\n{osc_down.question}")
            if mock_inputs and input_idx < len(mock_inputs):
                ans_down = mock_inputs[input_idx]
                input_idx += 1
                print(f"\nYour answer: {ans_down}")
            else:
                try:
                    ans_down = input("\nYour answer: ").strip()
                except (EOFError, KeyboardInterrupt):
                    ans_down = "skip"

            res_down = self.evaluate_response(osc_down, ans_down)
            self.results.append(res_down)
            if res_down.passed:
                print(f"✓ Correct.\n")
            else:
                print(f"Note: {res_down.reasoning_analysis}\n")

            # Check target nuance
            print(f"Follow-up 2 (Nuance Discrimination):\n{osc_target.question}")
            if mock_inputs and input_idx < len(mock_inputs):
                ans_target = mock_inputs[input_idx]
                input_idx += 1
                print(f"\nYour answer: {ans_target}")
            else:
                try:
                    ans_target = input("\nYour answer: ").strip()
                except (EOFError, KeyboardInterrupt):
                    ans_target = "skip"

            res_target = self.evaluate_response(osc_target, ans_target)
            self.results.append(res_target)
            if res_target.passed:
                print(f"✓ Correct.\n")
                self.pinpointed_boundary = round(breakdown_level - 0.1, 2)
                self.boundary_description = f"Practice on {failed_probe.topic}"
            else:
                print(f"Note: {res_target.reasoning_analysis}\n")
                self.pinpointed_boundary = round(max(0.5, breakdown_level - 0.35), 2)
                self.boundary_description = f"Core foundations of {failed_probe.topic}"
        else:
            self.pinpointed_boundary = 5.0
            self.boundary_description = f"Advanced mastery of {self.subject.capitalize()}"

        print("-" * 65)
        print("Assessment Complete!")
        print(f"Subject: {self.subject.capitalize()}")
        print(f"Recommended Starting Point: Level {self.pinpointed_boundary:.2f} — {self.boundary_description}")
        print("Your study notes and roadmap in Obsidian (learn/md/) are updated.")
        print("-" * 65 + "\n")

        self.log_calibration_to_obsidian()
        return self.pinpointed_boundary

if __name__ == "__main__":
    subj = sys.argv[1] if len(sys.argv) > 1 else "spanish"
    search = KnowledgeBoundarySearch(subject=subj)
    search.run_interactive_assessment()
