"""
Meta-Learning & Epistemic Boundary Engine
Continuously monitors cognitive friction, enforces strict ZPD (Zone of Proximal Development) boundaries,
evaluates pedagogical style efficacy, and dynamically adapts teaching methodologies.
"""

import os
import re
from typing import Dict, Any, List, Optional, Tuple

try:
    from .db import StateManager
    from .ai_tutor import call_real_ai
except ImportError:
    from db import StateManager
    from ai_tutor import call_real_ai

# Catalog of evidence-based pedagogical styles tailored for technical mastery
PEDAGOGICAL_STYLES: Dict[str, Dict[str, str]] = {
    "CAUSAL_SCENARIO": {
        "name": "Causal Scenario / Engineering Dilemma",
        "tag": "🛠️ Causal Engineering",
        "description": "Frames concrete design dilemmas and first-principles problems before attaching standard spec terminology.",
        "directive": (
            "PEDAGOGICAL STYLE: CAUSAL SCENARIO / FIRST-PRINCIPLES ENGINEERING.\n"
            "- CRITICAL RULE: NEVER ask the student to recall or guess arbitrary specification terms, token names, or acronyms.\n"
            "- Instead, present a real physical, circuit, or protocol engineering dilemma (e.g. 'Imagine you are designing the host controller and a device sends corrupted packets... how must the bus react?').\n"
            "- Guide the student to deduce the necessary mechanism through first principles.\n"
            "- Only AFTER the functional mechanism is clear, attach the formal specification name to it."
        )
    },
    "FEYNMAN_SYNTHESIS": {
        "name": "Feynman Synthesis / Teach-Back",
        "tag": "🎓 Feynman Teach-Back",
        "description": "Student explains the overarching architecture or packet journey in their own words; tutor validates and fills edge cases.",
        "directive": (
            "PEDAGOGICAL STYLE: FEYNMAN SYNTHESIS / TEACH-BACK.\n"
            "- Instead of quizzing or testing, prompt the student to synthesize the overarching concept or trace a packet's journey in their own words.\n"
            "- Act as an encouraging peer engineer listening to their walkthrough.\n"
            "- Validate their strong intuition, praise accurate mental models, and gently clarify missing links or edge cases without quizzing."
        )
    },
    "MECHANICAL_ANALOGY": {
        "name": "Mechanical / Physical Intuition",
        "tag": "⚙️ Physical Intuition",
        "description": "Bridges complex protocol mechanisms to intuitive real-world physical and mechanical system models.",
        "directive": (
            "PEDAGOGICAL STYLE: MECHANICAL & INTUITIVE ANALOGY.\n"
            "- Before diving into register bits, timing, or protocol states, anchor the concept in a vivid, precise physical or mechanical analogy.\n"
            "- Compare the abstract mechanism to familiar real-world systems (e.g., slotted airport runways for host scheduling, or pipe pressure for bus capacitance).\n"
            "- Check if the intuition makes sense before bridging directly into the hardware spec."
        )
    },
    "REVERSE_TRACE": {
        "name": "Reverse Trace / Step-by-Step Transaction Walkthrough",
        "tag": "🔍 Reverse Trace",
        "description": "Traces a concrete physical transaction, signal transition, or packet timeline from wire to host memory.",
        "directive": (
            "PEDAGOGICAL STYLE: REVERSE TRACE / TRANSACTION WALKTHROUGH.\n"
            "- Walk step-by-step through a concrete timeline or signal trace (e.g., Step 1: Physical line state -> Step 2: Packet token -> Step 3: Buffer FIFO).\n"
            "- Ask the student to predict only the immediate NEXT domino in the sequence based on physics and logic."
        )
    },
    "SOCRATIC_PROBE": {
        "name": "Socratic Boundary Probe",
        "tag": "🎯 Socratic Probe",
        "description": "Targeted diagnostic questions to locate the exact frontier of understanding, with immediate scaffolding.",
        "directive": (
            "PEDAGOGICAL STYLE: SOCRATIC BOUNDARY PROBE.\n"
            "- Ask ONE targeted conceptual question at the calibrated frontier of this active unit.\n"
            "- If the student shows any uncertainty or answers incorrectly, immediately provide scaffolding or a hint—never let them guess in the dark."
        )
    }
}

