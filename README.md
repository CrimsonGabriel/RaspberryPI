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

[ Raspberry Pi (IoT Edge Node) ] ──(MQTT / REST API)──┐
                                                     │
[ Android App (Mobile Client)  ] ──(REST / WS API)───┼──> [ VPS Backend (Central API) ]
                                                     │           │
[ Web Frontend (Admin Panel)   ] ──(REST / WS API)───┘           └──> [ Database ]
