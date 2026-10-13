# Capability-Matched Emergency Referral

**Taking the patient to the right hospital the first time**

Entry for the Seva First Innovation Challenge (Viksit Bharat 2047), Track A (Product / Technology), Theme: Swasth & Samavesh Bharat (Health) / Surakshit Bharat.
Full problem statement, evidence and sources: [document.md](./document.md) | Presentation deck: [CMER Presentation Deck](https://sevafirst.mic.gov.in).

> Status: simulation-based prototype. All results come from synthetic data. The system is decision support. The EMT and dispatcher make the final call.

---

## 1. Problem

When a person calls 108, the first priority is to reach the patient quickly. But reaching the nearest hospital does not guarantee reaching a hospital that can treat the patient.

A nearby hospital may have no suitable bed, no specialist on duty, no working equipment, or an emergency department that is already overwhelmed. The patient is then referred onward after arrival, which wastes time that cannot be recovered.

The question is not only:

> "How quickly can the ambulance reach the patient?"

but also:

> "Which capable hospital can treat the patient when the ambulance arrives?"

The proposed system does not replace 108 or its dispatch process. It is a coordination and decision-support layer connected to the existing 108 workflow.

---

## 2. Evidence that the problem is real

This section synthesises documented public evidence and audit findings from several states. Case studies highlight operational friction across emergency transport, noting that several acute incidents occurred during peak COVID-19 pandemic surges when hospital capacity faced extraordinary systemic stress.

### 2.1 Hospital choice is often not capability-based

* **Karnataka (health minister's statement, Deccan Herald).** The state's health minister noted that under legacy 108 operations, the choice of destination facility was routinely left to ambulance drivers, leading to suboptimal patient outcomes because facilities were not systematically mapped by clinical specialty. The stated reform was for the central command centre to actively steer ambulances to the nearest specialty-matched hospital.
* **Karnataka & National trauma emergency access (IIHMR & Emergency Access studies, ~2013).** Emergency response evaluations by the Indian Institute of Health Management Research (IIHMR) evaluated pre-hospital transport performance against an eight-minute operational response standard. The findings showed that for 10% to 12% of patients, the medical facility reached within that eight-minute window lacked the clinical capability (specialists, surgical suites, or critical care beds) to treat them, and under 5% reached an appropriately capable hospital within eight minutes. While 108 ambulances arrived on time, transport to facilities lacking specialty capabilities triggered avoidable onward shuttling.
* **Karnataka (CAG Performance Audit, 2014-15 to 2018-19).** The Comptroller and Auditor General's audit of the 'Arogya Kavacha' 108 service officially documented that ambulances failed to reach patients within the critical "golden hour" in 50% of trauma cases. It also confirmed that stipulated response times (20 min urban, 30 min rural) were met in only 72% of cases, dropping to under 40% (delays in over 60% of cases) for acute cardiac, stroke, and respiratory crises. The CAG explicitly recommended establishing standard operating protocols (SOPs) for pre-alerting destination hospitals. (Sources: Citizen Matters, Orissa Post, The News Minute.)

### 2.2 Patients shuttle between hospitals looking for a bed

* **Uttar Pradesh (Noida and Ghaziabad, June 2020).** A woman eight months pregnant died in an ambulance after her family said eight hospitals turned her away or cited no beds over about 12 to 13 hours. The district administration ordered an inquiry. (Sources: Hindustan Times, Deccan Herald, PTI reports.) This happened during COVID-19.
* **Telangana (Hyderabad, May 2021).** A pregnant woman and her unborn child died in an ambulance after several hospitals refused admission, according to ETV Bharat. This was also during COVID-19.
* **Bihar (Rohtas, 2024).** A pregnant woman was referred from a community health centre to the district hospital, and the family alleged that no ambulance was provided and that she delivered under a tree and the newborn died. The centre's medical in-charge disputed parts of this account. (Source: ETV Bharat.)
* **Eastern India (West Bengal, 2015 poster).** Clinicians at a hospital in Durgapur noted that without a centralised EMS system, patients present to under-resourced facilities and inter-facility ambulances carry a heavy load. (Source: International Journal of Emergency Medicine.)
* **National view (ORF).** An Observer Research Foundation analysis describes referral confusion between small private facilities and large public hospitals, ambulances shuttling patients while scrambling for an ICU bed, and suggests digital dashboards tracking ambulance locations and bed availability.

### 2.3 Hospitals have been asked to report beds before, and reporting quality was a problem

* **Delhi (June 2020).** The health minister said some hospitals were not updating the bed data on the Delhi Corona app on time or were misrepresenting actual data when patients called. The government then told hospitals to report admissions, discharges and bed status in real time. This is direct evidence for the freshness rules and reliability score in this proposal. (Source: The Tribune.)
* **Delhi (AIIMS and other hospitals).** AIIMS launched a real-time emergency bed availability dashboard, and the medical directors of major central and Delhi government hospitals agreed that every hospital needs one and that a unified dashboard should show beds across hospitals. (Source: The Tribune.)
* **Many states during COVID-19.** Delhi, Maharashtra, Telangana, Andhra Pradesh, Kerala, Gujarat, Tamil Nadu, Rajasthan, Madhya Pradesh, Haryana, Jharkhand and others ran bed-availability dashboards. Maharashtra's system included a hospital-side screen to update bed occupancy. These show hospitals can report counts, but they were built for COVID-19, not for emergency ambulance routing.
* **Research proposals.** A paper in the International Journal of Community Medicine and Public Health argues for a national real-time bed dashboard linking hospitals, ambulance services and state health systems.

### 2.4 Related gaps outside the scope of this project

Reports on ambulance availability and response times (the Karnataka CAG audit, a Kerala CAG report on calls not attended because no vehicle was available, and press reports on Jharkhand delays) show that dispatch capacity is a separate problem. This project does not claim to solve it.

### 2.5 What the evidence supports, and what it does not

It supports: hospital choice is often made without checking capability, patients get referred onward, and hospital-reported bed data is unreliable when not actively managed.

It does not prove: how often this happens nationally, or that this system would reduce deaths. That is why the prototype is evaluated in simulation and the next step is a supervised pilot.

---

## 3. Proposed solution

A Capability-Matched Emergency Referral System that helps the existing 108 system pick the best receiving hospital.

When a citizen calls 108, the normal call-taking and ambulance dispatch continue. The system receives the case details and evaluates nearby hospitals on:

* required clinical capability
* current capacity
* specialist availability
* equipment and services
* travel time
* emergency department load
* freshness and reliability of the hospital's reported information

It recommends a **primary hospital** and a **backup hospital**. The dispatcher and the ambulance crew retain control of the final destination.

---

## 4. How the system works

### 4.1 Dispatcher interface

The dispatcher records:

* patient location
* emergency type
* number of patients
* basic severity, if known

The system maps the emergency to the likely capability needed, for example:

| Emergency | Capability needed |
| --- | --- |
| Severe head injury | Trauma, neurosurgery, ICU |
| Obstetric emergency | Emergency obstetric care, blood, ICU or NICU |
| Cardiac emergency | Cardiac emergency care and specialist support |

The dispatcher sees the recommended hospital, the backup, estimated travel time, capacity confidence and the reason for the recommendation.

### 4.2 Ambulance crew app

After the ambulance is dispatched through the existing workflow, the crew receives the location and case information. After pickup, the crew member with the patient (not the driver) confirms or changes the emergency category from a short list:

* Trauma or head injury
* Cardiac emergency
* Stroke or neurological emergency
* Obstetric emergency
* Paediatric emergency
* Burns
* General or uncertain emergency

The category is pre-filled from the dispatcher's note, so it usually takes one tap. The app then shows the primary and backup hospitals. The crew can accept the recommendation or override it, with a short logged reason. The driver stays focused on driving.

**Unstable patient rule:** if the patient is critical or deteriorating, the crew may go to the nearest stabilising facility regardless of the ranking. The override is logged and any hospital hold is released.

### 4.3 Hospital dashboard

Hospitals update capacity, receive incoming-ambulance alerts, confirm or reject capacity requests and see their reservations.

---

## 5. Hospital ranking

Hospitals are first filtered for whether they can provide the required care. The rest are ranked by **expected time to appropriate treatment**, not by distance.

### 5.1 Inputs

* travel time with current traffic
* probability that the required capacity is available at arrival
* specialist on duty
* ICU or critical care availability
* required equipment and services
* emergency department load
* ambulances already heading to the same hospital
* freshness of the hospital's last report
* the hospital's historical reliability score

### 5.2 Expected time to treatment

For each candidate hospital h:

```
ETT(h) = travel_time(h) + ER_delay(h) + (1 - P_ok(h)) x reroute_penalty(h)

```

* `travel_time(h)`: estimated driving time from the ambulance's current position.
* `ER_delay(h)`: expected wait from the hospital's emergency load.
* `P_ok(h)`: probability that the required bed, specialist and equipment are available at arrival (Section 7).
* `reroute_penalty(h)`: extra time if the patient has to be sent onward, estimated from travel time to the backup hospital plus a fixed handling delay.

The hospital with the lowest ETT is the primary choice and the second lowest is the backup. If two ambulances are heading to the same hospital, the second ambulance sees a reduced `P_ok` because the first one's reservation counts against capacity.

---

## 6. Hospital data sync

### 6.1 Minimal data

Per hospital and ward: total beds, free beds, specialists on shift, key equipment status, emergency contact number. No patient data. This keeps privacy simple and makes joining easier.

### 6.2 Three ways to update

1. **Dashboard.** Admission desk or duty nurse updates counts on a simple web page.
2. **Lightweight updates.** Small facilities reply to an SMS or WhatsApp prompt with a short structured message (for example, "ICU 2").
3. **Automated feed.** Hospitals with their own information systems send counts through an API or file export. Standard facility identifiers, including ABDM facility IDs, can identify hospitals later.

### 6.3 Event-triggered updates

Updates are prompted by events that change capacity, not only by a timer: admission, discharge, transfer and shift change.

### 6.4 Freshness rules

Every status shows when it was last confirmed and falls into one of three bands (the thresholds below are starting assumptions to be tuned in simulation):

| Band | Age of last confirmation | Treatment |
| --- | --- | --- |
| Fresh | up to 15 minutes | trusted as reported |
| Aging | 15 to 30 minutes | probability estimate widens |
| Stale | over 30 minutes | estimator used, verification suggested |

A stale hospital is **not** removed from consideration. A close, capable hospital should not be dropped only because its last update is 40 minutes old.

### 6.5 One-tap verification

If a highly suitable hospital has stale data, the dispatcher can call its emergency desk with one tap, in parallel while the ambulance is already moving so the call adds no delay. The hospital answers "confirmed" or "unavailable." If confirmed, the hospital stays in the ranking with fresh data. If unavailable, the system moves to the next hospital immediately.

### 6.6 Reservation and pre-alert

The ambulance does not book a real bed on its own. The flow is:

1. The crew accepts a hospital.
2. The hospital receives an incoming-emergency alert with case type, ETA and capacity needed.
3. The hospital confirms or rejects.
4. On confirmation the capacity is held temporarily.
5. The hold expires automatically after ETA plus a buffer if the ambulance is cancelled, diverted or late.
6. Arrival closes the hold.

### 6.7 Reliability score

After each arrival, the crew or hospital records whether the reported bed, specialist and equipment were actually available and whether the patient was accepted. These records produce a per-hospital reliability score (Section 7.4). Hospitals with accurate, fresh reports get more trust in future recommendations, which gives hospitals a reason to keep data current.

---

## 7. How the probability works

The system treats the true number of free beds as hidden. A hospital report is a noisy reading that gets less reliable with age.

### 7.1 Estimating free beds now

Let `f0` be the free beds in the last report, taken `t` minutes ago. Over that time, discharges free beds and admissions use them.

```
E[free(t)] = f0 + d(h, hour) x t - a(h, hour) x t

```

* `d(h, hour)`: typical discharge rate per minute for hospital h and ward at this time of day.
* `a(h, hour)`: typical admission rate per minute, including ambulances already heading there.

The uncertainty grows with time. A simple model treats arrivals and discharges as independent random events (Poisson), so the variance is approximately `(d + a) x t`. This gives a distribution over free beds, not a single number.

### 7.2 Probability a bed is available at arrival

At estimated arrival time `T`, with a safety buffer for cleaning and turnover:

```
P_ok = P(free(T) - held_beds >= 1)

```

where `held_beds` counts reservations already placed by other ambulances. This is read from the estimated distribution. The system shows it as "85% chance of at least one ICU bed," not as a number that looks exact.

For specialists and equipment the same idea applies, using shift schedules and recent status instead of admission rates.

### 7.3 Defining "usable"

A bed counts as available only if it is in the right ward and specialty, has required equipment, and has had time to be cleaned after its last patient. A vacated bed is not instantly usable.

### 7.4 Reliability score

For each hospital, keep an exponentially weighted match rate between reports and what ambulances found:

```
R_new = (1 - alpha) x R_old + alpha x match

```

`match` is 1 if the report proved correct on arrival and 0 if not. A low `R` widens the uncertainty on that hospital's reports and lowers its `P_ok`. `alpha` (for example 0.1) is a tunable assumption.

### 7.5 Calibration

Probabilities are only useful if they are honest. The simulation checks calibration: of the cases where the system said 80% to 90% chance, roughly 80% to 90% should have found a bed. A reliability diagram and a calibration error number are reported.

### 7.6 Feedback loop

```
Hospital report -> Recommendation -> Hospital confirmation -> Arrival
-> Actual availability -> Outcome -> Updated rates and reliability

```

---

## 8. Why hospitals would join

Hospitals need a reason beyond goodwill. The proposal rests on these incentives:

1. **Pre-alerts.** A team and bed are prepared before the patient arrives, so handover is faster and less chaotic.
2. **Fewer wrong arrivals.** Patients they cannot treat are not sent to them, reducing crowding and wasted effort in the emergency department.
3. **Better case mix.** Capability-matched routing sends them the cases they are equipped for.
4. **Visibility.** They show up in the 108 operator's system as a reliable receiving hospital.
5. **Low burden.** Counts only, no patient data, with SMS or WhatsApp for facilities without IT.
6. **A push from the system.** The CAG audit in Karnataka recommended pre-alerting hospitals, and Delhi directed hospitals to report beds in real time. A pilot would use state health mission and 108 operator channels to make participation a condition of the pilot, not a favour.

Risks: hospitals may under-report free beds to avoid patients, or over-report them. The reliability score and arrival confirmations are designed to catch both.

---

## 9. Prototype

Built with synthetic data. It simulates 10 to 20 hospitals with different capabilities, bed availability, specialist schedules, equipment, ambulances, emergency cases, travel times, reporting delays, missing or stale updates, hospital confirmations and reservations.

Three interfaces:

1. **Dispatcher dashboard:** create an emergency, see the ranked hospitals and reasons.
2. **Ambulance crew app:** receive the case, confirm the emergency type, view primary and backup hospitals, accept or override, call the hospital.
3. **Hospital dashboard:** update capacity, receive incoming ambulances, confirm or reject, view reservations.

---

## 10. Simulation evaluation

### 10.1 Strategies compared

1. **Nearest hospital:** The baseline status quo—dispatches to the geographically closest facility regardless of clinical capability or bed status.
2. **Nearest capable hospital, specialties only:** Filters for basic specialty/capability match, but ignores real-time bed availability and queue delays.
3. **Nearest capable hospital with a currently reported free bed:** Filters for capability and positive bed count at last report, but ignores reporting delays, turnover, and queue decay.
4. **Capability-Matched Emergency Referral (CMER):** Dynamic ranking combining travel time, emergency department queue delays, arrival bed probability via Skellam distribution, and reroute penalties.

### 10.2 Non-circular evaluation protocol
> [!IMPORTANT]
> **Ground-Truth Process Independence:** To ensure calibration and performance tests are not mathematically circular, the discrete-event simulator generates the true bed occupancy process using a structurally different mechanism than the estimator assumes. While CMER's estimator models bed changes via Poisson/Skellam distributions based on reported rates, the simulator models underlying admissions and discharges using non-stationary, bursty queues (e.g., empirical diurnal bursts or Markov-modulated arrival patterns). This ensures that calibration metrics test robustness against model mismatch rather than tautological assumptions.

### 10.3 Metrics

* share of patients reaching a capable hospital without an onward diversion (first-time delivery rate)
* expected and actual time to definitive treatment
* number of onward secondary referrals
* receiving hospital capacity utilisation and queue stability
* recommendation accuracy
* probability calibration error (Brier score and reliability curves)
* performance degradation when hospital data is stale or missing

### 10.4 Robustness & sensitivity experiments

* **Reporting degradation sweep:** Vary the share of hospitals updating on time across 100%, 80%, 60%, 40%, and 30%.
* **Occupancy stress sweep:** Test baseline bed occupancies across 60%, 75%, 85%, and 95%.
* **Transit & traffic variance:** Apply road network delays from 1.0× to 2.5× baseline.
* **Misreporting frequency:** Test Bayesian reliability score (`R`) adaptation when a subset of hospitals consistently misreports beds.

### 10.5 Benchmark Results (250 Monte Carlo Runs, Seed=42)

The simulation tests all dispatch strategies without data leakage (strict separation between stale/noisy reported dashboards and evolving physical ground truth, realistic call-taking hold attempts capped at top 2 candidates, and secondary diversion capacity checks):

| Dispatch Strategy | First-Time Delivery (%) | Mean Treatment Time (min) | Secondary Transfers / 100 | Incapable Refusals (%) | Bed Refusals (%) | Paired vs S3 Time Diff (95% CI) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **1. Nearest Hospital (Status Quo)** | **28.8%** | 55.1 ± 1.3 | 72.4 | 67.2% | 4.0% | +21.31 min [+19.20, +23.47] |
| **2. Nearest Capable (Specialties Only)** | **94.0%** | 34.5 ± 0.8 | 6.0 | 0.0% | 6.0% | +0.71 min [-0.64, +2.09] |
| **3. Nearest Capable + Free Bed** | **96.0%** | 33.8 ± 0.7 | 4.0 | 0.0% | 4.0% | Baseline [0.00, 0.00] |
| **4. CMER (Capability + ETT + Bed Hold)** | **99.2%** | **33.2 ± 0.7** | **1.2** | **0.0%** | **0.8%** | **-0.54 min [-1.91, +0.73]** |
| *Ablation: Capable + Pre-Alert Hold* | 100.0% | 33.3 ± 0.7 | 0.0 | 0.0% | 0.0% | -0.51 min [-1.78, +0.65] |
| *Ablation: Capable + Bed + Pre-Alert Hold* | 100.0% | 32.8 ± 0.7 | 0.0 | 0.0% | 0.0% | -0.92 min [-2.13, +0.21] |
| *Ablation: CMER (Ranking Only, No Hold)* | 92.4% | 35.3 ± 0.9 | 7.6 | 0.0% | 7.6% | +1.54 min [-0.10, +3.19] |

> [!NOTE]
> **Key Finding on Pre-Alert Holds:** Notice that `Ablation: CMER (Ranking Only, No Hold)` achieves 92.4% delivery because stale dashboard beds decay during transit. Pre-alert bed hold confirmation (`attempt_prealert_hold`) is essential to protect patients from arrival bed snipes, explaining why the full CMER protocol pairs real-time $P_{ok}$ ranking with hospital pre-alert reservations.

### 10.6 Output reporting and visualisation

Every result is labelled as a simulation result on synthetic data. The simulation pipeline runs 250 independent stochastic runs per parameter setting (reporting means, bootstrap 95% confidence intervals, and standard error spreads) and automatically saves comparative evaluation plots (`sim_results_strategies.png`, `sim_calibration_diagram.png`, `sim_reporting_sweep.png`) to the project artifacts directory.

---

## 11. Assumptions

These are starting values for the simulation. They are not facts. They should be stated openly and varied in a sensitivity test.

| Area | Assumption |
| --- | --- |
| City | One synthetic city, 10 to 20 hospitals, mix of small, mid-size and tertiary |
| Capabilities | Each hospital has a fixed set of specialties and equipment, with tertiary hospitals covering more |
| Arrivals | Emergency calls follow a Poisson process with a daytime peak |
| Case mix | Fixed shares across the seven categories (for example trauma 30%, cardiac 20%, obstetric 15%, and so on) |
| Bed dynamics | Bed occupancy follows admissions and discharges with time-of-day patterns; high baseline occupancy (for example 75% to 90%) |
| Reporting | Each hospital reports at a hospital-specific delay; a share of reports are dropped |
| Report errors | Some hospitals report inaccurately at a set rate to test the reliability score |
| Travel time | Road network or distance-based estimate with random traffic delay |
| Handling times | Fixed delays for ER handover and for rerouting after a diversion |
| Ambulance behaviour | Crew follows the recommendation unless the patient is critical, in which case the nearest facility is chosen |
| Reservation hold | Hold lasts ETA plus a fixed buffer, then expires |

Sensitivity tests: vary occupancy, reporting delay, share of inaccurate hospitals, and traffic.

---

## 12. Safety and limitations

* The system is decision support, not an autonomous medical decision-maker. The dispatcher and EMT keep authority over the final destination.
* All results come from synthetic data, so they do not claim real-world clinical effectiveness.
* Phone-based triage is rough. The suggested category must be confirmed by the crew.
* Real deployment needs: a state or 108 operator partnership, hospital participation, secure data sharing, privacy and cybersecurity controls, clinical validation, and integration with existing 108 systems.
* Calibration matters. Overconfident predictions are dangerous, so the model must be tested before any real use.

## 13. Pilot and deployment pathway
 
### 13.1 Phased Implementation Roadmap
1. **Phase 1: Controlled Pilot Preparation (Months 1–2):** Co-design workflows with 1 representative district health society, 3–5 participating hospitals (1 government tertiary/medical college hospital, 1 district hospital, 2–3 sub-district or empanelled private facilities), and approximately 20 dedicated 108 ambulances. Stand up ABDM sandbox connectors and configure hospital triage web consoles.
2. **Phase 2: Supervised Dual-Run Field Trial (Months 3–8):** Advisory-only integration alongside the active CAD workflow (6–12 months total lifecycle). Dispatchers and EMTs receive real-time capability recommendations without mandatory overrides. Continuous audit of referral accuracy and hospital pre-alert check-in fidelity.
3. **Phase 3: Formal Outcome Evaluation & Policy Sign-Off (Months 9–10):** Measure impact against pre-pilot district baselines (secondary transfers, handover latency, diversion frequency). Present safety and audit findings to state emergency health directors.
4. **Phase 4: State-Wide Incremental Rollout (Months 11–12+):** Transition from district overlay to native CAD microservice integration across all district ambulance clusters.

### 13.2 Pilot Evaluation Framework & Core Metrics
* **First-time capability delivery rate:** Proportion of acute patients arriving at a facility equipped to treat them.
* **Secondary transfer reduction:** Reduction in inter-facility emergency diversions within 2 hours of arrival.
* **Handover latency:** Emergency department arrival-to-handover time, reflecting pre-alert readiness.
* **Bed-hold adherence:** Match rate between pre-alert hold confirmations and physical bed availability.
* **EMT & dispatcher override logs:** Frequency and distribution of clinical overrides.

### 13.3 Budget and Resourcing Note
> [!NOTE]
> **Financial Projections:** Formal pilot costs are not yet estimated and will be calculated during Phase 1 co-design based on state procurement models, existing tablet availability across the 108 fleet, and participating hospital IT readiness. Because CMER runs as a lightweight sidecar on top of existing CAD terminals and mobile devices, deployment avoids major custom hardware procurement.

---

## 14. Expected impact

* fewer avoidable hospital-to-hospital transfers
* faster access to appropriate treatment
* better use of existing hospital capacity
* better ambulance and hospital coordination
* visibility of emergency-care capacity for planners
* more reliable hospital capacity reporting

**Core proposition**

> 108 gets the ambulance to the patient. Capability-Matched Emergency Referral helps get the patient to the right hospital the first time.

---

## 15. Integration & Interoperability Architecture

### 15.1 ABDM and National Digital Health Ecosystem Alignment

* **Standards Compliance:** The architecture is designed to integrate with Ayushman Bharat Digital Mission (ABDM) standards, with planned support for HL7 FHIR R4 schema profiles (`Organization`, `Location`, `HealthcareService`) for standards-compliant health data interoperability across national digital public infrastructure.
* **Unified Identifiers:** Facilities are keyed by their ABDM Health Facility Registry (HFR) ID (e.g., `IN-KA-BLR-00109`), preventing duplicate facility records and ensuring future alignment with state and national health authority registries.

### 15.2 Legacy CAD Vendor Integration Strategy

* **Non-Disruptive Sidecar Deployment:** Rather than demanding a complete rewrite or replacement of proprietary Computer-Aided Dispatch (CAD) software used by private-public 108 operators (such as EMRI Green Health Services), the module integrates via a lightweight, secure API "sidecar" architecture.
* **Minimal Workflow Friction:** Dispatchers interact with a clean, high-contrast companion web overlay that pulls incident coordinates from the main CAD feed, computes the optimal capability match, and pushes back recommendations without modifying core dispatch logs.

### 15.3 Offline-Resilient Rural Edge Synchronization

* **Low-Bandwidth Optimization:** Recognizing connectivity drops in semi-urban or rural transit corridors, the ambulance crew application utilizes local caching and compressed data packets.
* **Fallback SMS/USSD Handshake:** If cellular data fails entirely during transit, critical pre-alerts and hospital confirmations automatically fall back to structured, low-latency SMS or USSD channels to ensure continuous coordination without data dependency.

---

## 16. Sources

Primary references, government audit findings, and clinical literature cited throughout this proposal:

* Deccan Herald, "Karnataka's '108' ambulances to get faster, fitter & more efficient" (health minister on driver-chosen hospitals): [https://www.deccanherald.com/india/karnataka](https://www.deccanherald.com/india/karnataka)
* IIHMR & Emergency Access Studies, evaluations on pre-hospital delay, trauma triage, and facility matching in emergency medical networks: [https://www.iihmrbangalore.edu.in/research/completed-projects](https://www.iihmrbangalore.edu.in/research/completed-projects)
* Citizen Matters, "When an ambulance driver stopped for dinner and never reached the patient, who died later" (Karnataka CAG audit analysis): [https://citizenmatters.in/when-an-ambulance-driver-stopped-for-dinner-and-never-reached-the-patient-who-died-later](https://citizenmatters.in/when-an-ambulance-driver-stopped-for-dinner-and-never-reached-the-patient-who-died-later)
* The News Minute, "108 ambulances failed to reach 50% patients within time in Karnataka: CAG" (Official audit findings on 72% compliance & golden hour access): [https://www.thenewsminute.com/karnataka/108-ambulances-failed-reach-50-patients-within-time-karnataka-cag-139366](https://www.thenewsminute.com/karnataka/108-ambulances-failed-reach-50-patients-within-time-karnataka-cag-139366)
* Orissa Post, "Karnataka: 108 ambulance service failed to reach 50% patients within time" (CAG audit findings & pre-alert recommendations): [https://www.orissapost.com/karnataka-108-ambulance-service-failed-to-reach-50-patients-within-time/](https://www.orissapost.com/karnataka-108-ambulance-service-failed-to-reach-50-patients-within-time/)
* Madhyamam, "CAG finds loopholes in running 108 ambulance services" (Kerala audit findings): [https://english.madhyamam.com/kerala/2015/mar/23/cag-finds-loopholes-running-108-ambulance-services](https://english.madhyamam.com/kerala/2015/mar/23/cag-finds-loopholes-running-108-ambulance-services)
* The Hindu, "Pregnant woman dies in ambulance after 13-hour search for hospital bed in Noida": [https://www.thehindu.com/news/cities/Delhi/pregnant-woman-dies-in-ambulance-after-13-hour-search-for-hospital-bed-in-noida/article31766023.ece](https://www.thehindu.com/news/cities/Delhi/pregnant-woman-dies-in-ambulance-after-13-hour-search-for-hospital-bed-in-noida/article31766023.ece)
* Hindustan Times (via PressReader), Noida pregnant woman case coverage: [https://www.pressreader.com/india/hindustan-times-delhi/20200607/281582357859092](https://www.pressreader.com/india/hindustan-times-delhi/20200607/281582357859092)
* The Siasat Daily / Local Reports, Hyderabad corporate hospital refusal during pandemic surge (May 2021): [https://www.siasat.com/hyderabad-pregnant-woman-dies-as-corporate-hospitals-refuse-admission-2137684/](https://www.siasat.com/hyderabad-pregnant-woman-dies-as-corporate-hospitals-refuse-admission-2137684/)
* ETV Bharat, "Turned away by health centre, pregnant woman delivers under tree, newborn dies" (Rohtas, Bihar, 2024): [https://www.etvbharat.com/en/!state/bihar-turned-away-by-health-centre-pregnant-woman-delivers-under-tree-newborn-dies-enn24040905023](https://www.etvbharat.com/en/!state/bihar-turned-away-by-health-centre-pregnant-woman-delivers-under-tree-newborn-dies-enn24040905023)
* International Journal of Emergency Medicine, "Inter hospital transfer or centralized ambulance number – what is the need of hour?" (Eastern India EMS study, DOI: 10.1186/1865-1380-8-S1-P2): [https://intjem.biomedcentral.com/articles/10.1186/1865-1380-8-S1-P2](https://intjem.biomedcentral.com/articles/10.1186/1865-1380-8-S1-P2)
* Observer Research Foundation (ORF), "Integrating India's Emergency Response: A Health System Priority": [https://www.orfonline.org/expert-speak/integrating-india-s-emergency-response-a-health-system-priority](https://www.orfonline.org/expert-speak/integrating-india-s-emergency-response-a-health-system-priority)
* The Tribune, "Delhi Health Minister asks hospitals to submit real-time data on beds": [https://www.tribuneindia.com/news/delhi/delhi-health-minister-reacts-on-shortage-of-beds-asks-hospitals-to-submit-real-time-data-95031](https://www.tribuneindia.com/news/delhi/delhi-health-minister-reacts-on-shortage-of-beds-asks-hospitals-to-submit-real-time-data-95031)
* The Tribune / AIIMS Dashboard Report, "Now know emergency bed status at AIIMS; real-time dashboard launched": [https://www.tribuneindia.com/news/delhi/now-know-emergency-bed-status-at-aiims-real-time-dashboard-launched-445647](https://www.tribuneindia.com/news/delhi/now-know-emergency-bed-status-at-aiims-real-time-dashboard-launched-445647)
* Government of Maharashtra, State Health Assurance Society (MJPJAY / CCMS Portal Guidelines): [https://jeevandayee.gov.in](https://jeevandayee.gov.in)
* International Journal of Community Medicine and Public Health (IJCMPH), "Unlocking India's hospital beds: why a digital portal is the cure for a stretched system" (Vol 13, Issue 3, DOI: 10.18203/2394-6040.ijcmph20260718): [https://www.ijcmph.com/index.php/ijcmph/article/view/14846](https://www.ijcmph.com/index.php/ijcmph/article/view/14846)
* Seva First Innovation Challenge: [https://sevafirst.mic.gov.in](https://sevafirst.mic.gov.in)