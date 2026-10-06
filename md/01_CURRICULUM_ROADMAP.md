# 🗺️ Spanish Grammar Study Roadmap

A structured learning progression from foundational grammar to advanced narrative fluency, based on the course materials in `learn/material/spanish/spanish_textbook.pdf`.

---

## 🧭 Topic Sequence

```mermaid
flowchart TD
    subgraph Prereqs ["Foundations (Mastered)"]
        P1["Present Indicative Regulars (-ar, -er, -ir)"]
        P2["Ser (Essence) vs. Estar (State/Location)"]
        P3["Stem-Vowel Alternations (e->ie, o->ue, e->i)"]
        P1 --> P2 --> P3
    end

    subgraph CurrentFocus ["Current Topic: Past Aspect"]
        F1["Preterite (Completed) vs. Imperfect (Ongoing/Habitual)"]
        F2["Regular Past Endings & Accent Marks"]
        F3["Common Irregular Stems: tuv-, estuv-, pus-, sup-, hic-"]
        F1 --> F2 --> F3
    end

    subgraph NextTopics ["Next: Stative Verbs in Past Tenses"]
        S1["Conocer: 'conocía' (knew) vs. 'conocí' (met)"]
        S2["Saber: 'sabía' (knew) vs. 'supe' (found out)"]
        S3["Querer: 'quería' (wanted) vs. 'quise' (tried/refused)"]
        S4["Poder: 'podía' (capable) vs. 'pude' (managed to)"]
        S1 & S2 & S3 & S4 --> Sint["Contextual Discrimination Practice"]
    end

    subgraph AdvancedTopics ["Advanced: Subjunctive Mood"]
        Sub1["WEIRDO Triggers (Wishes, Emotions, Doubts, Volition)"]
        Sub2["Opposite Vowel Conjugations"]
        Sub3["Assertion vs. Non-Assertion"]
        Sub1 --> Sub2 --> Sub3
    end

    subgraph Composition ["Final: Narrative Composition"]
        T1["Paragraph-Level Storytelling"]
        T2["Mixing Past Tenses Smoothly"]
        T3["Unassisted Writing Challenges"]
        T1 --> T2 --> T3
    end

    Prereqs ==> CurrentFocus
    CurrentFocus ==> NextTopics
    NextTopics ==> AdvancedTopics
    AdvancedTopics ==> Composition

    style CurrentFocus fill:#fff3e0,stroke:#e65100,stroke-width:2px;
    style NextTopics fill:#e8eaf6,stroke:#3f51b5,stroke-width:1px;
    style Composition fill:#e8f5e9,stroke:#2e7d32,stroke-width:1px;
```

---

## 📐 The Geometry of Past Aspect

A helpful visual way to distinguish the two Spanish past tenses:

```
                       THE GEOMETRY OF PAST TENSES
                       ===========================

  PRETERITE (Completed Event)
  ---------------------------
  An action viewed from the OUTSIDE as a finished whole with clear boundaries:
  
         [ Start •====================• End ]
           t1                               t2
     "Ayer hablé con María." (Finished, bounded event)


  IMPERFECT (Ongoing Background / Habit)
  --------------------------------------
  An action viewed from the INSIDE as an ongoing or habitual backdrop:
  
  ... ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ [ MOMENT IN TIME ] ~ ~ ~ ~ ~ ~ ~ ~ ~ ...
                          "Mientras yo leía..."
     (Ongoing stream; boundaries are not the focus)


  COMBINED: An Action Interrupted
  ------------------------------
  The imperfect creates the background; the preterite steps in:

  IMPERFECT (Background):  ══════════════════════════════════════════>
                           "Yo caminaba por el parque..."
                                         ▲
                                         │ (Punctual event)
  PRETERITE (Interruption):        [ ! ME CAÍ ! ]
                                   "cuando me caí."
```

---

## ⚡ Self-Check Milestones

- [x] Conjugate regular -ar, -er, -ir verbs in the present tense without needing pronouns.
- [x] Distinguish *ser listo* (smart) from *estar listo* (ready).
- [ ] Conjugate irregular preterite stems (*tener -> tuve*, *poner -> puse*).
- [ ] Choose between preterite and imperfect when describing an action that interrupts an ongoing activity.
- [ ] Explain the difference between *no quise ir* and *no quería ir*.
- [ ] Form the present subjunctive for irregular verbs (*hacer -> haga*, *tener -> tenga*).
