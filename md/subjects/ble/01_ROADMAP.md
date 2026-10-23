# 🗺️ BLE: Study Roadmap & Learning Units

A structured progression from foundational axioms to independent problem solving.

---

## 🧭 Topic Sequence Chart

```mermaid
flowchart TD
    classDef mastered fill:#2e7d32,stroke:#1b5e20,stroke-width:2px,color:#fff;
    classDef current fill:#f57c00,stroke:#e65100,stroke-width:3px,color:#fff;
    classDef upcoming fill:#37474f,stroke:#263238,stroke-width:1px,color:#cfd8dc;

    M1["1. Physical & Packet Foundations<br/><i>Test packet structure, access address formatting, and basic transmission concepts</i>"]:::current
    M2["2. Advertising & Device Discovery<br/><i>Advertising packet types (ADV_IND, ADV_DIRECT_IND, ADV_NONCONN_IND) and active scanning</i>"]:::upcoming
    M3["3. Link Layer & Connection Management<br/><i>State machine, connection establishment, master management, robustness, and low-power optimizations</i>"]:::upcoming
    M4["4. L2CAP & Signaling Channels<br/><i>Connectionless models, channel multiplexing, and connection parameter update commands</i>"]:::upcoming
    M5["5. Attribute Protocol (ATT) & Database<br/><i>Attribute database structure, handle discovery, permissions, and atomic operations</i>"]:::upcoming
    M6["6. GATT Services & Security Architecture<br/><i>Service-oriented abstraction, peripheral exposure, and AES/CSRK-based connection security</i>"]:::upcoming

    M1 ==>|Current Frontier| M2
    M2 --> M3
    M3 --> M4
    M4 --> M5
    M5 --> M6
```

---

## ✅ Learning Unit Checklists

- [ ] [[lessons/01_physical_packet_foundations|**1. Physical & Packet Foundations**]] 👉 **(Current Focus)**
  - *Concepts:* Test packet structure, access address formatting, and basic transmission concepts
- [ ] [[lessons/02_advertising_device_discovery|**2. Advertising & Device Discovery**]] *(Upcoming)*
  - *Concepts:* Advertising packet types (ADV_IND, ADV_DIRECT_IND, ADV_NONCONN_IND) and active scanning
- [ ] [[lessons/03_link_layer_connection_management|**3. Link Layer & Connection Management**]] *(Upcoming)*
  - *Concepts:* State machine, connection establishment, master management, robustness, and low-power optimizations
- [ ] [[lessons/04_l2cap_signaling_channels|**4. L2CAP & Signaling Channels**]] *(Upcoming)*
  - *Concepts:* Connectionless models, channel multiplexing, and connection parameter update commands
- [ ] [[lessons/05_attribute_protocol_att_database|**5. Attribute Protocol (ATT) & Database**]] *(Upcoming)*
  - *Concepts:* Attribute database structure, handle discovery, permissions, and atomic operations
- [ ] [[lessons/06_gatt_services_security_architecture|**6. GATT Services & Security Architecture**]] *(Upcoming)*
  - *Concepts:* Service-oriented abstraction, peripheral exposure, and AES/CSRK-based connection security

---

- [[00_DASHBOARD|← Back to BLE Hub]] | [[../../00_INDEX_DASHBOARD|Master Hub]]
