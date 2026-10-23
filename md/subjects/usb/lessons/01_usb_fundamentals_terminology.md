# 📖 Unit 1: USB Fundamentals & Terminology

> [!NOTE] Focus: Bus Architecture, Signals & The Four Transfer Types
> **Subject:** USB · **Frontier Level:** 0.65 · **Target Unit:** 1

---

## 🧭 1. Architectural & Conceptual Foundations

### The Problem USB Solves
In traditional microcontroller and embedded hardware systems, peripheral communication relies on protocols like **UART**, **I2C**, and **CAN**:
- **UART:** Typically point-to-point connections with dedicated clock rates agreed upon in advance. Adding multiple devices requires separate TX/RX pin pairs or muxes.
- **I2C:** A shared multi-drop bus using two open-drain lines ($SDA$/$SCL$). Masters address slaves via 7-bit addresses. However, adding devices increases **parasitic capacitance ($C_b$)**, degrading rise times, forcing lower clock speeds, and limiting cable lengths to mere centimeters.
- **CAN:** Uses differential signaling on a shared bus with bitwise arbitration, but is optimized for small, robust industrial payloads rather than flexible computer peripherals.

### Topology: Tiered Star vs. Shared Multi-Drop Bus
USB abandons shared multi-drop traces. Instead, it organizes the network as a **Tiered Star Topology**:
- At the center sits a single master: the **Host Controller**.
- Every physical expansion point is an active **Hub**.
- End devices (functions) plug into ports provided by either the root host controller or an intermediate hub.
- Up to **127 devices** can be dynamically addressed on a single USB bus domain.

```
                    +---------------------------+
                    |   Root Host Controller    |
                    +---------------------------+
                                  |
                                  v
                        +-------------------+
                        |     Root Hub      |
                        +-------------------+
                           /      |       \
                          /       |        \
                         v        v         v
                   [ Device A ] [ Hub 1 ]  [ Device B ]
                                 /     \
                                v       v
                          [ Device C ] [ Device D ]
```

### Physical Isolation & Concurrency
1. **No Cumulative Capacitive Loading:** Because each link between a hub and a device is a dedicated, terminated point-to-point transmission line, plugging in a new device does not load down or degrade the electrical integrity of other ports.
2. **Active Fault & Speed Isolation:** The hub monitors current to each port. If a device shorts, the hub shuts down that specific port without collapsing the entire bus. Furthermore, Low-Speed (1.5 Mbps), Full-Speed (12 Mbps), and High-Speed (480 Mbps) devices coexist safely because hubs filter traffic.
3. **Sequential Concurrency on the Wire:** Even though the wiring resembles a star, **bandwidth is shared**. Standard USB is half-duplex and token-based. The host schedules transfers into microsecond/millisecond frames—it multiplexes communication across time, creating the illusion of concurrency for the OS while maintaining absolute deterministic control on the physical wire.

---

## 🔌 2. Hardware, Physical Signals & Speed Detection

Standard USB 1.1/2.0 cables use a 4-wire shielded cable:
- **$V_{BUS}$** (+5V DC power)
- **GND** (0V Reference)
- **D+ and D-** (Twisted-pair differential data lines, half-duplex)

Clock synchronization is embedded directly into the packet stream using **NRZI** (Non-Return-to-Zero Inverted) encoding with bit stuffing, eliminating the need for a dedicated clock wire like I2C's $SCL$.

### Physical Attachment & Speed Detection Circuit
The host detects when a device is plugged in—and what speed it runs—using simple analog pull-up and pull-down resistors:

```
        Host (Downstream Port)               Device (Upstream Port)
     +-------------------------+          +-------------------------+
     |                         |          |                         |
     |   D+ ---[ 15kΩ ]--- GND | <======> | D+ ---[ 1.5kΩ ]--- +3.3V (Full/High Speed)
     |                         |          |                         |
     |   D- ---[ 15kΩ ]--- GND | <======> | D- ---[ 1.5kΩ ]--- +3.3V (Low Speed)
     |                         |          |                         |
     +-------------------------+          +-------------------------+
```

1. **Idle State (Unplugged):** The host's $15\text{ k}\Omega$ pull-down resistors pull both $D+$ and $D-$ to $0\text{V}$ (Single-Ended Zero, or **SE0**).
2. **Device Detection:**
   - If the peripheral pulls **$D+$** high with its $1.5\text{ k}\Omega$ resistor, the host detects a **Full-Speed (12 Mbps)** or **High-Speed** device.
   - If the peripheral pulls **$D-$** high, the host detects a **Low-Speed (1.5 Mbps)** device.
3. **Bus Reset:** Once detected, the host asserts a bus reset by driving both lines low (**SE0**) for at least $10\text{ ms}$, transitioning the device to its default powered state at **Address 0**.

---

## 🔄 3. Bus Communication: The Token-Based Polling Mechanism

In microcontroller architectures, peripherals use hardware **Interrupt lines** (an external pin pulled low triggers an interrupt service routine on the CPU). 

**USB has NO dedicated hardware interrupt wire.** Peripherals are electrically forbidden from driving the bus uninvited. All communication is host-scheduled:

```
Host Controller                                Peripheral (e.g. Mouse)
      |                                                   |
      | -------- 1. IN Token Packet (Address, EP) ------> |
      |                                                   |
      | <------- 2a. DATA Packet (if moved: ΔX, ΔY) ----- |
      |                      -- OR --                     |
      | <------- 2b. NAK Handshake (if no movement) ----- |
      |                                                   |
(Waits for next scheduled polling slot, e.g. 8ms)
```

