# Smart Home Ecosystem – Raspberry Pi IoT Edge Node

![Status](https://img.shields.io/badge/Status-Completed-brightgreen)
![Component](https://img.shields.io/badge/System-IoT%20Edge%20Node-orange)

Edge computing component of the **Modular Smart Home Ecosystem**. Handles hardware sensor readings, relay controls, local automation logic, and communicates real-time telemetry to the central VPS backend.

---

## Key Responsibilities

- **Hardware Interfacing:** Reading data from GPIO sensors (temperature, humidity, motion, etc.) and controlling physical relays/actuators.
- **Data Dispatching:** Transmitting telemetric data to the central cloud server via lightweight communication protocols.
- **Local Resilience:** Edge logic to ensure basic home controls function even during internet downtime.

---

## Authors & Collaboration

- **Main Developer:** Piotr Pepa ([@ptrpa](https://github.com/ptrpa)) – Hardware integration, edge architecture & sensor logic.
- **Contributor / Integrator:** Gabriel ([@CrimsonGabriel](https://github.com/CrimsonGabriel)) – Network communication protocols, backend API integration, system testing.

---

## Related Repositories
- [VPS Backend Repository](https://github.com/CrimsonGabriel/VPS-backend)
- [VPS Frontend Repository](https://github.com/CrimsonGabriel/VPS-frontend)
- [Android App Repository](https://github.com/CrimsonGabriel/Android-SmartHome)

```mermaid
graph TD
    subgraph Clients["📱 & 💻 Client Layer"]
        APP["📱 Android App<br/>(Mobile Client)"]
        WEB["💻 Web Dashboard<br/>(VPS Frontend)"]
    end

    subgraph Cloud["☁️ Cloud Infrastructure"]
        VPS["⚡ Central VPS Backend<br/>(REST API / WebSockets / DB)"]
    end

    subgraph Edge["🔌 Edge & Hardware Layer"]
        RPI["🔌 Raspberry Pi<br/>(IoT Edge Node)"]
        SENSORS["🌡️ Sensors & Actuators<br/>(Relays, Temp, Motion)"]
    end

    %% Connections
    APP <-->|"REST API / WebSockets"| VPS
    WEB <-->|"REST API / WebSockets"| VPS
    VPS <-->|"Telemetry / Commands (MQTT/REST)"| RPI
    RPI <-->|"GPIO / Serial"| SENSORS

    %% Styling
    style VPS fill:#1e293b,stroke:#3b82f6,stroke-width:2px,color:#fff
    style RPI fill:#1e293b,stroke:#f97316,stroke-width:2px,color:#fff
    style APP fill:#1e293b,stroke:#a855f7,stroke-width:2px,color:#fff
    style WEB fill:#1e293b,stroke:#22c55e,stroke-width:2px,color:#fff
    style SENSORS fill:#0f172a,stroke:#64748b,stroke-width:1px,color:#94a3b8