class MetaLearningEngine:
    def __init__(self, subject: str = "usb", check_in_interval: int = 5):
        self.subject = subject.strip().lower().replace(" ", "_")
        self.check_in_interval = check_in_interval
        self.db = StateManager()

    def get_current_style(self) -> Dict[str, str]:
        """Returns the active pedagogical style details."""
        state = self.db.get_meta_state(self.subject)
        key = state.get("current_style", "CAUSAL_SCENARIO").upper()
        if key not in PEDAGOGICAL_STYLES:
            key = "CAUSAL_SCENARIO"
        info = dict(PEDAGOGICAL_STYLES[key])
        info["key"] = key
        return info

    def set_style(self, style_key: str) -> bool:
        """Explicitly changes the active pedagogical style."""
        key = style_key.strip().upper()
        # Allow partial matches e.g. 'scenario' -> 'CAUSAL_SCENARIO'
        if key not in PEDAGOGICAL_STYLES:
            for k in PEDAGOGICAL_STYLES:
                if key in k:
                    key = k
                    break
        if key in PEDAGOGICAL_STYLES:
            curr = self.db.get_meta_state(self.subject)
            self.db.save_meta_state(
                self.subject,
                current_style=key,
                friction_count=0,
                turn_count=curr.get("turn_count", 0),
                last_assessment=f"Style manually set to {PEDAGOGICAL_STYLES[key]['name']}"
            )
            return True
        return False

    def list_styles(self) -> Dict[str, Dict[str, str]]:
        """Returns all available pedagogical styles."""
        return PEDAGOGICAL_STYLES

    def detect_friction(self, user_msg: str) -> bool:
        """Detects whether the student's message indicates cognitive friction or guessing."""
        text = user_msg.lower().strip()
        patterns = [
            r"\b(idk|i don'?t know|no idea|not sure|dont know|dunno|have no clue|no clue)\b",
            r"\b(guessing game|guessing|stop guessing|step back|outside of my knowledge|havent read|haven'?t read)\b",
            r"\b(can you give me a hint|give me a hint|hint\?)\b",
            r"\b(im lost|confused|too advanced|dont understand)\b"
        ]
        for p in patterns:
            if re.search(p, text):
                return True
        return False

    def detect_saturation(self, user_msg: str) -> bool:
        """Detects whether the student or dialogue indicates circularity/repetition or unit saturation."""
        text = user_msg.lower().strip()
        patterns = [
            r"(circles|in circles|round in circles|going around in circles)",
            r"(asked .*before|already asked|already answered|repeat|repeating|repeated)",
            r"(when to stop|stop asking|doesnt know when to stop|doesn'?t know when to stop)",
            r"(redundant|circular|looping|loop|going around in circles)"
        ]
        for p in patterns:
            if re.search(p, text):
                return True
        return False

    def advance_frontier(
        self,
        current_unit_idx: int,
        modules: List[Tuple[str, str]]
    ) -> Tuple[float, str]:
        """Advances student frontier level, updates curriculum mastery status, and syncs Obsidian."""
        new_level = float(current_unit_idx + 2)
        curr_title = modules[current_unit_idx][0] if current_unit_idx < len(modules) else f"Unit {current_unit_idx + 1}"
        next_title = modules[current_unit_idx + 1][0] if current_unit_idx + 1 < len(modules) else "Course Completed"

        self.db.set_subject_boundary(self.subject, new_level, f"Mastered {curr_title}")
        self.db.save_curriculum_modules(self.subject, modules, new_level)
        self.db.sync_to_obsidian(self.subject)
        return new_level, next_title

    def get_zpd_boundary_directive(
        self,
        active_unit_idx: int,
        active_unit_title: str,
        modules: List[Tuple[str, str]],
        boundary_level: float
    ) -> str:
        """
        Generates strict Zone of Proximal Development (ZPD) prompt directives
        preventing the model from quizzing on unintroduced downstream units or arbitrary trivia.
        """
        future_units = [m[0] for i, m in enumerate(modules) if i > active_unit_idx]
        future_warning = ""
        if future_units:
            future_warning = (
                f"\nFORBIDDEN TOPICS (DOWNSTREAM UNITS NOT YET COVERED BY STUDENT):\n"
                f"The following units have NOT been read or mastered by the student yet:\n"
                + "\n".join(f"  • {u}" for u in future_units) + "\n"
                f"STRICT DIRECTIVE: You are FORBIDDEN from quizzing, testing, or expecting knowledge of any specific mechanisms, tokens, or formulas from these future units!\n"
            )

        return (
            f"=== ZONE OF PROXIMAL DEVELOPMENT (ZPD) BOUNDARY ENFORCEMENT ===\n"
            f"- Current Active Unit: {active_unit_title} (Unit {active_unit_idx + 1} of {len(modules)})\n"
            f"- Calibrated Frontier Level: Level {boundary_level:.2f}\n"
            f"{future_warning}\n"
            f"STRICT PEDAGOGICAL BOUNDARY RULES:\n"
            f"1. Stay strictly anchored to the core conceptual territory of {active_unit_title}.\n"
            f"2. NO REPETITION / CIRCULAR QUESTIONS: Never re-ask concepts the student has already correctly answered (e.g. speed detection resistors, star topology, 4 transfer types, host-polled model).\n"
            f"3. UNIT MASTERY & STOPPING CRITERIA: When the student has demonstrated sound understanding of the active unit's core mechanisms, DO NOT keep generating more questions on the same unit. Instead, declare the unit mastered, celebrate their progress, and ask if they are ready to pause or advance to the next unit!\n"
            f"4. NO NOMENCLATURE GUESSING GAMES: Never quiz the student on arbitrary spec acronyms, standard request names (e.g. SetInterface, bAlternateSetting), or future packet types.\n"
            f"5. If the student answers 'idk' or shows uncertainty, IMMEDIATELY explain the first-principles reason clearly in 1-2 sentences. Never leave them in the dark."
        )

    def get_style_directive(self) -> str:
        """Returns the prompt directive for the active pedagogical style."""
        style = self.get_current_style()
        return style.get("directive", PEDAGOGICAL_STYLES["CAUSAL_SCENARIO"]["directive"])

    def record_turn_and_check(
        self,
        user_msg: str,
        tutor_msg: str,
        history: List[Dict[str, str]],
        active_unit: str = "Unit 1"
    ) -> Optional[Dict[str, Any]]:
        """
        Records a dialogue turn, updates friction metrics, and executes a
        periodic or friction-triggered meta-learning assessment.
        """
        state = self.db.get_meta_state(self.subject)
        curr_turn = state.get("turn_count", 0) + 1
        curr_friction = state.get("friction_count", 0)
        curr_style = state.get("current_style", "CAUSAL_SCENARIO")

        is_saturation = self.detect_saturation(user_msg)
        is_friction = self.detect_friction(user_msg)
        if is_friction:
            curr_friction += 1

        if is_saturation:
            # Immediate Concept Saturation & Unit Mastery Trigger!
            assessment = {
                "status": "🏆 Unit Mastery & Concept Saturation Detected",
                "diagnosis": f"All fundamental pillars of {active_unit} have been demonstrated. Repeated questions detected.",
                "active_style": PEDAGOGICAL_STYLES.get(curr_style, {}).get("name", curr_style),
                "recommended_style": "FEYNMAN_SYNTHESIS",
                "recommended_key": "FEYNMAN_SYNTHESIS",
                "message": (
                    f"You've fully mastered all core concepts of **{active_unit}**! "
                    f"The tutor was looping in circles because you've successfully verified every architecture topic in this unit. "
                    f"You are officially ready to advance to the next unit!"
                ),
                "is_saturation": True,
                "style_changed": False,
                "turn": curr_turn
            }
            self.db.save_meta_state(
                self.subject,
                current_style=curr_style,
                friction_count=0,
                turn_count=curr_turn,
                last_assessment=assessment["status"]
            )
            return assessment

        # Check triggers:
        # 1. Friction threshold hit (2 or more recent friction signals)
        # 2. Periodic cadence (every N turns)
        should_assess = (curr_friction >= 2) or (curr_turn % self.check_in_interval == 0)

        if not should_assess:
            self.db.save_meta_state(
                self.subject,
                current_style=curr_style,
                friction_count=curr_friction,
                turn_count=curr_turn,
                last_assessment=state.get("last_assessment", "")
            )
            return None

        # Execute Meta-Learning Assessment
        assessment = self._evaluate_epistemic_flow(
            history=history,
            active_unit=active_unit,
            curr_style=curr_style,
            is_friction=curr_friction >= 2,
            turn_count=curr_turn
        )

        # Enact style switch if friction was caused by nomenclature interrogation
        new_style = curr_style
        style_changed = False
        if curr_friction >= 2 and curr_style in ["SOCRATIC_PROBE", "REVERSE_TRACE"]:
            new_style = "CAUSAL_SCENARIO"
            style_changed = True
        elif curr_friction >= 2 and curr_style == "CAUSAL_SCENARIO":
            new_style = "FEYNMAN_SYNTHESIS"
            style_changed = True

        self.db.save_meta_state(
            self.subject,
            current_style=new_style,
            friction_count=0,  # Reset friction counter after adaptation
            turn_count=curr_turn,
            last_assessment=assessment.get("summary", "")
        )

        assessment["style_changed"] = style_changed
        assessment["new_style"] = new_style
        assessment["turn"] = curr_turn
        return assessment

    def _evaluate_epistemic_flow(
        self,
        history: List[Dict[str, str]],
        active_unit: str,
        curr_style: str,
        is_friction: bool,
        turn_count: int
    ) -> Dict[str, Any]:
        """Evaluates epistemic health and formulates pedagogical adaptation."""
        curr_info = PEDAGOGICAL_STYLES.get(curr_style, PEDAGOGICAL_STYLES["CAUSAL_SCENARIO"])

        if is_friction:
            status = "⚡ Cognitive Friction Detected"
            diagnosis = "The session hit friction on arbitrary spec nomenclature and guessing questions."
            recommended_style = "CAUSAL_SCENARIO" if curr_style != "CAUSAL_SCENARIO" else "FEYNMAN_SYNTHESIS"
            rec_info = PEDAGOGICAL_STYLES[recommended_style]
            message = (
                f"We noticed friction around specific protocol vocabulary or ungrounded questions. "
                f"Switching approach to **{rec_info['name']}**—we'll present the engineering dilemma first "
                f"so the mechanisms make intuitive physical sense before naming them."
            )
        else:
            status = "✨ Optimal Zone of Proximal Development (ZPD)"
            diagnosis = f"Good back-and-forth flow. Concepts in {active_unit} are consolidating solidly."
            recommended_style = curr_style
            message = (
                f"Current pace is well-calibrated. Core mental models are locking in without guessing. "
                f"Continuing with **{curr_info['name']}**."
            )

        return {
            "status": status,
            "diagnosis": diagnosis,
            "active_style": curr_info["name"],
            "recommended_style": PEDAGOGICAL_STYLES[recommended_style]["name"],
            "recommended_key": recommended_style,
            "message": message,
            "summary": f"Turn {turn_count}: {status} - Recommended {recommended_style}"
        }

    def run_explicit_assessment(self, history: List[Dict[str, str]], active_unit: str) -> Dict[str, Any]:
        """Runs a complete meta-learning diagnosis on request (e.g. /meta)."""
        state = self.db.get_meta_state(self.subject)
        curr_style = state.get("current_style", "CAUSAL_SCENARIO")
        curr_turn = state.get("turn_count", 0)

        # Detect total friction occurrences in recent history
        frictions = [m for m in history if m.get("role") == "user" and self.detect_friction(m.get("content", ""))]
        friction_rate = len(frictions) / max(1, len([m for m in history if m.get("role") == "user"]))

        if friction_rate > 0.3:
            status = "⚠️ Nomenclature / Interrogation Friction"
            rec_style = "CAUSAL_SCENARIO"
            action = "Shift to first-principles design dilemmas; eliminate trivia recall."
        elif friction_rate > 0.15:
            status = "⚖️ Moderate Challenge Frontier"
            rec_style = "FEYNMAN_SYNTHESIS"
            action = "Encourage student teach-back to solidify structural connections."
        else:
            status = "🎯 Fluent Schema Consolidation"
            rec_style = curr_style
            action = "Pace is optimal. Continue current trajectory to unit mastery."

        return {
            "status": status,
            "turn_count": curr_turn,
            "active_unit": active_unit,
            "active_style": PEDAGOGICAL_STYLES.get(curr_style, {}).get("name", curr_style),
            "recommended_style": PEDAGOGICAL_STYLES.get(rec_style, {}).get("name", rec_style),
            "action": action,
            "friction_events": len(frictions)
        }
