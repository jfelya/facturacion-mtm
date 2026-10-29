# Pickup-time calibration — findings

**Goal:** estimate a trip's **pickup time** from its **appointment/dropoff time** and **mileage**
(`pickup ≈ appointment − miles × ratio`), for the MTM billing automation.

**Data window analysed:** trips dated **2026-09-01 → 2026-10-02** (the only window where scheduled
pickup times exist). October is covered only by the provider export (no scheduled pickups).

---

## 1. Files and exact column headers

### 1a. `data/test/Trips/Listos/<day>/BULK UPLOAD*.xlsx` — **has the scheduled times** ✅
Sheet name: `Export Trip`. Exact header row:

```
TripNumber | Driver | Vehicle | ScheduledPickupTime | ReportedPickupArriveTime |
ReportedPickupPerformTime | ScheduledDropoffTime | ReportedDropoffArriveTime |
ReportedDropoffPerformTime | TripLogSignature
```

Sample rows (`BULK UPLOAD 10-01.xlsx`):

| TripNumber | Driver | Vehicle | ScheduledPickupTime | ReportedPickupArriveTime | ReportedPickupPerformTime | ScheduledDropoffTime | ReportedDropoffArriveTime | ReportedDropoffPerformTime | TripLogSignature |
|---|---|---|---|---|---|---|---|---|---|
| M4GZP0HNF0A | N242-541-93-600-0 | 2C4RDGBG0HR853353 | 14:05 | 14:02 | 14:03 | 14:30 | 14:24 | 14:24 | Y |
| M4GZP0HNF0B | N242-541-93-600-0 | 2C4RDGBG0HR853353 | 15:30 | 15:31 | 15:32 | 16:00 | 15:52 | 15:52 | Y |
| M4H0MMU6J0B | B203-938-58-800-0 | 5XYPGDA31KG574582 | 14:22 | 14:23 | 14:24 | 15:30 | 15:28 | 15:28 | Y |
| M4E9RLMGR0A | M618-049-78-900-0 | JTDKN3DU5D5566463 | 07:15 | 07:12 | 07:13 | 07:45 | 07:39 | 07:39 | Y |

**Important:** the BULK files contain **no mileage and no appointment date** — they must be joined to
another source for mileage.

### 1b. `data/**/ClaimInformation*.xlsx` — **has mileage + pickup time** ✅
Exact header (September variants):

```
Driver | Appt. Date | Member Info | Milage | Cost | Trip Number | License | VIN | PU Time
```

Sample rows (`ClaimInformation 09-22 FINISHED EXAMPLE.xlsx`):

| Driver | Appt. Date | Member Info | Milage | Cost | Trip Number | License | VIN | PU Time |
|---|---|---|---|---|---|---|---|---|
| 200 | 09/22/2026 | ELENA JOHANSON | 10.81 | $15.93 | M408JJTHU0B | N242-541-93-600-0 | 2C4RDGBG0HR853353 | 14:00 |
| 200 | 09/22/2026 | LAURA GOODROW | 8.18 | $15.00 | M4DMPVIDU0B | N242-541-93-600-0 | 2C4RDGBG0HR853353 | 13:45 |

> `PU Time` in ClaimInformation is **byte-for-byte equal** to `ScheduledPickupTime` in the BULK file for
> the same `TripNumber` (verified on 221/221 overlapping trips, 0 min difference). They are the same field.

### 1c. `data/base/10-*.xlsx` — the provider export (appointment + mileage)
41 columns incl. `Trip Number`, `Appointment Date`, `Time`, `Trip Mileage`, `Trip Cost`, `Will Call Flag`.
`Time` is the **appointment/dropoff** time (string, e.g. `"07:45 AM"`, or the literal `"Will Call"`).
**These files exist only for 10-05 … 10-15** and contain **no scheduled pickup** column.

### 1d. `data/test/Trips/Listos/<day>/RESUMEN FACTURACIÓN*.xlsx` — billing summary
Header: `DATE | LOS | TRIP ID | PAYER | NAME | LAST NAME | DRIVER | MILES | DRIVER`. **`TRIP ID` is
empty in all September files**, so it cannot be joined to BULK by trip number (October RESUMEN files
use UUIDs, not MTM trip numbers). Some October RESUMENs do carry a `P.U`/`P.U TIME` column, but those
trip IDs are UUIDs and do not match the provider trip numbers.

---

## 2. The join that works

