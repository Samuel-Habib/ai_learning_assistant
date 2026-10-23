# 📖 Unit 1: Physical & Packet Foundations

> [!NOTE] Focus: Over-The-Air Framing, Access Address Rules & Direct Test Mode
> **Subject:** Bluetooth Low Energy (BLE) · **Frontier Level:** 0.65 · **Target Unit:** 1

---

## 🧭 1. Architectural & Conceptual Foundations

### The Physical Reality of Over-The-Air Framing
Wired embedded protocols rely on direct electrical coupling:
- **UART:** Uses continuous start and stop framing bits around each transmitted byte.
- **SPI / I2C:** Rely on dedicated physical clock traces ($SCK$ / $SCL$) to synchronize data sampling.
- **CAN:** Employs dominant and recessive physical states with bitwise arbitration.

In **Bluetooth Low Energy (BLE)**, there is no shared clock wire or continuous physical carrier. Transmission occurs over an unguided, noisy radio frequency medium in the **2.4 GHz ISM band** (2402 MHz – 2480 MHz across 40 physical channels, 2 MHz spacing) using **Gaussian Frequency Shift Keying (GFSK)**. 

Because the receiver's demodulator must achieve carrier recovery, symbol clock synchronization, packet boundary identification, and payload integrity verification entirely from a transient microsecond burst of RF energy, every transmission follows a strict physical-to-link-layer atomic frame.

---

## 🔌 2. Over-the-Air Packet Structure

At the Link Layer physical interface (LE 1M Uncoded PHY), every packet is structured as follows:

```
+------------------+---------------------+-----------------------+------------------+
| Preamble         | Access Address      | PDU (Protocol Data)   | CRC              |
| 1 octet (1M PHY) | 4 octets (32 bits)  | 2 to 257 octets       | 3 octets (24 bits|
+------------------+---------------------+-----------------------+------------------+
  ^                  ^                     ^                       ^
  Clock sync & AGC   Bit/Packet sync &     Header + Payload data   Bit error detection
  (Alternating 1010) Hardware correlator   (Advertising or Data)
```

### Component Breakdown
1. **Preamble (1 octet for 1M PHY, 2 octets for 2M PHY):**
   - An alternating sequence of `10101010` or `01010101`.
   - Used by the receiver for automatic gain control (AGC) training and symbol clock synchronization.
   - The first bit of the preamble must match the least significant bit (LSB) of the Access Address to prevent false transitions.
2. **Access Address (AA - 4 octets / 32 bits):**
   - Serves as the radio hardware correlation key.
   - Matches incoming bits in analog/digital correlator hardware before waking up software parsing logic.
3. **Protocol Data Unit (PDU - 2 to 257 octets):**
   - Contains a 16-bit Link Layer header and up to 255 bytes of payload.
   - Differentiates between Advertising Channel PDUs and Data Channel PDUs.
4. **Cyclic Redundancy Check (CRC - 3 octets / 24 bits):**
   - Calculated over the entire PDU to detect single and burst bit errors over the air.

---

## 🔑 3. The Access Address (AA) Mechanics

The Access Address is not a software MAC address; it is matched directly in the radio hardware correlator.

### Advertising vs. Data Channels
| Channel Type | Access Address Value | Purpose |
| :--- | :--- | :--- |
| **Primary Advertising (Channels 37, 38, 39)** | Fixed: `0x8E89BED6` | Broadcast address recognized by all BLE scanning devices to detect advertisements and beacons. |
| **Connected Data Channels (Channels 0–36)** | Dynamically generated 32-bit pseudo-random value | Unique to each active Link Layer connection between Central and Peripheral. |

### Connected Access Address Generation Rules
To ensure the receiver's phase-locked loop (PLL) maintains synchronization and to prevent false triggering from ambient noise or adjacent connections, the BLE specification mandates:
1. It must **not** be the advertising channel Access Address (`0x8E89BED6`).
2. It must **not** be the bit-inverted advertising address.
3. It must not have more than **6 consecutive 0s or 1s** anywhere in the 32 bits.
4. It must not have all four octets equal.
5. It must have at least **two transitions** in the most significant 6 bits.
6. There must not be more than **24 bit transitions** across the entire 32-bit word.

---

## 🛠️ 4. Direct Test Mode (DTM) & RF Compliance

During hardware validation, manufacturing, and regulatory compliance (FCC/CE):
- **Direct Test Mode (DTM):** Transmits and receives raw physical layer packets over a 2-wire UART or host controller interface (HCI).
- **Test Packets:** Bypass upper Link Layer and GATT negotiation, sending raw pseudo-random sequences (PRBS9) or alternating `0xAA` / `0xF0` patterns inside the PDU.
- **RF Metrics Measured:** Frequency deviation ($\Delta f1_{\text{avg}}$, $\Delta f2_{\text{max}}$), carrier frequency drift, modulation index, and Bit Error Rate (BER).

---

## 🧠 5. Self-Check & Verification

> [!QUESTION] Scenario Check 1: Fixed vs. Random Access Address
> Why does BLE mandate a fixed Access Address (`0x8E89BED6`) for advertising channels, but require unique pseudo-random addresses for data connections?
> 
> > [!TIP]- Reveal Solution
> > - **Fixed Advertising Address:** Broadcasters and scanners do not share prior state. A universally known 32-bit hardware correlator key allows any scanner to wake up and recognize packet boundaries on channels 37, 38, and 39.
> > - **Randomized Connected Address:** Multiple independent BLE connections frequently occupy the same 2.4 GHz space. Unique pseudo-random addresses ensure hardware correlation filters out co-located packets belonging to other connections.

> [!QUESTION] Scenario Check 2: Run-Length Bit Constraints
> Why does the BLE specification forbid more than 6 consecutive 0s or 1s in a connected Access Address?
> 
> > [!TIP]- Reveal Solution
> > Constant bit runs eliminate signal transitions. Without transitions, the receiver's phase-locked loop (PLL) drifts, causing bit-clock synchronization loss and packet corruption.

---

## 🗂️ Navigation
- [[../00_DASHBOARD|← Return to BLE Hub]]
- [[../01_ROADMAP|View Full BLE Roadmap]]
- [[../../../00_INDEX_DASHBOARD|Master Study Hub]]