1. **Host-Initiated Polling:** The host periodically broadcasts an **IN** token specifically addressed to the peripheral's endpoint.
2. **The Response:**
   - If the peripheral has new data, it immediately sends a **DATA** packet.
   - If it has no new data, it responds with a hardware **NAK** ("negative acknowledgment"), which simply means *"I have nothing to report right now."*
3. **Guaranteed Latency:** The host driver guarantees it will poll the device at the interval requested by the peripheral (e.g. every 1 ms to 8 ms). Thus, "Interrupt Transfer" in USB means **host polling with a guaranteed maximum latency**, rather than a hardware-driven interrupt.

---

## 📊 4. The Four USB Transfer Types

USB classifies all communication into four fundamental transfer modes:

| Transfer Mode | Guaranteed Delivery (Error Retries) | Guaranteed Bandwidth & Latency | Typical Target Hardware | Ideal Use Case |
| :--- | :--- | :--- | :--- | :--- |
| **Control** | **Yes (100%)** — Handshake & parity checking | Allocated reserved slots | System Controllers | Enumeration, configuration, command requests (`SET_ADDRESS`, `GET_DESCRIPTOR`). |
| **Interrupt** | **Yes (100%)** — Automatic retries on error | **Yes** — Guaranteed maximum poll interval ($1\text{ ms} - 255\text{ ms}$) | Mice, Keyboards, Gamepads | Small, periodic human interface events where timely delivery is critical. |
| **Bulk** | **Yes (100%)** — Hardware ACK/NAK with infinite retry | **No** — Opportunistic; utilizes unallocated bandwidth | Flash drives, External SSDs, Printers | Large non-time-critical payloads where even a single bit error is unacceptable. |
| **Isochronous** | **No (0%)** — Corrupted packets discarded, no retries | **Yes** — Guaranteed fixed bandwidth and latency | USB Microphones, Webcams, Speakers | Real-time audio and video streams where constant pacing matters more than 100% reliability. |

---

## 🌳 5. Enumeration & Descriptors Hierarchy

Every newly attached USB device wakes up at **Address 0**. The host reads a hierarchy of data structures called **Descriptors** using Control Transfers to determine what driver to bind and what bandwidth to allocate:

```
                     +---------------------------+
                     |     Device Descriptor     |
                     |     (VID, PID, Class)     |
                     +---------------------------+
                                   |
                                   v
                     +---------------------------+
                     | Configuration Descriptor  |
                     |  (Bus-powered vs Self)    |
                     +---------------------------+
                                   |
                         +---------+---------+
                         |                   |
                         v                   v
               +-------------------+  +-------------------+
               | Interface 0 (HID) |  | Interface 1 (CDC) |
               +-------------------+  +-------------------+
                         |                   |
                         v                   v
               +-------------------+  +-------------------+
               | Endpoint 1 (IN)   |  | Endpoint 2 (IN/OUT|
               +-------------------+  +-------------------+
```

- **Device Descriptor:** Exactly one per physical product. Contains the Vendor ID (**VID**) and Product ID (**PID**).
- **Configuration Descriptor:** Specifies power requirements ($mA$) and the number of interfaces. (Only one configuration can be active at a time).
- **Interface Descriptor:** Represents a functional feature (e.g. a headset might expose Interface 0 for Audio and Interface 1 for Volume Buttons). Multiple interfaces can be active simultaneously (composite device).
- **Endpoint Descriptor:** Defines the physical FIFO pipe: direction (IN to host or OUT to device), transfer type (Control, Interrupt, Bulk, Isochronous), and maximum packet size.

---

## 💬 Classroom Dialogue & Deep Dives

### Composite Devices vs. Configurations
- **Question:** If a single USB device combines a keyboard, trackpad, and headphone jack, does it use multiple configurations or multiple interfaces?
- **Answer:** It uses **one active configuration with multiple interfaces**. Operating systems only allow one configuration to be chosen at runtime, but multiple interfaces operate concurrently.

### Address Assignment (`SET_ADDRESS`)
- **Question:** Why must the host assign a unique address before enumerating another newly plugged USB device?
- **Answer:** Because all newly connected USB devices default to **Address 0** upon reset. If a second device was plugged in and reset while the first was still at Address 0, both devices would respond to control tokens simultaneously, causing packet collisions on the wire.

---

## 🧠 6. Self-Check & Conceptual Mastery

> [!QUESTION] Scenario Check 1: Audio on Bulk vs. Firmware on Isochronous
> Why is Isochronous mode unacceptable for transferring firmware updates, and why does Bulk mode cause audio playback stutter when other devices are active on the bus?
> 
> > [!TIP]- Reveal Solution
> > - **Firmware on Isochronous:** Isochronous transfers drop corrupted packets without retransmitting them. A single bit error would silently corrupt the binary payload and potentially brick the peripheral.
> > - **Audio on Bulk:** Bulk transfers guarantee 100% accuracy through retries, but have no guaranteed bandwidth or latency. When other devices saturate the bus, Bulk packets are deferred, starving the audio DAC buffer and causing immediate audio stuttering.

> [!QUESTION] Scenario Check 2: Speed Detection Mechanism
> If you are designing an embedded USB sensor using a microcontroller that supports Full-Speed (12 Mbps), which physical data line must your board pull up to 3.3V, and what resistor value does the USB specification mandate?
> 
> > [!TIP]- Reveal Solution
> > The board must pull the **$D+$** line high to $+3.3\text{V}$ through a **$1.5\text{ k}\Omega$** resistor. (Pulling $D-$ high would mistakenly identify the device to the host as Low-Speed 1.5 Mbps).

---

## 🗂️ Navigation
- [[../00_DASHBOARD|← Return to Usb Hub]]
- [[../01_ROADMAP|View Full Usb Roadmap]]
- [[../../../00_INDEX_DASHBOARD|Master Study Hub]]