| Source | Key | Fields |
|---|---|---|
| BULK UPLOAD (Sep 1 – Oct 2) | `TripNumber` | ScheduledPickupTime, ScheduledDropoffTime, Reported*Perform* |
| ClaimInformation (Sep) | `Trip Number` | Milage, PU Time |

- **322** trip numbers match between BULK and ClaimInformation.
- **254** of those have both a scheduled pickup+dropoff **and** a usable mileage → the working dataset.
- **238** remain after dropping obvious mileage data errors (`miles ≤ 100` and lead `≤ 120 min`).

> **There is no overlap** between BULK (Sep) and the provider export (Oct): `bulk ∩ base = 0`. So
> `ScheduledDropoffTime` cannot be compared to the provider `Time` for the same trip number (see §5).

---

## 3. Ratio = lead minutes ÷ miles

`lead = ScheduledDropoffTime − ScheduledPickupTime` (minutes).

### Distribution of `lead / miles`

| set | n | min | p25 | median | mean | p75 | max | sd |
|---|---|---|---|---|---|---|---|---|
| **all joined** | 254 | 0.038 | 2.048 | **2.813** | 3.728 | 4.129 | 67.382 | 4.680 |
| **clean** (mi ≤ 100, lead ≤ 120) | 238 | 0.467 | 2.131 | **3.106** | 3.654 | 4.249 | 17.241 | 2.391 |

The mean/median are inflated by a **fixed per-trip buffer** (see §4) and by the fact that scheduled
leads are quantized to a 5-minute grid.

### Concrete examples (clean set)

| TripNumber | Member | Miles | Sched Pickup | Sched Dropoff | Lead (min) | min/mi | Reported perform PU→DO | Actual (min) |
|---|---|---|---|---|---|---|---|---|
| M4E5TO3K40A | LISA HALSEY | 0.84 | 08:25 | 08:30 | 5 | 5.95 | 08:21→08:29 | 8 |
| M4GRAGUVT0A | SERENITY MEEKS | 1.35 | 07:40 | 08:00 | 20 | 14.81 | 07:37→07:51 | 14 |
| M4CIS5JCD0A | BRIAN BETTMAN | 1.88 | 10:25 | 10:45 | 20 | 10.64 | 10:22→10:39 | 17 |
| M4DKE4OFO0A | MARIA IRIZARRY CARMON | 40.52 | 06:55 | 08:00 | 65 | 1.60 | 06:55→07:56 | 61 |
| M495IE6N30A | LOUIS MENDEZ | 57.62 | 07:30 | 09:00 | 90 | 1.56 | 07:31→08:50 | 79 |
| M4B7XFNOQ0A | JAMES RAMSEY | 72.80 | 05:50 | 07:30 | 100 | 1.37 | 05:43→07:21 | 98 |

Note how the effective min/mi **falls steeply with distance** — that is the fingerprint of a fixed
buffer on top of a per-mile rate.

### Median lead by distance bucket (scheduled)

| Miles | n | median lead (min) | median min/mi |
|---|---|---|---|
| 0–5 | 50 | 20.0 | 6.07 |
| 5–10 | 108 | 25.0 | 3.41 |
| 10–15 | 58 | 30.0 | 2.78 |
| 15–25 | 4 | 38.5 | 1.88 |
| 25–50 | 14 | 62.0 | 1.94 |

---

## 4. The real model: a per-mile rate **plus a fixed buffer**

Two independent fits:

| target | OLS fit | R² | n | through-origin ratio |
|---|---|---|---|---|
| **Scheduled** lead (pickup→appointment) | `lead = 14.01 + 1.422 × miles` | 0.740 | 238 | 2.126 |
| **Actual** travel (reported perform PU→DO) | `actual = 10.49 + 1.395 × miles` | **0.886** | 243 | **1.740** |

**The suspected 1.7 min/mile is confirmed as the true driving rate** — the through-origin ratio of the
*actual* travel times is **1.740 min/mile** (≈ 34 mph), and the OLS slope is 1.40 min/mile with a
≈10.5 min fixed intercept.

The scheduled lead simply adds a few extra minutes of padding: `scheduled − actual` has median
**+3 min** (mean +3.9). So the scheduler essentially writes `pickup = appointment − (drive time + small buffer)`.

Distribution of the **actual** travel ratio (min/mi): n=243, min 0.94, p25 2.04, median 2.48, mean 3.07,
p75 3.51, max 14.94 — again the median > slope because of the fixed intercept.

---

## 5. ScheduledDropoffTime vs provider `Time`

