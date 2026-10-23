# 🗺️ USB: Study Roadmap & Learning Units

A structured progression from foundational axioms to independent problem solving.

---

## 🧭 Topic Sequence Chart

```mermaid
flowchart TD
    classDef mastered fill:#2e7d32,stroke:#1b5e20,stroke-width:2px,color:#fff;
    classDef current fill:#f57c00,stroke:#e65100,stroke-width:3px,color:#fff;
    classDef upcoming fill:#37474f,stroke:#263238,stroke-width:1px,color:#cfd8dc;

    M1["1. USB Fundamentals & Terminology<br/><i>Essential definitions, topology, and physical signals</i>"]:::current
    M2["2. Architectural Overview & Physical Layer<br/><i>Hardware design, PHYs, and electrical signaling</i>"]:::upcoming
    M3["3. USB Data Flow Model<br/><i>Endpoints, pipes, transfer types, and bus scheduling</i>"]:::upcoming
    M4["4. USB Device Framework<br/><i>Standard descriptors, enumeration process, and device states</i>"]:::upcoming
    M5["5. Host Hardware & Software Architecture<br/><i>Host controller operation and driver stacks</i>"]:::upcoming
    M6["6. Practical Debugging & Protocol Analysis<br/><i>Wireshark/USB analyzer decoding and packet validation</i>"]:::upcoming

    M1 ==>|Current Frontier| M2
    M2 --> M3
    M3 --> M4
    M4 --> M5
    M5 --> M6
```

---

## ✅ Learning Unit Checklists

- [ ] [[lessons/01_usb_fundamentals_terminology|**1. USB Fundamentals & Terminology**]] 👉 **(Current Focus)**
  - *Concepts:* Essential definitions, topology, and physical signals
- [ ] [[lessons/02_architectural_overview_physical_layer|**2. Architectural Overview & Physical Layer**]] *(Upcoming)*
  - *Concepts:* Hardware design, PHYs, and electrical signaling
- [ ] [[lessons/03_usb_data_flow_model|**3. USB Data Flow Model**]] *(Upcoming)*
  - *Concepts:* Endpoints, pipes, transfer types, and bus scheduling
- [ ] [[lessons/04_usb_device_framework|**4. USB Device Framework**]] *(Upcoming)*
  - *Concepts:* Standard descriptors, enumeration process, and device states
- [ ] [[lessons/05_host_hardware_software_architecture|**5. Host Hardware & Software Architecture**]] *(Upcoming)*
  - *Concepts:* Host controller operation and driver stacks
- [ ] [[lessons/06_practical_debugging_protocol_analysis|**6. Practical Debugging & Protocol Analysis**]] *(Upcoming)*
  - *Concepts:* Wireshark/USB analyzer decoding and packet validation

---

- [[00_DASHBOARD|← Back to USB Hub]] | [[../../00_INDEX_DASHBOARD|Master Hub]]
