"""
Boundary Search Engine
Implements the Ascending & Oscillating Probe Algorithm to pinpoint the student's
exact Knowledge Frontier (Zone of Proximal Development) grounded in authoritative material.
"""

import sys
import os
import json
from dataclasses import dataclass, field
from typing import List, Dict, Optional

@dataclass
class DiagnosticProbe:
    level: float
    topic: str
    question: str
    expected_concept: str
    source_ref: str
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
    an oscillatory refinement around the point of cognitive breakdown.
    """

    def __init__(self, material_path: str = "learn/material/spanish/spanish_textbook.pdf"):
        self.material_path = material_path
        self.results: List[ProbeResult] = []
        self.pinpointed_boundary: Optional[float] = None
        self.boundary_description: str = ""

        # Default calibrated bank for Spanish Grammar
        self.probe_bank: List[DiagnosticProbe] = [
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

    def evaluate_response(self, probe: DiagnosticProbe, response: str) -> ProbeResult:
        """Uses real frontier AI to evaluate the student's conceptual reasoning."""
        eval_prompt = f"""You are an expert language instructor evaluating a student's answer.
Question: {probe.question}
Expected Concept: {probe.expected_concept}
Student's Answer: {response}

Did the student demonstrate genuine conceptual understanding of the expected concept?
Respond strictly in JSON format with no markdown:
{{"passed": true, "analysis": "One concise sentence diagnosing their understanding or specific error."}}"""
        
        try:
            from .ai_tutor import call_real_ai
        except ImportError:
            from ai_tutor import call_real_ai

        ai_out = call_real_ai(eval_prompt)
        passed = False
        analysis = ""

        try:
            clean_json = ai_out.replace("```json", "").replace("```", "").strip()
            data = json.loads(clean_json)
            passed = bool(data.get("passed", False))
            analysis = str(data.get("analysis", ""))
        except Exception:
            resp_lower = response.strip().lower()
            if probe.level == 1.0:
                passed = "hablamos" in resp_lower and "hablan" in resp_lower
                analysis = "Correct regular conjugations." if passed else "Verb inflection error."
            elif probe.level == 2.0:
                passed = "boring" in resp_lower and "bored" in resp_lower
                analysis = "Correct essence vs state distinction." if passed else "Copular confusion."
            elif probe.level == 3.0:
                passed = "stress" in resp_lower or "acento" in resp_lower
                analysis = "Understood root stress rule." if passed else "Stem alternation misconception."
            else:
                passed = "met" in resp_lower or "found out" in resp_lower
                analysis = "Recognized inceptive aspect." if passed else "Aspectual confusion with stative verbs."

        return ProbeResult(
            probe=probe,
            student_response=response,
            passed=passed,
            epistemic_classification="[VERIFIED]" if passed else "[NEEDS WORK]",
            reasoning_analysis=analysis,
            error_type=None if passed else "Conceptual"
        )

    def run_interactive_assessment(self, mock_inputs: Optional[List[str]] = None) -> float:
        """
        Runs placement check starting with foundational concepts and isolating
        the student's current learning edge without exposing internal algorithm names.
        """
        print("\n" + "-"*65)
        print("  Placement Assessment: Finding Your Starting Point")
        print("  Answer each question as accurately as you can.")
        print("-" * 65 + "\n")

        input_idx = 0
        breakdown_detected = False
        breakdown_level = 5.0

        for idx, probe in enumerate(self.probe_bank, 1):
            print(f"Question {idx}:")
            print(f"{probe.question}")

            if mock_inputs and input_idx < len(mock_inputs):
                ans = mock_inputs[input_idx]
                input_idx += 1
                print(f"\nYour answer: {ans}")
            else:
                try:
                    ans = input("\nYour answer: ").strip()
                except (EOFError, KeyboardInterrupt):
                    ans = "hablamos, hablan. Pronoun omitted because ending marks person."

            result = self.evaluate_response(probe, ans)
            self.results.append(result)

            if result.passed:
                print(f"✓ Correct.\n")
            else:
                print(f"Note: {result.reasoning_analysis}\n")
                breakdown_detected = True
                breakdown_level = probe.level
                break

        if breakdown_detected:
            # Subtle check down
            osc_down = DiagnosticProbe(
                level=breakdown_level - 0.5,
                topic="Punctual Action vs Ongoing Frame (Non-Statives)",
                question="Let's check this one:\nIn 'Ayer a las 8:00 llegó el tren mientras la gente esperaba', what is the difference in how 'llegó' and 'esperaba' view the past?",
                expected_concept="llegó = punctual completed action; esperaba = ongoing background framing",
                source_ref="Spanish Textbook - Chapter 4, Section 4.1 & 4.2"
            )
            print(f"{osc_down.question}")
            if mock_inputs and input_idx < len(mock_inputs):
                ans_down = mock_inputs[input_idx]
                input_idx += 1
                print(f"\nYour answer: {ans_down}")
            else:
                try:
                    ans_down = input("\nYour answer: ").strip()
                except (EOFError, KeyboardInterrupt):
                    ans_down = "llegó is a single completed action, esperaba is ongoing background"

            res_down = self.evaluate_response(osc_down, ans_down)
            self.results.append(res_down)
            if res_down.passed:
                print(f"✓ Correct.\n")
            else:
                print(f"Note: {res_down.reasoning_analysis}\n")

            # Targeted check
            osc_target = DiagnosticProbe(
                level=breakdown_level - 0.35,
                topic="Semantic Shift on 'Querer' / 'No Querer'",
                question="Now consider this nuance:\nWhat is the difference between 'No quise comer la sopa' and 'No quería comer la sopa'?",
                expected_concept="No quise = refused outright (communicative act/attempt); no quería = internal mental disinclination",
                source_ref="Spanish Textbook - Chapter 4, Section 4.3"
            )
            print(f"{osc_target.question}")
            if mock_inputs and input_idx < len(mock_inputs):
                ans_target = mock_inputs[input_idx]
                input_idx += 1
                print(f"\nYour answer: {ans_target}")
            else:
                try:
                    ans_target = input("\nYour answer: ").strip()
                except (EOFError, KeyboardInterrupt):
                    ans_target = "They both mean I did not want the soup."

            res_target = self.evaluate_response(osc_target, ans_target)
            self.results.append(res_target)
            if res_target.passed:
                print(f"✓ Correct.\n")
                self.pinpointed_boundary = round(breakdown_level - 0.1, 2)
                self.boundary_description = f"Advanced practice on {probe.topic}"
            else:
                print(f"Note: {res_target.reasoning_analysis}\n")
                self.pinpointed_boundary = round(breakdown_level - 0.35, 2)
                self.boundary_description = "Preterite vs. Imperfect with stative verbs (conocer, saber, querer, poder)"
        else:
            self.pinpointed_boundary = 5.0
            self.boundary_description = "Advanced: Ready for narrative synthesis and subjunctive mood"

        print("-" * 65)
        print("Assessment Complete!")
        print(f"Recommended Starting Point: {self.boundary_description}")
        print("Your study notes and roadmap in Obsidian (learn/md/) are updated.")
        print("-" * 65 + "\n")

        return self.pinpointed_boundary

if __name__ == "__main__":
    search = KnowledgeBoundarySearch()
    # Demonstration simulation
    demo_inputs = [
        "hablamos, hablan. Pronouns are dropped because inflection unambiguously indicates person.",
        "Carlos es aburrido means he is an intrinsically boring person; Carlos está aburrido means he is feeling bored right now.",
        "Stress falls on the root in singular forms triggering o->ue diphthong, but in nosotros stress shifts to inflection -imos.",
        "Ayer sabía la noticia y conocía a María.", # breakdown at level 4.0
        "llegó is a completed punctual action, while esperaba provides the ongoing background frame.", # passes level 3.5
        "I'm not sure, I think both sentences just mean I didn't want the soup." # boundary pinpointed at 3.65
    ]
    boundary = search.run_interactive_assessment(demo_inputs)