**Cannot be verified directly.** BULK files (Sep 1 – Oct 2) and the provider exports (Oct 5–15) share
**zero** trip numbers, and the October ClaimInformation `PU Time` cells are blank (the only "filled"
values were repeated header rows). There is therefore no file that contains both a scheduled dropoff
and the provider `Time` for the same trip.

**Circumstantial evidence that they are the same field (the appointment time):**
- Both are quantized to the same 5-minute grid: scheduled dropoff is at `:00/:05/:10` for 339/341 trips
  (284 exactly on `:00`); the provider `Time` is `:00` for 61/63 numeric values.
- Scheduled dropoff is always ≥ scheduled pickup, consistent with "appointment time".
- ClaimInformation `Appt. Date` matches the BULK trip's date.

**Working assumption:** `ScheduledDropoffTime == provider Time == appointment time`. Treat as
**unconfirmed** until a single day has both a BULK upload and its provider export.

---

## 6. Will Call trips

In the provider export, **18 / 81 trips** have `Will Call Flag = Y` and `Time = "Will Call"` (no clock time).

- **All 18 are return legs** (trip number ending in `B`); 17 are `Trip Type = F`, 1 is `T`.
- Each has an outbound `A` leg with a **real appointment time** and the same mileage, e.g.:

| Will-Call trip | Time | Miles | Outbound `A` leg | Time | Miles |
|---|---|---|---|---|---|
| M4F25F15R0B | Will Call | 10.57 | M4F25F15R0A | 07:45 AM | 10.95 |
| M4H5K1DB40B | Will Call | 8.97 | M4H5K1DB40A | 12:45 PM | 8.97 |
| M4HQYPPLT0B | Will Call | 2.66 | M4HQYPPLT0A | 12:30 PM | 2.66 |
| M4JDSSCRD0B | Will Call | 7.75 | M4JDSSCRD0A | 11:20 AM | 7.80 |

**Conclusion:** a Will Call trip has **no scheduled pickup time** and no appointment time — it is the
on-demand return leg, called in after the outbound appointment. It therefore has **no lead to estimate**
and must be **excluded** from any mileage→pickup model. The September BULK files contain no Will-Call
rows (all 341 scheduled times are numeric), consistent with Will-Call trips not being pre-scheduled.

---

## 7. Formula used by the app

The regression above models the portal's scheduled pickup from the appointment:

```
calibrated pickup = appointment_time − (1.4 × miles + 14 min)
```

The app uses a two-step version so it can also produce a plausible **DropOff Time**:

```
dropoff = appointment_time − 1..5 min          # deterministic per trip
pickup  = dropoff − (14 + 1.4 × miles ± 3 min) # same travel-time fit, with jitter
```

So the generated pickup is intentionally **1–5 minutes earlier** than the single-line calibrated
value; the dropoff always lands just before the appointment. `tests/test_pickup.py` pins this
behavior (for example, 5.67 mi and a 10:00 appointment produce dropoff 09:56 and pickup 09:34).

- **ratio = 1.4 minutes per mile** (OLS slope; the "true driving speed" is ≈1.7 min/mile)
- **buffer = 14 minutes** (10–15 min range). The app does not round to the 5-minute grid.
- Residual spread of this fit is **sd ≈ 8 min** (p10 −10, p90 +8), so treat the output as a good
  default, not an exact value.

**If a single number is mandatory** (no buffer allowed): use **≈2.1 min/mile** (through-origin on the
scheduled data). This is only accurate near the median trip (~8 miles); it under-estimates the lead for
short trips and over-estimates it for long ones. The suspected **1.7 min/mile is the driving rate
only** — using it without the ~14 min buffer will schedule pickups too late for short local trips
(the bulk of the volume: 159/254 trips are < 10 miles).

### Caveats
1. **Sample:** 254 joined trips (238 clean), all from **Sep 1 – Oct 2**. Not yet validated on October.
2. **No October scheduled pickups exist**, and BULK↔provider overlap is 0 → the model is single-period.
3. **Mileage data errors:** 10 trips report 200–394 miles with a ~15–47 min lead (e.g. `M3Y8KUFHH1A`,
   394 mi / 15 min / $15). These are clearly bad mileage values and were excluded (`miles > 100`).
4. **Quantization:** scheduled times sit on a 5-minute grid, so individual ratios are noisy; the
   regression (not the per-trip ratio) is the reliable signal.
5. `ScheduledDropoffTime == provider Time` is **assumed, not proven** (§5).
6. Will Call trips have no appointment time and must be excluded (§6).
