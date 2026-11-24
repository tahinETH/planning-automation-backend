"use strict";

// lib/factory-time.ts
var FACTORY_TIME_ZONE = "Europe/Istanbul";
function factoryNowSerial(value = /* @__PURE__ */ new Date()) {
  return (Date.parse(`${factoryDateTimeInput(value)}:00Z`) - Date.UTC(1899, 11, 30)) / 864e5;
}
function factoryDateParts(value) {
  const parts = new Intl.DateTimeFormat("en-US", {
    timeZone: FACTORY_TIME_ZONE,
    year: "numeric",
    month: "2-digit",
    day: "2-digit"
  }).formatToParts(value);
  const part = (type) => Number(parts.find((item) => item.type === type)?.value ?? 0);
  return { year: part("year"), month: part("month"), day: part("day") };
}
function factoryDateInput(value = /* @__PURE__ */ new Date()) {
  const date = value instanceof Date ? value : new Date(value);
  const { year, month, day } = factoryDateParts(date);
  return `${String(year).padStart(4, "0")}-${String(month).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
}
function factoryDateTimeInput(value = /* @__PURE__ */ new Date()) {
  const date = value instanceof Date ? value : new Date(value);
  const parts = new Intl.DateTimeFormat("en-US", {
    timeZone: FACTORY_TIME_ZONE,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    hourCycle: "h23"
  }).formatToParts(date);
  const part = (type) => parts.find((item) => item.type === type)?.value ?? "00";
  return `${part("year")}-${part("month")}-${part("day")}T${part("hour")}:${part("minute")}`;
}
function factoryDateTimeToIso(value) {
  if (!/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}$/.test(value)) return "";
  const parsed = /* @__PURE__ */ new Date(`${value}:00+03:00`);
  return Number.isFinite(parsed.getTime()) ? parsed.toISOString() : "";
}

// data/process-master-data.json
var process_master_data_default = {
  version: 2,
  transferBatchQuantities: {
    drilling: 100
  },
  source: {
    kind: "one-time-foundation",
    files: [
      "Makine Kodlama Standart\u0131 (1).xlsx",
      "Delme ve \xC7apak alma Parametre bilgileri (1).xlsx"
    ],
    calculatedOnce: "GKM vardiyal\u0131k kapasiteleri kaynak \xE7al\u0131\u015Fma kitab\u0131ndan bir kez hesapland\u0131 ve yaln\u0131zca sonu\xE7 adetleri sakland\u0131."
  },
  machineCodeStandard: [
    {
      processGroup: "AZDIRMA",
      prefix: "HB",
      meaning: "Hobbing",
      example: "HB-01"
    },
    {
      processGroup: "BASIN\xC7LI YIKAMA",
      prefix: "W",
      meaning: "Washing",
      example: "W-01"
    },
    {
      processGroup: "CNC D\u0130K \u0130\u015ELEM",
      prefix: "MC",
      meaning: "Machining Center",
      example: "MC-01"
    },
    {
      processGroup: "CNC TORNA",
      prefix: "C",
      meaning: "CNC Turning Center",
      example: "C-01"
    },
    {
      processGroup: "\xC7AP TA\u015ELAMA",
      prefix: "CG",
      meaning: "Cylindrical Grinding",
      example: "CG-01"
    },
    {
      processGroup: "\xC7APAK ALMA",
      prefix: "B",
      meaning: "Deburring / Burr Removal",
      example: "B-01"
    },
    {
      processGroup: "DELME",
      prefix: "D",
      meaning: "Drilling",
      example: "D-01"
    },
    {
      processGroup: "DO\u011ERULTMA",
      prefix: "ST",
      meaning: "Straightening",
      example: "ST-01"
    },
    {
      processGroup: "EDDY CURRENT",
      prefix: "EC",
      meaning: "Eddy Current",
      example: "EC-01"
    },
    {
      processGroup: "EZME",
      prefix: "BR",
      meaning: "Burnishing",
      example: "BR-01"
    },
    {
      processGroup: "F\u0130LTRE \xC7AKMA",
      prefix: "FP",
      meaning: "Filter Press / Fitting",
      example: "FP-01"
    },
    {
      processGroup: "F\u0130NAL KONTROL",
      prefix: "FI",
      meaning: "Final Inspection",
      example: "FI-01"
    },
    {
      processGroup: "FORM TA\u015ELAMA",
      prefix: "FG",
      meaning: "Form Grinding",
      example: "FG-01"
    },
    {
      processGroup: "FREZE",
      prefix: "M",
      meaning: "Milling",
      example: "M-01"
    },
    {
      processGroup: "G\xD6Z KONTROL",
      prefix: "V",
      meaning: "Visual Inspection",
      example: "V-01"
    },
    {
      processGroup: "GTM",
      prefix: "GTM",
      meaning: "Mevcut \xF6zel proses / makine grubu kodu",
      example: "GTM-01"
    },
    {
      processGroup: "HONLAMA",
      prefix: "H",
      meaning: "Honing",
      example: "H-01"
    },
    {
      processGroup: "\xD6L\xC7ME",
      prefix: "ME",
      meaning: "Measurement",
      example: "ME-01"
    },
    {
      processGroup: "TA\u015ELAMA",
      prefix: "G",
      meaning: "Grinding",
      example: "G-01"
    },
    {
      processGroup: "TESTERE-KESME",
      prefix: "SC",
      meaning: "Saw Cutting",
      example: "SC-01"
    },
    {
      processGroup: "TORNA",
      prefix: "L",
      meaning: "Lathe",
      example: "L-01"
    },
    {
      processGroup: "TORNA-SERT",
      prefix: "HT",
      meaning: "Hard Turning",
      example: "HT-01"
    }
  ],
  resources: [
    {
      id: "C-01",
      sourceProgramId: "C-01",
      erpWorkCenterCode: "01-16-02-002",
      name: "1-CITIZEN (Cincom)",
      operationCode: "010",
      operationName: "CNC TORNA",
      process: "turning",
      active: true,
      defaultShifts: 3
    },
    {
      id: "C-02",
      sourceProgramId: "C-02",
      erpWorkCenterCode: "01-16-02-003",
      name: "2-CITIZEN (Cincom)",
      operationCode: "010",
      operationName: "CNC TORNA",
      process: "turning",
      active: true,
      defaultShifts: 3
    },
    {
      id: "C-03",
      sourceProgramId: "C-03",
      erpWorkCenterCode: "01-16-02-004",
      name: "3-CITIZEN (Cincom)",
      operationCode: "010",
      operationName: "CNC TORNA",
      process: "turning",
      active: true,
      defaultShifts: 3
    },
    {
      id: "C-04",
      sourceProgramId: "C-04",
      erpWorkCenterCode: "01-16-02-005",
      name: "4-CITIZEN (Cincom)",
      operationCode: "010",
      operationName: "CNC TORNA",
      process: "turning",
      active: true,
      defaultShifts: 3
    },
    {
      id: "C-05",
      sourceProgramId: "C-05",
      erpWorkCenterCode: "01-16-02-006",
      name: "5-CITIZEN (Cincom)",
      operationCode: "010",
      operationName: "CNC TORNA",
      process: "turning",
      active: true,
      defaultShifts: 3
    },
    {
      id: "C-06",
      sourceProgramId: "C-06",
      erpWorkCenterCode: "01-16-02-007",
      name: "6-CITIZEN (Cincom)",
      operationCode: "010",
      operationName: "CNC TORNA",
      process: "turning",
      active: true,
      defaultShifts: 3
    },
    {
      id: "C-07",
      sourceProgramId: "C-07",
      erpWorkCenterCode: "01-16-02-008",
      name: "7-CITIZEN (Cincom)",
      operationCode: "010",
      operationName: "CNC TORNA",
      process: "turning",
      active: true,
      defaultShifts: 3
    },
    {
      id: "C-08",
      sourceProgramId: "C-08",
      erpWorkCenterCode: "01-16-02-010",
      name: "DOOSAN PUMA",
      operationCode: "010",
      operationName: "CNC TORNA",
      process: "turning",
      active: true,
      defaultShifts: 3
    },
    {
      id: "C-09",
      sourceProgramId: "C-09",
      erpWorkCenterCode: "01-10-02-005",
      name: "INDEX MS 32-1",
      operationCode: "010",
      operationName: "CNC TORNA",
      process: "turning",
      active: true,
      defaultShifts: 3
    },
    {
      id: "C-10",
      sourceProgramId: "C-10",
      erpWorkCenterCode: "01-16-02-009",
      name: "NOMURADS",
      operationCode: "010",
      operationName: "CNC TORNA",
      process: "turning",
      active: true,
      defaultShifts: 3
    },
    {
      id: "C-11",
      sourceProgramId: "C-11",
      erpWorkCenterCode: "01-13-02-006",
      name: "1-MIYANO ABX-64TH2",
      operationCode: "010",
      operationName: "CNC TORNA",
      process: "turning",
      active: true,
      defaultShifts: 3
    },
    {
      id: "C-12",
      sourceProgramId: "C-12",
      erpWorkCenterCode: "01-13-02-007",
      name: "2-MIYANO ABX-64TH2",
      operationCode: "010",
      operationName: "CNC TORNA",
      process: "turning",
      active: true,
      defaultShifts: 3
    },
    {
      id: "C-13",
      sourceProgramId: "C-13",
      erpWorkCenterCode: "01-20-02-002",
      name: "CITIZEN M32-2",
      operationCode: "010",
      operationName: "CNC TORNA",
      process: "turning",
      active: true,
      defaultShifts: 3
    },
    {
      id: "C-14",
      sourceProgramId: "C-14",
      erpWorkCenterCode: "01-20-02-001",
      name: "CITIZEN M32-1",
      operationCode: "010",
      operationName: "CNC TORNA",
      process: "turning",
      active: true,
      defaultShifts: 3
    },
    {
      id: "C-15",
      sourceProgramId: "C-15",
      erpWorkCenterCode: "01-20-02-003",
      name: "CITIZEN M32-3",
      operationCode: "010",
      operationName: "CNC TORNA",
      process: "turning",
      active: true,
      defaultShifts: 3
    },
    {
      id: "C-16",
      sourceProgramId: "C-16",
      erpWorkCenterCode: "Fason-1",
      name: "BENTRO",
      operationCode: "010",
      operationName: "CNC TORNA",
      process: "turning",
      active: true,
      defaultShifts: 3
    },
    {
      id: "C-17",
      sourceProgramId: "C-17",
      erpWorkCenterCode: "Fason-2",
      name: "YALIN OTO",
      operationCode: "010",
      operationName: "CNC TORNA",
      process: "turning",
      active: true,
      defaultShifts: 3
    },
    {
      id: "D-01",
      sourceProgramId: "D-01",
      erpWorkCenterCode: "01-16-09-003",
      name: "TBT SL250-4 SELSA",
      operationCode: "040",
      operationName: "DELME",
      process: "drilling",
      active: true,
      defaultShifts: 3
    },
    {
      id: "D-02",
      sourceProgramId: "D-02",
      erpWorkCenterCode: "01-16-09-002",
      name: "TBT SL200-2 SELSA",
      operationCode: "040",
      operationName: "DELME",
      process: "drilling",
      active: true,
      defaultShifts: 3
    },
    {
      id: "B-01-S1",
      sourceProgramId: "B-01 / S1",
      erpWorkCenterCode: "01-16-10-002",
      name: "1.\u0130stasyon/\xC7APAK ALMA MAK\u0130NES\u0130 SELSA - 2",
      operationCode: "060",
      operationName: "\xC7APAK ALMA",
      process: "deburring",
      active: true,
      defaultShifts: 3
    },
    {
      id: "B-01-S2",
      sourceProgramId: "B-01 / S2",
      erpWorkCenterCode: "01-16-10-002",
      name: "2.\u0130stasyon/\xC7APAK ALMA MAK\u0130NES\u0130 SELSA - 2",
      operationCode: "060",
      operationName: "\xC7APAK ALMA",
      process: "deburring",
      active: true,
      defaultShifts: 3
    },
    {
      id: "V-01",
      sourceProgramId: "V-01",
      erpWorkCenterCode: "01-21-16-001",
      name: "GKM-1 TEKNOSKOP",
      operationCode: "290",
      operationName: "G\xD6Z KONTROL",
      process: "gkm",
      active: true,
      defaultShifts: 3
    },
    {
      id: "V-02",
      sourceProgramId: "V-02",
      erpWorkCenterCode: "01-21-16-002",
      name: "GKM-2 TEKNOSKOP",
      operationCode: "290",
      operationName: "G\xD6Z KONTROL",
      process: "gkm",
      active: true,
      defaultShifts: 3
    },
    {
      id: "V-03",
      sourceProgramId: "V-03",
      erpWorkCenterCode: "01-21-16-003",
      name: "GKM-3 TEKNOSKOP",
      operationCode: "290",
      operationName: "G\xD6Z KONTROL",
      process: "gkm",
      active: true,
      defaultShifts: 3
    },
    {
      id: "V-04",
      sourceProgramId: "V-04",
      erpWorkCenterCode: "01-21-16-004",
      name: "GKM-4 TEKNOSKOP",
      operationCode: "290",
      operationName: "G\xD6Z KONTROL",
      process: "gkm",
      active: true,
      defaultShifts: 3
    },
    {
      id: "V-05",
      sourceProgramId: "V-05",
      erpWorkCenterCode: "01-21-16-005",
      name: "GKM-5 TEKNOSKOP",
      operationCode: "290",
      operationName: "G\xD6Z KONTROL",
      process: "gkm",
      active: true,
      defaultShifts: 3
    },
    {
      id: "V-06",
      sourceProgramId: "V-06",
      erpWorkCenterCode: "01-21-16-006",
      name: "GKM-6 TEKNOSKOP",
      operationCode: "290",
      operationName: "G\xD6Z KONTROL",
      process: "gkm",
      active: true,
      defaultShifts: 3
    },
    {
      id: "V-07",
      sourceProgramId: "V-07",
      erpWorkCenterCode: "01-21-16-007",
      name: "GKM-7 TEKNOSKOP",
      operationCode: "290",
      operationName: "G\xD6Z KONTROL",
      process: "gkm",
      active: true,
      defaultShifts: 3
    },
    {
      id: "V-08",
      sourceProgramId: "V-08",
      erpWorkCenterCode: "01-21-16-008",
      name: "GKM-8 TEKNOSKOP",
      operationCode: "290",
      operationName: "G\xD6Z KONTROL",
      process: "gkm",
      active: true,
      defaultShifts: 3
    },
    {
      id: "V-09",
      sourceProgramId: "V-09",
      erpWorkCenterCode: "01-21-16-011",
      name: "VISION TEKNOSKOP",
      operationCode: "290",
      operationName: "G\xD6Z KONTROL",
      process: "gkm",
      active: true,
      defaultShifts: 3
    }
  ],
  products: [
    {
      product: "R902200287",
      family: "center-pin",
      processes: [
        {
          process: "drilling",
          sequence: 1,
          waitWorkdaysBefore: 0,
          setupKey: "\xD83,0",
          resourcePriority: [
            "D-02"
          ],
          unitsPerShift: {
            "D-02": 793
          }
        },
        {
          process: "gkm",
          sequence: 2,
          waitWorkdaysBefore: 1,
          setupKey: "GKM",
          resourcePriority: [
            "V-01",
            "V-02",
            "V-03",
            "V-04",
            "V-05",
            "V-06",
            "V-07",
            "V-08",
            "V-09"
          ],
          unitsPerShift: {
            "V-01": 1428,
            "V-02": 1428,
            "V-03": 1428,
            "V-04": 1428,
            "V-05": 1428,
            "V-06": 1428,
            "V-07": 1428,
            "V-08": 1428,
            "V-09": 1428
          }
        }
      ]
    },
    {
      product: "R902375400",
      family: "center-pin",
      processes: [
        {
          process: "drilling",
          sequence: 1,
          waitWorkdaysBefore: 0,
          setupKey: "\xD83,2",
          resourcePriority: [
            "D-02"
          ],
          unitsPerShift: {
            "D-02": 659
          }
        },
        {
          process: "gkm",
          sequence: 2,
          waitWorkdaysBefore: 1,
          setupKey: "GKM",
          resourcePriority: [
            "V-01",
            "V-02",
            "V-03",
            "V-04",
            "V-05",
            "V-06",
            "V-07",
            "V-08",
            "V-09"
          ],
          unitsPerShift: {
            "V-01": 1071,
            "V-02": 1071,
            "V-03": 1071,
            "V-04": 1071,
            "V-05": 1071,
            "V-06": 1071,
            "V-07": 1071,
            "V-08": 1071,
            "V-09": 1071
          }
        }
      ]
    },
    {
      product: "R902719052",
      family: "center-pin",
      processes: [
        {
          process: "drilling",
          sequence: 1,
          waitWorkdaysBefore: 0,
          setupKey: "\xD83,0",
          resourcePriority: [
            "D-02"
          ],
          unitsPerShift: {
            "D-02": 793
          }
        },
        {
          process: "gkm",
          sequence: 2,
          waitWorkdaysBefore: 1,
          setupKey: "GKM",
          resourcePriority: [
            "V-01",
            "V-02",
            "V-03",
            "V-04",
            "V-05",
            "V-06",
            "V-07",
            "V-08",
            "V-09"
          ],
          unitsPerShift: {
            "V-01": 1428,
            "V-02": 1428,
            "V-03": 1428,
            "V-04": 1428,
            "V-05": 1428,
            "V-06": 1428,
            "V-07": 1428,
            "V-08": 1428,
            "V-09": 1428
          }
        }
      ]
    },
    {
      product: "R902719076",
      family: "center-pin",
      processes: [
        {
          process: "drilling",
          sequence: 1,
          waitWorkdaysBefore: 0,
          setupKey: "\xD82,5",
          resourcePriority: [
            "D-02"
          ],
          unitsPerShift: {
            "D-02": 1586
          }
        },
        {
          process: "gkm",
          sequence: 2,
          waitWorkdaysBefore: 1,
          setupKey: "GKM",
          resourcePriority: [
            "V-01",
            "V-02",
            "V-03",
            "V-04",
            "V-05",
            "V-06",
            "V-07",
            "V-08",
            "V-09"
          ],
          unitsPerShift: {
            "V-01": 1428,
            "V-02": 1428,
            "V-03": 1428,
            "V-04": 1428,
            "V-05": 1428,
            "V-06": 1428,
            "V-07": 1428,
            "V-08": 1428,
            "V-09": 1428
          }
        }
      ]
    },
    {
      product: "R902719738",
      family: "center-pin",
      processes: [
        {
          process: "drilling",
          sequence: 1,
          waitWorkdaysBefore: 0,
          setupKey: "\xD83,0",
          resourcePriority: [
            "D-02"
          ],
          unitsPerShift: {
            "D-02": 1557
          }
        },
        {
          process: "gkm",
          sequence: 2,
          waitWorkdaysBefore: 1,
          setupKey: "GKM",
          resourcePriority: [
            "V-01",
            "V-02",
            "V-03",
            "V-04",
            "V-05",
            "V-06",
            "V-07",
            "V-08",
            "V-09"
          ],
          unitsPerShift: {
            "V-01": 1127,
            "V-02": 1127,
            "V-03": 1127,
            "V-04": 1127,
            "V-05": 1127,
            "V-06": 1127,
            "V-07": 1127,
            "V-08": 1127,
            "V-09": 1127
          }
        }
      ]
    },
    {
      product: "R902719739",
      family: "center-pin",
      processes: [
        {
          process: "drilling",
          sequence: 1,
          waitWorkdaysBefore: 0,
          setupKey: "\xD83,2",
          resourcePriority: [
            "D-02"
          ],
          unitsPerShift: {
            "D-02": 1190
          }
        },
        {
          process: "gkm",
          sequence: 2,
          waitWorkdaysBefore: 1,
          setupKey: "GKM",
          resourcePriority: [
            "V-01",
            "V-02",
            "V-03",
            "V-04",
            "V-05",
            "V-06",
            "V-07",
            "V-08",
            "V-09"
          ],
          unitsPerShift: {
            "V-01": 1127,
            "V-02": 1127,
            "V-03": 1127,
            "V-04": 1127,
            "V-05": 1127,
            "V-06": 1127,
            "V-07": 1127,
            "V-08": 1127,
            "V-09": 1127
          }
        }
      ]
    },
    {
      product: "R902719740",
      family: "center-pin",
      processes: [
        {
          process: "drilling",
          sequence: 1,
          waitWorkdaysBefore: 0,
          setupKey: "\xD83,5",
          resourcePriority: [
            "D-02"
          ],
          unitsPerShift: {
            "D-02": 680
          }
        },
        {
          process: "gkm",
          sequence: 2,
          waitWorkdaysBefore: 1,
          setupKey: "GKM",
          resourcePriority: [
            "V-01",
            "V-02",
            "V-03",
            "V-04",
            "V-05",
            "V-06",
            "V-07",
            "V-08",
            "V-09"
          ],
          unitsPerShift: {
            "V-01": 714,
            "V-02": 714,
            "V-03": 714,
            "V-04": 714,
            "V-05": 714,
            "V-06": 714,
            "V-07": 714,
            "V-08": 714,
            "V-09": 714
          }
        }
      ]
    },
    {
      product: "R902719741",
      family: "center-pin",
      processes: [
        {
          process: "drilling",
          sequence: 1,
          waitWorkdaysBefore: 0,
          setupKey: "\xD84,0",
          resourcePriority: [
            "D-02"
          ],
          unitsPerShift: {
            "D-02": 1224
          }
        },
        {
          process: "gkm",
          sequence: 2,
          waitWorkdaysBefore: 1,
          setupKey: "GKM",
          resourcePriority: [
            "V-01",
            "V-02",
            "V-03",
            "V-04",
            "V-05",
            "V-06",
            "V-07",
            "V-08",
            "V-09"
          ],
          unitsPerShift: {
            "V-01": 1071,
            "V-02": 1071,
            "V-03": 1071,
            "V-04": 1071,
            "V-05": 1071,
            "V-06": 1071,
            "V-07": 1071,
            "V-08": 1071,
            "V-09": 1071
          }
        }
      ]
    },
    {
      product: "R902719742",
      family: "center-pin",
      processes: [
        {
          process: "drilling",
          sequence: 1,
          waitWorkdaysBefore: 0,
          setupKey: "\xD84,5",
          resourcePriority: [
            "D-02"
          ],
          unitsPerShift: {
            "D-02": 1098
          }
        },
        {
          process: "gkm",
          sequence: 2,
          waitWorkdaysBefore: 1,
          setupKey: "GKM",
          resourcePriority: [
            "V-01",
            "V-02",
            "V-03",
            "V-04",
            "V-05",
            "V-06",
            "V-07",
            "V-08",
            "V-09"
          ],
          unitsPerShift: {
            "V-01": 856,
            "V-02": 856,
            "V-03": 856,
            "V-04": 856,
            "V-05": 856,
            "V-06": 856,
            "V-07": 856,
            "V-08": 856,
            "V-09": 856
          }
        }
      ]
    },
    {
      product: "R902719743",
      family: "center-pin",
      processes: [
        {
          process: "drilling",
          sequence: 1,
          waitWorkdaysBefore: 0,
          setupKey: "\xD82,5",
          resourcePriority: [
            "D-02"
          ],
          unitsPerShift: {
            "D-02": 1586
          }
        },
        {
          process: "gkm",
          sequence: 2,
          waitWorkdaysBefore: 1,
          setupKey: "GKM",
          resourcePriority: [
            "V-01",
            "V-02",
            "V-03",
            "V-04",
            "V-05",
            "V-06",
            "V-07",
            "V-08",
            "V-09"
          ],
          unitsPerShift: {
            "V-01": 1428,
            "V-02": 1428,
            "V-03": 1428,
            "V-04": 1428,
            "V-05": 1428,
            "V-06": 1428,
            "V-07": 1428,
            "V-08": 1428,
            "V-09": 1428
          }
        }
      ]
    },
    {
      product: "R902719762",
      family: "center-pin",
      processes: [
        {
          process: "drilling",
          sequence: 1,
          waitWorkdaysBefore: 0,
          setupKey: "\xD82,5",
          resourcePriority: [
            "D-02"
          ],
          unitsPerShift: {
            "D-02": 1586
          }
        },
        {
          process: "gkm",
          sequence: 2,
          waitWorkdaysBefore: 1,
          setupKey: "GKM",
          resourcePriority: [
            "V-01",
            "V-02",
            "V-03",
            "V-04",
            "V-05",
            "V-06",
            "V-07",
            "V-08",
            "V-09"
          ],
          unitsPerShift: {
            "V-01": 1428,
            "V-02": 1428,
            "V-03": 1428,
            "V-04": 1428,
            "V-05": 1428,
            "V-06": 1428,
            "V-07": 1428,
            "V-08": 1428,
            "V-09": 1428
          }
        }
      ]
    },
    {
      product: "R902719763",
      family: "center-pin",
      processes: [
        {
          process: "drilling",
          sequence: 1,
          waitWorkdaysBefore: 0,
          setupKey: "\xD82,5",
          resourcePriority: [
            "D-02"
          ],
          unitsPerShift: {
            "D-02": 680
          }
        },
        {
          process: "gkm",
          sequence: 2,
          waitWorkdaysBefore: 1,
          setupKey: "GKM",
          resourcePriority: [
            "V-01",
            "V-02",
            "V-03",
            "V-04",
            "V-05",
            "V-06",
            "V-07",
            "V-08",
            "V-09"
          ],
          unitsPerShift: {
            "V-01": 1428,
            "V-02": 1428,
            "V-03": 1428,
            "V-04": 1428,
            "V-05": 1428,
            "V-06": 1428,
            "V-07": 1428,
            "V-08": 1428,
            "V-09": 1428
          }
        }
      ]
    },
    {
      product: "R902719764",
      family: "center-pin",
      processes: [
        {
          process: "drilling",
          sequence: 1,
          waitWorkdaysBefore: 0,
          setupKey: "\xD82,5",
          resourcePriority: [
            "D-02"
          ],
          unitsPerShift: {
            "D-02": 612
          }
        },
        {
          process: "gkm",
          sequence: 2,
          waitWorkdaysBefore: 1,
          setupKey: "GKM",
          resourcePriority: [
            "V-01",
            "V-02",
            "V-03",
            "V-04",
            "V-05",
            "V-06",
            "V-07",
            "V-08",
            "V-09"
          ],
          unitsPerShift: {
            "V-01": 1127,
            "V-02": 1127,
            "V-03": 1127,
            "V-04": 1127,
            "V-05": 1127,
            "V-06": 1127,
            "V-07": 1127,
            "V-08": 1127,
            "V-09": 1127
          }
        }
      ]
    },
    {
      product: "R902719765",
      family: "center-pin",
      processes: [
        {
          process: "drilling",
          sequence: 1,
          waitWorkdaysBefore: 0,
          setupKey: "\xD83,5",
          resourcePriority: [
            "D-02"
          ],
          unitsPerShift: {
            "D-02": 612
          }
        },
        {
          process: "gkm",
          sequence: 2,
          waitWorkdaysBefore: 1,
          setupKey: "GKM",
          resourcePriority: [
            "V-01",
            "V-02",
            "V-03",
            "V-04",
            "V-05",
            "V-06",
            "V-07",
            "V-08",
            "V-09"
          ],
          unitsPerShift: {
            "V-01": 1127,
            "V-02": 1127,
            "V-03": 1127,
            "V-04": 1127,
            "V-05": 1127,
            "V-06": 1127,
            "V-07": 1127,
            "V-08": 1127,
            "V-09": 1127
          }
        }
      ]
    },
    {
      product: "R902719766",
      family: "center-pin",
      processes: [
        {
          process: "drilling",
          sequence: 1,
          waitWorkdaysBefore: 0,
          setupKey: "\xD83,5",
          resourcePriority: [
            "D-02"
          ],
          unitsPerShift: {
            "D-02": 669
          }
        },
        {
          process: "gkm",
          sequence: 2,
          waitWorkdaysBefore: 1,
          setupKey: "GKM",
          resourcePriority: [
            "V-01",
            "V-02",
            "V-03",
            "V-04",
            "V-05",
            "V-06",
            "V-07",
            "V-08",
            "V-09"
          ],
          unitsPerShift: {
            "V-01": 1071,
            "V-02": 1071,
            "V-03": 1071,
            "V-04": 1071,
            "V-05": 1071,
            "V-06": 1071,
            "V-07": 1071,
            "V-08": 1071,
            "V-09": 1071
          }
        }
      ]
    },
    {
      product: "R902719767",
      family: "center-pin",
      processes: [
        {
          process: "drilling",
          sequence: 1,
          waitWorkdaysBefore: 0,
          setupKey: "\xD83,5",
          resourcePriority: [
            "D-02"
          ],
          unitsPerShift: {
            "D-02": 522
          }
        },
        {
          process: "gkm",
          sequence: 2,
          waitWorkdaysBefore: 1,
          setupKey: "GKM",
          resourcePriority: [
            "V-01",
            "V-02",
            "V-03",
            "V-04",
            "V-05",
            "V-06",
            "V-07",
            "V-08",
            "V-09"
          ],
          unitsPerShift: {
            "V-01": 856,
            "V-02": 856,
            "V-03": 856,
            "V-04": 856,
            "V-05": 856,
            "V-06": 856,
            "V-07": 856,
            "V-08": 856,
            "V-09": 856
          }
        }
      ]
    },
    {
      product: "R902719768",
      family: "center-pin",
      processes: [
        {
          process: "drilling",
          sequence: 1,
          waitWorkdaysBefore: 0,
          setupKey: "\xD84,5",
          resourcePriority: [
            "D-02"
          ],
          unitsPerShift: {
            "D-02": 1098
          }
        },
        {
          process: "gkm",
          sequence: 2,
          waitWorkdaysBefore: 1,
          setupKey: "GKM",
          resourcePriority: [
            "V-01",
            "V-02",
            "V-03",
            "V-04",
            "V-05",
            "V-06",
            "V-07",
            "V-08",
            "V-09"
          ],
          unitsPerShift: {
            "V-01": 856,
            "V-02": 856,
            "V-03": 856,
            "V-04": 856,
            "V-05": 856,
            "V-06": 856,
            "V-07": 856,
            "V-08": 856,
            "V-09": 856
          }
        }
      ]
    },
    {
      product: "R902719812",
      family: "piston",
      processes: [
        {
          process: "drilling",
          sequence: 1,
          waitWorkdaysBefore: 0,
          setupKey: "\xD82,5",
          resourcePriority: [
            "D-01",
            "D-02"
          ],
          unitsPerShift: {
            "D-01": 1586,
            "D-02": 793
          }
        },
        {
          process: "deburring",
          sequence: 2,
          waitWorkdaysBefore: 0,
          setupKey: "--",
          resourcePriority: [
            "B-01-S1",
            "B-01-S2"
          ],
          unitsPerShift: {
            "B-01-S1": 1338,
            "B-01-S2": 1338
          }
        },
        {
          process: "gkm",
          sequence: 3,
          waitWorkdaysBefore: 1,
          setupKey: "GKM",
          resourcePriority: [
            "V-01",
            "V-02",
            "V-03",
            "V-04",
            "V-05",
            "V-06",
            "V-07",
            "V-08",
            "V-09"
          ],
          unitsPerShift: {
            "V-01": 1428,
            "V-02": 1428,
            "V-03": 1428,
            "V-04": 1428,
            "V-05": 1428,
            "V-06": 1428,
            "V-07": 1428,
            "V-08": 1428,
            "V-09": 1428
          }
        }
      ]
    },
    {
      product: "R902725682",
      family: "center-pin",
      processes: [
        {
          process: "drilling",
          sequence: 1,
          waitWorkdaysBefore: 0,
          setupKey: "\xD82,3",
          resourcePriority: [
            "D-02"
          ],
          unitsPerShift: {
            "D-02": 1586
          }
        },
        {
          process: "gkm",
          sequence: 2,
          waitWorkdaysBefore: 1,
          setupKey: "GKM",
          resourcePriority: [
            "V-01",
            "V-02",
            "V-03",
            "V-04",
            "V-05",
            "V-06",
            "V-07",
            "V-08",
            "V-09"
          ],
          unitsPerShift: {
            "V-01": 1428,
            "V-02": 1428,
            "V-03": 1428,
            "V-04": 1428,
            "V-05": 1428,
            "V-06": 1428,
            "V-07": 1428,
            "V-08": 1428,
            "V-09": 1428
          }
        }
      ]
    },
    {
      product: "R902729695",
      family: "center-pin",
      processes: [
        {
          process: "drilling",
          sequence: 1,
          waitWorkdaysBefore: 0,
          setupKey: "\xD83,5",
          resourcePriority: [
            "D-02"
          ],
          unitsPerShift: {
            "D-02": 659
          }
        },
        {
          process: "gkm",
          sequence: 2,
          waitWorkdaysBefore: 1,
          setupKey: "GKM",
          resourcePriority: [
            "V-01",
            "V-02",
            "V-03",
            "V-04",
            "V-05",
            "V-06",
            "V-07",
            "V-08",
            "V-09"
          ],
          unitsPerShift: {
            "V-01": 1071,
            "V-02": 1071,
            "V-03": 1071,
            "V-04": 1071,
            "V-05": 1071,
            "V-06": 1071,
            "V-07": 1071,
            "V-08": 1071,
            "V-09": 1071
          }
        }
      ]
    },
    {
      product: "R902729941",
      family: "center-pin",
      processes: [
        {
          process: "drilling",
          sequence: 1,
          waitWorkdaysBefore: 0,
          setupKey: "\xD84,0",
          resourcePriority: [
            "D-02"
          ],
          unitsPerShift: {
            "D-02": 1224
          }
        },
        {
          process: "gkm",
          sequence: 2,
          waitWorkdaysBefore: 1,
          setupKey: "GKM",
          resourcePriority: [
            "V-01",
            "V-02",
            "V-03",
            "V-04",
            "V-05",
            "V-06",
            "V-07",
            "V-08",
            "V-09"
          ],
          unitsPerShift: {
            "V-01": 856,
            "V-02": 856,
            "V-03": 856,
            "V-04": 856,
            "V-05": 856,
            "V-06": 856,
            "V-07": 856,
            "V-08": 856,
            "V-09": 856
          }
        }
      ]
    },
    {
      product: "R902744004",
      family: "center-pin",
      processes: [
        {
          process: "drilling",
          sequence: 1,
          waitWorkdaysBefore: 0,
          setupKey: "\xD84,5",
          resourcePriority: [
            "D-02"
          ],
          unitsPerShift: {
            "D-02": 1098
          }
        },
        {
          process: "gkm",
          sequence: 2,
          waitWorkdaysBefore: 1,
          setupKey: "GKM",
          resourcePriority: [
            "V-01",
            "V-02",
            "V-03",
            "V-04",
            "V-05",
            "V-06",
            "V-07",
            "V-08",
            "V-09"
          ],
          unitsPerShift: {
            "V-01": 856,
            "V-02": 856,
            "V-03": 856,
            "V-04": 856,
            "V-05": 856,
            "V-06": 856,
            "V-07": 856,
            "V-08": 856,
            "V-09": 856
          }
        }
      ]
    },
    {
      product: "R902745116",
      family: "piston",
      processes: [
        {
          process: "drilling",
          sequence: 1,
          waitWorkdaysBefore: 0,
          setupKey: "\xD83,0",
          resourcePriority: [
            "D-01",
            "D-02"
          ],
          unitsPerShift: {
            "D-01": 1557,
            "D-02": 778
          }
        },
        {
          process: "deburring",
          sequence: 2,
          waitWorkdaysBefore: 0,
          setupKey: "--",
          resourcePriority: [
            "B-01-S1",
            "B-01-S2"
          ],
          unitsPerShift: {
            "B-01-S1": 1298,
            "B-01-S2": 1298
          }
        },
        {
          process: "gkm",
          sequence: 3,
          waitWorkdaysBefore: 1,
          setupKey: "GKM",
          resourcePriority: [
            "V-01",
            "V-02",
            "V-03",
            "V-04",
            "V-05",
            "V-06",
            "V-07",
            "V-08",
            "V-09"
          ],
          unitsPerShift: {
            "V-01": 1127,
            "V-02": 1127,
            "V-03": 1127,
            "V-04": 1127,
            "V-05": 1127,
            "V-06": 1127,
            "V-07": 1127,
            "V-08": 1127,
            "V-09": 1127
          }
        }
      ]
    },
    {
      product: "R902745117",
      family: "piston",
      processes: [
        {
          process: "drilling",
          sequence: 1,
          waitWorkdaysBefore: 0,
          setupKey: "\xD83,5",
          resourcePriority: [
            "D-01",
            "D-02"
          ],
          unitsPerShift: {
            "D-01": 1318,
            "D-02": 659
          }
        },
        {
          process: "deburring",
          sequence: 2,
          waitWorkdaysBefore: 0,
          setupKey: "--",
          resourcePriority: [
            "B-01-S1",
            "B-01-S2"
          ],
          unitsPerShift: {
            "B-01-S1": 1224,
            "B-01-S2": 1224
          }
        },
        {
          process: "gkm",
          sequence: 3,
          waitWorkdaysBefore: 1,
          setupKey: "GKM",
          resourcePriority: [
            "V-01",
            "V-02",
            "V-03",
            "V-04",
            "V-05",
            "V-06",
            "V-07",
            "V-08",
            "V-09"
          ],
          unitsPerShift: {
            "V-01": 1071,
            "V-02": 1071,
            "V-03": 1071,
            "V-04": 1071,
            "V-05": 1071,
            "V-06": 1071,
            "V-07": 1071,
            "V-08": 1071,
            "V-09": 1071
          }
        }
      ]
    },
    {
      product: "R902745119",
      family: "piston",
      processes: [
        {
          process: "drilling",
          sequence: 1,
          waitWorkdaysBefore: 0,
          setupKey: "\xD83,0",
          resourcePriority: [
            "D-01",
            "D-02"
          ],
          unitsPerShift: {
            "D-01": 1428,
            "D-02": 714
          }
        },
        {
          process: "deburring",
          sequence: 2,
          waitWorkdaysBefore: 0,
          setupKey: "--",
          resourcePriority: [
            "B-01-S1",
            "B-01-S2"
          ],
          unitsPerShift: {
            "B-01-S1": 1298,
            "B-01-S2": 1298
          }
        },
        {
          process: "gkm",
          sequence: 3,
          waitWorkdaysBefore: 1,
          setupKey: "GKM",
          resourcePriority: [
            "V-01",
            "V-02",
            "V-03",
            "V-04",
            "V-05",
            "V-06",
            "V-07",
            "V-08",
            "V-09"
          ],
          unitsPerShift: {
            "V-01": 1127,
            "V-02": 1127,
            "V-03": 1127,
            "V-04": 1127,
            "V-05": 1127,
            "V-06": 1127,
            "V-07": 1127,
            "V-08": 1127,
            "V-09": 1127
          }
        }
      ]
    },
    {
      product: "R902745121",
      family: "piston",
      processes: [
        {
          process: "drilling",
          sequence: 1,
          waitWorkdaysBefore: 0,
          setupKey: "\xD83,0",
          resourcePriority: [
            "D-01",
            "D-02"
          ],
          unitsPerShift: {
            "D-01": 1404,
            "D-02": 702
          }
        },
        {
          process: "deburring",
          sequence: 2,
          waitWorkdaysBefore: 0,
          setupKey: "--",
          resourcePriority: [
            "B-01-S1",
            "B-01-S2"
          ],
          unitsPerShift: {
            "B-01-S1": 1298,
            "B-01-S2": 1298
          }
        },
        {
          process: "gkm",
          sequence: 3,
          waitWorkdaysBefore: 1,
          setupKey: "GKM",
          resourcePriority: [
            "V-01",
            "V-02",
            "V-03",
            "V-04",
            "V-05",
            "V-06",
            "V-07",
            "V-08",
            "V-09"
          ],
          unitsPerShift: {
            "V-01": 1127,
            "V-02": 1127,
            "V-03": 1127,
            "V-04": 1127,
            "V-05": 1127,
            "V-06": 1127,
            "V-07": 1127,
            "V-08": 1127,
            "V-09": 1127
          }
        }
      ]
    },
    {
      product: "R902745123",
      family: "piston",
      processes: [
        {
          process: "drilling",
          sequence: 1,
          waitWorkdaysBefore: 0,
          setupKey: "\xD83,5",
          resourcePriority: [
            "D-01",
            "D-02"
          ],
          unitsPerShift: {
            "D-01": 1477,
            "D-02": 738
          }
        },
        {
          process: "deburring",
          sequence: 2,
          waitWorkdaysBefore: 0,
          setupKey: "--",
          resourcePriority: [
            "B-01-S1",
            "B-01-S2"
          ],
          unitsPerShift: {
            "B-01-S1": 1338,
            "B-01-S2": 1338
          }
        },
        {
          process: "gkm",
          sequence: 3,
          waitWorkdaysBefore: 1,
          setupKey: "GKM",
          resourcePriority: [
            "V-01",
            "V-02",
            "V-03",
            "V-04",
            "V-05",
            "V-06",
            "V-07",
            "V-08",
            "V-09"
          ],
          unitsPerShift: {
            "V-01": 1071,
            "V-02": 1071,
            "V-03": 1071,
            "V-04": 1071,
            "V-05": 1071,
            "V-06": 1071,
            "V-07": 1071,
            "V-08": 1071,
            "V-09": 1071
          }
        }
      ]
    },
    {
      product: "R902745127",
      family: "piston",
      processes: [
        {
          process: "drilling",
          sequence: 1,
          waitWorkdaysBefore: 0,
          setupKey: "\xD82,3",
          resourcePriority: [
            "D-01",
            "D-02"
          ],
          unitsPerShift: {
            "D-01": 1822,
            "D-02": 911
          }
        },
        {
          process: "deburring",
          sequence: 2,
          waitWorkdaysBefore: 0,
          setupKey: "--",
          resourcePriority: [
            "B-01-S1",
            "B-01-S2"
          ],
          unitsPerShift: {
            "B-01-S1": 1338,
            "B-01-S2": 1338
          }
        },
        {
          process: "gkm",
          sequence: 3,
          waitWorkdaysBefore: 1,
          setupKey: "GKM",
          resourcePriority: [
            "V-01",
            "V-02",
            "V-03",
            "V-04",
            "V-05",
            "V-06",
            "V-07",
            "V-08",
            "V-09"
          ],
          unitsPerShift: {
            "V-01": 1428,
            "V-02": 1428,
            "V-03": 1428,
            "V-04": 1428,
            "V-05": 1428,
            "V-06": 1428,
            "V-07": 1428,
            "V-08": 1428,
            "V-09": 1428
          }
        }
      ]
    },
    {
      product: "R902745129",
      family: "piston",
      processes: [
        {
          process: "drilling",
          sequence: 1,
          waitWorkdaysBefore: 0,
          setupKey: "\xD82,3",
          resourcePriority: [
            "D-01",
            "D-02"
          ],
          unitsPerShift: {
            "D-01": 1730,
            "D-02": 865
          }
        },
        {
          process: "deburring",
          sequence: 2,
          waitWorkdaysBefore: 0,
          setupKey: "--",
          resourcePriority: [
            "B-01-S1",
            "B-01-S2"
          ],
          unitsPerShift: {
            "B-01-S1": 1338,
            "B-01-S2": 1338
          }
        },
        {
          process: "gkm",
          sequence: 3,
          waitWorkdaysBefore: 1,
          setupKey: "GKM",
          resourcePriority: [
            "V-01",
            "V-02",
            "V-03",
            "V-04",
            "V-05",
            "V-06",
            "V-07",
            "V-08",
            "V-09"
          ],
          unitsPerShift: {
            "V-01": 1428,
            "V-02": 1428,
            "V-03": 1428,
            "V-04": 1428,
            "V-05": 1428,
            "V-06": 1428,
            "V-07": 1428,
            "V-08": 1428,
            "V-09": 1428
          }
        }
      ]
    },
    {
      product: "R902745131",
      family: "piston",
      processes: [
        {
          process: "drilling",
          sequence: 1,
          waitWorkdaysBefore: 0,
          setupKey: "\xD82,3",
          resourcePriority: [
            "D-01",
            "D-02"
          ],
          unitsPerShift: {
            "D-01": 1713,
            "D-02": 856
          }
        },
        {
          process: "deburring",
          sequence: 2,
          waitWorkdaysBefore: 0,
          setupKey: "--",
          resourcePriority: [
            "B-01-S1",
            "B-01-S2"
          ],
          unitsPerShift: {
            "B-01-S1": 1190,
            "B-01-S2": 1190
          }
        },
        {
          process: "gkm",
          sequence: 3,
          waitWorkdaysBefore: 1,
          setupKey: "GKM",
          resourcePriority: [
            "V-01",
            "V-02",
            "V-03",
            "V-04",
            "V-05",
            "V-06",
            "V-07",
            "V-08",
            "V-09"
          ],
          unitsPerShift: {
            "V-01": 1428,
            "V-02": 1428,
            "V-03": 1428,
            "V-04": 1428,
            "V-05": 1428,
            "V-06": 1428,
            "V-07": 1428,
            "V-08": 1428,
            "V-09": 1428
          }
        }
      ]
    },
    {
      product: "R902745133",
      family: "piston",
      processes: [
        {
          process: "drilling",
          sequence: 1,
          waitWorkdaysBefore: 0,
          setupKey: "\xD82,8",
          resourcePriority: [
            "D-01",
            "D-02"
          ],
          unitsPerShift: {
            "D-01": 1713,
            "D-02": 856
          }
        },
        {
          process: "deburring",
          sequence: 2,
          waitWorkdaysBefore: 0,
          setupKey: "--",
          resourcePriority: [
            "B-01-S1",
            "B-01-S2"
          ],
          unitsPerShift: {
            "B-01-S1": 1530,
            "B-01-S2": 1530
          }
        },
        {
          process: "gkm",
          sequence: 3,
          waitWorkdaysBefore: 1,
          setupKey: "GKM",
          resourcePriority: [
            "V-01",
            "V-02",
            "V-03",
            "V-04",
            "V-05",
            "V-06",
            "V-07",
            "V-08",
            "V-09"
          ],
          unitsPerShift: {
            "V-01": 1260,
            "V-02": 1260,
            "V-03": 1260,
            "V-04": 1260,
            "V-05": 1260,
            "V-06": 1260,
            "V-07": 1260,
            "V-08": 1260,
            "V-09": 1260
          }
        }
      ]
    },
    {
      product: "R902745135",
      family: "piston",
      processes: [
        {
          process: "drilling",
          sequence: 1,
          waitWorkdaysBefore: 0,
          setupKey: "\xD82,8",
          resourcePriority: [
            "D-01",
            "D-02"
          ],
          unitsPerShift: {
            "D-01": 1616,
            "D-02": 808
          }
        },
        {
          process: "deburring",
          sequence: 2,
          waitWorkdaysBefore: 0,
          setupKey: "--",
          resourcePriority: [
            "B-01-S1",
            "B-01-S2"
          ],
          unitsPerShift: {
            "B-01-S1": 1298,
            "B-01-S2": 1298
          }
        },
        {
          process: "gkm",
          sequence: 3,
          waitWorkdaysBefore: 1,
          setupKey: "GKM",
          resourcePriority: [
            "V-01",
            "V-02",
            "V-03",
            "V-04",
            "V-05",
            "V-06",
            "V-07",
            "V-08",
            "V-09"
          ],
          unitsPerShift: {
            "V-01": 1260,
            "V-02": 1260,
            "V-03": 1260,
            "V-04": 1260,
            "V-05": 1260,
            "V-06": 1260,
            "V-07": 1260,
            "V-08": 1260,
            "V-09": 1260
          }
        }
      ]
    },
    {
      product: "R902745138",
      family: "piston",
      processes: [
        {
          process: "drilling",
          sequence: 1,
          waitWorkdaysBefore: 0,
          setupKey: "\xD82,8",
          resourcePriority: [
            "D-01",
            "D-02"
          ],
          unitsPerShift: {
            "D-01": 1700,
            "D-02": 850
          }
        },
        {
          process: "deburring",
          sequence: 2,
          waitWorkdaysBefore: 0,
          setupKey: "--",
          resourcePriority: [
            "B-01-S1",
            "B-01-S2"
          ],
          unitsPerShift: {
            "B-01-S1": 1477,
            "B-01-S2": 1477
          }
        },
        {
          process: "gkm",
          sequence: 3,
          waitWorkdaysBefore: 1,
          setupKey: "GKM",
          resourcePriority: [
            "V-01",
            "V-02",
            "V-03",
            "V-04",
            "V-05",
            "V-06",
            "V-07",
            "V-08",
            "V-09"
          ],
          unitsPerShift: {
            "V-01": 1260,
            "V-02": 1260,
            "V-03": 1260,
            "V-04": 1260,
            "V-05": 1260,
            "V-06": 1260,
            "V-07": 1260,
            "V-08": 1260,
            "V-09": 1260
          }
        }
      ]
    },
    {
      product: "R902745143",
      family: "piston",
      processes: [
        {
          process: "drilling",
          sequence: 1,
          waitWorkdaysBefore: 0,
          setupKey: "\xD83,5",
          resourcePriority: [
            "D-01",
            "D-02"
          ],
          unitsPerShift: {
            "D-01": 1245,
            "D-02": 622
          }
        },
        {
          process: "deburring",
          sequence: 2,
          waitWorkdaysBefore: 0,
          setupKey: "--",
          resourcePriority: [
            "B-01-S1",
            "B-01-S2"
          ],
          unitsPerShift: {
            "B-01-S1": 1260,
            "B-01-S2": 1260
          }
        },
        {
          process: "gkm",
          sequence: 3,
          waitWorkdaysBefore: 1,
          setupKey: "GKM",
          resourcePriority: [
            "V-01",
            "V-02",
            "V-03",
            "V-04",
            "V-05",
            "V-06",
            "V-07",
            "V-08",
            "V-09"
          ],
          unitsPerShift: {
            "V-01": 856,
            "V-02": 856,
            "V-03": 856,
            "V-04": 856,
            "V-05": 856,
            "V-06": 856,
            "V-07": 856,
            "V-08": 856,
            "V-09": 856
          }
        }
      ]
    },
    {
      product: "R902745145",
      family: "piston",
      processes: [
        {
          process: "drilling",
          sequence: 1,
          waitWorkdaysBefore: 0,
          setupKey: "\xD83,5",
          resourcePriority: [
            "D-01",
            "D-02"
          ],
          unitsPerShift: {
            "D-01": 1224,
            "D-02": 612
          }
        },
        {
          process: "deburring",
          sequence: 2,
          waitWorkdaysBefore: 0,
          setupKey: "--",
          resourcePriority: [
            "B-01-S1",
            "B-01-S2"
          ],
          unitsPerShift: {
            "B-01-S1": 1381,
            "B-01-S2": 1381
          }
        },
        {
          process: "gkm",
          sequence: 3,
          waitWorkdaysBefore: 1,
          setupKey: "GKM",
          resourcePriority: [
            "V-01",
            "V-02",
            "V-03",
            "V-04",
            "V-05",
            "V-06",
            "V-07",
            "V-08",
            "V-09"
          ],
          unitsPerShift: {
            "V-01": 856,
            "V-02": 856,
            "V-03": 856,
            "V-04": 856,
            "V-05": 856,
            "V-06": 856,
            "V-07": 856,
            "V-08": 856,
            "V-09": 856
          }
        }
      ]
    },
    {
      product: "R902745147",
      family: "piston",
      processes: [
        {
          process: "drilling",
          sequence: 1,
          waitWorkdaysBefore: 0,
          setupKey: "\xD84,0",
          resourcePriority: [
            "D-01",
            "D-02"
          ],
          unitsPerShift: {
            "D-01": 1071,
            "D-02": 535
          }
        },
        {
          process: "deburring",
          sequence: 2,
          waitWorkdaysBefore: 0,
          setupKey: "--",
          resourcePriority: [
            "B-01-S1",
            "B-01-S2"
          ],
          unitsPerShift: {
            "B-01-S1": 1428,
            "B-01-S2": 1428
          }
        },
        {
          process: "gkm",
          sequence: 3,
          waitWorkdaysBefore: 1,
          setupKey: "GKM",
          resourcePriority: [
            "V-01",
            "V-02",
            "V-03",
            "V-04",
            "V-05",
            "V-06",
            "V-07",
            "V-08",
            "V-09"
          ],
          unitsPerShift: {
            "V-01": 856,
            "V-02": 856,
            "V-03": 856,
            "V-04": 856,
            "V-05": 856,
            "V-06": 856,
            "V-07": 856,
            "V-08": 856,
            "V-09": 856
          }
        }
      ]
    },
    {
      product: "R902745149",
      family: "piston",
      processes: [
        {
          process: "drilling",
          sequence: 1,
          waitWorkdaysBefore: 0,
          setupKey: "\xD84,0",
          resourcePriority: [
            "D-01",
            "D-02"
          ],
          unitsPerShift: {
            "D-01": 1109,
            "D-02": 554
          }
        },
        {
          process: "deburring",
          sequence: 2,
          waitWorkdaysBefore: 0,
          setupKey: "--",
          resourcePriority: [
            "B-01-S1",
            "B-01-S2"
          ],
          unitsPerShift: {
            "B-01-S1": 1530,
            "B-01-S2": 1530
          }
        },
        {
          process: "gkm",
          sequence: 3,
          waitWorkdaysBefore: 1,
          setupKey: "GKM",
          resourcePriority: [
            "V-01",
            "V-02",
            "V-03",
            "V-04",
            "V-05",
            "V-06",
            "V-07",
            "V-08",
            "V-09"
          ],
          unitsPerShift: {
            "V-01": 856,
            "V-02": 856,
            "V-03": 856,
            "V-04": 856,
            "V-05": 856,
            "V-06": 856,
            "V-07": 856,
            "V-08": 856,
            "V-09": 856
          }
        }
      ]
    },
    {
      product: "R902745161",
      family: "piston",
      processes: [
        {
          process: "drilling",
          sequence: 1,
          waitWorkdaysBefore: 0,
          setupKey: "\xD83,0",
          resourcePriority: [
            "D-01",
            "D-02"
          ],
          unitsPerShift: {
            "D-01": 1400,
            "D-02": 700
          }
        },
        {
          process: "deburring",
          sequence: 2,
          waitWorkdaysBefore: 0,
          setupKey: "--",
          resourcePriority: [
            "B-01-S1",
            "B-01-S2"
          ],
          unitsPerShift: {
            "B-01-S1": 1338,
            "B-01-S2": 1338
          }
        },
        {
          process: "gkm",
          sequence: 3,
          waitWorkdaysBefore: 1,
          setupKey: "GKM",
          resourcePriority: [
            "V-01",
            "V-02",
            "V-03",
            "V-04",
            "V-05",
            "V-06",
            "V-07",
            "V-08",
            "V-09"
          ],
          unitsPerShift: {
            "V-01": 1071,
            "V-02": 1071,
            "V-03": 1071,
            "V-04": 1071,
            "V-05": 1071,
            "V-06": 1071,
            "V-07": 1071,
            "V-08": 1071,
            "V-09": 1071
          }
        }
      ]
    },
    {
      product: "R902745163",
      family: "piston",
      processes: [
        {
          process: "drilling",
          sequence: 1,
          waitWorkdaysBefore: 0,
          setupKey: "\xD83,5",
          resourcePriority: [
            "D-01",
            "D-02"
          ],
          unitsPerShift: {
            "D-01": 1334,
            "D-02": 667
          }
        },
        {
          process: "deburring",
          sequence: 2,
          waitWorkdaysBefore: 0,
          setupKey: "--",
          resourcePriority: [
            "B-01-S1",
            "B-01-S2"
          ],
          unitsPerShift: {
            "B-01-S1": 1260,
            "B-01-S2": 1260
          }
        },
        {
          process: "gkm",
          sequence: 3,
          waitWorkdaysBefore: 1,
          setupKey: "GKM",
          resourcePriority: [
            "V-01",
            "V-02",
            "V-03",
            "V-04",
            "V-05",
            "V-06",
            "V-07",
            "V-08",
            "V-09"
          ],
          unitsPerShift: {
            "V-01": 1071,
            "V-02": 1071,
            "V-03": 1071,
            "V-04": 1071,
            "V-05": 1071,
            "V-06": 1071,
            "V-07": 1071,
            "V-08": 1071,
            "V-09": 1071
          }
        }
      ]
    },
    {
      product: "R902745165",
      family: "piston",
      processes: [
        {
          process: "drilling",
          sequence: 1,
          waitWorkdaysBefore: 0,
          setupKey: "\xD83,5",
          resourcePriority: [
            "D-01",
            "D-02"
          ],
          unitsPerShift: {
            "D-01": 1338,
            "D-02": 669
          }
        },
        {
          process: "deburring",
          sequence: 2,
          waitWorkdaysBefore: 0,
          setupKey: "--",
          resourcePriority: [
            "B-01-S1",
            "B-01-S2"
          ],
          unitsPerShift: {
            "B-01-S1": 1381,
            "B-01-S2": 1381
          }
        },
        {
          process: "gkm",
          sequence: 3,
          waitWorkdaysBefore: 1,
          setupKey: "GKM",
          resourcePriority: [
            "V-01",
            "V-02",
            "V-03",
            "V-04",
            "V-05",
            "V-06",
            "V-07",
            "V-08",
            "V-09"
          ],
          unitsPerShift: {
            "V-01": 1071,
            "V-02": 1071,
            "V-03": 1071,
            "V-04": 1071,
            "V-05": 1071,
            "V-06": 1071,
            "V-07": 1071,
            "V-08": 1071,
            "V-09": 1071
          }
        }
      ]
    },
    {
      product: "R902745167",
      family: "piston",
      processes: [
        {
          process: "drilling",
          sequence: 1,
          waitWorkdaysBefore: 0,
          setupKey: "\xD83,5",
          resourcePriority: [
            "D-01",
            "D-02"
          ],
          unitsPerShift: {
            "D-01": 1190,
            "D-02": 595
          }
        },
        {
          process: "deburring",
          sequence: 2,
          waitWorkdaysBefore: 0,
          setupKey: "--",
          resourcePriority: [
            "B-01-S1",
            "B-01-S2"
          ],
          unitsPerShift: {
            "B-01-S1": 1381,
            "B-01-S2": 1381
          }
        },
        {
          process: "gkm",
          sequence: 3,
          waitWorkdaysBefore: 1,
          setupKey: "GKM",
          resourcePriority: [
            "V-01",
            "V-02",
            "V-03",
            "V-04",
            "V-05",
            "V-06",
            "V-07",
            "V-08",
            "V-09"
          ],
          unitsPerShift: {
            "V-01": 856,
            "V-02": 856,
            "V-03": 856,
            "V-04": 856,
            "V-05": 856,
            "V-06": 856,
            "V-07": 856,
            "V-08": 856,
            "V-09": 856
          }
        }
      ]
    },
    {
      product: "R902745169",
      family: "piston",
      processes: [
        {
          process: "drilling",
          sequence: 1,
          waitWorkdaysBefore: 0,
          setupKey: "\xD83,0",
          resourcePriority: [
            "D-01",
            "D-02"
          ],
          unitsPerShift: {
            "D-01": 1452,
            "D-02": 726
          }
        },
        {
          process: "deburring",
          sequence: 2,
          waitWorkdaysBefore: 0,
          setupKey: "--",
          resourcePriority: [
            "B-01-S1",
            "B-01-S2"
          ],
          unitsPerShift: {
            "B-01-S1": 1381,
            "B-01-S2": 1381
          }
        },
        {
          process: "gkm",
          sequence: 3,
          waitWorkdaysBefore: 1,
          setupKey: "GKM",
          resourcePriority: [
            "V-01",
            "V-02",
            "V-03",
            "V-04",
            "V-05",
            "V-06",
            "V-07",
            "V-08",
            "V-09"
          ],
          unitsPerShift: {
            "V-01": 856,
            "V-02": 856,
            "V-03": 856,
            "V-04": 856,
            "V-05": 856,
            "V-06": 856,
            "V-07": 856,
            "V-08": 856,
            "V-09": 856
          }
        }
      ]
    },
    {
      product: "R902747620",
      family: "piston",
      processes: [
        {
          process: "drilling",
          sequence: 1,
          waitWorkdaysBefore: 0,
          setupKey: "\xD83,0",
          resourcePriority: [
            "D-01",
            "D-02"
          ],
          unitsPerShift: {
            "D-01": 1381,
            "D-02": 690
          }
        },
        {
          process: "deburring",
          sequence: 2,
          waitWorkdaysBefore: 0,
          setupKey: "--",
          resourcePriority: [
            "B-01-S1",
            "B-01-S2"
          ],
          unitsPerShift: {
            "B-01-S1": 1338,
            "B-01-S2": 1338
          }
        },
        {
          process: "gkm",
          sequence: 3,
          waitWorkdaysBefore: 1,
          setupKey: "GKM",
          resourcePriority: [
            "V-01",
            "V-02",
            "V-03",
            "V-04",
            "V-05",
            "V-06",
            "V-07",
            "V-08",
            "V-09"
          ],
          unitsPerShift: {
            "V-01": 856,
            "V-02": 856,
            "V-03": 856,
            "V-04": 856,
            "V-05": 856,
            "V-06": 856,
            "V-07": 856,
            "V-08": 856,
            "V-09": 856
          }
        }
      ]
    },
    {
      product: "R902747621",
      family: "piston",
      processes: [
        {
          process: "drilling",
          sequence: 1,
          waitWorkdaysBefore: 0,
          setupKey: "\xD83,5",
          resourcePriority: [
            "D-01",
            "D-02"
          ],
          unitsPerShift: {
            "D-01": 1947,
            "D-02": 973
          }
        },
        {
          process: "deburring",
          sequence: 2,
          waitWorkdaysBefore: 0,
          setupKey: "--",
          resourcePriority: [
            "B-01-S1",
            "B-01-S2"
          ],
          unitsPerShift: {
            "B-01-S1": 1298,
            "B-01-S2": 1298
          }
        },
        {
          process: "gkm",
          sequence: 3,
          waitWorkdaysBefore: 1,
          setupKey: "GKM",
          resourcePriority: [
            "V-01",
            "V-02",
            "V-03",
            "V-04",
            "V-05",
            "V-06",
            "V-07",
            "V-08",
            "V-09"
          ],
          unitsPerShift: {
            "V-01": 1071,
            "V-02": 1071,
            "V-03": 1071,
            "V-04": 1071,
            "V-05": 1071,
            "V-06": 1071,
            "V-07": 1071,
            "V-08": 1071,
            "V-09": 1071
          }
        }
      ]
    },
    {
      product: "R902747824",
      family: "center-pin",
      processes: [
        {
          process: "drilling",
          sequence: 1,
          waitWorkdaysBefore: 0,
          setupKey: "\xD84,0",
          resourcePriority: [
            "D-02"
          ],
          unitsPerShift: {
            "D-02": 612
          }
        },
        {
          process: "gkm",
          sequence: 2,
          waitWorkdaysBefore: 1,
          setupKey: "GKM",
          resourcePriority: [
            "V-01",
            "V-02",
            "V-03",
            "V-04",
            "V-05",
            "V-06",
            "V-07",
            "V-08",
            "V-09"
          ],
          unitsPerShift: {
            "V-01": 856,
            "V-02": 856,
            "V-03": 856,
            "V-04": 856,
            "V-05": 856,
            "V-06": 856,
            "V-07": 856,
            "V-08": 856,
            "V-09": 856
          }
        }
      ]
    },
    {
      product: "R902748350",
      family: "center-pin",
      processes: [
        {
          process: "drilling",
          sequence: 1,
          waitWorkdaysBefore: 0,
          setupKey: "\xD83,2",
          resourcePriority: [
            "D-02"
          ],
          unitsPerShift: {
            "D-02": 659
          }
        },
        {
          process: "gkm",
          sequence: 2,
          waitWorkdaysBefore: 1,
          setupKey: "GKM",
          resourcePriority: [
            "V-01",
            "V-02",
            "V-03",
            "V-04",
            "V-05",
            "V-06",
            "V-07",
            "V-08",
            "V-09"
          ],
          unitsPerShift: {
            "V-01": 1071,
            "V-02": 1071,
            "V-03": 1071,
            "V-04": 1071,
            "V-05": 1071,
            "V-06": 1071,
            "V-07": 1071,
            "V-08": 1071,
            "V-09": 1071
          }
        }
      ]
    },
    {
      product: "R902970039",
      family: "center-pin",
      processes: [
        {
          process: "drilling",
          sequence: 1,
          waitWorkdaysBefore: 0,
          setupKey: "\xD84,0",
          resourcePriority: [
            "D-02"
          ],
          unitsPerShift: {
            "D-02": 630
          }
        },
        {
          process: "gkm",
          sequence: 2,
          waitWorkdaysBefore: 1,
          setupKey: "GKM",
          resourcePriority: [
            "V-01",
            "V-02",
            "V-03",
            "V-04",
            "V-05",
            "V-06",
            "V-07",
            "V-08",
            "V-09"
          ],
          unitsPerShift: {
            "V-01": 856,
            "V-02": 856,
            "V-03": 856,
            "V-04": 856,
            "V-05": 856,
            "V-06": 856,
            "V-07": 856,
            "V-08": 856,
            "V-09": 856
          }
        }
      ]
    },
    {
      product: "R902970233",
      family: "piston",
      processes: [
        {
          process: "drilling",
          sequence: 1,
          waitWorkdaysBefore: 0,
          setupKey: "\xD83,5",
          resourcePriority: [
            "D-01",
            "D-02"
          ],
          unitsPerShift: {
            "D-01": 1328,
            "D-02": 664
          }
        },
        {
          process: "deburring",
          sequence: 2,
          waitWorkdaysBefore: 0,
          setupKey: "--",
          resourcePriority: [
            "B-01-S1",
            "B-01-S2"
          ],
          unitsPerShift: {
            "B-01-S1": 1477,
            "B-01-S2": 1477
          }
        },
        {
          process: "gkm",
          sequence: 3,
          waitWorkdaysBefore: 1,
          setupKey: "GKM",
          resourcePriority: [
            "V-01",
            "V-02",
            "V-03",
            "V-04",
            "V-05",
            "V-06",
            "V-07",
            "V-08",
            "V-09"
          ],
          unitsPerShift: {
            "V-01": 1020,
            "V-02": 1020,
            "V-03": 1020,
            "V-04": 1020,
            "V-05": 1020,
            "V-06": 1020,
            "V-07": 1020,
            "V-08": 1020,
            "V-09": 1020
          }
        }
      ]
    },
    {
      product: "R902970275",
      family: "piston",
      processes: [
        {
          process: "drilling",
          sequence: 1,
          waitWorkdaysBefore: 0,
          setupKey: "\xD83,5",
          resourcePriority: [
            "D-01",
            "D-02"
          ],
          unitsPerShift: {
            "D-01": 1260,
            "D-02": 630
          }
        },
        {
          process: "deburring",
          sequence: 2,
          waitWorkdaysBefore: 0,
          setupKey: "--",
          resourcePriority: [
            "B-01-S1",
            "B-01-S2"
          ],
          unitsPerShift: {
            "B-01-S1": 1477,
            "B-01-S2": 1477
          }
        },
        {
          process: "gkm",
          sequence: 3,
          waitWorkdaysBefore: 1,
          setupKey: "GKM",
          resourcePriority: [
            "V-01",
            "V-02",
            "V-03",
            "V-04",
            "V-05",
            "V-06",
            "V-07",
            "V-08",
            "V-09"
          ],
          unitsPerShift: {
            "V-01": 856,
            "V-02": 856,
            "V-03": 856,
            "V-04": 856,
            "V-05": 856,
            "V-06": 856,
            "V-07": 856,
            "V-08": 856,
            "V-09": 856
          }
        }
      ]
    },
    {
      product: "R902970276",
      family: "piston",
      processes: [
        {
          process: "drilling",
          sequence: 1,
          waitWorkdaysBefore: 0,
          setupKey: "\xD83,5",
          resourcePriority: [
            "D-01",
            "D-02"
          ],
          unitsPerShift: {
            "D-01": 1224,
            "D-02": 612
          }
        },
        {
          process: "deburring",
          sequence: 2,
          waitWorkdaysBefore: 0,
          setupKey: "--",
          resourcePriority: [
            "B-01-S1",
            "B-01-S2"
          ],
          unitsPerShift: {
            "B-01-S1": 1298,
            "B-01-S2": 1298
          }
        },
        {
          process: "gkm",
          sequence: 3,
          waitWorkdaysBefore: 1,
          setupKey: "GKM",
          resourcePriority: [
            "V-01",
            "V-02",
            "V-03",
            "V-04",
            "V-05",
            "V-06",
            "V-07",
            "V-08",
            "V-09"
          ],
          unitsPerShift: {
            "V-01": 856,
            "V-02": 856,
            "V-03": 856,
            "V-04": 856,
            "V-05": 856,
            "V-06": 856,
            "V-07": 856,
            "V-08": 856,
            "V-09": 856
          }
        }
      ]
    },
    {
      product: "R902970277",
      family: "center-pin",
      processes: [
        {
          process: "drilling",
          sequence: 1,
          waitWorkdaysBefore: 0,
          setupKey: "\xD84,5",
          resourcePriority: [
            "D-02"
          ],
          unitsPerShift: {
            "D-02": 1098
          }
        },
        {
          process: "gkm",
          sequence: 2,
          waitWorkdaysBefore: 1,
          setupKey: "GKM",
          resourcePriority: [
            "V-01",
            "V-02",
            "V-03",
            "V-04",
            "V-05",
            "V-06",
            "V-07",
            "V-08",
            "V-09"
          ],
          unitsPerShift: {
            "V-01": 856,
            "V-02": 856,
            "V-03": 856,
            "V-04": 856,
            "V-05": 856,
            "V-06": 856,
            "V-07": 856,
            "V-08": 856,
            "V-09": 856
          }
        }
      ]
    },
    {
      product: "R902970513",
      family: "piston",
      processes: [
        {
          process: "drilling",
          sequence: 1,
          waitWorkdaysBefore: 0,
          setupKey: "\xD82,8",
          resourcePriority: [
            "D-01",
            "D-02"
          ],
          unitsPerShift: {
            "D-01": 1477,
            "D-02": 738
          }
        },
        {
          process: "deburring",
          sequence: 2,
          waitWorkdaysBefore: 0,
          setupKey: "--",
          resourcePriority: [
            "B-01-S1",
            "B-01-S2"
          ],
          unitsPerShift: {
            "B-01-S1": 1190,
            "B-01-S2": 1190
          }
        },
        {
          process: "gkm",
          sequence: 3,
          waitWorkdaysBefore: 1,
          setupKey: "GKM",
          resourcePriority: [
            "V-01",
            "V-02",
            "V-03",
            "V-04",
            "V-05",
            "V-06",
            "V-07",
            "V-08",
            "V-09"
          ],
          unitsPerShift: {
            "V-01": 1260,
            "V-02": 1260,
            "V-03": 1260,
            "V-04": 1260,
            "V-05": 1260,
            "V-06": 1260,
            "V-07": 1260,
            "V-08": 1260,
            "V-09": 1260
          }
        }
      ]
    },
    {
      product: "R902970514",
      family: "piston",
      processes: [
        {
          process: "drilling",
          sequence: 1,
          waitWorkdaysBefore: 0,
          setupKey: "\xD82,8",
          resourcePriority: [
            "D-01",
            "D-02"
          ],
          unitsPerShift: {
            "D-01": 1428,
            "D-02": 714
          }
        },
        {
          process: "deburring",
          sequence: 2,
          waitWorkdaysBefore: 0,
          setupKey: "--",
          resourcePriority: [
            "B-01-S1",
            "B-01-S2"
          ],
          unitsPerShift: {
            "B-01-S1": 1428,
            "B-01-S2": 1428
          }
        },
        {
          process: "gkm",
          sequence: 3,
          waitWorkdaysBefore: 1,
          setupKey: "GKM",
          resourcePriority: [
            "V-01",
            "V-02",
            "V-03",
            "V-04",
            "V-05",
            "V-06",
            "V-07",
            "V-08",
            "V-09"
          ],
          unitsPerShift: {
            "V-01": 1260,
            "V-02": 1260,
            "V-03": 1260,
            "V-04": 1260,
            "V-05": 1260,
            "V-06": 1260,
            "V-07": 1260,
            "V-08": 1260,
            "V-09": 1260
          }
        }
      ]
    },
    {
      product: "R902970515",
      family: "piston",
      processes: [
        {
          process: "drilling",
          sequence: 1,
          waitWorkdaysBefore: 0,
          setupKey: "\xD82,8",
          resourcePriority: [
            "D-01",
            "D-02"
          ],
          unitsPerShift: {
            "D-01": 1428,
            "D-02": 714
          }
        },
        {
          process: "deburring",
          sequence: 2,
          waitWorkdaysBefore: 0,
          setupKey: "--",
          resourcePriority: [
            "B-01-S1",
            "B-01-S2"
          ],
          unitsPerShift: {
            "B-01-S1": 1338,
            "B-01-S2": 1338
          }
        },
        {
          process: "gkm",
          sequence: 3,
          waitWorkdaysBefore: 1,
          setupKey: "GKM",
          resourcePriority: [
            "V-01",
            "V-02",
            "V-03",
            "V-04",
            "V-05",
            "V-06",
            "V-07",
            "V-08",
            "V-09"
          ],
          unitsPerShift: {
            "V-01": 1260,
            "V-02": 1260,
            "V-03": 1260,
            "V-04": 1260,
            "V-05": 1260,
            "V-06": 1260,
            "V-07": 1260,
            "V-08": 1260,
            "V-09": 1260
          }
        }
      ]
    },
    {
      product: "R902970516",
      family: "piston",
      processes: [
        {
          process: "drilling",
          sequence: 1,
          waitWorkdaysBefore: 0,
          setupKey: "\xD83,0",
          resourcePriority: [
            "D-01",
            "D-02"
          ],
          unitsPerShift: {
            "D-01": 1616,
            "D-02": 808
          }
        },
        {
          process: "deburring",
          sequence: 2,
          waitWorkdaysBefore: 0,
          setupKey: "--",
          resourcePriority: [
            "B-01-S1",
            "B-01-S2"
          ],
          unitsPerShift: {
            "B-01-S1": 1224,
            "B-01-S2": 1224
          }
        },
        {
          process: "gkm",
          sequence: 3,
          waitWorkdaysBefore: 1,
          setupKey: "GKM",
          resourcePriority: [
            "V-01",
            "V-02",
            "V-03",
            "V-04",
            "V-05",
            "V-06",
            "V-07",
            "V-08",
            "V-09"
          ],
          unitsPerShift: {
            "V-01": 1260,
            "V-02": 1260,
            "V-03": 1260,
            "V-04": 1260,
            "V-05": 1260,
            "V-06": 1260,
            "V-07": 1260,
            "V-08": 1260,
            "V-09": 1260
          }
        }
      ]
    },
    {
      product: "R902970517",
      family: "piston",
      processes: [
        {
          process: "drilling",
          sequence: 1,
          waitWorkdaysBefore: 0,
          setupKey: "\xD83,0",
          resourcePriority: [
            "D-01",
            "D-02"
          ],
          unitsPerShift: {
            "D-01": 1647,
            "D-02": 823
          }
        },
        {
          process: "deburring",
          sequence: 2,
          waitWorkdaysBefore: 0,
          setupKey: "--",
          resourcePriority: [
            "B-01-S1",
            "B-01-S2"
          ],
          unitsPerShift: {
            "B-01-S1": 1224,
            "B-01-S2": 1224
          }
        },
        {
          process: "gkm",
          sequence: 3,
          waitWorkdaysBefore: 1,
          setupKey: "GKM",
          resourcePriority: [
            "V-01",
            "V-02",
            "V-03",
            "V-04",
            "V-05",
            "V-06",
            "V-07",
            "V-08",
            "V-09"
          ],
          unitsPerShift: {
            "V-01": 1260,
            "V-02": 1260,
            "V-03": 1260,
            "V-04": 1260,
            "V-05": 1260,
            "V-06": 1260,
            "V-07": 1260,
            "V-08": 1260,
            "V-09": 1260
          }
        }
      ]
    },
    {
      product: "R902970729",
      family: "center-pin",
      processes: [
        {
          process: "drilling",
          sequence: 1,
          waitWorkdaysBefore: 0,
          setupKey: "\xD83,2",
          resourcePriority: [
            "D-02"
          ],
          unitsPerShift: {
            "D-02": 793
          }
        },
        {
          process: "gkm",
          sequence: 2,
          waitWorkdaysBefore: 1,
          setupKey: "GKM",
          resourcePriority: [
            "V-01",
            "V-02",
            "V-03",
            "V-04",
            "V-05",
            "V-06",
            "V-07",
            "V-08",
            "V-09"
          ],
          unitsPerShift: {
            "V-01": 1127,
            "V-02": 1127,
            "V-03": 1127,
            "V-04": 1127,
            "V-05": 1127,
            "V-06": 1127,
            "V-07": 1127,
            "V-08": 1127,
            "V-09": 1127
          }
        }
      ]
    },
    {
      product: "R902970862",
      family: "piston",
      processes: [
        {
          process: "drilling",
          sequence: 1,
          waitWorkdaysBefore: 0,
          setupKey: "\xD84,0",
          resourcePriority: [
            "D-01",
            "D-02"
          ],
          unitsPerShift: {
            "D-01": 1118,
            "D-02": 559
          }
        },
        {
          process: "deburring",
          sequence: 2,
          waitWorkdaysBefore: 0,
          setupKey: "--",
          resourcePriority: [
            "B-01-S1",
            "B-01-S2"
          ],
          unitsPerShift: {
            "B-01-S1": 1428,
            "B-01-S2": 1428
          }
        },
        {
          process: "gkm",
          sequence: 3,
          waitWorkdaysBefore: 1,
          setupKey: "GKM",
          resourcePriority: [
            "V-01",
            "V-02",
            "V-03",
            "V-04",
            "V-05",
            "V-06",
            "V-07",
            "V-08",
            "V-09"
          ],
          unitsPerShift: {
            "V-01": 856,
            "V-02": 856,
            "V-03": 856,
            "V-04": 856,
            "V-05": 856,
            "V-06": 856,
            "V-07": 856,
            "V-08": 856,
            "V-09": 856
          }
        }
      ]
    },
    {
      product: "R902970863",
      family: "piston",
      processes: [
        {
          process: "drilling",
          sequence: 1,
          waitWorkdaysBefore: 0,
          setupKey: "\xD84,0",
          resourcePriority: [
            "D-01",
            "D-02"
          ],
          unitsPerShift: {
            "D-01": 1118,
            "D-02": 559
          }
        },
        {
          process: "deburring",
          sequence: 2,
          waitWorkdaysBefore: 0,
          setupKey: "--",
          resourcePriority: [
            "B-01-S1",
            "B-01-S2"
          ],
          unitsPerShift: {
            "B-01-S1": 1260,
            "B-01-S2": 1260
          }
        },
        {
          process: "gkm",
          sequence: 3,
          waitWorkdaysBefore: 1,
          setupKey: "GKM",
          resourcePriority: [
            "V-01",
            "V-02",
            "V-03",
            "V-04",
            "V-05",
            "V-06",
            "V-07",
            "V-08",
            "V-09"
          ],
          unitsPerShift: {
            "V-01": 856,
            "V-02": 856,
            "V-03": 856,
            "V-04": 856,
            "V-05": 856,
            "V-06": 856,
            "V-07": 856,
            "V-08": 856,
            "V-09": 856
          }
        }
      ]
    },
    {
      product: "R902970964",
      family: "center-pin",
      processes: [
        {
          process: "drilling",
          sequence: 1,
          waitWorkdaysBefore: 0,
          setupKey: "\xD84,5",
          resourcePriority: [
            "D-02"
          ],
          unitsPerShift: {
            "D-02": 1071
          }
        },
        {
          process: "gkm",
          sequence: 2,
          waitWorkdaysBefore: 1,
          setupKey: "GKM",
          resourcePriority: [
            "V-01",
            "V-02",
            "V-03",
            "V-04",
            "V-05",
            "V-06",
            "V-07",
            "V-08",
            "V-09"
          ],
          unitsPerShift: {
            "V-01": 856,
            "V-02": 856,
            "V-03": 856,
            "V-04": 856,
            "V-05": 856,
            "V-06": 856,
            "V-07": 856,
            "V-08": 856,
            "V-09": 856
          }
        }
      ]
    },
    {
      product: "R902972555",
      family: "piston",
      processes: [
        {
          process: "drilling",
          sequence: 1,
          waitWorkdaysBefore: 0,
          setupKey: "\xD82,3",
          resourcePriority: [
            "D-01",
            "D-02"
          ],
          unitsPerShift: {
            "D-01": 1586,
            "D-02": 793
          }
        },
        {
          process: "deburring",
          sequence: 2,
          waitWorkdaysBefore: 0,
          setupKey: "--",
          resourcePriority: [
            "B-01-S1",
            "B-01-S2"
          ],
          unitsPerShift: {
            "B-01-S1": 1338,
            "B-01-S2": 1338
          }
        },
        {
          process: "gkm",
          sequence: 3,
          waitWorkdaysBefore: 1,
          setupKey: "GKM",
          resourcePriority: [
            "V-01",
            "V-02",
            "V-03",
            "V-04",
            "V-05",
            "V-06",
            "V-07",
            "V-08",
            "V-09"
          ],
          unitsPerShift: {
            "V-01": 1428,
            "V-02": 1428,
            "V-03": 1428,
            "V-04": 1428,
            "V-05": 1428,
            "V-06": 1428,
            "V-07": 1428,
            "V-08": 1428,
            "V-09": 1428
          }
        }
      ]
    },
    {
      product: "R902972556",
      family: "piston",
      processes: [
        {
          process: "drilling",
          sequence: 1,
          waitWorkdaysBefore: 0,
          setupKey: "\xD82,3",
          resourcePriority: [
            "D-01",
            "D-02"
          ],
          unitsPerShift: {
            "D-01": 1586,
            "D-02": 793
          }
        },
        {
          process: "deburring",
          sequence: 2,
          waitWorkdaysBefore: 0,
          setupKey: "--",
          resourcePriority: [
            "B-01-S1",
            "B-01-S2"
          ],
          unitsPerShift: {
            "B-01-S1": 1338,
            "B-01-S2": 1338
          }
        },
        {
          process: "gkm",
          sequence: 3,
          waitWorkdaysBefore: 1,
          setupKey: "GKM",
          resourcePriority: [
            "V-01",
            "V-02",
            "V-03",
            "V-04",
            "V-05",
            "V-06",
            "V-07",
            "V-08",
            "V-09"
          ],
          unitsPerShift: {
            "V-01": 1428,
            "V-02": 1428,
            "V-03": 1428,
            "V-04": 1428,
            "V-05": 1428,
            "V-06": 1428,
            "V-07": 1428,
            "V-08": 1428,
            "V-09": 1428
          }
        }
      ]
    },
    {
      product: "R902972557",
      family: "piston",
      processes: [
        {
          process: "drilling",
          sequence: 1,
          waitWorkdaysBefore: 0,
          setupKey: "\xD83,0",
          resourcePriority: [
            "D-01",
            "D-02"
          ],
          unitsPerShift: {
            "D-01": 1586,
            "D-02": 793
          }
        },
        {
          process: "deburring",
          sequence: 2,
          waitWorkdaysBefore: 0,
          setupKey: "--",
          resourcePriority: [
            "B-01-S1",
            "B-01-S2"
          ],
          unitsPerShift: {
            "B-01-S1": 1338,
            "B-01-S2": 1338
          }
        },
        {
          process: "gkm",
          sequence: 3,
          waitWorkdaysBefore: 1,
          setupKey: "GKM",
          resourcePriority: [
            "V-01",
            "V-02",
            "V-03",
            "V-04",
            "V-05",
            "V-06",
            "V-07",
            "V-08",
            "V-09"
          ],
          unitsPerShift: {
            "V-01": 1428,
            "V-02": 1428,
            "V-03": 1428,
            "V-04": 1428,
            "V-05": 1428,
            "V-06": 1428,
            "V-07": 1428,
            "V-08": 1428,
            "V-09": 1428
          }
        }
      ]
    },
    {
      product: "R902974041",
      family: "piston",
      processes: [
        {
          process: "drilling",
          sequence: 1,
          waitWorkdaysBefore: 0,
          setupKey: "\xD82,8",
          resourcePriority: [
            "D-01",
            "D-02"
          ],
          unitsPerShift: {
            "D-01": 1586,
            "D-02": 793
          }
        },
        {
          process: "deburring",
          sequence: 2,
          waitWorkdaysBefore: 0,
          setupKey: "--",
          resourcePriority: [
            "B-01-S1",
            "B-01-S2"
          ],
          unitsPerShift: {
            "B-01-S1": 1260,
            "B-01-S2": 1260
          }
        },
        {
          process: "gkm",
          sequence: 3,
          waitWorkdaysBefore: 1,
          setupKey: "GKM",
          resourcePriority: [
            "V-01",
            "V-02",
            "V-03",
            "V-04",
            "V-05",
            "V-06",
            "V-07",
            "V-08",
            "V-09"
          ],
          unitsPerShift: {
            "V-01": 1428,
            "V-02": 1428,
            "V-03": 1428,
            "V-04": 1428,
            "V-05": 1428,
            "V-06": 1428,
            "V-07": 1428,
            "V-08": 1428,
            "V-09": 1428
          }
        }
      ]
    },
    {
      product: "R902974042",
      family: "center-pin",
      processes: [
        {
          process: "drilling",
          sequence: 1,
          waitWorkdaysBefore: 0,
          setupKey: "\xD83,5",
          resourcePriority: [
            "D-02"
          ],
          unitsPerShift: {
            "D-02": 1586
          }
        },
        {
          process: "gkm",
          sequence: 2,
          waitWorkdaysBefore: 1,
          setupKey: "GKM",
          resourcePriority: [
            "V-01",
            "V-02",
            "V-03",
            "V-04",
            "V-05",
            "V-06",
            "V-07",
            "V-08",
            "V-09"
          ],
          unitsPerShift: {
            "V-01": 1428,
            "V-02": 1428,
            "V-03": 1428,
            "V-04": 1428,
            "V-05": 1428,
            "V-06": 1428,
            "V-07": 1428,
            "V-08": 1428,
            "V-09": 1428
          }
        }
      ]
    }
  ]
};

// lib/process-master-data.ts
function activeProcessResourceIds(parameter) {
  return parameter.resourcePriority.filter((id) => !parameter.inactiveResourceIds?.includes(id));
}
var FILTER_PROCESS_ORDER = ["turning", "gtm", "diameter-grinding", "form-grinding", "measuring", "milling", "final-inspection", "filter-visual"];
function productionProcessOrder(seed) {
  return seed.productionArea === "cubuk-filtre" ? FILTER_PROCESS_ORDER : PRODUCT_PROCESS_ORDER;
}
function effectiveProductRoute(product, turningResourceId) {
  const route = productProcessRoute(product);
  if (product.family !== "cubuk-filtre") return route;
  if (["L-01", "L-02"].includes(turningResourceId ?? "")) return route.filter((p) => p !== "gtm");
  if (["L-03", "L-04", "L-05", "L-06"].includes(turningResourceId ?? "") && route.includes("turning"))
    return FILTER_PROCESS_ORDER.filter((process2) => process2 === "gtm" || route.includes(process2));
  return route;
}
var PRODUCT_PROCESS_ORDER = ["turning", "drilling", "deburring", "gkm"];
function productProcessRoute(product) {
  return product.route ?? ["turning", ...product.processes.slice().sort((a, b) => a.sequence - b.sequence).map((item) => item.process)];
}
function turningEnabled(master, product) {
  return processMasterDataForProduct(master, product)?.route?.includes("turning") ?? true;
}
var FOUNDATIONAL_PROCESS_MASTER_DATA = process_master_data_default;
function cloneFoundationalProcessMasterData() {
  return JSON.parse(JSON.stringify(FOUNDATIONAL_PROCESS_MASTER_DATA));
}
function processMasterDataForProduct(master, productCode) {
  const code3 = productCode.trim().toUpperCase();
  return master?.products.find((product) => product.product.toUpperCase() === code3);
}
function processProductGroup(product) {
  return product.productGroup?.trim() || product.family;
}
function resourceSupportsProcessProduct(resource, product) {
  if (resource.eligibleProductGroups === void 0) return true;
  const group = processProductGroup(product).toLocaleLowerCase("tr-TR");
  return resource.eligibleProductGroups.some((item) => item.trim().toLocaleLowerCase("tr-TR") === group);
}
function processLabel(process2) {
  return { turning: "Torna", drilling: "Delme", deburring: "\xC7apak alma", gkm: "GKM", gtm: "GTM", "diameter-grinding": "\xC7ap Ta\u015Flama", "form-grinding": "Form Ta\u015Flama", measuring: "\xD6l\xE7me", milling: "Freze", "final-inspection": "Final Kontrol", "filter-visual": "G\xF6z Kontrol" }[process2];
}

// lib/process-completion-time.ts
var SERIAL_EPOCH = Date.UTC(1899, 11, 30);
var DAY_MS = 864e5;
function processCompletionTimeInput(serial2) {
  return new Date(SERIAL_EPOCH + Math.round(serial2 * DAY_MS)).toISOString().slice(0, 16);
}

// lib/actual-date.ts
function actualDate(serial2, precision = "minute") {
  return { precision, value: processCompletionTimeInput(serial2).slice(0, precision === "day" ? 10 : 16) };
}
function parseActualDate(input, now = factoryNowSerial()) {
  if (!input || !["day", "minute"].includes(input.precision) || typeof input.value !== "string") throw Error("Tarih hassasiyetini se\xE7in.");
  const day = input.precision === "day";
  if (!(day ? /^\d{4}-\d{2}-\d{2}$/ : /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}$/).test(input.value)) throw Error("Ge\xE7erli bir ger\xE7ek tarih girin.");
  const serial2 = (Date.parse(`${input.value}${day ? "T00:00" : ""}:00Z`) - Date.UTC(1899, 11, 30)) / 864e5;
  if (!Number.isFinite(serial2) || serial2 <= 0 || actualDate(serial2, input.precision).value !== input.value) throw Error("Ge\xE7erli bir ger\xE7ek tarih girin.");
  if (day ? serial2 > Math.floor(now) : serial2 > now + 1e-8) throw Error("Ger\xE7ek tarih gelecekte olamaz.");
  return serial2;
}
function assertRecordedDateOrder(values, confirmed, now = factoryNowSerial()) {
  if (values.some((value) => value.precision === "day") && !confirmed) throw Error("Saat bilinmeyen kay\u0131tlarda proses s\u0131ras\u0131n\u0131 ve teslim \xF6ncesi tamamlanmay\u0131 onaylay\u0131n.");
  let earliest = -Infinity;
  for (const value of values) {
    const lower = value.value;
    if (!Number.isFinite(lower) || lower <= 0 || (value.precision === "day" ? !Number.isInteger(lower) || lower > Math.floor(now) : lower > now + 1e-8)) throw Error("Ge\xE7erli, gelecekte olmayan bir ger\xE7ek tarih girin.");
    const upper = value.precision === "day" ? Math.min(lower + 1 - 1e-8, now) : lower;
    earliest = Math.max(earliest, lower);
    if (earliest > upper + 1e-9) throw Error("Tarihler proses s\u0131ras\u0131yla \xE7eli\u015Fiyor. \xD6nceki proses sonraki prosesten veya teslimattan sonra olamaz.");
  }
}

// lib/process-waits.ts
function processWaitWorkdays(seed, process2) {
  const item = seed.processWaitSettings?.[process2];
  return item?.enabled ? item.workdays : 0;
}

// lib/delivery-deduction.ts
function stablePart(value) {
  return value.replace(/[^a-zA-Z0-9_-]+/g, "-").replace(/^-+|-+$/g, "").slice(0, 70);
}
function orderImportMetadataForSeed(seed) {
  if (seed.orderImport?.id && seed.orderImport.sourceFile && seed.orderImport.importedAt) return { ...seed.orderImport };
  const demand = seed.customerDemand;
  if (!demand?.sourceFile || !demand.importedAt) return null;
  return {
    id: `demand-${stablePart(demand.snapshotDate)}-${stablePart(demand.importedAt)}-${stablePart(demand.sourceFile)}`,
    sourceFile: demand.sourceFile,
    importedAt: demand.importedAt
  };
}
function effectiveDeliveryTimestamp(entry) {
  if (entry.deliveredAtPrecision === "day" && entry.deliveredAt) return entry.deliveredAt.slice(0, 10);
  if (entry.deliveredAtTime && Number.isFinite(Date.parse(entry.deliveredAtTime))) return new Date(entry.deliveredAtTime).toISOString();
  const deliveryDate = entry.deliveredAt?.slice(0, 10) ?? "";
  if (deliveryDate && entry.statusChangedAt && factoryDateInput(entry.statusChangedAt) === deliveryDate) {
    return new Date(entry.statusChangedAt).toISOString();
  }
  if (deliveryDate) return (/* @__PURE__ */ new Date(`${deliveryDate}T00:00:00+03:00`)).toISOString();
  return entry.statusChangedAt && Number.isFinite(Date.parse(entry.statusChangedAt)) ? new Date(entry.statusChangedAt).toISOString() : "";
}
function deliveryTimestampBounds(timestamp) {
  const dayOnly = /^\d{4}-\d{2}-\d{2}$/.test(timestamp);
  const lower = Date.parse(dayOnly ? `${timestamp}T00:00:00+03:00` : timestamp);
  return [lower, dayOnly ? lower + 864e5 - 1 : lower];
}
var uncertainCutoff = () => new Error("Teslim saati bilinmeyen g\xFCn kesim aral\u0131\u011F\u0131n\u0131n i\xE7inde b\xF6l\xFCn\xFCyor. Tam g\xFCn\xFC kapsayan tarih aral\u0131\u011F\u0131n\u0131 se\xE7in veya ger\xE7ek teslim saatini do\u011Frulay\u0131n.");
function isInsideFilter(timestamp, filter) {
  const [value, latest] = deliveryTimestampBounds(timestamp);
  const start = Date.parse(filter.startAt), end = Date.parse(filter.endAt);
  if (![value, start, end].every(Number.isFinite)) return false;
  const inside = (filter.includeStart ? value >= start : value > start) && latest <= end;
  if (!inside && value !== latest && latest >= start && value <= end) throw uncertainCutoff();
  return inside;
}
function validateFilter(filter) {
  const start = Date.parse(filter.startAt);
  const end = Date.parse(filter.endAt);
  if (!Number.isFinite(start) || !Number.isFinite(end)) throw new Error("Teslimat ba\u015Flang\u0131\xE7 veya plan \xE7al\u0131\u015Fma zaman\u0131 ge\xE7ersiz.");
  if (start > end) throw new Error("Teslimat ba\u015Flang\u0131\xE7 zaman\u0131 plan\u0131n \xE7al\u0131\u015Fma zaman\u0131ndan sonra olamaz.");
}
function deductDeliveries(input) {
  validateFilter(input.filter);
  if (input.filter.enabled && input.orderImport.shipmentsThrough && (Date.parse(input.filter.startAt) < Date.parse(input.orderImport.shipmentsThrough) || Date.parse(input.filter.startAt) === Date.parse(input.orderImport.shipmentsThrough) && input.filter.includeStart)) throw new Error("Bu tarihe kadar teslimatlar g\xFCnl\xFCk Excel bakiyesinden d\xFC\u015F\xFCld\xFC. Teslimat ba\u015Flang\u0131c\u0131n\u0131 dosya kesiminden sonra se\xE7in.");
  const orders = input.orders.map((order) => ({ ...order, deliveryMilestones: order.deliveryMilestones?.map((milestone) => ({ ...milestone })) }));
  const grossDemand = orders.reduce((sum, order) => sum + Math.max(0, order.quantity), 0);
  const importedProducts = new Set([...input.importProducts].map((product) => product.trim().toUpperCase()).filter(Boolean));
  const orderIndexesByProduct = /* @__PURE__ */ new Map();
  orders.forEach((order, index) => {
    const code3 = order.product.trim().toUpperCase();
    orderIndexesByProduct.set(code3, [...orderIndexesByProduct.get(code3) ?? [], index]);
  });
  for (const indexes of orderIndexesByProduct.values()) {
    indexes.sort((left, right) => orders[left].dueDate.localeCompare(orders[right].dueDate) || orders[left].sourceRow - orders[right].sourceRow);
  }
  const remainingByOrder = orders.map((order) => Math.max(0, order.quantity));
  const deductedByOrder = orders.map(() => 0);
  const seenIds = /* @__PURE__ */ new Set();
  const candidates = input.filter.enabled ? (input.productionHistory ?? []).filter((entry) => entry.inventoryStatus === "delivered" && entry.completedQuantity > 0 && !seenIds.has(entry.id) && seenIds.add(entry.id)).map((entry) => ({ entry, deliveredAt: effectiveDeliveryTimestamp(entry) })).filter(({ deliveredAt }) => deliveredAt && isInsideFilter(deliveredAt, input.filter)).sort((left, right) => left.deliveredAt.localeCompare(right.deliveredAt) || left.entry.id.localeCompare(right.entry.id)) : [];
  const items = [];
  for (const { entry, deliveredAt } of candidates) {
    const product = entry.product.trim().toUpperCase();
    const indexes = orderIndexesByProduct.get(product) ?? [];
    if (!importedProducts.has(product)) {
      items.push({ entryId: entry.id, sourceEntryId: entry.sourceEntryId, product, workOrder: entry.workOrder, deliveredAt, quantity: entry.completedQuantity, deductedQuantity: 0, excessQuantity: 0, matchedOrderIds: [], status: "unmatched" });
      continue;
    }
    if (!indexes.length) {
      items.push({ entryId: entry.id, sourceEntryId: entry.sourceEntryId, product, workOrder: entry.workOrder, deliveredAt, quantity: entry.completedQuantity, deductedQuantity: 0, excessQuantity: 0, matchedOrderIds: [], status: "outside-scope" });
      continue;
    }
    let remainingDelivery = entry.completedQuantity;
    let deductedQuantity2 = 0;
    const matchedOrderIds = [];
    for (const index of indexes) {
      if (remainingDelivery <= 0) break;
      const deducted = Math.min(remainingDelivery, remainingByOrder[index]);
      if (deducted <= 0) continue;
      remainingByOrder[index] -= deducted;
      deductedByOrder[index] += deducted;
      remainingDelivery -= deducted;
      deductedQuantity2 += deducted;
      matchedOrderIds.push(orders[index].id);
    }
    items.push({
      entryId: entry.id,
      sourceEntryId: entry.sourceEntryId,
      product,
      workOrder: entry.workOrder,
      deliveredAt,
      quantity: entry.completedQuantity,
      deductedQuantity: deductedQuantity2,
      excessQuantity: remainingDelivery,
      matchedOrderIds,
      status: remainingDelivery > 0 ? "excess" : "matched"
    });
  }
  const adjustedOrders = orders.flatMap((order, index) => {
    const deduction = deductedByOrder[index];
    const quantity = Math.max(0, order.quantity - deduction);
    if (quantity <= 0) return [];
    const milestones = orderDeliveryMilestones(order).map((milestone) => ({ ...milestone, quantity: Math.max(0, milestone.quantity - deduction) })).filter((milestone) => milestone.quantity > 0 && milestone.quantity < quantity);
    return [{
      ...order,
      quantity,
      allowPartial: milestones.length > 0,
      partialDeliveryQuantity: milestones[0]?.quantity ?? 0,
      partialDeliveryDate: milestones[0]?.date ?? "",
      deliveryMilestones: milestones
    }];
  });
  const deductedQuantity = deductedByOrder.reduce((sum, quantity) => sum + quantity, 0);
  const excessDeliveryQuantity = items.reduce((sum, item) => sum + item.excessQuantity, 0);
  const snapshot = {
    import: { ...input.orderImport },
    filter: { ...input.filter },
    grossDemand,
    deductedQuantity,
    plannedDemand: Math.max(0, grossDemand - deductedQuantity),
    excessDeliveryQuantity,
    items
  };
  const products = [...new Set(orders.map((order) => order.product.trim().toUpperCase()))].map((product) => {
    const indexes = orderIndexesByProduct.get(product) ?? [];
    const productGross = indexes.reduce((sum, index) => sum + orders[index].quantity, 0);
    const productDeducted = indexes.reduce((sum, index) => sum + deductedByOrder[index], 0);
    return {
      product,
      orderIds: indexes.map((index) => orders[index].id),
      grossDemand: productGross,
      deductedQuantity: productDeducted,
      plannedDemand: Math.max(0, productGross - productDeducted),
      excessDeliveryQuantity: items.filter((item) => item.product === product).reduce((sum, item) => sum + item.excessQuantity, 0)
    };
  });
  return {
    adjustedOrders,
    snapshot,
    products,
    unmatchedItems: items.filter((item) => item.status === "unmatched")
  };
}
function calculateDeliveryDeduction(input) {
  const importProducts = [...input.importProducts];
  const selected = deductDeliveries({ ...input, importProducts });
  const coverageStart = input.orderImport.shipmentsThrough ?? input.orderImport.importedAt;
  const importedAt = Date.parse(coverageStart);
  if (!Number.isFinite(importedAt)) throw new Error("Excel y\xFCkleme zaman\u0131 ge\xE7ersiz; teslimat kapsam\u0131 do\u011Frulanamad\u0131.");
  const earlierStart = input.filter.enabled && Date.parse(input.filter.startAt) < importedAt;
  const inclusive = deductDeliveries({ ...input, importProducts, filter: {
    ...input.filter,
    enabled: true,
    startAt: earlierStart ? input.filter.startAt : coverageStart,
    includeStart: earlierStart ? input.filter.includeStart : !input.orderImport.shipmentsThrough
  } });
  const selectedIds = new Set(selected.snapshot.items.map((item) => item.entryId));
  return {
    ...selected,
    excludedItems: inclusive.snapshot.items.filter((item) => !selectedIds.has(item.entryId) && item.matchedOrderIds.length > 0),
    includingExcludedProducts: inclusive.products
  };
}

// lib/daily-demand.ts
function assertFilterMonthlyPlan(plan, known) {
  const twelve = (values) => Array.isArray(values) && values.length === 12;
  if (!Number.isInteger(plan.year) || plan.year < 2e3 || plan.year > 2100 || !twelve(plan.workingDays) || plan.workingDays.some((days) => !(days >= 0 && days <= 31) || days * 2 % 1 !== 0)) throw new Error("\xC7al\u0131\u015Fma G\xFCnleri: y\u0131l veya ayl\u0131k i\u015F g\xFCn\xFC ge\xE7ersiz.");
  if (!Array.isArray(plan.rows) || !plan.rows.length || plan.rows.length > 60) throw new Error("\xC7al\u0131\u015Fma G\xFCnleri: \xFCr\xFCn sat\u0131r\u0131 bulunamad\u0131.");
  for (const row of plan.rows) {
    if (!known.has(row.product) || !["internal", "external"].includes(row.kind) || !twelve(row.quantities) || row.quantities.some((n) => !Number.isSafeInteger(n) || n < 0)) throw new Error(`\xC7al\u0131\u015Fma G\xFCnleri: ${row.label || "sat\u0131r"} \xFCr\xFCn\xFC, t\xFCr\xFC veya ayl\u0131k adedi ge\xE7ersiz.`);
  }
}

// lib/filter-monthly-demand.ts
var FILTER_315 = "F.00V.P01.315";
var FILTER_EXPECTED_GOOD_PERCENT = { "F.00V.P01.309": 96, [FILTER_315]: 96 };
var integer = (n) => Number.isSafeInteger(n) && n >= 0;
var dateValid = (s) => typeof s === "string" && /^\d{4}-\d{2}-\d{2}$/.test(s) && Number.isFinite(Date.parse(s)) && new Date(s).toISOString().slice(0, 10) === s;
var serial = (s) => (Date.parse(`${s}T00:00:00Z`) - Date.UTC(1899, 11, 30)) / 864e5;
var iso = (n) => new Date(Date.UTC(1899, 11, 30) + n * 864e5).toISOString().slice(0, 10);
function filterGoodPieces(product, physical) {
  if (!integer(physical)) throw new Error("Fiziksel adet ge\xE7ersiz.");
  const percent = FILTER_EXPECTED_GOOD_PERCENT[product];
  return percent === void 0 ? physical : Number(BigInt(physical) * BigInt(percent) / BigInt(100));
}
function filterRequiredInput(product, good) {
  if (!integer(good)) throw new Error("Sa\u011Flam par\xE7a ihtiyac\u0131 ge\xE7ersiz.");
  const percent = FILTER_EXPECTED_GOOD_PERCENT[product];
  const result = percent === void 0 ? good : Number((BigInt(good) * BigInt(100) + BigInt(percent - 1)) / BigInt(percent));
  if (!integer(result)) throw new Error("Gerekli giri\u015F adedi g\xFCvenli s\u0131n\u0131r\u0131 a\u015F\u0131yor.");
  return result;
}
function filterDeliveryBaselineFor(seed, year) {
  return seed.filterMonthlyDeliveryBaselines?.find((item) => item.year === year) ?? (seed.monthlyCustomerDemand?.year === year ? seed.monthlyCustomerDemand.deliveryBaseline : void 0) ?? (seed.filterInitialStockSetup?.deliveryBaseline?.year === year ? seed.filterInitialStockSetup.deliveryBaseline : void 0);
}
function promoteFilterMonthlyEvidence(seed) {
  if (seed.productionArea !== "cubuk-filtre") return;
  const monthly = seed.monthlyCustomerDemand;
  if (!seed.filterInitialStockSetup && monthly?.stockReconciliation) seed.filterInitialStockSetup = structuredClone({ ...monthly.stockReconciliation, sourceRows: monthly.stockReconciliation.sourceRows ?? monthly.openingStock?.rows });
  const baseline = monthly?.deliveryBaseline ?? (monthly && seed.orderImport?.shipmentsThrough ? { year: monthly.year, snapshotDate: monthly.snapshotDate, importedAt: monthly.importedAt, shipmentsThrough: seed.orderImport.shipmentsThrough, handovers: monthly.handovers } : seed.filterInitialStockSetup?.deliveryBaseline);
  if (baseline && !seed.filterMonthlyDeliveryBaselines?.some((item) => item.year === baseline.year)) seed.filterMonthlyDeliveryBaselines = [...seed.filterMonthlyDeliveryBaselines ?? [], structuredClone(baseline)];
}
function buildFilterMonthlyOrders(seed, data) {
  if (seed.productionArea !== "cubuk-filtre" || data.format !== "filter-monthly") throw new Error("Ayl\u0131k dosya yaln\u0131z \xC7ubuk Filtre alan\u0131na uygulanabilir.");
  assertFilterMonthlyPlan(data, new Set(seed.products.map((p) => p.product)));
  if (![data.startDate, data.endDate, data.snapshotDate].every(dateValid) || data.startDate > data.endDate || data.startDate.slice(0, 4) !== String(data.year) || data.endDate.slice(0, 4) !== String(data.year)) throw new Error("Ayl\u0131k sipari\u015F tarihlerini ve y\u0131l\u0131 kontrol edin.");
  if (!Array.isArray(data.handovers) || data.handovers.length > 720 || !Array.isArray(data.exceptions) || data.exceptions.length > 1e3) throw new Error("Teslimat veya tarihli ihtiya\xE7 listesi ge\xE7ersiz.");
  const products = new Set(data.rows.map((r) => r.product));
  if (products.size !== data.rows.length) throw new Error("Ayl\u0131k \xFCr\xFCn tekrarl\u0131.");
  const handovers = /* @__PURE__ */ new Map();
  for (const h of data.handovers) {
    const key = `${h.product}:${h.month}`;
    if (!products.has(h.product) || !/^\d{4}-(0[1-9]|1[0-2])$/.test(h.month) || h.month.slice(0, 4) !== String(data.year) || !integer(h.quantity) || handovers.has(key) || h.quantity > 0 && h.month > data.snapshotDate.slice(0, 7)) throw new Error("Teslim edilen adet, ay veya \xFCr\xFCn ge\xE7ersiz / tekrarl\u0131.");
    handovers.set(key, h.quantity);
  }
  if (data.openingStock) {
    if (!dateValid(data.openingStock.cutoffDate) || !Array.isArray(data.openingStock.rows) || data.openingStock.rows.length > 100) throw new Error("Stok kayna\u011F\u0131 ge\xE7ersiz.");
    const seen = /* @__PURE__ */ new Set();
    for (const row of data.openingStock.rows) {
      if (seen.has(row.product) || !seed.products.some((p) => p.product === row.product) || [row.delivered, row.visual, row.heat, row.milling, row.grinding].some((n) => n !== null && !integer(n))) throw new Error("Stok kayna\u011F\u0131 \xFCr\xFCn / adet ge\xE7ersiz.");
      seen.add(row.product);
    }
  }
  const exceptionKeys = /* @__PURE__ */ new Set();
  for (const e of data.exceptions) {
    const key = `${e.product}:${e.date}`;
    if (!products.has(e.product) || !dateValid(e.date) || e.date < data.startDate || e.date > data.endDate || !integer(e.quantity) || exceptionKeys.has(key)) throw new Error("Tarihli ihtiya\xE7 ge\xE7ersiz / tekrarl\u0131.");
    exceptionKeys.add(key);
  }
  const rows = [];
  const dailyRows = [];
  for (const row of data.rows) for (let m = 0; m < 12; m++) {
    const month = `${data.year}-${String(m + 1).padStart(2, "0")}`;
    if (month < data.startDate.slice(0, 7) || month > data.endDate.slice(0, 7)) continue;
    const ordered = row.quantities[m], key = `${row.product}:${month}`;
    if (ordered > 0 && month <= data.snapshotDate.slice(0, 7) && !handovers.has(key)) throw new Error(`${row.label} ${month}: tamamlanan teslimat\u0131 girin; yoksa 0 ile do\u011Frulay\u0131n.`);
    const delivered = handovers.get(key) ?? 0;
    const remaining = Math.max(0, ordered - delivered);
    rows.push({ product: row.product, month, ordered, delivered, remaining });
    const exceptions = data.exceptions.filter((e) => e.product === row.product && e.date.startsWith(month));
    const assigned = exceptions.reduce((s, e) => s + e.quantity, 0);
    if (!integer(assigned) || assigned > remaining) throw new Error(`${row.label} ${month}: tarihli adet ayl\u0131k kalan ihtiyac\u0131 a\u015F\u0131yor.`);
    dailyRows.push(...exceptions.filter((e) => e.quantity > 0));
    const days = [];
    const end = Math.min(serial(data.endDate), serial(new Date(Date.UTC(data.year, m + 1, 0)).toISOString().slice(0, 10)));
    for (let day = Math.max(serial(`${month}-01`), serial(data.startDate)); day <= end; day++) {
      const date = iso(day);
      if (exceptions.some((e) => e.date === date)) continue;
      const weight = machineDayCapacity(seed, { id: "CF-DEMAND", shiftFactor: 2 }, day).shifts;
      if (weight > 0) days.push({ date, weight });
    }
    const residual = remaining - assigned, total = days.reduce((s, d) => s + d.weight, 0);
    if (residual > 0 && total === 0) throw new Error(`${row.label} ${month}: kalan ihtiyac\u0131 da\u011F\u0131tacak \xE7al\u0131\u015Fma g\xFCn\xFC yok.`);
    let cumulativeWeight = 0, previous = 0;
    for (const day of days) {
      cumulativeWeight += day.weight;
      const cumulative = Number(BigInt(residual) * BigInt(cumulativeWeight) / BigInt(total));
      const quantity = cumulative - previous;
      previous = cumulative;
      if (quantity > 0) dailyRows.push({ product: row.product, date: day.date, quantity });
    }
  }
  dailyRows.sort((a, b) => a.date.localeCompare(b.date) || a.product.localeCompare(b.product));
  const orders = [];
  for (const product of products) {
    const days = dailyRows.filter((r) => r.product === product);
    if (!days.length) continue;
    let quantity = 0;
    const milestones = days.map((d) => ({ id: `monthly-${product}-${d.date}`, date: d.date, quantity: quantity += d.quantity }));
    if (!integer(quantity)) throw new Error("Y\u0131ll\u0131k ihtiya\xE7 g\xFCvenli adet s\u0131n\u0131r\u0131n\u0131 a\u015F\u0131yor.");
    orders.push({
      id: `monthly-${product}`,
      product,
      sourceRow: data.rows.find((r) => r.product === product).sourceRow,
      quantity,
      savedPlanned: 0,
      savedDifference: 0,
      savedMachines: [],
      dueDate: milestones.at(-1).date,
      allowPartial: true,
      partialDeliveryQuantity: 0,
      partialDeliveryDate: "",
      deliveryMilestones: milestones
    });
  }
  return { orders, rows, dailyRows };
}
function filterSupplyGoodPieces(seed, product, physical, completed = false) {
  return seed.productionArea === "cubuk-filtre" && seed.monthlyCustomerDemand && !completed ? filterGoodPieces(product, physical) : physical;
}
function filterCommittedSupply(seed, batches) {
  const rows = [];
  if (!seed.customerDemand) for (const [product, quantity] of Object.entries(seed.openingStock ?? {})) rows.push({ id: `opening:${product}`, product, quantity, completed: true });
  for (const [index, row] of (seed.processStockSettings?.opening ?? []).entries()) rows.push({ id: `stock:${index}`, product: row.product, quantity: row.quantity, completed: row.groupId === "warehouse" });
  for (const machine of seed.machines) if (machine.currentJob.quantity > 0) rows.push({ id: `current:${machine.id}`, product: machine.currentJob.product, quantity: machine.currentJob.quantity, chargeId: machine.currentJob.sharedCharge?.id });
  for (const entry of seed.productionHistory ?? []) if ((entry.inventoryStatus ?? "semi-finished") === "semi-finished") {
    const lots = (seed.wipLots ?? []).filter((lot) => lot.sourceHistoryEntryId === entry.id && lot.availableQuantity > 0 && !["delivered", "scrapped"].includes(lot.stage));
    const linked = lots.reduce((sum, lot) => sum + lot.availableQuantity, 0);
    if (linked > entry.completedQuantity) throw new Error(`${entry.product}: \u015Farj ve ar\u015Fiv miktarlar\u0131 uzla\u015Fm\u0131yor.`);
    for (const lot of lots) rows.push({ id: `wip:${lot.id}`, product: lot.product, quantity: lot.availableQuantity, completed: lot.stage === "delivery-ready", chargeId: lot.sharedCharge?.id });
    if (entry.completedQuantity > linked) rows.push({ id: `history:${entry.id}`, product: entry.product, quantity: entry.completedQuantity - linked, chargeId: entry.sharedCharge?.id });
  }
  for (const batch of batches) if (batch.status === "planned" && batch.quantity > 0) rows.push({ id: `batch:${batch.id}`, product: batch.product, quantity: batch.quantity, chargeId: batch.sharedCharge?.id, planned: true });
  const cumulative = /* @__PURE__ */ new Map();
  return rows.sort((a, b) => Number(Boolean(a.planned)) - Number(Boolean(b.planned)) || a.id.localeCompare(b.id)).map((row) => {
    if (!row.chargeId || row.completed) return { ...row, quantity: filterSupplyGoodPieces(seed, row.product, row.quantity, row.completed) };
    const key = `${row.product}:${row.chargeId}`, before = cumulative.get(key) ?? 0, after = before + row.quantity;
    cumulative.set(key, after);
    return { ...row, quantity: filterSupplyGoodPieces(seed, row.product, after) - filterSupplyGoodPieces(seed, row.product, before) };
  });
}
function filterInputForShortage(seed, product, good) {
  return seed.productionArea === "cubuk-filtre" && seed.monthlyCustomerDemand ? filterRequiredInput(product, good) : good;
}
function filterHistoryGoodPieces(seed, entry) {
  if (seed.productionArea !== "cubuk-filtre" || !seed.monthlyCustomerDemand) return entry.completedQuantity;
  const lots = (seed.wipLots ?? []).filter((l) => l.sourceHistoryEntryId === entry.id && l.availableQuantity > 0 && !["delivered", "scrapped"].includes(l.stage));
  const linked = lots.reduce((s, l) => s + l.availableQuantity, 0);
  if (linked > entry.completedQuantity) throw new Error(`${entry.product}: \u015Farj ve ar\u015Fiv miktarlar\u0131 uzla\u015Fm\u0131yor.`);
  return lots.reduce((s, l) => s + filterSupplyGoodPieces(seed, l.product, l.availableQuantity, l.stage === "delivery-ready"), 0) + filterSupplyGoodPieces(seed, entry.product, entry.completedQuantity - linked);
}

// lib/production-interruptions.ts
function validateProductionInterruption(input, quantity, startedAt, occurredAt) {
  if (!input || typeof input.produced !== "boolean") throw new Error("\xDCretim oldu mu? Evet veya Hay\u0131r se\xE7in.");
  if (!Number.isFinite(occurredAt) || occurredAt < startedAt) throw new Error("Ara verme tarihi \xFCretim ba\u015Flang\u0131c\u0131ndan \xF6nce olamaz.");
  if (!Number.isInteger(quantity) || quantity <= 0) throw new Error("Mevcut i\u015Fin adedi ge\xE7ersiz.");
  if (input.kind && !["partial-completion", "interruption"].includes(input.kind)) throw new Error("\xDCretim aktar\u0131m se\xE7imi ge\xE7ersiz.");
  if (!input.produced) return 0;
  if (!Number.isInteger(input.quantity) || input.quantity <= 0 || input.quantity >= quantity) throw new Error("\xDCretilen adet s\u0131f\u0131rdan b\xFCy\xFCk ve mevcut i\u015F adedinden k\xFC\xE7\xFCk olmal\u0131d\u0131r. \u0130\u015Fin tamam\u0131 \xFCretildiyse prosesi bitirin.");
  if (!input.reason?.trim()) throw new Error(input.kind === "partial-completion" ? "\u0130\u015F de\u011Fi\u015Ftirme nedeni zorunludur." : "\u0130\u015Fe ara verme nedeni zorunludur.");
  if (input.reason.trim().length > 2e3) throw new Error("\u0130\u015Fe ara verme nedeni en fazla 2000 karakter olabilir.");
  return input.quantity;
}
function activeLotInterruptions(seed, lot) {
  return (seed.productionInterruptions ?? []).filter((item) => isProductionInterruption(item) && !item.completedAt && lot?.interruptionIds?.includes(item.id));
}
function isProductionInterruption(item) {
  return item.producedQuantity !== 0 && item.kind !== "partial-completion";
}
function isProtectedProductionRemainder(item) {
  return item.producedQuantity !== 0;
}
function hasActiveProductionInterruption(seed, chargeId, interruptionId) {
  const records2 = seed.productionInterruptions ?? [];
  if (records2.some((item) => isProductionInterruption(item) && !item.completedAt && (Boolean(chargeId && item.chargeId === chargeId) || item.id === interruptionId))) return true;
  return Boolean(interruptionId && !records2.some((item) => item.id === interruptionId));
}
function hasProtectedProductionRemainder(seed, chargeId, interruptionId) {
  const records2 = seed.productionInterruptions ?? [];
  if (records2.some((item) => isProtectedProductionRemainder(item) && (Boolean(chargeId && item.chargeId === chargeId) || item.id === interruptionId))) return true;
  return Boolean(interruptionId && !records2.some((item) => item.id === interruptionId));
}
function finishProductionInterruptions(seed, chargeId, process2, completedAt) {
  if (!chargeId) return;
  for (const item of seed.productionInterruptions ?? []) if (item.chargeId === chargeId && item.process === process2 && !item.completedAt) item.completedAt = completedAt;
}
function hasRecordedTurningProduction(seed, batch) {
  if (batch.sharedCharge && (seed.machines.some((machine) => machine.currentJob.quantity > 0 && machine.currentJob.sharedCharge?.id === batch.sharedCharge.id) || (seed.wipLots ?? []).some((lot) => lot.sharedCharge?.id === batch.sharedCharge.id) || (seed.productionHistory ?? []).some((entry) => entry.inventoryStatus !== "voided" && entry.completedQuantity > 0 && entry.sharedCharge?.id === batch.sharedCharge.id))) return true;
  const key = (value) => (value ?? "").trim().toUpperCase();
  const sameWork = (record) => Boolean(key(batch.workOrder)) && key(record.workOrder) === key(batch.workOrder) && key(record.product) === key(batch.product);
  const events = (seed.productionInterruptions ?? []).filter((item) => item.chargeId === batch.id || item.id === batch.interruptionId || !item.chargeId && sameWork(item));
  const eventIds = new Set(events.map((item) => item.id));
  const linkedEvent = (ids) => ids?.some((id) => eventIds.has(id)) ?? false;
  if (events.some((item) => item.producedQuantity !== 0)) return true;
  if (batch.interruptionId && !events.some((item) => item.id === batch.interruptionId)) return true;
  if (events.some((item) => item.id === batch.interruptionId && item.chargeId !== batch.id)) return true;
  if (seed.machines.some((machine) => machine.currentJob.quantity > 0 && (machine.currentJob.batchId === batch.id || !machine.currentJob.batchId && sameWork(machine.currentJob)))) return true;
  if ((seed.productionHistory ?? []).some((item) => item.inventoryStatus !== "voided" && item.completedQuantity !== 0 && (item.sourceBatchId === batch.id || (!item.sourceBatchId || item.sourceBatchId === item.id) && sameWork(item) || linkedEvent(item.interruptionIds)))) return true;
  if ((seed.wipLots ?? []).some((item) => item.sourceBatchId === batch.id || (!item.sourceBatchId || item.sourceBatchId === item.sourceHistoryEntryId) && sameWork(item) || linkedEvent(item.interruptionIds))) return true;
  return (seed.processCurrentJobs ?? []).some((item) => item.batchId === batch.id || !item.batchId && sameWork(item));
}
function protectedInterruptedBatches(seed, batches = []) {
  const latest = /* @__PURE__ */ new Map();
  for (const item of seed.productionInterruptions ?? []) if (item.process === "turning" && isProtectedProductionRemainder(item) && !item.completedAt && item.turningBatch) latest.set(item.chargeId, item);
  return [...latest.values()].filter((item) => !seed.machines.some((machine) => machine.currentJob.batchId === item.chargeId && machine.currentJob.quantity > 0)).map((item) => {
    const matches = (batch) => batch.id === item.chargeId && batch.interruptionId === item.id && batch.quantity === item.remainingQuantity;
    return { ...batches.find(matches) ?? seed.manualBatches?.find(matches) ?? item.turningBatch };
  });
}
function withInterruptedBatches(seed, batches) {
  const live = protectedInterruptedBatches(seed, batches);
  const known = new Set((seed.productionInterruptions ?? []).filter((item) => item.process === "turning" && isProtectedProductionRemainder(item) && item.turningBatch).map((item) => item.chargeId));
  const result = batches.filter((batch) => !known.has(batch.id)).map((batch) => ({ ...batch }));
  result.push(...live);
  return result;
}
function canonicalSwitchSnapshot(snapshot, queueDefaults = false) {
  if (!Array.isArray(snapshot) || snapshot.length !== 11 || !Array.isArray(snapshot[10])) throw new Error("Invalid switch snapshot");
  const queue = [...snapshot[10]].map((batch) => queueDefaults ? { ...batch, locked: batch.locked ?? false, manuallyPlaced: batch.manuallyPlaced ?? false, workOrder: batch.workOrder ?? "" } : batch).sort((a, b) => a.machineId < b.machineId ? -1 : a.machineId > b.machineId ? 1 : a.planColumn - b.planColumn);
  const stable2 = (value) => {
    if (Array.isArray(value)) return value.map(stable2);
    if (value && typeof value === "object") return Object.fromEntries(Object.entries(value).sort(([a], [b]) => a < b ? -1 : a > b ? 1 : 0).map(([key, item]) => [key, stable2(item)]));
    return value;
  };
  return JSON.stringify(stable2([...snapshot.slice(0, 10), queue]));
}
function compactSnapshot(canonical) {
  let a = 3735928559, b = 1103547991;
  for (let index = 0; index < canonical.length; index++) {
    const code3 = canonical.charCodeAt(index);
    a = Math.imul(a ^ code3, 2654435761);
    b = Math.imul(b ^ code3, 1597334677);
  }
  a = Math.imul(a ^ a >>> 16, 2246822507) ^ Math.imul(b ^ b >>> 13, 3266489909);
  b = Math.imul(b ^ b >>> 16, 2246822507) ^ Math.imul(a ^ a >>> 13, 3266489909);
  return `v2:${canonical.length}:${(a >>> 0).toString(16)}${(b >>> 0).toString(16)}`;
}
function productionSwitchSnapshot(seed, batches) {
  return [seed.machines, seed.processCurrentJobs ?? [], seed.wipLots ?? [], seed.productionInterruptions ?? [], seed.processOperationOverrides ?? [], seed.processMasterData, seed.calendarEvents, seed.products, seed.holidays, seed.setupSettings, batches];
}
function productionSwitchSignature(seed, batches) {
  return compactSnapshot(canonicalSwitchSnapshot(productionSwitchSnapshot(seed, batches)));
}
function assertProductionSwitchSnapshot(seed, batches, input) {
  if (!input?.expectedSignature) return;
  const current = productionSwitchSignature(seed, batches);
  if (input.expectedSignature === current) return;
  const displayed = canonicalSwitchSnapshot(productionSwitchSnapshot(seed, batches), true);
  if (input.expectedSignature === compactSnapshot(displayed)) return;
  try {
    if (canonicalSwitchSnapshot(JSON.parse(input.expectedSignature), true) === displayed) return;
  } catch {
  }
  throw new Error("Mevcut i\u015F veya kuyruk de\u011Fi\u015Fti. Pencereyi kapat\u0131p g\xFCncel kay\u0131tla yeniden a\xE7\u0131n.");
}

// lib/filter-quality-calendar.ts
var FILTER_QUALITY_RESOURCE = "CF-KALITE";
function filterQualityReadyAt(seed, completed) {
  if (!Number.isFinite(completed) || completed <= 0) throw new Error("Kalite bekleme ba\u015Flang\u0131c\u0131 ge\xE7ersiz.");
  const fraction = completed - Math.floor(completed);
  const resource = { id: FILTER_QUALITY_RESOURCE, shiftFactor: seed.filterQualityShifts ?? 1 };
  for (let day = Math.floor(completed) + 1; day <= Math.floor(completed) + 3660; day++) {
    if (machineDayCapacity(seed, resource, day).shifts > 0) return day + fraction;
  }
  throw new Error("Kalite bekleme takviminde a\xE7\u0131k \xE7al\u0131\u015Fma g\xFCn\xFC bulunamad\u0131.");
}

// lib/flow-settings.ts
function validateFlowSettings(value) {
  const fail = () => {
    throw new Error("Ak\u0131\u015F ayarlar\u0131 ge\xE7ersiz. S\xFCreler 0\u201310080 dakika, vardiyalar 0\u20133 olmal\u0131; ayn\u0131 ge\xE7i\u015F i\xE7in yaln\u0131zca bir etkin kural kullan\u0131labilir.");
  };
  if (!value || typeof value !== "object") return fail();
  const v = value;
  const shifts = (n) => Number.isInteger(n) && n >= 0 && n <= 3;
  const minutes = (n) => typeof n === "number" && Number.isFinite(n) && n >= 0 && n <= 10080;
  if (v.version !== 1 || v.department !== "piston" || typeof v.enabled !== "boolean" || !shifts(v.defaultShifts) || !Array.isArray(v.rules) || v.rules.length > 100 || !Array.isArray(v.shiftOverrides) || v.shiftOverrides.length > 3660) return fail();
  const dates = /* @__PURE__ */ new Set();
  for (const item of v.shiftOverrides) {
    if (!item || !Number.isInteger(item.date) || item.date <= 0 || item.date > 2958465 || !shifts(item.shifts) || dates.has(item.date)) return fail();
    dates.add(item.date);
  }
  const ids = /* @__PURE__ */ new Set(), transitions = /* @__PURE__ */ new Set();
  const order = ["turning", "drilling", "deburring", "gkm", "delivery"];
  for (const rule of v.rules) {
    if (!rule || typeof rule.id !== "string" || !rule.id.trim() || ids.has(rule.id) || !["piston", "center-pin"].includes(rule.family) || !["dynamic", "static"].includes(rule.mode) || typeof rule.active !== "boolean" || typeof rule.description !== "string" || rule.description.length > 500 || !minutes(rule.minutes) || order.indexOf(rule.from) < 0 || order.indexOf(rule.from) >= 4 || order.indexOf(rule.to) <= order.indexOf(rule.from) || rule.to === "delivery" && rule.mode !== "static") return fail();
    ids.add(rule.id);
    const key = `${rule.family}:${rule.from}:${rule.to}`;
    if (rule.active && transitions.has(key)) return fail();
    if (rule.active) transitions.add(key);
  }
  for (const process2 of ["drilling", "deburring", "gkm"]) {
    const setup = v.setupMinutes?.[process2];
    if (!setup || !["first", "sameProduct", "sameKey", "differentKey", "differentFamily"].every((key) => minutes(setup[key]))) return fail();
  }
  return structuredClone(v);
}
function flowRule(seed, family, from, to) {
  return seed.productionArea !== "cubuk-filtre" && seed.flowSettings?.enabled ? seed.flowSettings.rules.find((rule) => rule.active && rule.family === family && rule.from === from && rule.to === to) : void 0;
}
function addDepartmentWorkMinutes(seed, start, minutes) {
  if (!minutes) return start;
  const settings = seed.flowSettings;
  const shiftHours = Math.max(1, Math.min(24, seed.setupSettings?.shiftHours ?? 8));
  let cursor = start, remaining = minutes;
  for (let guard = 0; guard < 36600; guard += 1) {
    const day = Math.floor(cursor);
    const sunday = new Date(Date.UTC(1899, 11, 30) + day * 864e5).getUTCDay() === 0;
    const holiday = seed.holidays.find((item) => Math.floor(item.serial) === day);
    const override = settings.shiftOverrides.find((item) => item.date === day);
    const shifts = override?.shifts ?? (holiday ? holiday.workingShifts ?? 0 : sunday ? 0 : settings.defaultShifts);
    const end = day + Math.min(24, shifts * shiftHours) / 24;
    const available = Math.max(0, end - cursor) * 1440;
    if (available + 1e-7 >= remaining) return cursor + remaining / 1440;
    remaining -= available;
    cursor = day + 1;
  }
  throw new Error("Piston b\xF6l\xFCm\xFC i\xE7in \xE7al\u0131\u015F\u0131labilir bekleme saati bulunamad\u0131. Vardiya ve Mesai Bilgileri\u2019ni kontrol edin.");
}

// lib/delivery-calendar.ts
var EXCEL_EPOCH = Date.UTC(1899, 11, 30);
var DAY_MS2 = 864e5;
var TURNING_DELIVERY_LEAD_WORKDAYS = 4;
function dayOfWeek(serial2) {
  return new Date(EXCEL_EPOCH + Math.floor(serial2) * DAY_MS2).getUTCDay();
}
function addDeliveryWorkdays(completionSerial, workdays) {
  if (!Number.isFinite(completionSerial) || completionSerial <= 0) return completionSerial;
  const fraction = completionSerial - Math.floor(completionSerial);
  let serial2 = Math.floor(completionSerial);
  let remaining = Math.max(0, Math.trunc(workdays));
  while (remaining > 0) {
    serial2 += 1;
    if (dayOfWeek(serial2) !== 0) remaining -= 1;
  }
  return serial2 + fraction;
}
function isFactoryWorkday(seed, serialValue) {
  const serial2 = Math.floor(serialValue);
  const addedShift = (seed.calendarEvents ?? []).some(
    (event) => event.kind === "shift" && event.shiftCount > 0 && serial2 >= Math.floor(event.start) && serial2 <= Math.floor(event.end)
  );
  if (addedShift) return true;
  const holiday = seed.holidays.find((item) => Math.floor(item.serial) === serial2);
  if (holiday) return (holiday.workingShifts ?? 0) > 0;
  return dayOfWeek(serial2) !== 0;
}
function addFactoryWorkdays(seed, startValue, workdaysValue) {
  if (!Number.isFinite(startValue) || startValue <= 0) return startValue;
  const workdays = Math.max(0, Math.trunc(workdaysValue));
  if (!workdays) return startValue;
  let serial2 = Math.floor(startValue);
  let remaining = workdays;
  while (remaining > 0) {
    serial2 += 1;
    if (isFactoryWorkday(seed, serial2)) remaining -= 1;
  }
  return serial2;
}
function turningDeliveryReadyAt(completionSerial) {
  return addDeliveryWorkdays(completionSerial, TURNING_DELIVERY_LEAD_WORKDAYS);
}
function routedDeliveryReadyAt(seed, routeCompletionSerial, family, lastProcess = "gkm") {
  const rule = family ? flowRule(seed, family, lastProcess, "delivery") : void 0;
  if (rule?.mode === "static") return addDepartmentWorkMinutes(seed, routeCompletionSerial, rule.minutes);
  return seed.productionArea === "cubuk-filtre" ? seed.monthlyCustomerDemand ? filterQualityReadyAt(seed, routeCompletionSerial) : routeCompletionSerial + 0.5 : addFactoryWorkdays(seed, routeCompletionSerial, processWaitWorkdays(seed, lastProcess));
}

// lib/shared-charge.ts
function chargeIdNamespace() {
  return BigInt(`0x${crypto.randomUUID().replace(/-/g, "")}`).toString(36);
}
function allocateSharedQuantity(quantity, resources) {
  if (!Number.isSafeInteger(quantity) || quantity <= 0 || !resources.length) return void 0;
  const limits = resources.filter((item) => Number.isFinite(item.start) && Number.isFinite(item.end) && item.end > item.start);
  if (!limits.length) return void 0;
  const capacity = (item, until) => Math.min(quantity, Math.max(0, Math.floor(item.capacity(Math.min(until, item.end)) + 1e-6)));
  let low = Math.min(...limits.map((item) => item.start)), high = Math.max(...limits.map((item) => item.end));
  if (limits.reduce((sum, item) => sum + capacity(item, high), 0) < quantity) return void 0;
  for (let i = 0; i < 42; i++) {
    const middle = (low + high) / 2;
    if (limits.reduce((sum, item) => sum + capacity(item, middle), 0) >= quantity) high = middle;
    else low = middle;
  }
  let left = quantity;
  const allocations = limits.flatMap((item) => {
    const count = Math.min(left, capacity(item, high));
    if (!count) return [];
    const timing = item.timing(count);
    if (!Number.isFinite(timing.end) || timing.end > item.end + 1e-6) return [];
    left -= count;
    return [{ resource: item.resource, quantity: count, ...timing }];
  });
  return left === 0 ? allocations : void 0;
}
function filterTurningGroup(id) {
  return ["L-01", "L-02"].includes(id) ? "transfer" : ["L-03", "L-04", "L-05", "L-06"].includes(id) ? "lathe" : id;
}

// lib/process-placement-identity.ts
function processPlacementIdentities(seed, batchId, allowInheritance = true) {
  const identities = [batchId];
  const sourceBatchIds = /* @__PURE__ */ new Set();
  let lot = seed.wipLots?.find((item) => item.id === batchId);
  const visited = /* @__PURE__ */ new Set();
  while (allowInheritance && lot && !visited.has(lot.id)) {
    visited.add(lot.id);
    if (lot.sourceBatchId) sourceBatchIds.add(lot.sourceBatchId);
    if (lot.parentLotId) identities.push(lot.parentLotId);
    lot = seed.wipLots?.find((item) => item.id === lot.parentLotId);
  }
  identities.push(...sourceBatchIds);
  const machine = seed.machines?.find((item) => `current:${item.id}` === batchId);
  if (allowInheritance && machine?.currentJob.batchId) identities.push(machine.currentJob.batchId);
  return identities;
}

// lib/process-flow.ts
function curve(seed, resource, start, end, setupHours, quantity, capacityAt) {
  const windows = [];
  let setup = setupHours, hours = 0;
  if (end - start > 36600 || end <= start || quantity <= 0) return void 0;
  for (let day = Math.floor(start); day <= Math.floor(end); day += 1) {
    const shifts = (capacityAt ? capacityAt(day) : machineDayCapacity(seed, resource, day)).shifts;
    let left = Math.max(start, day);
    const right = Math.min(end, day + shifts * getSetupSettings(seed).shiftHours / 24);
    const skipped = Math.min(setup, Math.max(0, right - left) * 24);
    setup -= skipped;
    left += skipped / 24;
    if (right > left) {
      windows.push({ start: left, end: right });
      hours += (right - left) * 24;
    }
  }
  if (hours <= 1e-8) return void 0;
  let before = 0;
  const rate = quantity / hours * 24;
  const segments = windows.map((window2) => {
    const segment = { ...window2, before, rate };
    before += (window2.end - window2.start) * rate;
    return segment;
  });
  return { segments, quantity, start: windows[0].start, end: windows.at(-1).end };
}
function produced(curve2, time) {
  if (time < curve2.start - 1e-10) return 0;
  if (time >= curve2.end) return curve2.quantity;
  const segment = curve2.segments.find((item) => time <= item.end) ?? curve2.segments.at(-1);
  return Math.min(curve2.quantity, segment.before + Math.max(0, time - segment.start) * segment.rate);
}
function noStarvation(supply, demand) {
  const times = [...supply.segments, ...demand.segments].flatMap((item) => [item.start, item.end]);
  for (const time of times) {
    if (time < demand.start - 1e-10 || time > demand.end + 1e-10) continue;
    const needed = Math.min(demand.quantity, produced(demand, time) + Math.min(1, demand.quantity));
    if (produced(supply, time) + 1e-5 < needed) return false;
  }
  for (const segment of demand.segments) {
    const time = segment.start + (demand.quantity - Math.min(1, demand.quantity) - segment.before) / segment.rate;
    if (time >= segment.start && time <= segment.end && produced(supply, time) + 1e-5 < demand.quantity) return false;
  }
  return true;
}
function dynamicFlowTiming(seed, calendarSeed, resource, predecessor, requestedStart, setupHours, runHours, quantity, targetMinutes) {
  const machine = { id: resource.id, shiftFactor: resource.defaultShifts, finishOffset: 0 };
  const capacities = /* @__PURE__ */ new Map();
  const capacityAt = (day) => {
    let value = capacities.get(day);
    if (!value) {
      value = machineDayCapacity(calendarSeed, machine, day);
      capacities.set(day, value);
    }
    return value;
  };
  const schedule = (start) => addMachineCapacityHours(calendarSeed, machine, start, setupHours + runHours, capacityAt);
  const targetEnd = predecessor.end + targetMinutes / 1440;
  const upstream = predecessor.process === "turning" ? seed.machines.find((item) => item.id === predecessor.resourceId) : seed.processMasterData?.resources.find((item) => item.id === predecessor.resourceId);
  const upstreamCalendar = predecessor.resourceId.startsWith("B-01-") ? { ...seed, calendarEvents: seed.calendarEvents?.map((event) => event.machineId === "B-01" ? { ...event, machineId: predecessor.resourceId } : event) } : seed;
  const supply = upstream && !predecessor.current && !(predecessor.process === "turning" && predecessor.source === "current-turning") && !predecessor.actual && predecessor.quantity === quantity ? curve(upstreamCalendar, { id: upstream.id, shiftFactor: "shiftFactor" in upstream ? upstream.shiftFactor : upstream.defaultShifts }, predecessor.start, predecessor.end, predecessor.setupHours, quantity) : void 0;
  if (!supply) return { ...schedule(Math.max(requestedStart, predecessor.end)), targetEnd, reason: "\xD6nceki prosesin g\xFCvenilir par\xE7a \xE7\u0131k\u0131\u015F e\u011Frisi yok; kay\u0131tl\u0131 biti\u015F sonras\u0131 g\xFCvenli ba\u015Flang\u0131\xE7 kullan\u0131ld\u0131." };
  const safe = (start) => {
    const timing = schedule(start);
    const consumption = curve(calendarSeed, machine, timing.start, timing.end, setupHours, quantity, capacityAt);
    return !!consumption && noStarvation(supply, consumption);
  };
  let left = Math.max(requestedStart, predecessor.start), right = Math.max(left, predecessor.end);
  if (!safe(left)) {
    for (let iteration = 0; iteration < 36; iteration += 1) {
      const middle = (left + right) / 2;
      if (safe(middle)) right = middle;
      else left = middle;
    }
    left = right;
  }
  const earliest = schedule(left + 1e-8);
  if (earliest.end > targetEnd + 1e-6) return { ...earliest, targetEnd, reason: "Hedef; par\xE7a beslemesi, setup, vardiya/bak\u0131m veya dolu kuyruk nedeniyle sa\u011Flanam\u0131yor. En erken kesintisiz ve g\xFCvenli biti\u015F g\xF6steriliyor." };
  right = Math.max(left, targetEnd);
  for (let iteration = 0; iteration < 36; iteration += 1) {
    const middle = (left + right) / 2;
    if (schedule(middle).end <= targetEnd + 1e-7) left = middle;
    else right = middle;
  }
  return { ...schedule(left), targetEnd };
}

// lib/turning-queue-identity.ts
function reconcileTurningQueue(seed, batches) {
  const inspected = inspectTurningQueue(seed, batches);
  if (inspected.conflicts.length) throw new Error(inspected.conflicts[0].message);
  return inspected.reconciledBatches;
}
function recoveredTurningBatches(seed) {
  const original = seed.manualBatches ?? [];
  const positions = new Map(original.map((batch, index) => [batch.id, index]));
  return withInterruptedBatches(seed, original).sort((a, b) => (positions.get(a.id) ?? original.length) - (positions.get(b.id) ?? original.length));
}
function reconcileTurningSeed(seed) {
  const original = seed.manualBatches ?? [];
  const batches = reconcileTurningQueue(seed, recoveredTurningBatches(seed));
  if (JSON.stringify(batches) === JSON.stringify(original)) return seed;
  return { ...seed, manualBatches: batches, lastAutomaticPlan: void 0, planNeedsRecalculation: true };
}
var identityKey = (value) => String(value ?? "").trim().toUpperCase();
var identityMessage = (batch) => `${batch.machineId} \xB7 ${batch.workOrder || batch.product}: mevcut \xFCretim/ar\u015Fiv ile kuyruktaki \u015Farj kimli\u011Fi belirsiz. \u0130\u015F emri ve \u015Farj kay\u0131tlar\u0131n\u0131 kontrol edin; i\u015Flem uygulanmad\u0131.`;
function inspectTurningQueue(seed, batches = seed.manualBatches ?? []) {
  const records2 = [
    ...seed.machines.filter((m) => m.currentJob.quantity > 0).map((m) => ({ kind: "current", id: m.id, chargeId: m.currentJob.batchId, machineId: m.id, product: m.currentJob.product, workOrder: m.currentJob.workOrder, quantity: m.currentJob.originalQuantity ?? m.currentJob.quantity })),
    ...(seed.productionHistory ?? []).filter((h) => (!h.process || h.process === "turning") && h.inventoryStatus !== "voided" && !h.interruptionIds?.length).map((h) => ({ kind: "history", id: h.id, chargeId: h.sourceBatchId === h.id ? void 0 : h.sourceBatchId, machineId: h.machineId, product: h.product, workOrder: h.workOrder, quantity: h.originalQuantity, status: h.inventoryStatus })),
    ...(seed.wipLots ?? []).filter((l) => l.sourceBatchId && l.sourceBatchId !== l.sourceHistoryEntryId && !seed.productionHistory?.some((h) => h.id === l.sourceHistoryEntryId && h.inventoryStatus === "voided")).map((l) => ({ kind: "wip", id: l.id, chargeId: l.sourceBatchId, machineId: "", product: l.product, workOrder: l.workOrder, quantity: l.originalQuantity, status: l.stage }))
  ];
  const conflicts = [];
  const reconciledBatches = batches.filter((batch) => {
    const duplicates = batches.filter((b) => b.id === batch.id);
    const exact = records2.filter((r) => r.chargeId && r.chargeId === batch.id);
    const legacy = records2.filter((r) => !r.chargeId && identityKey(r.workOrder) && identityKey(r.workOrder) === identityKey(batch.workOrder) && identityKey(r.product) === identityKey(batch.product));
    let reason;
    let evidence = [];
    if (duplicates.length > 1) {
      reason = "duplicate-queue-id";
      evidence = duplicates.map((b) => ({ kind: "queue", id: b.id, machineId: b.machineId, product: b.product, workOrder: b.workOrder ?? "", quantity: b.quantity }));
    } else if (exact.length) {
      if (exact.some((r) => identityKey(r.product) !== identityKey(batch.product))) {
        reason = "product-mismatch";
        evidence = exact;
      } else return false;
    } else if (!hasProtectedProductionRemainder(seed, batch.id, batch.interruptionId) && legacy.length) {
      const candidates = batches.filter((b) => identityKey(b.workOrder) === identityKey(batch.workOrder) && identityKey(b.product) === identityKey(batch.product));
      if (legacy.length !== 1 || candidates.length !== 1 || legacy[0].quantity !== batch.quantity || legacy[0].machineId !== batch.machineId) {
        reason = "legacy-ambiguous";
        evidence = legacy;
      } else return false;
    }
    if (reason && reason !== "duplicate-queue-id") evidence.push({ kind: "queue", id: batch.id, machineId: batch.machineId, product: batch.product, workOrder: batch.workOrder ?? "", quantity: batch.quantity, status: batch.locked ? "locked" : batch.status });
    if (reason) conflicts.push({ batchId: batch.id, machineId: batch.machineId, product: batch.product, workOrder: batch.workOrder ?? "", message: identityMessage(batch), reason, records: evidence.map((r) => ({ kind: r.kind, id: r.id, machineId: r.machineId, product: r.product, workOrder: r.workOrder, quantity: r.quantity, ...r.status ? { status: r.status } : {} })) });
    return true;
  });
  return { conflicts, reconciledBatches };
}
function turningIdentityScope(seed, batches = seed.manualBatches ?? []) {
  const conflicts = inspectTurningQueue(seed, batches).conflicts;
  const products = new Set(conflicts.flatMap((c) => [c.product, ...c.records.map((r) => r.product)]).map(identityKey).filter(Boolean));
  const machineIds = new Set(conflicts.flatMap((c) => [c.machineId, ...c.records.map((r) => r.machineId)]).filter(Boolean));
  const batchIds = new Set(conflicts.map((c) => c.batchId));
  const lotIds = /* @__PURE__ */ new Set();
  const historyIds = /* @__PURE__ */ new Set();
  const add = (set, value) => {
    if (value) set.add(value);
  };
  const related = (product) => products.has(identityKey(product));
  let size = -1;
  while (size !== machineIds.size + batchIds.size + lotIds.size + historyIds.size) {
    size = machineIds.size + batchIds.size + lotIds.size + historyIds.size;
    for (const b of batches) if (related(b.product) || batchIds.has(b.id) || machineIds.has(b.machineId)) {
      add(machineIds, b.machineId);
      add(batchIds, b.id);
    }
    for (const m of seed.machines) if (related(m.currentJob.product) || batchIds.has(m.currentJob.batchId ?? "") || machineIds.has(m.id)) {
      add(machineIds, m.id);
      add(batchIds, m.currentJob.batchId);
      add(batchIds, `current:${m.id}`);
    }
    for (const h of seed.productionHistory ?? []) if (related(h.product) || historyIds.has(h.id) || historyIds.has(h.sourceEntryId ?? "") || batchIds.has(h.sourceBatchId ?? "") || h.wipAllocations?.some((a) => lotIds.has(a.lotId))) {
      add(historyIds, h.id);
      add(historyIds, h.sourceEntryId);
      add(batchIds, h.sourceBatchId);
      for (const a of h.wipAllocations ?? []) add(lotIds, a.lotId);
    }
    for (const l of seed.wipLots ?? []) if (related(l.product) || lotIds.has(l.id) || lotIds.has(l.parentLotId ?? "") || historyIds.has(l.sourceHistoryEntryId) || batchIds.has(l.sourceBatchId ?? "")) {
      add(lotIds, l.id);
      add(lotIds, l.parentLotId);
      add(historyIds, l.sourceHistoryEntryId);
      add(batchIds, l.sourceBatchId);
    }
    for (const j of seed.processCurrentJobs ?? []) if (related(j.product) || batchIds.has(j.batchId) || lotIds.has(j.wipLotId)) {
      add(batchIds, j.batchId);
      add(lotIds, j.wipLotId);
    }
    for (const i of seed.productionInterruptions ?? []) if (related(i.product) || batchIds.has(i.chargeId)) {
      add(batchIds, i.chargeId);
      if (i.process === "turning") add(machineIds, i.resourceId);
    }
  }
  return { products: [...products].sort(), machineIds: [...machineIds].sort(), batchIds: [...batchIds].sort(), lotIds: [...lotIds].sort(), historyIds: [...historyIds].sort() };
}
function structural(value) {
  return JSON.stringify(value, (_key, item) => item && typeof item === "object" && !Array.isArray(item) ? Object.fromEntries(Object.keys(item).sort().filter((k) => item[k] !== void 0).map((k) => [k, item[k]])) : item);
}
var frozenConfiguration = ["products", "preferences", "restrictions", "holidays", "calendarEvents", "setupSettings", "processWaitSettings", "processMasterData", "savedBatches", "activePlanningScope", "customerDemand", "openingStock", "demandTargets", "orderImport", "orderImportGrossOrders", "customerOrderOverrides"];
function protectedIdentitySnapshot(seed, scope) {
  const p = (value) => scope.products.includes(identityKey(value));
  const b = (value) => Boolean(value && scope.batchIds.includes(value));
  const l = (value) => Boolean(value && scope.lotIds.includes(value));
  const h = (value) => Boolean(value && scope.historyIds.includes(value));
  return {
    configuration: Object.fromEntries(frozenConfiguration.map((k) => [k, seed[k] ?? null])),
    machines: seed.machines.filter((m) => scope.machineIds.includes(m.id) || p(m.currentJob.product) || b(m.currentJob.batchId)),
    manualBatches: (seed.manualBatches ?? []).filter((r) => p(r.product) || b(r.id) || scope.machineIds.includes(r.machineId)),
    productionHistory: (seed.productionHistory ?? []).filter((r) => p(r.product) || h(r.id) || h(r.sourceEntryId) || b(r.sourceBatchId) || r.wipAllocations?.some((a) => l(a.lotId))),
    wipLots: (seed.wipLots ?? []).filter((r) => p(r.product) || l(r.id) || l(r.parentLotId) || h(r.sourceHistoryEntryId) || b(r.sourceBatchId)),
    wipMovements: (seed.wipMovements ?? []).filter((r) => l(r.lotId)),
    productionInterruptions: (seed.productionInterruptions ?? []).filter((r) => p(r.product) || b(r.chargeId) || r.process === "turning" && scope.machineIds.includes(r.resourceId)),
    processCurrentJobs: (seed.processCurrentJobs ?? []).filter((r) => p(r.product) || b(r.batchId) || l(r.wipLotId)),
    processOperationOverrides: (seed.processOperationOverrides ?? []).filter((r) => b(r.batchId) || l(r.batchId)),
    orders: seed.orders.filter((r) => p(r.product))
  };
}
function assertNoReconciledDuplicates(seed) {
  const checked = reconcileTurningSeed(seed);
  if (structural(checked.manualBatches ?? []) !== structural(seed.manualBatches ?? [])) throw new Error("Mevcut veya tamamlanm\u0131\u015F \u015Farj kuyrukta tekrar bulunuyor. Ortak veriyi y\xFCkleyin.");
}
function assertTurningIdentityTransition(before, next) {
  const previous = inspectTurningQueue(before).conflicts;
  if (!previous.length) {
    assertNoReconciledDuplicates(next);
    return;
  }
  const scope = turningIdentityScope(before);
  if (structural(protectedIdentitySnapshot(before, scope)) !== structural(protectedIdentitySnapshot(next, scope))) throw new Error("Bu i\u015Flem inceleme bekleyen \u015Farj\u0131 veya ba\u011Fl\u0131 kay\u0131tlar\u0131n\u0131 de\u011Fi\u015Ftiriyor. \xD6nce \u0130ncele ve d\xFCzelt ile \u015Farj kayd\u0131n\u0131 do\u011Frulay\u0131n.");
  if (structural(recoveredTurningBatches(next)) !== structural(next.manualBatches ?? [])) throw new Error("Yar\u0131m kalan \u015Farj\u0131n kuyruk kayd\u0131 korunmal\u0131d\u0131r. Ortak veriyi y\xFCkleyin.");
  const inspected = inspectTurningQueue(next);
  if (structural(previous) !== structural(inspected.conflicts)) throw new Error("\u0130\u015Flem yeni bir \u015Farj kimli\u011Fi \xE7ak\u0131\u015Fmas\u0131 olu\u015Fturuyor. \u0130ncele ve d\xFCzelt ile kay\u0131tlar\u0131 do\u011Frulay\u0131n.");
  if (inspected.reconciledBatches.length !== (next.manualBatches ?? []).length) throw new Error("Mevcut veya tamamlanm\u0131\u015F \u015Farj kuyrukta tekrar bulunuyor. Ortak veriyi y\xFCkleyin.");
}

// lib/process-eligibility.ts
function actualProcessStartEligibility(seed, operation, at, confirmedInterruption = false) {
  const denied = (reason) => ({ ok: false, reason });
  if (!Number.isFinite(at) || at <= 0) return denied("Ge\xE7erli bir \xFCretim ba\u015Flang\u0131\xE7 tarihi se\xE7in.");
  if (operation.actual || operation.current || operation.process === "turning" || operation.source !== "wip") return denied("Bu i\u015F hen\xFCz sahadaki yar\u0131 mam\xFCl de\u011Fil; \xF6nce \xF6nceki operasyon tamamlanmal\u0131.");
  const lot = seed.wipLots?.find((l) => l.id === operation.wipLotId);
  if (!lot || lot.nextProcess !== operation.process || lot.availableQuantity <= 0 || lot.stage === "on-hold" || lot.stage === "unclassified") return denied("\xD6nceki proses hen\xFCz tamamlanmad\u0131 veya yar\u0131 mam\xFCl serbest b\u0131rak\u0131lmad\u0131.");
  if (!Number.isInteger(operation.quantity) || operation.quantity <= 0 || operation.quantity > lot.availableQuantity) return denied("\xDCretime al\u0131nacak adet yar\u0131 mam\xFCl bakiyesiyle uyu\u015Fmuyor.");
  if (!Number.isFinite(wipOperationReadyAt(lot)) || wipOperationReadyAt(lot) > at + 1e-8) return denied("Yar\u0131 mam\xFCl\xFCn ger\xE7ek haz\u0131r olma tarihi hen\xFCz gelmedi.");
  if (activeLotInterruptions(seed, lot).length && !confirmedInterruption) return denied("\xDCretim sonlanmad\u0131, yine de \xFCretime alay\u0131m m\u0131? Devam etmek i\xE7in onaylay\u0131n.");
  if (seed.processCurrentJobs?.some((j) => j.resourceId === operation.resourceId)) return denied(`${operation.resourceId} \xFCzerinde zaten \xE7al\u0131\u015Fan bir i\u015F var.`);
  const resource = seed.processMasterData?.resources.find((r) => r.id === operation.resourceId);
  const product = processMasterDataForProduct(seed.processMasterData, lot.product);
  const parameter = product?.processes.find((p) => p.process === operation.process);
  if (!resource?.active || resource.process !== operation.process || resource.defaultShifts <= 0 || !product || !resourceSupportsProcessProduct(resource, product) || !parameter || !activeProcessResourceIds(parameter).includes(resource.id) || !Number.isFinite(parameter.unitsPerShift[resource.id]) || parameter.unitsPerShift[resource.id] <= 0 || product.route && !product.route.includes(operation.process)) return denied("\u0130\u015F merkezi, \xFCr\xFCn rotas\u0131 veya vardiya kapasitesi \xFCretime uygun de\u011Fil.");
  if ((resource.availableStart ?? 0) > at + 1e-8 || resource.planEnd && at >= Math.floor(resource.planEnd) + 1) return denied("\u0130\u015F merkezi se\xE7ilen tarihte \xFCretime uygun de\u011Fil.");
  return { ok: true, reason: "" };
}

// lib/process-route-state.ts
function describeProcessRoute(seed, job, warnings) {
  const product = processMasterDataForProduct(seed.processMasterData, job.product);
  if (!product) return { routeSteps: [], readinessIssues: [{ code: "missing-product", message: "\xDCr\xFCn rotas\u0131 bulunamad\u0131; miktar korunuyor." }] };
  const route = effectiveProductRoute(product, job.turningMachineId);
  const lot = seed.wipLots?.find((l) => l.id === job.wipLotId);
  const chargeId = job.source === "current-turning" ? seed.machines?.find((m) => m.id === job.turningMachineId)?.currentJob.batchId : job.batchId;
  const pause = seed.productionInterruptions?.find((p) => isProductionInterruption(p) && !p.completedAt && p.chargeId === chargeId);
  const partial = activeLotInterruptions(seed, lot).length > 0;
  const issues = [];
  const routeSteps = route.map((process2) => {
    const op = job.operations.find((o) => (o.recordedProcess ?? o.process) === process2);
    const base = { process: process2, quantity: job.quantity, operationId: op?.id, resourceId: op?.resourceId };
    if (op?.actual) return { ...base, state: "completed" };
    if (lot?.manualReceipt?.completedProcesses.includes(process2)) return { ...base, state: "completed", reason: lot.manualReceipt.productionDate === void 0 ? "Manuel adet kayd\u0131 ile do\u011Frulanan proses konumu; \xFCretim tarihi bilinmiyor." : "Manuel adet kayd\u0131 ile do\u011Frulanan proses konumu; ge\xE7mi\u015F tezgah i\u015Fi olu\u015Fturulmad\u0131." };
    if (op?.current || job.source === "current-turning" && process2 === "turning" || seed.processCurrentJobs?.some((current) => current.batchId === job.batchId && current.process === process2)) return { ...base, state: "running" };
    if (op) return { ...base, state: "scheduled" };
    let state = "capacity-blocked";
    let message = `${processLabel(process2)} i\xE7in tarih hesaplanamad\u0131; kapasite ve kay\u0131tl\u0131 yerle\u015Fimi kontrol edin.`;
    let code3 = state;
    if (lot?.stage === "on-hold" || lot?.stage === "unclassified") {
      code3 = lot.stage === "on-hold" ? "held" : "unclassified";
      state = "predecessor-pending";
      message = lot.stage === "on-hold" ? "Yar\u0131 mam\xFCl blokeli." : "Yar\u0131 mam\xFCl\xFCn ger\xE7ek konumu do\u011Frulanmal\u0131.";
    } else if (pause && route.indexOf(process2) >= route.indexOf(pause.process)) {
      state = process2 === pause.process ? "paused" : "predecessor-pending";
      code3 = state;
      message = process2 === pause.process ? "Ara verilen i\u015F kuyrukta korunuyor." : "Ara verilen \xF6nceki prosesin tamamlanmas\u0131 bekleniyor.";
    } else if (partial) {
      state = process2 === lot?.nextProcess ? "manual-required" : "predecessor-pending";
      code3 = state;
      message = state === "manual-required" ? "Yar\u0131m \xFCretim: bu prosesi Manuel \u015Farj ile kuyru\u011Fa ekleyin." : "\xD6nceki proses ve manuel \xFCretim onay\u0131 bekleniyor.";
    } else if (seed.plannedThroughProcess !== void 0 && productionProcessOrder(seed).indexOf(process2) > productionProcessOrder(seed).indexOf(seed.plannedThroughProcess)) {
      state = "predecessor-pending";
      code3 = state;
      message = `${processLabel(process2)} hen\xFCz planlanmad\u0131. Sonraki prosesi planla veya T\xFCm prosesi planla ile devam edin.`;
    } else if (warnings.some((w) => w.product === job.product && (w.code === "invalid-route" || w.code === "missing-parameter" && !w.batchId))) {
      state = "invalid-route";
      code3 = state;
      message = "\xDCr\xFCn rotas\u0131 veya proses parametreleri eksik.";
    } else if (route.indexOf(process2) > 0 && !job.operations.some((o) => (o.recordedProcess ?? o.process) === route[route.indexOf(process2) - 1])) {
      state = "predecessor-pending";
      code3 = state;
      message = "\xD6nceki prosesin haz\u0131r olma tarihi belirlenemedi.";
    }
    issues.push({ code: code3, message, process: process2 });
    return { ...base, state, reason: message };
  });
  if (!route.length) issues.push({ code: "invalid-route", message: "Aktif \xFCr\xFCn rotas\u0131 bulunamad\u0131." });
  if (!job.deliveryReadyAt && !issues.length) issues.push({ code: "missing-schedule", message: "Teslimata haz\u0131r tarih do\u011Frulanamad\u0131." });
  return { routeSteps, readinessIssues: issues };
}
function processQueueEntries(seed, jobs, operations) {
  const rows = /* @__PURE__ */ new Map();
  const intents = (seed.processOperationOverrides ?? []).filter((intent) => intent.routeMode !== "automatic");
  for (const pause of seed.productionInterruptions ?? []) {
    if (!isProductionInterruption(pause) || pause.completedAt || pause.process === "turning" || pause.process === "washing" || intents.some((i) => i.batchId === pause.chargeId && i.process === pause.process)) continue;
    intents.push({ batchId: pause.chargeId, process: pause.process, resourceId: pause.resourceId, requestedStart: pause.occurredAt, resumeAfterCurrent: true, updatedAt: "" });
  }
  for (const intent of intents) {
    const job = jobs.find((j) => j.batchId === intent.batchId);
    if (!job || job.quantity <= 0) continue;
    const step = job.routeSteps?.find((s) => s.process === intent.process);
    if (step?.state === "completed" || step?.state === "running") continue;
    if (seed.plannedThroughProcess !== void 0 && productionProcessOrder(seed).indexOf(intent.process) > productionProcessOrder(seed).indexOf(seed.plannedThroughProcess)) continue;
    if (seed.processCurrentJobs?.some((c) => c.batchId === job.batchId && c.process === intent.process)) continue;
    const op = operations.find((o) => o.batchId === job.batchId && o.process === intent.process && !o.actual && !o.current);
    rows.set(`${job.batchId}:${intent.process}`, { id: `${job.batchId}:${intent.process}`, batchId: job.batchId, product: job.product, workOrder: job.workOrder, quantity: job.quantity, process: intent.process, resourceId: intent.resourceId, scheduled: Boolean(op), operationId: op?.id, reason: op ? void 0 : step?.reason ?? "Kay\u0131tl\u0131 i\u015F i\xE7in tarih hesaplanamad\u0131; rota ve kapasiteyi kontrol edin.", queueOrder: intent.queueOrder ?? Number.MAX_SAFE_INTEGER, resumeAfterCurrent: Boolean(intent.resumeAfterCurrent) });
  }
  return [...rows.values()].sort((a, b) => Number(b.resumeAfterCurrent) - Number(a.resumeAfterCurrent) || a.queueOrder - b.queueOrder || a.id.localeCompare(b.id));
}

// lib/weekly-plan-status.ts
function inputDateSerial(value) {
  return value ? (Date.parse(`${value}T00:00:00Z`) - Date.UTC(1899, 11, 30)) / 864e5 : 0;
}
function routedQuantityByDate(seed, events, product, serial2) {
  return deliveryReadyQuantityFromEvents(seed, events, product, serial2);
}
function checkpointsForOrder(order) {
  const byDate = /* @__PURE__ */ new Map();
  for (const milestone of orderDeliveryMilestones(order)) {
    if (!milestone.date) continue;
    byDate.set(milestone.date, Math.max(byDate.get(milestone.date) ?? 0, milestone.quantity));
  }
  if (order.dueDate) byDate.set(order.dueDate, Math.max(byDate.get(order.dueDate) ?? 0, order.quantity));
  let previousQuantity = 0;
  return [...byDate.entries()].map(([date, quantity]) => ({ date, quantity })).sort((left, right) => left.date.localeCompare(right.date)).map((checkpoint) => {
    const incrementalQuantity = Math.max(0, checkpoint.quantity - previousQuantity);
    previousQuantity = Math.max(previousQuantity, checkpoint.quantity);
    return { ...checkpoint, quantity: incrementalQuantity };
  });
}
function weekLabel(seed, dueDate) {
  const matchingWeek = seed.customerDemand?.weeks.find((week) => week.weekEnd === dueDate);
  if (matchingWeek) return `W${String(matchingWeek.isoWeek).padStart(2, "0")}`;
  const activeStart = seed.customerDemand?.weeks.find((week) => week.id === seed.customerDemand?.activeScope.startWeekId)?.weekStart ?? seed.customerDemand?.weeks[0]?.weekStart;
  if (activeStart && dueDate < activeStart) return "Devreden";
  return new Intl.DateTimeFormat("tr-TR", { day: "2-digit", month: "short", timeZone: "UTC" }).format(/* @__PURE__ */ new Date(`${dueDate}T00:00:00Z`));
}
function excludedPriorBacklogStatus(seed, result, readinessEvents) {
  const demand = seed.customerDemand;
  if (!demand || (seed.activePlanRun?.includePriorBacklog ?? true)) return null;
  const startIndex = demand.weeks.findIndex((week) => week.id === demand.activeScope.startWeekId);
  const activeWeek = demand.weeks[startIndex];
  if (!activeWeek) return null;
  const dueSerial = inputDateSerial(activeWeek.weekStart) - 2;
  const dueDate = new Date(Date.UTC(1899, 11, 30) + dueSerial * 864e5).toISOString().slice(0, 10);
  const products = demand.products.map((product) => {
    const required2 = Math.max(0, startIndex === 0 ? product.priorDemand : product.weeklyDemands[startIndex - 1]?.cumulativeQuantity ?? product.priorDemand);
    const available = routedQuantityByDate(seed, readinessEvents, product.product, dueSerial);
    const ready2 = Math.min(required2, available);
    return { product: product.product.toUpperCase(), required: required2, ready: ready2, shortage: Math.max(0, required2 - ready2) };
  }).filter((product) => product.required > 0);
  const required = products.reduce((sum, product) => sum + product.required, 0);
  if (required <= 0) return null;
  const ready = products.reduce((sum, product) => sum + product.ready, 0);
  return {
    id: "excluded-prior-backlog",
    label: "Devreden a\xE7\u0131k",
    dueDate,
    newDemand: required,
    required,
    ready,
    shortage: Math.max(0, required - ready),
    riskProductCount: products.filter((product) => product.shortage > 0).length,
    products,
    excludedFromPlan: true
  };
}
function buildWeeklyPlanStatus(seed, result, readinessEvents = buildDeliveryReadinessEvents(seed, result)) {
  const checkpointsByProduct = /* @__PURE__ */ new Map();
  for (const order of seed.orders.filter((item) => item.quantity > 0)) {
    const product = order.product.toUpperCase();
    const current = checkpointsByProduct.get(product) ?? [];
    checkpointsByProduct.set(product, [...current, ...checkpointsForOrder(order)]);
  }
  const dates = [...new Set([...checkpointsByProduct.values()].flatMap((checkpoints) => checkpoints.map((checkpoint) => checkpoint.date)))].filter(Boolean).sort();
  let previousRequired = 0;
  const weeklyRows = dates.map((dueDate) => {
    const dueSerial = inputDateSerial(dueDate);
    const products = [...checkpointsByProduct.entries()].map(([product, checkpoints]) => {
      const required2 = checkpoints.filter((checkpoint) => checkpoint.date <= dueDate).reduce((sum, checkpoint) => sum + checkpoint.quantity, 0);
      const available = routedQuantityByDate(seed, readinessEvents, product, dueSerial);
      const ready2 = Math.min(required2, available);
      return { product, required: required2, ready: ready2, shortage: Math.max(0, required2 - ready2) };
    }).filter((product) => product.required > 0);
    const required = products.reduce((sum, product) => sum + product.required, 0);
    const ready = products.reduce((sum, product) => sum + product.ready, 0);
    const row = {
      id: dueDate,
      label: weekLabel(seed, dueDate),
      dueDate,
      newDemand: Math.max(0, required - previousRequired),
      required,
      ready,
      shortage: Math.max(0, required - ready),
      riskProductCount: products.filter((product) => product.shortage > 0).length,
      products
    };
    previousRequired = required;
    return row;
  });
  const excludedPriorBacklog = excludedPriorBacklogStatus(seed, result, readinessEvents);
  return excludedPriorBacklog ? [excludedPriorBacklog, ...weeklyRows] : weeklyRows;
}

// lib/process-planning.ts
function sourceSharedCharge(source) {
  return source.batch?.sharedCharge ?? source.machine?.currentJob.sharedCharge ?? source.lot?.sharedCharge;
}
function sourceChargeKey(source) {
  return `${source.product}:${sourceSharedCharge(source)?.id ?? (source.workOrder.trim() || source.id)}`;
}
function calculateDownstreamSetup(process2, previous, next, settings) {
  if (settings?.enabled && (process2 === "drilling" || process2 === "deburring" || process2 === "gkm")) {
    const values = settings.setupMinutes[process2];
    const key = !previous ? "first" : previous.product === next.product ? "sameProduct" : previous.family !== next.family ? "differentFamily" : previous.setupKey === next.setupKey ? "sameKey" : "differentKey";
    return { hours: values[key] / 60, label: "SETUP S\xFCreleri" };
  }
  if (process2 === "gkm") return { hours: 0, label: "GKM ge\xE7i\u015Fi \xB7 setup yok" };
  if (!previous) return process2 === "drilling" ? { hours: 3, label: "\u0130lk delme haz\u0131rl\u0131\u011F\u0131" } : { hours: 1, label: "\u0130lk \xE7apak alma haz\u0131rl\u0131\u011F\u0131" };
  if (previous.product === next.product) return { hours: 0, label: "Ayn\u0131 \xFCr\xFCn \xB7 setup yok" };
  if (process2 === "deburring") return { hours: 1, label: "\xDCr\xFCn de\u011Fi\u015Fimi" };
  if (previous.family !== next.family) return { hours: 5, label: "Piston \u2194 Center Pin ge\xE7i\u015Fi" };
  if (previous.setupKey === next.setupKey) return { hours: 1, label: "Ayn\u0131 delik \xE7ap\u0131" };
  return { hours: 3, label: "Farkl\u0131 delik \xE7ap\u0131" };
}
function addProcessWaitWorkdays(seed, startValue, workdaysValue) {
  return addFactoryWorkdays(seed, startValue, workdaysValue);
}
function validateProcessMasterData(master) {
  const warnings = [];
  const resources = /* @__PURE__ */ new Map();
  for (const resource of master.resources) {
    if (resources.has(resource.id)) warnings.push({ code: "duplicate-definition", message: `${resource.id} i\u015F merkezi birden fazla tan\u0131mlanm\u0131\u015F.` });
    resources.set(resource.id, resource);
  }
  const products = /* @__PURE__ */ new Set();
  for (const product of master.products) {
    if (products.has(product.product)) warnings.push({ code: "duplicate-definition", product: product.product, message: `${product.product} \xFCr\xFCn rotas\u0131 birden fazla tan\u0131mlanm\u0131\u015F.` });
    products.add(product.product);
    const expected = product.route ? product.route.filter((process2) => process2 !== "turning") : product.family === "piston" ? ["drilling", "deburring", "gkm"] : ["drilling", "gkm"];
    if (product.route && (!product.route.length || product.route.join("|") !== (product.family === "cubuk-filtre" ? FILTER_PROCESS_ORDER : PRODUCT_PROCESS_ORDER).filter((process2) => product.route.includes(process2)).join("|"))) warnings.push({ code: "invalid-route", product: product.product, message: `${product.product} aktif proses s\u0131ras\u0131 ge\xE7ersiz.` });
    const actual = product.processes.slice().sort((left, right) => left.sequence - right.sequence).map((item) => item.process);
    if (actual.join("|") !== expected.join("|")) warnings.push({ code: "invalid-route", product: product.product, message: `${product.product} rotas\u0131 beklenen proses s\u0131ras\u0131yla uyu\u015Fmuyor.` });
    const processKeys = /* @__PURE__ */ new Set();
    for (const parameter of product.processes) {
      if (processKeys.has(parameter.process)) warnings.push({ code: "duplicate-definition", product: product.product, message: `${product.product} i\xE7in ${parameter.process} prosesi birden fazla tan\u0131mlanm\u0131\u015F.` });
      processKeys.add(parameter.process);
      if (parameter.process === "drilling" && !parameter.setupKey.trim()) warnings.push({ code: "missing-parameter", product: product.product, message: `${product.product} i\xE7in matkap \xE7ap\u0131 tan\u0131ml\u0131 de\u011Fil.` });
      for (const resourceId of parameter.resourcePriority) {
        const resource = resources.get(resourceId);
        if (!resource || resource.process !== parameter.process) {
          warnings.push({ code: "missing-resource", product: product.product, message: `${product.product} \xB7 ${parameter.process} i\xE7in ${resourceId} i\u015F merkezi bulunamad\u0131.` });
        }
        const capacity = parameter.unitsPerShift[resourceId];
        if (!Number.isFinite(capacity) || capacity <= 0) warnings.push({ code: "invalid-capacity", product: product.product, message: `${product.product} \xB7 ${resourceId} vardiya kapasitesi ge\xE7ersiz.` });
      }
    }
  }
  return warnings;
}
function turningOperation(seed, source) {
  const { batch, masterProduct } = source;
  const machine = source.machine ?? seed.machines.find((item) => item.id === batch?.machineId);
  if (!machine) throw new Error("Torna kayna\u011F\u0131 bulunamad\u0131.");
  const current = source.source === "current-turning" ? machine.currentJob : void 0;
  const start = current?.start ?? batch?.start ?? 0;
  const end = current?.end ?? batch?.end ?? 0;
  const quantity = current?.quantity ?? batch?.quantity ?? source.quantity;
  const product = current?.product ?? batch?.product ?? source.product;
  const diameter = current?.diameter ?? batch?.diameter ?? "";
  return {
    id: `${source.id}:turning`,
    ...sourceSharedCharge(source) ? { sharedCharge: sourceSharedCharge(source) } : {},
    batchId: source.id,
    product,
    family: masterProduct.family,
    quantity,
    process: "turning",
    sequence: 0,
    resourceId: machine.id,
    resourceName: machine.name,
    setupKey: diameter,
    unitsPerShift: machine.rates[product.toUpperCase()] ?? 0,
    setupHours: batch?.setupHours ?? 0,
    runHours: batch?.runHours ?? Math.max(0, (end - start) * 24),
    waitWorkdaysBefore: 0,
    readyAt: start,
    start,
    end,
    source: source.source,
    actual: false,
    workOrder: source.workOrder
  };
}
function actualWipOperations(lot, masterProduct) {
  if (!lot) return [];
  return (lot.completedSteps ?? []).map((step, index) => ({
    id: `${lot.id}:${step.process}:actual:${index}`,
    batchId: lot.id,
    product: lot.product,
    family: masterProduct?.family ?? lot.family,
    quantity: step.quantity,
    process: step.process === "washing" ? "gkm" : step.process,
    recordedProcess: step.process,
    sequence: step.process === "turning" ? 0 : masterProduct?.processes.find((item) => item.process === step.process)?.sequence ?? index + 1,
    resourceId: step.resourceId,
    resourceName: step.resourceName,
    setupKey: "actual",
    unitsPerShift: 0,
    setupHours: 0,
    runHours: step.startPrecision === "day" || step.endPrecision === "day" ? 0 : Math.max(0, (step.end - step.start) * 24),
    actualDurationUnknown: step.startPrecision === "day" || step.endPrecision === "day",
    startPrecision: step.startPrecision,
    endPrecision: step.endPrecision,
    waitWorkdaysBefore: 0,
    waitRuleLabel: "Fiili kay\u0131t \xB7 kay\u0131tl\u0131 ba\u015Flang\u0131\xE7 ve biti\u015F",
    readyAt: step.start,
    start: step.start,
    end: step.end,
    plannedStart: step.plannedStart,
    plannedEnd: step.plannedEnd,
    source: "wip",
    actual: true,
    workOrder: lot.workOrder,
    wipLotId: lot.id
  }));
}
function processCalendarSeed(seed, resourceId) {
  if (!resourceId.startsWith("B-01-S")) return seed;
  const shared = (seed.calendarEvents ?? []).filter((event) => event.machineId === "B-01");
  if (!shared.length) return seed;
  return {
    ...seed,
    calendarEvents: [
      ...seed.calendarEvents ?? [],
      ...shared.map((event) => ({ ...event, id: `${event.id}-${resourceId}`, machineId: resourceId }))
    ]
  };
}
function processResource(master, resourceId) {
  return master.resources.find((resource) => resource.id === resourceId);
}
function setupSourceForOperation(operation) {
  return {
    product: operation.product,
    family: operation.family,
    setupKey: operation.setupKey
  };
}
function processPlacementOverride(seed, batchId, product, process2, allowInheritance = true) {
  const identities = processPlacementIdentities(seed, batchId, allowInheritance);
  const machine = seed.machines?.find((item) => `current:${item.id}` === batchId);
  return identities.flatMap((id) => seed.processOperationOverrides?.filter((item) => item.batchId === id && item.process === process2 && (!item.sourceProduct || item.sourceProduct === product) && (!item.sourceCurrentJobKey || machine && currentJobRouteIdentity(machine) === item.sourceCurrentJobKey)) ?? [])[0];
}
var inputDateSerial2 = (value) => value ? (Date.parse(`${value}T00:00:00Z`) - Date.UTC(1899, 11, 30)) / 864e5 : 0;
function sourceDueSerial(seed, source) {
  const own = source.batch?.demandDueDate ? inputDateSerial2(source.batch.demandDueDate) : 0;
  if (own > 0) return own;
  const dates = seed.orders.filter((order) => order.product.toUpperCase() === source.product.toUpperCase() && order.quantity > 0 && order.dueDate).map((order) => inputDateSerial2(order.dueDate)).filter((value) => value > 0);
  return dates.length ? Math.min(...dates) : void 0;
}
function estimateDeliveryReadyFromStage(seed, master, source, stage) {
  const route = productProcessRoute(source.masterProduct);
  const stageIndex = route.indexOf(stage.process);
  if (stageIndex < 0) return Number.POSITIVE_INFINITY;
  let previous = stage;
  const shiftHours = getSetupSettings(seed).shiftHours;
  for (const process2 of route.slice(stageIndex + 1)) {
    if (process2 === "turning") continue;
    const parameter = source.masterProduct.processes.find((item) => item.process === process2);
    if (!parameter) return Number.POSITIVE_INFINITY;
    const rule = flowRule(seed, source.masterProduct.family, previous.process, process2);
    let best;
    try {
      const readyAt = rule?.mode === "static" ? addDepartmentWorkMinutes(seed, previous.end, rule.minutes) : rule?.mode === "dynamic" && !parameter.leadStages?.length ? previous.start : applyProcessLeadStages(
        seed,
        addProcessWaitWorkdays(seed, previous.end, processWaitWorkdays(seed, previous.process)),
        parameter.leadStages
      );
      for (const resourceId of activeProcessResourceIds(parameter)) {
        const resource = processResource(master, resourceId);
        const rate = parameter.unitsPerShift[resourceId];
        if (!resource?.active || resource.process !== process2 || resource.defaultShifts <= 0 || !resourceSupportsProcessProduct(resource, source.masterProduct) || !Number.isFinite(rate) || rate <= 0) continue;
        const setupHours = parameter.setupMinutesByResource ? (parameter.setupMinutesByResource[resourceId] + (parameter.handlingMinutes ?? 0)) / 60 : calculateDownstreamSetup(process2, void 0, { product: source.product, family: source.masterProduct.family, setupKey: parameter.setupKey }, seed.flowSettings).hours;
        if (!Number.isFinite(setupHours)) continue;
        const runHours = source.quantity / rate * shiftHours;
        const startAt = Math.max(readyAt, resource.availableStart ?? readyAt);
        const calendar = processCalendarSeed(seed, resourceId);
        try {
          const timing = rule?.mode === "dynamic" ? dynamicFlowTiming(seed, calendar, resource, { ...previous, source: source.source, quantity: source.quantity, actual: false }, startAt, setupHours, runHours, source.quantity, rule.minutes) : addMachineCapacityHours(calendar, { id: resourceId, shiftFactor: resource.defaultShifts, finishOffset: 0 }, startAt, setupHours + runHours);
          if (resource.planEnd && timing.end > Math.floor(resource.planEnd) + 1 + 1e-8) continue;
          if (!best || timing.end < best.end) best = { process: process2, resourceId, setupHours, start: timing.start, end: timing.end };
        } catch {
        }
      }
    } catch {
      return Number.POSITIVE_INFINITY;
    }
    if (!best) return Number.POSITIVE_INFINITY;
    previous = best;
  }
  try {
    return routedDeliveryReadyAt(seed, previous.end, source.masterProduct.family, previous.process);
  } catch {
    return Number.POSITIVE_INFINITY;
  }
}
function downstreamSetupRank(process2, option, queue, nextSetup, pinnedForResource, firstSetupHours) {
  const previous = option.gapIndex >= 0 ? option.previousOperation ? setupSourceForOperation(option.previousOperation) : void 0 : queue;
  if (previous?.product === nextSetup.product || Boolean(pinnedForResource?.has(nextSetup.product))) return 0;
  if (process2 === "drilling" && previous) {
    if (previous.family !== nextSetup.family && option.setupHours > firstSetupHours + 1e-8) return 3;
    if (previous.setupKey === nextSetup.setupKey && option.setupHours < firstSetupHours - 1e-8) return 1;
  }
  return 2;
}
function scheduleStage(seed, master, process2, sources, operationsByKey, warnings, includeInterruptedCandidates = false) {
  const isPistonDownstream = seed.productionArea !== "cubuk-filtre" && (process2 === "drilling" || process2 === "deburring" || process2 === "gkm");
  const queueByResource = /* @__PURE__ */ new Map();
  const eligibleResources = /* @__PURE__ */ new Map();
  const usableResources = (source, parameter) => {
    let ids = eligibleResources.get(source.masterProduct);
    if (!ids) {
      ids = activeProcessResourceIds(parameter).filter((id) => {
        const resource = processResource(master, id);
        return resource?.active && resource.process === process2 && resource.defaultShifts > 0 && resourceSupportsProcessProduct(resource, source.masterProduct) && Number.isFinite(parameter.unitsPerShift[id]) && parameter.unitsPerShift[id] > 0;
      });
      eligibleResources.set(source.masterProduct, ids);
    }
    return ids;
  };
  const overrideCache = /* @__PURE__ */ new Map();
  const placementOverride = (batchId, product, allowInheritance = true) => {
    const key = JSON.stringify([batchId, product, allowInheritance]);
    if (!overrideCache.has(key)) overrideCache.set(key, processPlacementOverride(seed, batchId, product, process2, allowInheritance));
    return overrideCache.get(key);
  };
  const machineFreeTimes = /* @__PURE__ */ new Map();
  const machineFree = (item) => {
    let free = machineFreeTimes.get(item.source);
    if (free === void 0) {
      free = process2 === "drilling" || isPistonDownstream ? Math.min(...usableResources(item.source, item.parameter).map((id) => Math.max(
        processResource(master, id)?.availableStart ?? 0,
        ...seed.productionArea === "cubuk-filtre" ? [] : (seed.processCurrentJobs ?? []).filter((job) => job.resourceId === id && job.batchId !== item.source.id).map((job) => job.end)
      )), Number.POSITIVE_INFINITY) : 0;
      machineFreeTimes.set(item.source, free);
    }
    return free;
  };
  const strategy = master.planningStrategies?.[process2] ?? (process2 === "drilling" ? "campaign" : "earliest-ready");
  const candidates = sources.flatMap((source) => {
    if (!source.nextProcess) return [];
    const stages = productionProcessOrder(seed);
    if (seed.plannedThroughProcess !== void 0 && stages.indexOf(process2) > stages.indexOf(seed.plannedThroughProcess) && !seed.processCurrentJobs?.some((item) => item.batchId === source.id && item.process === process2)) return [];
    const parameter = source.masterProduct.processes.find((item) => item.process === process2);
    if (!parameter) return [];
    if (source.masterProduct.route && !source.masterProduct.route.includes(process2)) return [];
    const orderedRoute = productProcessRoute(source.masterProduct).filter((item) => item !== "turning").map((process3) => ({ process: process3 }));
    const routeIndex = orderedRoute.findIndex((item) => item.process === process2);
    const nextRouteIndex = orderedRoute.findIndex((item) => item.process === source.nextProcess);
    if (nextRouteIndex < 0) return [];
    if (routeIndex < nextRouteIndex) return [];
    const predecessorProcess = routeIndex > 0 ? orderedRoute[routeIndex - 1].process : "turning";
    const predecessor = operationsByKey.get(`${source.id}:${predecessorProcess}`);
    const firstRemaining = process2 === source.nextProcess;
    const interrupted = activeLotInterruptions(seed, source.lot).length > 0;
    const explicitPlacement = seed.processOperationOverrides?.some((item) => item.batchId === source.id && item.process === process2 && item.routeMode !== "automatic");
    const running = seed.processCurrentJobs?.some((item) => item.batchId === source.id && item.process === process2);
    if (seed.productionInterruptions?.some((item) => isProductionInterruption(item) && !item.completedAt && item.chargeId === source.id && item.process === source.nextProcess) && !firstRemaining) return [];
    if (interrupted && !running && !explicitPlacement && !(includeInterruptedCandidates && firstRemaining)) return [];
    if (!predecessor && !firstRemaining) {
      warnings.push({ code: "missing-parameter", product: source.product, batchId: source.id, message: `${source.product} \xB7 ${process2} i\xE7in \xF6nceki rota ad\u0131m\u0131 bulunamad\u0131.` });
      return [];
    }
    const effectiveWaitWorkdays = seed.productionArea === "cubuk-filtre" ? firstRemaining && source.source === "wip" ? 0 : parameter.waitWorkdaysBefore : firstRemaining && source.source === "wip" ? 0 : processWaitWorkdays(seed, predecessorProcess);
    const filterGap = seed.productionArea === "cubuk-filtre" ? parameter.finishGapMinutes : void 0;
    const rule = typeof filterGap === "number" && Number.isFinite(filterGap) && filterGap >= 0 ? { mode: "dynamic", minutes: filterGap } : flowRule(seed, source.masterProduct.family, predecessorProcess, process2);
    let legacyReadyAt;
    try {
      legacyReadyAt = applyProcessLeadStages(seed, firstRemaining ? source.source === "wip" ? source.releaseAt : addProcessWaitWorkdays(seed, predecessor?.end ?? source.releaseAt, effectiveWaitWorkdays) : addProcessWaitWorkdays(seed, predecessor.end, effectiveWaitWorkdays), firstRemaining && source.source === "wip" ? [] : parameter.leadStages);
    } catch (error) {
      warnings.push({ code: "invalid-capacity", product: source.product, batchId: source.id, message: error instanceof Error ? error.message : "Bekleme takvimi hesaplanamad\u0131." });
      return [];
    }
    const usesRule = rule && !(firstRemaining && source.source === "wip");
    const readyAt = usesRule ? rule.mode === "static" ? addDepartmentWorkMinutes(seed, predecessor?.end ?? source.releaseAt, rule.minutes) : parameter.leadStages?.length ? legacyReadyAt : predecessor?.start ?? source.releaseAt : legacyReadyAt;
    const storedOverride = placementOverride(source.id, source.product, !interrupted);
    const override = storedOverride?.routeMode === "automatic" && !storedOverride.parallelAllocations ? void 0 : storedOverride?.routeMode === "priority" ? { ...storedOverride, requestedStart: readyAt } : storedOverride;
    const currentJob = seed.processCurrentJobs?.find((item) => item.batchId === source.id && item.process === process2);
    const hours = (minutes) => String(Math.round(minutes / 60 * 100) / 100).replace(".", ",");
    const waitRuleLabel = currentJob ? "\xC7al\u0131\u015Fan i\u015F \xB7 kay\u0131tl\u0131 ba\u015Flang\u0131\xE7" : firstRemaining && source.source === "wip" ? "Kay\u0131tl\u0131 haz\u0131r olma (yar\u0131 mamul)" : usesRule ? rule.mode === "dynamic" ? `Biti\u015F fark\u0131 hedefi ${hours(rule.minutes)} takvim saati` : `${hours(rule.minutes)} \xE7al\u0131\u015Fma saati` : effectiveWaitWorkdays > 0 ? `${effectiveWaitWorkdays} i\u015F g\xFCn\xFC` : "Bekleme yok";
    return [{ source, parameter, predecessor, readyAt, override, currentJob, effectiveWaitWorkdays, waitRuleLabel, rule: usesRule ? rule : void 0 }];
  }).sort((left, right) => {
    if (Boolean(left.currentJob) !== Boolean(right.currentJob)) return left.currentJob ? -1 : 1;
    if (Boolean(left.override?.resumeAfterCurrent) !== Boolean(right.override?.resumeAfterCurrent)) return left.override?.resumeAfterCurrent ? -1 : 1;
    if (process2 === "drilling") {
      const difference = usableResources(left.source, left.parameter).length - usableResources(right.source, right.parameter).length;
      if (difference) return difference;
    }
    const leftScheduleAt = Math.max(left.readyAt, left.override?.requestedStart ?? left.readyAt, Number.isFinite(machineFree(left)) ? machineFree(left) : 0);
    const rightScheduleAt = Math.max(right.readyAt, right.override?.requestedStart ?? right.readyAt, Number.isFinite(machineFree(right)) ? machineFree(right) : 0);
    const leftOrder = left.override?.queueOrder ?? Number.MAX_SAFE_INTEGER;
    const rightOrder = right.override?.queueOrder ?? Number.MAX_SAFE_INTEGER;
    if (leftOrder !== rightOrder) return leftOrder - rightOrder;
    if (Math.abs(leftScheduleAt - rightScheduleAt) > 1e-8) return leftScheduleAt - rightScheduleAt;
    const rank = (source) => source === "wip" ? 0 : source === "current-turning" ? 1 : 2;
    if (!isPistonDownstream && left.source.source !== right.source.source) return rank(left.source.source) - rank(right.source.source);
    if (isPistonDownstream) {
      if (Boolean(left.override) !== Boolean(right.override)) return left.override ? -1 : 1;
      const leftDue = sourceDueSerial(seed, left.source) ?? Number.MAX_SAFE_INTEGER;
      const rightDue = sourceDueSerial(seed, right.source) ?? Number.MAX_SAFE_INTEGER;
      if (leftDue !== rightDue) return leftDue - rightDue;
      if (process2 === "drilling") {
        const feeds = (item) => productProcessRoute(item.source.masterProduct).includes("deburring") ? 0 : 1;
        if (feeds(left) !== feeds(right)) return feeds(left) - feeds(right);
      }
      if (left.source.source !== right.source.source) return rank(left.source.source) - rank(right.source.source);
    }
    if (strategy === "campaign") {
      const setupOrder = left.parameter.setupKey.localeCompare(right.parameter.setupKey, "tr", { numeric: true });
      if (setupOrder) return setupOrder;
      const productOrder = left.source.product.localeCompare(right.source.product, "tr", { numeric: true });
      if (productOrder) return productOrder;
    }
    return left.readyAt - right.readyAt || left.source.releaseAt - right.source.releaseAt || left.source.id.localeCompare(right.source.id);
  });
  const pinnedProducts = /* @__PURE__ */ new Map();
  for (const item of candidates) if (item.override && !item.currentJob) {
    const set = pinnedProducts.get(item.override.resourceId) ?? /* @__PURE__ */ new Set();
    set.add(item.source.product);
    pinnedProducts.set(item.override.resourceId, set);
  }
  const scheduled = [];
  const formResources = /* @__PURE__ */ new Map();
  if (seed.productionArea === "cubuk-filtre" && process2 === "form-grinding") for (const source of sources) {
    const step = source.lot?.completedSteps.find((item) => item.process === "form-grinding");
    if (step && !formResources.has(sourceChargeKey(source))) formResources.set(sourceChargeKey(source), step.resourceId);
  }
  const pending = [...candidates];
  while (pending.length) {
    let index = 0;
    const first = pending[0];
    if (seed.productionArea === "cubuk-filtre" && process2 === "gtm" && !first.currentJob && !first.override) {
      const freeAt = Math.min(...usableResources(first.source, first.parameter).map((id) => Math.max(first.readyAt, queueByResource.get(id)?.tail ?? first.readyAt, processResource(master, id)?.availableStart ?? 0)));
      const activeKeys = new Set(scheduled.filter((operation2) => operation2.start <= freeAt && operation2.end > freeAt).map((operation2) => `${operation2.product}:${operation2.sharedCharge?.id ?? (operation2.workOrder.trim() || operation2.batchId)}`));
      if (activeKeys.has(sourceChargeKey(first.source))) {
        const different = pending.findIndex((item2) => !item2.currentJob && !item2.override && item2.readyAt <= freeAt && !activeKeys.has(sourceChargeKey(item2.source)) && usableResources(item2.source, item2.parameter).some((id) => Math.max(queueByResource.get(id)?.tail ?? item2.readyAt, processResource(master, id)?.availableStart ?? 0) <= freeAt));
        if (different >= 0) index = different;
      }
    }
    if (isPistonDownstream && !first.currentJob && !first.override) {
      const firstUsable = usableResources(first.source, first.parameter);
      const firstCount = firstUsable.length;
      if (firstCount > 0) {
        const freeAt = Math.min(...firstUsable.map((id) => Math.max(first.readyAt, queueByResource.get(id)?.tail ?? first.readyAt, processResource(master, id)?.availableStart ?? 0)));
        const readySetupRank = (candidate) => {
          const setup = { product: candidate.source.product, family: candidate.source.masterProduct.family, setupKey: candidate.parameter.setupKey };
          const firstSetupHours = calculateDownstreamSetup(process2, void 0, setup, seed.flowSettings).hours;
          let best = 4;
          for (const id of usableResources(candidate.source, candidate.parameter)) {
            const tail = Math.max(queueByResource.get(id)?.tail ?? 0, processResource(master, id)?.availableStart ?? 0);
            if (tail > freeAt + 1e-8) continue;
            const queue = queueByResource.get(id);
            const hours = calculateDownstreamSetup(process2, queue, setup, seed.flowSettings).hours;
            const rank = downstreamSetupRank(process2, { gapIndex: -1, setupHours: hours }, queue, setup, pinnedProducts.get(id), firstSetupHours);
            if (rank < best) best = rank;
          }
          return best;
        };
        const readyIndices = [];
        for (let i = 0; i < pending.length; i += 1) {
          const candidate = pending[i];
          if (candidate.currentJob || candidate.override) break;
          if (process2 === "drilling" && usableResources(candidate.source, candidate.parameter).length !== firstCount) break;
          if (candidate.readyAt <= freeAt + 1e-8) readyIndices.push(i);
        }
        if (readyIndices.length > 1) {
          readyIndices.sort((a, b) => {
            const left = pending[a], right = pending[b];
            const leftDue = sourceDueSerial(seed, left.source) ?? Number.MAX_SAFE_INTEGER;
            const rightDue = sourceDueSerial(seed, right.source) ?? Number.MAX_SAFE_INTEGER;
            if (leftDue !== rightDue) return leftDue - rightDue;
            if (leftDue < Number.MAX_SAFE_INTEGER || strategy === "campaign") {
              const setupDiff = readySetupRank(left) - readySetupRank(right);
              if (setupDiff) return setupDiff;
            }
            return a - b;
          });
          index = readyIndices[0];
        }
      }
    }
    const [item] = pending.splice(index, 1);
    const { source, parameter, predecessor, readyAt, override, currentJob, effectiveWaitWorkdays, waitRuleLabel, rule } = item;
    const nextSetup = { product: source.product, family: source.masterProduct.family, setupKey: parameter.setupKey };
    const activeResources = activeProcessResourceIds(parameter);
    const consolidatedResource = process2 === "milling" ? sourceSharedCharge(source)?.consolidated?.milling : void 0;
    const sameFormResource = seed.productionArea === "cubuk-filtre" && process2 === "form-grinding" ? formResources.get(sourceChargeKey(source)) : void 0;
    const resourceCandidates = currentJob ? [currentJob.resourceId] : (override && !override.parallelAllocations ? activeResources.filter((id) => id === override.resourceId) : activeResources).filter((id) => (!sameFormResource || id === sameFormResource) && (!consolidatedResource || id === consolidatedResource));
    const evaluated = resourceCandidates.flatMap((resourceId, priority) => {
      const resource = processResource(master, resourceId);
      const unitsPerShift = parameter.unitsPerShift[resourceId];
      if (!resource || resource.process !== process2 || !resource.active || resource.defaultShifts <= 0 || !resourceSupportsProcessProduct(resource, source.masterProduct) || !Number.isFinite(unitsPerShift) || unitsPerShift <= 0) return [];
      if (!currentJob && seed.productionArea === "cubuk-filtre" && !Number.isFinite(parameter.setupMinutesByResource?.[resourceId])) return [];
      const queue = queueByResource.get(resourceId);
      const setup = parameter.setupMinutesByResource ? { hours: ((queue?.product === source.product ? 0 : parameter.setupMinutesByResource[resourceId]) + (parameter.handlingMinutes ?? 0)) / 60, label: "Operasyon rotas\u0131 haz\u0131rl\u0131\u011F\u0131" } : calculateDownstreamSetup(process2, queue, nextSetup, seed.productionArea === "cubuk-filtre" ? void 0 : seed.flowSettings);
      if (!Number.isFinite(setup.hours)) return [];
      const runHours = currentJob ? Math.max(0, (currentJob.end - currentJob.start) * 24 - currentJob.setupHours) : source.quantity / unitsPerShift * getSetupSettings(seed).shiftHours;
      const requestedStart = Math.max(readyAt, queue?.tail ?? readyAt, override?.requestedStart ?? readyAt, currentJob ? readyAt : resource.availableStart ?? readyAt);
      const timeline = currentJob ? { start: currentJob.start, end: currentJob.end } : rule?.mode === "dynamic" && predecessor ? dynamicFlowTiming(seed, processCalendarSeed(seed, resource.id), resource, predecessor, requestedStart, setup.hours, runHours, source.quantity, rule.minutes) : addMachineCapacityHours(
        processCalendarSeed(seed, resource.id),
        { id: resource.id, shiftFactor: resource.defaultShifts, finishOffset: 0 },
        requestedStart,
        setup.hours + runHours
      );
      const options = [{ resource, unitsPerShift, setupHours: setup.hours, protectedSetupHoursAfter: 0, runHours, priority, gapIndex: -1, previousOperation: void 0, ...timeline }].filter((option) => currentJob || seed.productionArea === "cubuk-filtre" && process2 === "milling" && (!override || override.parallelAllocations) || !resource.planEnd || option.end <= Math.floor(resource.planEnd) + 1 + 1e-8);
      if (!currentJob && process2 === "drilling") {
        const reservations = scheduled.filter((operation2) => operation2.resourceId === resource.id).sort((left, right) => left.start - right.start || left.end - right.end || left.id.localeCompare(right.id));
        const currentEnd = Math.max(0, ...reservations.filter((operation2) => operation2.current).map((operation2) => operation2.end));
        const gaps = reservations.map((nextReservation, index2) => ({
          nextReservation,
          previousOperation: reservations[index2 - 1],
          cursor: Math.max(reservations[index2 - 1]?.end ?? 0, currentEnd),
          tail: reservations[index2 - 1] ? setupSourceForOperation(reservations[index2 - 1]) : void 0
        }));
        const calendarSeed = processCalendarSeed(seed, resource.id);
        for (const [gapIndex, gap] of gaps.entries()) {
          const nextOverride = placementOverride(gap.nextReservation.batchId, gap.nextReservation.product);
          if (override?.queueOrder !== void 0 && nextOverride?.queueOrder !== void 0 && override.queueOrder > nextOverride.queueOrder) continue;
          const incomingSetup = calculateDownstreamSetup(process2, gap.tail, nextSetup, seed.productionArea === "cubuk-filtre" ? void 0 : seed.flowSettings);
          const gapStart = Math.max(readyAt, gap.cursor, override?.requestedStart ?? readyAt, resource.availableStart ?? readyAt);
          if (gapStart > gap.nextReservation.start + 2e-6 + 1e-8) continue;
          const gapTimeline = rule?.mode === "dynamic" && predecessor ? dynamicFlowTiming(seed, calendarSeed, resource, predecessor, gapStart, incomingSetup.hours, runHours, source.quantity, rule.minutes) : addMachineCapacityHours(
            calendarSeed,
            { id: resource.id, shiftFactor: resource.defaultShifts, finishOffset: 0 },
            gapStart,
            incomingSetup.hours + runHours
          );
          if (resource.planEnd && gapTimeline.end > Math.floor(resource.planEnd) + 1 + 1e-8) continue;
          const requiredReservedSetup = calculateDownstreamSetup(process2, nextSetup, setupSourceForOperation(gap.nextReservation), seed.productionArea === "cubuk-filtre" ? void 0 : seed.flowSettings).hours;
          const protectedSetupHoursAfter = Math.max(0, requiredReservedSetup - gap.nextReservation.setupHours);
          const restored = addMachineCapacityHours(
            calendarSeed,
            { id: resource.id, shiftFactor: resource.defaultShifts, finishOffset: 0 },
            gapTimeline.end,
            protectedSetupHoursAfter
          );
          if (restored.end > gap.nextReservation.start + 1e-8) continue;
          options.push({
            resource,
            unitsPerShift,
            setupHours: incomingSetup.hours,
            protectedSetupHoursAfter,
            runHours,
            priority,
            gapIndex,
            previousOperation: gap.previousOperation,
            ...gapTimeline
          });
        }
      }
      return options;
    }).sort((left, right) => left.end - right.end || left.priority - right.priority || left.resource.id.localeCompare(right.resource.id));
    let parallel = seed.productionArea === "cubuk-filtre" && process2 === "milling" && !currentJob && !override && !consolidatedResource && evaluated.length > 1 ? allocateSharedQuantity(source.quantity, evaluated.map((option) => {
      const start = Math.max(readyAt, predecessor?.end ?? readyAt, queueByResource.get(option.resource.id)?.tail ?? readyAt, option.resource.availableStart ?? readyAt);
      const end = option.resource.planEnd ? Math.floor(option.resource.planEnd) + 1 - 1e-6 : start + 366;
      const hoursPerPiece = getSetupSettings(seed).shiftHours / option.unitsPerShift;
      const calendar = processCalendarSeed(seed, option.resource.id);
      const machine = { id: option.resource.id, shiftFactor: option.resource.defaultShifts, finishOffset: 0 };
      return {
        resource: option,
        start,
        end,
        capacity: (until) => Math.max(0, machineCapacityHoursBetween(calendar, machine, start, until) - option.setupHours) / hoursPerPiece,
        timing: (quantity) => addMachineCapacityHours(calendar, machine, start, option.setupHours + quantity * hoursPerPiece)
      };
    })) : void 0;
    if (seed.productionArea === "cubuk-filtre" && process2 === "milling" && !currentJob && override?.parallelAllocations) {
      const parts = override.parallelAllocations;
      const tails = /* @__PURE__ */ new Map();
      const placed = parts.flatMap((part) => {
        if (!Number.isSafeInteger(part.quantity) || part.quantity <= 0 || !Number.isFinite(part.requestedStart)) return [];
        const automatic = override.routeMode === "automatic";
        const options = evaluated.filter((item2) => automatic || item2.resource.id === part.resourceId).flatMap((option) => {
          const resourceId = option.resource.id;
          const start = Math.max(readyAt, predecessor?.end ?? readyAt, automatic ? readyAt : part.requestedStart, queueByResource.get(resourceId)?.tail ?? readyAt, tails.get(resourceId) ?? 0, option.resource.availableStart ?? 0);
          const timing = addMachineCapacityHours(
            processCalendarSeed(seed, resourceId),
            { id: resourceId, shiftFactor: option.resource.defaultShifts, finishOffset: 0 },
            start,
            option.setupHours + part.quantity / option.unitsPerShift * getSetupSettings(seed).shiftHours
          );
          if (option.resource.planEnd && timing.end > Math.floor(option.resource.planEnd) + 1 + 1e-8) return [];
          if (override.routeMode === "keep" && (Math.abs(timing.start - part.requestedStart) > 1e-6 || part.preservedEnd !== void 0 && Math.abs(timing.end - part.preservedEnd) > 1e-6)) return [];
          return [{ id: part.id, resource: option, quantity: part.quantity, ...timing }];
        }).sort((a, b) => a.end - b.end || a.resource.resource.id.localeCompare(b.resource.resource.id));
        const selected = options[0];
        if (!selected) return [];
        tails.set(selected.resource.resource.id, selected.end);
        return [selected];
      });
      if (!parts.length || new Set(parts.map((part) => part.id)).size !== parts.length || placed.length !== parts.length || placed.reduce((sum, part) => sum + part.quantity, 0) !== source.quantity) {
        warnings.push({ code: "placement-conflict", product: source.product, batchId: source.id, message: `${source.product} \xB7 Freze ortak \u015Farj paylar\u0131 miktar veya kapasite ile uyu\u015Fmuyor. \xDCretim ak\u0131\u015F\u0131n\u0131 d\xFCzenle ile yeniden inceleyin.` });
        continue;
      }
      parallel = placed;
    }
    const earliestFinish = evaluated.find((option) => currentJob || !option.resource.planEnd || option.end <= Math.floor(option.resource.planEnd) + 1 + 1e-8);
    const preferred = process2 === "drilling" && !currentJob && !override && earliestFinish ? evaluated.filter((option) => option.start <= earliestFinish.start + 1e-8).sort((left, right) => left.priority - right.priority || left.end - right.end || left.resource.id.localeCompare(right.resource.id))[0] : earliestFinish;
    const due = sourceDueSerial(seed, source);
    let stageChoice = preferred;
    if (isPistonDownstream && !currentJob && !override && due !== void 0 && evaluated.length) {
      const firstSetupHours = calculateDownstreamSetup(process2, void 0, nextSetup, seed.flowSettings).hours;
      const seenResources = /* @__PURE__ */ new Set();
      const perResource = evaluated.filter((option) => {
        if (option.resource.planEnd && option.end > Math.floor(option.resource.planEnd) + 1 + 1e-8) return false;
        if (seenResources.has(option.resource.id)) return false;
        seenResources.add(option.resource.id);
        return true;
      }).map((option) => ({
        option,
        setupRank: downstreamSetupRank(process2, option, queueByResource.get(option.resource.id), nextSetup, pinnedProducts.get(option.resource.id), firstSetupHours),
        projectedReady: estimateDeliveryReadyFromStage(seed, master, source, { ...option, process: process2, resourceId: option.resource.id })
      }));
      if (perResource.length) {
        const onTime = perResource.filter((item2) => Math.floor(item2.projectedReady) <= Math.floor(due));
        let pool = onTime;
        if (!pool.length) {
          const earliestEnd = Math.min(...perResource.map((item2) => item2.option.end));
          pool = perResource.filter((item2) => item2.option.end <= earliestEnd + 1e-6);
        }
        const bestRank = Math.min(...pool.map((item2) => item2.setupRank));
        const ranked = pool.filter((item2) => item2.setupRank === bestRank);
        if (process2 === "drilling") {
          const earliestStart = Math.min(...ranked.map((item2) => item2.option.start));
          const equalStart = ranked.filter((item2) => item2.option.start <= earliestStart + 1e-8);
          stageChoice = (equalStart.length ? equalStart : ranked).sort((left, right) => left.option.setupHours - right.option.setupHours || left.option.priority - right.option.priority || left.option.end - right.option.end || left.option.resource.id.localeCompare(right.option.resource.id))[0].option;
        } else {
          stageChoice = ranked.sort((left, right) => left.option.setupHours - right.option.setupHours || left.option.end - right.option.end || left.option.priority - right.option.priority || left.option.resource.id.localeCompare(right.option.resource.id))[0].option;
        }
      }
    }
    const chosen = parallel && (parallel.length > 1 || override?.parallelAllocations) ? parallel[0].resource : stageChoice;
    if (!chosen) {
      warnings.push({ code: "missing-resource", product: source.product, batchId: source.id, message: `${source.product} \xB7 ${process2} i\xE7in kullan\u0131labilir i\u015F merkezi veya vardiya kapasitesi yok.` });
      continue;
    }
    const operation = {
      ...sourceSharedCharge(source) ? { sharedCharge: sourceSharedCharge(source) } : {},
      flowTargetEnd: "targetEnd" in chosen ? chosen.targetEnd : void 0,
      flowReason: "reason" in chosen ? chosen.reason : void 0,
      id: `${source.id}:${process2}`,
      batchId: source.id,
      product: source.product,
      family: source.masterProduct.family,
      quantity: currentJob?.remainingQuantity ?? source.quantity,
      process: process2,
      sequence: parameter.sequence,
      resourceId: chosen.resource.id,
      resourceName: chosen.resource.name,
      setupKey: parameter.setupKey,
      unitsPerShift: chosen.unitsPerShift,
      setupHours: currentJob?.setupHours ?? chosen.setupHours,
      protectedSetupHoursAfter: chosen.protectedSetupHoursAfter || void 0,
      runHours: chosen.runHours,
      waitWorkdaysBefore: effectiveWaitWorkdays,
      waitRuleLabel,
      readyAt,
      start: chosen.start,
      end: chosen.end,
      predecessorOperationId: predecessor?.id,
      requiresInterruptionConfirmation: activeLotInterruptions(seed, source.lot).length > 0,
      manualCandidate: activeLotInterruptions(seed, source.lot).length > 0 && !override && !currentJob,
      source: source.source,
      actual: false,
      current: Boolean(currentJob),
      workOrder: currentJob?.workOrder ?? source.workOrder,
      wipLotId: source.lot?.id,
      manualOverride: Boolean(override)
    };
    if (operation.flowReason) warnings.push({ code: "flow-target", product: source.product, batchId: source.id, message: `${source.product} \xB7 ${processLabelForError(process2)}: ${operation.flowReason}` });
    if (parallel && (parallel.length > 1 || override?.parallelAllocations)) {
      const sharedCharge = sourceSharedCharge(source) ?? { id: source.id, quantity: source.quantity };
      const portions = parallel.map((part) => ({
        ...operation,
        sharedCharge,
        parallelPortion: true,
        id: part.id ?? `${source.id}:${process2}:${part.resource.resource.id}`,
        resourceId: part.resource.resource.id,
        resourceName: part.resource.resource.name,
        quantity: part.quantity,
        start: part.start,
        end: part.end,
        unitsPerShift: part.resource.unitsPerShift,
        setupHours: part.resource.setupHours,
        runHours: part.quantity / part.resource.unitsPerShift * getSetupSettings(seed).shiftHours,
        flowTargetEnd: void 0,
        flowReason: void 0,
        readyAt: Math.max(readyAt, predecessor?.end ?? readyAt)
      }));
      for (const portion of portions) {
        scheduled.push(portion);
        queueByResource.set(portion.resourceId, { tail: portion.end, ...nextSetup });
      }
      operationsByKey.set(`${source.id}:${process2}`, {
        ...operation,
        resourceId: "",
        quantity: source.quantity,
        start: Math.min(...portions.map((part) => part.start)),
        end: Math.max(...portions.map((part) => part.end))
      });
      continue;
    }
    scheduled.push(operation);
    if (process2 === "form-grinding" && seed.productionArea === "cubuk-filtre" && !formResources.has(sourceChargeKey(source))) formResources.set(sourceChargeKey(source), operation.resourceId);
    if (override?.routeMode === "keep" && !currentJob && (Math.abs(operation.start - (override.preservedStart ?? override.requestedStart)) > 1e-8 || Math.abs(operation.end - (override.preservedEnd ?? operation.end)) > 1e-8)) warnings.push({ code: "placement-conflict", product: source.product, batchId: source.id, message: `${source.workOrder || source.product} \xB7 ${processLabelForError(process2)} mevcut yerle\u015Fimi de\u011Fi\u015Fen girdilerle korunam\u0131yor. \xDCretim ak\u0131\u015F\u0131n\u0131 d\xFCzenle ile yeniden inceleyin.` });
    operationsByKey.set(`${source.id}:${process2}`, operation);
    if (chosen.gapIndex >= 0) {
      if (chosen.previousOperation) chosen.previousOperation.protectedSetupHoursAfter = void 0;
    } else {
      queueByResource.set(chosen.resource.id, { tail: operation.end, ...nextSetup });
    }
  }
  return scheduled;
}
function assertProcessPlacementResource(seed, operation, resourceId) {
  const master = seed.processMasterData;
  const product = master ? processMasterDataForProduct(master, operation.product) : void 0;
  const resource = master?.resources.find((item) => item.id === resourceId);
  const parameter = product?.processes.find((item) => item.process === operation.process);
  if (!resource || resource.process !== operation.process) throw new Error(`${resourceId}, ${processLabelForError(operation.process)} i\xE7in ge\xE7erli bir i\u015F merkezi de\u011Fil.`);
  if (!resource.active) throw new Error(`${resourceId} pasif; \xF6nce i\u015F merkezini planlamaya a\xE7\u0131n.`);
  if (resource.defaultShifts <= 0) throw new Error(`${resourceId} i\xE7in vardiya 0; kapasite a\xE7\u0131lmadan i\u015F ta\u015F\u0131namaz.`);
  if (!product || !resourceSupportsProcessProduct(resource, product)) throw new Error(`${resourceId}, ${operation.product} \xFCr\xFCn grubunu \xE7al\u0131\u015Ft\u0131ramaz.`);
  if (!parameter || !activeProcessResourceIds(parameter).includes(resourceId) || !(parameter.unitsPerShift[resourceId] > 0)) throw new Error(`${operation.product} i\xE7in ${resourceId} aktif i\u015F merkezi ve vardiya h\u0131z\u0131 tan\u0131ml\u0131 de\u011Fil.`);
  return resource;
}
function processPlacementSignature(preview) {
  return JSON.stringify([preview.requestedStart, preview.operation.id, preview.plan.operations, preview.plan.jobs.map((job) => [job.batchId, job.deliveryReadyAt]), preview.affectedOperations]);
}
function cloneSeedOverrides(seed) {
  return {
    ...seed,
    processOperationOverrides: (seed.processOperationOverrides ?? []).map((override) => ({
      ...override,
      ...override.parallelAllocations ? { parallelAllocations: override.parallelAllocations.map((part) => ({ ...part })) } : {}
    }))
  };
}
function preserveParallelAllocations(seed, operations) {
  const groups = /* @__PURE__ */ new Map();
  for (const operation of operations) if (operation.parallelPortion && !operation.current && !operation.actual)
    groups.set(operation.batchId, [...groups.get(operation.batchId) ?? [], operation]);
  for (const [batchId, parts] of groups) {
    const previous = seed.processOperationOverrides?.find((item) => item.batchId === batchId && item.process === "milling");
    if (previous?.parallelAllocations) continue;
    seed.processOperationOverrides = [
      ...(seed.processOperationOverrides ?? []).filter((item) => item.batchId !== batchId || item.process !== "milling"),
      {
        ...previous,
        batchId,
        process: "milling",
        resourceId: parts[0].resourceId,
        requestedStart: Math.min(...parts.map((part) => part.start)),
        updatedAt: (/* @__PURE__ */ new Date()).toISOString(),
        parallelAllocations: parts.map((part) => ({ id: part.id, resourceId: part.resourceId, quantity: part.quantity, requestedStart: part.start, preservedEnd: part.end }))
      }
    ];
  }
}
function previewParallelMillingPlacement(seed, result, baseline, operation, resourceId, requestedStart, stageOnly = false) {
  const next = cloneSeedOverrides(seed);
  preserveParallelAllocations(next, operation.parallelPortion ? baseline.operations : [...baseline.operations, { ...operation, parallelPortion: true }]);
  const override = next.processOperationOverrides.find((item) => item.batchId === operation.batchId && item.process === "milling");
  const portion = override.parallelAllocations.find((item) => item.id === operation.id);
  portion.resourceId = resourceId;
  portion.requestedStart = requestedStart;
  override.routeMode = "manual";
  const plan = stageOnly ? buildSingleStagePlanFromBaseline(next, result, baseline, "milling") : buildDownstreamProcessPlanFromStage(next, result, baseline, "milling");
  const conflict = plan.warnings.find((item) => item.code === "placement-conflict");
  if (conflict) throw new Error(conflict.message);
  const moved = plan.operations.find((item) => item.id === operation.id);
  if (!moved || moved.resourceId !== resourceId || moved.start < requestedStart - 1e-8) throw new Error("Freze pay\u0131 istenen kayna\u011Fa yerle\u015Ftirilemedi.");
  if (stageOnly) {
    return { seed: next, plan, operation: moved, requestedStart, insertionIndex: 0, adjustments: [], affectedOperations: [], deliveryWarnings: [] };
  }
  const affectedOperations = [];
  for (const before of baseline.operations) {
    const after = plan.operations.find((item) => item.id === before.id);
    if (!after || after.quantity !== before.quantity || after.product !== before.product) throw new Error("Rota d\xFCzenlemesi \u015Farj pay\u0131n\u0131 veya miktar\u0131n\u0131 koruyamad\u0131.");
    const changed = after.resourceId !== before.resourceId || after.start !== before.start || after.end !== before.end;
    if (changed && (before.actual || before.current)) throw new Error("\xC7al\u0131\u015Fan ve tamamlanan i\u015Fler de\u011Fi\u015Ftirilemez.");
    if (changed && before.id !== operation.id) affectedOperations.push({ before, after });
  }
  const order = plan.operations.filter((item) => item.process === "milling" && item.resourceId === resourceId && !item.actual && !item.current).sort((a, b) => a.start - b.start || a.id.localeCompare(b.id));
  return {
    seed: next,
    plan,
    operation: moved,
    requestedStart,
    insertionIndex: order.findIndex((item) => item.id === moved.id),
    affectedOperations,
    adjustments: ["Yaln\u0131z se\xE7ili Freze pay\u0131 ta\u015F\u0131nd\u0131. Ortak \u015Farj\u0131n di\u011Fer paylar\u0131 ve toplam adedi korundu."],
    deliveryWarnings: placementDeliveryWarnings(seed, result, baseline, plan)
  };
}
function processPlacementBaseline(seed, result, operationId) {
  return placementBaselineWithCandidate(seed, result, operationId, buildDownstreamProcessPlan(seed, result));
}
function placementBaselineWithCandidate(seed, result, operationId, baseline) {
  if (baseline.operations.some((item) => item.id === operationId)) return baseline;
  const candidate = buildDownstreamProcessPlan(seed, result, true).operations.find((item) => item.id === operationId && item.manualCandidate);
  if (candidate) {
    return { ...baseline, operations: [...baseline.operations, candidate], jobs: baseline.jobs.map((job) => job.batchId === candidate.batchId ? { ...job, operations: [...job.operations, candidate] } : job) };
  }
  return baseline;
}
function previewProcessOperationReschedule(seed, result, operationId, resourceId, requestedStart, existingBaseline) {
  const baseline = existingBaseline && stagePlanContexts.has(existingBaseline) ? placementBaselineWithCandidate(seed, result, operationId, existingBaseline) : processPlacementBaseline(seed, result, operationId);
  return previewProcessOperationRescheduleWithBaseline(seed, result, operationId, resourceId, requestedStart, baseline);
}
function previewProcessOperationRescheduleWithBaseline(seed, result, operationId, resourceId, requestedStart, baseline, individual = false, stageOnly = false) {
  const operation = baseline.operations.find((item) => item.id === operationId);
  if (!operation || operation.actual || operation.current || operation.process === "turning") throw new Error("Yaln\u0131zca kuyruktaki downstream operasyonlar\u0131 ta\u015F\u0131nabilir; \xE7al\u0131\u015Fan ve tamamlanan i\u015Fler sabittir.");
  if (!Number.isFinite(requestedStart) || requestedStart <= 0) throw new Error("Ge\xE7erli bir yeni ba\u015Flang\u0131\xE7 zaman\u0131 se\xE7in.");
  if (!individual && seed.productionArea === "cubuk-filtre" && operation.sharedCharge) {
    const portions = baseline.operations.filter((item) => item.sharedCharge?.id === operation.sharedCharge.id && item.process === operation.process && !item.actual);
    if (portions.length > 1 && new Set(portions.map((item) => item.resourceId)).size > 1)
      return previewLinkedProcessPlacement(seed, result, baseline, operation, portions, resourceId, requestedStart);
  }
  if (requestedStart < operation.readyAt - 1e-8) {
    const predecessor = baseline.operations.find((item) => item.id === operation.predecessorOperationId);
    throw new Error(`\xD6nceki proses tamamlanmad\u0131: ${operation.product} i\xE7in ${predecessor ? processLabelForError(predecessor.process) : "\xF6nceki proses"} ve zorunlu bekleme nedeniyle en erken ba\u015Flang\u0131\xE7 ${processStartDate(operation.readyAt)}. \u0130stenen: ${processStartDate(requestedStart)}.`);
  }
  const resource = assertProcessPlacementResource(seed, operation, resourceId);
  if (resource.planEnd && requestedStart >= Math.floor(resource.planEnd) + 1) throw new Error(`${resourceId} plan penceresi ${processStartDate(resource.planEnd)} tarihinde bitiyor.`);
  if (operation.parallelPortion || operation.process === "milling" && baseline.operations.some((item) => item.parallelPortion)) return previewParallelMillingPlacement(seed, result, baseline, operation, resourceId, requestedStart, stageOnly);
  return previewQueuedProcessPlacement(seed, result, baseline, [operation], resource, requestedStart, stageOnly);
}
function previewQueuedProcessPlacement(seed, result, baseline, selected, resource, requestedStart, stageOnly = false) {
  const [operation] = selected;
  const resourceId = resource.id;
  const selectedIds = new Set(selected.map((item) => item.id));
  const process2 = operation.process;
  if (process2 === "turning") throw new Error("Bu i\u015Flem yaln\u0131zca Torna sonras\u0131ndaki prosesler i\xE7in kullan\u0131labilir.");
  const queues = /* @__PURE__ */ new Map();
  for (const item of baseline.operations.filter((item2) => item2.process === process2 && !item2.actual && !item2.current && !selectedIds.has(item2.id))) {
    queues.set(item.resourceId, [...queues.get(item.resourceId) ?? [], item]);
  }
  for (const queue of queues.values()) queue.sort((a, b) => a.start - b.start || a.id.localeCompare(b.id));
  const destination = queues.get(resourceId) ?? [];
  const nextIndex = destination.findIndex((item) => item.end > requestedStart + 1e-8);
  const insertionIndex = nextIndex < 0 ? destination.length : nextIndex;
  destination.splice(insertionIndex, 0, ...selected);
  queues.set(resourceId, destination);
  const nextSeed = stageOnly ? cloneSeedOverrides(seed) : JSON.parse(JSON.stringify(seed));
  const queuedIds = new Set([...queues.values()].flat().map((item) => item.batchId));
  const updatedAt = (/* @__PURE__ */ new Date()).toISOString();
  nextSeed.processOperationOverrides = [
    ...(seed.processOperationOverrides ?? []).filter((item) => item.process !== process2 || !queuedIds.has(item.batchId)),
    ...[...queues].flatMap(([queueResourceId, queue]) => {
      let cursor = 0;
      return queue.map((item, queueOrder) => {
        const moving = selectedIds.has(item.id);
        const anchor = item.id === operation.id ? requestedStart : Math.max(moving ? item.readyAt : item.start, cursor);
        cursor = anchor + 1 / 86400;
        const previous = seed.processOperationOverrides?.find((value) => value.batchId === item.batchId && value.process === process2);
        const currentMachine = item.source === "current-turning" ? seed.machines.find((machine) => `current:${machine.id}` === item.batchId) : void 0;
        return { ...previous, ...moving ? { routeMode: "manual", resumeAfterCurrent: false, preservedStart: void 0, preservedEnd: void 0 } : {}, batchId: item.batchId, process: process2, resourceId: queueResourceId, requestedStart: anchor, updatedAt, queueOrder, sourceProduct: item.product, sourceCurrentJobKey: currentMachine ? currentJobRouteIdentity(currentMachine) : void 0 };
      });
    })
  ];
  const plan = stageOnly ? buildSingleStagePlanFromBaseline(nextSeed, result, baseline, process2) : buildDownstreamProcessPlanFromStage(nextSeed, result, baseline, process2);
  if (process2 === "drilling") {
    const resourceCount = (product) => {
      const masterProduct = processMasterDataForProduct(seed.processMasterData, product);
      const parameter = masterProduct?.processes.find((item) => item.process === "drilling");
      return !masterProduct || !parameter ? 0 : activeProcessResourceIds(parameter).filter((id) => {
        const candidate = processResource(seed.processMasterData, id);
        return candidate?.active && candidate.defaultShifts > 0 && candidate.process === "drilling" && resourceSupportsProcessProduct(candidate, masterProduct) && Number.isFinite(parameter.unitsPerShift[id]) && parameter.unitsPerShift[id] > 0;
      }).length;
    };
    if (selected.some((item) => resourceCount(item.product) > 1)) for (const reserved of baseline.operations.filter((item) => item.process === process2 && item.resourceId === resourceId && !item.actual && !item.current && !selectedIds.has(item.id) && resourceCount(item.product) === 1)) {
      const after = plan.operations.find((item) => item.id === reserved.id);
      if (!after || after.start > reserved.start + 1e-8 || after.end > reserved.end + 1e-8)
        throw new Error(`${resourceId} kaynak rezervi ve setup d\xF6n\xFC\u015F s\xFCresi istenen s\u0131raya izin vermiyor. Rezervasyonu geciktirmeyen bir bo\u015Fluk veya uygun ba\u015Fka bir istasyon se\xE7in.`);
    }
  }
  const moved = plan.operations.find((item) => item.id === operation.id);
  const placementConflict = plan.warnings.find((warning) => warning.code === "placement-conflict");
  if (placementConflict) throw new Error(placementConflict.message);
  const checkedBaseline = stageOnly ? baseline.operations.filter((item) => item.process === process2) : baseline.operations;
  for (const before of checkedBaseline) {
    const after = plan.operations.find((item) => item.id === before.id);
    if (!after) {
      const limit = seed.processMasterData?.resources.find((item) => item.id === (selectedIds.has(before.id) ? resourceId : before.resourceId))?.planEnd;
      throw new Error(`${before.product} \xB7 ${processLabelForError(before.process)} ad\u0131m\u0131 kapasiteye s\u0131\u011Fm\u0131yor${limit ? `; plan penceresi ${processStartDate(limit)} tarihinde bitiyor` : "; i\u015F merkezi kapasitesini ve rota parametrelerini kontrol edin"}. Ta\u015F\u0131ma uygulanmad\u0131.`);
    }
    if ((before.current || before.actual) && (before.start !== after.start || before.end !== after.end || before.resourceId !== after.resourceId)) throw new Error("Ta\u015F\u0131ma \xE7al\u0131\u015Fan veya tamamlanan bir i\u015Fi de\u011Fi\u015Ftirece\u011Fi i\xE7in uygulanamad\u0131.");
    if (before.process === process2 && !selectedIds.has(before.id) && before.resourceId !== after.resourceId) throw new Error(`${before.product} i\xE7in mevcut i\u015F merkezi korunamad\u0131. Ta\u015F\u0131ma uygulanmad\u0131.`);
  }
  if (!moved || moved.resourceId !== resourceId || moved.start < requestedStart - 1e-8) throw new Error("Se\xE7ilen yerle\u015Fim rota ve kapasite kurallar\u0131yla olu\u015Fturulamad\u0131.");
  const actualOrder = plan.operations.filter((item) => item.process === process2 && item.resourceId === resourceId && !item.actual && !item.current).sort((a, b) => a.start - b.start || a.id.localeCompare(b.id));
  if (actualOrder.length !== destination.length || actualOrder.some((item, index) => item.id !== destination[index]?.id)) throw new Error(`${resourceId} kaynak rezervi ve setup d\xF6n\xFC\u015F s\xFCresi istenen s\u0131raya izin vermiyor. Haz\u0131r olma ve kapasite kurallar\u0131na uyan bir bo\u015Fluk veya uygun ba\u015Fka bir istasyon se\xE7in.`);
  if (stageOnly) {
    return { seed: nextSeed, plan, operation: moved, requestedStart, insertionIndex, adjustments: [], affectedOperations: [], deliveryWarnings: [] };
  }
  const adjustments = [];
  if (moved.start > requestedStart + 1e-8) {
    if ((resource.availableStart ?? 0) > requestedStart) adjustments.push(`${resourceId} en erken ${processStartDate(resource.availableStart)} tarihinde kullan\u0131labilir.`);
    const blocking = plan.operations.filter((item) => item.resourceId === resourceId && item.id !== moved.id && item.end > requestedStart && item.end <= moved.start + 1e-8).sort((a, b) => b.end - a.end)[0];
    if (blocking) adjustments.push(`${blocking.workOrder || blocking.product} i\u015Fi ${processStartDate(blocking.end)} tarihine kadar istasyonu kullan\u0131yor.`);
    const calendarSeed = processCalendarSeed(seed, resourceId);
    const capacity = machineDayCapacity(calendarSeed, { id: resourceId, shiftFactor: resource.defaultShifts }, requestedStart);
    if (capacity.kind !== "normal" || !blocking) adjustments.push(`${capacity.label} \xB7 vardiya/tatil/bak\u0131m kapasitesine g\xF6re uygun ba\u015Flang\u0131\xE7 ${processStartDate(moved.start)}.`);
  }
  const affectedOperations = baseline.operations.flatMap((before) => {
    const after = plan.operations.find((item) => item.id === before.id);
    return !selectedIds.has(before.id) && (Math.abs(before.start - after.start) > 1e-8 || Math.abs(before.end - after.end) > 1e-8 || before.resourceId !== after.resourceId) ? [{ before, after }] : [];
  });
  return { seed: nextSeed, plan, operation: moved, requestedStart, insertionIndex, adjustments, affectedOperations, deliveryWarnings: placementDeliveryWarnings(seed, result, baseline, plan) };
}
function previewLinkedProcessPlacement(seed, result, baseline, operation, portions, resourceId, requestedStart) {
  if (portions.some((item) => item.current)) throw new Error("Ortak \u015Farj\u0131n \xE7al\u0131\u015Fan par\xE7as\u0131 var. Ger\xE7ek ba\u015Flang\u0131\xE7 de\u011Fi\u015Ftirilemez.");
  const resources = new Map(portions.map((item) => [item.id, item.id === operation.id ? resourceId : item.resourceId]));
  const groups = /* @__PURE__ */ new Map();
  for (const portion of [...portions].sort((a, b) => a.start - b.start || a.id.localeCompare(b.id))) {
    const resource = resources.get(portion.id);
    groups.set(resource, [...groups.get(resource) ?? [], portion]);
  }
  const ids = new Set(portions.map((item) => item.id));
  let next = cloneSeedOverrides(seed);
  preserveParallelAllocations(next, baseline.operations);
  for (const saved of next.processOperationOverrides ?? []) if (portions.some((item) => item.batchId === saved.batchId && item.process === saved.process)) {
    saved.routeMode = "manual";
    delete saved.preservedStart;
    delete saved.preservedEnd;
  }
  let plan = baseline;
  let commonStart = Math.max(requestedStart, ...[...groups.values()].map((items) => items[0].readyAt));
  const batchParallelMilling = operation.process === "milling" && (operation.parallelPortion || baseline.operations.some((item) => item.parallelPortion));
  if (batchParallelMilling) {
    for (const [target, group] of groups) {
      for (const portion of group) {
        const res = assertProcessPlacementResource(next, portion, target);
        if (res.planEnd && commonStart >= Math.floor(res.planEnd) + 1) {
          throw new Error(`${target} plan penceresi ${processStartDate(res.planEnd)} tarihinde bitiyor.`);
        }
      }
    }
  }
  for (let attempt = 0; attempt < 128; attempt++) {
    if (batchParallelMilling) {
      for (const [target, group] of groups) {
        for (const portion of group) {
          const current = plan.operations.find((item) => item.id === portion.id);
          const req = Math.max(commonStart, current.readyAt);
          if (req < current.readyAt - 1e-8) {
            const predecessor = baseline.operations.find((item) => item.id === current.predecessorOperationId);
            throw new Error(`\xD6nceki proses tamamlanmad\u0131: ${current.product} i\xE7in ${predecessor ? processLabelForError(predecessor.process) : "\xF6nceki proses"} ve zorunlu bekleme nedeniyle en erken ba\u015Flang\u0131\xE7 ${processStartDate(current.readyAt)}. \u0130stenen: ${processStartDate(req)}.`);
          }
          const override = next.processOperationOverrides.find((item) => item.batchId === portion.batchId && item.process === "milling");
          const part = override.parallelAllocations.find((item) => item.id === portion.id);
          part.resourceId = target;
          part.requestedStart = req;
          override.routeMode = "manual";
        }
      }
      plan = buildSingleStagePlanFromBaseline(next, result, plan, "milling");
      const conflict = plan.warnings.find((item) => item.code === "placement-conflict");
      if (conflict) throw new Error(conflict.message);
      for (const [target, group] of groups) {
        let cursor = commonStart;
        for (const portion of group) {
          const movedPortion = plan.operations.find((item) => item.id === portion.id);
          const req = Math.max(cursor, portion.readyAt);
          if (!movedPortion || movedPortion.resourceId !== target || movedPortion.start < req - 1e-8) {
            throw new Error("Freze pay\u0131 istenen kayna\u011Fa yerle\u015Ftirilemedi.");
          }
          const override = next.processOperationOverrides.find((item) => item.batchId === portion.batchId && item.process === "milling");
          const part = override.parallelAllocations.find((item) => item.id === portion.id);
          part.requestedStart = req;
          cursor = movedPortion.end;
        }
      }
    } else {
      for (const [target, group] of groups) {
        let cursor = commonStart;
        for (const portion of group) {
          const current = plan.operations.find((item) => item.id === portion.id);
          const preview = previewProcessOperationRescheduleWithBaseline(next, result, portion.id, target, Math.max(cursor, current.readyAt), plan, true, true);
          next = preview.seed;
          plan = preview.plan;
          cursor = preview.operation.end;
        }
      }
    }
    const moved = plan.operations.filter((item) => ids.has(item.id));
    const groupStarts = [...groups.keys()].map((target) => Math.min(...moved.filter((item) => item.resourceId === target).map((item) => item.start)));
    const nextStart = Math.max(...groupStarts);
    if (moved.length === portions.length && groupStarts.every((start) => Math.abs(start - nextStart) < 1e-8)) {
      plan = buildDownstreamProcessPlanFromStage(next, result, baseline, operation.process);
      const conflict = plan.warnings.find((item) => item.code === "placement-conflict");
      if (conflict) throw new Error(conflict.message);
      const affectedOperations = [];
      for (const before of baseline.operations) {
        const after = plan.operations.find((item) => item.id === before.id);
        if (!after || after.quantity !== before.quantity || after.product !== before.product) throw new Error("Ortak ta\u015F\u0131ma \u015Farj kimli\u011Fini veya miktar\u0131n\u0131 koruyamad\u0131.");
        const changed = after.resourceId !== before.resourceId || after.start !== before.start || after.end !== before.end;
        if (changed && (before.actual || before.current)) throw new Error("\xC7al\u0131\u015Fan ve tamamlanan i\u015Fler de\u011Fi\u015Ftirilemez.");
        if (changed && before.id !== operation.id) affectedOperations.push({ before, after });
      }
      const selected = plan.operations.find((item) => item.id === operation.id);
      const order = plan.operations.filter((item) => item.process === selected.process && item.resourceId === resourceId && !item.current && !item.actual).sort((a, b) => a.start - b.start || a.id.localeCompare(b.id));
      return {
        seed: next,
        plan,
        operation: selected,
        requestedStart,
        insertionIndex: order.findIndex((item) => item.id === selected.id),
        affectedOperations,
        adjustments: ["Ortak \u015Farj\u0131n par\xE7alar\u0131 ilk ortak uygun ba\u015Flang\u0131ca ta\u015F\u0131nd\u0131."],
        deliveryWarnings: placementDeliveryWarnings(seed, result, baseline, plan)
      };
    }
    if (!Number.isFinite(nextStart)) break;
    commonStart = nextStart;
  }
  throw new Error("\u015Earj\u0131n t\xFCm par\xE7alar\u0131 i\xE7in ortak uygun ba\u015Flang\u0131\xE7 bulunamad\u0131. Takvimleri kontrol edin.");
}
function placementDeliveryWarnings(seed, result, baseline, plan) {
  if (seed.productionArea === "cubuk-filtre") return filterPlacementDeliveryWarnings(seed, result, baseline, plan);
  const before = new Map(baseline.jobs.map((job) => [job.batchId, job]));
  return plan.jobs.flatMap((job) => {
    const previous = before.get(job.batchId);
    const batch = result.batches.find((item) => item.id === job.batchId);
    const dueDate = batch?.demandDueDate || seed.orders.filter((order) => order.product.toUpperCase() === job.product.toUpperCase() && order.quantity > 0 && order.dueDate).map((order) => order.dueDate).sort()[0];
    const due = dueDate ? inputDateSerial2(dueDate) + 1 : 0;
    if (!previous || !due || !job.deliveryReadyAt || job.deliveryReadyAt <= due + 1e-8 || job.deliveryReadyAt <= (previous.deliveryReadyAt || 0) + 1e-8) return [];
    return [{ batchId: job.batchId, product: job.product, workOrder: job.workOrder, dueDate, beforeReadyAt: previous.deliveryReadyAt, afterReadyAt: job.deliveryReadyAt, lateDays: Math.ceil(job.deliveryReadyAt - due) }];
  });
}
function filterPlacementDeliveryWarnings(seed, result, baseline, plan) {
  const readyBefore = new Map(baseline.jobs.map((job) => [job.batchId, job.deliveryReadyAt]));
  const delayed = plan.jobs.filter((job) => {
    const previous = readyBefore.get(job.batchId) ?? 0;
    return previous > 0 && Math.floor(job.deliveryReadyAt) > Math.floor(previous);
  });
  if (!delayed.length) return [];
  const before = buildWeeklyPlanStatus(seed, result, buildDeliveryReadinessEvents(seed, result, baseline));
  const after = buildWeeklyPlanStatus(seed, result, buildDeliveryReadinessEvents(seed, result, plan));
  const priorShortage = new Map(before.flatMap((row) => row.products.map((product) => [`${row.dueDate}:${product.product}`, product.shortage])));
  const worse = after.filter((row) => !row.excludedFromPlan).flatMap((row) => row.products.filter((product) => product.shortage > (priorShortage.get(`${row.dueDate}:${product.product}`) ?? 0)).map((product) => ({ product: product.product, dueDate: row.dueDate, dueDay: inputDateSerial2(row.dueDate) })));
  return delayed.flatMap((job) => {
    const beforeReadyAt = readyBefore.get(job.batchId);
    const afterDay = Math.floor(job.deliveryReadyAt);
    const due = worse.find((row) => row.product === job.product.toUpperCase() && Math.floor(beforeReadyAt) <= row.dueDay && row.dueDay < afterDay);
    if (!due) return [];
    return [{
      batchId: job.batchId,
      product: job.product,
      workOrder: job.workOrder,
      dueDate: due.dueDate,
      beforeReadyAt,
      afterReadyAt: job.deliveryReadyAt,
      lateDays: afterDay - due.dueDay
    }];
  });
}
function previewProcessQueuePlacement(seed, result, request) {
  const baseline = processPlacementBaseline(seed, result, request.operationId);
  const operation = baseline.operations.find((item) => item.id === request.operationId);
  if (!operation || operation.actual || operation.current || operation.process === "turning") throw new Error("Yaln\u0131zca kuyruktaki downstream operasyonlar\u0131 ta\u015F\u0131nabilir; \xE7al\u0131\u015Fan ve tamamlanan i\u015Fler sabittir.");
  const resource = assertProcessPlacementResource(seed, operation, request.resourceId);
  const ordered = baseline.operations.filter((item) => item.process === operation.process && item.resourceId === request.resourceId && !item.actual && !item.current && !item.manualCandidate).sort((a, b) => a.start - b.start || a.id.localeCompare(b.id));
  const currentIndex = ordered.findIndex((item) => item.id === operation.id);
  const queue = ordered.filter((item) => item.id !== operation.id);
  const position = request.position === "end" ? queue.length : request.position;
  if (!Number.isInteger(position) || position < 0 || position > queue.length) throw new Error(`Ge\xE7erli kuyruk s\u0131ras\u0131 1\u2013${queue.length + 1} aras\u0131nda olmal\u0131d\u0131r. Kuyruk de\u011Fi\u015Ftiyse yerle\u015Fimi yeniden se\xE7in.`);
  if (currentIndex === position) return { seed, plan: baseline, operation, requestedStart: operation.start, insertionIndex: position, adjustments: [], affectedOperations: [] };
  const requestedStart = queue[position]?.start ?? queue.at(-1)?.end ?? Math.max(
    operation.readyAt,
    resource.availableStart ?? 0,
    ...baseline.operations.filter((item) => item.resourceId === request.resourceId && (item.current || item.actual)).map((item) => item.end)
  );
  return previewProcessOperationRescheduleWithBaseline(seed, result, operation.id, request.resourceId, requestedStart, baseline);
}
function processJobStartAvailability(seed, plan, resourceId, now) {
  const resource = seed.processMasterData?.resources.find((item) => item.id === resourceId);
  if (!resource?.active) return { reason: "\u0130\u015F merkezi aktif de\u011Fil.", guidance: "\u0130\u015F merkezi ayarlar\u0131nda aktiflik durumunu kontrol edin." };
  if (seed.processCurrentJobs?.some((job) => job.resourceId === resourceId)) return { reason: "\u0130\u015F merkezinde \xE7al\u0131\u015Fan bir i\u015F var.", guidance: "Mevcut i\u015Fi tamamlay\u0131n veya Mevcut i\u015Fi de\u011Fi\u015Ftir ile ba\u015Fka bir haz\u0131r \u015Farj se\xE7in." };
  if ((resource.availableStart ?? 0) > now) return { reason: `\u0130\u015F merkezi ${processStartDate(resource.availableStart)} tarihinde kullan\u0131labilir.`, guidance: "M\xFCsait ba\u015Flang\u0131\xE7 alan\u0131n\u0131 kontrol edin; bu zaman gelmeden \xFCretim ba\u015Flat\u0131lamaz." };
  if (resource.planEnd && Math.floor(resource.planEnd) < Math.floor(now)) return { reason: "\u0130\u015F merkezinin plan penceresi sona erdi.", guidance: "Plan biti\u015Fi alan\u0131n\u0131 kontrol edin." };
  const queue = plan.operations.filter((operation2) => operation2.resourceId === resourceId && !operation2.actual && !operation2.current).sort((a, b) => a.start - b.start || a.id.localeCompare(b.id));
  const released = queue.filter((operation2) => {
    const lot = seed.wipLots?.find((item) => item.id === operation2.wipLotId);
    return operation2.source === "wip" && lot && lot.availableQuantity > 0 && lot.nextProcess === operation2.process && lot.stage !== "on-hold" && lot.stage !== "unclassified";
  });
  const operation = released.find((item) => item.readyAt <= now + 1e-8 && actualProcessStartEligibility(seed, item, now, true).ok);
  if (operation) return { operation, reason: "" };
  if (released.length) {
    const earliest = released.reduce((left, right) => left.readyAt <= right.readyAt ? left : right);
    return { reason: `Yar\u0131 mam\xFCl ${processStartDate(earliest.readyAt)} tarihinde haz\u0131r olacak.`, guidance: `${earliest.workOrder || earliest.product} \xB7 \u015Earj Yolculu\u011Fu\u2019nda \xF6nceki prosesin ger\xE7ek tamamlanma tarihini ve saatini, varsa bekleme a\u015Famas\u0131n\u0131 kontrol edin. Saat T\xFCrkiye saatidir.` };
  }
  if (queue.length) return { reason: "\xD6nceki proses hen\xFCz tamamlanmad\u0131 veya yar\u0131 mam\xFCl serbest b\u0131rak\u0131lmad\u0131.", guidance: "\u015Earj Yolculu\u011Fu\u2019nda \xF6nceki prosesi ve yar\u0131 mam\xFCl\xFCn konumunu kontrol edin. Kuyrukta planl\u0131 i\u015F olmas\u0131, malzemenin \xFCretime haz\u0131r oldu\u011Fu anlam\u0131na gelmez." };
  const held = seed.wipLots?.find((lot) => {
    const product = processMasterDataForProduct(seed.processMasterData, lot.product);
    const parameter = product?.processes.find((item) => item.process === resource.process);
    return lot.availableQuantity > 0 && (lot.stage === "on-hold" || lot.stage === "unclassified") && (lot.nextProcess === resource.process || lot.stage === "unclassified") && product && resourceSupportsProcessProduct(resource, product) && parameter && activeProcessResourceIds(parameter).includes(resourceId);
  });
  if (held) return { reason: held.stage === "on-hold" ? `${held.workOrder || held.product} \u015Farj\u0131 blokeli.` : `${held.workOrder || held.product} \u015Farj\u0131n\u0131n konumu do\u011Frulanmal\u0131.`, guidance: "Bu i\u015F merkezinde ba\u015Flat\u0131labilecek planl\u0131 i\u015F yok. Yar\u0131 mam\xFCl ekran\u0131nda \u015Farj\u0131n blokaj\u0131n\u0131 veya ger\xE7ek konumunu kontrol edin." };
  return { reason: "Bu i\u015F merkezinde \xFCretime al\u0131nabilecek planl\u0131 i\u015F yok. \xDCr\xFCn rotas\u0131 ve kapasite ayarlar\u0131n\u0131 kontrol edin.", guidance: "Kuyru\u011Fu, \xFCr\xFCn\xFCn bu i\u015F merkezine uygunlu\u011Funu ve vardiya h\u0131z\u0131n\u0131 kontrol edin. Plan uyar\u0131lar\u0131 ile G\xFCnl\xFCk vardiya / Planl\u0131 bak\u0131m kay\u0131tlar\u0131 kapasite eksikli\u011Fini a\xE7\u0131klayabilir." };
}
function processStartDate(serial2) {
  return new Intl.DateTimeFormat("tr-TR", { day: "2-digit", month: "2-digit", year: "numeric", hour: "2-digit", minute: "2-digit", timeZone: "UTC" }).format(excelSerialToDate(serial2));
}
function initialProcessEditSeed(seed, process2) {
  if (seed.initialProcessPlanComplete !== false) return seed;
  const order = productionProcessOrder(seed);
  const index = order.indexOf(process2);
  if (index < 0 || seed.plannedThroughProcess === void 0 || index > order.indexOf(seed.plannedThroughProcess))
    throw new Error("\xD6nce se\xE7ili prosesi planlay\u0131n.");
  const filteredOverrides = (seed.processOperationOverrides ?? []).filter((row) => order.indexOf(row.process) <= index || seed.processCurrentJobs?.some((job) => job.batchId === row.batchId && job.process === row.process));
  if (seed.plannedThroughProcess === process2 && filteredOverrides.length === (seed.processOperationOverrides?.length ?? 0)) {
    return seed;
  }
  const next = cloneSeedOverrides(seed);
  next.plannedThroughProcess = process2;
  next.processOperationOverrides = filteredOverrides.map((override) => ({
    ...override,
    ...override.parallelAllocations ? { parallelAllocations: override.parallelAllocations.map((part) => ({ ...part })) } : {}
  }));
  return next;
}
function resetDownstreamProcessPlan(seed, result, process2) {
  if (!productionProcessOrder(seed).filter((p) => p !== "turning").includes(process2)) throw new Error("Yaln\u0131zca Delme, \xC7apak Alma veya GKM ayr\u0131 planlanabilir.");
  const nextSeed = structuredClone(initialProcessEditSeed(seed, process2));
  nextSeed.processOperationOverrides = (nextSeed.processOperationOverrides ?? []).filter((override) => override.process !== process2 || nextSeed.processCurrentJobs?.some((job) => job.batchId === override.batchId && job.process === process2) || nextSeed.productionInterruptions?.some((item) => isProductionInterruption(item) && !item.completedAt && item.chargeId === override.batchId && item.process === process2) || activeLotInterruptions(nextSeed, nextSeed.wipLots?.find((lot) => lot.id === override.batchId)).length > 0);
  return { seed: nextSeed, plan: buildDownstreamProcessPlan(nextSeed, result) };
}
function startProcessCurrentJob(seed, result, operationId, requestedStart, confirmedInterruption = false) {
  const plan = buildDownstreamProcessPlan(seed, result);
  const operation = plan.operations.find((item) => item.id === operationId);
  if (!operation || operation.actual || operation.current || operation.process === "turning") throw new Error("Mevcut i\u015Fe al\u0131nacak downstream operasyonu bulunamad\u0131.");
  if (operation.source !== "wip" || !operation.wipLotId) throw new Error("Bu i\u015F hen\xFCz sahadaki yar\u0131 mam\xFCl de\u011Fil; \xF6nce \xF6nceki operasyon tamamlanmal\u0131.");
  const lot = seed.wipLots?.find((item) => item.id === operation.wipLotId);
  if (!lot || lot.nextProcess !== operation.process || lot.availableQuantity <= 0 || lot.stage === "on-hold" || lot.stage === "unclassified") throw new Error("\xD6nceki proses hen\xFCz tamamlanmad\u0131 veya yar\u0131 mam\xFCl serbest b\u0131rak\u0131lmad\u0131.");
  if (activeLotInterruptions(seed, lot).length && !confirmedInterruption) throw new Error("\xDCretim sonlanmad\u0131, yine de \xFCretime alay\u0131m m\u0131? Devam etmek i\xE7in onaylay\u0131n.");
  if ((seed.processCurrentJobs ?? []).some((item) => item.resourceId === operation.resourceId)) throw new Error(`${operation.resourceId} \xFCzerinde zaten \xE7al\u0131\u015Fan bir i\u015F var.`);
  const resource = assertProcessPlacementResource(seed, operation, operation.resourceId);
  const start = Math.max(operation.readyAt, requestedStart ?? operation.start, resource.availableStart ?? operation.readyAt);
  const eligibility = actualProcessStartEligibility(seed, operation, start, confirmedInterruption);
  if (!eligibility.ok) throw new Error(eligibility.reason);
  if (requestedStart != null && requestedStart < operation.readyAt - 1e-8) throw new Error(`${operation.product}, \xF6nceki operasyon tamamlanmadan \xFCretime al\u0131namaz.`);
  const timeline = addMachineCapacityHours(
    processCalendarSeed(seed, resource.id),
    { id: resource.id, shiftFactor: resource.defaultShifts, finishOffset: 0 },
    start,
    operation.setupHours + operation.runHours
  );
  if (resource.planEnd && timeline.end > Math.floor(resource.planEnd) + 1 + 1e-8) throw new Error(`${resource.id} plan penceresinde bu i\u015Fi tamamlayacak s\xFCre yok.`);
  const admittedLot = operation.parallelPortion && operation.quantity < lot.availableQuantity ? reserveFilterMillingPortion(seed, lot.id, operation.quantity, timeline.start) : lot;
  if (admittedLot.id !== lot.id) {
    for (const saved of seed.processOperationOverrides ?? []) if (saved.batchId === lot.id && saved.process === "milling" && saved.parallelAllocations)
      saved.parallelAllocations = saved.parallelAllocations.filter((part) => part.id !== operation.id);
  }
  const updatedAt = (/* @__PURE__ */ new Date()).toISOString();
  const current = {
    ...admittedLot.sharedCharge ? { sharedCharge: admittedLot.sharedCharge } : {},
    resourceId: resource.id,
    resourceName: resource.name,
    process: operation.process,
    batchId: admittedLot.id,
    operationId: `${admittedLot.id}:${operation.process}`,
    wipLotId: admittedLot.id,
    workOrder: operation.workOrder,
    product: operation.product,
    family: operation.family,
    originalQuantity: operation.quantity,
    remainingQuantity: operation.quantity,
    readyAt: operation.readyAt,
    start: timeline.start,
    end: timeline.end,
    setupKey: operation.setupKey,
    unitsPerShift: operation.unitsPerShift,
    setupHours: operation.setupHours,
    updatedAt
  };
  for (const pause of seed.productionInterruptions ?? []) if (!pause.completedAt && pause.chargeId === current.batchId && pause.process === current.process) pause.resumedAt = current.start;
  seed.processCurrentJobs = [...seed.processCurrentJobs ?? [], current];
  seed.processOperationOverrides = [
    ...(seed.processOperationOverrides ?? []).filter((item) => !(item.batchId === current.batchId && item.process === operation.process)),
    { batchId: current.batchId, process: operation.process, resourceId: resource.id, requestedStart: timeline.start, updatedAt }
  ];
  return current;
}
function updateProcessCurrentJob(seed, resourceId, input) {
  const current = (seed.processCurrentJobs ?? []).find((item) => item.resourceId === resourceId);
  if (!current) throw new Error(`${resourceId} \xFCzerinde d\xFCzenlenecek mevcut i\u015F bulunamad\u0131.`);
  const lot = (seed.wipLots ?? []).find((item) => item.id === current.wipLotId);
  if (!Number.isInteger(input.originalQuantity) || input.originalQuantity <= 0) throw new Error("Orijinal adet s\u0131f\u0131rdan b\xFCy\xFCk tam say\u0131 olmal\u0131d\u0131r.");
  if (lot && input.originalQuantity > lot.availableQuantity) throw new Error("Orijinal adet yar\u0131 mam\xFCl bakiyesini a\u015Famaz.");
  if (!Number.isInteger(input.remainingQuantity) || input.remainingQuantity <= 0 || input.remainingQuantity > input.originalQuantity) throw new Error("Kalan adet, orijinal adedi a\u015Fmayan pozitif tam say\u0131 olmal\u0131d\u0131r.");
  const resource = seed.processMasterData?.resources.find((item) => item.id === resourceId && item.process === current.process);
  if (!resource || !resource.active || resource.defaultShifts <= 0) throw new Error(`${resourceId} i\xE7in aktif vardiya kapasitesi bulunamad\u0131.`);
  if (input.remainingAsOf === void 0 && seed.productionArea === "cubuk-filtre") {
    const runHours2 = input.remainingQuantity / current.unitsPerShift * getSetupSettings(seed).shiftHours;
    const timeline = addMachineCapacityHours(processCalendarSeed(seed, resource.id), { id: resource.id, shiftFactor: resource.defaultShifts, finishOffset: 0 }, current.start, current.setupHours + runHours2);
    Object.assign(current, { originalQuantity: input.originalQuantity, remainingQuantity: input.remainingQuantity, start: timeline.start, end: timeline.end, updatedAt: (/* @__PURE__ */ new Date()).toISOString() });
    seed.processOperationOverrides = [
      ...(seed.processOperationOverrides ?? []).filter((item) => !(item.batchId === current.batchId && item.process === current.process)),
      { batchId: current.batchId, process: current.process, resourceId, requestedStart: current.start, updatedAt: current.updatedAt }
    ];
    return current;
  }
  const remainingAsOf = input.remainingAsOf ?? factoryNowSerial();
  if (!Number.isFinite(remainingAsOf) || remainingAsOf <= 0) throw new Error("Kalan miktar\u0131n ge\xE7erli oldu\u011Fu tarih ve saat ge\xE7ersiz.");
  if (remainingAsOf < current.start - 1e-8) throw new Error("Kalan miktar\u0131n tarihi mevcut i\u015Fin fiili ba\u015Flang\u0131c\u0131ndan \xF6nce olamaz.");
  if (input.remainingAsOf !== void 0 && remainingAsOf > factoryNowSerial() + 1 / 1440) throw new Error("Kalan miktar\u0131n tarihi gelecekte olamaz.");
  const calendar = processCalendarSeed(seed, resource.id);
  const capacity = { id: resource.id, shiftFactor: resource.defaultShifts, finishOffset: 0 };
  const runHours = input.remainingQuantity / current.unitsPerShift * getSetupSettings(seed).shiftHours;
  const setupEnd = addMachineCapacityHours(calendar, capacity, current.start, current.setupHours).end;
  const end = addMachineCapacityHours(calendar, capacity, Math.max(setupEnd, remainingAsOf), runHours).end;
  Object.assign(current, {
    originalQuantity: input.originalQuantity,
    remainingQuantity: input.remainingQuantity,
    end,
    remainingAsOf,
    updatedAt: (/* @__PURE__ */ new Date()).toISOString()
  });
  seed.processOperationOverrides = [
    ...(seed.processOperationOverrides ?? []).filter((item) => !(item.batchId === current.batchId && item.process === current.process)),
    { batchId: current.batchId, process: current.process, resourceId, requestedStart: current.start, updatedAt: current.updatedAt }
  ];
  return current;
}
function replaceProcessCurrentJob(seed, result, resourceId, operationId, requestedStart, input, confirmedInterruption = false) {
  assertProductionSwitchSnapshot(seed, result.batches, input);
  const next = structuredClone(seed);
  const outcome = replaceProcessCurrentJobInPlace(next, result, resourceId, operationId, requestedStart, input, confirmedInterruption);
  Object.assign(seed, next);
  return outcome;
}
function replaceProcessCurrentJobInPlace(seed, result, resourceId, operationId, requestedStart, input, confirmedInterruption) {
  const previous = (seed.processCurrentJobs ?? []).find((item) => item.resourceId === resourceId);
  if (!previous) throw new Error(`${resourceId} \xFCzerinde de\u011Fi\u015Ftirilecek mevcut i\u015F bulunamad\u0131.`);
  const plan = processPlacementBaseline(seed, result, operationId);
  const target = plan.operations.find((item) => item.id === operationId);
  if (!target || target.actual || target.current || target.process === "turning") throw new Error("Mevcut i\u015Fe al\u0131nacak downstream operasyonu bulunamad\u0131.");
  if (target.process !== previous.process) throw new Error(`Yaln\u0131zca ${processLabelForError(previous.process)} i\u015Fleri mevcut \xFCretime al\u0131nabilir.`);
  if (target.source !== "wip" || !target.wipLotId) throw new Error("Bu \u015Farj hen\xFCz sahadaki yar\u0131 mam\xFCl de\u011Fil; \xF6nce \xF6nceki operasyon tamamlanmal\u0131.");
  assertProcessPlacementResource(seed, target, resourceId);
  const start = requestedStart ?? target.start;
  if (start < target.readyAt - 1e-8) throw new Error("Yeni \u015Farj\u0131n \xF6nceki prosesi veya beklemesi hen\xFCz tamamlanmad\u0131.");
  const produced2 = validateProductionInterruption(input, previous.originalQuantity, previous.start, start);
  const previousLot = seed.wipLots?.find((lot) => lot.id === previous.wipLotId);
  if (!previousLot || previous.originalQuantity !== previousLot.availableQuantity) throw new Error("Mevcut i\u015Fin adedi yar\u0131 mam\xFCl bakiyesiyle uyu\u015Fmuyor; kayd\u0131 kontrol edin.");
  if (produced2 > 0) {
    const pauseId = `pause-${crypto.randomUUID()}`;
    seed.productionInterruptions = [...seed.productionInterruptions ?? [], { id: pauseId, chargeId: previous.batchId, process: previous.process, resourceId, product: previous.product, workOrder: previous.workOrder, producedQuantity: produced2, remainingQuantity: previous.originalQuantity - produced2, reason: input.produced ? input.reason.trim() : "", occurredAt: start }];
    const split = completeWipOperation(seed, { lotId: previous.wipLotId, process: previous.process, resourceId, resourceName: previous.resourceName, quantity: produced2, startedAt: previous.start, completedAt: start, plannedStart: previous.start, plannedEnd: previous.end, confirmedInterruption: true });
    split.completed.interruptionIds = [...split.completed.interruptionIds ?? [], pauseId];
  }
  const updatedAt = (/* @__PURE__ */ new Date()).toISOString();
  seed.processCurrentJobs = (seed.processCurrentJobs ?? []).filter((item) => item.resourceId !== resourceId);
  seed.processOperationOverrides = [
    ...(seed.processOperationOverrides ?? []).filter((item) => !(item.batchId === previous.batchId && item.process === previous.process || item.batchId === target.batchId && item.process === target.process)),
    { batchId: previous.batchId, process: previous.process, resourceId, requestedStart: start + 1 / 86400, resumeAfterCurrent: true, updatedAt },
    { batchId: target.batchId, process: target.process, resourceId, requestedStart: start, updatedAt }
  ];
  const current = startProcessCurrentJob(seed, result, operationId, start, confirmedInterruption);
  const swappedPlan = buildDownstreamProcessPlan(seed, result);
  const resourceQueue = swappedPlan.operations.filter((item) => !item.actual && !item.current && item.process === previous.process && item.resourceId === resourceId).sort((left, right) => left.start - right.start || left.id.localeCompare(right.id));
  const interrupted = resourceQueue.find((item) => item.id === previous.operationId);
  if (!interrupted) throw new Error("\xD6nceki mevcut i\u015F tezgah kuyru\u011Funa geri al\u0131namad\u0131.");
  const desiredQueue = [interrupted, ...resourceQueue.filter((item) => item.id !== interrupted.id)];
  const queueBatchIds = new Set(desiredQueue.map((item) => item.batchId));
  let cursor = current.end;
  const localQueueOverrides = desiredQueue.map((item) => {
    cursor = Math.max(cursor, item.readyAt);
    const requestedStart2 = cursor;
    cursor += 1 / 86400;
    return { batchId: item.batchId, process: previous.process, resourceId, requestedStart: requestedStart2, resumeAfterCurrent: item.id === previous.operationId, updatedAt };
  });
  seed.processOperationOverrides = [
    ...(seed.processOperationOverrides ?? []).filter((item) => !(item.process === previous.process && queueBatchIds.has(item.batchId))),
    ...localQueueOverrides
  ];
  const finalPlan = buildDownstreamProcessPlan(seed, result);
  const finalQueue = finalPlan.operations.filter((item) => !item.actual && !item.current && item.process === previous.process && item.resourceId === resourceId).sort((left, right) => left.start - right.start || left.id.localeCompare(right.id));
  const queued = finalQueue[0];
  if (!queued || queued.id !== previous.operationId) throw new Error("\xD6nceki mevcut i\u015F tezgah kuyru\u011Funun ilk s\u0131ras\u0131na geri al\u0131namad\u0131.");
  return { current, queued };
}
function completeProcessCurrentJob(seed, result, resourceId, completedAt, completedQuantity, actualResourceId = resourceId, remainderAction, confirmedBuffer = false, countCorrectionReason) {
  const draft = structuredClone(seed);
  const outcome = completeProcessCurrentJobInPlace(draft, result, resourceId, completedAt, completedQuantity, actualResourceId, remainderAction, confirmedBuffer, countCorrectionReason);
  Object.assign(seed, draft);
  return outcome;
}
function completeProcessCurrentJobInPlace(seed, result, resourceId, completedAt, completedQuantity, actualResourceId = resourceId, remainderAction, confirmedBuffer = false, countCorrectionReason) {
  const scope = turningIdentityScope(seed, result.batches);
  const protectedIdentity = (product, batchId, lotId2) => scope.products.includes(product.trim().toUpperCase()) || scope.batchIds.includes(batchId) || scope.lotIds.includes(batchId) || Boolean(lotId2 && scope.lotIds.includes(lotId2));
  const current = (seed.processCurrentJobs ?? []).find((item) => item.resourceId === resourceId);
  if (!current) throw new Error(`${resourceId} \xFCzerinde tamamlanacak mevcut i\u015F bulunamad\u0131.`);
  if (protectedIdentity(current.product, current.batchId, current.wipLotId)) throw new Error("Bu mevcut i\u015F inceleme bekleyen \u015Farja ba\u011Fl\u0131. \xD6nce \u0130ncele ve d\xFCzelt ile kay\u0131tlar\u0131 do\u011Frulay\u0131n.");
  const lot = (seed.wipLots ?? []).find((item) => item.id === current.wipLotId);
  if (!lot) throw new Error("Mevcut i\u015Fe ba\u011Fl\u0131 yar\u0131 mam\xFCl kayd\u0131 bulunamad\u0131.");
  const actualResource = seed.processMasterData?.resources.find((item) => item.id === actualResourceId && item.process === current.process);
  if (!actualResource) throw new Error(`${actualResourceId}, ${processLabelForError(current.process)} i\xE7in ge\xE7erli bir i\u015F merkezi de\u011Fil.`);
  const realReadyAt = wipCompletionEarliestAt(seed, lot);
  if (completedAt < wipOperationReadyAt(lot) && !confirmedBuffer) throw new Error("Planlanan beklemeden erken tamamlama i\xE7in ilgili kontrol / y\u0131kaman\u0131n tamamland\u0131\u011F\u0131n\u0131 onaylay\u0131n.");
  if (!Number.isFinite(completedAt) || completedAt < realReadyAt) throw new Error("Tamamlanma tarihi \u015Farj\u0131n ger\xE7ek haz\u0131r olma tarihinden \xF6nce olamaz.");
  const quantity = completedQuantity ?? current.originalQuantity;
  if (!Number.isSafeInteger(quantity) || quantity <= 0) throw new Error("Fiili tamamlanan adet pozitif tam say\u0131 olmal\u0131d\u0131r.");
  completeWipOperation(seed, {
    lotId: current.wipLotId,
    process: current.process,
    resourceId: actualResource.id,
    resourceName: actualResource.name,
    quantity,
    countCorrectionReason,
    remainderAction,
    startedAt: Math.max(realReadyAt, Math.min(current.start, completedAt)),
    completedAt,
    plannedStart: current.start,
    plannedEnd: current.end,
    confirmedInterruption: true,
    confirmedBuffer
  });
  seed.processCurrentJobs = (seed.processCurrentJobs ?? []).filter((item) => item.resourceId !== resourceId);
  seed.processOperationOverrides = (seed.processOperationOverrides ?? []).filter((item) => !(item.batchId === current.batchId && item.process === current.process));
  const nextPlan = buildDownstreamProcessPlan(seed, result);
  const candidates = nextPlan.operations.filter((item) => !item.actual && !item.current && item.process === current.process && item.resourceId === resourceId).sort((left, right) => left.start - right.start || left.id.localeCompare(right.id));
  let promoted;
  const retainedQueue = (nextPlan.queueEntries ?? []).filter((row) => row.resourceId === resourceId && row.process === current.process);
  for (const candidate of candidates) {
    const placement = retainedQueue.find((row) => row.batchId === candidate.batchId);
    const blockedHead = retainedQueue.some((row) => !row.scheduled && (!placement || Number(row.resumeAfterCurrent) > Number(placement.resumeAfterCurrent) || row.resumeAfterCurrent === placement.resumeAfterCurrent && row.queueOrder <= placement.queueOrder));
    if (blockedHead) break;
    if (protectedIdentity(candidate.product, candidate.batchId, candidate.wipLotId)) {
      if (candidate.manualOverride) break;
      continue;
    }
    const eligibility = actualProcessStartEligibility(seed, candidate, completedAt);
    const resource = seed.processMasterData.resources.find((r) => r.id === resourceId);
    const timeline = eligibility.ok ? addMachineCapacityHours(processCalendarSeed(seed, resourceId), { id: resourceId, shiftFactor: resource.defaultShifts, finishOffset: 0 }, Math.max(completedAt, candidate.readyAt), candidate.setupHours + candidate.runHours) : void 0;
    const fits = timeline && (!resource.planEnd || timeline.end < Math.floor(resource.planEnd) + 1 + 1e-8);
    if (eligibility.ok && fits && candidate.readyAt <= completedAt + 1e-8) {
      promoted = startProcessCurrentJob(seed, result, candidate.id, completedAt);
      break;
    }
    if (candidate.manualOverride) break;
  }
  return { completedProduct: current.product, completedWorkOrder: current.workOrder, completedResourceId: actualResource.id, promoted };
}
function processLabelForError(process2) {
  return process2 === "gkm" ? "GKM" : processLabel(process2).toLocaleLowerCase("tr-TR");
}
function processGapDiagnostics(seed, master, operations) {
  const gaps = [];
  const shiftHours = getSetupSettings(seed).shiftHours;
  for (const resource of master.resources.filter((item) => item.process !== "turning")) {
    const queue = operations.filter((operation) => !operation.actual && operation.resourceId === resource.id).sort((left, right) => left.start - right.start || left.id.localeCompare(right.id));
    for (let index = 1; index < queue.length; index += 1) {
      const previous = queue[index - 1];
      const next = queue[index];
      if (next.start <= previous.end + 1e-8) continue;
      let code3 = "no-eligible-wip";
      let message = `Bu aral\u0131kta ${resource.id} i\xE7in uygun ve haz\u0131r yar\u0131 mam\xFCl yoktu; s\u0131radaki i\u015F ${next.product} oldu.`;
      if (next.readyAt > previous.end + 1e-8) {
        if (next.waitWorkdaysBefore > 0) {
          code3 = "route-wait";
          message = `${next.product}, rota gere\u011Fi ${next.waitWorkdaysBefore} i\u015F g\xFCn\xFC bekledikten sonra ${resource.id} i\xE7in haz\u0131r oldu.`;
        } else {
          code3 = "upstream-not-ready";
          message = `${next.product} \xF6nceki operasyonu tamamlanmad\u0131\u011F\u0131 i\xE7in bu aral\u0131kta ${resource.id} \xFCzerinde ba\u015Flat\u0131lamad\u0131.`;
        }
      } else {
        const calendarSeed = processCalendarSeed(seed, resource.id);
        const startDay = Math.floor(previous.end);
        const endDay = Math.floor(next.start);
        const days = Array.from({ length: Math.max(1, endDay - startDay + 1) }, (_, offset) => startDay + offset);
        const closed = days.map((serial2) => ({ serial: serial2, capacity: machineDayCapacity(calendarSeed, { id: resource.id, shiftFactor: resource.defaultShifts }, serial2) })).find(({ capacity }) => capacity.shifts === 0);
        if (closed) {
          code3 = closed.capacity.kind === "maintenance" ? "maintenance" : closed.capacity.kind === "shift" ? "zero-shift" : "closed-day";
          message = `${closed.capacity.label} nedeniyle ${resource.id} kapasitesi kapal\u0131yd\u0131; i\u015F ilk \xE7al\u0131\u015F\u0131labilir zamana ta\u015F\u0131nd\u0131.`;
        } else {
          const capacity = machineDayCapacity(calendarSeed, { id: resource.id, shiftFactor: resource.defaultShifts }, startDay);
          const windowEnd = startDay + capacity.shifts * shiftHours / 24;
          if (capacity.shifts > 0 && previous.end >= windowEnd - 1e-8) {
            code3 = "daily-capacity";
            message = `${resource.id} i\xE7in g\xFCnl\xFCk ${capacity.shifts} vardiyal\u0131k kapasite doldu; s\u0131radaki i\u015F bir sonraki \xE7al\u0131\u015Fma penceresinde ba\u015Flad\u0131.`;
          }
        }
      }
      gaps.push({ id: `${resource.id}:${previous.id}:${next.id}`, process: resource.process, resourceId: resource.id, start: previous.end, end: next.start, code: code3, message });
    }
  }
  return gaps;
}
var stagePlanContexts = /* @__PURE__ */ new WeakMap();
function finalizeDownstreamProcessPlan(seed, result, ctx, stageResults) {
  const { master, sources, representedBatchIds, baseOperations, baseWarnings, stageOrder } = ctx;
  const warnings = [...baseWarnings];
  const downstream = [];
  for (const process2 of stageOrder) {
    const stage = stageResults.get(process2);
    if (!stage) continue;
    warnings.push(...stage.warnings);
    downstream.push(...stage.operations);
  }
  const operations = [...baseOperations, ...downstream].sort((left, right) => left.start - right.start || left.sequence - right.sequence || Number(right.actual) - Number(left.actual) || left.id.localeCompare(right.id));
  const jobs = sources.map((source) => {
    const route = operations.filter((operation) => operation.batchId === source.id).sort((left, right) => left.sequence - right.sequence || Number(right.actual) - Number(left.actual) || left.end - right.end);
    const completion2 = route.at(-1)?.end ?? source.releaseAt;
    const customRouteComplete = !source.masterProduct.route || source.masterProduct.route.length > 0 && !warnings.some((warning) => warning.product === source.product && warning.code === "invalid-route") && source.masterProduct.route.every((process2) => route.some((operation) => (operation.recordedProcess ?? operation.process) === process2) || source.lot?.manualReceipt?.completedProcesses.includes(process2)) && source.lot?.stage !== "on-hold" && source.lot?.stage !== "unclassified";
    const deliveryReadyAt = !customRouteComplete ? 0 : source.lot?.stage === "delivery-ready" ? source.lot.readyAt : source.masterProduct.route || route.some((operation) => operation.process === "gkm") ? routedDeliveryReadyAt(seed, completion2, source.masterProduct.family, route.at(-1)?.process) : 0;
    return {
      batchId: source.id,
      source: source.source,
      workOrder: source.workOrder,
      wipLotId: source.lot?.id,
      product: source.product,
      family: source.masterProduct.family,
      quantity: source.quantity,
      turningMachineId: route.find((operation) => operation.process === "turning")?.resourceId ?? source.batch?.machineId ?? source.machine?.id ?? "",
      operations: route,
      completion: completion2,
      deliveryReadyAt
    };
  });
  const represented = new Set(jobs.map((job) => job.batchId));
  const addMissing = (job) => {
    if (represented.has(job.batchId)) return;
    jobs.push(job);
    represented.add(job.batchId);
    operations.push(...job.operations);
  };
  for (const lot of seed.wipLots ?? []) if (lot.availableQuantity > 0 && lot.stage !== "delivered" && lot.stage !== "scrapped") {
    addMissing({ batchId: lot.id, source: "wip", workOrder: lot.workOrder, wipLotId: lot.id, product: lot.product, family: lot.family, quantity: lot.availableQuantity, turningMachineId: lot.completedSteps?.find((step) => step.process === "turning")?.resourceId ?? "", operations: actualWipOperations(lot, processMasterDataForProduct(master, lot.product)), completion: 0, deliveryReadyAt: 0 });
  }
  for (const machine of seed.machines ?? []) if (machine.currentJob.product && machine.currentJob.quantity > 0) {
    addMissing({ batchId: `current:${machine.id}`, source: "current-turning", workOrder: machine.currentJob.workOrder, product: machine.currentJob.product, family: processMasterDataForProduct(master, machine.currentJob.product)?.family ?? "piston", familyKnown: Boolean(processMasterDataForProduct(master, machine.currentJob.product)), quantity: machine.currentJob.quantity, turningMachineId: machine.id, operations: [], completion: 0, deliveryReadyAt: 0 });
  }
  for (const batch of result.batches) if (batch.status === "planned" && batch.quantity > 0 && !representedBatchIds.has(batch.id)) {
    addMissing({ batchId: batch.id, source: "turning-plan", workOrder: batch.workOrder ?? "", product: batch.product, family: processMasterDataForProduct(master, batch.product)?.family ?? "piston", familyKnown: Boolean(processMasterDataForProduct(master, batch.product)), quantity: batch.quantity, turningMachineId: batch.machineId, operations: [], completion: 0, deliveryReadyAt: 0 });
  }
  for (const job of jobs) Object.assign(job, describeProcessRoute(seed, job, warnings));
  const queueEntries = processQueueEntries(seed, jobs, operations);
  const completion = Math.max(0, ...jobs.map((job) => job.completion));
  const deliveryCompletion = Math.max(0, ...jobs.map((job) => job.deliveryReadyAt));
  const gaps = processGapDiagnostics(seed, master, downstream);
  const plan = { state: operations.length ? "planned" : "empty", operations, jobs, warnings, gaps, completion, deliveryCompletion, queueEntries };
  stagePlanContexts.set(plan, { ...ctx, stageResults });
  return plan;
}
var lastDownstreamExecution = null;
function downstreamBaseInputKey(seed, result) {
  return JSON.stringify([
    seed.productionArea,
    seed.processMasterData,
    seed.machines,
    seed.wipLots,
    seed.processCurrentJobs,
    seed.productionInterruptions,
    seed.flowSettings,
    seed.processWaitSettings,
    seed.setupSettings,
    seed.holidays,
    seed.calendarEvents,
    seed.orders,
    result.batches
  ]);
}
function downstreamStageInputKey(seed, process2, fullOrder) {
  const enabled = seed.plannedThroughProcess === void 0 || fullOrder.indexOf(process2) <= fullOrder.indexOf(seed.plannedThroughProcess);
  const overrides = (seed.processOperationOverrides ?? []).filter((item) => item.process === process2);
  return JSON.stringify([enabled, overrides]);
}
function buildDownstreamBaseContext(seed, result, includeInterruptedCandidates) {
  const master = seed.processMasterData ?? { version: 0, source: { kind: "one-time-foundation", files: [], calculatedOnce: "" }, machineCodeStandard: [], products: [], resources: [] };
  const baseWarnings = validateProcessMasterData(master);
  const sources = [];
  for (const lot of (seed.wipLots ?? []).filter((item) => item.availableQuantity > 0 && item.stage !== "delivered" && item.stage !== "scrapped")) {
    const masterProduct = processMasterDataForProduct(master, lot.product);
    if (!masterProduct) {
      baseWarnings.push({ code: "missing-product", product: lot.product, batchId: lot.id, message: `${lot.product} yar\u0131 mam\xFCl\xFC i\xE7in downstream \xFCr\xFCn rotas\u0131 bulunamad\u0131.` });
      continue;
    }
    sources.push({
      id: lot.id,
      source: "wip",
      product: lot.product,
      quantity: lot.availableQuantity,
      workOrder: lot.workOrder,
      releaseAt: lot.readyAt,
      nextProcess: lot.stage === "on-hold" || lot.stage === "unclassified" ? void 0 : lot.nextProcess,
      lot,
      masterProduct
    });
  }
  const representedBatchIds = new Set((seed.wipLots ?? []).map((lot) => lot.sourceBatchId).filter(Boolean));
  for (const machine of (seed.machines ?? []).filter((item) => item.currentJob.product && item.currentJob.quantity > 0 && item.currentJob.end > 0)) {
    const product = machine.currentJob.product.trim().toUpperCase();
    const masterProduct = processMasterDataForProduct(master, product);
    if (!masterProduct) {
      baseWarnings.push({ code: "missing-product", product, batchId: `current:${machine.id}`, message: `${product} mevcut torna i\u015Fi i\xE7in downstream \xFCr\xFCn rotas\u0131 bulunamad\u0131.` });
      continue;
    }
    sources.push({
      id: `current:${machine.id}`,
      source: "current-turning",
      product,
      quantity: machine.currentJob.quantity,
      workOrder: machine.currentJob.workOrder ?? "",
      releaseAt: machine.currentJob.end,
      nextProcess: hasActiveProductionInterruption(seed, machine.currentJob.batchId, machine.currentJob.interruptionId) ? void 0 : productProcessRoute(masterProduct).find((process2) => process2 !== "turning"),
      machine,
      masterProduct
    });
  }
  for (const batch of result.batches.filter((item) => item.status === "planned" && item.quantity > 0 && item.end > 0)) {
    if (representedBatchIds.has(batch.id)) continue;
    const masterProduct = processMasterDataForProduct(master, batch.product);
    if (!masterProduct) {
      baseWarnings.push({ code: "missing-product", product: batch.product, batchId: batch.id, message: `${batch.product} i\xE7in downstream \xFCr\xFCn rotas\u0131 bulunamad\u0131.` });
      continue;
    }
    sources.push({ id: batch.id, source: "turning-plan", product: batch.product, quantity: batch.quantity, workOrder: batch.workOrder ?? "", releaseAt: batch.end, nextProcess: hasActiveProductionInterruption(seed, batch.id, batch.interruptionId) ? void 0 : productProcessRoute(masterProduct).find((process2) => process2 !== "turning"), batch, masterProduct });
  }
  for (const source of sources) {
    if (source.masterProduct.family !== "cubuk-filtre") continue;
    const turningId = source.machine?.id ?? source.batch?.machineId ?? source.lot?.completedSteps.find((s) => s.process === "turning")?.resourceId;
    const route = effectiveProductRoute(source.masterProduct, turningId);
    source.masterProduct = { ...source.masterProduct, route, processes: source.masterProduct.processes.filter((p) => route.includes(p.process)) };
    if (source.source !== "wip" && source.nextProcess) source.nextProcess = route.find((p) => p !== "turning");
  }
  const sourceRank = (source) => source === "wip" ? 0 : source === "current-turning" ? 1 : 2;
  sources.sort((left, right) => sourceRank(left.source) - sourceRank(right.source) || left.releaseAt - right.releaseAt || left.id.localeCompare(right.id));
  const baseOperationsByKey = /* @__PURE__ */ new Map();
  const baseOperations = sources.flatMap((source) => source.source === "wip" ? actualWipOperations(source.lot, source.masterProduct) : [turningOperation(seed, source)]);
  for (const operation of baseOperations) baseOperationsByKey.set(`${operation.batchId}:${operation.process}`, operation);
  const stageOrder = productionProcessOrder(seed).filter((process2) => process2 !== "turning");
  return { master, sources, representedBatchIds, baseOperations, baseWarnings, baseOperationsByKey, stageOrder, includeInterruptedCandidates };
}
function buildSingleStagePlanFromBaseline(seed, result, baseline, process2) {
  const ctx = stagePlanContexts.get(baseline);
  const fullOrder = productionProcessOrder(seed);
  const stageOrder = fullOrder.filter((item) => item !== "turning");
  const fromIndex = ctx ? ctx.stageOrder.indexOf(process2) : -1;
  if (!ctx || ctx.master !== (seed.processMasterData ?? ctx.master) || fromIndex < 0 || ctx.stageOrder.join("|") !== stageOrder.join("|")) {
    return buildDownstreamProcessPlan(seed, result);
  }
  const currentOperationsByKey = new Map(
    fromIndex === 0 ? ctx.baseOperationsByKey : ctx.stageResults.get(ctx.stageOrder[fromIndex - 1]).operationsByKeyAfter
  );
  const stageWarnings = [];
  const stageOps = scheduleStage(seed, ctx.master, process2, ctx.sources, currentOperationsByKey, stageWarnings, ctx.includeInterruptedCandidates);
  const stageResults = new Map(ctx.stageResults);
  stageResults.set(process2, {
    operations: stageOps,
    warnings: stageWarnings,
    operationsByKeyAfter: new Map(currentOperationsByKey)
  });
  if (lastDownstreamExecution && lastDownstreamExecution.ctx === ctx) {
    lastDownstreamExecution.stageKeys.set(process2, downstreamStageInputKey(seed, process2, fullOrder));
    lastDownstreamExecution.stageResults.set(process2, stageResults.get(process2));
    for (let i = fromIndex + 1; i < ctx.stageOrder.length; i += 1) {
      lastDownstreamExecution.stageKeys.delete(ctx.stageOrder[i]);
    }
    lastDownstreamExecution.plan = void 0;
  }
  const operations = [
    ...baseline.operations.filter((item) => item.process !== process2 || item.actual),
    ...stageOps
  ].sort((left, right) => left.start - right.start || left.sequence - right.sequence || Number(right.actual) - Number(left.actual) || left.id.localeCompare(right.id));
  const warnings = [...ctx.baseWarnings];
  for (let i = 0; i <= fromIndex; i += 1) {
    warnings.push(...stageResults.get(ctx.stageOrder[i])?.warnings ?? []);
  }
  const plan = { ...baseline, operations, warnings };
  stagePlanContexts.set(plan, { ...ctx, stageResults });
  return plan;
}
function buildDownstreamProcessPlanFromStage(seed, result, baseline, fromProcess) {
  const ctx = stagePlanContexts.get(baseline);
  const fullOrder = productionProcessOrder(seed);
  const stageOrder = fullOrder.filter((item) => item !== "turning");
  const fromIndex = ctx ? ctx.stageOrder.indexOf(fromProcess) : -1;
  if (!ctx || ctx.master !== (seed.processMasterData ?? ctx.master) || fromIndex < 0 || ctx.stageOrder.join("|") !== stageOrder.join("|")) {
    return buildDownstreamProcessPlan(seed, result);
  }
  const stageResults = /* @__PURE__ */ new Map();
  const stageKeys = /* @__PURE__ */ new Map();
  for (let i = 0; i < fromIndex; i += 1) {
    const prior = ctx.stageOrder[i];
    stageResults.set(prior, ctx.stageResults.get(prior));
    stageKeys.set(prior, downstreamStageInputKey(seed, prior, fullOrder));
  }
  let startIndex = fromIndex;
  const targetStageKey = downstreamStageInputKey(seed, fromProcess, fullOrder);
  if (lastDownstreamExecution && lastDownstreamExecution.ctx === ctx && lastDownstreamExecution.stageKeys.get(fromProcess) === targetStageKey && lastDownstreamExecution.stageResults.has(fromProcess)) {
    stageResults.set(fromProcess, lastDownstreamExecution.stageResults.get(fromProcess));
    stageKeys.set(fromProcess, targetStageKey);
    startIndex = fromIndex + 1;
  }
  const currentOperationsByKey = new Map(
    startIndex === 0 ? ctx.baseOperationsByKey : stageResults.get(ctx.stageOrder[startIndex - 1]).operationsByKeyAfter
  );
  for (let i = startIndex; i < ctx.stageOrder.length; i += 1) {
    const process2 = ctx.stageOrder[i];
    const stageWarnings = [];
    const stageOps = scheduleStage(seed, ctx.master, process2, ctx.sources, currentOperationsByKey, stageWarnings, ctx.includeInterruptedCandidates);
    stageResults.set(process2, {
      operations: stageOps,
      warnings: stageWarnings,
      operationsByKeyAfter: new Map(currentOperationsByKey)
    });
    stageKeys.set(process2, downstreamStageInputKey(seed, process2, fullOrder));
  }
  const plan = finalizeDownstreamProcessPlan(seed, result, ctx, stageResults);
  if (lastDownstreamExecution && lastDownstreamExecution.ctx === ctx) {
    lastDownstreamExecution.stageKeys = stageKeys;
    lastDownstreamExecution.stageResults = stageResults;
    lastDownstreamExecution.plan = plan;
  }
  return plan;
}
function buildDownstreamProcessPlan(seed, result, includeInterruptedCandidates = false) {
  const baseKey = downstreamBaseInputKey(seed, result);
  const fullOrder = productionProcessOrder(seed);
  const canReuseBase = Boolean(
    lastDownstreamExecution && lastDownstreamExecution.baseKey === baseKey && lastDownstreamExecution.includeInterruptedCandidates === includeInterruptedCandidates
  );
  const ctx = canReuseBase ? lastDownstreamExecution.ctx : buildDownstreamBaseContext(seed, result, includeInterruptedCandidates);
  const stageResults = /* @__PURE__ */ new Map();
  const stageKeys = /* @__PURE__ */ new Map();
  let firstChangedIndex = 0;
  if (canReuseBase) {
    while (firstChangedIndex < ctx.stageOrder.length) {
      const process2 = ctx.stageOrder[firstChangedIndex];
      const key = downstreamStageInputKey(seed, process2, fullOrder);
      const cached = lastDownstreamExecution.stageResults.get(process2);
      if (lastDownstreamExecution.stageKeys.get(process2) !== key || !cached) break;
      stageResults.set(process2, cached);
      stageKeys.set(process2, key);
      firstChangedIndex += 1;
    }
    if (firstChangedIndex === ctx.stageOrder.length && lastDownstreamExecution.plan) {
      return lastDownstreamExecution.plan;
    }
  }
  const currentOperationsByKey = new Map(
    firstChangedIndex === 0 ? ctx.baseOperationsByKey : stageResults.get(ctx.stageOrder[firstChangedIndex - 1]).operationsByKeyAfter
  );
  for (let i = firstChangedIndex; i < ctx.stageOrder.length; i += 1) {
    const process2 = ctx.stageOrder[i];
    const stageWarnings = [];
    const stageOps = scheduleStage(seed, ctx.master, process2, ctx.sources, currentOperationsByKey, stageWarnings, includeInterruptedCandidates);
    stageResults.set(process2, {
      operations: stageOps,
      warnings: stageWarnings,
      operationsByKeyAfter: new Map(currentOperationsByKey)
    });
    stageKeys.set(process2, downstreamStageInputKey(seed, process2, fullOrder));
  }
  const plan = finalizeDownstreamProcessPlan(seed, result, ctx, stageResults);
  lastDownstreamExecution = {
    baseKey,
    includeInterruptedCandidates,
    ctx,
    stageKeys,
    stageResults,
    plan
  };
  return plan;
}

// lib/delivery-readiness.ts
function datedEvents(seed, result, processPlan) {
  const representedBatchIds = /* @__PURE__ */ new Set([
    ...processPlan.jobs.filter((job) => job.source === "turning-plan" && Boolean(seed.processMasterData)).map((job) => job.batchId),
    ...(seed.wipLots ?? []).map((lot) => lot.sourceBatchId).filter(Boolean)
  ]);
  const representedLotIds = new Set(processPlan.jobs.filter((job) => job.source === "wip" && job.deliveryReadyAt > 0).map((job) => job.batchId));
  const filterQuantities = seed.productionArea === "cubuk-filtre" ? new Map(filterCommittedSupply(seed, result.batches).map((row) => [row.id, row.quantity])) : void 0;
  const routed = processPlan.jobs.filter((job) => {
    const lot = seed.wipLots?.find((item) => item.id === job.wipLotId);
    return !lot || lot.stage !== "on-hold" && lot.stage !== "unclassified";
  }).filter((job) => job.quantity > 0 && job.deliveryReadyAt > 0 && (Boolean(processMasterDataForProduct(seed.processMasterData, job.product)?.route) || job.operations.some((operation) => operation.process === "gkm") || (seed.wipLots ?? []).some((lot) => lot.id === job.wipLotId && lot.stage === "delivery-ready"))).map((job) => ({ id: `route:${job.batchId}`, product: job.product.toUpperCase(), quantity: filterQuantities?.get(job.source === "wip" ? `wip:${job.wipLotId}` : job.source === "current-turning" ? `current:${job.turningMachineId}` : `batch:${job.batchId}`) ?? filterSupplyGoodPieces(seed, job.product, job.quantity, Boolean(seed.wipLots?.find((lot) => lot.id === job.wipLotId && lot.stage === "delivery-ready"))), readyAt: job.deliveryReadyAt, source: "routed", routeSource: job.source, wipLotId: job.wipLotId }));
  const fallbackBatches = result.batches.filter((batch) => !seed.processMasterData && batch.status === "planned" && !hasActiveProductionInterruption(seed, batch.id, batch.interruptionId) && batch.quantity > 0 && batch.end > 0 && !representedBatchIds.has(batch.id)).map((batch) => ({ id: `batch:${batch.id}`, product: batch.product.toUpperCase(), quantity: batch.quantity, readyAt: turningDeliveryReadyAt(batch.end), source: "turning-fallback" }));
  const fallbackReadyWip = (seed.wipLots ?? []).filter((lot) => !seed.processMasterData && lot.stage === "delivery-ready" && lot.availableQuantity > 0 && lot.readyAt > 0 && !representedLotIds.has(lot.id)).map((lot) => ({ id: `wip:${lot.id}`, product: lot.product.toUpperCase(), quantity: lot.availableQuantity, readyAt: lot.readyAt, source: "wip-fallback" }));
  return [...routed, ...fallbackBatches, ...fallbackReadyWip].filter((event) => Number.isFinite(event.readyAt) && event.readyAt > 0).sort((left, right) => left.readyAt - right.readyAt || left.id.localeCompare(right.id));
}
function buildDeliveryReadinessEvents(seed, result, plan = buildDownstreamProcessPlan(seed, result)) {
  return datedEvents(seed, result, plan);
}
function deliveryReadyQuantityByDate(seed, result, product, serial2) {
  return deliveryReadyQuantityFromEvents(seed, buildDeliveryReadinessEvents(seed, result), product, serial2);
}
function deliveryReadyQuantityFromEvents(seed, events, product, serial2) {
  const code3 = product.trim().toUpperCase();
  const dueDay = Math.floor(serial2);
  const openingStock = seed.customerDemand ? 0 : Math.max(0, seed.openingStock?.[code3] ?? 0);
  return openingStock + events.filter((event) => event.product === code3 && Math.floor(event.readyAt) <= dueDay).reduce((sum, event) => sum + event.quantity, 0);
}

// lib/parameter-deactivation.ts
var code = (value) => value.trim().toUpperCase();
var clone = (value) => structuredClone(value);
var label = (target) => `${target.product} \xD7 ${target.resourceId} (${target.process === "turning" ? "Torna" : processLabel(target.process)})`;
function downstreamParameter(seed, product, process2) {
  return seed.processMasterData?.products.find((item) => code(item.product) === code(product))?.processes.find((item) => item.process === process2);
}
function isAssignmentPasif(seed, target) {
  if (target.process === "turning") return Boolean(seed.products.find((item) => code(item.product) === code(target.product))?.inactiveMachineIds?.includes(target.resourceId));
  return Boolean(downstreamParameter(seed, target.product, target.process)?.inactiveResourceIds?.includes(target.resourceId));
}
function setAssignmentPasif(seed, target) {
  if (target.process === "turning") {
    const product = seed.products.find((item) => code(item.product) === code(target.product));
    if (!product) throw new Error(`${target.product} Torna parametresi bulunamad\u0131.`);
    product.inactiveMachineIds = [.../* @__PURE__ */ new Set([...product.inactiveMachineIds ?? [], target.resourceId])];
    return;
  }
  const parameter = downstreamParameter(seed, target.product, target.process);
  if (!parameter || !parameter.resourcePriority.includes(target.resourceId)) throw new Error(`${label(target)} atamas\u0131 Parametreler\u2019de bulunamad\u0131.`);
  parameter.inactiveResourceIds = [.../* @__PURE__ */ new Set([...parameter.inactiveResourceIds ?? [], target.resourceId])];
}
function turningMoveTargets(seed, target) {
  return seed.machines.filter((machine) => machine.id !== target.resourceId && machine.active && machine.shiftFactor > 0 && (machine.rates[code(target.product)] ?? 0) > 0 && isMachineEligibleForProduct(seed, machine.id, target.product)).map((machine) => machine.id);
}
function downstreamMoveTargets(seed, target) {
  const product = seed.processMasterData?.products.find((item) => code(item.product) === code(target.product));
  const parameter = downstreamParameter(seed, target.product, target.process);
  if (!product || !parameter) return [];
  return activeProcessResourceIds(parameter).filter((id) => {
    const resource = seed.processMasterData?.resources.find((item) => item.id === id);
    const hasSetup = seed.productionArea !== "cubuk-filtre" || Number.isFinite(parameter.setupMinutesByResource?.[id]);
    return id !== target.resourceId && resource?.active && resource.process === target.process && resource.defaultShifts > 0 && resourceSupportsProcessProduct(resource, product) && (parameter.unitsPerShift[id] ?? 0) > 0 && hasSetup;
  });
}
function referencedByLaterWork(seed, batchId) {
  return Boolean(seed.wipLots?.some((lot) => lot.sourceBatchId === batchId) || seed.processOperationOverrides?.some((item) => item.batchId === batchId) || seed.processCurrentJobs?.some((item) => item.batchId === batchId) || seed.productionHistory?.some((item) => item.sourceBatchId === batchId));
}
function signatureOf(running, queued) {
  return JSON.stringify([...running, ...queued].map((job) => [job.key, job.resourceId, job.quantity, job.start, job.end, job.locked]));
}
function parameterDeactivationImpact(seed, result, target) {
  const after = clone(seed);
  if (!isAssignmentPasif(after, target)) setAssignmentPasif(after, target);
  const running = [];
  const queued = [];
  if (target.process === "turning") {
    const machine = seed.machines.find((item) => item.id === target.resourceId);
    if (!machine) throw new Error(`${target.resourceId} tezgah\u0131 bulunamad\u0131.`);
    const current = machine.currentJob;
    if (current.quantity > 0 && code(current.product) === code(target.product)) running.push({
      key: `turning:current:${machine.id}`,
      kind: "running",
      process: "turning",
      product: current.product,
      resourceId: machine.id,
      batchId: current.batchId ?? `current:${machine.id}`,
      workOrder: current.workOrder,
      quantity: current.remainingQuantity ?? current.quantity,
      start: current.start,
      end: current.end,
      locked: true,
      protectedRemainder: false,
      pinned: true,
      allowedDecisions: [],
      moveTargets: []
    });
    const baseMoveTargets = turningMoveTargets(after, target);
    for (const batch of result.batches.filter((item) => item.status === "planned" && item.machineId === target.resourceId && code(item.product) === code(target.product)).sort((a, b) => a.planColumn - b.planColumn)) {
      const protectedRemainder = hasProtectedProductionRemainder(seed, batch.id, batch.interruptionId);
      const sharedId = batch.sharedCharge?.id;
      const siblingMachines = sharedId ? /* @__PURE__ */ new Set([
        ...result.batches.filter((item) => item.id !== batch.id && item.sharedCharge?.id === sharedId).map((item) => item.machineId),
        ...seed.machines.filter((item) => item.currentJob.quantity > 0 && item.currentJob.sharedCharge?.id === sharedId).map((item) => item.id)
      ]) : /* @__PURE__ */ new Set();
      const splitShared = siblingMachines.size > 0;
      const moveTargets = splitShared ? baseMoveTargets.filter((id) => !siblingMachines.has(id)) : baseMoveTargets;
      const removable = !splitShared && !batch.locked && !protectedRemainder && !batch.routeCommitted && !referencedByLaterWork(seed, batch.id);
      queued.push({
        key: `turning:${batch.id}`,
        kind: "queued",
        process: "turning",
        product: batch.product,
        resourceId: batch.machineId,
        batchId: batch.id,
        workOrder: batch.workOrder?.trim() ?? "",
        quantity: batch.quantity,
        start: batch.start,
        end: batch.end,
        locked: Boolean(batch.locked),
        protectedRemainder,
        pinned: true,
        allowedDecisions: [...moveTargets.length ? ["move"] : [], ...removable ? ["remove"] : []],
        moveTargets
      });
    }
  } else {
    const process2 = target.process;
    const visible = clone(seed);
    const parameter = downstreamParameter(visible, target.product, process2);
    if (parameter) parameter.inactiveResourceIds = parameter.inactiveResourceIds?.filter((id) => id !== target.resourceId);
    const plan = buildDownstreamProcessPlan(visible, result);
    const moveTargets = downstreamMoveTargets(after, { ...target, process: process2 });
    for (const operation of plan.operations.filter((item) => item.process === process2 && item.resourceId === target.resourceId && code(item.product) === code(target.product) && !item.actual)) {
      const pinned = Boolean(seed.processOperationOverrides?.some((item) => item.batchId === operation.batchId && item.process === process2 && item.resourceId === target.resourceId && item.routeMode !== "automatic"));
      const job = {
        key: `${process2}:${operation.batchId}`,
        kind: operation.current ? "running" : "queued",
        process: process2,
        product: operation.product,
        resourceId: operation.resourceId,
        batchId: operation.batchId,
        workOrder: operation.workOrder,
        quantity: operation.quantity,
        start: operation.start,
        end: operation.end,
        locked: Boolean(operation.current),
        protectedRemainder: false,
        pinned,
        allowedDecisions: operation.current ? [] : [...moveTargets.length ? ["move"] : [], "release-to-automatic"],
        moveTargets: operation.current ? [] : moveTargets
      };
      (operation.current ? running : queued).push(job);
    }
  }
  return { target, running, queued, signature: signatureOf(running, queued) };
}
function applyParameterDeactivation(seed, result, target, decisions, signature) {
  const impact = parameterDeactivationImpact(seed, result, target);
  if (impact.signature !== signature) throw new Error("Plan de\u011Fi\u015Fti; etkilenen i\u015Fleri yeniden inceleyin.");
  const byKey = /* @__PURE__ */ new Map();
  for (const decision of decisions) {
    if (byKey.has(decision.key)) throw new Error(`${label(target)}: ${decision.key} i\xE7in birden fazla karar var.`);
    byKey.set(decision.key, decision);
  }
  const unknown = decisions.find((decision) => !impact.queued.some((job) => job.key === decision.key));
  if (unknown) throw new Error(`${label(target)}: ${unknown.key} etkilenen kuyruk i\u015Fleri aras\u0131nda de\u011Fil.`);
  for (const job of impact.queued) {
    const decision = byKey.get(job.key);
    const trace = `${job.product} \xB7 ${job.workOrder || job.batchId} \xB7 ${job.resourceId}`;
    if (!decision) throw new Error(`Parametreler: ${label(target)} Pasif yap\u0131lamad\u0131. ${trace} kuyrukta bekliyor; bu i\u015F i\xE7in karar se\xE7in.`);
    if (!job.allowedDecisions.includes(decision.kind)) throw new Error(`Parametreler: ${trace} i\xE7in \u201C${decision.kind}\u201D karar\u0131 uygun de\u011Fil${job.locked ? " (kilitli i\u015F)" : ""}${job.protectedRemainder ? " (yar\u0131m kalan i\u015F)" : ""}.`);
    if (decision.kind === "move" && !job.moveTargets.includes(decision.targetResourceId ?? "")) throw new Error(`Parametreler: ${trace} i\xE7in se\xE7ilen hedef ${decision.targetResourceId || "\u2014"} aktif ve uygun de\u011Fil.`);
  }
  const nextSeed = clone(seed);
  setAssignmentPasif(nextSeed, target);
  let nextResult = { ...result, batches: result.batches.map((batch) => ({ ...batch })) };
  const updatedAt = (/* @__PURE__ */ new Date()).toISOString();
  if (target.process === "turning") {
    let batches = nextResult.batches;
    for (const job of impact.queued) {
      const decision = byKey.get(job.key);
      if (decision.kind === "remove") batches = batches.filter((batch) => batch.id !== job.batchId);
      if (decision.kind === "move") {
        const tail = Math.max(12, ...batches.filter((batch) => batch.status === "planned" && batch.machineId === decision.targetResourceId).map((batch) => batch.planColumn));
        batches = batches.map((batch) => {
          if (batch.id !== job.batchId) return batch;
          const { linkedStart: _linked, ...rest } = batch;
          return { ...rest, machineId: decision.targetResourceId, planColumn: tail + 1 };
        });
      }
    }
    const touched = /* @__PURE__ */ new Set([target.resourceId, ...[...byKey.values()].map((item) => item.targetResourceId).filter(Boolean)]);
    const recalculated = recalculateManualScenario({ ...nextSeed, machines: nextSeed.machines.filter((machine) => touched.has(machine.id)) }, batches.filter((batch) => touched.has(batch.machineId) && batch.status === "planned"));
    const byId = new Map(recalculated.batches.map((batch) => [batch.id, batch]));
    const merged = batches.map((batch) => byId.get(batch.id) ?? batch);
    nextResult = { ...scenarioResultFromBatches(nextSeed, merged), planRun: result.planRun ?? seed.activePlanRun };
  } else {
    const process2 = target.process;
    for (const job of impact.queued) {
      const decision = byKey.get(job.key);
      nextSeed.processOperationOverrides = (nextSeed.processOperationOverrides ?? []).filter((item) => !(item.batchId === job.batchId && item.process === process2));
      nextSeed.processOperationOverrides.push(decision.kind === "move" ? { batchId: job.batchId, process: process2, resourceId: decision.targetResourceId, requestedStart: job.start, routeMode: "manual", sourceProduct: job.product, updatedAt } : { batchId: job.batchId, process: process2, resourceId: target.resourceId, requestedStart: job.start, routeMode: "automatic", sourceProduct: job.product, updatedAt });
    }
  }
  nextSeed.planNeedsRecalculation = true;
  const moved = impact.queued.filter((job) => byKey.get(job.key)?.kind === "move").length;
  const removed = impact.queued.filter((job) => byKey.get(job.key)?.kind === "remove").length;
  const released = impact.queued.length - moved - removed;
  return {
    seed: nextSeed,
    result: nextResult,
    summary: `${label(target)} Pasif \xB7 ${impact.running.length} \xE7al\u0131\u015Fan i\u015F korundu \xB7 ${moved} ta\u015F\u0131nd\u0131 \xB7 ${released} otomatik planlamaya b\u0131rak\u0131ld\u0131 \xB7 ${removed} plandan \xE7\u0131kar\u0131ld\u0131`
  };
}
function pasifTargets(seed) {
  const targets = [];
  for (const product of seed.products) for (const resourceId of product.inactiveMachineIds ?? []) targets.push({ process: "turning", product: product.product, resourceId });
  for (const product of seed.processMasterData?.products ?? []) for (const parameter of product.processes) {
    for (const resourceId of parameter.inactiveResourceIds ?? []) targets.push({ process: parameter.process, product: product.product, resourceId });
  }
  return targets;
}
var targetKey = (target) => `${target.process}|${code(target.product)}|${target.resourceId}`;
function assertParameterTransitionDecided(before, after, batches = after.manualBatches ?? []) {
  const previous = new Set(pasifTargets(before).map(targetKey));
  const problems = [];
  for (const target of pasifTargets(after).filter((item) => !previous.has(targetKey(item)))) {
    if (target.process === "turning") {
      for (const batch of batches.filter((item) => item.status === "planned" && item.machineId === target.resourceId && code(item.product) === code(target.product))) {
        problems.push(`${batch.product} \xB7 ${batch.workOrder?.trim() || batch.id} \xB7 ${batch.machineId} (Torna${batch.locked ? ", kilitli" : ""})`);
      }
    } else {
      const process2 = target.process;
      const visible = { ...before, manualBatches: batches };
      const affected = parameterDeactivationImpact(visible, { batches }, target).queued;
      for (const job of affected) {
        const decided = after.processOperationOverrides?.some((item) => item.batchId === job.batchId && item.process === process2 && (item.routeMode === "automatic" || item.resourceId !== target.resourceId));
        if (!decided) problems.push(`${job.product} \xB7 ${job.workOrder || job.batchId} \xB7 ${job.resourceId} (${processLabel(process2)}${job.pinned ? ", elle yerle\u015Fim" : ""})`);
      }
    }
  }
  if (problems.length) {
    throw new Error(`Parametreler: Pasif yap\u0131lan atamada kuyruktaki i\u015Fler i\xE7in karar gerekiyor. ${problems.slice(0, 5).join("; ")}${problems.length > 5 ? ` ve ${problems.length - 5} i\u015F daha` : ""}. \u201CPasif yapmadan \xF6nce etkilenen i\u015Fler\u201D penceresinden her i\u015F i\xE7in karar verin.`);
  }
}

// data/product-setup-families.json
var product_setup_families_default = {
  "center-pin": [
    "R902747824",
    "R902970729",
    "R902719738",
    "R902719052",
    "R902719743",
    "R902719740",
    "R902719739",
    "R902970277",
    "R902725682",
    "R902970039",
    "R902375400",
    "R902748350",
    "R902719742",
    "R902729941",
    "R902970964",
    "R902719741",
    "R902719765",
    "R902719764",
    "R902744004",
    "R902719763",
    "R902719766",
    "R902719767",
    "R902729695"
  ],
  piston: [
    "R902745143",
    "R902745138",
    "R902747620",
    "R902745121",
    "R902745149",
    "R902745145",
    "R902747621",
    "R902970515",
    "R902970275",
    "R902745163",
    "R902745169",
    "R902745119",
    "R902745133",
    "R902719812",
    "R902745116",
    "R902745129",
    "R902745135",
    "R902745117",
    "R902745123",
    "R902745127",
    "R902745161",
    "R902970516",
    "R902745147",
    "R902745131",
    "R902970513",
    "R902970276",
    "R902745165",
    "R902970862",
    "R902970233",
    "R902970514",
    "R902970517",
    "R902970863"
  ]
};

// lib/setup-families.ts
var FAMILY_VALUES = /* @__PURE__ */ new Set(["center-pin", "piston", "cubuk-filtre"]);
var catalog = { ...product_setup_families_default, "cubuk-filtre": [] };
var familyByProduct = /* @__PURE__ */ new Map();
for (const family of ["center-pin", "piston"]) {
  for (const rawProduct of catalog[family]) {
    const product = rawProduct.trim().toUpperCase();
    const existing = familyByProduct.get(product);
    if (existing && existing !== family) throw new Error(`${product} hem ${existing} hem ${family} setup ailesinde tan\u0131ml\u0131.`);
    familyByProduct.set(product, family);
  }
}
function normalizeProductSetupFamily(value) {
  return typeof value === "string" && FAMILY_VALUES.has(value) ? value : void 0;
}
function catalogProductSetupFamily(productCode) {
  return familyByProduct.get(productCode.trim().toUpperCase());
}
function resolvedProductSetupFamily(productCode, storedFamily) {
  return normalizeProductSetupFamily(storedFamily) ?? catalogProductSetupFamily(productCode);
}

// lib/cubuk-filtre-parameters.ts
function validateFilterShipment(seed, code3, quantity) {
  if (seed.productionArea !== "cubuk-filtre") return;
  const product = seed.products.find((p) => p.product === code3);
  if (!product || product.moq <= 0) throw new Error("Min. Sevkiyat Adedi tan\u0131mlanmal\u0131.");
  if (quantity < product.moq || (product.shipmentMultiple ?? 0) > 0 && quantity % product.shipmentMultiple !== 0) throw new Error("Teslim adedi Min. Sevkiyat Adedi ve Sevkiyat Kat\u0131 kural\u0131na uymuyor.");
}

// lib/plan-reset.ts
function withoutRouteChoices(batch) {
  const { routeCommitted: _commitment, routeTargetDate: _target, linkedStart: _linkedStart, ...retained } = batch;
  return retained;
}
var processOverrideKey = (row) => JSON.stringify([row.batchId, row.process]);
function resetFutureProcessOverrides(seed) {
  const currentKeys = new Set((seed.processCurrentJobs ?? []).map(processOverrideKey));
  const kept = (seed.processOperationOverrides ?? []).filter((row) => currentKeys.has(processOverrideKey(row))).map((row) => ({ ...row }));
  for (const lot of seed.wipLots ?? []) {
    const identities = processPlacementIdentities(seed, lot.id).slice(1);
    for (const inherited of kept.slice()) {
      const key = processOverrideKey({ batchId: lot.id, process: inherited.process });
      if (currentKeys.has(key) || kept.some((row) => processOverrideKey(row) === key) || !identities.includes(inherited.batchId) || inherited.sourceCurrentJobKey || inherited.sourceProduct && inherited.sourceProduct !== lot.product) continue;
      kept.push({
        batchId: lot.id,
        process: inherited.process,
        resourceId: inherited.resourceId,
        requestedStart: inherited.requestedStart,
        updatedAt: inherited.updatedAt,
        sourceProduct: lot.product,
        routeMode: "automatic"
      });
    }
  }
  return kept;
}
function mergeResetProcessOverrides(draft, live) {
  const currentKeys = new Set((live.processCurrentJobs ?? []).map(processOverrideKey));
  const protectedRows = resetFutureProcessOverrides(live);
  const proposed = (draft.processOperationOverrides ?? []).filter((row) => !currentKeys.has(processOverrideKey(row)));
  const proposedKeys = new Set(proposed.map(processOverrideKey));
  return [...protectedRows.filter((row) => currentKeys.has(processOverrideKey(row)) || !proposedKeys.has(processOverrideKey(row))), ...proposed];
}

// lib/planning.ts
function shortageExtraChargePolicyForSeed(seed) {
  return normalizeShortageExtraChargePolicy(seed.activePlanRun?.shortageExtraCharge);
}
function normalizeShortageExtraChargePolicy(policy) {
  const normalized = policy ?? { enabled: true, thresholdPercent: 50 };
  if (!Number.isFinite(normalized.thresholdPercent) || normalized.thresholdPercent < 0 || normalized.thresholdPercent > 100) {
    throw new Error("Eksik \u015Farj e\u015Fi\u011Fi 0 ile 100 aras\u0131nda olmal\u0131d\u0131r.");
  }
  return { enabled: Boolean(normalized.enabled), thresholdPercent: normalized.thresholdPercent };
}
function productionTargetForShortage(quantity, batchSize, policy) {
  if (batchSize <= 0) return quantity;
  const safeQuantity = Math.max(0, quantity);
  const wholeLots = Math.floor(safeQuantity / batchSize);
  const residual = safeQuantity - wholeLots * batchSize;
  const normalized = normalizeShortageExtraChargePolicy(policy);
  const reachesThreshold = residual > 1e-7 && residual / batchSize * 100 + 1e-7 >= normalized.thresholdPercent;
  return (wholeLots + (normalized.enabled && reachesThreshold ? 1 : 0)) * batchSize;
}
function diameterNumeric(value) {
  const match = value.replace(",", ".").match(/\d+(?:\.\d+)?/);
  return match ? Number(match[0]) : 0;
}
function excelSerialToDate(serial2) {
  return new Date(Date.UTC(1899, 11, 30) + serial2 * 864e5);
}
var excelDateFormatters = /* @__PURE__ */ new Map();
var MAX_EXCEL_DATE_FORMATTERS = 32;
function formatExcelDate(serial2, options) {
  if (!serial2 || !Number.isFinite(serial2)) return "\u2014";
  const formatOptions = { ...options ?? { day: "2-digit", month: "short", year: "numeric" }, timeZone: "UTC" };
  const key = JSON.stringify(Object.entries(formatOptions).sort(([left], [right]) => left.localeCompare(right)));
  let formatter = excelDateFormatters.get(key);
  if (!formatter) formatter = new Intl.DateTimeFormat("tr-TR", formatOptions);
  else excelDateFormatters.delete(key);
  excelDateFormatters.set(key, formatter);
  if (excelDateFormatters.size > MAX_EXCEL_DATE_FORMATTERS) excelDateFormatters.delete(excelDateFormatters.keys().next().value);
  return formatter.format(excelSerialToDate(serial2));
}
function addWorkdays(startSerial, daysValue, holidays, offset) {
  let serial2 = Math.floor(startSerial);
  let remaining = Math.max(0, Math.trunc(daysValue));
  while (remaining > 0) {
    serial2 += 1;
    const day = excelSerialToDate(serial2).getUTCDay();
    if (day !== 0 && !holidays.has(serial2)) remaining -= 1;
  }
  return serial2 + offset;
}
function shiftCount(value) {
  if (!Number.isFinite(value)) return 0;
  return Math.max(0, Math.min(3, Math.trunc(value)));
}
function machineDayCapacity(seed, machine, serialValue) {
  const serial2 = Math.floor(serialValue);
  const events = (seed.calendarEvents ?? []).filter((event) => event.machineId === machine.id && serial2 >= Math.floor(event.start) && serial2 <= Math.floor(event.end));
  const maintenance = events.find((event) => event.kind === "maintenance");
  if (maintenance) return { shifts: 0, kind: "maintenance", label: maintenance.name || "Planl\u0131 bak\u0131m" };
  const shiftOverride = [...events].reverse().find((event) => event.kind === "shift");
  if (shiftOverride) return { shifts: shiftCount(shiftOverride.shiftCount), kind: "shift", label: shiftOverride.name || "Vardiya de\u011Fi\u015Fikli\u011Fi" };
  const holiday = seed.holidays.find((item) => Math.floor(item.serial) === serial2);
  if (holiday) {
    const shifts = shiftCount(holiday.workingShifts);
    return { shifts, kind: "holiday", label: shifts ? `${holiday.name} \xB7 ${shifts} vardiya` : holiday.name };
  }
  if (excelSerialToDate(serial2).getUTCDay() === 0) return { shifts: 0, kind: "sunday", label: "Pazar \xB7 \xFCretim yok" };
  return { shifts: shiftCount(machine.shiftFactor), kind: "normal", label: `${shiftCount(machine.shiftFactor)} vardiya` };
}
function addMachineWorkdays(seed, machine, startSerial, daysValue, offset) {
  const defaultShifts = shiftCount(machine.shiftFactor);
  if (defaultShifts <= 0) return addWorkdays(startSerial, daysValue, new Set(seed.holidays.map((holiday) => Math.floor(holiday.serial))), offset);
  let serial2 = Math.floor(startSerial);
  let remainingShiftUnits = Math.max(0, Math.trunc(daysValue)) * defaultShifts;
  let guard = 0;
  while (remainingShiftUnits > 0) {
    serial2 += 1;
    remainingShiftUnits -= machineDayCapacity(seed, machine, serial2).shifts;
    guard += 1;
    if (guard > 36600) throw new Error(`${machine.id} i\xE7in \xE7al\u0131\u015F\u0131labilir takvim g\xFCn\xFC bulunamad\u0131.`);
  }
  return serial2 + offset;
}
function normalizedDiameter(value) {
  return value.toUpperCase().replace("\xD8", "").replace(/MM/g, "").replace(/\s/g, "").replace(".", ",");
}
function isProductCode(value, seed) {
  return /^R.{7,}$/i.test(value.trim()) || seed?.productionArea === "cubuk-filtre" && seed.products.some((product) => product.product.toUpperCase() === value.trim().toUpperCase());
}
function unique(values) {
  return [...new Set(values)];
}
function machineCapacityFactor(machine) {
  return Number.isFinite(machine.capacityFactor) ? machine.capacityFactor : 1;
}
var DEFAULT_SETUP_SETTINGS = {
  model: "product-family",
  shiftHours: 8,
  sameDiameterHours: 1,
  differentDiameterHours: 3,
  sameFamilyDifferentDiameterHours: 2,
  crossFamilyHours: 5
};
function getSetupSettings(seed) {
  const source = seed.setupSettings ?? DEFAULT_SETUP_SETTINGS;
  const model = source.model === "diameter-only" ? "diameter-only" : "product-family";
  const nonNegative = (value, fallback) => Number.isFinite(value) ? Math.max(0, Number(value)) : fallback;
  return {
    model,
    shiftHours: Math.max(1, Math.min(24, nonNegative(source.shiftHours, DEFAULT_SETUP_SETTINGS.shiftHours))),
    sameDiameterHours: nonNegative(source.sameDiameterHours, DEFAULT_SETUP_SETTINGS.sameDiameterHours),
    differentDiameterHours: nonNegative(source.differentDiameterHours, DEFAULT_SETUP_SETTINGS.differentDiameterHours),
    sameFamilyDifferentDiameterHours: nonNegative(source.sameFamilyDifferentDiameterHours, DEFAULT_SETUP_SETTINGS.sameFamilyDifferentDiameterHours),
    crossFamilyHours: nonNegative(source.crossFamilyHours, DEFAULT_SETUP_SETTINGS.crossFamilyHours)
  };
}
function productSetupFamily(seed, productCode) {
  const code3 = productCode.trim().toUpperCase();
  const storedFamily = seed.products.find((product) => product.product.trim().toUpperCase() === code3)?.setupFamily;
  return resolvedProductSetupFamily(code3, storedFamily);
}
function setupTypeRank(type) {
  if (type === "same-product") return 0;
  if (type === "same-diameter") return 1;
  if (type === "same-family") return 2;
  if (type === "different-diameter") return 3;
  if (type === "cross-family") return 4;
  return 5;
}
function calculateSetup(seed, previousProduct, previousDiameter, nextProduct, nextDiameter, machineId) {
  const configured = seed.products.find((p) => p.product === nextProduct);
  if (configured?.turningSetupMinutes) {
    const minutes = configured.turningSetupMinutes[machineId ?? ""];
    if (!Number.isFinite(minutes)) throw new Error(`${nextProduct} \xB7 ${machineId} setup s\xFCresi eksik.`);
    return {
      hours: ((previousProduct === nextProduct ? 0 : minutes) + (configured.handlingMinutes ?? 0)) / 60,
      type: previousProduct === nextProduct ? "same-product" : "different-diameter",
      label: "Operasyon rotas\u0131 setup + i\u015F emri haz\u0131rl\u0131\u011F\u0131"
    };
  }
  const settings = getSetupSettings(seed);
  const previousCode = previousProduct.trim().toUpperCase();
  const nextCode = nextProduct.trim().toUpperCase();
  const previous = normalizedDiameter(previousDiameter);
  const next = normalizedDiameter(nextDiameter);
  if (previousCode && nextCode && previousCode === nextCode) return { hours: 0, type: "same-product", label: "Ayn\u0131 \xFCr\xFCn \xB7 setup yok" };
  if (settings.model === "product-family" && previousCode && nextCode) {
    const previousFamily = productSetupFamily(seed, previousCode);
    const nextFamily = productSetupFamily(seed, nextCode);
    if (previousFamily && nextFamily && previousFamily !== nextFamily) {
      return { hours: settings.crossFamilyHours, type: "cross-family", label: "Center Pin \u2194 piston ge\xE7i\u015Fi" };
    }
    if (previous && next && previous === next) return { hours: settings.sameDiameterHours, type: "same-diameter", label: "Farkl\u0131 \xFCr\xFCn \xB7 ayn\u0131 \xE7ap" };
    if (previousFamily && nextFamily && previousFamily === nextFamily) {
      return { hours: settings.sameFamilyDifferentDiameterHours, type: "same-family", label: "Ayn\u0131 aile \xB7 farkl\u0131 \xE7ap" };
    }
  }
  if (previous && next && previous === next) return { hours: settings.sameDiameterHours, type: "same-diameter", label: "Ayn\u0131 \xE7ap setup" };
  return { hours: settings.differentDiameterHours, type: "different-diameter", label: "Farkl\u0131 \xE7ap / ba\u015Flang\u0131\xE7 setup" };
}
function machineRunHours(seed, machine, productCode, quantity) {
  const shiftRate = machine.rates[productCode.toUpperCase()] ?? 0;
  const hourlyRate = shiftRate / getSetupSettings(seed).shiftHours * machineCapacityFactor(machine);
  return hourlyRate > 0 ? quantity / hourlyRate : Number.POSITIVE_INFINITY;
}
function addMachineCapacityHours(seed, machine, startValue, hoursValue, capacityAt) {
  let cursor = Math.max(0, startValue);
  let remaining = Math.max(0, hoursValue);
  let actualStart = 0;
  let guard = 0;
  const shiftHours = getSetupSettings(seed).shiftHours;
  while (remaining > 0 || !actualStart) {
    const day = Math.floor(cursor);
    const capacityHours = (capacityAt ? capacityAt(day) : machineDayCapacity(seed, machine, day)).shifts * shiftHours;
    const windowStart = day;
    const windowEnd = day + capacityHours / 24;
    if (capacityHours <= 0 || cursor >= windowEnd - 1e-8) {
      cursor = day + 1;
      guard += 1;
      if (guard > 36600) throw new Error(`${machine.id} i\xE7in \xE7al\u0131\u015F\u0131labilir takvim saati bulunamad\u0131.`);
      continue;
    }
    cursor = Math.max(cursor, windowStart);
    if (!actualStart) actualStart = cursor;
    if (remaining <= 0) break;
    const availableHours = Math.max(0, (windowEnd - cursor) * 24);
    const consumed = Math.min(remaining, availableHours);
    cursor += consumed / 24;
    remaining -= consumed;
    if (remaining > 1e-8) cursor = day + 1;
    guard += 1;
    if (guard > 36600) throw new Error(`${machine.id} i\xE7in \xE7al\u0131\u015F\u0131labilir takvim saati bulunamad\u0131.`);
  }
  return { start: actualStart, end: Math.round((cursor + machine.finishOffset) * 1e6) / 1e6 };
}
function machineCapacityHoursBetween(seed, machine, startValue, endValue) {
  const start = Math.max(0, startValue);
  const end = Math.max(start, endValue);
  const shiftHours = getSetupSettings(seed).shiftHours;
  let total = 0;
  for (let day = Math.floor(start); day <= Math.floor(end); day += 1) {
    const capacityHours = machineDayCapacity(seed, machine, day).shifts * shiftHours;
    if (capacityHours <= 0) continue;
    const windowStart = day;
    const windowEnd = day + capacityHours / 24;
    total += Math.max(0, Math.min(end, windowEnd) - Math.max(start, windowStart)) * 24;
  }
  return total;
}
var BALANCED_UTILIZATION_TOLERANCE = 0.12;
var RESTRICTED_MACHINE_IDS = /* @__PURE__ */ new Set(["C-03", "C-04", "C-11", "C-12", "C-15", "C-16", "C-17"]);
var LARGE_DIAMETER_BLOCKED = /* @__PURE__ */ new Set(["C-01", "C-02", "C-04", "C-05"]);
function isMachineEligibleForProduct(seed, machineId, productCode) {
  if (!turningEnabled(seed.processMasterData, productCode)) return false;
  const code3 = productCode.toUpperCase();
  const product = seed.products.find((item) => item.product.toUpperCase() === code3);
  if (!product) return false;
  if (seed.productionArea === "cubuk-filtre" && !Number.isFinite(product.turningSetupMinutes?.[machineId])) return false;
  if (product.inactiveMachineIds?.includes(machineId)) return false;
  const preference = seed.preferences.find((rule) => rule.key.toUpperCase() === code3);
  if (preference) return preference.machines.includes(machineId);
  if (diameterNumeric(product.diameter) >= 25.5 && LARGE_DIAMETER_BLOCKED.has(machineId)) return false;
  if (!RESTRICTED_MACHINE_IDS.has(machineId)) return true;
  return seed.restrictions.some((rule) => rule.machineId === machineId && rule.product.toUpperCase() === code3);
}
function semiFinishedProduction(seed) {
  return (seed.productionHistory ?? []).filter((entry) => (entry.inventoryStatus ?? "semi-finished") === "semi-finished");
}
function committedProductionQuantities(seed, fixedBatches) {
  const quantities = /* @__PURE__ */ new Map();
  const add = (product, quantity) => {
    const code3 = product.toUpperCase();
    if (isProductCode(code3, seed) && quantity > 0) quantities.set(code3, (quantities.get(code3) ?? 0) + quantity);
  };
  if (seed.productionArea === "cubuk-filtre") {
    for (const row of filterCommittedSupply(seed, fixedBatches)) add(row.product, row.quantity);
    return quantities;
  }
  if (!seed.customerDemand) Object.entries(seed.openingStock ?? {}).forEach(([product, quantity]) => add(product, quantity));
  for (const row of seed.processStockSettings?.opening ?? []) add(row.product, filterSupplyGoodPieces(seed, row.product, row.quantity, row.groupId === "warehouse"));
  seed.machines.forEach((machine) => add(machine.currentJob.product, filterSupplyGoodPieces(seed, machine.currentJob.product, machine.currentJob.quantity)));
  semiFinishedProduction(seed).forEach((entry) => add(entry.product, filterHistoryGoodPieces(seed, entry)));
  fixedBatches.filter((batch) => batch.status === "planned").forEach((batch) => add(batch.product, filterSupplyGoodPieces(seed, batch.product, batch.quantity)));
  return quantities;
}
function withheldReplacementQuantities(seed) {
  const orders = new Map(seed.orders.map((order) => [order.id, order]));
  const byProduct = /* @__PURE__ */ new Map();
  for (const item of seed.productionCancellations ?? []) {
    if (item.review?.status === "replacement-approved") continue;
    const product = item.product.toUpperCase();
    byProduct.set(product, [...byProduct.get(product) ?? [], item]);
  }
  const withheld = /* @__PURE__ */ new Map();
  for (const [product, records2] of byProduct) {
    const flow = maxFlow(seed, product, records2, orders);
    if (flow > 0) withheld.set(product, flow);
  }
  return withheld;
}
function maxFlow(seed, product, records2, orders) {
  const graph = [[], []];
  const addEdge = (from, to, capacity) => {
    graph[from].push({ to, capacity, reverse: graph[to].length });
    graph[to].push({ to: from, capacity: 0, reverse: graph[from].length - 1 });
  };
  const orderNode = /* @__PURE__ */ new Map();
  const nodeFor = (id) => {
    let node = orderNode.get(id);
    if (node === void 0) {
      node = graph.length;
      graph.push([]);
      orderNode.set(id, node);
      addEdge(node, 1, Math.max(0, orders.get(id).quantity));
    }
    return node;
  };
  for (const item of records2) {
    if (!Number.isSafeInteger(item.cancelledQuantity) || item.cancelledQuantity <= 0) continue;
    const made = Number.isSafeInteger(item.completedQuantity) ? item.completedQuantity : 0;
    const budget = filterSupplyGoodPieces(seed, product, made + item.cancelledQuantity) - filterSupplyGoodPieces(seed, product, made);
    if (!budget) continue;
    const edges = [...new Set(item.orderIds ?? [])].flatMap((id) => {
      const order = orders.get(id);
      if (!order || order.product.toUpperCase() !== product || order.quantity <= 0) return [];
      const snapshot = item.orderQuantities?.[id];
      const cap = Math.max(0, Math.min(order.quantity, Number.isFinite(snapshot) ? snapshot : order.quantity));
      return cap > 0 ? [{ id, cap }] : [];
    });
    if (!edges.length) continue;
    const recordNode = graph.length;
    graph.push([]);
    addEdge(0, recordNode, budget);
    for (const edge of edges) addEdge(recordNode, nodeFor(edge.id), edge.cap);
  }
  let total = 0;
  for (; ; ) {
    const level = new Array(graph.length).fill(-1);
    level[0] = 0;
    const queue = [0];
    for (let head = 0; head < queue.length; head += 1) for (const edge of graph[queue[head]]) {
      if (edge.capacity > 0 && level[edge.to] < 0) {
        level[edge.to] = level[queue[head]] + 1;
        queue.push(edge.to);
      }
    }
    if (level[1] < 0) return total;
    const pointer = new Array(graph.length).fill(0);
    const push = (node, limit) => {
      if (node === 1) return limit;
      for (; pointer[node] < graph[node].length; pointer[node] += 1) {
        const edge = graph[node][pointer[node]];
        if (edge.capacity <= 0 || level[edge.to] !== level[node] + 1) continue;
        const sent = push(edge.to, Math.min(limit, edge.capacity));
        if (sent > 0) {
          edge.capacity -= sent;
          graph[edge.to][edge.reverse].capacity += sent;
          return sent;
        }
      }
      return 0;
    };
    for (let sent = push(0, Number.POSITIVE_INFINITY); sent > 0; sent = push(0, Number.POSITIVE_INFINITY)) total += sent;
  }
}
function newProductionBudgetCommitments(seed, fixedBatches) {
  const quantities = committedProductionQuantities(seed, fixedBatches);
  withheldReplacementQuantities(seed).forEach((quantity, product) => quantities.set(product, (quantities.get(product) ?? 0) + quantity));
  return quantities;
}
function currentJobRouteIdentity(machine) {
  const job = machine.currentJob;
  return JSON.stringify(job.batchId ? [machine.id, job.batchId, job.product] : [machine.id, job.product, job.workOrder, job.start, job.originalQuantity ?? job.quantity]);
}
function retainRouteCommitments(seed, fixedBatches) {
  const sharedIds = new Set([...fixedBatches, ...(seed.manualBatches ?? []).filter((batch) => batch.locked || batch.routeCommitted || hasRecordedTurningProduction(seed, batch))].flatMap((batch) => batch.sharedCharge ? [batch.sharedCharge.id] : []));
  const ids = new Set(fixedBatches.map((batch) => batch.id));
  const represented = /* @__PURE__ */ new Set([...(seed.wipLots ?? []).map((lot) => lot.sourceBatchId), ...seed.machines.map((machine) => machine.currentJob.batchId)]);
  return [...fixedBatches, ...(seed.manualBatches ?? []).filter((batch) => (batch.routeCommitted || batch.sharedCharge && sharedIds.has(batch.sharedCharge.id)) && batch.status === "planned" && !ids.has(batch.id) && !represented.has(batch.id))];
}
function runScenario(seed, fixedBatches, strategy, optimizationGoal) {
  seed = reconcileTurningSeed(seed);
  fixedBatches = retainRouteCommitments(seed, fixedBatches);
  const products = new Map(seed.products.map((product) => [product.product.toUpperCase(), product]));
  const preferences = new Map(seed.preferences.filter((rule) => /^R/i.test(rule.key)).map((rule) => [rule.key.toUpperCase(), rule]));
  const states = new Map(seed.machines.map((machine) => [machine.id, { ...machine, scheduled: [] }]));
  fixedBatches = reconcileTurningQueue(seed, withInterruptedBatches(seed, fixedBatches));
  const frozen = fixedBatches.filter((batch) => batch.status === "planned").map((batch) => ({ ...batch, explanation: `Dondurulmu\u015F plan: ${batch.machineId} \xFCzerindeki s\u0131ra korunuyor.` }));
  for (const batch of frozen.sort((a, b) => a.planColumn - b.planColumn || a.sequence - b.sequence)) states.get(batch.machineId)?.scheduled.push(batch);
  const lastProduct = (state) => state.scheduled.at(-1)?.product ?? state.currentJob.product;
  const lastDiameter = (state) => normalizedDiameter(state.scheduled.at(-1)?.diameter ?? state.currentJob.diameter);
  const reusableHistory = semiFinishedProduction(seed);
  const currentProducts = new Set([...seed.machines.map((machine) => machine.currentJob.product), ...reusableHistory.map((entry) => entry.product), ...frozen.map((batch) => batch.product)].filter((code3) => isProductCode(code3, seed)));
  const activeMachineProducts = new Set(
    [...states.values()].filter((state) => state.active).map((state) => lastProduct(state)).filter((code3) => isProductCode(code3, seed)).map((code3) => code3.toUpperCase())
  );
  const existingByProduct = newProductionBudgetCommitments(seed, frozen);
  const dueSerial = (order) => {
    const firstMilestone = orderDeliveryMilestones(order)[0]?.date;
    return inputDateSerial3(firstMilestone || order.dueDate) || Number.MAX_SAFE_INTEGER;
  };
  const earliestDueByProduct = /* @__PURE__ */ new Map();
  let latestOrderDueDate = "";
  for (const order of seed.orders) {
    const key = order.product.toUpperCase();
    const due = dueSerial(order);
    const current = earliestDueByProduct.get(key);
    if (current === void 0 || due < current) earliestDueByProduct.set(key, due);
    if (order.dueDate && (!latestOrderDueDate || order.dueDate > latestOrderDueDate)) latestOrderDueDate = order.dueDate;
  }
  const productEarliestDueSerial = (order) => earliestDueByProduct.get(order.product.toUpperCase()) ?? Number.MAX_SAFE_INTEGER;
  const standardScopeDueDate = seed.activePlanRun?.scope.endDate || latestOrderDueDate;
  const activeMachineRank = (order) => activeMachineProducts.has(order.product.toUpperCase()) ? 0 : 1;
  const wipRank = (order) => currentProducts.has(order.product) ? 0 : 1;
  const ratedMachineIds = (order) => seed.machines.filter((machine) => machine.active && isMachineEligibleForProduct(seed, machine.id, order.product) && (machine.rates[order.product.toUpperCase()] ?? 0) * machine.shiftFactor * machineCapacityFactor(machine) > 0).map((machine) => machine.id);
  const ratedMachineCount = (order) => ratedMachineIds(order).length;
  const scarcityRank = (order) => ratedMachineCount(order) <= 2 ? 0 : 1;
  const orderDiameter = (order) => normalizedDiameter(products.get(order.product.toUpperCase())?.diameter ?? "");
  const orderedOrders = strategy === "optimized" ? [...seed.orders].sort((a, b) => optimizationGoal === "standard" ? activeMachineRank(a) - activeMachineRank(b) || productEarliestDueSerial(a) - productEarliestDueSerial(b) || ratedMachineCount(a) - ratedMachineCount(b) || wipRank(a) - wipRank(b) || orderDiameter(a).localeCompare(orderDiameter(b), "tr", { numeric: true }) || a.product.localeCompare(b.product) || dueSerial(a) - dueSerial(b) || a.sourceRow - b.sourceRow : optimizationGoal === "coarse" ? (seed.productionArea === "cubuk-filtre" ? 0 : dueSerial(a) - dueSerial(b)) || ratedMachineCount(a) - ratedMachineCount(b) || wipRank(a) - wipRank(b) || orderDiameter(a).localeCompare(orderDiameter(b), "tr", { numeric: true }) || a.product.localeCompare(b.product) || a.sourceRow - b.sourceRow : dueSerial(a) - dueSerial(b) || scarcityRank(a) - scarcityRank(b) || wipRank(a) - wipRank(b) || a.sourceRow - b.sourceRow) : [
    ...seed.orders.filter((order) => currentProducts.has(order.product)),
    ...seed.orders.filter((order) => !currentProducts.has(order.product))
  ];
  const planningLots = [];
  const demandByProduct = /* @__PURE__ */ new Map();
  const targetByProduct = /* @__PURE__ */ new Map();
  for (const order of orderedOrders) {
    const productCode = order.product.toUpperCase();
    const product = products.get(productCode);
    const existingQuantity = existingByProduct.get(productCode) ?? 0;
    const priorDemand = demandByProduct.get(productCode) ?? 0;
    const priorTarget = targetByProduct.get(productCode) ?? 0;
    demandByProduct.set(productCode, priorDemand + order.quantity);
    if (!product) {
      planningLots.push({ order, quantity: 0, targetNewQuantity: 0, dueDate: order.dueDate, checkpointId: "missing-product", lotIndex: 0, missingProduct: true });
      continue;
    }
    const batchSize = product.batchSize > 0 ? product.batchSize : order.quantity;
    const cumulativeTarget = Math.max(priorTarget, productionTargetForShortage(filterInputForShortage(seed, productCode, Math.max(0, priorDemand + order.quantity - existingQuantity)), batchSize, shortageExtraChargePolicyForSeed(seed)));
    const targetNewQuantity = cumulativeTarget - priorTarget;
    targetByProduct.set(productCode, cumulativeTarget);
    if (strategy !== "optimized" || optimizationGoal === "standard" || !seed.customerDemand && !seed.dailyCustomerDemand && !seed.monthlyCustomerDemand) {
      planningLots.push({ order, quantity: targetNewQuantity, targetNewQuantity, dueDate: order.dueDate, checkpointId: "order-total", lotIndex: 0 });
      continue;
    }
    const checkpoints = [
      ...orderDeliveryMilestones(order),
      ...order.dueDate ? [{ id: "final", quantity: order.quantity, date: order.dueDate }] : []
    ].sort((left, right) => left.date.localeCompare(right.date) || left.quantity - right.quantity);
    let effectiveTarget = priorTarget;
    let lotIndex = 0;
    for (const checkpoint of checkpoints) {
      const roundedTarget = productionTargetForShortage(filterInputForShortage(seed, productCode, Math.max(0, priorDemand + checkpoint.quantity - existingQuantity)), batchSize, shortageExtraChargePolicyForSeed(seed));
      const nextTarget = Math.min(cumulativeTarget, Math.max(effectiveTarget, roundedTarget));
      for (let plannedTarget = effectiveTarget; plannedTarget < nextTarget; plannedTarget += batchSize) {
        planningLots.push({
          order,
          quantity: Math.min(batchSize, nextTarget - plannedTarget),
          targetNewQuantity: 0,
          dueDate: checkpoint.date,
          checkpointId: checkpoint.id,
          lotIndex: lotIndex++
        });
      }
      effectiveTarget = nextTarget;
    }
    const eventualTarget = cumulativeTarget;
    for (let plannedTarget = effectiveTarget; plannedTarget < eventualTarget; plannedTarget += batchSize) {
      planningLots.push({
        order,
        quantity: Math.min(batchSize, eventualTarget - plannedTarget),
        targetNewQuantity: 0,
        dueDate: order.dueDate,
        checkpointId: "eventual-total",
        lotIndex: lotIndex++
      });
    }
    for (const lot of planningLots.filter((item) => item.order.id === order.id)) lot.targetNewQuantity = targetNewQuantity;
  }
  if (strategy === "optimized" && optimizationGoal !== "standard" && (seed.customerDemand || seed.dailyCustomerDemand || seed.monthlyCustomerDemand)) {
    planningLots.sort((left, right) => (inputDateSerial3(left.dueDate) || Number.MAX_SAFE_INTEGER) - (inputDateSerial3(right.dueDate) || Number.MAX_SAFE_INTEGER) || (optimizationGoal === "balanced" || optimizationGoal === "coarse" ? ratedMachineCount(left.order) - ratedMachineCount(right.order) : scarcityRank(left.order) - scarcityRank(right.order)) || wipRank(left.order) - wipRank(right.order) || (optimizationGoal === "coarse" ? orderDiameter(left.order).localeCompare(orderDiameter(right.order), "tr", { numeric: true }) : 0) || (optimizationGoal === "coarse" ? left.order.product.localeCompare(right.order.product) : 0) || left.order.sourceRow - right.order.sourceRow || left.lotIndex - right.lotIndex);
  }
  const remainingExclusiveLotsByMachine = /* @__PURE__ */ new Map();
  if (optimizationGoal === "balanced" || optimizationGoal === "coarse" || optimizationGoal === "standard") {
    for (const lot of planningLots) {
      const product = products.get(lot.order.product.toUpperCase());
      const machineIds = ratedMachineIds(lot.order);
      if (!product || machineIds.length !== 1 || lot.quantity <= 0) continue;
      const batchSize = product.batchSize > 0 ? product.batchSize : lot.quantity;
      const batchCount = Math.max(1, Math.ceil(lot.quantity / batchSize));
      remainingExclusiveLotsByMachine.set(machineIds[0], (remainingExclusiveLotsByMachine.get(machineIds[0]) ?? 0) + batchCount);
    }
  }
  const batches = frozen.map((batch) => ({ ...batch }));
  const newlyPlannedByOrder = /* @__PURE__ */ new Map();
  const assignedMachinesByOrder = /* @__PURE__ */ new Map();
  let sequence = Math.max(0, ...frozen.map((batch) => batch.sequence)) + 1;
  const reservedBatchIds = new Set([
    ...frozen.map((batch) => batch.id),
    ...seed.machines.map((machine) => machine.currentJob.batchId),
    ...(seed.productionHistory ?? []).flatMap((entry) => [entry.id, entry.sourceBatchId]),
    ...(seed.wipLots ?? []).flatMap((lot) => [lot.id, lot.sourceBatchId, lot.parentLotId]),
    ...(seed.processOperationOverrides ?? []).map((override) => override.batchId),
    ...(seed.processCurrentJobs ?? []).map((job) => job.batchId),
    ...(seed.productionInterruptions ?? []).flatMap((item) => [item.chargeId, item.turningBatch?.id]),
    ...(seed.productionCancellations ?? []).map((item) => item.chargeId),
    ...(seed.chargeJourneyNotes ?? []).map((note) => note.chargeKey)
  ].filter(Boolean));
  const nextScenarioIdentity = () => {
    while (reservedBatchIds.has(`scenario-${sequence}`)) sequence += 1;
    const id = `scenario-${sequence}`;
    reservedBatchIds.add(id);
    return { id, sequence: sequence++, ...seed.productionArea === "cubuk-filtre" && seed.activePlanRun?.chargeIdNamespace ? { workOrder: `ID-${sequence - 1}-${seed.activePlanRun.chargeIdNamespace}` } : {} };
  };
  const planningCapacityByMachine = new Map([...states.values()].map((state) => [
    state.id,
    machineCapacityHoursBetween(seed, state, state.availableStart, Math.floor(state.planEnd) + 1)
  ]));
  const committedHours = (state) => {
    const windowEnd = Math.floor(state.planEnd) + 1;
    const currentEnd = Math.min(windowEnd, Math.max(state.currentJob.start, state.currentJob.end - state.finishOffset));
    const currentHours = state.currentJob.product ? machineCapacityHoursBetween(seed, state, Math.max(state.availableStart, state.currentJob.start), currentEnd) : 0;
    return currentHours + state.scheduled.reduce((sum, batch) => {
      const recordedHours = (batch.setupHours ?? 0) + (batch.runHours ?? 0);
      if (recordedHours > 0) return sum + recordedHours;
      return sum + machineCapacityHoursBetween(seed, state, batch.start, Math.max(batch.start, batch.end - state.finishOffset));
    }, 0);
  };
  for (const lot of planningLots) {
    const order = lot.order;
    const productCode = order.product.toUpperCase();
    const product = products.get(productCode);
    const existingQuantity = existingByProduct.get(productCode) ?? 0;
    const assignedMachines = assignedMachinesByOrder.get(order.id) ?? unique(frozen.filter((batch) => batch.product.toUpperCase() === productCode).map((batch) => batch.machineId));
    let newlyPlanned = newlyPlannedByOrder.get(order.id) ?? 0;
    if (!product || lot.missingProduct || product.retired && lot.quantity > 0) {
      batches.push({
        ...nextScenarioIdentity(),
        product: order.product,
        orderQuantity: order.quantity,
        quantity: 0,
        machineId: "PLANLANAMADI",
        diameter: "",
        batchSize: 0,
        dailyRate: 0,
        availableStart: 0,
        planEnd: 0,
        reason: product?.retired ? "Tip kullan\u0131mdan kald\u0131r\u0131ld\u0131." : "\xDCr\xFCn parametreleri bulunamad\u0131.",
        explanation: product?.retired ? "Yeni \u015Farj planlanmaz. Mevcut i\u015Fler ve \xFCretim kay\u0131tlar\u0131 korunur." : "\u015Earj b\xFCy\xFCkl\xFC\u011F\xFC, \xE7ap ve \xFCretim h\u0131z\u0131 olmadan sipari\u015F planlanamaz.",
        planColumn: 0,
        existingQuantity,
        start: 0,
        end: 0,
        status: "unplanned",
        demandDueDate: lot.dueDate,
        demandCheckpointId: lot.checkpointId
      });
    } else {
      const batchSize = product.batchSize > 0 ? product.batchSize : order.quantity;
      let remaining = lot.quantity;
      const targetTotal = existingQuantity + lot.targetNewQuantity;
      const special = preferences.get(productCode);
      const isLargeDiameter = diameterNumeric(product.diameter) >= 25.5;
      while (remaining > 0) {
        const lotQuantity = Math.min(batchSize, remaining);
        const targetDiameter = normalizedDiameter(product.diameter);
        let candidates;
        if (special) {
          candidates = special.machines.map((machineId) => states.get(machineId)).filter((state) => Boolean(state?.active)).filter((state) => isMachineEligibleForProduct(seed, state.id, productCode)).map((state, index) => ({ state, bucket: index }));
        } else {
          const preference = product.alternativeMachines;
          candidates = [...states.values()].filter((state) => state.active && isMachineEligibleForProduct(seed, state.id, productCode)).map((state) => {
            const preferred = preference.includes(state.id);
            const previousProduct = lastProduct(state);
            const previousDiameter = lastDiameter(state);
            let bucket = 7;
            if (isLargeDiameter && ["C-06", "C-07"].includes(state.id)) bucket = 0;
            else if (isProductCode(previousProduct, seed) && previousProduct.toUpperCase() === productCode) bucket = 1;
            else if (targetDiameter && previousDiameter && previousDiameter === targetDiameter) bucket = preferred ? 2 : 3;
            else if (!previousDiameter) bucket = preferred ? 4 : 5;
            else if (preferred) bucket = 6;
            return { state, bucket };
          });
          if (strategy === "v51") candidates.sort((a, b) => a.bucket - b.bucket || a.state.scheduled.length - b.state.scheduled.length || a.state.id.localeCompare(b.state.id));
        }
        if (seed.productionArea === "cubuk-filtre" && strategy === "optimized") {
          const groups = [...new Set(candidates.map(({ state }) => filterTurningGroup(state.id)))];
          const choices = groups.flatMap((group) => {
            const resources = candidates.filter(({ state }) => filterTurningGroup(state.id) === group).flatMap(({ state }) => {
              if (state.shiftFactor <= 0 || !(state.rates[productCode] > 0)) return [];
              const setup = calculateSetup(seed, lastProduct(state), lastDiameter(state), productCode, targetDiameter, state.id);
              const hoursPerPiece = machineRunHours(seed, state, productCode, 1);
              if (!Number.isFinite(setup.hours) || !(hoursPerPiece > 0)) return [];
              const start = Math.max(state.availableStart, state.scheduled.at(-1)?.end ?? state.currentJob.end);
              const end = Math.floor(state.planEnd) + 1 - 1e-6;
              return [{
                resource: { state, setup, hoursPerPiece },
                start,
                end,
                capacity: (until) => Math.max(0, machineCapacityHoursBetween(seed, state, start, until - state.finishOffset) - setup.hours) / hoursPerPiece,
                timing: (quantity) => addMachineCapacityHours(seed, state, start, setup.hours + quantity * hoursPerPiece)
              }];
            });
            const allocation = allocateSharedQuantity(lotQuantity, resources);
            return allocation ? [{ allocation, end: Math.max(...allocation.map((item) => item.end)) }] : [];
          }).sort((a, b) => a.end - b.end);
          const shared = choices[0]?.allocation;
          if (shared && shared.length > 1) {
            const identity = nextScenarioIdentity();
            const sharedCharge = { id: identity.workOrder ?? identity.id, quantity: lotQuantity };
            for (const [index, portion] of shared.entries()) {
              const { state, setup, hoursPerPiece } = portion.resource;
              const batch = {
                ...index === 0 ? identity : nextScenarioIdentity(),
                ...identity.workOrder ? { workOrder: identity.workOrder } : {},
                sharedCharge,
                product: order.product,
                orderQuantity: order.quantity,
                quantity: portion.quantity,
                machineId: state.id,
                diameter: targetDiameter,
                batchSize,
                dailyRate: state.rates[productCode] * state.shiftFactor * machineCapacityFactor(state),
                availableStart: state.availableStart,
                planEnd: state.planEnd,
                reason: "Ortak \u015Farj",
                explanation: `${lotQuantity} adetlik ortak \u015Farj\u0131n ${portion.quantity} adedi. Kapasiteye g\xF6re yak\u0131n biti\u015F hedefi; toplam miktar korunur.`,
                planColumn: 13 + state.scheduled.length,
                existingQuantity,
                start: portion.start,
                end: portion.end,
                status: "planned",
                setupHours: setup.hours,
                setupType: setup.type,
                runHours: portion.quantity * hoursPerPiece,
                demandDueDate: lot.dueDate,
                demandCheckpointId: lot.checkpointId
              };
              state.scheduled.push(batch);
              batches.push(batch);
              assignedMachines.push(state.id);
            }
            newlyPlanned += lotQuantity;
            remaining -= lotQuantity;
            continue;
          }
        }
        let selected;
        let selectedStart = 0;
        let selectedEnd = 0;
        let selectedRate = 0;
        let selectedSetupHours = 0;
        let selectedSetupType;
        let selectedSetupLabel = "";
        let selectedRunHours = 0;
        let selectedPriority = Number.POSITIVE_INFINITY;
        let selectedQueueLength = Number.POSITIVE_INFINITY;
        let selectedProjectedUtilization = 0;
        const evaluateSlot = (candidate) => {
          if (strategy === "v51" && candidate.scheduled.length >= 14) return null;
          const previousEnd = candidate.scheduled.at(-1)?.end ?? candidate.currentJob.end;
          const rate = (candidate.rates[productCode] ?? 0) * candidate.shiftFactor * machineCapacityFactor(candidate);
          if (rate <= 0) return null;
          if (strategy === "optimized") {
            const setup = calculateSetup(seed, lastProduct(candidate), lastDiameter(candidate), productCode, targetDiameter, candidate.id);
            const runHours = machineRunHours(seed, candidate, productCode, lotQuantity);
            const readyAt = Math.max(candidate.availableStart, previousEnd);
            const timeline = addMachineCapacityHours(seed, candidate, readyAt, setup.hours + runHours);
            return timeline.start >= candidate.availableStart && timeline.end < Math.floor(candidate.planEnd) + 1 ? { ...timeline, rate, setupHours: setup.hours, setupType: setup.type, setupLabel: setup.label, runHours } : null;
          }
          const start = previousEnd + 0.1;
          const end = addMachineWorkdays(seed, candidate, start, lotQuantity / rate + 0.5, candidate.finishOffset);
          return start >= candidate.availableStart && end <= candidate.planEnd ? { start, end, rate, setupHours: 0, setupLabel: "V51 s\xFCre modeli", runHours: 0 } : null;
        };
        if (strategy === "optimized" && (!special || optimizationGoal)) {
          const evaluated = candidates.flatMap(({ state: candidate, bucket }) => {
            const slot = evaluateSlot(candidate);
            if (!slot) return [];
            const capacityHours = planningCapacityByMachine.get(candidate.id) ?? 0;
            const projectedUtilization = capacityHours > 0 ? (committedHours(candidate) + slot.setupHours + slot.runHours) / capacityHours : Number.POSITIVE_INFINITY;
            return [{ candidate, bucket, slot, queueLength: candidate.scheduled.length, projectedUtilization, deliveryReadyAt: turningDeliveryReadyAt(slot.end) }];
          });
          if (optimizationGoal === "standard" && evaluated.length) {
            let standardCandidates = evaluated;
            const due = inputDateSerial3(standardScopeDueDate || lot.dueDate);
            if (seed.productionArea !== "cubuk-filtre" && due > 0) {
              const onTime = standardCandidates.filter((item) => Math.floor(item.deliveryReadyAt) <= Math.floor(due));
              if (onTime.length) standardCandidates = onTime;
              else {
                const earliestDelivery = Math.min(...standardCandidates.map((item) => item.deliveryReadyAt));
                standardCandidates = standardCandidates.filter((item) => item.deliveryReadyAt <= earliestDelivery + 1e-6);
              }
            }
            const sameProductCandidates = standardCandidates.filter((item) => item.slot.setupType === "same-product" || lastProduct(item.candidate).trim().toUpperCase() === productCode);
            if (sameProductCandidates.length) {
              standardCandidates = sameProductCandidates;
            } else if (standardCandidates.length > 1) {
              const withoutExclusivePressure = standardCandidates.filter((item) => (remainingExclusiveLotsByMachine.get(item.candidate.id) ?? 0) === 0);
              if (withoutExclusivePressure.length) standardCandidates = withoutExclusivePressure;
            }
            standardCandidates.sort((left, right) => setupTypeRank(left.slot.setupType) - setupTypeRank(right.slot.setupType) || left.slot.setupHours - right.slot.setupHours || left.projectedUtilization - right.projectedUtilization || left.slot.end - right.slot.end || left.bucket - right.bucket || left.candidate.id.localeCompare(right.candidate.id));
            const chosen = standardCandidates[0];
            selected = chosen.candidate;
            selectedStart = chosen.slot.start;
            selectedEnd = chosen.slot.end;
            selectedRate = chosen.slot.rate;
            selectedSetupHours = chosen.slot.setupHours;
            selectedSetupType = chosen.slot.setupType;
            selectedSetupLabel = chosen.slot.setupLabel;
            selectedRunHours = chosen.slot.runHours;
            selectedPriority = chosen.bucket;
            selectedQueueLength = chosen.queueLength;
            selectedProjectedUtilization = chosen.projectedUtilization;
          } else if (optimizationGoal === "coarse" && evaluated.length) {
            let coarseCandidates = evaluated;
            const due = inputDateSerial3(lot.dueDate);
            if (seed.productionArea !== "cubuk-filtre" && due > 0) {
              const onTime = coarseCandidates.filter((item) => Math.floor(item.deliveryReadyAt) <= Math.floor(due));
              if (onTime.length) coarseCandidates = onTime;
              else {
                const earliestDelivery = Math.min(...coarseCandidates.map((item) => item.deliveryReadyAt));
                coarseCandidates = coarseCandidates.filter((item) => item.deliveryReadyAt <= earliestDelivery + 1e-6);
              }
            }
            if (coarseCandidates.length > 1) {
              const withoutExclusivePressure = coarseCandidates.filter((item) => (remainingExclusiveLotsByMachine.get(item.candidate.id) ?? 0) === 0);
              if (withoutExclusivePressure.length) coarseCandidates = withoutExclusivePressure;
            }
            coarseCandidates.sort((left, right) => setupTypeRank(left.slot.setupType) - setupTypeRank(right.slot.setupType) || left.slot.setupHours - right.slot.setupHours || left.projectedUtilization - right.projectedUtilization || left.slot.end - right.slot.end || left.bucket - right.bucket || left.candidate.id.localeCompare(right.candidate.id));
            const chosen = coarseCandidates[0];
            selected = chosen.candidate;
            selectedStart = chosen.slot.start;
            selectedEnd = chosen.slot.end;
            selectedRate = chosen.slot.rate;
            selectedSetupHours = chosen.slot.setupHours;
            selectedSetupType = chosen.slot.setupType;
            selectedSetupLabel = chosen.slot.setupLabel;
            selectedRunHours = chosen.slot.runHours;
            selectedPriority = chosen.bucket;
            selectedQueueLength = chosen.queueLength;
            selectedProjectedUtilization = chosen.projectedUtilization;
          } else if (optimizationGoal === "balanced" && evaluated.length) {
            let balancedCandidates = evaluated;
            const due = inputDateSerial3(lot.dueDate);
            if (due > 0) {
              const onTime = balancedCandidates.filter((item) => item.deliveryReadyAt <= due + 1e-6);
              if (onTime.length) balancedCandidates = onTime;
              else {
                const earliestDelivery = Math.min(...balancedCandidates.map((item) => item.deliveryReadyAt));
                balancedCandidates = balancedCandidates.filter((item) => item.deliveryReadyAt <= earliestDelivery + 1e-6);
              }
            }
            if (evaluated.length > 1) {
              const withoutExclusivePressure = balancedCandidates.filter((item) => (remainingExclusiveLotsByMachine.get(item.candidate.id) ?? 0) === 0);
              if (withoutExclusivePressure.length) balancedCandidates = withoutExclusivePressure;
            }
            const lowestUtilization = Math.min(...balancedCandidates.map((item) => item.projectedUtilization));
            const balancedBand = balancedCandidates.filter((item) => item.projectedUtilization <= lowestUtilization + BALANCED_UTILIZATION_TOLERANCE + 1e-6);
            balancedBand.sort((left, right) => setupTypeRank(left.slot.setupType) - setupTypeRank(right.slot.setupType) || left.slot.setupHours - right.slot.setupHours || left.projectedUtilization - right.projectedUtilization || left.bucket - right.bucket || left.slot.end - right.slot.end || left.candidate.id.localeCompare(right.candidate.id));
            const chosen = balancedBand[0];
            selected = chosen.candidate;
            selectedStart = chosen.slot.start;
            selectedEnd = chosen.slot.end;
            selectedRate = chosen.slot.rate;
            selectedSetupHours = chosen.slot.setupHours;
            selectedSetupType = chosen.slot.setupType;
            selectedSetupLabel = chosen.slot.setupLabel;
            selectedRunHours = chosen.slot.runHours;
            selectedPriority = chosen.bucket;
            selectedQueueLength = chosen.queueLength;
            selectedProjectedUtilization = chosen.projectedUtilization;
          } else {
            for (const { candidate, bucket, slot, queueLength, projectedUtilization } of evaluated) {
              const better = !selected || (optimizationGoal === "all-compatible" ? queueLength < selectedQueueLength || queueLength === selectedQueueLength && (slot.end < selectedEnd || slot.end === selectedEnd && candidate.id.localeCompare(selected.id) < 0) : optimizationGoal === "minimum-setup" ? slot.setupHours < selectedSetupHours || slot.setupHours === selectedSetupHours && (bucket < selectedPriority || bucket === selectedPriority && (slot.end < selectedEnd || slot.end === selectedEnd && candidate.id.localeCompare(selected.id) < 0)) : slot.end < selectedEnd || slot.end === selectedEnd && (bucket < selectedPriority || bucket === selectedPriority && candidate.id.localeCompare(selected.id) < 0));
              if (better) {
                selected = candidate;
                selectedStart = slot.start;
                selectedEnd = slot.end;
                selectedRate = slot.rate;
                selectedSetupHours = slot.setupHours;
                selectedSetupType = slot.setupType;
                selectedSetupLabel = slot.setupLabel;
                selectedRunHours = slot.runHours;
                selectedPriority = bucket;
                selectedQueueLength = queueLength;
                selectedProjectedUtilization = projectedUtilization;
              }
            }
          }
        } else {
          for (const { state: candidate } of candidates) {
            const slot = evaluateSlot(candidate);
            if (!slot) continue;
            selected = candidate;
            selectedStart = slot.start;
            selectedEnd = slot.end;
            selectedRate = slot.rate;
            selectedSetupHours = slot.setupHours;
            selectedSetupType = slot.setupType;
            selectedSetupLabel = slot.setupLabel;
            selectedRunHours = slot.runHours;
            break;
          }
        }
        const roundingReason = Math.abs(targetTotal - order.quantity) > 1e-4 ? `\u015Earj yuvarlama + mevcut \xFCretim. Sipari\u015F=${order.quantity}; mevcut=${existingQuantity}; yeni hedef=${lot.targetNewQuantity}; toplam hedef=${targetTotal}` : "";
        if (!selected) {
          const candidateMachineIds = candidates.map(({ state }) => state.id);
          const missingRateMachineIds = candidates.filter(({ state }) => !((state.rates[productCode] ?? 0) > 0)).map(({ state }) => state.id);
          const allCandidateRatesMissing = candidates.length > 0 && missingRateMachineIds.length === candidates.length;
          const noActiveCandidate = candidates.length === 0;
          const unplannedReason = noActiveCandidate ? "Uygun ve aktif tezgah bulunamad\u0131: tezgah tercihlerini, aktiflik ve vardiya ayarlar\u0131n\u0131 kontrol edin." : allCandidateRatesMissing ? `\xDCr\xFCn\u2013tezgah \xFCretim h\u0131z\u0131 eksik: ${missingRateMachineIds.join(", ")}. Alternatif tezgah se\xE7imi tek ba\u015F\u0131na s\xFCre hesab\u0131 olu\u015Fturmaz.` : strategy === "v51" ? "Kapasite/tarih yetersiz: uygun aktif tezgahlar\u0131n 14 s\u0131ral\u0131k kuyru\u011Funda plan biti\u015Finden \xF6nce tamamlanabilecek yer bulunamad\u0131." : "Kapasite/tarih yetersiz: uygun aktif tezgahlarda plan biti\u015Finden \xF6nce tamamlanabilecek yer bulunamad\u0131.";
          const unplannedExplanation = noActiveCandidate ? "\xDCr\xFCn i\xE7in tan\u0131mlanan tezgahlar aras\u0131nda aktif ve vardiyas\u0131 a\xE7\u0131k bir i\u015F merkezi yok." : allCandidateRatesMissing ? `${missingRateMachineIds.join(", ")} alternatif olarak tan\u0131ml\u0131; ancak bu \xFCr\xFCn i\xE7in vardiya ba\u015F\u0131na \xFCretim h\u0131zlar\u0131 kaydedilmedi\u011Fi i\xE7in s\xFCre hesaplanam\u0131yor.` : `${candidateMachineIds.length} uygun aktif tezgah kontrol edildi; hi\xE7biri bu \u015Farj\u0131 planlama penceresi i\xE7inde tamamlayam\u0131yor.${missingRateMachineIds.length ? ` H\u0131z kayd\u0131 olmayan alternatifler: ${missingRateMachineIds.join(", ")}.` : ""}`;
          batches.push({
            ...nextScenarioIdentity(),
            product: order.product,
            orderQuantity: order.quantity,
            quantity: 0,
            machineId: "PLANLANAMADI",
            diameter: normalizedDiameter(product.diameter),
            batchSize,
            dailyRate: 0,
            availableStart: 0,
            planEnd: 0,
            reason: unplannedReason,
            explanation: unplannedExplanation,
            planColumn: 0,
            existingQuantity,
            start: 0,
            end: 0,
            status: "unplanned",
            demandDueDate: lot.dueDate,
            demandCheckpointId: lot.checkpointId
          });
        } else {
          const previousProduct = lastProduct(selected);
          const previousDiameter = lastDiameter(selected);
          let explanation = `${selected.id} uygun ve \u015Farj tezgah\u0131n m\xFCsaitlik penceresi i\xE7inde tamamlan\u0131yor.`;
          if (strategy === "optimized" && special) {
            explanation = optimizationGoal === "all-compatible" ? `${selected.id}, s\u0131ral\u0131 uygun tezgahlar aras\u0131nda en k\u0131sa kuyru\u011Fa sahip tezgah. ${selectedSetupLabel}: ${selectedSetupHours.toFixed(1)} saat; \xFCretim: ${selectedRunHours.toFixed(1)} saat.` : optimizationGoal === "balanced" ? `${selected.id}, tezgah \xF6nceli\u011Fi, kampanya uyumu ve kapasite dengesi birlikte de\u011Ferlendirilerek se\xE7ildi. Tahmini y\xFCk %${(selectedProjectedUtilization * 100).toFixed(1)}; ${selectedSetupLabel}: ${selectedSetupHours.toFixed(1)} saat; \xFCretim: ${selectedRunHours.toFixed(1)} saat.` : optimizationGoal === "standard" ? `${selected.id}, se\xE7ili tarih aral\u0131\u011F\u0131ndaki ayn\u0131 tip \u015Farjlar\u0131 arka arkaya ba\u011Flayarak setup'\u0131 azaltmak i\xE7in se\xE7ildi. Tahmini pencere y\xFCk\xFC %${(selectedProjectedUtilization * 100).toFixed(1)}; ${selectedSetupLabel}: ${selectedSetupHours.toFixed(1)} saat; \xFCretim: ${selectedRunHours.toFixed(1)} saat.` : optimizationGoal === "coarse" ? `${selected.id}, haftal\u0131k termini koruyarak ayn\u0131 \xFCr\xFCn/\xE7ap kampanyas\u0131n\u0131 s\xFCrd\xFCrmek ve setup'\u0131 azaltmak i\xE7in se\xE7ildi. Tahmini pencere y\xFCk\xFC %${(selectedProjectedUtilization * 100).toFixed(1)}; ${selectedSetupLabel}: ${selectedSetupHours.toFixed(1)} saat; \xFCretim: ${selectedRunHours.toFixed(1)} saat.` : optimizationGoal === "minimum-setup" ? `${selected.id}, s\u0131ral\u0131 uygun tezgahlar aras\u0131nda setup s\xFCresi en d\xFC\u015F\xFCk tezgah. ${selectedSetupLabel}: ${selectedSetupHours.toFixed(1)} saat; \xFCretim: ${selectedRunHours.toFixed(1)} saat.` : optimizationGoal === "earliest-finish" ? `${selected.id}, s\u0131ral\u0131 uygun tezgahlar aras\u0131nda bu \u015Farj\u0131 en erken tamamlayan tezgah (${formatExcelDate(selectedEnd)}). ${selectedSetupLabel}: ${selectedSetupHours.toFixed(1)} saat; \xFCretim: ${selectedRunHours.toFixed(1)} saat.` : `${selected.id}, s\u0131ral\u0131 tezgah kampanyas\u0131ndaki kapasitesi yeterli ilk tezgah: ${special.machines.join(" \u2192 ")}. ${selectedSetupLabel}: ${selectedSetupHours.toFixed(1)} saat; \xFCretim: ${selectedRunHours.toFixed(1)} saat.`;
          } else if (strategy === "optimized") {
            explanation = optimizationGoal === "all-compatible" ? `${selected.id}, uygun tezgahlar aras\u0131nda en k\u0131sa kuyru\u011Fa sahip tezgah. ${selectedSetupLabel}: ${selectedSetupHours.toFixed(1)} saat; \xFCretim: ${selectedRunHours.toFixed(1)} saat.` : optimizationGoal === "balanced" ? `${selected.id}, ayn\u0131 \xFCr\xFCn/\xE7ap kampanyas\u0131 ile uygun tezgahlar\u0131n kapasite y\xFCk\xFC birlikte de\u011Ferlendirilerek se\xE7ildi. Tahmini y\xFCk %${(selectedProjectedUtilization * 100).toFixed(1)}; ${selectedSetupLabel}: ${selectedSetupHours.toFixed(1)} saat; \xFCretim: ${selectedRunHours.toFixed(1)} saat.` : optimizationGoal === "standard" ? `${selected.id}, se\xE7ili tarih aral\u0131\u011F\u0131ndaki ayn\u0131 tip \u015Farjlar\u0131 arka arkaya ba\u011Flayarak setup'\u0131 azaltmak i\xE7in se\xE7ildi. Tahmini pencere y\xFCk\xFC %${(selectedProjectedUtilization * 100).toFixed(1)}; ${selectedSetupLabel}: ${selectedSetupHours.toFixed(1)} saat; \xFCretim: ${selectedRunHours.toFixed(1)} saat.` : optimizationGoal === "coarse" ? `${selected.id}, haftal\u0131k termini koruyarak ayn\u0131 \xFCr\xFCn/\xE7ap kampanyas\u0131n\u0131 s\xFCrd\xFCrmek ve setup'\u0131 azaltmak i\xE7in se\xE7ildi. Tahmini pencere y\xFCk\xFC %${(selectedProjectedUtilization * 100).toFixed(1)}; ${selectedSetupLabel}: ${selectedSetupHours.toFixed(1)} saat; \xFCretim: ${selectedRunHours.toFixed(1)} saat.` : optimizationGoal === "minimum-setup" ? `${selected.id}, uygun tezgahlar aras\u0131nda setup s\xFCresi en d\xFC\u015F\xFCk tezgah. ${selectedSetupLabel}: ${selectedSetupHours.toFixed(1)} saat; \xFCretim: ${selectedRunHours.toFixed(1)} saat.` : `${selected.id} setup dahil bu \u015Farj\u0131 en erken tamamlayan tezgah (${formatExcelDate(selectedEnd)}). ${selectedSetupLabel}: ${selectedSetupHours.toFixed(1)} saat; \xFCretim: ${selectedRunHours.toFixed(1)} saat.`;
          } else if (special) explanation = `${selected.id}, \xE7al\u0131\u015Fma kitab\u0131ndaki s\u0131raya g\xF6re m\xFCsait ilk tezgah: ${special.machines.join(" \u2192 ")}.`;
          else if (previousProduct.toUpperCase() === productCode) explanation = `${selected.id} kuyru\u011Funun sonundaki ayn\u0131 \xFCr\xFCne devam ediyor.`;
          else if (previousDiameter === normalizedDiameter(product.diameter)) explanation = `${selected.id} ayn\u0131 hammadde \xE7ap\u0131 kampanyas\u0131na devam ediyor.`;
          if (seed.customerDemand && lot.dueDate) explanation += ` Hedef teslim haftas\u0131: ${lot.dueDate}.`;
          const planned2 = {
            ...nextScenarioIdentity(),
            product: order.product,
            orderQuantity: order.quantity,
            quantity: lotQuantity,
            machineId: selected.id,
            diameter: normalizedDiameter(product.diameter),
            batchSize,
            dailyRate: selectedRate,
            availableStart: selected.availableStart,
            planEnd: selected.planEnd,
            reason: roundingReason,
            explanation,
            planColumn: 13 + selected.scheduled.length,
            existingQuantity,
            start: selectedStart,
            end: selectedEnd,
            status: "planned",
            setupHours: selectedSetupHours,
            setupType: selectedSetupType,
            runHours: selectedRunHours,
            demandDueDate: lot.dueDate,
            demandCheckpointId: lot.checkpointId
          };
          selected.scheduled.push(planned2);
          batches.push(planned2);
          assignedMachines.push(selected.id);
          newlyPlanned += lotQuantity;
        }
        remaining -= lotQuantity;
      }
    }
    if (optimizationGoal === "balanced" || optimizationGoal === "coarse" || optimizationGoal === "standard") {
      const product2 = products.get(productCode);
      const exclusiveMachineIds = ratedMachineIds(order);
      if (product2 && exclusiveMachineIds.length === 1 && lot.quantity > 0) {
        const batchSize = product2.batchSize > 0 ? product2.batchSize : lot.quantity;
        const releasedCount = Math.max(1, Math.ceil(lot.quantity / batchSize));
        const machineId = exclusiveMachineIds[0];
        remainingExclusiveLotsByMachine.set(machineId, Math.max(0, (remainingExclusiveLotsByMachine.get(machineId) ?? 0) - releasedCount));
      }
    }
    newlyPlannedByOrder.set(order.id, newlyPlanned);
    assignedMachinesByOrder.set(order.id, unique(assignedMachines));
  }
  const readinessEvents = seed.productionArea === "cubuk-filtre" && seed.monthlyCustomerDemand && seed.orders.some((order) => inputDateSerial3(order.dueDate)) ? buildDeliveryReadinessEvents(seed, { batches }) : void 0;
  const resultsInSourceOrder = seed.orders.map((order) => {
    const productCode = order.product.toUpperCase();
    const existingQuantity = existingByProduct.get(productCode) ?? 0;
    const newlyPlanned = newlyPlannedByOrder.get(order.id) ?? 0;
    const breakdown = orderProductionBreakdown(seed, batches, order, readinessEvents);
    const planned2 = breakdown.existingProduction + breakdown.newlyPlanned;
    const assignedMachines = assignedMachinesByOrder.get(order.id) ?? unique(frozen.filter((batch) => batch.product.toUpperCase() === productCode).map((batch) => batch.machineId));
    return {
      ...order,
      planned: planned2,
      difference: planned2 - order.quantity,
      ...breakdown,
      assignedMachines: unique(assignedMachines.length ? assignedMachines : order.savedMachines)
    };
  });
  const demand = seed.orders.reduce((sum, order) => sum + order.quantity, 0);
  const planned = resultsInSourceOrder.reduce((sum, order) => sum + order.planned, 0);
  const shortage = resultsInSourceOrder.reduce((sum, order) => sum + Math.max(0, -order.difference), 0);
  const overproduction = resultsInSourceOrder.reduce((sum, order) => sum + Math.max(0, order.difference), 0);
  const plannedBatches = batches.filter((batch) => batch.status === "planned");
  return {
    state: "planned",
    batches,
    orders: resultsInSourceOrder,
    createdAt: (/* @__PURE__ */ new Date()).toISOString(),
    planRun: seed.activePlanRun,
    summary: {
      demand,
      planned,
      shortage,
      overproduction,
      plannedBatchCount: new Set(plannedBatches.map((batch) => batch.sharedCharge?.id ?? batch.id)).size,
      unplannedBatchCount: batches.filter((batch) => batch.status === "unplanned").length,
      totalSetupHours: plannedBatches.reduce((sum, batch) => sum + (batch.setupHours ?? 0), 0),
      completion: Math.max(0, ...plannedBatches.map((batch) => batch.end)),
      machinesUsed: new Set(plannedBatches.map((batch) => batch.machineId)).size
    }
  };
}
function inputDateSerial3(value) {
  return value ? (Date.parse(`${value}T00:00:00Z`) - Date.UTC(1899, 11, 30)) / 864e5 : 0;
}
function orderDeliveryMilestones(order) {
  if (!order.allowPartial) return [];
  const milestones = order.deliveryMilestones?.length ? order.deliveryMilestones : order.partialDeliveryQuantity > 0 && order.partialDeliveryDate ? [{ id: "legacy-partial", quantity: order.partialDeliveryQuantity, date: order.partialDeliveryDate }] : [];
  return milestones.map((milestone, index) => ({
    id: milestone.id || `delivery-${index + 1}`,
    quantity: Math.max(0, Math.trunc(Number(milestone.quantity) || 0)),
    date: milestone.date || ""
  })).sort((left, right) => left.date.localeCompare(right.date) || left.quantity - right.quantity);
}
function validateDeliveryMilestones(milestones, quantity, dueDate) {
  let previousQuantity = 0;
  let previousDate = "";
  for (const [index, milestone] of milestones.entries()) {
    if (milestone.quantity <= previousQuantity || milestone.quantity > quantity) throw new Error(`${index + 1}. ara teslim adedi \xF6nceki teslimattan b\xFCy\xFCk olmal\u0131 ve toplam sipari\u015Fi a\u015Fmamal\u0131d\u0131r.`);
    if (!milestone.date) throw new Error(`${index + 1}. ara teslim tarihi zorunludur.`);
    if (previousDate && milestone.date <= previousDate) throw new Error("Ara teslim tarihleri artan s\u0131rada olmal\u0131d\u0131r.");
    if (dueDate && milestone.date > dueDate) throw new Error("Ara teslim tarihi nihai terminden sonra olamaz.");
    previousQuantity = milestone.quantity;
    previousDate = milestone.date;
  }
}
function productionQuantityByDate(seed, batches, product, serial2, readinessEvents) {
  if (seed.productionArea === "cubuk-filtre" && seed.monthlyCustomerDemand) return readinessEvents ? deliveryReadyQuantityFromEvents(seed, readinessEvents, product, serial2) : deliveryReadyQuantityByDate(seed, { batches }, product, serial2);
  const code3 = product.toUpperCase();
  const dueDay = Math.floor(serial2);
  const openingStock = seed.customerDemand ? 0 : Math.max(0, seed.openingStock?.[code3] ?? 0);
  const completed = semiFinishedProduction(seed).filter((entry) => entry.product.toUpperCase() === code3 && Math.floor(turningDeliveryReadyAt(entry.completedAt)) <= dueDay).reduce((sum, entry) => sum + entry.completedQuantity, 0);
  const current = seed.machines.filter((machine) => machine.currentJob.product.toUpperCase() === code3 && Math.floor(turningDeliveryReadyAt(machine.currentJob.end)) <= dueDay).reduce((sum, machine) => sum + machine.currentJob.quantity, 0);
  const planned = batches.filter((batch) => batch.status === "planned" && batch.product.toUpperCase() === code3 && Math.floor(turningDeliveryReadyAt(batch.end)) <= dueDay).reduce((sum, batch) => sum + batch.quantity, 0);
  return openingStock + completed + current + planned;
}
function productionQuantityByTurningDate(seed, batches, product, serial2) {
  const code3 = product.toUpperCase();
  const dueDay = Math.floor(serial2);
  const openingStock = seed.customerDemand ? 0 : Math.max(0, seed.openingStock?.[code3] ?? 0);
  const completed = semiFinishedProduction(seed).filter((entry) => entry.product.toUpperCase() === code3 && Math.floor(entry.completedAt) <= dueDay).reduce((sum, entry) => sum + entry.completedQuantity, 0);
  const current = seed.machines.filter((machine) => machine.currentJob.product.toUpperCase() === code3 && Math.floor(machine.currentJob.end) <= dueDay).reduce((sum, machine) => sum + machine.currentJob.quantity, 0);
  const planned = batches.filter((batch) => batch.status === "planned" && batch.product.toUpperCase() === code3 && Math.floor(batch.end) <= dueDay).reduce((sum, batch) => sum + batch.quantity, 0);
  return openingStock + completed + current + planned;
}
function orderProductionBreakdown(seed, batches, order, readinessEvents) {
  const code3 = order.product.toUpperCase();
  const filterRows = seed.productionArea === "cubuk-filtre" ? filterCommittedSupply(seed, batches).filter((row) => row.product.toUpperCase() === code3) : void 0;
  const existingTotal = filterRows ? filterRows.filter((row) => !row.planned).reduce((sum, row) => sum + row.quantity, 0) : (seed.processStockSettings?.opening ?? []).filter((row) => row.product === code3).reduce((sum, row) => sum + filterSupplyGoodPieces(seed, row.product, row.quantity, row.groupId === "warehouse"), 0) + (seed.customerDemand ? 0 : Math.max(0, seed.openingStock?.[code3] ?? 0)) + semiFinishedProduction(seed).filter((entry) => entry.product.toUpperCase() === code3).reduce((sum, entry) => sum + filterHistoryGoodPieces(seed, entry), 0) + seed.machines.filter((machine) => machine.currentJob.product.toUpperCase() === code3).reduce((sum, machine) => sum + filterSupplyGoodPieces(seed, machine.currentJob.product, machine.currentJob.quantity), 0);
  const plannedTotal = filterRows ? filterRows.filter((row) => row.planned).reduce((sum, row) => sum + row.quantity, 0) : batches.filter((batch) => batch.status === "planned" && batch.product.toUpperCase() === code3).reduce((sum, batch) => sum + filterSupplyGoodPieces(seed, batch.product, batch.quantity), 0);
  const dueSerial = inputDateSerial3(order.dueDate);
  const onTimeTotal = dueSerial ? seed.productionArea === "cubuk-filtre" && seed.activePlanRun?.optimizationGoal === "coarse" && !seed.monthlyCustomerDemand ? productionQuantityByTurningDate(seed, batches, order.product, dueSerial) : productionQuantityByDate(seed, batches, order.product, dueSerial, readinessEvents) : null;
  const productOrders = seed.orders.filter((item) => item.product.toUpperCase() === code3).sort((a, b) => (a.dueDate || "9999").localeCompare(b.dueDate || "9999") || a.sourceRow - b.sourceRow || a.id.localeCompare(b.id));
  const position = productOrders.findIndex((item) => item.id === order.id);
  const priorDemand = productOrders.slice(0, Math.max(0, position)).reduce((sum, item) => sum + item.quantity, 0);
  const limit = position === productOrders.length - 1 || position < 0 ? Number.POSITIVE_INFINITY : order.quantity;
  const allocated = (total) => Math.min(limit, Math.max(0, total - priorDemand));
  const existingProduction = allocated(existingTotal);
  const newlyPlanned = allocated(existingTotal + plannedTotal) - existingProduction;
  const onTimePlanned = onTimeTotal === null ? null : allocated(onTimeTotal);
  return {
    existingProduction,
    newlyPlanned,
    onTimePlanned,
    onTimeDifference: onTimePlanned === null ? null : onTimePlanned - order.quantity
  };
}
function batchSignature(batch) {
  return `${batch.product}|${batch.machineId}|${batch.quantity}`;
}
function multisetDelta(left, right) {
  const counts = /* @__PURE__ */ new Map();
  for (const batch of right) counts.set(batchSignature(batch), (counts.get(batchSignature(batch)) ?? 0) + 1);
  let unmatched = 0;
  for (const batch of left) {
    const key = batchSignature(batch);
    const available = counts.get(key) ?? 0;
    if (available > 0) counts.set(key, available - 1);
    else unmatched += 1;
  }
  return unmatched;
}
function previewOrderRevision(seed, currentResult, request, strategy = "v51") {
  const currentOrder = seed.orders.find((order) => order.id === request.orderId);
  if (!currentOrder) throw new Error("De\u011Fi\u015Ftirilecek sipari\u015F bulunamad\u0131.");
  if (request.quantity < 0) throw new Error("Sipari\u015F miktar\u0131 negatif olamaz.");
  if (!request.reason.trim()) throw new Error("De\u011Fi\u015Fiklik nedeni zorunludur.");
  const requestedMilestones = orderDeliveryMilestones(request);
  if (request.allowPartial && requestedMilestones.length === 0) throw new Error("En az bir ara teslimat ekleyin.");
  validateDeliveryMilestones(requestedMilestones, request.quantity, request.dueDate);
  const revisedSeed = JSON.parse(JSON.stringify(seed));
  const revisedOrder = revisedSeed.orders.find((order) => order.id === request.orderId);
  if (!revisedOrder) throw new Error("Sipari\u015F kopyas\u0131 olu\u015Fturulamad\u0131.");
  revisedOrder.quantity = request.quantity;
  revisedOrder.dueDate = request.dueDate;
  revisedOrder.allowPartial = request.allowPartial;
  revisedOrder.deliveryMilestones = requestedMilestones;
  revisedOrder.partialDeliveryQuantity = requestedMilestones[0]?.quantity ?? 0;
  revisedOrder.partialDeliveryDate = requestedMilestones[0]?.date ?? "";
  const frozen = currentResult.batches.filter((batch) => batch.status === "planned" && (batch.locked || batch.start <= request.freezeThrough));
  const nextResult = runScenario(revisedSeed, frozen, strategy);
  const frozenIds = new Set(frozen.map((batch) => batch.id));
  const currentFlexible = currentResult.batches.filter((batch) => batch.status === "planned" && !frozenIds.has(batch.id));
  const nextFlexible = nextResult.batches.filter((batch) => batch.status === "planned" && !frozenIds.has(batch.id));
  const affectedMachines = revisedSeed.machines.map((machine) => {
    const before = currentResult.batches.filter((batch) => batch.status === "planned" && batch.machineId === machine.id).reduce((sum, batch) => sum + batch.quantity, 0);
    const after = nextResult.batches.filter((batch) => batch.status === "planned" && batch.machineId === machine.id).reduce((sum, batch) => sum + batch.quantity, 0);
    return before === after ? "" : machine.id;
  }).filter(Boolean);
  const checks = [
    ...requestedMilestones,
    ...request.dueDate ? [{ id: "final", quantity: request.quantity, date: request.dueDate }] : []
  ].map((milestone) => {
    const available = productionQuantityByDate(revisedSeed, nextResult.batches, currentOrder.product, inputDateSerial3(milestone.date));
    return { id: milestone.id, required: milestone.quantity, date: milestone.date, available, feasible: available >= milestone.quantity };
  });
  const primaryCheck = checks.find((check) => !check.feasible) ?? checks[0];
  const deliveryRequired = primaryCheck?.required ?? request.quantity;
  const deliveryDate = primaryCheck?.date ?? request.dueDate;
  const availableByDeliveryDate = primaryCheck?.available ?? 0;
  return {
    seed: revisedSeed,
    result: nextResult,
    impact: {
      frozenBatchCount: frozen.length,
      addedBatchCount: multisetDelta(nextFlexible, currentFlexible),
      removedBatchCount: multisetDelta(currentFlexible, nextFlexible),
      plannedDelta: nextResult.summary.planned - currentResult.summary.planned,
      shortageDelta: nextResult.summary.shortage - currentResult.summary.shortage,
      overproductionDelta: nextResult.summary.overproduction - currentResult.summary.overproduction,
      affectedMachines,
      deliveryRequired,
      deliveryDate,
      availableByDeliveryDate,
      deliveryFeasible: checks.length ? checks.every((check) => check.feasible) : null,
      deliveryChecks: checks
    }
  };
}
function manualMachineAllowed(seed, machineId, productCode, diameter) {
  const machine = seed.machines.find((item) => item.id === machineId);
  if (!machine?.active) return false;
  return isMachineEligibleForProduct(seed, machineId, productCode);
}
function scenarioResultFromBatches(seed, batches) {
  const machinesByProduct = /* @__PURE__ */ new Map();
  for (const batch of batches.filter((item) => item.status === "planned")) {
    const code3 = batch.product.toUpperCase();
    machinesByProduct.set(code3, unique([...machinesByProduct.get(code3) ?? [], batch.machineId]));
  }
  const readinessEvents = seed.productionArea === "cubuk-filtre" && seed.monthlyCustomerDemand && seed.orders.some((order) => inputDateSerial3(order.dueDate)) ? buildDeliveryReadinessEvents(seed, { batches }) : void 0;
  const orders = seed.orders.map((order) => {
    const code3 = order.product.toUpperCase();
    const breakdown = orderProductionBreakdown(seed, batches, order, readinessEvents);
    const planned2 = breakdown.existingProduction + breakdown.newlyPlanned;
    return { ...order, planned: planned2, difference: planned2 - order.quantity, ...breakdown, assignedMachines: machinesByProduct.get(code3) ?? order.savedMachines };
  });
  const demand = orders.reduce((sum, order) => sum + order.quantity, 0);
  const planned = orders.reduce((sum, order) => sum + order.planned, 0);
  const plannedBatches = batches.filter((batch) => batch.status === "planned");
  return {
    state: "planned",
    batches,
    orders,
    createdAt: (/* @__PURE__ */ new Date()).toISOString(),
    planRun: seed.activePlanRun,
    summary: {
      demand,
      planned,
      shortage: orders.reduce((sum, order) => sum + Math.max(0, -order.difference), 0),
      overproduction: orders.reduce((sum, order) => sum + Math.max(0, order.difference), 0),
      plannedBatchCount: new Set(plannedBatches.map((batch) => batch.sharedCharge?.id ?? batch.id)).size,
      unplannedBatchCount: batches.filter((batch) => batch.status === "unplanned").length,
      totalSetupHours: plannedBatches.reduce((sum, batch) => sum + (batch.setupHours ?? 0), 0),
      completion: Math.max(0, ...plannedBatches.map((batch) => batch.end)),
      machinesUsed: new Set(plannedBatches.map((batch) => batch.machineId)).size
    }
  };
}
function withoutObsoletePlanRollForward(batch) {
  const { rolledForwardFrom: _rolledForwardFrom, rolledForwardAt: _rolledForwardAt, ...recordedBatch } = batch;
  return recordedBatch;
}
function recalculateOperationalScenario(before, next, sourceBatches) {
  return recalculateOperationalProjection(before, next, sourceBatches, scenarioResultFromBatches);
}
function recalculateOperationalProjection(before, next, sourceBatches, project) {
  const candidate = { ...next, manualBatches: sourceBatches };
  assertTurningIdentityTransition(before, candidate);
  const scope = turningIdentityScope(before);
  if (!scope.machineIds.length) return project(next, recalculateManualBatches(next, sourceBatches));
  const protectedBatch = (batch) => scope.machineIds.includes(batch.machineId) || scope.batchIds.includes(batch.id) || scope.products.includes(batch.product.trim().toUpperCase());
  const healthySeed = { ...next, machines: next.machines.filter((machine) => !scope.machineIds.includes(machine.id)) };
  const healthy = project(healthySeed, recalculateManualBatches(healthySeed, sourceBatches.filter((batch) => !protectedBatch(batch))));
  const byId = new Map(healthy.batches.map((batch) => [batch.id, batch]));
  const batches = sourceBatches.map((batch) => protectedBatch(batch) ? { ...batch } : byId.get(batch.id)).filter(Boolean);
  assertTurningIdentityTransition(before, { ...next, manualBatches: batches });
  return project(next, batches);
}
function assertOperationalMachineIdentity(seed, result, machineId) {
  const baseline = { ...seed, manualBatches: result.batches };
  assertTurningIdentityTransition(baseline, baseline);
  if (turningIdentityScope(baseline).machineIds.includes(machineId)) throw new Error(`${machineId}: Bu tezgah inceleme bekleyen \u015Farja ba\u011Fl\u0131. \xD6nce \u0130ncele ve d\xFCzelt ile kay\u0131tlar\u0131 do\u011Frulay\u0131n.`);
}
function recalculateManualScenario(seed, sourceBatches, options = { allowPlanEndOverflow: true }) {
  return scenarioResultFromBatches(seed, recalculateManualBatches(seed, sourceBatches, options));
}
function recalculateManualBatches(seed, sourceBatches, options = { allowPlanEndOverflow: true }) {
  sourceBatches = reconcileTurningQueue(seed, sourceBatches);
  const products = new Map(seed.products.map((product) => [product.product.toUpperCase(), product]));
  const queues = new Map(seed.machines.map((machine) => [machine.id, []]));
  for (const batch of sourceBatches.filter((item) => item.status === "planned" && item.quantity > 0)) {
    const trace = batch.workOrder?.trim() || batch.id;
    const lock = batch.locked ? "kilitli" : "kilitsiz";
    if (!queues.has(batch.machineId)) throw new Error(`${batch.product} \xB7 ${trace} \xB7 ${batch.machineId} \xB7 ${lock}: kay\u0131tl\u0131 tezgah bulunamad\u0131.`);
    queues.get(batch.machineId)?.push(withoutObsoletePlanRollForward(batch));
  }
  for (const queue of queues.values()) queue.sort((a, b) => a.planColumn - b.planColumn || a.sequence - b.sequence || a.id.localeCompare(b.id));
  const recalculated = [];
  const unplanned = sourceBatches.filter((item) => item.status === "unplanned").map(withoutObsoletePlanRollForward);
  for (const machine of seed.machines) {
    const queue = queues.get(machine.id) ?? [];
    let previousEnd = Math.max(machine.availableStart, machine.currentJob.end);
    let previousProduct = machine.currentJob.product;
    let previousDiameter = machine.currentJob.diameter;
    for (let index = 0; index < queue.length; index += 1) {
      const batch = queue[index];
      const trace = batch.workOrder?.trim() || batch.id;
      const context = `${batch.product} \xB7 ${trace} \xB7 ${machine.id} ${index + 1}. s\u0131ra \xB7 ${batch.locked ? "kilitli" : "kilitsiz"}`;
      const product = products.get(batch.product.toUpperCase());
      if (!product) throw new Error(`${context}: \xFCr\xFCn parametresi bulunamad\u0131.`);
      const pasifOnly = !manualMachineAllowed(seed, machine.id, batch.product, product.diameter) && machine.active && Boolean(product.inactiveMachineIds?.includes(machine.id)) && manualMachineAllowed({ ...seed, products: seed.products.map((item) => item === product ? { ...item, inactiveMachineIds: item.inactiveMachineIds?.filter((id) => id !== machine.id) } : item) }, machine.id, batch.product, product.diameter);
      if (!pasifOnly && !manualMachineAllowed(seed, machine.id, batch.product, product.diameter)) {
        throw new Error(`${context}: \xFCr\xFCn bu tezgahta \xFCretime izinli de\u011Fil. Parametreler\u2019de ${batch.product} \xD7 ${machine.id} uygunlu\u011Funu kontrol edin veya \u015Farj\u0131 uygun bir tezgaha ta\u015F\u0131y\u0131n.`);
      }
      const shiftRate = machine.rates[batch.product.toUpperCase()] ?? 0;
      const dailyRate = shiftRate * machine.shiftFactor * machineCapacityFactor(machine);
      if (dailyRate <= 0) throw new Error(`${context}: \xFCretim h\u0131z\u0131 tan\u0131ml\u0131 de\u011Fil.`);
      const setup = calculateSetup(seed, previousProduct, previousDiameter, batch.product, product.diameter, machine.id);
      const runHours = machineRunHours(seed, machine, batch.product, batch.quantity);
      const timeline = addMachineCapacityHours(seed, machine, Math.max(
        previousEnd,
        seed.monthlyCustomerDemand && Number.isFinite(batch.backwardNotBefore) ? batch.backwardNotBefore : 0,
        Number.isFinite(batch.linkedStart) ? batch.linkedStart : 0
      ), setup.hours + runHours);
      const start = timeline.start;
      const end = timeline.end;
      if (start < machine.availableStart - 1e-8) {
        throw new Error(`${context}: hesaplanan tarih ${formatExcelDate(start)}\u2013${formatExcelDate(end)}; tezgah\u0131n m\xFCsaitlik tarihi ${formatExcelDate(machine.availableStart)}.`);
      }
      if (!options.allowPlanEndOverflow && end >= Math.floor(machine.planEnd) + 1) {
        throw new Error(`${context}: hesaplanan tarih ${formatExcelDate(start)}\u2013${formatExcelDate(end)}; ${machine.id} plan penceresi ${formatExcelDate(machine.availableStart)}\u2013${formatExcelDate(machine.planEnd)}.`);
      }
      recalculated.push({
        ...batch,
        sequence: batch.sequence,
        machineId: machine.id,
        diameter: normalizedDiameter(product.diameter),
        batchSize: product.batchSize,
        dailyRate,
        availableStart: machine.availableStart,
        planEnd: machine.planEnd,
        planColumn: 13 + index,
        start,
        end,
        reason: batch.reason,
        explanation: `Manuel plan: ${machine.id} kuyru\u011Funda ${index + 1}. s\u0131ra. ${setup.label}: ${setup.hours.toFixed(1)} saat; \xFCretim: ${runHours.toFixed(1)} saat.${pasifOnly ? ` Parametre incelemesi: ${batch.product} \xD7 ${machine.id} Pasif; bu i\u015F i\xE7in karar verin.` : ""}`,
        status: "planned",
        setupHours: setup.hours,
        setupType: setup.type,
        runHours
      });
      previousEnd = end;
      previousProduct = batch.product;
      previousDiameter = product.diameter;
    }
  }
  return [...recalculated, ...unplanned].sort((a, b) => a.sequence - b.sequence);
}
function plannedQueuesByMachine(result) {
  const queues = /* @__PURE__ */ new Map();
  for (const batch of result.batches) {
    if (batch.status !== "planned") continue;
    queues.set(batch.machineId, [...queues.get(batch.machineId) ?? [], batch]);
  }
  for (const queue of queues.values()) queue.sort((a, b) => a.planColumn - b.planColumn);
  return queues;
}
function propagateQueueUnlock(queues, throughByMachine, seedUnlockedGroups) {
  const pending = new Set(seedUnlockedGroups);
  while (pending.size) {
    const current = new Set(pending);
    pending.clear();
    for (const [id, list] of queues) {
      const limit = throughByMachine.get(id) ?? -1;
      for (let index = 0; index <= limit; index += 1) {
        const sharedId = list[index].sharedCharge?.id;
        if (sharedId && current.has(sharedId)) {
          for (let dropped = index; dropped <= limit; dropped += 1) {
            const droppedGroup = list[dropped].sharedCharge?.id;
            if (droppedGroup) pending.add(droppedGroup);
          }
          throughByMachine.set(id, index - 1);
          break;
        }
      }
    }
  }
}
function lockQueueThrough(result, machineId, batchId) {
  const queues = plannedQueuesByMachine(result);
  const queue = queues.get(machineId) ?? [];
  const through = queue.findIndex((batch) => batch.id === batchId);
  if (through < 0) throw new Error("Kilitlenecek \u015Farj bu tezgah kuyru\u011Funda bulunamad\u0131.");
  const throughByMachine = /* @__PURE__ */ new Map();
  for (const [id, list] of queues) {
    throughByMachine.set(id, id === machineId ? through : list.reduce((last, batch, index) => batch.locked ? index : last, -1));
  }
  const seedUnlocked = new Set(
    queue.slice(through + 1).map((batch) => batch.sharedCharge?.id).filter((id) => Boolean(id))
  );
  propagateQueueUnlock(queues, throughByMachine, seedUnlocked);
  const pendingLockGroups = new Set(
    queue.slice(0, through + 1).map((batch) => batch.sharedCharge?.id).filter((id) => Boolean(id))
  );
  while (pendingLockGroups.size) {
    const current = new Set(pendingLockGroups);
    pendingLockGroups.clear();
    for (const [id, list] of queues) {
      let limit = throughByMachine.get(id) ?? -1;
      for (let index = limit + 1; index < list.length; index += 1) {
        const sharedId = list[index].sharedCharge?.id;
        if (sharedId && current.has(sharedId)) {
          for (let added = limit + 1; added <= index; added += 1) {
            const addedGroup = list[added].sharedCharge?.id;
            if (addedGroup) pendingLockGroups.add(addedGroup);
          }
          limit = index;
          throughByMachine.set(id, limit);
        }
      }
    }
  }
  const lockedIds = /* @__PURE__ */ new Set();
  for (const [id, list] of queues) {
    const limit = throughByMachine.get(id) ?? -1;
    for (let index = 0; index <= limit; index += 1) lockedIds.add(list[index].id);
  }
  return {
    ...result,
    createdAt: (/* @__PURE__ */ new Date()).toISOString(),
    batches: result.batches.map(
      (batch) => batch.status === "planned" && queues.has(batch.machineId) ? { ...batch, locked: lockedIds.has(batch.id) } : { ...batch }
    )
  };
}
function unlockMachineQueue(result, machineId) {
  const queues = plannedQueuesByMachine(result);
  const queue = queues.get(machineId) ?? [];
  const throughByMachine = /* @__PURE__ */ new Map();
  for (const [id, list] of queues) {
    throughByMachine.set(id, id === machineId ? -1 : list.reduce((last, batch, index) => batch.locked ? index : last, -1));
  }
  const seedUnlocked = new Set(
    queue.map((batch) => batch.sharedCharge?.id).filter((id) => Boolean(id))
  );
  propagateQueueUnlock(queues, throughByMachine, seedUnlocked);
  const lockedIds = /* @__PURE__ */ new Set();
  for (const [id, list] of queues) {
    const limit = throughByMachine.get(id) ?? -1;
    for (let index = 0; index <= limit; index += 1) lockedIds.add(list[index].id);
  }
  return {
    ...result,
    createdAt: (/* @__PURE__ */ new Date()).toISOString(),
    batches: result.batches.map(
      (batch) => batch.status === "planned" && queues.has(batch.machineId) ? { ...batch, locked: lockedIds.has(batch.id) } : batch.machineId === machineId ? { ...batch, locked: false } : { ...batch }
    )
  };
}
function setAllMachineQueueLocks(result, locked) {
  if (typeof locked !== "boolean") throw new Error("Kuyruk kilidi se\xE7imi ge\xE7ersiz.");
  return { ...result, createdAt: (/* @__PURE__ */ new Date()).toISOString(), batches: result.batches.map((batch) => batch.status === "planned" ? { ...batch, locked } : { ...batch }) };
}
function updateMachineCurrentJob(seed, result, machineId, input, remainingAsOf) {
  const nextSeed = JSON.parse(JSON.stringify(seed));
  const machine = nextSeed.machines.find((item) => item.id === machineId);
  if (!machine) throw new Error(`${machineId} tezgah\u0131 bulunamad\u0131.`);
  if (hasProtectedProductionRemainder(nextSeed, machine.currentJob.batchId, machine.currentJob.interruptionId) && (input.product !== machine.currentJob.product || input.workOrder.trim() !== machine.currentJob.workOrder || input.originalQuantity !== machine.currentJob.quantity)) throw new Error("Yar\u0131m kalan mevcut i\u015Fin kimli\u011Fi ve toplam adedi de\u011Fi\u015Ftirilemez; Mevcut i\u015Fi de\u011Fi\u015Ftir ak\u0131\u015F\u0131n\u0131 kullan\u0131n.");
  const product = nextSeed.products.find((item) => item.product.toUpperCase() === input.product.toUpperCase());
  if (machine.currentJob.sharedCharge && (input.product !== machine.currentJob.product || input.originalQuantity !== machine.currentJob.quantity || input.workOrder.trim() !== machine.currentJob.workOrder)) throw new Error("Ortak \u015Farj\u0131n kimli\u011Fi ve atanm\u0131\u015F toplam adedi bu pencereden de\u011Fi\u015Ftirilemez.");
  const matchesRecordedCurrentJob = machine.currentJob.product.toUpperCase() === input.product.toUpperCase();
  if (!turningEnabled(nextSeed.processMasterData, input.product) && (!matchesRecordedCurrentJob || machine.currentJob.quantity <= 0)) throw new Error("Bu tipin Torna prosesi Pasif; yeni Torna i\u015Fi ba\u015Flat\u0131lamaz.");
  if (!product && !matchesRecordedCurrentJob) throw new Error("Ge\xE7erli bir \xFCr\xFCn se\xE7in.");
  if (input.originalQuantity <= 0 || input.remainingQuantity < 0 || input.remainingQuantity > input.originalQuantity) throw new Error("Kalan miktar 0 ile orijinal miktar aras\u0131nda olmal\u0131d\u0131r.");
  if (!input.start) throw new Error("\xDCretim ba\u015Flang\u0131\xE7 tarihi zorunludur.");
  if (!remainingAsOf) throw new Error("Kalan miktar\u0131n ge\xE7erli oldu\u011Fu tarih zorunludur.");
  const productCode = product?.product ?? machine.currentJob.product;
  const suppliedShiftRate = Number(input.shiftRate ?? 0);
  if (suppliedShiftRate > 0) machine.rates[productCode.toUpperCase()] = suppliedShiftRate;
  const configuredBaseRate = machine.rates[productCode.toUpperCase()] ?? 0;
  const recordedCurrentRate = machine.currentJob.product.toUpperCase() === productCode.toUpperCase() ? machine.currentJob.dailyRate : 0;
  const dailyRate = configuredBaseRate > 0 ? configuredBaseRate * machine.shiftFactor * machineCapacityFactor(machine) : recordedCurrentRate;
  if (dailyRate <= 0) throw new Error(`${productCode} \xD7 ${machineId} \xFCretim h\u0131z\u0131 tan\u0131ml\u0131 de\u011Fil.`);
  const calculationStart = Math.max(input.start, remainingAsOf);
  const shiftHours = getSetupSettings(nextSeed).shiftHours;
  const hourlyRate = configuredBaseRate > 0 ? configuredBaseRate / shiftHours * machineCapacityFactor(machine) : recordedCurrentRate / (shiftHours * Math.max(1, machine.shiftFactor));
  const end = input.remainingQuantity > 0 ? addMachineCapacityHours(nextSeed, machine, calculationStart, input.remainingQuantity / hourlyRate).end : calculationStart;
  machine.currentJob = { ...matchesRecordedCurrentJob && machine.currentJob.sharedCharge ? { sharedCharge: machine.currentJob.sharedCharge } : {}, batchId: matchesRecordedCurrentJob ? machine.currentJob.batchId : void 0, interruptionId: matchesRecordedCurrentJob ? machine.currentJob.interruptionId : void 0, workOrder: input.workOrder.trim(), product: productCode, quantity: input.originalQuantity, originalQuantity: input.originalQuantity, remainingQuantity: input.remainingQuantity, remainingAsOf: calculationStart, start: input.start, end, dailyRate, diameter: product ? normalizedDiameter(product.diameter) : machine.currentJob.diameter };
  machine.availableStart = end;
  machine.operationalAvailableStart = end;
  const nextResult = result.state === "planned" ? recalculateOperationalScenario({ ...seed, manualBatches: result.batches }, nextSeed, result.batches) : result;
  return { seed: nextSeed, result: nextResult };
}
function rollForwardUnfinishedProduction(seed, asOf = inputDateSerial3(factoryDateInput()), options = {}) {
  if (!Number.isFinite(asOf) || asOf <= 0) throw new Error("Devreden i\u015Fler i\xE7in ge\xE7erli bir ba\u015Flang\u0131\xE7 tarihi se\xE7in.");
  const rollTurning = options.turning ?? true;
  const rollDownstream = options.downstream ?? true;
  const rolledMachineIds = [];
  const shiftHours = getSetupSettings(seed).shiftHours;
  for (const machine of rollTurning ? seed.machines : []) {
    const current = machine.currentJob;
    const remaining = current.remainingQuantity ?? current.quantity;
    const originalCurrentBoundary = isProductCode(current.product, seed) && remaining > 0 ? current.end : 0;
    const originalOperationalBoundary = Math.max(machine.operationalAvailableStart ?? machine.availableStart, originalCurrentBoundary);
    const planningWindowDays = Math.max(1, Math.floor(machine.planEnd) - Math.floor(originalOperationalBoundary));
    if (originalOperationalBoundary < asOf) {
      machine.planEnd = Math.max(machine.planEnd, Math.floor(asOf) + planningWindowDays);
    }
    const unfinishedPastJob = isProductCode(current.product, seed) && remaining > 0 && current.end < asOf;
    if (unfinishedPastJob) {
      current.rolledForwardFrom = current.rolledForwardFrom ?? current.end;
      current.rolledForwardAt = excelSerialToDate(asOf).toISOString();
      const configuredShiftRate = machine.rates[current.product.toUpperCase()] ?? 0;
      const configuredHourlyRate = configuredShiftRate > 0 ? configuredShiftRate / shiftHours * machineCapacityFactor(machine) : 0;
      const recordedHourlyRate = current.dailyRate > 0 ? current.dailyRate / (shiftHours * Math.max(1, machine.shiftFactor)) : 0;
      const hourlyRate = configuredHourlyRate || recordedHourlyRate;
      if (hourlyRate > 0 && machine.shiftFactor > 0) {
        const timeline = addMachineCapacityHours(seed, machine, asOf, remaining / hourlyRate);
        current.start = timeline.start;
        current.end = timeline.end;
      } else {
        current.start = asOf;
        current.end = asOf;
      }
      machine.availableStart = current.end;
      machine.operationalAvailableStart = current.end;
      rolledMachineIds.push(machine.id);
      continue;
    }
    const currentBoundary = isProductCode(current.product, seed) && remaining > 0 ? current.end : 0;
    const operational = machine.operationalAvailableStart ?? machine.availableStart;
    const floor = Math.max(asOf, operational, currentBoundary);
    machine.availableStart = floor;
    machine.operationalAvailableStart = floor;
  }
  for (const lot of rollDownstream ? seed.wipLots ?? [] : []) {
    const unfinished = lot.availableQuantity > 0 && lot.stage !== "delivery-ready" && lot.stage !== "delivered" && lot.stage !== "scrapped";
    if (!unfinished || lot.readyAt >= asOf) continue;
    lot.rolledForwardFrom = lot.rolledForwardFrom ?? lot.readyAt;
    lot.rolledForwardAt = excelSerialToDate(asOf).toISOString();
    lot.readyAt = asOf;
  }
  return rolledMachineIds;
}
function requireTurningRemainderAction(assigned, completed, action) {
  if (action !== void 0 && action !== null && action !== "" && action !== "keep" && action !== "scrap") throw new Error("Ge\xE7ersiz kalan miktar i\u015Flemi.");
  if (!Number.isInteger(completed) || completed <= 0 || completed > assigned) throw new Error("Fiili tamamlanan adet toplam adedi a\u015Fmayan pozitif tam say\u0131 olmal\u0131d\u0131r.");
  if (completed < assigned && action !== "keep" && action !== "scrap") {
    const recovery = action == null ? " Eski sekmeden gelen bu i\u015Flem kaydedilmedi. Bekleyen iste\u011Fi Bu i\u015Flemi daha sonra incele \u2192 Yedekle ve beklemeden \xE7\u0131kar ile koruyun. Sonra sayfay\u0131 yenileyip i\u015Flemi yeniden a\xE7\u0131n." : "";
    throw new Error(`Kalan miktar i\xE7in Tornada devam et veya Iskartaya ay\u0131r se\xE7in.${recovery}`);
  }
  return completed < assigned ? action : void 0;
}
function completeMachineCurrentJob(seed, result, machineId, completedAt, completedQuantity, remainderAction = "keep") {
  assertOperationalMachineIdentity(seed, result, machineId);
  const nextSeed = JSON.parse(JSON.stringify(seed));
  const machine = nextSeed.machines.find((item) => item.id === machineId);
  if (!machine) throw new Error(`${machineId} tezgah\u0131 bulunamad\u0131.`);
  const current = machine.currentJob;
  if (!isProductCode(current.product, seed) || current.quantity <= 0) throw new Error("Ar\u015Five al\u0131nacak aktif \xFCretim i\u015Fi bulunamad\u0131.");
  if (!Number.isFinite(completedAt) || !completedAt || completedAt < current.start) throw new Error("Tamamlanma tarihi \xFCretim ba\u015Flang\u0131c\u0131ndan \xF6nce olamaz.");
  const originalQuantity = current.originalQuantity ?? current.quantity;
  if (!Number.isSafeInteger(originalQuantity) || originalQuantity <= 0) throw new Error("Mevcut i\u015Fin toplam adedi ge\xE7ersiz.");
  const actualQuantity = completedQuantity ?? originalQuantity;
  if (!Number.isInteger(actualQuantity) || actualQuantity <= 0) throw new Error("Fiili tamamlanan adet s\u0131f\u0131rdan b\xFCy\xFCk tam say\u0131 olmal\u0131d\u0131r.");
  if (actualQuantity > originalQuantity) throw new Error("Fiili tamamlanan adet mevcut i\u015Fin toplam adedini a\u015Famaz.");
  requireTurningRemainderAction(originalQuantity, actualQuantity, remainderAction);
  if (hasActiveProductionInterruption(nextSeed, current.batchId, current.interruptionId) && actualQuantity !== current.quantity && !(remainderAction === "scrap" && originalQuantity === current.quantity)) throw new Error("Yar\u0131m kalan \u015Farj\u0131n kalan adedini tamamlay\u0131n; yeniden ara vermek i\xE7in Mevcut i\u015Fi de\u011Fi\u015Ftir kullan\u0131n.");
  const loss = remainderAction === "scrap" ? originalQuantity - actualQuantity : 0;
  const partial = actualQuantity < originalQuantity && !loss;
  if (partial && result.batches.some((batch) => batch.machineId === machineId && batch.locked)) throw new Error("Kalan i\u015Fi ilk s\u0131raya eklemek i\xE7in tezgah kuyru\u011Fundaki kilitleri \xF6nce kald\u0131r\u0131n.");
  const splitId = partial ? `split-${crypto.randomUUID()}` : void 0;
  const chargeId = current.batchId ?? `remainder-${crypto.randomUUID()}`;
  const archivedAt = (/* @__PURE__ */ new Date()).toISOString();
  const archived = {
    sourceBatchId: partial ? `output-${splitId}` : current.batchId,
    ...current.sharedCharge ? { sharedCharge: current.sharedCharge } : {},
    interruptionIds: splitId ? [splitId] : void 0,
    id: `history-${crypto.randomUUID()}`,
    machineId,
    machineName: machine.name,
    workOrder: current.workOrder,
    product: current.product,
    originalQuantity: actualQuantity < originalQuantity ? actualQuantity : originalQuantity,
    completedQuantity: actualQuantity,
    start: current.start,
    plannedEnd: current.end,
    completedAt,
    archivedAt,
    process: "turning",
    inventoryStatus: "semi-finished",
    statusChangedAt: archivedAt
  };
  archived.sourceBatchId ??= archived.id;
  const currentRouteKey = currentJobRouteIdentity(machine);
  nextSeed.processOperationOverrides = (nextSeed.processOperationOverrides ?? []).map((item) => item.batchId === `current:${machineId}` && item.sourceCurrentJobKey === currentRouteKey ? { ...item, batchId: archived.sourceBatchId, sourceCurrentJobKey: void 0 } : item);
  const scrapped = loss > 0 ? {
    ...archived,
    id: `history-scrap-${crypto.randomUUID()}`,
    sourceBatchId: `scrap-output-${crypto.randomUUID()}`,
    originalQuantity: loss,
    completedQuantity: loss,
    inventoryStatus: "scrapped",
    scrappedAt: archivedAt,
    splitKind: "scrap",
    statusChangeReason: `Torna tamamlama s\u0131ras\u0131nda ${loss} adet \u0131skarta.`
  } : void 0;
  nextSeed.productionHistory = [archived, ...scrapped ? [scrapped] : [], ...nextSeed.productionHistory ?? []];
  const queue = result.batches.filter((batch) => batch.status === "planned" && batch.machineId === machineId).sort((a, b) => a.planColumn - b.planColumn);
  let remainder;
  if (partial) {
    const product = nextSeed.products.find((item) => item.product === current.product);
    if (!product) throw new Error("Kalan \xFCretimin \xFCr\xFCn parametreleri bulunamad\u0131.");
    remainder = {
      ...current.sharedCharge ? { sharedCharge: current.sharedCharge } : {},
      id: chargeId,
      interruptionId: splitId,
      sequence: Math.max(0, ...result.batches.map((b) => b.sequence)) + 1,
      product: current.product,
      workOrder: current.workOrder,
      quantity: originalQuantity - actualQuantity,
      orderQuantity: originalQuantity,
      machineId,
      diameter: current.diameter,
      batchSize: product.batchSize,
      dailyRate: current.dailyRate,
      availableStart: completedAt,
      planEnd: machine.planEnd,
      start: completedAt,
      end: completedAt,
      planColumn: 13,
      existingQuantity: 0,
      status: "planned",
      locked: false,
      manuallyPlaced: true,
      reason: "K\u0131smi \xFCretimin kalan i\u015Fi.",
      explanation: ""
    };
    nextSeed.productionInterruptions = [...nextSeed.productionInterruptions ?? [], {
      id: splitId,
      kind: "partial-completion",
      chargeId,
      process: "turning",
      resourceId: machineId,
      product: current.product,
      workOrder: current.workOrder,
      producedQuantity: actualQuantity,
      remainingQuantity: remainder.quantity,
      occurredAt: completedAt,
      reason: "Torna k\u0131smi tamamlama",
      turningBatch: remainder
    }];
  }
  const promotedBatch = queue[0] ?? remainder;
  const remainingBatches = result.batches.filter((batch) => batch.id !== promotedBatch?.id).map((batch) => partial && batch.machineId === machineId && batch.status === "planned" ? { ...batch, planColumn: 14 + queue.filter((b) => b.id !== promotedBatch?.id).findIndex((b) => b.id === batch.id) } : batch);
  if (remainder && promotedBatch !== remainder) remainingBatches.push(remainder);
  if (promotedBatch) {
    const product = nextSeed.products.find((item) => item.product.toUpperCase() === promotedBatch.product.toUpperCase());
    const dailyRate = (machine.rates[promotedBatch.product.toUpperCase()] ?? 0) * machine.shiftFactor * machineCapacityFactor(machine);
    if (!product || dailyRate <= 0) throw new Error("S\u0131radaki i\u015F mevcut \xFCretime ge\xE7irilemedi; \xFCr\xFCn veya h\u0131z bilgisi eksik.");
    const setup = calculateSetup(nextSeed, current.product, current.diameter, promotedBatch.product, product.diameter, machine.id);
    const runHours = machineRunHours(nextSeed, machine, promotedBatch.product, promotedBatch.quantity);
    const timeline = addMachineCapacityHours(nextSeed, machine, completedAt, setup.hours + runHours);
    machine.currentJob = { ...promotedBatch.sharedCharge ? { sharedCharge: promotedBatch.sharedCharge } : {}, batchId: promotedBatch.id, interruptionId: promotedBatch.interruptionId, workOrder: promotedBatch.workOrder ?? "", product: promotedBatch.product, quantity: promotedBatch.quantity, originalQuantity: promotedBatch.quantity, remainingQuantity: promotedBatch.quantity, start: timeline.start, end: timeline.end, dailyRate, diameter: normalizedDiameter(product.diameter) };
    machine.availableStart = timeline.end;
    machine.operationalAvailableStart = timeline.end;
  } else {
    machine.currentJob = { workOrder: "", product: "", quantity: 0, originalQuantity: 0, remainingQuantity: 0, start: completedAt, end: completedAt, dailyRate: 0, diameter: "" };
    machine.availableStart = completedAt;
    machine.operationalAvailableStart = completedAt;
  }
  if (!partial) finishProductionInterruptions(nextSeed, current.batchId, "turning", completedAt);
  if (promotedBatch?.interruptionId) {
    const pause = nextSeed.productionInterruptions?.find((item) => item.id === promotedBatch.interruptionId);
    if (pause) pause.resumedAt = completedAt;
  }
  const nextResult = partial ? scenarioResultFromBatches(nextSeed, [
    ...recalculateManualScenario({ ...nextSeed, machines: [machine] }, remainingBatches.filter((b) => b.machineId === machineId)).batches,
    ...remainingBatches.filter((b) => b.machineId !== machineId)
  ]) : result.state === "planned" ? recalculateOperationalScenario({ ...seed, manualBatches: result.batches }, nextSeed, remainingBatches) : result;
  if (splitId) {
    const split = nextSeed.productionInterruptions.find((item) => item.id === splitId);
    split.turningBatch = { ...nextResult.batches.find((b) => b.id === chargeId) ?? remainder };
    nextSeed.manualBatches = nextResult.batches;
    nextSeed.planNeedsRecalculation = true;
    nextSeed.lastAutomaticPlan = void 0;
    nextSeed.planRunSequence = void 0;
  }
  return { seed: nextSeed, result: nextResult, archived, scrapped, promotedBatch };
}
function updateProductionHistoryStatus(seed, result, entryId, inventoryStatus, actionDate = "", changedAt = (/* @__PURE__ */ new Date()).toISOString(), changeReason = "", changedBy = "Planlama oturumu") {
  const nextSeed = JSON.parse(JSON.stringify(seed));
  const entry = (nextSeed.productionHistory ?? []).find((item) => item.id === entryId);
  if (!entry) throw new Error("\xDCretim ar\u015Fivi kayd\u0131 bulunamad\u0131.");
  if (entry.inventoryStatus === "voided") throw new Error("\u0130ptal edilmi\u015F kay\u0131t de\u011Fi\u015Ftirilemez.");
  if (!["semi-finished", "delivered", "scrapped", "voided"].includes(inventoryStatus)) throw new Error("Ar\u015Fiv durumu ge\xE7ersiz.");
  if (entry.inventoryStatus === "delivered" && !["delivered", "semi-finished"].includes(inventoryStatus)) throw new Error("\xD6nce teslimat\u0131 geri al\u0131n.");
  if (entry.inventoryStatus === "scrapped" && inventoryStatus === "delivered") throw new Error("\xD6nce \u0131skartay\u0131 yar\u0131 mamule geri al\u0131n.");
  const hidingScrap = entry.inventoryStatus === "scrapped" && inventoryStatus === "voided";
  const reversingTerminalState = inventoryStatus === "semi-finished" && (entry.inventoryStatus === "delivered" || entry.inventoryStatus === "scrapped");
  if (reversingTerminalState && !changeReason.trim()) throw new Error("Yar\u0131 mamule geri alma nedeni zorunludur.");
  const deliveryDate = actionDate.slice(0, 10);
  if (inventoryStatus === "delivered" && !/^\d{4}-\d{2}-\d{2}(T\d{2}:\d{2})?$/.test(actionDate)) {
    throw new Error("Teslim tarihini se\xE7in.");
  }
  if (inventoryStatus === "delivered" && inputDateSerial3(deliveryDate) < Math.floor(entry.completedAt)) {
    throw new Error("Teslim tarihi \xFCretimin tamamlanma tarihinden \xF6nce olamaz.");
  }
  if (inventoryStatus === "delivered" && (deliveryDate > factoryDateInput(changedAt) || actionDate.includes("T") && factoryDateTimeToIso(actionDate) > changedAt)) {
    throw new Error("Fiili teslim tarihi gelecekte olamaz.");
  }
  entry.inventoryStatus = inventoryStatus;
  entry.statusChangedAt = changedAt;
  entry.statusChangeReason = changeReason.trim() || void 0;
  entry.statusChangedBy = changedBy.trim() || "Planlama oturumu";
  if (inventoryStatus === "delivered") {
    entry.deliveredAt = deliveryDate;
    entry.deliveredAtTime = actionDate.includes("T") ? factoryDateTimeToIso(actionDate) : factoryDateInput(changedAt) === deliveryDate ? changedAt : (/* @__PURE__ */ new Date(`${deliveryDate}T00:00:00+03:00`)).toISOString();
    delete entry.scrappedAt;
    delete entry.voidedAt;
  } else if (inventoryStatus === "semi-finished") {
    delete entry.deliveredAt;
    delete entry.deliveredAtTime;
    delete entry.scrappedAt;
    delete entry.voidedAt;
  } else if (inventoryStatus === "scrapped") {
    entry.scrappedAt = actionDate || changedAt;
    delete entry.deliveredAt;
    delete entry.deliveredAtTime;
    delete entry.voidedAt;
  } else {
    entry.voidedAt = changedAt;
    delete entry.deliveredAt;
    delete entry.deliveredAtTime;
    delete entry.scrappedAt;
  }
  const nextResult = result.state === "planned" && !hidingScrap ? recalculateOperationalScenario({ ...seed, manualBatches: result.batches }, nextSeed, result.batches) : result;
  return { seed: nextSeed, result: nextResult, entry };
}
function validateProductionActuals(entry, actualQuantity, completedAt) {
  if (!Number.isInteger(actualQuantity) || actualQuantity <= 0) {
    throw new Error("Fiili tamamlanan adet s\u0131f\u0131rdan b\xFCy\xFCk tam say\u0131 olmal\u0131d\u0131r.");
  }
  if (!Number.isFinite(completedAt) || completedAt < Math.floor(entry.start)) {
    throw new Error("Tamamlanma tarihi planlanan ba\u015Flang\u0131\xE7tan \xF6nce olamaz.");
  }
  if (entry.deliveredAt && Math.floor(completedAt) > inputDateSerial3(entry.deliveredAt)) {
    throw new Error("Tamamlanma tarihi teslim tarihinden sonra olamaz.");
  }
}
function updateProductionHistoryEntry(seed, result, entryId, actualQuantity, completedAt, changedAt = (/* @__PURE__ */ new Date()).toISOString()) {
  const nextSeed = JSON.parse(JSON.stringify(seed));
  const entry = (nextSeed.productionHistory ?? []).find((item) => item.id === entryId);
  if (!entry) throw new Error("\xDCretim ar\u015Fivi kayd\u0131 bulunamad\u0131.");
  if (entry.inventoryStatus === "voided") throw new Error("\u0130ptal edilmi\u015F kay\u0131t de\u011Fi\u015Ftirilemez.");
  validateProductionActuals(entry, actualQuantity, completedAt);
  entry.completedQuantity = actualQuantity;
  entry.completedAt = completedAt;
  entry.statusChangedAt = changedAt;
  const nextResult = result.state === "planned" ? recalculateOperationalScenario({ ...seed, manualBatches: result.batches }, nextSeed, result.batches) : result;
  return { seed: nextSeed, result: nextResult, entry };
}
function allocateProductionHistoryEntry(seed, result, entryId, input, changedAt = (/* @__PURE__ */ new Date()).toISOString(), applyRelatedQuantities) {
  const nextSeed = JSON.parse(JSON.stringify(seed));
  const history = nextSeed.productionHistory ?? [];
  const entryIndex = history.findIndex((item) => item.id === entryId);
  if (entryIndex < 0) throw new Error("\xDCretim ar\u015Fivi kayd\u0131 bulunamad\u0131.");
  const entry = history[entryIndex];
  if (entry.inventoryStatus !== "semi-finished") throw new Error("Yaln\u0131zca yar\u0131 mamul kay\u0131t teslim veya \u0131skarta olarak ayr\u0131labilir.");
  validateProductionActuals(entry, input.actualQuantity, input.completedAt);
  if (!Number.isInteger(input.deliveredQuantity) || input.deliveredQuantity < 0 || input.deliveredQuantity > input.actualQuantity) {
    throw new Error("Teslim adedi s\u0131f\u0131r ile fiili tamamlanan adet aras\u0131nda tam say\u0131 olmal\u0131d\u0131r.");
  }
  if (input.deliveredQuantity > 0) {
    validateFilterShipment(seed, entry.product, input.deliveredQuantity);
    if (!/^\d{4}-\d{2}-\d{2}(T\d{2}:\d{2})?$/.test(input.deliveryDate)) throw new Error("Teslim tarihini se\xE7in.");
    if (inputDateSerial3(input.deliveryDate.slice(0, 10)) < Math.floor(input.completedAt)) {
      throw new Error("Teslim tarihi \xFCretimin tamamlanma tarihinden \xF6nce olamaz.");
    }
  }
  const remainder = input.actualQuantity - input.deliveredQuantity;
  if (input.deliveredQuantity === 0 && input.remainderAction === "keep") {
    throw new Error("Teslim adedi girin veya tamam\u0131n\u0131 \u0131skartaya ay\u0131r\u0131n.");
  }
  const base = { ...entry, completedAt: input.completedAt, statusChangedAt: changedAt };
  const created = [];
  if (input.deliveredQuantity > 0) {
    created.push({
      ...base,
      id: remainder ? `${entry.id}-teslim-${Date.now()}` : entry.id,
      originalQuantity: input.deliveredQuantity,
      completedQuantity: input.deliveredQuantity,
      inventoryStatus: "delivered",
      deliveredAt: input.deliveryDate.slice(0, 10),
      deliveredAtTime: input.deliveryDate.includes("T") ? factoryDateTimeToIso(input.deliveryDate) : factoryDateInput(changedAt) === input.deliveryDate ? changedAt : (/* @__PURE__ */ new Date(`${input.deliveryDate}T00:00:00+03:00`)).toISOString(),
      sourceEntryId: remainder ? entry.id : entry.sourceEntryId,
      splitKind: remainder ? "delivery" : entry.splitKind,
      scrappedAt: void 0,
      voidedAt: void 0
    });
  }
  if (remainder > 0) {
    created.push({
      ...base,
      id: input.deliveredQuantity > 0 ? entry.id : `${entry.id}-iskarta-${Date.now()}`,
      originalQuantity: remainder,
      completedQuantity: remainder,
      inventoryStatus: input.remainderAction === "scrap" ? "scrapped" : "semi-finished",
      deliveredAt: void 0,
      deliveredAtTime: void 0,
      scrappedAt: input.remainderAction === "scrap" ? changedAt : void 0,
      voidedAt: void 0,
      sourceEntryId: input.remainderAction === "scrap" ? entry.id : entry.sourceEntryId,
      splitKind: input.remainderAction === "scrap" ? "scrap" : entry.splitKind
    });
  }
  if (!remainder && input.deliveredQuantity === 0) {
    created.push({ ...base, completedQuantity: input.actualQuantity, originalQuantity: input.actualQuantity, inventoryStatus: "scrapped", scrappedAt: changedAt, deliveredAt: void 0, deliveredAtTime: void 0, voidedAt: void 0, splitKind: "scrap" });
  }
  history.splice(entryIndex, 1, ...created);
  nextSeed.productionHistory = history;
  applyRelatedQuantities?.(nextSeed, created);
  const nextResult = result.state === "planned" ? recalculateOperationalScenario({ ...seed, manualBatches: result.batches }, nextSeed, result.batches) : result;
  return { seed: nextSeed, result: nextResult, entries: created };
}

// lib/process-lead-time.ts
var FILTER_WAIT_RESOURCE = "CF-BEKLEME";
function applyProcessLeadStages(seed, start, stages) {
  const resource = { id: FILTER_WAIT_RESOURCE, shiftFactor: seed.filterWaitShifts ?? 1, finishOffset: 0 };
  let cursor = start;
  for (const stage of stages ?? []) {
    if (!Number.isFinite(stage.days) || stage.days < 0 || stage.days > 366) throw new Error("Bekleme s\xFCresi 0\u2013366 g\xFCn aras\u0131nda olmal\u0131d\u0131r.");
    if (stage.days === 0) continue;
    if (stage.calendarMode && resource.shiftFactor === 0 && !seed.calendarEvents?.some((event) => event.machineId === FILTER_WAIT_RESOURCE && event.end >= Math.floor(cursor) && (event.shiftCount ?? 0) > 0) && !seed.holidays.some((holiday) => holiday.serial >= Math.floor(cursor) && (holiday.workingShifts ?? 0) > 0)) throw new Error("\xC7ubuk Filtre bekleme takviminde \xE7al\u0131\u015Fma vardiyas\u0131 yok.");
    if (stage.calendarMode === "workdays") {
      if (!Number.isInteger(stage.days) || stage.days < 0) throw new Error("Bekleme i\u015F g\xFCn\xFC pozitif tam say\u0131 veya s\u0131f\u0131r olmal\u0131d\u0131r.");
      const fraction = cursor - Math.floor(cursor);
      let day = Math.floor(cursor), remaining = stage.days, guard = 0;
      while (remaining > 0) {
        day++;
        if (machineDayCapacity(seed, resource, day).shifts > 0) remaining--;
        if (++guard > 36600) throw new Error("\xC7ubuk Filtre bekleme takviminde \xE7al\u0131\u015Fma g\xFCn\xFC bulunamad\u0131.");
      }
      cursor = day + fraction;
    } else if (stage.calendarMode === "workhours") {
      cursor = addMachineCapacityHours(seed, resource, cursor, stage.days * 24).end;
    } else cursor += stage.days;
  }
  return cursor;
}

// lib/production-archive.ts
function productionHistoryLots(seed, entry) {
  const matching = (seed.wipLots ?? []).filter((lot) => lot.product === entry.product && lot.workOrder === entry.workOrder);
  if (entry.inventoryStatus === "delivered" && entry.wipAllocations) return matching.filter((lot) => entry.wipAllocations.some((item) => item.lotId === lot.id));
  const direct = matching.filter((lot) => lot.sourceHistoryEntryId === entry.id);
  return direct.length ? direct : matching.filter((lot) => lot.sourceHistoryEntryId === entry.sourceEntryId);
}

// lib/wip-ledger.ts
var terminalStages = /* @__PURE__ */ new Set(["delivered", "scrapped"]);
function isoNow(value) {
  return value ?? (/* @__PURE__ */ new Date()).toISOString();
}
function movementId(seed, recordedAt) {
  return `wip-move-${recordedAt.replace(/\D/g, "").slice(0, 17)}-${(seed.wipMovements ?? []).length + 1}`;
}
function lotId(seed, sourceId) {
  const base = `wip-${sourceId}`;
  if (!(seed.wipLots ?? []).some((lot) => lot.id === base)) return base;
  let ordinal = 2;
  while ((seed.wipLots ?? []).some((lot) => lot.id === `${base}-${ordinal}`)) ordinal += 1;
  return `${base}-${ordinal}`;
}
function appendMovement(seed, movement) {
  const value = { ...movement, id: movementId(seed, movement.recordedAt) };
  seed.wipMovements = [...seed.wipMovements ?? [], value].slice(-2e3);
  return value;
}
function addWipWaitWorkdays(seed, startValue, workdaysValue) {
  return addFactoryWorkdays(seed, startValue, workdaysValue);
}
function nextProcessForWipStage(stage) {
  if (stage === "quality-hold" || stage === "drilling-queue") return "drilling";
  if (stage === "deburring-queue") return "deburring";
  if (stage === "washing-buffer" || stage === "gkm-buffer" || stage === "gkm-queue") return "gkm";
  return void 0;
}
function reserveFilterMillingPortion(seed, sourceId, quantity, occurredAt) {
  const source = seed.wipLots?.find((item) => item.id === sourceId);
  if (seed.productionArea !== "cubuk-filtre" || !source || source.nextProcess !== "milling" || source.stage === "on-hold" || source.stage === "unclassified" || !Number.isSafeInteger(quantity) || quantity <= 0 || quantity >= source.availableQuantity || !Number.isFinite(occurredAt) || occurredAt < source.readyAt - 1e-8 || seed.processCurrentJobs?.some((item) => item.wipLotId === source.id)) throw new Error("Freze i\xE7in b\xF6l\xFCnecek haz\u0131r yar\u0131 mam\xFCl adedini kontrol edin.");
  const recordedAt = isoNow();
  const sharedCharge = source.sharedCharge ?? { id: source.id, quantity: source.availableQuantity };
  const portion = {
    ...structuredClone(source),
    sharedCharge,
    id: lotId(seed, source.sourceHistoryEntryId),
    parentLotId: source.id,
    originalQuantity: quantity,
    availableQuantity: quantity,
    deliveredQuantity: 0,
    scrappedQuantity: 0,
    createdAt: recordedAt,
    updatedAt: recordedAt
  };
  source.sharedCharge = sharedCharge;
  source.originalQuantity -= quantity;
  source.availableQuantity -= quantity;
  source.updatedAt = recordedAt;
  seed.wipLots = [...seed.wipLots ?? [], portion];
  appendMovement(seed, {
    lotId: source.id,
    kind: "split",
    quantity,
    fromStage: source.stage,
    toStage: source.stage,
    occurredAt,
    recordedAt,
    note: `${portion.id}: Freze ortak \u015Farj\u0131 i\xE7in ayr\u0131 miktar atand\u0131; \xFCretim tamamlanmad\u0131.`
  });
  return portion;
}
function turningReadyAt(seed, completedAt, family, applyCurrentFlow) {
  if (!applyCurrentFlow) return addWipWaitWorkdays(seed, completedAt, 1);
  const rule = flowRule(seed, family, "turning", "drilling");
  if (rule) return rule.mode === "static" ? addDepartmentWorkMinutes(seed, completedAt, rule.minutes) : completedAt;
  return addWipWaitWorkdays(seed, completedAt, processWaitWorkdays(seed, "turning"));
}
function registerTurningCompletion(seed, history, recordedAt = history.archivedAt, applyCurrentFlow = true) {
  const existing = (seed.wipLots ?? []).find((lot) => lot.sourceHistoryEntryId === history.id && !lot.parentLotId);
  if (existing) return existing;
  const product = processMasterDataForProduct(seed.processMasterData, history.product);
  if (!product || history.process !== "turning" || history.completedQuantity <= 0 || history.inventoryStatus !== "semi-finished") return void 0;
  const createdAt = isoNow(recordedAt);
  const created = {
    ...history.sharedCharge ? { sharedCharge: { ...history.sharedCharge } } : {},
    id: lotId(seed, history.id),
    interruptionIds: history.interruptionIds ? [...history.interruptionIds] : void 0,
    sourceHistoryEntryId: history.id,
    sourceBatchId: history.sourceBatchId,
    workOrder: history.workOrder.trim(),
    product: history.product.trim().toUpperCase(),
    family: product.family,
    originalQuantity: history.completedQuantity,
    availableQuantity: history.completedQuantity,
    deliveredQuantity: 0,
    scrappedQuantity: 0,
    stage: turningReadyAt(seed, history.completedAt, product.family, applyCurrentFlow) > history.completedAt ? "quality-hold" : "drilling-queue",
    nextProcess: "drilling",
    readyAt: turningReadyAt(seed, history.completedAt, product.family, applyCurrentFlow),
    completedSteps: [{
      process: "turning",
      resourceId: history.machineId,
      resourceName: history.machineName,
      start: history.start,
      end: history.completedAt,
      plannedStart: history.start,
      plannedEnd: history.plannedEnd,
      quantity: history.completedQuantity,
      recordedAt: createdAt
    }],
    createdAt,
    updatedAt: createdAt
  };
  if (product.route) applyCustomRouteProgress(seed, created, "turning", history.completedAt);
  if (applyCurrentFlow) applyCompletedFlow(seed, created, "turning", history.completedAt);
  seed.wipLots = [...seed.wipLots ?? [], created];
  appendMovement(seed, {
    lotId: created.id,
    kind: "created",
    quantity: created.availableQuantity,
    toStage: created.stage,
    occurredAt: history.completedAt,
    recordedAt: createdAt,
    note: "Torna tamamlanmas\u0131ndan otomatik yar\u0131 mam\xFCl kayd\u0131"
  });
  return created;
}
function registerManualArchiveReceipt(seed, history, receipt) {
  const lot = registerTurningCompletion(seed, { ...history, process: "turning" }, receipt.recordedAt);
  if (!lot) throw new Error("Manuel adet i\xE7in \xFCr\xFCn rotas\u0131 bulunamad\u0131.");
  lot.completedSteps = [];
  lot.manualReceipt = structuredClone(receipt);
  if (history.process !== "turning") advanceStage(seed, lot, history.process, history.completedAt);
  const movement = seed.wipMovements.at(-1);
  movement.note = `Manuel adet kayd\u0131 \xB7 ${receipt.reason} \xB7 ${receipt.productionDate === void 0 ? "\xDCretim tarihi bilinmiyor; kay\u0131t an\u0131ndan itibaren kullan\u0131labilir" : "Bildirilen \xFCretim tarihi"}`;
  return lot;
}
function hydrateWipFromProductionHistory(seed) {
  seed.wipLots = seed.wipLots ?? [];
  seed.wipMovements = seed.wipMovements ?? [];
  for (const entry of seed.productionHistory ?? []) registerTurningCompletion(seed, entry, entry.statusChangedAt || entry.archivedAt, false);
}
function applyCustomRouteProgress(seed, lot, process2, completedAt) {
  const product = processMasterDataForProduct(seed.processMasterData, lot.product);
  const route = effectiveProductRoute(product, lot.completedSteps.find((s) => s.process === "turning")?.resourceId);
  const next = route[route.indexOf(process2) + 1];
  if (next && next !== "turning") {
    const parameter = product.processes.find((item) => item.process === next);
    if (!parameter) throw new Error(`${lot.product} i\xE7in ${processLabel(next)} parametreleri tamamlanmal\u0131; mevcut \xFCretim korunuyor.`);
    const wait = product.family === "cubuk-filtre" ? parameter.waitWorkdaysBefore : processWaitWorkdays(seed, process2);
    lot.nextProcess = next;
    lot.stage = product.family === "cubuk-filtre" ? parameter.leadStages?.length ? "process-buffer" : "process-queue" : next === "drilling" ? wait > 0 ? "quality-hold" : "drilling-queue" : next === "deburring" ? "deburring-queue" : wait > 0 ? "gkm-buffer" : "gkm-queue";
    lot.readyAt = applyProcessLeadStages(seed, addWipWaitWorkdays(seed, completedAt, wait), parameter.leadStages);
  } else {
    lot.stage = "delivery-ready";
    delete lot.nextProcess;
    lot.readyAt = routedDeliveryReadyAt(seed, completedAt, lot.family, process2);
  }
}
function applyCompletedFlow(seed, lot, process2, completedAt) {
  const rule = flowRule(seed, lot.family, process2, lot.nextProcess ?? "delivery");
  if (!rule) return;
  lot.readyAt = rule.mode === "static" ? addDepartmentWorkMinutes(seed, completedAt, rule.minutes) : completedAt;
  if (lot.nextProcess === "drilling") lot.stage = lot.readyAt > completedAt ? "quality-hold" : "drilling-queue";
  if (lot.nextProcess === "gkm") lot.stage = lot.readyAt > completedAt ? "washing-buffer" : "gkm-queue";
}
function advanceStage(seed, lot, process2, completedAt) {
  if (processMasterDataForProduct(seed.processMasterData, lot.product)?.route) {
    applyCustomRouteProgress(seed, lot, process2, completedAt);
  } else if (process2 === "drilling" && lot.family === "piston") {
    lot.stage = "deburring-queue";
    lot.nextProcess = "deburring";
    lot.readyAt = addWipWaitWorkdays(seed, completedAt, processWaitWorkdays(seed, process2));
  } else if (process2 === "drilling") {
    lot.stage = processWaitWorkdays(seed, process2) > 0 ? "washing-buffer" : "gkm-queue";
    lot.nextProcess = "gkm";
    lot.readyAt = addWipWaitWorkdays(seed, completedAt, processWaitWorkdays(seed, process2));
  } else if (process2 === "deburring") {
    lot.stage = processWaitWorkdays(seed, process2) > 0 ? "gkm-buffer" : "gkm-queue";
    lot.nextProcess = "gkm";
    lot.readyAt = addWipWaitWorkdays(seed, completedAt, processWaitWorkdays(seed, process2));
  } else {
    lot.stage = "delivery-ready";
    delete lot.nextProcess;
    lot.readyAt = routedDeliveryReadyAt(seed, completedAt, lot.family, process2);
  }
  applyCompletedFlow(seed, lot, process2, completedAt);
  delete lot.rolledForwardFrom;
  delete lot.rolledForwardAt;
}
function wipOperationReadyAt(lot) {
  return lot.rolledForwardFrom ?? lot.readyAt;
}
function wipCompletionEarliestAt(seed, lot) {
  const route = processMasterDataForProduct(seed.processMasterData, lot.product)?.route ?? (lot.family === "piston" ? ["turning", "drilling", "deburring", "gkm"] : ["turning", "drilling", "gkm"]);
  const index = lot.stage === "delivery-ready" ? route.length : route.indexOf(lot.nextProcess);
  const predecessors = route.slice(0, index);
  if (index <= 0 || lot.stage === "on-hold" || lot.stage === "unclassified" || terminalStages.has(lot.stage)) return wipOperationReadyAt(lot);
  const steps = predecessors.map((process2) => lot.completedSteps.find((step) => step.process === process2));
  if (steps.some((step) => !step || !Number.isFinite(step.end))) return wipOperationReadyAt(lot);
  const actualEnd = Math.max(...lot.completedSteps.map((step) => step.end));
  return Number.isFinite(actualEnd) ? actualEnd : wipOperationReadyAt(lot);
}
function completedDeliveryRouteEnd(seed, lot) {
  const route = processMasterDataForProduct(seed.processMasterData, lot.product)?.route;
  const product = processMasterDataForProduct(seed.processMasterData, lot.product);
  const required = route && product ? effectiveProductRoute(product, lot.completedSteps.find((s) => s.process === "turning")?.resourceId) : ["gkm"];
  if (!required.length) return void 0;
  const steps = required.map((process2) => lot.completedSteps.find((step) => step.process === process2) ?? (lot.manualReceipt?.completedProcesses.includes(process2) ? { end: lot.manualReceipt.productionDate ?? lot.manualReceipt.observedAt } : void 0));
  if (steps.some((step) => !step || !Number.isFinite(step.end))) return void 0;
  return Math.max(...steps.map((step) => step.end));
}
function releaseWipBuffer(seed, lotId2, occurredAt, confirmed, recordedAt = (/* @__PURE__ */ new Date()).toISOString()) {
  const lot = seed.wipLots?.find((item) => item.id === lotId2);
  if (!lot || lot.availableQuantity <= 0) throw new Error("A\xE7\u0131k yar\u0131 mam\xFCl bulunamad\u0131.");
  const product = processMasterDataForProduct(seed.processMasterData, lot.product);
  const filterBuffer = lot.stage === "process-buffer" && lot.family === "cubuk-filtre";
  const customRoute = filterBuffer && product?.route ? effectiveProductRoute(product, lot.completedSteps.find((step) => step.process === "turning")?.resourceId) : product?.route;
  const previousProcess = customRoute ? lot.stage === "delivery-ready" ? customRoute.at(-1) : customRoute[customRoute.indexOf(lot.nextProcess) - 1] : { "quality-hold": "turning", "washing-buffer": "drilling", "gkm-buffer": "deburring", "delivery-ready": "gkm" }[lot.stage];
  const previous = lot.completedSteps.find((step) => step.process === previousProcess);
  if (!previous || !Number.isFinite(previous.end) || !Number.isFinite(occurredAt) || occurredAt < previous.end) throw new Error("Bekleme yaln\u0131z \xF6nceki proses ger\xE7ekten tamamland\u0131ktan sonra kald\u0131r\u0131labilir.");
  if (!confirmed) throw new Error("Proses kontrol\xFCn\xFCn tamamland\u0131\u011F\u0131n\u0131 onaylay\u0131n.");
  if (occurredAt >= wipOperationReadyAt(lot)) throw new Error("Bu \u015Farj\u0131n bekleme s\xFCresi zaten tamamlanm\u0131\u015F.");
  const previousReadyAt = wipOperationReadyAt(lot);
  const fromStage = lot.stage;
  if (filterBuffer) lot.stage = "process-queue";
  lot.readyAt = occurredAt;
  delete lot.rolledForwardFrom;
  delete lot.rolledForwardAt;
  lot.updatedAt = recordedAt;
  appendMovement(seed, {
    lotId: lot.id,
    kind: "buffer-released",
    quantity: lot.availableQuantity,
    fromStage,
    toStage: lot.stage,
    occurredAt,
    recordedAt,
    note: filterBuffer ? "D\u0131\u015F proses beklemesi tamamland\u0131." : fromStage === "delivery-ready" ? "Proses kontrol ve paketleme tamamland\u0131 onay\u0131yla teslimat tamponu kald\u0131r\u0131ld\u0131." : "\u0130lgili kontrol / y\u0131kama tamamland\u0131 onay\u0131yla proses tamponu kald\u0131r\u0131ld\u0131.",
    previousReadyAt
  });
  return lot;
}
function assertResourceEligibility(seed, lot, input) {
  const product = processMasterDataForProduct(seed.processMasterData, lot.product);
  if (product?.route) {
    if (!product.route.includes(input.process)) throw new Error("Bu proses \xFCr\xFCn rotas\u0131nda Pasif.");
    for (const process2 of product.route.filter((item) => item !== "turning")) {
      const parameter2 = product.processes.find((item) => item.process === process2);
      if (!parameter2 || !Number.isFinite(parameter2.waitWorkdaysBefore) || parameter2.waitWorkdaysBefore < 0) throw new Error("Aktif proses parametreleri eksik; \xFCr\xFCn rotas\u0131n\u0131 kontrol edin.");
    }
  }
  const parameter = product?.processes.find((item) => item.process === input.process);
  if (!parameter) throw new Error(`${lot.product} i\xE7in ${input.process} prosesi tan\u0131ml\u0131 de\u011Fil.`);
  if (!parameter.resourcePriority.includes(input.resourceId)) throw new Error(`${input.resourceId}, ${lot.product} i\xE7in uygun bir i\u015F merkezi de\u011Fil.`);
}
function completeWipOperation(seed, input) {
  const source = (seed.wipLots ?? []).find((lot) => lot.id === input.lotId);
  if (!source) throw new Error("Yar\u0131 mam\xFCl \u015Farj\u0131 bulunamad\u0131.");
  if (activeLotInterruptions(seed, source).length && !input.confirmedInterruption) throw new Error("\xDCretim sonlanmad\u0131, yine de \xFCretime alay\u0131m m\u0131? Devam etmek i\xE7in onaylay\u0131n.");
  if (source.stage === "on-hold") throw new Error("Blokeli yar\u0131 mam\xFCl i\u015Fleme al\u0131namaz.");
  if (terminalStages.has(source.stage)) throw new Error("Kapanm\u0131\u015F yar\u0131 mam\xFCl i\u015Fleme al\u0131namaz.");
  if (source.nextProcess !== input.process) throw new Error(`S\u0131radaki operasyon ${source.nextProcess ?? "tan\u0131ml\u0131 de\u011Fil"}.`);
  assertProcessNotCompleted(source, input.process);
  if (!Number.isSafeInteger(input.quantity) || input.quantity <= 0) throw new Error("Tamamlanan adet pozitif tam say\u0131 olmal\u0131d\u0131r.");
  if (input.quantity > source.availableQuantity && seed.productionArea !== "cubuk-filtre") throw new Error("Tamamlanan adet, yar\u0131 mam\xFCl bakiyesini a\u015Fmayan pozitif tam say\u0131 olmal\u0131d\u0131r.");
  if (input.quantity > source.availableQuantity && !input.countCorrectionReason?.trim()) throw new Error("Adet bakiyeyi a\u015F\u0131yor. Say\u0131m d\xFCzeltmesi nedenini yaz\u0131n.");
  if (input.remainderAction && input.remainderAction !== "keep" && input.remainderAction !== "scrap") throw new Error("Kalan miktar i\u015Flemini se\xE7in.");
  if (!Number.isFinite(input.startedAt) || !Number.isFinite(input.completedAt) || input.completedAt < input.startedAt) throw new Error("Operasyon ba\u015Flang\u0131\xE7 ve biti\u015F tarihlerini kontrol edin.");
  const early = input.startedAt + 1e-8 < wipOperationReadyAt(source);
  if (early && !input.confirmedBuffer) throw new Error("Planlanan beklemeden erken tamamlama i\xE7in ilgili kontrol / y\u0131kaman\u0131n tamamland\u0131\u011F\u0131n\u0131 onaylay\u0131n.");
  if (input.startedAt + 1e-8 < wipCompletionEarliestAt(seed, source)) throw new Error("Operasyon \xF6nceki ger\xE7ek proses biti\u015Finden \xF6nce ba\u015Flayamaz; eksik proses kayd\u0131n\u0131 kontrol edin.");
  assertResourceEligibility(seed, source, input);
  if (processMasterDataForProduct(seed.processMasterData, source.product)?.route) applyCustomRouteProgress(seed, structuredClone(source), input.process, input.completedAt);
  if (input.quantity > source.availableQuantity) {
    const reason = input.countCorrectionReason.trim();
    if (reason.length > 500) throw new Error("Say\u0131m d\xFCzeltmesi nedeni en fazla 500 karakter olmal\u0131d\u0131r.");
    const draft = structuredClone(seed);
    const lot = draft.wipLots.find((item) => item.id === source.id);
    const history = draft.productionHistory?.find((item) => item.id === lot.sourceHistoryEntryId && item.inventoryStatus === "semi-finished");
    if (!history || history.product !== lot.product || history.workOrder.trim() !== lot.workOrder.trim()) throw new Error("Say\u0131m d\xFCzeltmesi i\xE7in a\xE7\u0131k \xFCretim ar\u015Fivi e\u015Fle\u015Fmesi gerekir.");
    const difference = input.quantity - lot.availableQuantity;
    if (![lot.originalQuantity + difference, history.completedQuantity + difference, history.originalQuantity + difference].every(Number.isSafeInteger)) throw new Error("Say\u0131m d\xFCzeltmesi adedi ge\xE7ersiz.");
    const recordedAt2 = isoNow(input.recordedAt);
    appendMovement(draft, {
      lotId: lot.id,
      kind: "quantity-corrected",
      quantity: difference,
      fromStage: lot.stage,
      toStage: lot.stage,
      occurredAt: input.completedAt,
      recordedAt: recordedAt2,
      note: `${processLabel(input.process)} say\u0131m d\xFCzeltmesi: ${lot.availableQuantity} \u2192 ${input.quantity} (+${difference}). ${reason}`
    });
    lot.originalQuantity += difference;
    lot.availableQuantity += difference;
    history.originalQuantity += difference;
    history.completedQuantity += difference;
    history.statusChangedAt = recordedAt2;
    const outcome = completeWipOperation(draft, { ...input, countCorrectionReason: void 0 });
    Object.assign(seed, draft);
    return outcome;
  }
  const scrapQuantity = source.availableQuantity - input.quantity;
  const scrapHistory = input.remainderAction === "scrap" && scrapQuantity > 0 ? seed.productionHistory?.find((entry) => entry.id === source.sourceHistoryEntryId && entry.inventoryStatus === "semi-finished") : void 0;
  if (input.remainderAction === "scrap" && scrapQuantity > 0 && (!scrapHistory || scrapHistory.completedQuantity < scrapQuantity || scrapHistory.originalQuantity < scrapQuantity)) {
    throw new Error("Iskarta i\xE7in yar\u0131 mam\xFCl ve \xFCretim ar\u015Fivi e\u015Fle\u015Fmiyor.");
  }
  const recordedAt = isoNow(input.recordedAt);
  const fromStage = source.stage;
  let completed = source;
  let remainder;
  if (input.quantity < source.availableQuantity) {
    source.originalQuantity -= input.quantity;
    source.availableQuantity -= input.quantity;
    source.updatedAt = recordedAt;
    completed = {
      ...JSON.parse(JSON.stringify(source)),
      id: lotId(seed, source.sourceHistoryEntryId),
      parentLotId: source.id,
      originalQuantity: input.quantity,
      availableQuantity: input.quantity,
      deliveredQuantity: 0,
      scrappedQuantity: 0,
      createdAt: recordedAt,
      updatedAt: recordedAt
    };
    seed.wipLots = [...seed.wipLots ?? [], completed];
    remainder = source;
    appendMovement(seed, {
      lotId: source.id,
      kind: "split",
      quantity: input.quantity,
      fromStage,
      toStage: source.stage,
      occurredAt: input.completedAt,
      recordedAt,
      note: `${completed.id} k\u0131smi operasyon i\xE7in ayr\u0131ld\u0131`
    });
  }
  if (remainder && input.remainderAction === "scrap") {
    const history = scrapHistory;
    const scrapId = `${history.id}-iskarta-${crypto.randomUUID()}`;
    const processName = processLabel(input.process);
    const scrapReason = `${processName} s\u0131ras\u0131nda ${scrapQuantity.toLocaleString("tr-TR")} adet \u0131skarta.`;
    if (history.completedQuantity === scrapQuantity) {
      history.inventoryStatus = "scrapped";
      history.scrappedAt = recordedAt;
      history.statusChangedAt = recordedAt;
      history.splitKind = "scrap";
      history.statusChangeReason = scrapReason;
      delete history.statusChangedBy;
    } else {
      history.completedQuantity -= scrapQuantity;
      history.originalQuantity -= scrapQuantity;
      seed.productionHistory = [...seed.productionHistory ?? [], {
        ...history,
        id: scrapId,
        sourceEntryId: history.id,
        originalQuantity: scrapQuantity,
        completedQuantity: scrapQuantity,
        inventoryStatus: "scrapped",
        statusChangedAt: recordedAt,
        scrappedAt: recordedAt,
        splitKind: "scrap",
        statusChangeReason: scrapReason,
        statusChangedBy: void 0
      }];
      remainder.sourceHistoryEntryId = scrapId;
    }
    scrapWipQuantity(seed, remainder.id, scrapQuantity, input.completedAt, recordedAt);
    finishProductionInterruptions(seed, source.id, input.process, input.completedAt);
  }
  if (!remainder) finishProductionInterruptions(seed, source.id, input.process, input.completedAt);
  if (early) {
    appendMovement(seed, {
      lotId: completed.id,
      kind: "buffer-released",
      quantity: input.quantity,
      fromStage,
      toStage: fromStage,
      occurredAt: input.startedAt,
      recordedAt,
      previousReadyAt: wipOperationReadyAt(completed),
      note: "Fiili tamamlama s\u0131ras\u0131nda ilgili kontrol / y\u0131kama tamamland\u0131 onay\u0131yla yaln\u0131z tamamlanan adedin planlanan beklemesi kald\u0131r\u0131ld\u0131."
    });
  }
  completed.completedSteps = [...completed.completedSteps, {
    process: input.process,
    resourceId: input.resourceId,
    resourceName: input.resourceName,
    start: input.startedAt,
    end: input.completedAt,
    plannedStart: input.plannedStart,
    plannedEnd: input.plannedEnd,
    quantity: input.quantity,
    recordedAt
  }];
  advanceStage(seed, completed, input.process, input.completedAt);
  completed.updatedAt = recordedAt;
  appendMovement(seed, {
    lotId: completed.id,
    kind: "process-completed",
    quantity: input.quantity,
    fromStage,
    toStage: completed.stage,
    process: input.process,
    resourceId: input.resourceId,
    occurredAt: input.completedAt,
    recordedAt
  });
  return { completed, remainder };
}
function hasCompletedProcess(lot, process2) {
  return lot.completedSteps.some((step) => step.process === process2) || Boolean(lot.manualReceipt?.completedProcesses.includes(process2));
}
function assertProcessNotCompleted(lot, process2) {
  if (hasCompletedProcess(lot, process2)) throw new Error(`${processLabel(process2)} bu par\xE7ada zaten tamamlanm\u0131\u015F. Konum de\u011Fi\u015Fikli\u011Fi veya tekrar tamamlama ile ge\xE7mi\u015F de\u011Fi\u015Ftirilemez.`);
}
function processAtStage(lot, stage) {
  return stage === "process-queue" || stage === "process-buffer" ? lot.nextProcess : nextProcessForWipStage(stage);
}
function correctableWipStages(seed, lot) {
  const common = ["unclassified", "delivery-ready", "on-hold"];
  const unfinished = (stage) => !lot || !processAtStage(lot, stage) || !hasCompletedProcess(lot, processAtStage(lot, stage));
  if (seed.productionArea === "cubuk-filtre") {
    return (lot?.nextProcess ? ["process-queue", "process-buffer", ...common] : common).filter(unfinished);
  }
  const positions = ["quality-hold", "drilling-queue", "deburring-queue", "washing-buffer", "gkm-buffer", "gkm-queue"];
  const product = lot && processMasterDataForProduct(seed.processMasterData, lot.product);
  const route = product?.route && effectiveProductRoute(product, lot?.completedSteps.find((step) => step.process === "turning")?.resourceId);
  return [...positions.filter((stage) => !route || route.includes(nextProcessForWipStage(stage))), ...common].filter(unfinished);
}
function correctWipStage(seed, lotIdValue, stage, occurredAt, note = "Manuel konum do\u011Frulamas\u0131", recordedAtValue) {
  const lot = (seed.wipLots ?? []).find((item) => item.id === lotIdValue);
  if (!lot) throw new Error("Yar\u0131 mam\xFCl \u015Farj\u0131 bulunamad\u0131.");
  if (terminalStages.has(lot.stage)) throw new Error("Teslim edilmi\u015F veya \u0131skartaya ayr\u0131lm\u0131\u015F \u015Farj\u0131n konumu de\u011Fi\u015Ftirilemez.");
  if (!Number.isFinite(occurredAt)) throw new Error("Konum tarihi ge\xE7ersiz.");
  if (lot.stage === "on-hold") throw new Error("Konumu de\u011Fi\u015Ftirmeden \xF6nce Blokeyi kald\u0131r kullan\u0131n.");
  const nextProcess = processAtStage(lot, stage);
  if (nextProcess) assertProcessNotCompleted(lot, nextProcess);
  if (!correctableWipStages(seed, lot).includes(stage)) throw new Error("Bu rota i\xE7in konum ge\xE7ersiz. Teslim ve \u0131skarta i\xE7in ilgili \xFCretim i\u015Flemini kullan\u0131n.");
  const completionEnds = lot.completedSteps.map((step) => step.end);
  if (lot.manualReceipt) completionEnds.push(lot.manualReceipt.productionDate ?? lot.manualReceipt.observedAt);
  if (completionEnds.some((end) => !Number.isFinite(end))) throw new Error("Kay\u0131tl\u0131 proses tarihlerini inceleyin.");
  const latestEnd = Math.max(0, ...completionEnds);
  if (Math.floor(occurredAt) < Math.floor(latestEnd)) throw new Error("Konum g\xFCn\xFC tamamlanm\u0131\u015F proseslerden \xF6nce olamaz. \xDCretim tarihlerini ayr\u0131 olarak d\xFCzeltin.");
  const recordedAt = isoNow(recordedAtValue);
  const fromStage = lot.stage;
  if (stage === "on-hold") {
    lot.heldFromStage = lot.stage;
    lot.heldNextProcess = lot.nextProcess;
    delete lot.nextProcess;
  } else {
    delete lot.heldFromStage;
    delete lot.heldNextProcess;
    lot.nextProcess = nextProcess;
  }
  lot.stage = stage;
  lot.readyAt = Math.max(occurredAt, latestEnd);
  lot.updatedAt = recordedAt;
  appendMovement(seed, { lotId: lot.id, kind: stage === "on-hold" ? "hold" : "stage-corrected", quantity: lot.availableQuantity, fromStage, toStage: stage, occurredAt, recordedAt, note });
  return lot;
}
function releaseWipHold(seed, lotIdValue, occurredAt, recordedAtValue) {
  const lot = (seed.wipLots ?? []).find((item) => item.id === lotIdValue);
  if (!lot || lot.stage !== "on-hold") throw new Error("Serbest b\u0131rak\u0131lacak blokeli yar\u0131 mam\xFCl bulunamad\u0131.");
  const recordedAt = isoNow(recordedAtValue);
  const nextStage = lot.heldFromStage && lot.heldFromStage !== "on-hold" ? lot.heldFromStage : "unclassified";
  lot.stage = nextStage;
  lot.nextProcess = lot.heldNextProcess ?? nextProcessForWipStage(nextStage);
  lot.readyAt = occurredAt;
  lot.updatedAt = recordedAt;
  delete lot.heldFromStage;
  delete lot.heldNextProcess;
  appendMovement(seed, { lotId: lot.id, kind: "release", quantity: lot.availableQuantity, fromStage: "on-hold", toStage: nextStage, occurredAt, recordedAt });
  return lot;
}
var relatedLots = productionHistoryLots;
function consumeLots(seed, lots, quantityValue, kind, occurredAt, recordedAt) {
  let quantity = quantityValue;
  const eligible = kind === "delivered" ? lots.filter((lot) => lot.stage === "delivery-ready" && Math.floor(lot.readyAt) <= Math.floor(occurredAt)) : lots.filter((lot) => lot.availableQuantity > 0 && !terminalStages.has(lot.stage));
  const available = eligible.reduce((sum, lot) => sum + lot.availableQuantity, 0);
  if (quantity > available) {
    throw new Error(kind === "delivered" ? `Teslimata haz\u0131r yar\u0131 mam\xFCl yaln\u0131zca ${available.toLocaleString("tr-TR")} adet.` : `Iskartaya ayr\u0131labilir yar\u0131 mam\xFCl yaln\u0131zca ${available.toLocaleString("tr-TR")} adet.`);
  }
  for (const lot of eligible.sort((left, right) => left.readyAt - right.readyAt || left.createdAt.localeCompare(right.createdAt))) {
    if (quantity <= 0) break;
    const consumed = Math.min(quantity, lot.availableQuantity);
    const fromStage = lot.stage;
    lot.availableQuantity -= consumed;
    if (kind === "delivered") lot.deliveredQuantity += consumed;
    else lot.scrappedQuantity += consumed;
    if (lot.availableQuantity === 0) {
      if (kind === "scrapped") {
        lot.scrappedFromStage = fromStage;
        lot.scrappedNextProcess = lot.nextProcess;
      }
      lot.stage = kind;
      delete lot.nextProcess;
    }
    lot.updatedAt = recordedAt;
    appendMovement(seed, { lotId: lot.id, kind, quantity: consumed, fromStage, toStage: lot.stage, occurredAt, recordedAt });
    quantity -= consumed;
  }
}
function deliverWipQuantity(seed, lotId2, quantity, occurredAt, recordedAt, precision = "minute") {
  const lot = seed.wipLots?.find((item) => item.id === lotId2);
  const completedAt = lot ? completedDeliveryRouteEnd(seed, lot) : void 0;
  if (!lot || lot.stage !== "delivery-ready" || completedAt === void 0 || precision !== "day" && !lot.completedSteps.some((step) => step.endPrecision === "day") && completedAt > occurredAt) throw new Error("Aktif \xFCretim rotas\u0131 (GKM aktifse GKM dahil) tamamlanmadan teslimat yap\u0131lamaz.");
  if (!Number.isInteger(quantity) || quantity <= 0 || !Number.isFinite(occurredAt) || occurredAt < wipOperationReadyAt(lot)) throw new Error("Teslim adedini ve haz\u0131r olma zaman\u0131n\u0131 kontrol edin.");
  if (precision === "day" || lot.completedSteps.some((step) => step.startPrecision === "day" || step.endPrecision === "day")) {
    assertRecordedDateOrder([...lot.completedSteps.flatMap((step) => [{ value: step.start, precision: step.startPrecision }, { value: step.end, precision: step.endPrecision }]), { value: occurredAt, precision }], lot.processOrderConfirmed === true, factoryNowSerial(recordedAt));
  }
  consumeLots(seed, [lot], quantity, "delivered", occurredAt, recordedAt);
  if (precision === "day") seed.wipMovements.at(-1).occurredAtPrecision = "day";
}
function scrapWipQuantity(seed, lotId2, quantity, occurredAt, recordedAt) {
  const lot = seed.wipLots?.find((item) => item.id === lotId2);
  if (!lot || !Number.isInteger(quantity) || quantity <= 0 || !Number.isFinite(occurredAt)) throw new Error("Iskarta miktar\u0131n\u0131 ve \u015Farj\u0131 kontrol edin.");
  consumeLots(seed, [lot], quantity, "scrapped", occurredAt, recordedAt);
}
function applyHistoryAllocationToWip(seed, entry, input, recordedAtValue, deliveryEntryId) {
  const lots = relatedLots(seed, entry);
  if (!lots.length) {
    if (input.deliveredQuantity > 0) throw new Error("Teslimat i\xE7in do\u011Frulanm\u0131\u015F bir WIP rota kayd\u0131 bulunamad\u0131.");
    return;
  }
  const recordedAt = isoNow(recordedAtValue);
  const timed = input.deliveryDate.includes("T");
  const deliveryIso = timed ? factoryDateTimeToIso(input.deliveryDate) : "";
  if (input.deliveredQuantity > 0 && timed && (!deliveryIso || factoryDateTimeInput(deliveryIso) !== input.deliveryDate)) throw new Error("Ge\xE7erli bir teslim tarihi ve saati se\xE7in.");
  const deliveryAt = timed ? factoryNowSerial(deliveryIso) : input.deliveryDate ? Date.parse(`${input.deliveryDate}T00:00:00Z`) / 864e5 + 25569 : input.completedAt;
  if (input.deliveredQuantity > 0 && timed && deliveryAt > factoryNowSerial(recordedAt)) throw new Error("Teslim tarihi ve saati \u015Fu andan sonra olamaz.");
  const deliveryLots = timed ? lots.filter((lot) => lot.availableQuantity > 0 && lot.stage === "delivery-ready" && (completedDeliveryRouteEnd(seed, lot) ?? Infinity) <= deliveryAt && lot.completedSteps.every((step) => Number.isFinite(step.end) && step.end <= deliveryAt) && (wipOperationReadyAt(lot) <= deliveryAt || input.confirmedDeliveryBuffer === true)) : lots;
  if (input.deliveredQuantity > 0 && timed && deliveryLots.reduce((sum, lot) => sum + lot.availableQuantity, 0) < input.deliveredQuantity) {
    throw new Error("Se\xE7ilen saatte yeterli miktar teslimata haz\u0131r de\u011Fil. Aktif prosesleri tamamlay\u0131n; erken teslimat i\xE7in proses kontrol ve paketlemenin tamamland\u0131\u011F\u0131n\u0131 onaylay\u0131n.");
  }
  const before = new Map(lots.map((lot) => [lot.id, lot.deliveredQuantity]));
  if (input.deliveredQuantity > 0 && timed) {
    let left = input.deliveredQuantity;
    for (const lot of deliveryLots.sort((a, b) => a.readyAt - b.readyAt || a.createdAt.localeCompare(b.createdAt))) {
      const amount = Math.min(left, lot.availableQuantity);
      if (!amount) continue;
      const early = deliveryAt < wipOperationReadyAt(lot);
      const readiness = { readyAt: lot.readyAt, rolledForwardFrom: lot.rolledForwardFrom, rolledForwardAt: lot.rolledForwardAt };
      if (early) releaseWipBuffer(seed, lot.id, deliveryAt, true, recordedAt);
      deliverWipQuantity(seed, lot.id, amount, deliveryAt, recordedAt);
      if (early) {
        const release = seed.wipMovements?.findLast((movement) => movement.lotId === lot.id && movement.kind === "buffer-released");
        if (release) release.quantity = amount;
        if (lot.availableQuantity > 0) Object.assign(lot, readiness);
      }
      left -= amount;
      if (!left) break;
    }
  } else if (input.deliveredQuantity > 0) consumeLots(seed, deliveryLots, input.deliveredQuantity, "delivered", deliveryAt, recordedAt);
  const shipped = seed.productionHistory?.find((item) => item.inventoryStatus === "delivered" && (!deliveryEntryId || item.id === deliveryEntryId) && (item.id === entry.id || item.sourceEntryId === entry.id) && !item.wipAllocations && item.completedQuantity === input.deliveredQuantity);
  if (shipped) shipped.wipAllocations = lots.map((lot) => ({ lotId: lot.id, quantity: lot.deliveredQuantity - (before.get(lot.id) ?? 0) })).filter((item) => item.quantity > 0);
  const remainder = input.actualQuantity - input.deliveredQuantity;
  if (remainder > 0 && input.remainderAction === "scrap") consumeLots(seed, lots, remainder, "scrapped", input.completedAt, recordedAt);
}
function applyHistoryStatusToWip(seed, entry, nextStatus, occurredAt, recordedAtValue, note = "", actor = "Planlama oturumu") {
  if (entry.inventoryStatus === "delivered" && !["delivered", "semi-finished"].includes(nextStatus)) throw new Error("\xD6nce teslimat\u0131 geri al\u0131n.");
  if (entry.inventoryStatus === "scrapped" && nextStatus === "delivered") throw new Error("\xD6nce \u0131skartay\u0131 yar\u0131 mamule geri al\u0131n.");
  const lots = relatedLots(seed, entry);
  if (!lots.length) {
    if (nextStatus === "delivered") throw new Error("Teslimat i\xE7in do\u011Frulanm\u0131\u015F bir WIP rota kayd\u0131 bulunamad\u0131.");
    return;
  }
  if (entry.inventoryStatus === nextStatus) return;
  if (entry.inventoryStatus === "scrapped" && nextStatus === "voided") return;
  const recordedAt = isoNow(recordedAtValue);
  if (nextStatus === "delivered") consumeLots(seed, lots, entry.completedQuantity, "delivered", occurredAt, recordedAt);
  else if (nextStatus === "scrapped" || nextStatus === "voided") consumeLots(seed, lots, entry.completedQuantity, "scrapped", occurredAt, recordedAt);
  else if (nextStatus === "semi-finished") {
    const fromScrap = entry.inventoryStatus === "scrapped";
    const balance = (lot) => fromScrap ? lot.scrappedQuantity : lot.deliveredQuantity;
    const restorable = lots.filter((lot) => balance(lot) > 0);
    if (restorable.reduce((sum, lot) => sum + balance(lot), 0) < entry.completedQuantity) {
      throw new Error(fromScrap ? "Iskarta kayd\u0131n\u0131n yar\u0131 mam\xFCl bakiyesi yetersiz. Ar\u015Fiv ve \u015Farj e\u015Fle\u015Fmesini kontrol edin." : "Teslimat kayd\u0131n\u0131n yar\u0131 mam\xFCl bakiyesi yetersiz. Ar\u015Fiv ve \u015Farj e\u015Fle\u015Fmesini kontrol edin.");
    }
    let remaining = entry.completedQuantity;
    for (const lot of restorable) {
      if (remaining <= 0) break;
      const restored = Math.min(remaining, balance(lot));
      if (fromScrap) lot.scrappedQuantity -= restored;
      else lot.deliveredQuantity -= restored;
      lot.availableQuantity += restored;
      lot.stage = fromScrap ? lot.scrappedFromStage ?? "delivery-ready" : "delivery-ready";
      lot.nextProcess = fromScrap ? lot.scrappedNextProcess ?? nextProcessForWipStage(lot.stage) : void 0;
      if (fromScrap && lot.scrappedQuantity === 0) {
        delete lot.scrappedFromStage;
        delete lot.scrappedNextProcess;
      }
      lot.readyAt = occurredAt;
      lot.updatedAt = recordedAt;
      appendMovement(seed, { lotId: lot.id, kind: "restored", quantity: restored, fromStage: fromScrap ? "scrapped" : "delivered", toStage: lot.stage, occurredAt, recordedAt, note: note.trim() || "Ar\u015Fivden yar\u0131 mamule geri al\u0131nd\u0131", actor });
      remaining -= restored;
    }
  }
}
function syncWipWithHistoryEdit(seed, entry, actualQuantity, completedAt, recordedAtValue, correctionLotId) {
  const lots = relatedLots(seed, entry);
  if (!lots.length) return;
  const open = lots.filter((lot2) => lot2.availableQuantity > 0 && !terminalStages.has(lot2.stage));
  const sameDate = Math.floor(completedAt) === Math.floor(entry.completedAt);
  const delta = actualQuantity - entry.completedQuantity;
  if (!delta && sameDate) return;
  if (entry.inventoryStatus !== "semi-finished") throw new Error("Teslim edilmi\u015F miktar\u0131 teslimat d\xFCzenleme penceresinden de\u011Fi\u015Ftirin.");
  if (open.length !== 1 && !correctionLotId) throw new Error("Bu kay\u0131t birden fazla a\xE7\u0131k \u015Farja b\xF6l\xFCnm\xFC\u015F. Adet fark\u0131n\u0131n uygulanaca\u011F\u0131 \u015Farj\u0131 se\xE7in.");
  const lot = correctionLotId ? open.find((item) => item.id === correctionLotId) : open[0];
  if (!lot) throw new Error("Se\xE7ilen \u015Farj art\u0131k a\xE7\u0131k de\u011Fil. G\xFCncel kayd\u0131 yeniden se\xE7in.");
  if (lot.availableQuantity + delta <= 0) throw new Error("Yeni adet teslim / \u0131skarta miktar\u0131ndan b\xFCy\xFCk olmal\u0131d\u0131r. Tamam\u0131n\u0131 kald\u0131rmak i\xE7in \u0131skarta i\u015Flemini kullan\u0131n.");
  if (!sameDate && (lots.length !== 1 || lot.completedSteps.length !== 1 || lot.deliveredQuantity || lot.scrappedQuantity)) throw new Error("Sonraki prosese ge\xE7mi\u015F \u015Farj\u0131n Torna tarihi de\u011Fi\u015Ftirilemez; adet ayr\u0131 olarak d\xFCzeltilebilir.");
  const changedAt = isoNow(recordedAtValue);
  lot.originalQuantity += delta;
  lot.availableQuantity += delta;
  if (lot.completedSteps.length === 1 && !lot.deliveredQuantity && !lot.scrappedQuantity) {
    lot.completedSteps[0] = { ...lot.completedSteps[0], end: sameDate ? entry.completedAt : completedAt, quantity: lot.originalQuantity };
    if (!sameDate) lot.readyAt = addWipWaitWorkdays(seed, completedAt, processWaitWorkdays(seed, "turning"));
  }
  lot.updatedAt = changedAt;
  appendMovement(seed, { lotId: lot.id, kind: "quantity-corrected", quantity: Math.abs(delta), fromStage: lot.stage, toStage: lot.stage, occurredAt: completedAt, recordedAt: changedAt, note: `Fiili adet ${entry.completedQuantity} \u2192 ${actualQuantity} olarak d\xFCzeltildi; ge\xE7mi\u015F proses kay\u0131tlar\u0131 korundu.` });
}

// lib/manual-archive-receipt.ts
function recordManualArchiveReceipt(seed, input, recordedAt = (/* @__PURE__ */ new Date()).toISOString()) {
  const observedAt = factoryNowSerial(recordedAt);
  const product = processMasterDataForProduct(seed.processMasterData, input.product);
  const route = product ? effectiveProductRoute(product) : [];
  const index = route.indexOf(input.process);
  if (!product || index < 0) throw Error("\xDCr\xFCn i\xE7in ge\xE7erli bir proses rotas\u0131 ve tamamlanan proses se\xE7in.");
  if (!Number.isSafeInteger(input.quantity) || input.quantity <= 0) throw Error("Adet pozitif bir tam say\u0131 olmal\u0131d\u0131r.");
  if (!input.reason?.trim() || input.reason.length > 1e3) throw Error("En fazla 1000 karakterle kay\u0131t a\xE7\u0131klamas\u0131 girin.");
  if (!/^[A-Za-z0-9_.:-]{1,128}$/.test(input.id) || seed.productionHistory?.some((row) => row.id === input.id)) throw Error("Manuel kay\u0131t kimli\u011Fi ge\xE7ersiz veya kay\u0131t zaten var.");
  if (input.productionDate !== void 0 && (!Number.isFinite(input.productionDate) || input.productionDate <= 0 || input.productionDate > observedAt)) throw Error("\xDCretim tarihi ge\xE7erli olmal\u0131 ve gelecekte olmamal\u0131d\u0131r.");
  const next = structuredClone(seed);
  const anchor = input.productionDate ?? observedAt;
  const manualReceipt = {
    observedAt,
    recordedAt,
    productionDate: input.productionDate,
    completedThrough: input.process,
    completedProcesses: route.slice(0, index + 1),
    reason: input.reason.trim()
  };
  const entry = {
    id: input.id,
    product: product.product,
    process: input.process,
    machineId: "MANUEL",
    machineName: "Manuel adet kayd\u0131",
    workOrder: input.id,
    originalQuantity: input.quantity,
    completedQuantity: input.quantity,
    start: anchor,
    plannedEnd: anchor,
    completedAt: anchor,
    archivedAt: recordedAt,
    statusChangedAt: recordedAt,
    inventoryStatus: "semi-finished",
    statusChangeReason: input.reason.trim(),
    manualReceipt
  };
  registerManualArchiveReceipt(next, entry, manualReceipt);
  next.productionHistory = [...next.productionHistory ?? [], entry];
  next.planNeedsRecalculation = true;
  delete next.lastAutomaticPlan;
  delete next.planRunSequence;
  return next;
}

// lib/planning-persistence.ts
var MAX_PLANNING_SAVE_BYTES = 6 * 1024 * 1024;

// lib/planning-delta.ts
function records(value) {
  if (!Array.isArray(value)) return null;
  const result = /* @__PURE__ */ new Map();
  for (const item of value) {
    if (!item || typeof item !== "object" || typeof item.id !== "string" || !item.id || result.has(item.id)) return null;
    result.set(item.id, item);
  }
  return result;
}
function applyPlanningDelta(base, delta) {
  const result = structuredClone(base);
  const object = (value) => Boolean(value && typeof value === "object" && !Array.isArray(value));
  const invalid = () => new Error("Kay\u0131t yan\u0131t\u0131ndaki fark ge\xE7ersiz. Yerel kopyay\u0131 koruyun.");
  if (!object(delta) || Object.keys(delta).sort().join() !== "arrays,remove,set" || !object(delta.set) || !Array.isArray(delta.remove) || !object(delta.arrays)) throw invalid();
  const names = [...Object.keys(delta.set), ...delta.remove, ...Object.keys(delta.arrays)];
  if (new Set(names).size !== names.length || names.some((key) => typeof key !== "string" || !/^[A-Za-z][A-Za-z0-9_]{0,99}$/.test(key) || ["constructor", "prototype"].includes(key))) throw invalid();
  for (const key of delta.remove) {
    if (!Object.hasOwn(result, key)) throw invalid();
    delete result[key];
  }
  for (const [key, value] of Object.entries(delta.set)) Object.defineProperty(result, key, { value, enumerable: true, writable: true, configurable: true });
  for (const [key, change] of Object.entries(delta.arrays)) {
    const rows = records(result[key]);
    if (!object(change) || Object.keys(change).some((key2) => !["upsert", "remove", "order"].includes(key2))) throw invalid();
    const upsert = records(change.upsert);
    if (!rows || !upsert || !Array.isArray(change.remove) || new Set(change.remove).size !== change.remove.length || change.remove.some((id) => typeof id !== "string" || !rows.has(id) || upsert.has(id))) throw invalid();
    for (const id of change.remove) rows.delete(id);
    for (const [id, row] of upsert) rows.set(id, structuredClone(row));
    const order = change.order ?? [...rows.keys()];
    if (!Array.isArray(order) || new Set(order).size !== rows.size || order.length !== rows.size || order.some((id) => !rows.has(id))) throw invalid();
    result[key] = order.map((id) => rows.get(id));
  }
  return result;
}

// lib/collaboration-runtime.ts
var import_node_fs = require("node:fs");
var import_node_crypto = require("node:crypto");

// lib/production-area.ts
function assertProductionArea(seed, area) {
  if ((seed.productionArea ?? "torna") !== area) throw new Error("Bu kay\u0131t ba\u015Fka bir \xFCretim alan\u0131na ait.");
}

// lib/number-format.ts
var integerFormatter = new Intl.NumberFormat("tr-TR", { maximumFractionDigits: 0 });
function formatInteger(value) {
  return integerFormatter.format(value);
}
function formatDecimal(value, maximumFractionDigits = 2) {
  return new Intl.NumberFormat("tr-TR", { maximumFractionDigits }).format(value);
}

// features/planning/shared/format.ts
function inputDateToSerial(value) {
  return value ? (Date.parse(`${value}T00:00:00Z`) - Date.UTC(1899, 11, 30)) / 864e5 : 0;
}

// features/planning/shared/production.ts
function clampShiftCount(value) {
  return Math.max(0, Math.min(3, Math.trunc(Number(value) || 0)));
}
function queuePosition(column) {
  return column >= 13 ? column - 12 : 0;
}

// data/product-weights.json
var product_weights_default = {
  sourceFile: "Delme ve C\u0327apak alma Parametre bilgileri (2).xlsx",
  sourceSheet: "\xDCR\xDCN A\u011EIRLIKLARI",
  sha256: "f62457050fd305059909aa34c0704ee7f9397f493c0a612e7d3861484c8800e9",
  unit: "Gram",
  rows: [
    {
      product: "R902200287",
      productName: "A2 CENTER PIN",
      materialCode: "Z170004",
      materialName: "[31CrMoV9V+SH+E] [\xD817,2mm] [3000mm] [DIN]",
      grams: 74.45,
      sourceRow: 619
    },
    {
      product: "R902375400",
      productName: "A2 CENTER PIN",
      materialCode: "Z170010",
      materialName: "[31CrMoV9] [\xD825,5mm] [3000mm] [DIN]",
      grams: 380.63,
      sourceRow: 640
    },
    {
      product: "R902719052",
      productName: "A2 CENTER PIN",
      materialCode: "Z170004",
      materialName: "[31CrMoV9V+SH+E] [\xD817,2mm] [3000mm] [DIN]",
      grams: 74.45,
      sourceRow: 580
    },
    {
      product: "R902719076",
      productName: "A2 CENTER PIN",
      materialCode: "Z170007",
      materialName: "[31CrMoV9+QT] [\xD814,2mm] [3000mm] [DIN]",
      grams: 43.15,
      sourceRow: 575
    },
    {
      product: "R902719738",
      productName: "A2 CENTER PIN",
      materialCode: "Z170008",
      materialName: "[31CrMoV9+QT] [\xD819,8mm] [3000mm] [DIN]",
      grams: 80.45,
      sourceRow: 584
    },
    {
      product: "R902719739",
      productName: "A2 CENTER PIN",
      materialCode: "Z170009",
      materialName: "[31CrMoV9+QT] [\xD820,7mm] [3000mm] [DIN]",
      grams: 228.91,
      sourceRow: 566
    },
    {
      product: "R902719740",
      productName: "A2 CENTER PIN",
      materialCode: "Z170010",
      materialName: "[31CrMoV9] [\xD825,5mm] [3000mm] [DIN]",
      grams: 402.33,
      sourceRow: 587
    },
    {
      product: "R902719741",
      productName: "A2 CENTER PIN",
      materialCode: "Z170011",
      materialName: "[31CrMoV9+QT] [\xD827mm] [3000mm] [DIN]",
      grams: 504.17,
      sourceRow: 588
    },
    {
      product: "R902719742",
      productName: "A2 CENTER PIN",
      materialCode: "Z170012",
      materialName: "[31CrMoV9+QT] [\xD830mm] [3000mm] [DIN]",
      grams: 697.93,
      sourceRow: 595
    },
    {
      product: "R902719743",
      productName: "A2 CENTER PIN",
      materialCode: "Z170007",
      materialName: "[31CrMoV9+QT] [\xD814,2mm] [3000mm] [DIN]",
      grams: 75.13,
      sourceRow: 576
    },
    {
      product: "R902719762",
      productName: "A2 CENTER PIN",
      materialCode: "Z170007",
      materialName: "[31CrMoV9+QT] [\xD814,2mm] [3000mm] [DIN]",
      grams: 71.42,
      sourceRow: 577
    },
    {
      product: "R902719763",
      productName: "A2 CENTER PIN",
      materialCode: "Z170004",
      materialName: "[31CrMoV9V+SH+E] [\xD817,2mm] [3000mm] [DIN]",
      grams: 70.35,
      sourceRow: 581
    },
    {
      product: "R902719764",
      productName: "A2 CENTER PIN",
      materialCode: "Z170008",
      materialName: "[31CrMoV9+QT] [\xD819,8mm] [3000mm] [DIN]",
      grams: 77.95,
      sourceRow: 585
    },
    {
      product: "R902719765",
      productName: "A2 CENTER PIN",
      materialCode: "Z170009",
      materialName: "[31CrMoV9+QT] [\xD820,7mm] [3000mm] [DIN]",
      grams: 228.91,
      sourceRow: 568
    },
    {
      product: "R902719766",
      productName: "A2 CENTER PIN",
      materialCode: "Z170010",
      materialName: "[31CrMoV9] [\xD825,5mm] [3000mm] [DIN]",
      grams: 378.84,
      sourceRow: 569
    },
    {
      product: "R902719767",
      productName: "A2 CENTER PIN",
      materialCode: "Z170011",
      materialName: "[31CrMoV9+QT] [\xD827mm] [3000mm] [DIN]",
      grams: 477.84,
      sourceRow: 571
    },
    {
      product: "R902719768",
      productName: "A2 CENTER PIN",
      materialCode: "Z170012",
      materialName: "[31CrMoV9+QT] [\xD830mm] [3000mm] [DIN]",
      grams: 662.66,
      sourceRow: 594
    },
    {
      product: "R902719812",
      productName: "P\u0130STON",
      materialCode: "Z170007",
      materialName: "[31CrMoV9+QT] [\xD814,2mm] [3000mm] [DIN]",
      grams: 37.09,
      sourceRow: 578
    },
    {
      product: "R902725682",
      productName: "A2 CENTER PIN",
      materialCode: "Z170007",
      materialName: "[31CrMoV9+QT] [\xD814,2mm] [3000mm] [DIN]",
      grams: 45.13,
      sourceRow: 579
    },
    {
      product: "R902729695",
      productName: "A2 CENTER PIN",
      materialCode: "Z170010",
      materialName: "[31CrMoV9] [\xD825,5mm] [3000mm] [DIN]",
      grams: 402.33,
      sourceRow: 567
    },
    {
      product: "R902729941",
      productName: "A2 CENTER PIN",
      materialCode: "Z170011",
      materialName: "[31CrMoV9+QT] [\xD827mm] [3000mm] [DIN]",
      grams: 504.17,
      sourceRow: 590
    },
    {
      product: "R902744004",
      productName: "A2 CENTER PIN",
      materialCode: "Z170012",
      materialName: "[31CrMoV9+QT] [\xD830mm] [3000mm] [DIN]",
      grams: 697.93,
      sourceRow: 593
    },
    {
      product: "R902745116",
      productName: "P\u0130STON",
      materialCode: "Z170008",
      materialName: "[31CrMoV9+QT] [\xD819,8mm] [3000mm] [DIN]",
      grams: 181,
      sourceRow: 363
    },
    {
      product: "R902745117",
      productName: "P\u0130STON",
      materialCode: "Z170010",
      materialName: "[31CrMoV9] [\xD825,5mm] [3000mm] [DIN]",
      grams: 340,
      sourceRow: 366
    },
    {
      product: "R902745119",
      productName: "P\u0130STON",
      materialCode: "Z170009",
      materialName: "[31CrMoV9+QT] [\xD820,7mm] [3000mm] [DIN]",
      grams: 222,
      sourceRow: 374
    },
    {
      product: "R902745121",
      productName: "P\u0130STON",
      materialCode: "Z170009",
      materialName: "[31CrMoV9+QT] [\xD820,7mm] [3000mm] [DIN]",
      grams: 204,
      sourceRow: 375
    },
    {
      product: "R902745123",
      productName: "P\u0130STON",
      materialCode: "Z170010",
      materialName: "[31CrMoV9] [\xD825,5mm] [3000mm] [DIN]",
      grams: 380,
      sourceRow: 376
    },
    {
      product: "R902745127",
      productName: "P\u0130STON",
      materialCode: "Z170007",
      materialName: "[31CrMoV9+QT] [\xD814,2mm] [3000mm] [DIN]",
      grams: 67,
      sourceRow: 377
    },
    {
      product: "R902745129",
      productName: "P\u0130STON",
      materialCode: "Z170007",
      materialName: "[31CrMoV9+QT] [\xD814,2mm] [3000mm] [DIN]",
      grams: 67,
      sourceRow: 379
    },
    {
      product: "R902745131",
      productName: "P\u0130STON",
      materialCode: "Z170007",
      materialName: "[31CrMoV9+QT] [\xD814,2mm] [3000mm] [DIN]",
      grams: 67,
      sourceRow: 378
    },
    {
      product: "R902745133",
      productName: "P\u0130STON",
      materialCode: "Z170004",
      materialName: "[31CrMoV9V+SH+E] [\xD817,2mm] [3000mm] [DIN]",
      grams: 121,
      sourceRow: 380
    },
    {
      product: "R902745135",
      productName: "P\u0130STON",
      materialCode: "Z170004",
      materialName: "[31CrMoV9V+SH+E] [\xD817,2mm] [3000mm] [DIN]",
      grams: 121,
      sourceRow: 381
    },
    {
      product: "R902745138",
      productName: "P\u0130STON",
      materialCode: "Z170004",
      materialName: "[31CrMoV9V+SH+E] [\xD817,2mm] [3000mm] [DIN]",
      grams: 121,
      sourceRow: 382
    },
    {
      product: "R902745143",
      productName: "P\u0130STON",
      materialCode: "Z170011",
      materialName: "[31CrMoV9+QT] [\xD827mm] [3000mm] [DIN]",
      grams: 461.76,
      sourceRow: 383
    },
    {
      product: "R902745145",
      productName: "P\u0130STON",
      materialCode: "Z170011",
      materialName: "[31CrMoV9+QT] [\xD827mm] [3000mm] [DIN]",
      grams: 461.76,
      sourceRow: 384
    },
    {
      product: "R902745147",
      productName: "P\u0130STON",
      materialCode: "Z170012",
      materialName: "[31CrMoV9+QT] [\xD830mm] [3000mm] [DIN]",
      grams: 651,
      sourceRow: 385
    },
    {
      product: "R902745149",
      productName: "P\u0130STON",
      materialCode: "Z170012",
      materialName: "[31CrMoV9+QT] [\xD830mm] [3000mm] [DIN]",
      grams: 651,
      sourceRow: 386
    },
    {
      product: "R902745161",
      productName: "P\u0130STON( CLUSTER 2)",
      materialCode: "Z170016",
      materialName: "[31CrMoV9+QT] [\xD823mm] [3000mm] [DIN]",
      grams: 266,
      sourceRow: 389
    },
    {
      product: "R902745163",
      productName: "P\u0130STON( CLUSTER 1)",
      materialCode: "Z170010",
      materialName: "[31CrMoV9] [\xD825,5mm] [3000mm] [DIN]",
      grams: 360,
      sourceRow: 390
    },
    {
      product: "R902745165",
      productName: "P\u0130STON( CLUSTER 1)",
      materialCode: "Z170010",
      materialName: "[31CrMoV9] [\xD825,5mm] [3000mm] [DIN]",
      grams: 360,
      sourceRow: 391
    },
    {
      product: "R902745167",
      productName: "P\u0130STON( CLUSTER 1)",
      materialCode: "Z170010",
      materialName: "[31CrMoV9] [\xD825,5mm] [3000mm] [DIN]",
      grams: 360,
      sourceRow: 392
    },
    {
      product: "R902745169",
      productName: "P\u0130STON( CLUSTER 2)",
      materialCode: "Z170016",
      materialName: "[31CrMoV9+QT] [\xD823mm] [3000mm] [DIN]",
      grams: 260,
      sourceRow: 393
    },
    {
      product: "R902747620",
      productName: "P\u0130STON( CLUSTER 2)",
      materialCode: "Z170016",
      materialName: "[31CrMoV9+QT] [\xD823mm] [3000mm] [DIN]",
      grams: 266,
      sourceRow: 387
    },
    {
      product: "R902747621",
      productName: "P\u0130STON( CLUSTER 2)",
      materialCode: "Z170016",
      materialName: "[31CrMoV9+QT] [\xD823mm] [3000mm] [DIN]",
      grams: 266,
      sourceRow: 388
    },
    {
      product: "R902747824",
      productName: "A2 CENTER PIN",
      materialCode: "Z170011",
      materialName: "[31CrMoV9+QT] [\xD827mm] [3000mm] [DIN]",
      grams: 469,
      sourceRow: 565
    },
    {
      product: "R902748350",
      productName: "A2 CENTER PIN",
      materialCode: "Z170010",
      materialName: "[31CrMoV9] [\xD825,5mm] [3000mm] [DIN]",
      grams: 380.63,
      sourceRow: 589
    },
    {
      product: "R902970039",
      productName: "A2 CENTER PIN",
      materialCode: "Z170011",
      materialName: "[31CrMoV9+QT] [\xD827mm] [3000mm] [DIN]",
      grams: 468.02,
      sourceRow: 570
    },
    {
      product: "R902970233",
      productName: "P\u0130STON( CLUSTER 1)",
      materialCode: "Z170010",
      materialName: "[31CrMoV9] [\xD825,5mm] [3000mm] [DIN]",
      grams: 360,
      sourceRow: 520
    },
    {
      product: "R902970275",
      productName: "P\u0130STON( CLUSTER 4)",
      materialCode: "Z170011",
      materialName: "[31CrMoV9+QT] [\xD827mm] [3000mm] [DIN]",
      grams: 461.76,
      sourceRow: 397
    },
    {
      product: "R902970276",
      productName: "P\u0130STON( CLUSTER 4)",
      materialCode: "Z170011",
      materialName: "[31CrMoV9+QT] [\xD827mm] [3000mm] [DIN]",
      grams: 461.76,
      sourceRow: 398
    },
    {
      product: "R902970277",
      productName: "A2 CENTER PIN",
      materialCode: "Z170012",
      materialName: "[31CrMoV9+QT] [\xD830mm] [3000mm] [DIN]",
      grams: 626.57,
      sourceRow: 591
    },
    {
      product: "R902970513",
      productName: "P\u0130STON( CLUSTER 3)",
      materialCode: "Z170004",
      materialName: "[31CrMoV9V+SH+E] [\xD817,2mm] [3000mm] [DIN]",
      grams: 121,
      sourceRow: 487
    },
    {
      product: "R902970514",
      productName: "P\u0130STON( CLUSTER 3)",
      materialCode: "Z170004",
      materialName: "[31CrMoV9V+SH+E] [\xD817,2mm] [3000mm] [DIN]",
      grams: 121,
      sourceRow: 394
    },
    {
      product: "R902970515",
      productName: "P\u0130STON( CLUSTER 3)",
      materialCode: "Z170004",
      materialName: "[31CrMoV9V+SH+E] [\xD817,2mm] [3000mm] [DIN]",
      grams: 121,
      sourceRow: 395
    },
    {
      product: "R902970516",
      productName: "P\u0130STON( CLUSTER 3)",
      materialCode: "Z170008",
      materialName: "[31CrMoV9+QT] [\xD819,8mm] [3000mm] [DIN]",
      grams: 160,
      sourceRow: 396
    },
    {
      product: "R902970517",
      productName: "P\u0130STON( CLUSTER 3)",
      materialCode: "Z170008",
      materialName: "[31CrMoV9+QT] [\xD819,8mm] [3000mm] [DIN]",
      grams: 158.91,
      sourceRow: 460
    },
    {
      product: "R902970729",
      productName: "A2 CENTER PIN",
      materialCode: "Z170009",
      materialName: "[31CrMoV9+QT] [\xD820,7mm] [3000mm] [DIN]",
      grams: 201.63,
      sourceRow: 586
    },
    {
      product: "R902970862",
      productName: "P\u0130STON ( CLUSTER 6)",
      materialCode: "Z170012",
      materialName: "[31CrMoV9+QT] [\xD830mm] [3000mm] [DIN]",
      grams: 595,
      sourceRow: 547
    },
    {
      product: "R902970863",
      productName: "P\u0130STON ( CLUSTER 6)",
      materialCode: "Z170012",
      materialName: "[31CrMoV9+QT] [\xD830mm] [3000mm] [DIN]",
      grams: 595,
      sourceRow: 548
    },
    {
      product: "R902970964",
      productName: "A2 CENTER PIN",
      materialCode: "Z170018",
      materialName: "\xD8  33,5    31 CRMOV 9V + SH + E",
      grams: 885.4,
      sourceRow: 592
    },
    {
      product: "R902972555",
      productName: "P\u0130STON",
      materialCode: "Z170004",
      materialName: "[31CrMoV9V+SH+E] [\xD817,2mm] [3000mm] [DIN]",
      grams: 65.28,
      sourceRow: 572
    },
    {
      product: "R902972556",
      productName: "P\u0130STON",
      materialCode: "Z170004",
      materialName: "[31CrMoV9V+SH+E] [\xD817,2mm] [3000mm] [DIN]",
      grams: 65.28,
      sourceRow: 573
    },
    {
      product: "R902972557",
      productName: "P\u0130STON",
      materialCode: "Z170004",
      materialName: "[31CrMoV9V+SH+E] [\xD817,2mm] [3000mm] [DIN]",
      grams: 65.28,
      sourceRow: 622
    },
    {
      product: "R902974041",
      productName: "P\u0130STON",
      materialCode: "Z170004",
      materialName: "[31CrMoV9V+SH+E] [\xD817,2mm] [3000mm] [DIN]",
      grams: 111.33,
      sourceRow: 582
    },
    {
      product: "R902974042",
      productName: "A2 CENTER PIN",
      materialCode: "Z170004",
      materialName: "[31CrMoV9V+SH+E] [\xD817,2mm] [3000mm] [DIN]",
      grams: 126.89,
      sourceRow: 583
    }
  ]
};

// lib/product-weights.ts
function initialProductWeights() {
  return structuredClone(product_weights_default.rows);
}

// lib/raw-material-settings.ts
function initialRawMaterialSettings() {
  return { scrapPercent: 2, stockDate: "", stocks: [] };
}

// lib/order-entry.ts
var TIPLER_ORDER_TEMPLATE = [
  { product: "R902745116", quantity: 3840 },
  { product: "R902745117", quantity: 0 },
  { product: "R902745119", quantity: 0 },
  { product: "R902745121", quantity: 5940 },
  { product: "R902745123", quantity: 3960 },
  { product: "R902745127", quantity: 7200 },
  { product: "R902745129", quantity: 0 },
  { product: "R902745131", quantity: 11520 },
  { product: "R902745133", quantity: 0 },
  { product: "R902745135", quantity: 1920 },
  { product: "R902745138", quantity: 1920 },
  { product: "R902747621", quantity: 0 },
  { product: "R902745143", quantity: 7680 },
  { product: "R902745145", quantity: 1920 },
  { product: "R902745147", quantity: 6400 },
  { product: "R902745149", quantity: 0 },
  { product: "R902970275", quantity: 9600 },
  { product: "R902970276", quantity: 5760 },
  { product: "R902745165", quantity: 0 },
  { product: "R902745163", quantity: 1980 },
  { product: "R902745167", quantity: 0 },
  { product: "R902970233", quantity: 0 },
  { product: "R902745169", quantity: 0 },
  { product: "R902747620", quantity: 7920 },
  { product: "R902745161", quantity: 5940 },
  { product: "R902970513", quantity: 1920 },
  { product: "R902970514", quantity: 1920 },
  { product: "R902970515", quantity: 0 },
  { product: "R902970516", quantity: 0 },
  { product: "R902970517", quantity: 0 },
  { product: "R902970862", quantity: 0 },
  { product: "R902970863", quantity: 0 },
  { product: "R902974041", quantity: 0 },
  { product: "R902972555", quantity: 0 },
  { product: "R902972556", quantity: 0 },
  { product: "R902719812", quantity: 4e3 },
  { product: "R902972557", quantity: 0 },
  { product: "R902719052", quantity: 0 },
  { product: "R902719076", quantity: 0 },
  { product: "R902719738", quantity: 0 },
  { product: "R902719739", quantity: 0 },
  { product: "R902719740", quantity: 1920 },
  { product: "R902719741", quantity: 1920 },
  { product: "R902719742", quantity: 0 },
  { product: "R902719743", quantity: 960 },
  { product: "R902719762", quantity: 0 },
  { product: "R902719763", quantity: 0 },
  { product: "R902719764", quantity: 0 },
  { product: "R902719765", quantity: 0 },
  { product: "R902719766", quantity: 0 },
  { product: "R902719767", quantity: 0 },
  { product: "R902719768", quantity: 0 },
  { product: "R902725682", quantity: 960 },
  { product: "R902729695", quantity: 0 },
  { product: "R902729941", quantity: 0 },
  { product: "R902744004", quantity: 0 },
  { product: "R902747824", quantity: 3840 },
  { product: "R902748350", quantity: 1920 },
  { product: "R902970039", quantity: 0 },
  { product: "R902970277", quantity: 0 },
  { product: "R902970729", quantity: 2e3 },
  { product: "R902970964", quantity: 0 },
  { product: "R902974042", quantity: 0 },
  { product: "R902200287", quantity: 0 },
  { product: "R902375400", quantity: 450 }
];
function sortOrdersByCatalog(orders, catalog2 = TIPLER_ORDER_TEMPLATE.map((row) => row.product)) {
  const catalogIndex = new Map(catalog2.map((product, index) => [product.toUpperCase(), index]));
  return [...orders].sort((left, right) => {
    const leftIndex = catalogIndex.get(left.product.toUpperCase()) ?? Number.MAX_SAFE_INTEGER;
    const rightIndex = catalogIndex.get(right.product.toUpperCase()) ?? Number.MAX_SAFE_INTEGER;
    return leftIndex - rightIndex || left.sourceRow - right.sourceRow || left.product.localeCompare(right.product);
  });
}

// lib/customer-order-overrides.ts
function normalizedProduct(value) {
  return value.trim().toUpperCase();
}
function overrideOrder(override, existing, sourceRow) {
  return {
    id: existing?.id ?? `customer-override-${override.product}`,
    sourceRow,
    product: override.product,
    periodId: override.dueDate ? override.dueDate.slice(0, 7) : existing?.periodId,
    quantity: override.quantity,
    savedPlanned: existing?.savedPlanned ?? 0,
    savedDifference: existing?.savedDifference ?? 0,
    savedMachines: existing?.savedMachines ?? [],
    dueDate: override.dueDate,
    allowPartial: false,
    partialDeliveryQuantity: 0,
    partialDeliveryDate: "",
    deliveryMilestones: []
  };
}
function applyCustomerOrderOverrides(baseOrders, overrides = [], catalog2, existingOrders = []) {
  const normalizedCatalog = [...new Set([
    ...catalog2.map(normalizedProduct),
    ...overrides.map((item) => normalizedProduct(item.product))
  ].filter(Boolean))];
  const overrideByProduct = new Map(overrides.map((item) => [normalizedProduct(item.product), item]));
  const existingByProduct = new Map(existingOrders.map((order) => [normalizedProduct(order.product), order]));
  const baseByProduct = new Map(baseOrders.map((order) => [normalizedProduct(order.product), order]));
  const next = [];
  for (const product of normalizedCatalog) {
    const override = overrideByProduct.get(product);
    const base = baseByProduct.get(product);
    if (!override) {
      if (base) next.push(base);
      continue;
    }
    if (override.quantity <= 0) continue;
    const sourceRow = normalizedCatalog.indexOf(product) + 2;
    next.push(overrideOrder(override, base ?? existingByProduct.get(product), sourceRow));
  }
  return sortOrdersByCatalog(next, normalizedCatalog);
}

// lib/weekly-demand.ts
var NET_SHORTAGE_CALCULATION_MODEL = "net-shortage-v1";
function planningWeekLabel(week) {
  return `W${String(week.isoWeek).padStart(2, "0")}.${week.isoYear}`;
}
function resolvePlanningWeekRanges(weeks, ranges) {
  if (!ranges.length) throw new Error("En az bir planlama hafta aral\u0131\u011F\u0131 ekleyin.");
  let previousEndIndex = -1;
  return ranges.map((range, index) => {
    const startIndex = weeks.findIndex((week) => week.id === range.startWeekId);
    const endIndex = weeks.findIndex((week) => week.id === range.endWeekId);
    if (startIndex < 0 || endIndex < 0) throw new Error(`${index + 1}. aral\u0131ktaki ba\u015Flang\u0131\xE7 ve biti\u015F haftas\u0131n\u0131 se\xE7in.`);
    if (startIndex > endIndex) throw new Error(`${index + 1}. aral\u0131\u011F\u0131n ba\u015Flang\u0131\xE7 haftas\u0131 biti\u015F haftas\u0131ndan sonra olamaz.`);
    if (index > 0 && startIndex <= previousEndIndex) throw new Error(`${index + 1}. aral\u0131k \xF6nceki aral\u0131kla \xE7ak\u0131\u015F\u0131yor veya geriye gidiyor.`);
    if (index > 0 && startIndex !== previousEndIndex + 1) throw new Error(`${index + 1}. aral\u0131k \xF6nceki aral\u0131\u011F\u0131n hemen arkas\u0131ndan ba\u015Flamal\u0131d\u0131r.`);
    previousEndIndex = endIndex;
    const firstWeek = weeks[startIndex];
    const lastWeek = weeks[endIndex];
    return {
      ...range,
      startIndex,
      endIndex,
      label: `${planningWeekLabel(firstWeek)}\u2013${planningWeekLabel(lastWeek)}`,
      startDate: firstWeek.weekStart,
      endDate: lastWeek.weekEnd
    };
  });
}
function validMonthId(value) {
  return /^\d{4}-(0[1-9]|1[0-2])$/.test(value);
}
function weekScopeForPlanningMonthRange(weeks, range) {
  if (!validMonthId(range.startMonth) || !validMonthId(range.endMonth)) {
    throw new Error("Planlama ba\u015Flang\u0131\xE7 ve biti\u015F ay\u0131 zorunludur.");
  }
  if (range.startMonth > range.endMonth) {
    throw new Error("Planlama ba\u015Flang\u0131\xE7 ay\u0131 biti\u015F ay\u0131ndan sonra olamaz.");
  }
  const selected = weeks.filter((week) => {
    const deliveryMonth = week.weekEnd.slice(0, 7);
    return deliveryMonth >= range.startMonth && deliveryMonth <= range.endMonth;
  });
  if (!selected.length) {
    throw new Error("Se\xE7ilen ay aral\u0131\u011F\u0131nda Cumartesi termini bulunan m\xFC\u015Fteri haftas\u0131 yok.");
  }
  return {
    startWeekId: selected[0].id,
    endWeekId: selected.at(-1).id
  };
}
function isoDateToUtc(value) {
  const date = /* @__PURE__ */ new Date(`${value}T00:00:00Z`);
  if (!/^\d{4}-\d{2}-\d{2}$/.test(value) || !Number.isFinite(date.getTime())) {
    throw new Error(`Ge\xE7ersiz ISO tarih: ${value}`);
  }
  return date;
}
function addUtcDays(value, days) {
  const date = isoDateToUtc(value);
  date.setUTCDate(date.getUTCDate() + days);
  return date.toISOString().slice(0, 10);
}
function normalizeCustomerDemandDataset(dataset) {
  const weeks = dataset.weeks.map((week) => ({
    ...week,
    weekEnd: addUtcDays(week.weekStart, 5)
  }));
  const baselineDueDate = weeks[0] ? addUtcDays(weeks[0].weekStart, -2) : dataset.baselineDueDate;
  const normalizedWeeks = new Map(weeks.map((week) => [week.id, week]));
  const products = dataset.products.map((product) => {
    let cumulativeQuantity = Math.max(0, -Number(product.baselineBalance || 0));
    const priorDemand = cumulativeQuantity;
    const weeklyDemands = product.weeklyDemands.map((week) => {
      const normalizedWeek = normalizedWeeks.get(week.weekId);
      const requiredQuantity = Math.max(0, -Number(week.balance || 0));
      const nextCumulativeQuantity = Math.max(cumulativeQuantity, requiredQuantity);
      const quantity = nextCumulativeQuantity - cumulativeQuantity;
      cumulativeQuantity = nextCumulativeQuantity;
      return {
        ...week,
        weekStart: normalizedWeek?.weekStart ?? week.weekStart,
        weekEnd: normalizedWeek?.weekEnd ?? addUtcDays(week.weekStart, 5),
        quantity,
        cumulativeQuantity,
        requiredQuantity
      };
    });
    return {
      ...product,
      baselineDueDate,
      priorDemand,
      weeklyDemands,
      totalDemand: cumulativeQuantity
    };
  });
  const weeksWithQuantity = weeks.map((week) => ({
    ...week,
    quantity: products.reduce(
      (sum, product) => sum + (product.weeklyDemands.find((point) => point.weekId === week.id)?.quantity ?? 0),
      0
    )
  }));
  return {
    ...dataset,
    calculationModel: NET_SHORTAGE_CALCULATION_MODEL,
    baselineDueDate,
    weeks: weeksWithQuantity,
    products
  };
}
function normalizedScope(preview, scope) {
  if (!preview.weeks.length) throw new Error("Excel dosyas\u0131nda planlanabilir ISO hafta bulunamad\u0131.");
  const next = scope ?? { startWeekId: preview.weeks[0].id, endWeekId: preview.weeks.at(-1).id };
  const startIndex = preview.weeks.findIndex((week) => week.id === next.startWeekId);
  const endIndex = preview.weeks.findIndex((week) => week.id === next.endWeekId);
  if (startIndex < 0 || endIndex < 0) throw new Error("Se\xE7ilen ISO hafta kapsam\u0131 m\xFC\u015Fteri dosyas\u0131nda bulunamad\u0131.");
  if (startIndex > endIndex) throw new Error("Planlama ba\u015Flang\u0131\xE7 haftas\u0131 biti\u015F haftas\u0131ndan sonra olamaz.");
  return next;
}
function orderForProduct(product, productIndex, startIndex, endIndex, previous, includePriorBacklog = true) {
  const cumulativeDemandBeforeScope = startIndex === 0 ? product.priorDemand : product.weeklyDemands[startIndex - 1]?.cumulativeQuantity ?? product.priorDemand;
  const selectedWeeks = product.weeklyDemands.slice(startIndex, endIndex + 1);
  const deliveryPoints = [];
  let cumulative = 0;
  if (includePriorBacklog && cumulativeDemandBeforeScope > 0) {
    cumulative += cumulativeDemandBeforeScope;
    deliveryPoints.push({
      id: `${product.product}-scope-backlog`,
      quantity: cumulative,
      date: addUtcDays(selectedWeeks[0].weekStart, -2)
    });
  }
  for (const week of selectedWeeks) {
    if (week.quantity <= 0) continue;
    cumulative += week.quantity;
    deliveryPoints.push({
      id: `${product.product}-${week.weekId}`,
      quantity: cumulative,
      date: week.weekEnd
    });
  }
  if (cumulative <= 0) return void 0;
  const finalPoint = deliveryPoints.at(-1);
  const milestones = deliveryPoints.slice(0, -1);
  return {
    id: `confirmed-${product.product}`,
    sourceRow: productIndex + 2,
    product: product.product,
    periodId: finalPoint.date.slice(0, 7),
    quantity: cumulative,
    savedPlanned: previous?.savedPlanned ?? 0,
    savedDifference: previous?.savedDifference ?? 0,
    savedMachines: previous?.savedMachines ?? [],
    dueDate: finalPoint.date,
    allowPartial: milestones.length > 0,
    partialDeliveryQuantity: milestones[0]?.quantity ?? 0,
    partialDeliveryDate: milestones[0]?.date ?? "",
    deliveryMilestones: milestones
  };
}
function weeklyScopeDemandSummary(preview, requestedScope) {
  const scope = normalizedScope(preview, requestedScope);
  const startIndex = preview.weeks.findIndex((week) => week.id === scope.startWeekId);
  const endIndex = preview.weeks.findIndex((week) => week.id === scope.endWeekId);
  return preview.products.reduce((summary, product) => {
    const priorBacklog = startIndex === 0 ? product.priorDemand : product.weeklyDemands[startIndex - 1]?.cumulativeQuantity ?? product.priorDemand;
    const selectedDemand = product.weeklyDemands.slice(startIndex, endIndex + 1).reduce((sum, week) => sum + Math.max(0, week.quantity), 0);
    return {
      priorBacklog: summary.priorBacklog + Math.max(0, priorBacklog),
      selectedDemand: summary.selectedDemand + selectedDemand
    };
  }, { priorBacklog: 0, selectedDemand: 0 });
}
function buildWeeklyPlanningState(preview, existingOrders = [], requestedScope, customerOrderOverrides = [], options = {}) {
  if (preview.format !== "confirmed-overview") throw new Error("M\xFC\u015Fteri sipari\u015F dosyas\u0131 '3. Overview (confirmed)' format\u0131nda de\u011Fil.");
  if (preview.calculationModel !== NET_SHORTAGE_CALCULATION_MODEL) throw new Error("M\xFC\u015Fteri talebi net ihtiya\xE7 modeliyle hesaplanmam\u0131\u015F. Excel\u2019i yeniden do\u011Frulay\u0131n.");
  const scope = normalizedScope(preview, requestedScope);
  const startIndex = preview.weeks.findIndex((week) => week.id === scope.startWeekId);
  const endIndex = preview.weeks.findIndex((week) => week.id === scope.endWeekId);
  const includePriorBacklog = options.includePriorBacklog ?? true;
  const demandSummary = weeklyScopeDemandSummary(preview, scope);
  const existingByProduct = new Map(existingOrders.map((order) => [order.product.toUpperCase(), order]));
  const baseOrders = [];
  preview.products.forEach((product, index) => {
    if (product.weeklyDemands.length !== preview.weeks.length) {
      throw new Error(`${product.product} i\xE7in haftal\u0131k bakiye say\u0131s\u0131 dosya ba\u015Fl\u0131klar\u0131yla e\u015Fle\u015Fmiyor.`);
    }
    const order = orderForProduct(
      product,
      index,
      startIndex,
      endIndex,
      existingByProduct.get(product.product.toUpperCase()),
      includePriorBacklog
    );
    if (order) baseOrders.push(order);
  });
  const orderCatalog = [...new Set([
    ...preview.products.map((product) => product.product),
    ...customerOrderOverrides.map((override) => override.product.trim().toUpperCase())
  ].filter(Boolean))];
  const orders = applyCustomerOrderOverrides(baseOrders, customerOrderOverrides, orderCatalog, existingOrders);
  const selectedEnd = preview.weeks[endIndex].weekEnd;
  const dataset = {
    format: "confirmed-overview",
    calculationModel: NET_SHORTAGE_CALCULATION_MODEL,
    sourceFile: preview.fileName,
    sheetName: preview.sheetName,
    snapshotDate: preview.snapshotDate,
    baselineLabel: preview.baselineLabel,
    baselineDueDate: preview.baselineDueDate,
    weeks: preview.weeks,
    products: preview.products,
    activeScope: scope,
    importedAt: (/* @__PURE__ */ new Date()).toISOString()
  };
  const totalDemand = orders.reduce((sum, order) => sum + order.quantity, 0);
  return {
    dataset,
    orders,
    orderCatalog,
    planEndDate: addUtcDays(selectedEnd, 28),
    summary: {
      orderCount: orders.length,
      totalDemand,
      priorBacklog: demandSummary.priorBacklog,
      selectedDemand: demandSummary.selectedDemand,
      includedPriorBacklog: includePriorBacklog
    }
  };
}
function previewFromDataset(dataset) {
  const normalized = normalizeCustomerDemandDataset(dataset);
  const totalQuantity = normalized.products.reduce((sum, product) => sum + product.totalDemand, 0);
  const firstWeekRequirement = normalized.products.reduce(
    (sum, product) => sum + (product.weeklyDemands[0]?.cumulativeQuantity ?? product.priorDemand),
    0
  );
  return {
    format: "confirmed-overview",
    calculationModel: NET_SHORTAGE_CALCULATION_MODEL,
    fileName: normalized.sourceFile,
    sheetName: normalized.sheetName,
    snapshotDate: normalized.snapshotDate,
    baselineLabel: normalized.baselineLabel,
    baselineDueDate: normalized.baselineDueDate,
    weeks: normalized.weeks,
    products: normalized.products,
    rows: normalized.products.map((product) => ({ product: product.product, quantity: product.totalDemand })),
    summary: {
      productCount: normalized.products.length,
      orderCount: normalized.products.filter((product) => product.totalDemand > 0).length,
      totalQuantity,
      openingStock: normalized.products.reduce((sum, product) => sum + product.availableQuantity, 0),
      priorDemand: normalized.products.reduce((sum, product) => sum + product.priorDemand, 0),
      firstWeekRequirement,
      lastWeekRequirement: totalQuantity,
      weekCount: normalized.weeks.length,
      firstWeek: normalized.weeks[0]?.id ?? "",
      lastWeek: normalized.weeks.at(-1)?.id ?? "",
      ignoredBlankRows: 0
    }
  };
}

// lib/planning-state.ts
var CURRENT_PLANNING_SCHEMA_VERSION = 22;
var CUSTOMER_DEMAND_PLAN_RESET_VERSION = 8;
var OPERATIONAL_AVAILABILITY_VERSION = 10;
var PRODUCT_FAMILY_SETUP_VERSION = 12;
var PROCESS_MASTER_DATA_VERSION = 13;
var WIP_LEDGER_VERSION = 14;
var PROCESS_RESOURCE_CONFIGURATION_VERSION = 16;
var DRILLING_TRANSFER_FLOW_VERSION = 18;
var FACTORY_ROUTE_CALENDAR_VERSION = 19;
var DOOSAN_ALTERNATIVE_CONFIGURATION_VERSION = 20;
var LEGACY_ORDER_PERIOD = "2026-08";
var periodPattern = /^(\d{4})-(0[1-9]|1[0-2])$/;
function previousSaturdayIfSunday(value) {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(value)) return value;
  const date = /* @__PURE__ */ new Date(`${value}T00:00:00Z`);
  if (Number.isNaN(date.getTime()) || date.getUTCDay() !== 0) return value;
  date.setUTCDate(date.getUTCDate() - 1);
  return date.toISOString().slice(0, 10);
}
function inputDateToSerial2(value) {
  return value ? (Date.parse(`${value}T00:00:00Z`) - Date.UTC(1899, 11, 30)) / 864e5 : 0;
}
function isPeriodId(value) {
  return typeof value === "string" && periodPattern.test(value);
}
function periodIndex(periodId) {
  if (!isPeriodId(periodId)) throw new Error(`Ge\xE7ersiz d\xF6nem: ${String(periodId)}`);
  const [year, month] = periodId.split("-").map(Number);
  return year * 12 + month - 1;
}
function periodFromIndex(index) {
  if (!Number.isInteger(index) || index < 0) throw new Error(`Ge\xE7ersiz d\xF6nem indeksi: ${index}`);
  const year = Math.floor(index / 12);
  const month = index % 12 + 1;
  return `${year}-${String(month).padStart(2, "0")}`;
}
function periodRange(scope) {
  const start = periodIndex(scope.startPeriod);
  const end = periodIndex(scope.endPeriod);
  if (start > end) throw new Error("Planlama ba\u015Flang\u0131\xE7 d\xF6nemi biti\u015F d\xF6neminden sonra olamaz.");
  return Array.from({ length: end - start + 1 }, (_, offset) => periodFromIndex(start + offset));
}
function normalizePlanningScope(scope) {
  periodRange(scope);
  return { startPeriod: scope.startPeriod, endPeriod: scope.endPeriod };
}
function migratePlanningSeed(seed, fallbackPeriod = LEGACY_ORDER_PERIOD) {
  if (!isPeriodId(fallbackPeriod)) throw new Error(`Ge\xE7ersiz ge\xE7i\u015F d\xF6nemi: ${fallbackPeriod}`);
  const copy2 = JSON.parse(JSON.stringify(seed));
  promoteFilterMonthlyEvidence(copy2);
  if (copy2.flowSettings !== void 0) copy2.flowSettings = validateFlowSettings(copy2.flowSettings);
  if (copy2.productWeights === void 0) copy2.productWeights = copy2.productionArea === "cubuk-filtre" ? [] : initialProductWeights();
  if (copy2.rawMaterialSettings === void 0) copy2.rawMaterialSettings = initialRawMaterialSettings();
  const previousSchemaVersion = Number(copy2.schemaVersion ?? 0);
  if (previousSchemaVersion < 21 && copy2.manualBatches?.length) copy2.planNeedsRecalculation = true;
  if (previousSchemaVersion < 22 && copy2.flowSettings?.enabled && copy2.processWaitSettings && copy2.manualBatches?.length) copy2.planNeedsRecalculation = true;
  copy2.schemaVersion = CURRENT_PLANNING_SCHEMA_VERSION;
  if (copy2.productionArea === "cubuk-filtre" && !copy2.processMasterData) throw new Error("\xC7ubuk Filtre \xFCretim verileri eksik.");
  if (copy2.productionArea !== "cubuk-filtre" && (previousSchemaVersion < PROCESS_MASTER_DATA_VERSION || !copy2.processMasterData)) {
    copy2.processMasterData = cloneFoundationalProcessMasterData();
  }
  if (copy2.processMasterData) {
    copy2.processMasterData.products = copy2.processMasterData.products.map((product) => ({
      ...product,
      productGroup: product.productGroup?.trim() || product.family
    }));
    copy2.processMasterData.planningStrategies = {
      ...copy2.processMasterData.planningStrategies,
      drilling: copy2.processMasterData.planningStrategies?.drilling ?? "campaign",
      deburring: copy2.processMasterData.planningStrategies?.deburring ?? "earliest-ready",
      gkm: copy2.processMasterData.planningStrategies?.gkm ?? "earliest-ready"
    };
    copy2.processMasterData.transferBatchQuantities = {
      ...copy2.processMasterData.transferBatchQuantities,
      drilling: copy2.processMasterData.transferBatchQuantities?.drilling ?? 100
    };
    if (previousSchemaVersion < DRILLING_TRANSFER_FLOW_VERSION) {
      copy2.processMasterData.products = copy2.processMasterData.products.map((product) => ({
        ...product,
        processes: product.processes.map((parameter) => parameter.process === "drilling" ? { ...parameter, waitWorkdaysBefore: 0 } : parameter)
      }));
    }
    copy2.processMasterData.resources = copy2.processMasterData.resources.map((resource) => {
      const defaultGroups = resource.process === "gkm" ? resource.id === "V-01" || resource.id === "V-02" || resource.id === "V-03" ? ["piston", "center-pin"] : [] : ["piston", "center-pin"];
      const configureGkm = previousSchemaVersion < PROCESS_RESOURCE_CONFIGURATION_VERSION && resource.process === "gkm";
      return {
        ...resource,
        active: configureGkm ? resource.id === "V-01" || resource.id === "V-02" : resource.active,
        defaultShifts: Math.max(0, Math.min(3, Math.trunc(Number(resource.defaultShifts) || 0))),
        availableStart: Number.isFinite(resource.availableStart) && resource.availableStart > 0 ? Math.floor(resource.availableStart) : void 0,
        planEnd: Number.isFinite(resource.planEnd) && resource.planEnd > 0 ? Math.ceil(resource.planEnd) : void 0,
        eligibleProductGroups: resource.eligibleProductGroups ?? defaultGroups
      };
    });
  }
  copy2.processOperationOverrides = (copy2.processOperationOverrides ?? []).filter(
    (override) => Boolean(override.batchId && override.process && override.resourceId && Number.isFinite(override.requestedStart) && override.requestedStart > 0)
  );
  copy2.products = copy2.products.map((product) => {
    const setupFamily = resolvedProductSetupFamily(product.product, product.setupFamily);
    return setupFamily ? { ...product, setupFamily } : product;
  });
  if (copy2.productionArea !== "cubuk-filtre" && previousSchemaVersion < DOOSAN_ALTERNATIVE_CONFIGURATION_VERSION) {
    const productCodes = ["R902970277", "R902719742", "R902970964"];
    const machineIds = ["C-11", "C-12", "C-08"];
    for (const productCode of productCodes) {
      const product = copy2.products.find((item) => item.product.toUpperCase() === productCode);
      const fallbackShiftRate = machineIds.map((machineId) => Number(copy2.machines.find((machine) => machine.id === machineId)?.rates[productCode]) || 0).find((rate) => rate > 0) ?? (Number(product?.shiftRate) > 0 ? Number(product?.shiftRate) : Number(product?.dailyRate) / 3);
      const preference = copy2.preferences.find((item) => item.key.toUpperCase() === productCode);
      const repairedPreference = {
        key: productCode,
        machines: [...machineIds],
        ruleType: "operational-alternative",
        description: "C-11 ve C-12 i\xE7in C-08 Doosan alternatif tezgah\u0131",
        source: "Operasyon karar\u0131 \xB7 2026-08-27"
      };
      if (preference) Object.assign(preference, repairedPreference);
      else copy2.preferences.push(repairedPreference);
      if (product) {
        product.eligibleMachines = [...machineIds];
        product.alternativeMachines = [...machineIds];
      }
      if (fallbackShiftRate > 0) {
        for (const machineId of machineIds) {
          const machine = copy2.machines.find((item) => item.id === machineId);
          if (machine && !(Number(machine.rates[productCode]) > 0)) machine.rates[productCode] = fallbackShiftRate;
        }
      }
    }
  }
  if (previousSchemaVersion < PRODUCT_FAMILY_SETUP_VERSION) {
    const legacy = copy2.setupSettings;
    copy2.setupSettings = {
      model: "product-family",
      shiftHours: Number.isFinite(legacy?.shiftHours) ? Number(legacy?.shiftHours) : 8,
      sameDiameterHours: 1,
      differentDiameterHours: Number.isFinite(legacy?.differentDiameterHours) ? Number(legacy?.differentDiameterHours) : 3,
      sameFamilyDifferentDiameterHours: 2,
      crossFamilyHours: 5
    };
  }
  copy2.orders = copy2.orders.map((order) => ({
    ...order,
    periodId: isPeriodId(order.periodId) ? order.periodId : fallbackPeriod
  }));
  if (Array.isArray(copy2.demandTargets)) {
    copy2.demandTargets = copy2.demandTargets.map((target) => ({
      ...target,
      periodId: isPeriodId(target.periodId) ? target.periodId : fallbackPeriod
    }));
  }
  copy2.customerOrderOverrides = (copy2.customerOrderOverrides ?? []).map((override) => ({
    product: String(override.product ?? "").trim().toUpperCase(),
    quantity: Math.max(0, Math.trunc(Number(override.quantity) || 0)),
    dueDate: String(override.dueDate ?? "").trim(),
    updatedAt: String(override.updatedAt ?? "")
  })).filter((override) => Boolean(override.product));
  copy2.productionHistory = (copy2.productionHistory ?? []).map((entry) => ({
    ...entry,
    process: entry.process ?? "turning",
    inventoryStatus: entry.inventoryStatus ?? "semi-finished",
    statusChangedAt: entry.statusChangedAt ?? entry.archivedAt
  }));
  copy2.wipLots = (copy2.wipLots ?? []).map((lot) => {
    const completedSteps = lot.completedSteps ?? [];
    const lastStep = completedSteps.at(-1);
    const legacyRouteReadyAt = previousSchemaVersion < FACTORY_ROUTE_CALENDAR_VERSION && lot.stage === "delivery-ready" && lastStep?.process === "gkm" ? addFactoryWorkdays(copy2, lastStep.end, 1) : lot.readyAt;
    return {
      ...lot,
      readyAt: legacyRouteReadyAt,
      availableQuantity: Math.max(0, Number(lot.availableQuantity) || 0),
      deliveredQuantity: Math.max(0, Number(lot.deliveredQuantity) || 0),
      scrappedQuantity: Math.max(0, Number(lot.scrappedQuantity) || 0),
      nextProcess: lot.nextProcess ?? nextProcessForWipStage(lot.stage),
      completedSteps
    };
  });
  copy2.productionInterruptions = copy2.productionInterruptions ?? [];
  copy2.wipMovements = copy2.wipMovements ?? [];
  copy2.chargeJourneyNotes = (copy2.chargeJourneyNotes ?? []).filter((note) => Boolean(note.chargeKey && note.segmentId && note.note?.trim()));
  if (previousSchemaVersion < WIP_LEDGER_VERSION || !copy2.wipLots.length) hydrateWipFromProductionHistory(copy2);
  const activeScopeStart = copy2.activePlanRun?.scope.kind === "customer-weeks" ? inputDateToSerial2(copy2.activePlanRun.scope.startDate) : 0;
  copy2.machines = copy2.machines.map((machine) => {
    if (Number.isFinite(machine.operationalAvailableStart)) return machine;
    let operationalAvailableStart = machine.availableStart;
    if (previousSchemaVersion < OPERATIONAL_AVAILABILITY_VERSION && activeScopeStart > 0) {
      const currentJobEnd = Number(machine.currentJob?.end) || 0;
      operationalAvailableStart = currentJobEnd > 0 ? Math.min(machine.availableStart, currentJobEnd) : Math.min(machine.availableStart, activeScopeStart);
    }
    return { ...machine, operationalAvailableStart };
  });
  if (copy2.customerDemand) {
    const previousDemand = copy2.customerDemand;
    copy2.customerDemand = normalizeCustomerDemandDataset(copy2.customerDemand);
    const dateReplacements = new Map([
      [previousDemand.baselineDueDate, copy2.customerDemand.baselineDueDate],
      ...previousDemand.weeks.map((week, index) => [week.weekEnd, copy2.customerDemand.weeks[index]?.weekEnd ?? week.weekEnd])
    ]);
    const overriddenProducts = new Set(copy2.customerOrderOverrides.map((override) => override.product));
    const normalizedCustomerDate = (orderId, value) => dateReplacements.get(value) ?? (orderId.startsWith("confirmed-") ? previousSaturdayIfSunday(value) : value);
    copy2.orders = copy2.orders.map((order) => overriddenProducts.has(order.product.toUpperCase()) ? order : {
      ...order,
      dueDate: normalizedCustomerDate(order.id, order.dueDate),
      partialDeliveryDate: normalizedCustomerDate(order.id, order.partialDeliveryDate),
      deliveryMilestones: order.deliveryMilestones?.map((milestone) => ({
        ...milestone,
        date: normalizedCustomerDate(order.id, milestone.date)
      }))
    });
    if (previousSchemaVersion < CUSTOMER_DEMAND_PLAN_RESET_VERSION) {
      copy2.manualBatches = [];
      copy2.activePlanRun = void 0;
      copy2.planRunSequence = void 0;
      copy2.lastAutomaticPlan = void 0;
    }
  }
  copy2.openingStock = copy2.customerDemand ? {} : Object.entries(copy2.openingStock ?? {}).reduce((stock, [product, quantity]) => {
    const code3 = product.trim().toUpperCase();
    const normalizedQuantity = Math.max(0, Number(quantity) || 0);
    if (code3 && normalizedQuantity > 0) stock[code3] = normalizedQuantity;
    return stock;
  }, {});
  const existingScope = copy2.activePlanningScope;
  copy2.activePlanningScope = existingScope && isPeriodId(existingScope.startPeriod) && isPeriodId(existingScope.endPeriod) ? normalizePlanningScope(existingScope) : { startPeriod: fallbackPeriod, endPeriod: fallbackPeriod };
  return copy2;
}

// features/planning/session/planning-state.ts
var machineCatalogNames = { "C-13": "C\u0130T\u0130ZEN 32-2 DS", "C-14": "C\u0130T\u0130ZEN 32-1 DS", "C-15": "C\u0130T\u0130ZEN 32-3 DS", "C-16": "BENTRO", "C-17": "YALIN OTO" };
function cloneSeed(seed) {
  if (inspectTurningQueue(seed).conflicts.length) return { ...structuredClone(seed), planNeedsRecalculation: true };
  const copy2 = migratePlanningSeed(seed);
  copy2.orders = copy2.orders.map((order) => {
    const normalized = { ...order, dueDate: order.dueDate ?? "", allowPartial: order.allowPartial ?? false, partialDeliveryQuantity: order.partialDeliveryQuantity ?? 0, partialDeliveryDate: order.partialDeliveryDate ?? "", deliveryMilestones: order.deliveryMilestones ?? [] };
    const milestones = orderDeliveryMilestones(normalized);
    return { ...normalized, deliveryMilestones: milestones, partialDeliveryQuantity: milestones[0]?.quantity ?? 0, partialDeliveryDate: milestones[0]?.date ?? "", allowPartial: milestones.length > 0 };
  });
  copy2.orderCatalog = Array.isArray(copy2.orderCatalog) ? [...new Set(copy2.orderCatalog.map((product) => String(product).trim().toUpperCase()).filter(Boolean))] : void 0;
  copy2.orderCatalogName = copy2.orderCatalogName?.trim() || void 0;
  copy2.products = copy2.products.map((product) => ({ ...product, eligibleMachines: product.eligibleMachines ?? [], alternativeMachines: product.alternativeMachines ?? [] }));
  copy2.machines = copy2.machines.map((machine) => {
    const normalized = machine.capacityFactor == null && machine.shiftFactor > 0 && machine.shiftFactor < 1 ? { ...machine, capacityFactor: machine.shiftFactor, shiftFactor: 1 } : { ...machine, capacityFactor: machine.capacityFactor ?? 1 };
    const clean = (value) => value.trim().toLocaleLowerCase("tr-TR") === "none" ? "" : value;
    return { ...normalized, name: copy2.machineCatalogVersion ? normalized.name : machineCatalogNames[normalized.id] ?? normalized.name, currentJob: { ...normalized.currentJob, workOrder: clean(normalized.currentJob.workOrder), product: clean(normalized.currentJob.product), diameter: normalized.currentJob.diameter === "0" ? "" : normalized.currentJob.diameter, originalQuantity: normalized.currentJob.originalQuantity ?? normalized.currentJob.quantity, remainingQuantity: normalized.currentJob.remainingQuantity ?? normalized.currentJob.quantity } };
  });
  copy2.machineCatalogVersion = 1;
  copy2.setupSettings = getSetupSettings(copy2);
  copy2.manualBatches = (copy2.manualBatches ?? []).map((batch) => {
    const { rolledForwardFrom: _rolledForwardFrom, rolledForwardAt: _rolledForwardAt, ...plannedBatch } = batch;
    return { ...plannedBatch, locked: batch.locked ?? false, manuallyPlaced: batch.manuallyPlaced ?? false, workOrder: batch.workOrder ?? "" };
  });
  copy2.productionHistory = copy2.productionHistory ?? [];
  copy2.wipLots = copy2.wipLots ?? [];
  copy2.wipMovements = copy2.wipMovements ?? [];
  copy2.chargeJourneyNotes = copy2.chargeJourneyNotes ?? [];
  copy2.orderImport = orderImportMetadataForSeed(copy2) ?? void 0;
  copy2.orderImportGrossOrders = copy2.orderImport && !copy2.customerDemand ? (copy2.orderImportGrossOrders ?? copy2.orders).map((order) => ({ ...order, deliveryMilestones: order.deliveryMilestones?.map((milestone) => ({ ...milestone })) })) : void 0;
  copy2.planningEvents = copy2.planningEvents ?? [];
  copy2.holidays = (copy2.holidays ?? []).map((holiday) => ({ ...holiday, workingShifts: clampShiftCount(holiday.workingShifts) }));
  copy2.calendarEvents = (copy2.calendarEvents ?? []).map((event) => ({ ...event, start: Math.floor(event.start), end: Math.max(Math.floor(event.start), Math.floor(event.end)), shiftCount: clampShiftCount(event.shiftCount) }));
  rollForwardUnfinishedProduction(copy2, inputDateToSerial(factoryDateInput()), { turning: false });
  if (copy2.customerDemand && !copy2.activePlanRun) {
    const importedAt = copy2.customerDemand.importedAt;
    const demandState = buildWeeklyPlanningState(
      previewFromDataset(copy2.customerDemand),
      copy2.orders,
      copy2.customerDemand.activeScope,
      copy2.customerOrderOverrides,
      { includePriorBacklog: true }
    );
    copy2.orders = demandState.orders;
    copy2.orderCatalog = demandState.orderCatalog;
    copy2.customerDemand = { ...demandState.dataset, importedAt };
    copy2.openingStock = {};
  }
  try {
    return reconcileTurningSeed(copy2);
  } catch {
    copy2.planNeedsRecalculation = true;
    return copy2;
  }
}

// lib/filter-shared-transfer.ts
function clearCurrent(machine, at) {
  machine.currentJob = { workOrder: "", product: "", quantity: 0, originalQuantity: 0, remainingQuantity: 0, start: at, end: at, dailyRate: 0, diameter: "" };
}
function startTurning(seed, batches, machineId, at) {
  const machine = seed.machines.find((item) => item.id === machineId);
  if (machine.currentJob.quantity > 0 || !machine.active || machine.availableStart > at || machine.shiftFactor <= 0) return;
  const first = batches.filter((item) => item.machineId === machineId && item.status === "planned").sort((a, b) => a.planColumn - b.planColumn)[0];
  if (!first || !isMachineEligibleForProduct(seed, machineId, first.product)) return;
  const rate = machine.rates[first.product];
  if (!(rate > 0)) return;
  const setup = calculateSetup(seed, "", "", first.product, first.diameter, machineId);
  if (!Number.isFinite(setup.hours)) return;
  const timing = addMachineCapacityHours(seed, machine, at, setup.hours + first.quantity / rate * getSetupSettings(seed).shiftHours / (machine.capacityFactor || 1));
  if (timing.start > at + 1e-6 || timing.end >= Math.floor(machine.planEnd) + 1) return;
  machine.currentJob = {
    batchId: first.id,
    sharedCharge: first.sharedCharge,
    interruptionId: first.interruptionId,
    workOrder: first.workOrder ?? "",
    product: first.product,
    quantity: first.quantity,
    originalQuantity: first.quantity,
    remainingQuantity: first.quantity,
    start: timing.start,
    end: timing.end,
    dailyRate: rate * machine.shiftFactor * (machine.capacityFactor || 1),
    diameter: first.diameter
  };
  batches.splice(batches.indexOf(first), 1);
}
function consolidateTurning(seed, batches, at) {
  const transfers = [];
  const groups = new Set([...batches.map((item) => item.sharedCharge?.id), ...seed.machines.map((item) => item.currentJob.sharedCharge?.id)].filter((id) => !!id));
  for (const id of groups) {
    const queued = batches.filter((item) => item.sharedCharge?.id === id && item.status === "planned");
    const running = seed.machines.filter((item) => item.currentJob.sharedCharge?.id === id && item.currentJob.quantity > 0);
    const identity = queued[0]?.sharedCharge ?? running[0]?.currentJob.sharedCharge;
    const product = queued[0]?.product ?? running[0]?.currentJob.product;
    if (!identity || !product || identity.consolidated?.turning || !Number.isSafeInteger(identity.quantity) || identity.quantity <= 0) continue;
    const quantity = queued.reduce((sum, item) => sum + item.quantity, 0) + running.reduce((sum, item) => sum + item.currentJob.quantity, 0);
    const resources = /* @__PURE__ */ new Set([...queued.map((item) => item.machineId), ...running.map((item) => item.id)]);
    if (resources.size < 2 || quantity <= 0 || quantity * 10 > identity.quantity) continue;
    const recorded = (seed.wipLots ?? []).filter((item) => item.sharedCharge?.id === id);
    if (recorded.some((item) => item.product !== product || item.sharedCharge?.quantity !== identity.quantity)) continue;
    const output = recorded.reduce((sum, item) => sum + item.originalQuantity, 0);
    if (output + quantity !== identity.quantity || queued.some((item) => item.locked || item.routeCommitted || item.product !== product || item.sharedCharge?.quantity !== identity.quantity) || running.some((item) => item.currentJob.product !== product || item.currentJob.sharedCharge?.quantity !== identity.quantity || item.currentJob.quantity !== (item.currentJob.remainingQuantity ?? item.currentJob.quantity))) continue;
    const scope = turningIdentityScope({ ...seed, manualBatches: batches });
    if (scope.products.includes(product) || [...resources].some((resource) => scope.machineIds.includes(resource))) continue;
    const definition = seed.products.find((item) => item.product === product);
    if (!definition) continue;
    let sequence = Math.max(0, ...batches.map((item) => item.sequence));
    const portions = [...queued.map((item) => ({ ...item })), ...running.map((machine) => {
      const job = machine.currentJob;
      return {
        id: job.batchId ?? `portion-${crypto.randomUUID()}`,
        interruptionId: job.interruptionId,
        sharedCharge: job.sharedCharge,
        sequence: ++sequence,
        product,
        workOrder: job.workOrder,
        quantity: job.quantity,
        orderQuantity: identity.quantity,
        machineId: machine.id,
        diameter: job.diameter,
        batchSize: definition.batchSize,
        dailyRate: job.dailyRate,
        availableStart: at,
        planEnd: machine.planEnd,
        reason: "Ortak \u015Farj\u0131n kalan miktar\u0131",
        explanation: "Fiili \xE7\u0131kt\u0131 ayr\u0131ca kaydedildi.",
        planColumn: 13,
        existingQuantity: output,
        start: at,
        end: at,
        status: "planned",
        manuallyPlaced: true
      };
    })];
    const choices = seed.machines.flatMap((machine) => {
      if (!machine.active || machine.shiftFactor <= 0 || !isMachineEligibleForProduct(seed, machine.id, product) || !(machine.rates[product] > 0)) return [];
      if (batches.some((item) => item.machineId === machine.id && (item.locked || item.routeCommitted))) return [];
      const currentSame = running.some((item) => item.id === machine.id);
      const currentEnd = currentSame ? addMachineCapacityHours(
        seed,
        machine,
        Math.max(at, machine.availableStart),
        machine.currentJob.quantity / machine.rates[product] * getSetupSettings(seed).shiftHours / (machine.capacityFactor || 1)
      ).end : machine.currentJob.end;
      let cursor = Math.max(at, machine.availableStart, currentEnd);
      let previous = machine.currentJob.product;
      const planned = portions.filter((portion) => !currentSame || portion.id !== machine.currentJob.batchId).map((portion) => {
        const setup = calculateSetup(seed, previous, machine.currentJob.diameter, product, definition.diameter, machine.id);
        if (!Number.isFinite(setup.hours)) return void 0;
        const runHours = portion.quantity / machine.rates[product] * getSetupSettings(seed).shiftHours / (machine.capacityFactor || 1);
        const timing = addMachineCapacityHours(seed, machine, cursor, setup.hours + runHours);
        cursor = timing.end;
        previous = product;
        return {
          ...portion,
          machineId: machine.id,
          ...timing,
          setupHours: setup.hours,
          runHours,
          dailyRate: machine.rates[product] * machine.shiftFactor * (machine.capacityFactor || 1),
          availableStart: machine.availableStart,
          planEnd: machine.planEnd
        };
      });
      return planned.every((item) => !!item) && cursor < Math.floor(machine.planEnd) + 1 ? [{ machineId: machine.id, end: cursor, currentEnd, planned }] : [];
    }).sort((a, b) => a.end - b.end || a.machineId.localeCompare(b.machineId));
    const chosen = choices[0];
    if (!chosen) continue;
    const portionIds = new Set(portions.map((item) => item.id));
    for (const machine of running) if (machine.id !== chosen.machineId) clearCurrent(machine, at);
    const retained = batches.filter((item) => !portionIds.has(item.id));
    const targetQueue = retained.filter((item) => item.machineId === chosen.machineId && item.status === "planned").sort((a, b) => a.planColumn - b.planColumn);
    const sharedCharge = { ...identity, consolidated: { ...identity.consolidated, turning: chosen.machineId } };
    const targetCurrent = seed.machines.find((item) => item.id === chosen.machineId).currentJob;
    if (targetCurrent.sharedCharge?.id === id) {
      targetCurrent.sharedCharge = sharedCharge;
      targetCurrent.end = chosen.currentEnd;
    }
    chosen.planned.forEach((item, index) => {
      item.sharedCharge = sharedCharge;
      item.planColumn = 13 + index;
      for (const pause of seed.productionInterruptions ?? []) if (pause.chargeId === item.id && pause.turningBatch && !pause.completedAt) pause.turningBatch = structuredClone(item);
    });
    let tail = chosen.end;
    let previousProduct = product;
    let previousDiameter = definition.diameter;
    const targetMachine = seed.machines.find((item) => item.id === chosen.machineId);
    for (const [index, item] of targetQueue.entries()) {
      const setup = calculateSetup(seed, previousProduct, previousDiameter, item.product, item.diameter, targetMachine.id);
      const rate = targetMachine.rates[item.product];
      if (!(rate > 0) || !Number.isFinite(setup.hours)) throw new Error("Aktar\u0131m sonras\u0131 kuyruk hesaplanamad\u0131; kaynak parametrelerini kontrol edin.");
      const runHours = item.quantity / rate * getSetupSettings(seed).shiftHours / (targetMachine.capacityFactor || 1);
      const timing = addMachineCapacityHours(seed, targetMachine, tail, setup.hours + runHours);
      Object.assign(item, timing, { setupHours: setup.hours, runHours, planColumn: 13 + chosen.planned.length + index });
      tail = timing.end;
      previousProduct = item.product;
      previousDiameter = item.diameter;
    }
    batches.splice(0, batches.length, ...retained, ...chosen.planned);
    const released = [...resources].filter((resource) => resource !== chosen.machineId);
    for (const resource of [chosen.machineId, ...released]) startTurning(seed, batches, resource, at);
    transfers.push({ chargeId: id, process: "turning", quantity, target: chosen.machineId, released });
  }
  return transfers;
}
function consolidateMilling(seed, batches, at) {
  const transfers = [];
  const ids = new Set((seed.wipLots ?? []).map((item) => item.sharedCharge?.id).filter((id) => !!id));
  for (const id of ids) {
    const all = seed.wipLots.filter((item) => item.sharedCharge?.id === id);
    const pending = all.filter((item) => item.availableQuantity > 0 && !item.completedSteps.some((step) => step.process === "milling") && !["delivered", "scrapped"].includes(item.stage));
    const identity = pending[0]?.sharedCharge;
    if (!identity || identity.consolidated?.milling || !Number.isSafeInteger(identity.quantity) || identity.quantity <= 0) continue;
    const quantity = pending.reduce((sum, item) => sum + item.availableQuantity, 0);
    if (all.some((item) => item.product !== pending[0].product || item.sharedCharge?.quantity !== identity.quantity)) continue;
    if (quantity <= 0 || quantity * 10 > identity.quantity || all.reduce((sum, item) => sum + item.originalQuantity, 0) !== identity.quantity) continue;
    const ready = pending.filter((item) => item.nextProcess === "milling" && item.stage !== "on-hold" && item.stage !== "unclassified" && item.readyAt <= at);
    const readyIds = new Set(ready.map((item) => item.id));
    const running = (seed.processCurrentJobs ?? []).filter((item) => item.process === "milling" && readyIds.has(item.wipLotId));
    if (running.some((item) => item.originalQuantity !== item.remainingQuantity || item.originalQuantity !== ready.find((lot) => lot.id === item.wipLotId)?.availableQuantity)) continue;
    const before = buildDownstreamProcessPlan(seed, { batches });
    const resources = new Set(before.operations.filter((item) => item.process === "milling" && readyIds.has(item.wipLotId ?? "") && !item.actual).map((item) => item.resourceId));
    if (resources.size < 2 || !ready.length) continue;
    const parameter = seed.processMasterData?.products.find((item) => item.product === ready[0].product)?.processes.find((item) => item.process === "milling");
    if (!parameter) continue;
    const updatedAt = (/* @__PURE__ */ new Date()).toISOString();
    const trial = (resourceId) => {
      const next = structuredClone(seed);
      next.processCurrentJobs = next.processCurrentJobs?.filter((item) => item.resourceId === resourceId || !running.some((current) => current.operationId === item.operationId));
      const retainedCurrent = next.processCurrentJobs?.find((item) => item.resourceId === resourceId && running.some((current) => current.operationId === item.operationId));
      if (retainedCurrent) {
        const resource = next.processMasterData?.resources.find((item) => item.id === resourceId);
        if (!resource?.active || resource.defaultShifts <= 0 || !(retainedCurrent.unitsPerShift > 0)) return void 0;
        const capacity = { id: resourceId, shiftFactor: resource.defaultShifts, finishOffset: 0 };
        const setupEnd = addMachineCapacityHours(next, capacity, retainedCurrent.start, retainedCurrent.setupHours).end;
        retainedCurrent.end = addMachineCapacityHours(
          next,
          capacity,
          Math.max(at, setupEnd, resource.availableStart ?? 0),
          retainedCurrent.remainingQuantity / retainedCurrent.unitsPerShift * getSetupSettings(next).shiftHours
        ).end;
      }
      next.processOperationOverrides = [
        ...(next.processOperationOverrides ?? []).filter((item) => !(readyIds.has(item.batchId) && item.process === "milling")),
        ...ready.map((lot) => ({ batchId: lot.id, process: "milling", resourceId, requestedStart: at, updatedAt }))
      ];
      const plan = buildDownstreamProcessPlan(next, { batches });
      const placements = plan.operations.filter((item) => item.process === "milling" && readyIds.has(item.wipLotId ?? "") && !item.actual);
      if (placements.length !== ready.length || placements.some((item) => item.resourceId !== resourceId)) return void 0;
      return { next, plan, resourceId, end: Math.max(...placements.map((item) => item.end)) };
    };
    const chosen = activeProcessResourceIds(parameter).flatMap((resource) => {
      const option = trial(resource);
      return option ? [option] : [];
    }).sort((a, b) => a.end - b.end || a.resourceId.localeCompare(b.resourceId))[0];
    if (!chosen) continue;
    Object.assign(seed, chosen.next);
    for (const lot of seed.wipLots ?? []) if (pending.some((item) => item.id === lot.id)) lot.sharedCharge = { ...identity, consolidated: { ...identity.consolidated, milling: chosen.resourceId } };
    const released = [...resources].filter((resource) => resource !== chosen.resourceId);
    for (const resource of [chosen.resourceId, ...released]) {
      const plan = buildDownstreamProcessPlan(seed, { batches });
      const available = processJobStartAvailability(seed, plan, resource, at);
      if (available.operation) startProcessCurrentJob(seed, { batches }, available.operation.id, at);
    }
    transfers.push({ chargeId: id, process: "milling", quantity, target: chosen.resourceId, released });
  }
  return transfers;
}
function consolidateFilterSharedRemainders(seed, result, at) {
  if (seed.productionArea !== "cubuk-filtre") return { seed, result, transfers: [] };
  if (!Number.isFinite(at) || at <= 0) throw new Error("Aktar\u0131m tarihi ge\xE7ersiz.");
  const next = structuredClone(seed), batches = structuredClone(result.batches);
  const transfers = [...consolidateTurning(next, batches, at), ...consolidateMilling(next, batches, at)];
  if (!transfers.length) return { seed, result, transfers };
  next.manualBatches = batches;
  next.planNeedsRecalculation = true;
  next.planningEvents = [...transfers.map((transfer) => ({
    id: crypto.randomUUID(),
    createdAt: (/* @__PURE__ */ new Date()).toISOString(),
    type: "current-job",
    machineId: transfer.target,
    message: `${transfer.chargeId}: %10 kalan kural\u0131; ${transfer.quantity} adet ${transfer.target} \xFCzerinde topland\u0131. Serbest kalan: ${transfer.released.join(", ")}.`
  })), ...next.planningEvents ?? []].slice(0, 200);
  return { seed: next, result: scenarioResultFromBatches(next, batches), transfers };
}

// lib/production-command.ts
var productionCommandNames = ["correctJourneyDates", "recordManualArchiveReceipt", "saveMachineAvailability", "setMachineQueueLock", "setAllMachineQueueLocks", "saveCurrentJob", "replaceTurningJob", "recordOutsidePlanProduction", "completeCurrentJob", "changeProductionHistoryStatus", "restoreProductionDelivery", "editProductionHistoryEntry", "allocateProductionHistory", "deliverJourneyWip", "releaseJourneyBuffer", "finishWipOperation", "beginDownstreamCurrentJob", "replaceDownstreamCurrentJob", "saveDownstreamCurrentJob", "finishDownstreamCurrentJob", "changeWipStage", "releaseHeldWip", "saveJourneyNote", "cancelRemainingProduction", "reviewProductionCancellation", "reviseOfficialOrder", "deactivateParameters"];
function productionCommandBasis(seed, command) {
  if (seed.productionArea === "cubuk-filtre" && command.kind !== "saveJourneyNote") return { ...seed, chargeJourneyNotes: [], planningEvents: [] };
  if (command.kind === "completeCurrentJob" || command.kind === "deliverJourneyWip") {
    const machineId = command.kind === "completeCurrentJob" ? String(command.args[0]) : void 0;
    const lotId2 = command.kind === "deliverJourneyWip" ? command.args[0]?.lotId : void 0;
    const machine = seed.machines.find((row) => row.id === machineId);
    const lot = seed.wipLots?.find((row) => row.id === lotId2);
    const queue = (seed.manualBatches ?? []).filter((row) => row.machineId === machineId);
    const products = new Set([machine?.currentJob.product, ...seed.productionArea === "cubuk-filtre" ? [lot?.product] : [], ...queue.map((row) => row.product)].filter(Boolean).map((value) => value.trim().toUpperCase()));
    const identities = new Set([lotId2, machine?.currentJob.batchId, ...queue.map((row) => row.id)].filter((value) => Boolean(value)));
    const fields = ["productionHistory", "wipLots", "wipMovements", "productionInterruptions", "processCurrentJobs", "processOperationOverrides"];
    const links = (row) => [
      row.id,
      row.sourceEntryId,
      row.sourceBatchId,
      row.sourceHistoryEntryId,
      row.parentLotId,
      row.lotId,
      row.batchId,
      row.chargeId,
      row.wipLotId,
      row.interruptionId,
      ...row.interruptionIds ?? [],
      ...(row.wipAllocations ?? []).map((item) => item.lotId)
    ].filter((value) => typeof value === "string" && Boolean(value));
    const related = (row) => products.has(String(row.product ?? "").trim().toUpperCase()) || links(row).some((id) => identities.has(id));
    let size = -1;
    while (size !== identities.size) {
      size = identities.size;
      for (const field of fields) for (const row of seed[field] ?? []) {
        const record = row;
        if (related(record)) for (const id of links(record)) identities.add(id);
      }
    }
    const basis = {
      ...seed,
      commandBasisVersion: 2,
      commandKind: command.kind,
      chargeJourneyNotes: [],
      planningEvents: [],
      planNeedsRecalculation: false,
      lastAutomaticPlan: null,
      planRunSequence: null,
      // Delivery uses the recorded route and lot, never a machine's current job
      // or a queued proposal. Completion still checks all machine facts.
      machines: machineId ? seed.machines : seed.machines.map(({ currentJob: _current, availableStart: _available, operationalAvailableStart: _operational, ...configuration }) => configuration),
      manualBatches: machineId ? queue : []
    };
    for (const field of fields) basis[field] = (seed[field] ?? []).filter((row) => related(row));
    return basis;
  }
  return legacyProductionCommandBasis(seed, command);
}
function legacyProductionCommandBasis(seed, command) {
  if (command.kind === "saveJourneyNote") {
    const input = command.args[0];
    return (seed.chargeJourneyNotes ?? []).filter((note) => note.chargeKey === input.chargeKey && note.segmentId === input.segmentId);
  }
  const localKinds = ["deliverJourneyWip", "releaseJourneyBuffer", "changeWipStage", "releaseHeldWip"];
  if (localKinds.includes(command.kind)) {
    const arg = command.args[0];
    const lotId2 = typeof arg === "string" ? arg : arg?.lotId;
    const lot = seed.wipLots?.find((row) => row.id === lotId2);
    const ids = new Set([lotId2, lot?.sourceHistoryEntryId, lot?.sourceBatchId, lot?.parentLotId].filter(Boolean));
    const related = (row) => Boolean(row && typeof row === "object" && Object.values(row).some((v) => typeof v === "string" && ids.has(v)));
    return {
      ...seed,
      chargeJourneyNotes: [],
      planningEvents: [],
      planNeedsRecalculation: false,
      lastAutomaticPlan: null,
      planRunSequence: null,
      wipLots: (seed.wipLots ?? []).filter(related),
      wipMovements: (seed.wipMovements ?? []).filter(related),
      productionHistory: (seed.productionHistory ?? []).filter(related)
    };
  }
  return { ...seed, chargeJourneyNotes: [], planningEvents: [] };
}

// lib/production-interruption-actions.ts
function replaceTurningCurrentJob(seed, result, machineId, targetBatchId, input, occurredAt) {
  assertProductionSwitchSnapshot(seed, result.batches, input);
  assertOperationalMachineIdentity(seed, result, machineId);
  const next = structuredClone(seed);
  const machine = next.machines.find((item) => item.id === machineId);
  if (!machine?.currentJob.product || machine.currentJob.quantity <= 0) throw new Error("De\u011Fi\u015Ftirilecek mevcut Torna i\u015Fi bulunamad\u0131.");
  const current = machine.currentJob;
  const produced2 = validateProductionInterruption(input, current.quantity, current.start, occurredAt);
  const target = result.batches.find((item) => item.id === targetBatchId && item.status === "planned");
  if (!target || target.machineId !== machineId) throw new Error("Ayn\u0131 tezgah\u0131n kuyru\u011Fundan yeni bir \u015Farj se\xE7in.");
  if (result.batches.some((item) => item.machineId === machineId && item.locked)) throw new Error("\u0130\u015F de\u011Fi\u015Fimi i\xE7in tezgah kuyru\u011Fundaki kilitleri \xF6nce kald\u0131r\u0131n.");
  if (!machine.active || !isMachineEligibleForProduct(next, machineId, target.product)) throw new Error("Yeni i\u015F bu tezgahta \xFCretime uygun de\u011Fil.");
  const rate = machine.rates[target.product.toUpperCase()] ?? 0;
  if (rate <= 0 || machine.shiftFactor <= 0) throw new Error("Yeni i\u015F i\xE7in \xFCretim h\u0131z\u0131 veya vardiya eksik.");
  const chargeId = current.batchId ?? `returned-${crypto.randomUUID()}`;
  const pause = produced2 > 0 ? { id: `pause-${crypto.randomUUID()}`, kind: input.kind, chargeId, process: "turning", resourceId: machineId, product: current.product, workOrder: current.workOrder, producedQuantity: produced2, remainingQuantity: current.quantity - produced2, reason: input.reason.trim(), occurredAt } : void 0;
  if (pause) {
    next.productionInterruptions = [...next.productionInterruptions ?? [], pause];
    const id = pause.id;
    const archivedAt = (/* @__PURE__ */ new Date()).toISOString();
    const history = { ...current.sharedCharge ? { sharedCharge: current.sharedCharge } : {}, id: `history-${id}`, interruptionIds: [id], machineId, machineName: machine.name, workOrder: current.workOrder, product: current.product, originalQuantity: produced2, completedQuantity: produced2, start: current.start, plannedEnd: current.end, completedAt: occurredAt, archivedAt, process: "turning", inventoryStatus: "semi-finished", statusChangedAt: archivedAt, statusChangeReason: `${pause.kind === "partial-completion" ? "K\u0131smi \xFCretim tamamland\u0131." : "\xDCretime ara verildi."} ${pause.reason}` };
    next.productionHistory = [history, ...next.productionHistory ?? []];
    if (!registerTurningCompletion(next, history)) throw new Error("\xDCretilen adedin yar\u0131 mam\xFCl kayd\u0131 i\xE7in \xFCr\xFCn rotas\u0131n\u0131 tamamlay\u0131n.");
  }
  const setup = calculateSetup(next, current.product, current.diameter, target.product, target.diameter, machine.id);
  const hours = target.quantity / rate * getSetupSettings(next).shiftHours / (machine.capacityFactor ?? 1);
  const timeline = addMachineCapacityHours(next, machine, occurredAt, setup.hours + hours);
  machine.currentJob = { ...target.sharedCharge ? { sharedCharge: target.sharedCharge } : {}, batchId: target.id, interruptionId: target.interruptionId, workOrder: target.workOrder ?? "", product: target.product, quantity: target.quantity, originalQuantity: target.quantity, remainingQuantity: target.quantity, start: timeline.start, end: timeline.end, dailyRate: rate * machine.shiftFactor * (machine.capacityFactor ?? 1), diameter: target.diameter };
  machine.availableStart = timeline.end;
  machine.operationalAvailableStart = timeline.end;
  const resumed = next.productionInterruptions?.find((item) => item.id === target.interruptionId);
  if (resumed) resumed.resumedAt = occurredAt;
  const priorPause = (next.productionInterruptions ?? []).findLast((item) => item.chargeId === chargeId && item.process === "turning" && !item.completedAt && item.producedQuantity !== 0);
  const recovery = pause ?? priorPause;
  const { sharedCharge: _targetCharge, ...targetFields } = target;
  const remainder = { ...targetFields, ...current.sharedCharge ? { sharedCharge: current.sharedCharge } : {}, routeCommitted: void 0, routeTargetDate: void 0, id: chargeId, interruptionId: recovery?.id ?? (hasProtectedProductionRemainder(next, chargeId, current.interruptionId) ? current.interruptionId : void 0), product: current.product, workOrder: current.workOrder, quantity: current.quantity - produced2, diameter: current.diameter, sequence: Math.max(0, ...result.batches.map((item) => item.sequence)) + 1, locked: false, manuallyPlaced: true, planColumn: 13, reason: recovery ? recovery.kind === "partial-completion" ? "K\u0131smi \xFCretimin kalan i\u015Fi." : "\xDCretime ara verildi." : "\xDCretim yap\u0131lmadan kuyru\u011Fa d\xF6nd\xFC.", explanation: recovery?.reason ?? "" };
  const localQueue = result.batches.filter((item) => item.id !== target.id && item.machineId === machineId && item.status === "planned").sort((left, right) => left.planColumn - right.planColumn || left.sequence - right.sequence).map((item, index) => ({ ...item, planColumn: 14 + index }));
  const local = recalculateManualScenario({ ...next, machines: [machine] }, [remainder, ...localQueue]);
  const unchanged = result.batches.filter((item) => item.machineId !== machineId || item.status !== "planned").map((item) => ({ ...item }));
  const nextResult = scenarioResultFromBatches(next, [...local.batches, ...unchanged]);
  if (recovery) recovery.turningBatch = { ...nextResult.batches.find((item) => item.id === chargeId) };
  next.manualBatches = nextResult.batches;
  next.lastAutomaticPlan = void 0;
  next.planRunSequence = void 0;
  next.planNeedsRecalculation = true;
  return { seed: next, result: nextResult };
}
function recordOutsidePlanProduction(seed, result, input, now) {
  assertProductionSwitchSnapshot(seed, result.batches, { kind: "partial-completion", produced: true, expectedSignature: input.expectedSignature });
  const batch = result.batches.find((item) => item.id === input.batchId && item.status === "planned");
  if (!batch) throw new Error("Kuyrukta se\xE7ilen \u015Farj bulunamad\u0131. Pencereyi kapat\u0131p g\xFCncel kay\u0131tla yeniden a\xE7\u0131n.");
  const reason = input.reason?.trim() ?? "";
  if (!reason || reason.length > 2e3) throw new Error("Plan d\u0131\u015F\u0131 \xFCretim nedeni zorunludur ve en fazla 2000 karakter olabilir.");
  if (!Number.isSafeInteger(input.quantity) || input.quantity <= 0 || input.quantity > batch.quantity) throw new Error(`\xDCretilen adet 1 ile ${batch.quantity} aras\u0131nda tam say\u0131 olmal\u0131d\u0131r.`);
  if (!Number.isFinite(input.producedAt) || input.producedAt <= 0 || input.producedAt > now + 1e-8) throw new Error("\xDCretim tarihi gelecekte olamaz.");
  const next = structuredClone(seed);
  const machine = next.machines.find((item) => item.id === batch.machineId);
  if (!machine) throw new Error(`${batch.machineId} tezgah\u0131 bulunamad\u0131.`);
  const partial = input.quantity < batch.quantity;
  const splitId = partial ? `split-${crypto.randomUUID()}` : void 0;
  const archivedAt = (/* @__PURE__ */ new Date()).toISOString();
  const history = {
    ...batch.sharedCharge ? { sharedCharge: batch.sharedCharge } : {},
    id: `history-${crypto.randomUUID()}`,
    sourceBatchId: partial ? `output-${splitId}` : batch.id,
    interruptionIds: splitId ? [splitId] : void 0,
    machineId: machine.id,
    machineName: machine.name,
    workOrder: batch.workOrder ?? "",
    product: batch.product,
    originalQuantity: input.quantity,
    completedQuantity: input.quantity,
    start: input.producedAt,
    plannedEnd: batch.end,
    completedAt: input.producedAt,
    archivedAt,
    process: "turning",
    inventoryStatus: "semi-finished",
    statusChangedAt: archivedAt,
    statusChangeReason: `Plan d\u0131\u015F\u0131 \xFCretim kayd\u0131. ${reason}`
  };
  next.productionHistory = [history, ...next.productionHistory ?? []];
  const remaining = partial ? { ...batch, quantity: batch.quantity - input.quantity, interruptionId: splitId, manuallyPlaced: true, reason: "Plan d\u0131\u015F\u0131 \xFCretimin kalan i\u015Fi.", explanation: reason } : void 0;
  finishProductionInterruptions(next, batch.id, "turning", input.producedAt);
  if (partial) next.productionInterruptions = [...next.productionInterruptions ?? [], {
    id: splitId,
    kind: "partial-completion",
    chargeId: batch.id,
    process: "turning",
    resourceId: machine.id,
    product: batch.product,
    workOrder: batch.workOrder ?? "",
    producedQuantity: input.quantity,
    remainingQuantity: remaining.quantity,
    reason,
    occurredAt: input.producedAt,
    turningBatch: { ...remaining }
  }];
  if (!registerTurningCompletion(next, history)) throw new Error("\xDCretilen adedin yar\u0131 mam\xFCl kayd\u0131 i\xE7in \xFCr\xFCn rotas\u0131n\u0131 tamamlay\u0131n.");
  const batches = result.batches.flatMap((item) => item.id !== batch.id ? [{ ...item }] : remaining ? [remaining] : []);
  const nextResult = scenarioResultFromBatches(next, batches);
  next.manualBatches = nextResult.batches;
  next.lastAutomaticPlan = void 0;
  next.planRunSequence = void 0;
  next.planNeedsRecalculation = true;
  return { seed: next, result: nextResult, batch };
}

// lib/machine-management.ts
function setMachineAvailability(seed, machineId, start) {
  const machine = seed.machines.find((item) => item.id === machineId);
  if (!machine) throw new Error(`${machineId} tezgah\u0131 bulunamad\u0131.`);
  if (!Number.isInteger(start) || start <= 0) throw new Error("Ge\xE7erli bir m\xFCsait ba\u015Flang\u0131\xE7 tarihi girin.");
  machine.availableStart = start;
  machine.operationalAvailableStart = start;
  seed.planNeedsRecalculation = true;
  seed.lastAutomaticPlan = void 0;
  seed.planRunSequence = void 0;
}

// lib/archive-corrections.ts
function archiveEntrySignature(entry) {
  return JSON.stringify(entry);
}
function assertArchiveEntry(seed, entryId, expected) {
  const entry = seed.productionHistory?.find((item) => item.id === entryId);
  if (!entry || expected && archiveEntrySignature(entry) !== expected) throw new Error("Ar\u015Fiv kayd\u0131 de\u011Fi\u015Fti. G\xFCncel bilgileri yeniden a\xE7\u0131n.");
  return entry;
}
function shipmentAllocations(seed, entry) {
  if (entry.wipAllocations) {
    if (entry.wipAllocations.reduce((sum, item) => sum + item.quantity, 0) !== entry.completedQuantity) throw new Error("Teslimat ile \u015Farj bakiyesi e\u015Fle\u015Fmiyor.");
    for (const item of entry.wipAllocations) if (!(item.quantity > 0) || (seed.wipLots?.find((lot) => lot.id === item.lotId)?.deliveredQuantity ?? 0) < item.quantity) throw new Error("Teslim edilen \u015Farj bakiyesi yetersiz.");
    return structuredClone(entry.wipAllocations);
  }
  let remaining = entry.completedQuantity;
  const allocations = [];
  for (const lot of productionHistoryLots(seed, entry)) {
    const reserved = (seed.productionHistory ?? []).filter((other) => other.id !== entry.id && other.inventoryStatus === "delivered").flatMap((other) => other.wipAllocations ?? []).filter((item) => item.lotId === lot.id).reduce((sum, item) => sum + item.quantity, 0);
    const quantity = Math.min(remaining, Math.max(0, lot.deliveredQuantity - reserved));
    if (quantity) allocations.push({ lotId: lot.id, quantity });
    remaining -= quantity;
  }
  if (remaining) throw new Error("Bu eski teslimat\u0131n do\u011Frulanm\u0131\u015F \u015Farj bakiyesi bulunamad\u0131. Ar\u015Fiv ve yar\u0131 mam\xFCl e\u015Fle\u015Fmesini kontrol edin.");
  return allocations;
}
function clearDelivery(entry) {
  entry.inventoryStatus = "semi-finished";
  delete entry.deliveredAt;
  delete entry.deliveredAtTime;
  delete entry.deliveredAtPrecision;
  delete entry.wipAllocations;
  entry.statusChangedAt = (/* @__PURE__ */ new Date()).toISOString();
}
function restorePieces(seed, allocations, quantity, restoredEntry, reason) {
  let left = quantity;
  const recordedAt = (/* @__PURE__ */ new Date()).toISOString();
  const now = factoryNowSerial(recordedAt);
  for (const allocation of allocations) {
    const amount = Math.min(left, allocation.quantity);
    if (!amount) continue;
    const lot = seed.wipLots.find((item) => item.id === allocation.lotId);
    lot.deliveredQuantity -= amount;
    lot.originalQuantity -= amount;
    lot.updatedAt = recordedAt;
    allocation.quantity -= amount;
    const restored = {
      ...structuredClone(lot),
      id: `restored-${crypto.randomUUID()}`,
      sourceHistoryEntryId: restoredEntry.id,
      parentLotId: lot.id,
      originalQuantity: amount,
      availableQuantity: amount,
      deliveredQuantity: 0,
      scrappedQuantity: 0,
      stage: "delivery-ready",
      nextProcess: void 0,
      readyAt: now,
      rolledForwardAt: void 0,
      rolledForwardFrom: void 0,
      createdAt: recordedAt,
      updatedAt: recordedAt
    };
    seed.wipLots.push(restored);
    seed.wipMovements = [...seed.wipMovements ?? [], { id: `restore-${crypto.randomUUID()}`, lotId: restored.id, kind: "restored", quantity: amount, fromStage: "delivered", toStage: "delivery-ready", occurredAt: now, recordedAt, note: reason }];
    left -= amount;
  }
  if (left) throw new Error("Geri al\u0131nacak teslimat bakiyesi yetersiz.");
}
function restoreArchiveDelivery(seed, result, entryId, reason, expected) {
  assertArchiveEntry(seed, entryId, expected);
  if (!reason.trim()) throw new Error("Geri alma nedenini yaz\u0131n.");
  const next = structuredClone(seed);
  const entry = assertArchiveEntry(next, entryId);
  if (entry.inventoryStatus !== "delivered") throw new Error("Yaln\u0131zca teslim edilmi\u015F kay\u0131t geri al\u0131nabilir.");
  const allocations = shipmentAllocations(next, entry);
  restorePieces(next, allocations, entry.completedQuantity, entry, reason.trim());
  clearDelivery(entry);
  entry.statusChangeReason = reason.trim();
  next.lastAutomaticPlan = void 0;
  next.planRunSequence = void 0;
  return { seed: next, result };
}
function correctArchiveRecord(seed, result, entryId, quantity, completedAt, deliveryDate, expected, correctionLotId) {
  const source = assertArchiveEntry(seed, entryId, expected);
  if (source.inventoryStatus === "delivered" && quantity !== source.completedQuantity) validateFilterShipment(seed, source.product, quantity);
  const sameDay = Math.floor(completedAt) === Math.floor(source.completedAt);
  if (source.manualReceipt && !sameDay) throw new Error("Manuel adet kayd\u0131n\u0131n tarihini bu i\u015Flemle de\u011Fi\u015Ftiremezsiniz. Kay\u0131t an\u0131 \xFCretim tarihi de\u011Fildir.");
  const actualAt = sameDay ? source.completedAt : completedAt;
  if (source.inventoryStatus === "delivered" && !sameDay) throw new Error("Teslim edilmi\u015F \u015Farj\u0131n Torna tarihi de\u011Fi\u015Ftirilemez; teslim adedi ve tarihi d\xFCzeltilebilir.");
  const dateOnly = source.inventoryStatus === "delivered" && quantity === source.completedQuantity;
  if (dateOnly && (!Number.isInteger(quantity) || quantity <= 0 || !Number.isFinite(actualAt))) throw new Error("Ar\u015Fiv kayd\u0131n\u0131n adedi ve tamamlanma tarihi ge\xE7erli olmal\u0131d\u0131r.");
  const copied = dateOnly ? structuredClone(seed) : void 0;
  const next = copied ? { seed: copied, result, entry: copied.productionHistory.find((item) => item.id === entryId) } : updateProductionHistoryEntry(seed, result, entryId, quantity, actualAt);
  if (source.inventoryStatus === "delivered") {
    const dayOnly = source.deliveredAtPrecision === "day" && (!deliveryDate || /^\d{4}-\d{2}-\d{2}$/.test(deliveryDate));
    const deliveryValue = dayOnly ? { precision: "day", value: deliveryDate || source.deliveredAt } : { precision: "minute", value: deliveryDate || factoryDateTimeInput(source.deliveredAtTime || factoryDateTimeToIso(`${source.deliveredAt}T00:00`)) };
    let deliveryAt;
    try {
      deliveryAt = parseActualDate(deliveryValue);
    } catch (error) {
      throw Error(error instanceof Error && error.message.includes("gelecekte") ? "Teslim tarihi ve saati \u015Fu andan sonra olamaz." : "Ge\xE7erli bir teslim tarihi ve saati se\xE7in.");
    }
    const deliveryIso = dayOnly ? void 0 : factoryDateTimeToIso(deliveryValue.value);
    const related = productionHistoryLots(seed, source);
    if (dayOnly || source.completedAtPrecision === "day" || related.some((lot) => lot.completedSteps.some((step) => step.endPrecision === "day" || step.startPrecision === "day"))) {
      for (const lot of related) assertRecordedDateOrder([...lot.completedSteps.flatMap((step) => [{ value: step.start, precision: step.startPrecision }, { value: step.end, precision: step.endPrecision }]), { value: deliveryAt, precision: deliveryValue.precision }], lot.processOrderConfirmed === true);
      assertRecordedDateOrder([{ value: actualAt, precision: source.completedAtPrecision }, { value: deliveryAt, precision: deliveryValue.precision }], related.length > 0 && related.every((lot) => lot.processOrderConfirmed === true));
    } else if (deliveryAt < actualAt || related.some((lot) => lot.completedSteps.some((step) => step.end > deliveryAt))) throw new Error("Teslim tarihi tamamlanan proseslerden \xF6nce olamaz.");
    const difference = quantity - source.completedQuantity;
    const allocations = dateOnly ? void 0 : shipmentAllocations(next.seed, source);
    if (difference < 0) {
      const returned = { ...source, id: `return-${crypto.randomUUID()}`, originalQuantity: -difference, completedQuantity: -difference, sourceEntryId: source.id };
      clearDelivery(returned);
      restorePieces(next.seed, allocations, -difference, returned, "Teslim edilen adet d\xFCzeltildi; fark Paketleme / Final Kontrol\u2019e al\u0131nd\u0131.");
      next.seed.productionHistory.push(returned);
    } else if (difference > 0) {
      const ids = new Set([source.id, source.sourceEntryId].filter(Boolean));
      let changed = true;
      while (changed) {
        changed = false;
        for (const entry of next.seed.productionHistory ?? []) if (entry.sourceEntryId && ids.has(entry.sourceEntryId) && !ids.has(entry.id)) {
          ids.add(entry.id);
          changed = true;
        }
      }
      const lots = (next.seed.wipLots ?? []).filter((lot) => ids.has(lot.sourceHistoryEntryId) && lot.product === source.product && lot.workOrder === source.workOrder && lot.availableQuantity > 0 && lot.stage === "delivery-ready" && wipOperationReadyAt(lot) <= deliveryAt);
      if (lots.reduce((sum, lot) => sum + lot.availableQuantity, 0) < difference) throw new Error("Art\u0131\u015F i\xE7in se\xE7ilen tarihte yeterli teslimata haz\u0131r miktar yok. Bekleyen \u015Farj\u0131 Teslimat\u0131 tamamla ile onaylay\u0131n.");
      let left = difference;
      for (const lot of lots) {
        const amount = Math.min(left, lot.availableQuantity);
        const history = next.seed.productionHistory.find((entry) => entry.id === lot.sourceHistoryEntryId && entry.inventoryStatus === "semi-finished");
        if (!history || history.completedQuantity < amount) throw new Error("A\xE7\u0131k ar\u015Fiv bakiyesi e\u015Fle\u015Fmiyor.");
        deliverWipQuantity(next.seed, lot.id, amount, deliveryAt, (/* @__PURE__ */ new Date()).toISOString());
        const existing = allocations.find((item) => item.lotId === lot.id);
        if (existing) existing.quantity += amount;
        else allocations.push({ lotId: lot.id, quantity: amount });
        history.completedQuantity -= amount;
        history.originalQuantity = history.completedQuantity;
        if (!history.completedQuantity) history.inventoryStatus = "voided";
        left -= amount;
        if (!left) break;
      }
    }
    if (allocations) {
      next.entry.wipAllocations = allocations.filter((item) => item.quantity > 0);
      next.entry.originalQuantity = quantity;
    }
    next.entry.deliveredAt = deliveryDate?.slice(0, 10) || source.deliveredAt;
    next.entry.deliveredAtTime = deliveryIso;
    next.entry.deliveredAtPrecision = deliveryValue.precision;
    next.entry.statusChangedAt = (/* @__PURE__ */ new Date()).toISOString();
    next.entry.statusChangeReason = `Teslimat d\xFCzeltmesi: ${source.completedQuantity} \u2192 ${quantity} adet; ${source.deliveredAtTime || source.deliveredAt} \u2192 ${deliveryValue.value}${dayOnly ? " \xB7 Saat bilinmiyor" : ""}`;
  } else {
    syncWipWithHistoryEdit(next.seed, source, quantity, actualAt, void 0, correctionLotId);
    const delta = quantity - source.completedQuantity;
    if (delta) {
      const ids = new Set(productionHistoryLots(next.seed, next.entry).filter((lot) => lot.availableQuantity > 0 && lot.availableQuantity !== seed.wipLots?.find((item) => item.id === lot.id)?.availableQuantity).map((lot) => lot.id));
      for (const job of next.seed.processCurrentJobs ?? []) if (ids.has(job.wipLotId)) updateProcessCurrentJob(next.seed, job.resourceId, { originalQuantity: job.originalQuantity + delta, remainingQuantity: job.remainingQuantity + delta, remainingAsOf: job.remainingAsOf ?? job.start });
    }
  }
  next.seed.lastAutomaticPlan = void 0;
  next.seed.planRunSequence = void 0;
  next.seed.planNeedsRecalculation = true;
  return next;
}

// lib/production-date-correction.ts
function correctProductionDates(seed, result, input, now, recordedAt) {
  const source = seed.wipLots?.find((lot2) => lot2.id === input.lotId);
  if (!source || source.stage !== "delivery-ready" || source.availableQuantity <= 0 || source.manualReceipt) throw Error("Tarih d\xFCzeltmesi i\xE7in tamamlanm\u0131\u015F a\xE7\u0131k \u015Farj\u0131 se\xE7in.");
  if (seed.processCurrentJobs?.some((job) => job.wipLotId === source.id)) throw Error("Se\xE7ili par\xE7ada \xE7al\u0131\u015Fan proses var; \xF6nce \xFCretim kayd\u0131n\u0131 inceleyin.");
  const history = seed.productionHistory?.find((entry) => entry.id === source.sourceHistoryEntryId);
  if (!history || history.inventoryStatus !== "semi-finished" || history.product !== source.product || history.workOrder !== source.workOrder || !input.expectedHistory || archiveEntrySignature(history) !== input.expectedHistory) throw Error("Ar\u015Fiv kayd\u0131 de\u011Fi\u015Fti. \u0130ncelemeyi yeniden a\xE7\u0131n.");
  const correction = input.correction;
  if (!correction || correction.confirmedOrder !== true) throw Error("Proses s\u0131ras\u0131n\u0131 ve teslim \xF6ncesi kontrol ile paketlemenin tamamland\u0131\u011F\u0131n\u0131 onaylay\u0131n.");
  if (typeof correction.reason !== "string" || !correction.reason.trim() || correction.reason.length > 2e3) throw Error("D\xFCzeltme nedeni zorunludur (en fazla 2000 karakter).");
  const product = processMasterDataForProduct(seed.processMasterData, source.product);
  const route = product ? effectiveProductRoute(product, source.completedSteps.find((step) => step.process === "turning")?.resourceId) : [];
  if (completedDeliveryRouteEnd(seed, source) === void 0 || !source.completedSteps.length) throw Error("Aktif rota tamamlanmam\u0131\u015F; eksik proses tarih d\xFCzeltmesiyle olu\u015Fturulamaz.");
  if (new Set(source.completedSteps.map((step) => step.process)).size !== source.completedSteps.length || route.length && route.some((process2, index) => source.completedSteps.findIndex((step) => step.process === process2) < 0 || index > 0 && source.completedSteps.findIndex((step) => step.process === route[index - 1]) >= source.completedSteps.findIndex((step) => step.process === process2))) throw Error("Kay\u0131tl\u0131 proses s\u0131ras\u0131 do\u011Frulanamad\u0131.");
  if (!Array.isArray(correction.steps) || correction.steps.length !== source.completedSteps.length) throw Error("B\xFCt\xFCn kay\u0131tl\u0131 proses tarihlerini inceleyin.");
  const steps = source.completedSteps.map((step, index) => {
    const proposed = correction.steps[index];
    if (!proposed || proposed.process !== step.process) throw Error("Proses kimli\u011Fi veya s\u0131ras\u0131 de\u011Fi\u015Ftirilemez.");
    const parsedStart = parseActualDate(proposed.start, now), parsedEnd = parseActualDate(proposed.end, now);
    const unchanged = (value, precision, proposed2) => JSON.stringify(actualDate(value, precision)) === JSON.stringify(proposed2);
    return {
      ...step,
      start: unchanged(step.start, step.startPrecision, proposed.start) ? step.start : parsedStart,
      end: unchanged(step.end, step.endPrecision, proposed.end) ? step.end : parsedEnd,
      startPrecision: proposed.start.precision,
      endPrecision: proposed.end.precision
    };
  });
  const deliveryAt = parseActualDate(correction.delivery, now);
  assertRecordedDateOrder([...steps.flatMap((step) => [{ value: step.start, precision: step.startPrecision }, { value: step.end, precision: step.endPrecision }]), { value: deliveryAt, precision: correction.delivery.precision }], true, now);
  const quantity = source.availableQuantity;
  if (!Number.isSafeInteger(quantity) || quantity <= 0 || history.completedQuantity < quantity || source.originalQuantity !== quantity + source.deliveredQuantity + source.scrappedQuantity) throw Error("Se\xE7ili par\xE7an\u0131n ar\u015Fiv bakiyesi e\u015Fle\u015Fmiyor.");
  validateFilterShipment(seed, source.product, quantity);
  const next = structuredClone(seed);
  let lot = next.wipLots.find((row) => row.id === source.id);
  if (lot.deliveredQuantity || lot.scrappedQuantity) {
    lot.originalQuantity -= quantity;
    lot.availableQuantity = 0;
    lot.stage = lot.deliveredQuantity ? "delivered" : "scrapped";
    lot = {
      ...structuredClone(source),
      id: `date-correction-${crypto.randomUUID()}`,
      parentLotId: source.id,
      originalQuantity: quantity,
      availableQuantity: quantity,
      deliveredQuantity: 0,
      scrappedQuantity: 0,
      createdAt: recordedAt
    };
    next.wipLots.push(lot);
  }
  const oldHistory = next.productionHistory.find((row) => row.id === history.id);
  const shipment = {
    ...structuredClone(history),
    id: `corrected-delivery-${crypto.randomUUID()}`,
    sourceEntryId: history.id,
    originalQuantity: quantity,
    completedQuantity: quantity,
    start: steps[0].start,
    completedAt: steps[0].end,
    completedAtPrecision: steps[0].endPrecision,
    inventoryStatus: "delivered",
    deliveredAt: correction.delivery.value.slice(0, 10),
    deliveredAtPrecision: correction.delivery.precision,
    deliveredAtTime: correction.delivery.precision === "minute" ? factoryDateTimeToIso(correction.delivery.value) : void 0,
    statusChangedAt: recordedAt,
    statusChangeReason: correction.reason.trim(),
    wipAllocations: [{ lotId: lot.id, quantity }]
  };
  oldHistory.completedQuantity -= quantity;
  if (!oldHistory.completedQuantity) oldHistory.inventoryStatus = "voided";
  next.productionHistory.push(shipment);
  lot.sourceHistoryEntryId = shipment.id;
  lot.completedSteps = steps;
  lot.processOrderConfirmed = true;
  lot.readyAt = deliveryAt;
  delete lot.rolledForwardAt;
  delete lot.rolledForwardFrom;
  lot.updatedAt = recordedAt;
  next.wipMovements = [...next.wipMovements ?? [], {
    id: crypto.randomUUID(),
    lotId: lot.id,
    kind: "dates-corrected",
    quantity,
    fromStage: source.stage,
    toStage: source.stage,
    occurredAt: deliveryAt,
    occurredAtPrecision: correction.delivery.precision,
    recordedAt,
    note: correction.reason.trim(),
    dateCorrection: {
      before: structuredClone(source.completedSteps),
      after: structuredClone(steps),
      previousReadyAt: source.readyAt,
      delivery: correction.delivery,
      confirmedOrder: true
    }
  }];
  deliverWipQuantity(next, lot.id, quantity, deliveryAt, recordedAt, correction.delivery.precision);
  next.planNeedsRecalculation = true;
  next.lastAutomaticPlan = void 0;
  next.planRunSequence = void 0;
  return { seed: next, result, entries: [shipment] };
}

// lib/wip-manual-actions.ts
function wipActionSignature(lot) {
  return JSON.stringify([lot.id, lot.updatedAt, lot.stage, lot.availableQuantity, lot.readyAt, lot.rolledForwardFrom, lot.completedSteps]);
}
function wipBufferQuestion(lot) {
  if (lot.stage === "process-buffer" && lot.family === "cubuk-filtre") return "D\u0131\u015F proses beklemesi tamamland\u0131 m\u0131?";
  if (lot.stage === "quality-hold") return "Proses kontrol tamamland\u0131 m\u0131?";
  if (lot.stage === "washing-buffer" || lot.stage === "gkm-buffer") return "Y\u0131kama ve proses kontrol tamamland\u0131 m\u0131?";
  if (lot.stage === "delivery-ready") return "Proses kontrol ve paketleme tamamland\u0131 m\u0131?";
}
function assertWipActionSnapshot(seed, input) {
  const lot = seed.wipLots?.find((item) => item.id === input.lotId);
  if (!lot || wipActionSignature(lot) !== input.expectedLot) throw new Error("\u015Earj de\u011Fi\u015Fti. G\xFCncel bilgileri yeniden a\xE7\u0131p onaylay\u0131n.");
  if (!input.confirmed) throw new Error("\u0130lgili kontrollerin tamamland\u0131\u011F\u0131n\u0131 onaylay\u0131n.");
  return lot;
}
function completeWipDelivery(seed, result, input, occurredAt, recordedAt = (/* @__PURE__ */ new Date()).toISOString()) {
  if (input.dateCorrection) {
    assertWipActionSnapshot(seed, input);
    return correctProductionDates(seed, result, { ...input, correction: input.dateCorrection }, occurredAt, recordedAt);
  }
  if (input.allocation) return allocateJourneyDelivery(seed, result, input, occurredAt, recordedAt);
  const lot = assertWipActionSnapshot(seed, input);
  if (lot.stage !== "delivery-ready" || lot.availableQuantity <= 0) throw new Error(seed.productionArea === "cubuk-filtre" ? "\u015Earj teslimata haz\u0131r a\u015Famas\u0131nda de\u011Fil." : "\u015Earj Paketleme & Final Kontrol a\u015Famas\u0131nda de\u011Fil.");
  const completedAt = completedDeliveryRouteEnd(seed, lot);
  if (completedAt === void 0 || !Number.isFinite(occurredAt) || occurredAt < completedAt) throw new Error(seed.productionArea === "cubuk-filtre" ? "Teslimat i\xE7in \xFCr\xFCn\xFCn aktif \xFCretim rotas\u0131 tamamlanm\u0131\u015F olmal\u0131d\u0131r." : "Teslimat i\xE7in aktif \xFCretim rotas\u0131 (GKM aktifse GKM dahil) ger\xE7ekten tamamlanm\u0131\u015F olmal\u0131d\u0131r.");
  if (!Number.isInteger(input.quantity) || input.quantity <= 0 || input.quantity > lot.availableQuantity) throw new Error("Teslim adedi kalan miktar\u0131 a\u015Fmayan pozitif tam say\u0131 olmal\u0131d\u0131r.");
  const history = seed.productionHistory?.find((entry) => entry.id === lot.sourceHistoryEntryId && entry.inventoryStatus === "semi-finished" && entry.product.toUpperCase() === lot.product.toUpperCase());
  if (!history) throw new Error("\u015Earj\u0131n a\xE7\u0131k \xFCretim ar\u015Fivi kayd\u0131 bulunamad\u0131. Ar\u015Fiv e\u015Fle\u015Fmesini kontrol edin.");
  const next = allocateProductionHistoryEntry(seed, result, history.id, {
    actualQuantity: history.completedQuantity,
    completedAt: history.completedAt,
    deliveredQuantity: input.quantity,
    deliveryDate: factoryDateInput(recordedAt),
    remainderAction: "keep"
  }, recordedAt, (nextSeed, entries) => {
    if (occurredAt < wipOperationReadyAt(lot)) releaseWipBuffer(nextSeed, lot.id, occurredAt, true, recordedAt);
    deliverWipQuantity(nextSeed, lot.id, input.quantity, occurredAt, recordedAt);
    entries.find((entry) => entry.inventoryStatus === "delivered").wipAllocations = [{ lotId: lot.id, quantity: input.quantity }];
    const remaining = nextSeed.wipLots.find((item) => item.id === lot.id);
    if (remaining.availableQuantity > 0 && occurredAt < wipOperationReadyAt(lot)) {
      remaining.readyAt = lot.readyAt;
      remaining.rolledForwardFrom = lot.rolledForwardFrom;
      remaining.rolledForwardAt = lot.rolledForwardAt;
      const release = nextSeed.wipMovements?.findLast((movement) => movement.lotId === lot.id && movement.kind === "buffer-released");
      if (release) release.quantity = input.quantity;
    }
  });
  next.seed.lastAutomaticPlan = void 0;
  next.seed.planRunSequence = void 0;
  return next;
}
function allocateJourneyDelivery(seed, result, input, now, recordedAt) {
  const lot = assertWipActionSnapshot(seed, input);
  const allocation = input.allocation;
  if (lot.stage !== "delivery-ready" || lot.availableQuantity <= 0) throw new Error(seed.productionArea === "cubuk-filtre" ? "\u015Earj teslimata haz\u0131r a\u015Famas\u0131nda de\u011Fil." : "\u015Earj Paketleme & Final Kontrol a\u015Famas\u0131nda de\u011Fil.");
  const completedAt = completedDeliveryRouteEnd(seed, lot);
  if (completedAt === void 0 || completedAt > now) throw new Error(seed.productionArea === "cubuk-filtre" ? "Teslimat i\xE7in \xFCr\xFCn\xFCn aktif \xFCretim rotas\u0131 tamamlanm\u0131\u015F olmal\u0131d\u0131r." : "Teslimat i\xE7in aktif \xFCretim rotas\u0131 (GKM aktifse GKM dahil) ger\xE7ekten tamamlanm\u0131\u015F olmal\u0131d\u0131r.");
  if (!input.expectedHistory) throw new Error("\xDCretim ar\u015Fivi e\u015Fle\u015Fmesini yeniden a\xE7\u0131p kontrol edin.");
  const history = assertArchiveEntry(seed, lot.sourceHistoryEntryId, input.expectedHistory);
  if (history.inventoryStatus !== "semi-finished" || history.product !== lot.product || history.workOrder !== lot.workOrder) throw new Error("\u015Earj\u0131n a\xE7\u0131k \xFCretim ar\u015Fivi kayd\u0131 e\u015Fle\u015Fmiyor.");
  if (!Number.isInteger(allocation.actualQuantity) || allocation.actualQuantity <= 0 || !Number.isInteger(allocation.deliveredQuantity) || allocation.deliveredQuantity < 0 || allocation.deliveredQuantity > allocation.actualQuantity || !["keep", "scrap"].includes(allocation.remainderAction)) throw new Error("Fiili ve teslim edilen adetleri kontrol edin.");
  let deliveredAt = now;
  if (allocation.deliveredQuantity > 0) {
    const value = allocation.deliveryDate;
    deliveredAt = (Date.parse(`${value}:00Z`) - Date.UTC(1899, 11, 30)) / 864e5;
    if (!/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}$/.test(value) || !Number.isFinite(deliveredAt) || processCompletionTimeInput(deliveredAt) !== value) throw new Error("Ge\xE7erli bir teslim tarihi ve saati se\xE7in.");
    if (deliveredAt > now + 1e-8) throw new Error("Teslim tarihi ve saati \u015Fu andan sonra olamaz.");
    if (deliveredAt < Math.max(history.completedAt, ...lot.completedSteps.map((step) => step.end)) - 1e-8) throw new Error("Teslim tarihi ve saati tamamlanan proseslerden \xF6nce olamaz.");
  }
  const total = history.completedQuantity + allocation.actualQuantity - lot.availableQuantity;
  if (total < allocation.actualQuantity) throw new Error("\u015Earj miktar\u0131 a\xE7\u0131k ar\u015Fiv bakiyesiyle e\u015Fle\u015Fmiyor.");
  const corrected = correctArchiveRecord(seed, result, history.id, total, allocation.completedAt, void 0, input.expectedHistory, lot.id);
  if (allocation.deliveredQuantity === 0 && allocation.remainderAction === "keep") return { ...corrected, entries: [corrected.entry] };
  const selected = corrected.seed.wipLots.find((item) => item.id === lot.id);
  let scopedHistory = corrected.entry;
  if (total > allocation.actualQuantity) {
    scopedHistory = {
      ...corrected.entry,
      id: `journey-${crypto.randomUUID()}`,
      sourceEntryId: corrected.entry.id,
      originalQuantity: allocation.actualQuantity,
      completedQuantity: allocation.actualQuantity
    };
    corrected.entry.completedQuantity = total - allocation.actualQuantity;
    corrected.entry.originalQuantity = corrected.entry.completedQuantity;
    corrected.seed.productionHistory.push(scopedHistory);
    selected.sourceHistoryEntryId = scopedHistory.id;
  }
  const next = allocateProductionHistoryEntry(
    corrected.seed,
    corrected.result,
    scopedHistory.id,
    { ...allocation, completedAt: scopedHistory.completedAt },
    recordedAt,
    (nextSeed, entries) => {
      const early = allocation.deliveredQuantity > 0 && deliveredAt < wipOperationReadyAt(lot);
      if (early) releaseWipBuffer(nextSeed, lot.id, deliveredAt, true, recordedAt);
      if (allocation.deliveredQuantity > 0) {
        deliverWipQuantity(nextSeed, lot.id, allocation.deliveredQuantity, deliveredAt, recordedAt);
        entries.find((entry) => entry.inventoryStatus === "delivered").wipAllocations = [{ lotId: lot.id, quantity: allocation.deliveredQuantity }];
      }
      const remainder = allocation.actualQuantity - allocation.deliveredQuantity;
      if (remainder > 0 && allocation.remainderAction === "scrap") scrapWipQuantity(nextSeed, lot.id, remainder, now, recordedAt);
      const remaining = nextSeed.wipLots.find((item) => item.id === lot.id);
      if (early) {
        if (remaining.availableQuantity > 0) {
          remaining.readyAt = lot.readyAt;
          remaining.rolledForwardFrom = lot.rolledForwardFrom;
          remaining.rolledForwardAt = lot.rolledForwardAt;
        }
        const release = nextSeed.wipMovements?.findLast((movement) => movement.lotId === lot.id && movement.kind === "buffer-released");
        if (release) release.quantity = allocation.deliveredQuantity;
      }
    }
  );
  next.seed.lastAutomaticPlan = void 0;
  next.seed.planRunSequence = void 0;
  return next;
}

// lib/charge-journey-notes.ts
var CHARGE_JOURNEY_REASONS = [
  { value: "machine-breakdown", label: "Makine ar\u0131zas\u0131" },
  { value: "tooling", label: "Tak\u0131m problemi" },
  { value: "raw-material", label: "Hammadde gecikmesi" },
  { value: "quality", label: "Kalite problemi" },
  { value: "staffing", label: "Personel eksikli\u011Fi" },
  { value: "setup-overrun", label: "Setup uzamas\u0131" },
  { value: "cycle-time", label: "\xC7evrim s\xFCresi sapmas\u0131" },
  { value: "previous-operation", label: "\xD6nceki operasyon gecikmesi" },
  { value: "external-process", label: "D\u0131\u015F proses gecikmesi" },
  { value: "unplanned-priority", label: "Plans\u0131z \xF6ncelikli i\u015F" },
  { value: "other", label: "Di\u011Fer" }
];
function chargeJourneyReasonLabel(reason) {
  return CHARGE_JOURNEY_REASONS.find((item) => item.value === reason)?.label ?? "Di\u011Fer";
}
function noteId(input) {
  const safeCharge = input.chargeKey.trim().replace(/[^a-zA-Z0-9_-]+/g, "-");
  const safeSegment = input.segmentId.trim().replace(/[^a-zA-Z0-9_-]+/g, "-");
  return `journey-note-${safeCharge}-${safeSegment}`;
}
function saveChargeJourneyNote(seed, input, updatedAt = (/* @__PURE__ */ new Date()).toISOString()) {
  const chargeKey = input.chargeKey.trim();
  const segmentId = input.segmentId.trim();
  if (!chargeKey || !segmentId) throw new Error("A\xE7\u0131klaman\u0131n ba\u011Fl\u0131 oldu\u011Fu \u015Farj veya zaman aral\u0131\u011F\u0131 bulunamad\u0131.");
  if (!Number.isFinite(input.start) || !Number.isFinite(input.end) || input.end < input.start) throw new Error("A\xE7\u0131klama tarih aral\u0131\u011F\u0131 ge\xE7ersiz.");
  const notes = seed.chargeJourneyNotes ?? [];
  const retained = notes.filter((note2) => !(note2.chargeKey === chargeKey && note2.segmentId === segmentId));
  const listed = input.reason && input.reason !== "other" ? input.reason : void 0;
  const note = listed ? chargeJourneyReasonLabel(listed) : input.note.trim();
  if (!note) {
    if (input.reason === "other") throw new Error("Di\u011Fer se\xE7ildi\u011Finde a\xE7\u0131klama yaz\u0131lmal\u0131d\u0131r.");
    seed.chargeJourneyNotes = retained;
    return void 0;
  }
  const saved = {
    ...input,
    id: notes.find((item) => item.chargeKey === chargeKey && item.segmentId === segmentId)?.id ?? noteId({ chargeKey, segmentId }),
    chargeKey,
    segmentId,
    reason: listed ?? (input.reason ? "other" : void 0),
    note,
    updatedAt
  };
  if (!saved.reason) delete saved.reason;
  seed.chargeJourneyNotes = [...retained, saved];
  return saved;
}

// features/planning/session/production-actions.ts
var cloneSeed2 = (seed) => structuredClone(seed);
function createProductionActions({ seed, result, commitOperationalChange: commit, setOperationAlert, setDirty, dirty = false, submitCommand }) {
  const commitOperationalChange = (nextSeed, nextResult, message, event, undoMessage) => {
    if (nextSeed.productionArea === "cubuk-filtre" && event && ["current-job", "complete", "wip"].includes(event.type)) {
      const transfer = consolidateFilterSharedRemainders(nextSeed, nextResult, factoryNowSerial());
      nextSeed = transfer.seed;
      nextResult = transfer.result;
      if (transfer.transfers.length) message += `; kalan ortak \u015Farj tek tezgahta topland\u0131`;
    }
    nextSeed.planNeedsRecalculation = Boolean(nextSeed.planNeedsRecalculation || dirty || event?.type === "archive-status");
    commit(nextSeed, nextResult, message, event, undoMessage);
  };
  function setMachineQueueLock(machineId, throughBatchId) {
    if (typeof machineId !== "string" || !seed.machines.some((machine) => machine.id === machineId) || throughBatchId !== null && (typeof throughBatchId !== "string" || !throughBatchId)) throw new Error("Tezgah veya kilitlenecek \u015Farj ge\xE7ersiz.");
    const next = throughBatchId === null ? unlockMachineQueue(result, machineId) : lockQueueThrough(result, machineId, throughBatchId);
    const message = throughBatchId === null ? `${machineId} ortak kuyruk kilidi kald\u0131r\u0131ld\u0131` : `${machineId} ortak kuyruk kilidi kaydedildi`;
    commitOperationalChange(cloneSeed2(seed), next, message, { type: throughBatchId === null ? "unlock" : "lock", machineId, message });
  }
  function setAllMachineQueueLocks2(locked) {
    const next = setAllMachineQueueLocks(result, locked);
    const message = locked ? "T\xFCm tezgah kuyruklar\u0131 kilitlendi" : "T\xFCm tezgah kuyruklar\u0131n\u0131n kilitleri kald\u0131r\u0131ld\u0131";
    commitOperationalChange(cloneSeed2(seed), next, message, { type: locked ? "lock" : "unlock", message });
  }
  function saveMachineAvailability(machineId, start) {
    try {
      const next = cloneSeed2(seed);
      setMachineAvailability(next, machineId, start);
      commitOperationalChange(next, result, `${machineId} m\xFCsait ba\u015Flang\u0131c\u0131 kaydedildi \xB7 plan\u0131 yeniden \xE7al\u0131\u015Ft\u0131r\u0131n`, void 0, "M\xFCsait ba\u015Flang\u0131\xE7 de\u011Fi\u015Fikli\u011Fi geri al\u0131nabilir");
    } catch (error) {
      setOperationAlert({ id: Date.now(), message: error instanceof Error ? error.message : "M\xFCsait ba\u015Flang\u0131\xE7 kaydedilemedi." });
    }
  }
  function rescheduleDownstreamOperation(operationId, resourceId, requestedStart, reviewedSignature) {
    const preview = previewProcessOperationReschedule(seed, result, operationId, resourceId, requestedStart);
    if (processPlacementSignature(preview) !== reviewedSignature) throw new Error("Plan de\u011Fi\u015Fti. G\xFCncel yerle\u015Fimi yeniden inceleyip onaylay\u0131n.");
    const moved = preview.operation;
    commitOperationalChange(
      preview.seed,
      result,
      `${processLabel(moved.process)} \xB7 ${moved.product} \xB7 ${resourceId} yerle\u015Fimi uyguland\u0131`,
      { type: "wip", machineId: resourceId, message: `${moved.workOrder || moved.product} \xB7 ${processLabel(moved.process)} Gantt yerle\u015Fimi g\xFCncellendi.` },
      "Proses ta\u015F\u0131mas\u0131 geri al\u0131nabilir"
    );
    if (dirty) setDirty(true);
    return moved;
  }
  function placeDownstreamQueueOperation(request, reviewedSignature) {
    const preview = previewProcessQueuePlacement(seed, result, request);
    if (processPlacementSignature(preview) !== reviewedSignature) throw new Error("Kuyruk veya plan de\u011Fi\u015Fti. G\xFCncel yerle\u015Fimi yeniden inceleyip onaylay\u0131n.");
    if (preview.seed === seed) return preview.operation;
    const moved = preview.operation;
    commitOperationalChange(
      preview.seed,
      result,
      `${processLabel(moved.process)} \xB7 ${moved.workOrder || moved.product} \xB7 ${moved.resourceId} kuyru\u011Fu g\xFCncellendi`,
      { type: "wip", machineId: moved.resourceId, message: `${moved.workOrder || moved.product} \xB7 ${processLabel(moved.process)} ${preview.insertionIndex + 1}. s\u0131raya yerle\u015Ftirildi.` },
      "Proses kuyruk de\u011Fi\u015Fikli\u011Fi geri al\u0131nabilir"
    );
    if (dirty) setDirty(true);
    return moved;
  }
  function replanDownstreamProcess(process2) {
    try {
      const next = resetDownstreamProcessPlan(seed, result, process2);
      commitOperationalChange(
        next.seed,
        result,
        `${processLabel(process2)} otomatik plan\u0131 g\xFCncellendi \xB7 Torna plan\u0131 korundu`,
        { type: "wip", message: `${processLabel(process2)} kuyruklar\u0131 otomatik planland\u0131; \xE7al\u0131\u015Fan i\u015Fler ve Torna plan\u0131 korundu.` },
        `${processLabel(process2)} planlamas\u0131 geri al\u0131nabilir`
      );
      if (dirty) setDirty(true);
      return true;
    } catch (error) {
      setOperationAlert({ id: Date.now(), message: error instanceof Error ? error.message : "Proses planlanamad\u0131." });
      return false;
    }
  }
  function saveCurrentJob(machineId, input, remainingAsOf) {
    try {
      const next = updateMachineCurrentJob(seed, result, machineId, input, remainingAsOf);
      next.seed.lastAutomaticPlan = void 0;
      commitOperationalChange(next.seed, next.result, `${machineId} mevcut i\u015Fi g\xFCncellendi`, { type: "current-job", machineId, message: `${machineId} mevcut i\u015Fi ${input.product} olarak g\xFCncellendi.` });
    } catch (error) {
      throw error instanceof Error ? error : new Error("Mevcut i\u015F g\xFCncellenemedi.");
    }
  }
  function replaceTurningJob(machineId, batchId, input) {
    const next = replaceTurningCurrentJob(seed, result, machineId, batchId, input, factoryNowSerial());
    const label2 = input.produced ? input.kind === "partial-completion" ? "K\u0131smi \xFCretim tamamland\u0131." : "\xDCretime ara verildi." : "\u0130\u015F kuyru\u011Fa d\xF6nd\xFC.";
    commitOperationalChange(next.seed, next.result, `Mevcut i\u015F de\u011Fi\u015Ftirildi \xB7 ${label2}`, { type: "current-job", machineId, message: `${label2} ${input.produced ? `${input.quantity} adet \xFCretildi. ${input.reason?.trim()}` : "\xDCretim yap\u0131lmad\u0131."}` }, "Mevcut i\u015F de\u011Fi\u015Fikli\u011Fi geri al\u0131nabilir");
    setDirty(true);
  }
  function recordOutsidePlanProduction2(input) {
    const next = recordOutsidePlanProduction(seed, result, input, factoryNowSerial());
    const label2 = `${next.batch.workOrder || next.batch.product} \xB7 ${formatInteger(input.quantity)} adet plan d\u0131\u015F\u0131 \xFCretim kaydedildi`;
    commitOperationalChange(next.seed, next.result, `${label2} \xB7 plan\u0131 yeniden \xE7al\u0131\u015Ft\u0131r\u0131n`, { type: "current-job", machineId: next.batch.machineId, message: `${label2}. ${input.reason.trim()}` }, "Plan d\u0131\u015F\u0131 \xFCretim kayd\u0131 geri al\u0131nabilir");
    setDirty(true);
  }
  function completeCurrentJob(machineId, completedAt, completedQuantity, remainderAction) {
    const current = seed.machines.find((machine) => machine.id === machineId)?.currentJob;
    if (!current) throw new Error("Tezgah bulunamad\u0131.");
    const assigned = current.originalQuantity ?? current.quantity;
    const action = requireTurningRemainderAction(assigned, completedQuantity ?? assigned, remainderAction);
    const next = completeMachineCurrentJob(seed, result, machineId, completedAt, completedQuantity, action);
    const lot = registerTurningCompletion(next.seed, next.archived);
    if (next.archived.interruptionIds?.length && !lot) throw new Error("K\u0131smi \xFCretimin yar\u0131 mam\xFCl kayd\u0131 olu\u015Fturulamad\u0131; \xFCr\xFCn rotas\u0131n\u0131 kontrol edin.");
    if (next.scrapped) {
      const scrapLot = registerTurningCompletion(next.seed, { ...next.scrapped, inventoryStatus: "semi-finished" });
      if (!lot || !scrapLot) throw new Error("Torna \u0131skarta kayd\u0131 olu\u015Fturulamad\u0131; \xFCr\xFCn rotas\u0131n\u0131 kontrol edin.");
      scrapWipQuantity(next.seed, scrapLot.id, next.scrapped.completedQuantity, completedAt, next.scrapped.archivedAt);
    }
    next.seed.lastAutomaticPlan = void 0;
    const promotion = next.promotedBatch ? `; ${next.promotedBatch.product} \xFCretime al\u0131nd\u0131` : "; s\u0131rada yeni i\u015F yok";
    const loss = next.scrapped ? `; ${next.scrapped.completedQuantity} adet \u0131skartaya ayr\u0131ld\u0131` : "";
    commitOperationalChange(next.seed, next.result, `${next.archived.product} tamamland\u0131${loss}${promotion}`, { type: "complete", machineId, message: `${next.archived.workOrder || next.archived.product} tamamland\u0131 ve ar\u015Five al\u0131nd\u0131${loss}${promotion}.` });
  }
  function changeProductionHistoryStatus(entryId, inventoryStatus, actionDate = "", reason = "") {
    const source = (seed.productionHistory ?? []).find((entry) => entry.id === entryId);
    if (!source) {
      throw new Error("\xDCretim ar\u015Fivi kayd\u0131 bulunamad\u0131.");
    }
    try {
      const changedAt = (/* @__PURE__ */ new Date()).toISOString();
      const next = updateProductionHistoryStatus(seed, result, entryId, inventoryStatus, actionDate, changedAt, reason);
      const occurredAt = actionDate ? inputDateToSerial(actionDate.slice(0, 10)) : source.completedAt;
      applyHistoryStatusToWip(next.seed, source, inventoryStatus, occurredAt, changedAt, reason);
      next.seed.lastAutomaticPlan = void 0;
      next.seed.planRunSequence = void 0;
      const action = inventoryStatus === "delivered" ? `${source.product} teslim edildi` : inventoryStatus === "semi-finished" ? `${source.product} yar\u0131 mamule geri al\u0131nd\u0131${reason.trim() ? ` \xB7 ${reason.trim()}` : ""}` : inventoryStatus === "scrapped" ? `${source.product} \u0131skartaya ayr\u0131ld\u0131` : `${source.product} ar\u015Fiv kayd\u0131 iptal edildi`;
      commitOperationalChange(
        next.seed,
        next.result,
        `${action} \xB7 plan\u0131 yeniden \xE7al\u0131\u015Ft\u0131r\u0131n`,
        { type: "archive-status", machineId: source.machineId, message: `${action}.` },
        "Ar\u015Fiv durum de\u011Fi\u015Fikli\u011Fi geri al\u0131nabilir"
      );
      setDirty(true);
    } catch (error) {
      throw error instanceof Error ? error : new Error("Ar\u015Fiv durumu g\xFCncellenemedi.");
    }
  }
  function restoreProductionDelivery(entryId, reason, expected) {
    const next = restoreArchiveDelivery(seed, result, entryId, reason, expected);
    commitOperationalChange(next.seed, next.result, "Teslimat geri al\u0131nd\u0131 \xB7 Paketleme / Final Kontrol\u2019e d\xF6nd\xFC \xB7 plan\u0131 yeniden \xE7al\u0131\u015Ft\u0131r\u0131n", { type: "archive-status", message: `Teslimat geri al\u0131nd\u0131: ${reason.trim()}` }, "Teslimat\u0131 geri alma i\u015Flemi geri al\u0131nabilir");
    setDirty(true);
    return true;
  }
  function editProductionHistoryEntry(entryId, actualQuantity, completedAt, deliveryDate, expected, correctionLotId) {
    const source = assertArchiveEntry(seed, entryId, expected);
    const next = correctArchiveRecord(seed, result, entryId, actualQuantity, completedAt, deliveryDate, expected, correctionLotId);
    commitOperationalChange(next.seed, next.result, `${source.product} ar\u015Fiv kayd\u0131 g\xFCncellendi \xB7 plan\u0131 yeniden \xE7al\u0131\u015Ft\u0131r\u0131n`, { type: "archive-status", machineId: source.machineId, message: `${source.product} \xB7 ${formatInteger(actualQuantity)} adet \xB7 ${next.entry.statusChangeReason || "Fiili \xFCretim d\xFCzeltildi"}.` }, "Ar\u015Fiv d\xFCzenlemesi geri al\u0131nabilir");
    setDirty(true);
    return true;
  }
  function allocateProductionHistory(entryId, input, expected, correctionLotId) {
    const source = assertArchiveEntry(seed, entryId, expected);
    const corrected = correctArchiveRecord(seed, result, entryId, input.actualQuantity, input.completedAt, void 0, expected, correctionLotId);
    if (input.deliveredQuantity === 0 && input.remainderAction === "keep") return editProductionHistoryEntry(entryId, input.actualQuantity, input.completedAt, void 0, expected, correctionLotId);
    const actualInput = { ...input, completedAt: corrected.entry.completedAt };
    const next = allocateProductionHistoryEntry(corrected.seed, corrected.result, entryId, actualInput, void 0, (nextSeed, entries) => {
      applyHistoryAllocationToWip(nextSeed, corrected.entry, actualInput, void 0, entries.find((entry) => entry.inventoryStatus === "delivered")?.id);
    });
    next.seed.lastAutomaticPlan = void 0;
    next.seed.planRunSequence = void 0;
    const remainder = input.actualQuantity - input.deliveredQuantity;
    const detail = remainder > 0 ? `; ${formatInteger(remainder)} adet ${input.remainderAction === "scrap" ? "\u0131skartaya ayr\u0131ld\u0131" : "yar\u0131 mamulde kald\u0131"}` : "";
    commitOperationalChange(next.seed, next.result, `${source.product} teslimat\u0131 kaydedildi \xB7 plan\u0131 yeniden \xE7al\u0131\u015Ft\u0131r\u0131n`, { type: "archive-status", machineId: source.machineId, message: `${formatInteger(input.deliveredQuantity)} adet teslim edildi${detail}.` }, "Teslimat ayr\u0131\u015Ft\u0131rmas\u0131 geri al\u0131nabilir");
    setDirty(true);
    return true;
  }
  function commitJourneyDelivery(input) {
    const now = (/* @__PURE__ */ new Date()).toISOString();
    const next = completeWipDelivery(seed, result, input, factoryNowSerial(), now);
    commitOperationalChange(
      next.seed,
      next.result,
      "Teslimat kaydedildi \xB7 plan\u0131 yeniden \xE7al\u0131\u015Ft\u0131r\u0131n",
      { type: "archive-status", message: input.dateCorrection ? `${input.quantity} adet i\xE7in \xFCretim tarihleri d\xFCzeltildi ve teslimat kaydedildi. ${input.dateCorrection.reason}` : input.allocation ? `${input.allocation.deliveredQuantity} adet teslim edildi; ${input.allocation.actualQuantity - input.allocation.deliveredQuantity} adet ${input.allocation.remainderAction === "scrap" ? "\u0131skartaya ayr\u0131ld\u0131" : "yar\u0131 mamulde kald\u0131"}.` : `${input.quantity} adet teslim edildi; proses kontrol ve paketleme onayland\u0131.` },
      "Teslimat geri al\u0131nabilir"
    );
    setDirty(true);
  }
  function deliverJourneyWip(input) {
    if (input.dateCorrection) throw Error("Tarih d\xFCzeltmesi i\xE7in yeni d\xFCzeltme komutunu kullan\u0131n.");
    commitJourneyDelivery(input);
  }
  function correctJourneyDates(input) {
    if (!input.dateCorrection) throw Error("Tarih d\xFCzeltme incelemesi zorunludur.");
    commitJourneyDelivery(input);
  }
  function releaseJourneyBuffer(input) {
    const selected = assertWipActionSnapshot(seed, input);
    if (!wipBufferQuestion(selected)) throw new Error("\u015Earj bu i\u015Flem i\xE7in beklemede de\u011Fil.");
    const nextSeed = cloneSeed2(seed);
    const lot = releaseWipBuffer(nextSeed, input.lotId, factoryNowSerial(), input.confirmed);
    commitOperationalChange(
      nextSeed,
      result,
      `${lot.workOrder || lot.product} beklemesi tamamland\u0131`,
      { type: "wip", message: `${lot.workOrder || lot.product} i\xE7in kontrol onay\u0131yla bekleme tamamland\u0131.` },
      "Bekleme onay\u0131 geri al\u0131nabilir"
    );
    if (dirty) setDirty(true);
  }
  function finishWipOperation(input) {
    try {
      const nextSeed = cloneSeed2(seed);
      const current = (nextSeed.processCurrentJobs ?? []).find((job) => job.wipLotId === input.lotId && job.process === input.process);
      const completed = current ? (() => {
        completeProcessCurrentJob(nextSeed, result, current.resourceId, input.completedAt, input.quantity, input.resourceId, input.remainderAction, input.confirmedBuffer, input.countCorrectionReason);
        return (nextSeed.wipLots ?? []).find((lot) => lot.id === input.lotId) ?? (nextSeed.wipLots ?? []).find((lot) => lot.parentLotId === input.lotId);
      })() : completeWipOperation(nextSeed, input).completed;
      if (input.remainderAction === "scrap") nextSeed.planNeedsRecalculation = true;
      commitOperationalChange(
        nextSeed,
        result,
        `${completed.workOrder || completed.product} \xB7 ${input.process} tamamland\u0131`,
        { type: "wip", machineId: input.resourceId, message: `${completed.workOrder || completed.product} i\xE7in ${formatInteger(input.quantity)} adet ${input.process} tamamland\u0131.` },
        "Yar\u0131 mam\xFCl operasyonu geri al\u0131nabilir"
      );
      return true;
    } catch (error) {
      setOperationAlert({ id: Date.now(), message: error instanceof Error ? error.message : "Yar\u0131 mam\xFCl operasyonu tamamlanamad\u0131." });
      return false;
    }
  }
  function beginDownstreamCurrentJob(operationId, confirmedInterruption = false) {
    try {
      const nextSeed = cloneSeed2(seed);
      const current = startProcessCurrentJob(nextSeed, result, operationId, factoryNowSerial(), confirmedInterruption);
      commitOperationalChange(
        nextSeed,
        result,
        `${current.resourceId} \xB7 ${current.product} mevcut \xFCretime al\u0131nd\u0131`,
        { type: "wip", machineId: current.resourceId, message: `${current.workOrder || current.product}, ${current.resourceId} \xFCzerinde mevcut \xFCretime al\u0131nd\u0131.` },
        "Mevcut i\u015Fe alma i\u015Flemi geri al\u0131nabilir"
      );
    } catch (error) {
      throw error instanceof Error ? error : new Error("Downstream i\u015Fi mevcut \xFCretime al\u0131namad\u0131.");
    }
  }
  function replaceDownstreamCurrentJob(resourceId, operationId, input, confirmedInterruption = false) {
    try {
      const nextSeed = structuredClone(seed);
      const outcome = replaceProcessCurrentJob(nextSeed, result, resourceId, operationId, factoryNowSerial(), input, confirmedInterruption);
      nextSeed.planNeedsRecalculation = true;
      commitOperationalChange(
        nextSeed,
        result,
        `${resourceId} mevcut i\u015Fi ${outcome.current.workOrder || outcome.current.product} olarak de\u011Fi\u015Ftirildi`,
        { type: "wip", machineId: resourceId, message: `${outcome.current.workOrder || outcome.current.product} mevcut \xFCretime al\u0131nd\u0131; ${outcome.queued.workOrder || outcome.queued.product} kuyru\u011Fun ilk s\u0131ras\u0131na ta\u015F\u0131nd\u0131.` },
        "Mevcut i\u015F de\u011Fi\u015Fikli\u011Fi geri al\u0131nabilir"
      );
    } catch (error) {
      throw error instanceof Error ? error : new Error("Downstream mevcut i\u015Fi de\u011Fi\u015Ftirilemedi.");
    }
  }
  function saveDownstreamCurrentJob(resourceId, input) {
    try {
      const nextSeed = cloneSeed2(seed);
      const current = updateProcessCurrentJob(nextSeed, resourceId, input);
      commitOperationalChange(
        nextSeed,
        result,
        `${resourceId} mevcut i\u015Fi g\xFCncellendi`,
        { type: "wip", machineId: resourceId, message: `${current.workOrder || current.product}, ${resourceId} \xFCzerinde g\xFCncellendi.` },
        "Mevcut i\u015F d\xFCzenlemesi geri al\u0131nabilir"
      );
    } catch (error) {
      throw error instanceof Error ? error : new Error("Downstream mevcut i\u015Fi g\xFCncellenemedi.");
    }
  }
  function finishDownstreamCurrentJob(resourceId, completedAt, completedQuantity, actualResourceId, remainderAction, confirmedBuffer = false, countCorrectionReason) {
    try {
      const nextSeed = cloneSeed2(seed);
      const outcome = completeProcessCurrentJob(nextSeed, result, resourceId, completedAt, completedQuantity, actualResourceId, remainderAction, confirmedBuffer, countCorrectionReason);
      if (remainderAction === "scrap") nextSeed.planNeedsRecalculation = true;
      const promotion = outcome.promoted ? `; ${outcome.promoted.product} mevcut \xFCretime al\u0131nd\u0131` : "; s\u0131rada haz\u0131r yar\u0131 mam\xFCl yok";
      commitOperationalChange(
        nextSeed,
        result,
        `${resourceId} \xB7 ${outcome.completedProduct} tamamland\u0131${promotion}`,
        { type: "wip", machineId: outcome.completedResourceId, message: `${outcome.completedWorkOrder || outcome.completedProduct}, ${outcome.completedResourceId} \xFCzerinde tamamland\u0131${promotion}.` },
        "Downstream tamamlama i\u015Flemi geri al\u0131nabilir"
      );
    } catch (error) {
      throw error instanceof Error ? error : new Error("Downstream mevcut i\u015Fi tamamlanamad\u0131.");
    }
  }
  function changeWipStage(lotId2, stage, occurredAt) {
    try {
      const nextSeed = cloneSeed2(seed);
      const lot = stage === "on-hold" ? correctWipStage(nextSeed, lotId2, stage, occurredAt) : correctWipStage(nextSeed, lotId2, stage, occurredAt);
      commitOperationalChange(nextSeed, result, `${lot.workOrder || lot.product} yar\u0131 mam\xFCl konumu g\xFCncellendi`, { type: "wip", message: `${lot.workOrder || lot.product} konumu ${stage} olarak g\xFCncellendi.` }, "Yar\u0131 mam\xFCl konum de\u011Fi\u015Fikli\u011Fi geri al\u0131nabilir");
    } catch (error) {
      setOperationAlert({ id: Date.now(), message: error instanceof Error ? error.message : "Yar\u0131 mam\xFCl konumu g\xFCncellenemedi." });
    }
  }
  function releaseHeldWip(lotId2, occurredAt) {
    try {
      const nextSeed = cloneSeed2(seed);
      const lot = releaseWipHold(nextSeed, lotId2, occurredAt);
      commitOperationalChange(nextSeed, result, `${lot.workOrder || lot.product} blokesi kald\u0131r\u0131ld\u0131`, { type: "wip", message: `${lot.workOrder || lot.product} yar\u0131 mam\xFCl blokesi kald\u0131r\u0131ld\u0131.` }, "Bloke kald\u0131rma i\u015Flemi geri al\u0131nabilir");
    } catch (error) {
      setOperationAlert({ id: Date.now(), message: error instanceof Error ? error.message : "Yar\u0131 mam\xFCl blokesi kald\u0131r\u0131lamad\u0131." });
    }
  }
  function saveJourneyNote(input) {
    try {
      const nextSeed = cloneSeed2(seed);
      const saved = saveChargeJourneyNote(nextSeed, input);
      commitOperationalChange(
        nextSeed,
        result,
        saved ? "\u015Earj yolculu\u011Fu a\xE7\u0131klamas\u0131 kaydedildi" : "\u015Earj yolculu\u011Fu a\xE7\u0131klamas\u0131 kald\u0131r\u0131ld\u0131",
        { type: "wip", message: `${input.chargeKey} \xB7 ${input.kind === "delay" ? "gecikme" : "bekleme"} a\xE7\u0131klamas\u0131 ${saved ? "kaydedildi" : "kald\u0131r\u0131ld\u0131"}.` },
        "\u015Earj yolculu\u011Fu a\xE7\u0131klamas\u0131 geri al\u0131nabilir"
      );
    } catch (error) {
      setOperationAlert({ id: Date.now(), message: error instanceof Error ? error.message : "\u015Earj yolculu\u011Fu a\xE7\u0131klamas\u0131 kaydedilemedi." });
    }
  }
  const actions = {
    setMachineQueueLock,
    setAllMachineQueueLocks: setAllMachineQueueLocks2,
    saveMachineAvailability,
    rescheduleDownstreamOperation,
    placeDownstreamQueueOperation,
    replanDownstreamProcess,
    replaceTurningJob,
    recordOutsidePlanProduction: recordOutsidePlanProduction2,
    saveCurrentJob,
    completeCurrentJob,
    changeProductionHistoryStatus,
    editProductionHistoryEntry,
    restoreProductionDelivery,
    allocateProductionHistory,
    finishWipOperation,
    deliverJourneyWip,
    correctJourneyDates,
    releaseJourneyBuffer,
    beginDownstreamCurrentJob,
    replaceDownstreamCurrentJob,
    saveDownstreamCurrentJob,
    finishDownstreamCurrentJob,
    changeWipStage,
    releaseHeldWip,
    saveJourneyNote
  };
  if (!submitCommand) return actions;
  return new Proxy(actions, { get(target, property) {
    if (!productionCommandNames.includes(property)) return Reflect.get(target, property);
    return (...args) => {
      submitCommand({ kind: property === "deliverJourneyWip" && args[0]?.dateCorrection ? "correctJourneyDates" : property, args });
      return true;
    };
  } });
}

// lib/production-cancellation.ts
var MAX_CLOSED = 200;
var code2 = (value) => value.trim().toUpperCase();
var clone2 = (value) => structuredClone(value);
function producedBefore(seed, chargeId) {
  return (seed.productionInterruptions ?? []).filter((item) => item.process === "turning" && item.chargeId === chargeId && isProtectedProductionRemainder(item)).reduce((sum, item) => sum + Math.max(0, item.producedQuantity), 0);
}
function cancellableRemainders(seed, result) {
  const rows = [];
  for (const machine of seed.machines) {
    const current = machine.currentJob;
    if (!current.product || current.quantity <= 0 || current.sharedCharge) continue;
    const chargeId = current.batchId ?? `current:${machine.id}`;
    rows.push({
      kind: "current",
      machineId: machine.id,
      chargeId,
      product: current.product,
      workOrder: current.workOrder,
      assignedQuantity: current.quantity,
      previouslyProduced: producedBefore(seed, chargeId),
      requiresCompletedQuantity: true,
      start: current.start,
      signature: JSON.stringify(["current", machine.id, chargeId, current.product, current.workOrder, current.quantity, current.remainingQuantity ?? current.quantity, current.remainingAsOf ?? null, current.start])
    });
  }
  const open = new Map((seed.productionInterruptions ?? []).filter((item) => item.process === "turning" && isProtectedProductionRemainder(item) && !item.completedAt).map((item) => [item.chargeId, item]));
  for (const batch of result.batches.filter((item) => item.status === "planned" && !item.sharedCharge && open.has(item.id))) {
    if (seed.machines.some((machine) => machine.currentJob.batchId === batch.id && machine.currentJob.quantity > 0)) continue;
    const interruptions = (seed.productionInterruptions ?? []).filter((item) => item.process === "turning" && item.chargeId === batch.id && !item.completedAt && isProtectedProductionRemainder(item));
    const valid = interruptions.every((item) => Number.isFinite(item.occurredAt) && item.occurredAt > 0 && (item.resumedAt == null || Number.isFinite(item.resumedAt) && item.resumedAt >= item.occurredAt));
    const start = valid ? Math.max(...interruptions.flatMap((item) => [item.occurredAt, item.resumedAt ?? item.occurredAt])) : Number.NaN;
    rows.push({
      kind: "remainder",
      machineId: batch.machineId,
      chargeId: batch.id,
      product: batch.product,
      workOrder: batch.workOrder?.trim() ?? "",
      assignedQuantity: batch.quantity,
      previouslyProduced: producedBefore(seed, batch.id),
      requiresCompletedQuantity: false,
      start,
      signature: JSON.stringify([
        "remainder",
        batch.machineId,
        batch.id,
        batch.product,
        batch.workOrder ?? "",
        batch.quantity,
        interruptions.map((item) => [item.id, item.occurredAt, item.resumedAt, item.producedQuantity, item.remainingQuantity])
      ])
    });
  }
  return rows;
}
function validateCancellationTime(row, cancelledAt, now = /* @__PURE__ */ new Date()) {
  if (!Number.isFinite(row.start)) throw new Error("\xDCretim ge\xE7mi\u015Findeki tarih eksik veya ge\xE7ersiz. \u0130ptalden \xF6nce yar\u0131m \xFCretim kayd\u0131n\u0131 inceleyin.");
  if (!Number.isFinite(cancelledAt) || cancelledAt < row.start - 1e-8) throw new Error(row.kind === "remainder" ? "\u0130ptal zaman\u0131 kaydedilmi\u015F son \xFCretim veya devam zaman\u0131ndan \xF6nce olamaz." : "\u0130ptal zaman\u0131 \xFCretim ba\u015Flang\u0131c\u0131ndan \xF6nce olamaz.");
  if (cancelledAt > factoryNowSerial(now) + 1e-8) throw new Error("\u0130ptal zaman\u0131 gelecekte olamaz.");
}
function cancelRemainingProduction(seed, result, input, now = /* @__PURE__ */ new Date()) {
  const row = cancellableRemainders(seed, result).find((item) => item.machineId === input.machineId && item.chargeId === input.chargeId);
  if (!row) throw new Error("\u0130ptal edilecek Torna kalan \xFCretimi bulunamad\u0131. Kay\u0131t de\u011Fi\u015Ftiyse pencereyi yeniden a\xE7\u0131n.");
  if (row.signature !== input.expectedSignature) throw new Error("Mevcut i\u015F de\u011Fi\u015Fti; iptal bilgisini yeniden kontrol edin.");
  const reason = input.reason?.trim() ?? "";
  if (!reason) throw new Error("\u0130ptal nedeni zorunludur.");
  if (!Number.isSafeInteger(input.completedQuantity) || input.completedQuantity < 0) throw new Error("\xDCretilen adet s\u0131f\u0131r veya pozitif tam say\u0131 olmal\u0131d\u0131r.");
  if (!Number.isSafeInteger(input.cancelledQuantity) || input.cancelledQuantity <= 0) throw new Error("\u0130ptal edilen adet pozitif tam say\u0131 olmal\u0131d\u0131r.");
  if (input.completedQuantity + input.cancelledQuantity !== row.assignedQuantity) throw new Error(`\xDCretilen + iptal edilen adet ${row.assignedQuantity} olmal\u0131d\u0131r.`);
  if (!row.requiresCompletedQuantity && input.completedQuantity !== 0) throw new Error("Yar\u0131m kalan \u015Farjda yeni \xFCretim \xF6nce Mevcut i\u015Fi de\u011Fi\u015Ftir veya tamamlama ile kaydedilir; iptal yaln\u0131z kalan adedi kapsar.");
  validateCancellationTime(row, input.cancelledAt, now);
  let nextSeed;
  let nextResult;
  let archived;
  if (row.kind === "current" && input.completedQuantity === 0) {
    nextSeed = clone2(seed);
    const machine = nextSeed.machines.find((item) => item.id === row.machineId);
    machine.currentJob = { workOrder: "", product: "", quantity: 0, originalQuantity: 0, remainingQuantity: 0, start: input.cancelledAt, end: input.cancelledAt, dailyRate: 0, diameter: "" };
    machine.availableStart = input.cancelledAt;
    machine.operationalAvailableStart = input.cancelledAt;
    nextResult = scenarioResultFromBatches(nextSeed, result.batches.map((batch) => ({ ...batch })));
  } else if (row.kind === "current") {
    const working = clone2(seed);
    const machine = working.machines.find((item) => item.id === row.machineId);
    machine.currentJob.quantity = input.completedQuantity;
    machine.currentJob.originalQuantity = input.completedQuantity;
    machine.currentJob.remainingQuantity = 0;
    const completed = completeMachineCurrentJob(working, result, row.machineId, input.cancelledAt);
    nextSeed = completed.seed;
    nextResult = completed.result;
    archived = completed.archived;
    archived.statusChangeReason = `Kalan \xFCretim iptal edildi: ${row.assignedQuantity} atanm\u0131\u015F, ${input.completedQuantity} \xFCretildi, ${input.cancelledQuantity} iptal. Neden: ${reason}`;
    registerTurningCompletion(nextSeed, archived);
  } else {
    nextSeed = clone2(seed);
    const batches = result.batches.filter((batch) => batch.id !== row.chargeId).map((batch) => ({ ...batch }));
    nextResult = { ...scenarioResultFromBatches(nextSeed, batches), state: result.state, planRun: result.planRun };
  }
  finishProductionInterruptions(nextSeed, row.chargeId, "turning", input.cancelledAt);
  const orders = nextSeed.orders.filter((order) => code2(order.product) === code2(row.product));
  const cancellation = {
    id: `cancellation-${crypto.randomUUID()}`,
    version: 1,
    product: row.product,
    process: "turning",
    chargeId: row.chargeId,
    workOrder: row.workOrder,
    machineId: row.machineId,
    assignedQuantity: row.assignedQuantity,
    completedQuantity: input.completedQuantity,
    cancelledQuantity: input.cancelledQuantity,
    reason,
    cancelledAt: factoryDateTimeToIso(excelSerialToDate(input.cancelledAt).toISOString().slice(0, 16)),
    orderIds: orders.map((order) => order.id),
    orderQuantities: Object.fromEntries(orders.map((order) => [order.id, order.quantity])),
    historyEntryId: archived?.id,
    review: { status: "pending" }
  };
  nextSeed.productionCancellations = boundedCancellations([...nextSeed.productionCancellations ?? [], cancellation]);
  nextSeed.manualBatches = nextResult.batches.map((batch) => ({ ...batch }));
  nextSeed.planNeedsRecalculation = true;
  nextSeed.lastAutomaticPlan = void 0;
  nextSeed.planRunSequence = void 0;
  return { seed: nextSeed, result: nextResult, cancellation, archived };
}
function boundedCancellations(records2) {
  const holding = records2.filter((item) => item.review.status !== "replacement-approved");
  const approved = records2.filter((item) => item.review.status === "replacement-approved").slice(-MAX_CLOSED);
  return [...holding, ...approved];
}
function reviewProductionCancellation(seed, id, decision, note = "", now = /* @__PURE__ */ new Date()) {
  const next = clone2(seed);
  const record = next.productionCancellations?.find((item) => item.id === id);
  if (!record) throw new Error("\u0130ptal kayd\u0131 bulunamad\u0131.");
  if (record.review.status !== "pending") throw new Error("Bu iptal kayd\u0131 zaten incelendi.");
  if (decision !== "replacement-approved" && decision !== "replacement-declined") throw new Error("\u0130nceleme karar\u0131 ge\xE7ersiz.");
  record.review = { status: decision, reviewedAt: now.toISOString(), ...note.trim() ? { note: note.trim().slice(0, 500) } : {} };
  next.productionCancellations = boundedCancellations(next.productionCancellations);
  next.planNeedsRecalculation = true;
  next.lastAutomaticPlan = void 0;
  next.planRunSequence = void 0;
  return next;
}

// lib/plan-run.ts
var PLAN_ENGINE_VERSION = 6;
function clone3(value) {
  return JSON.parse(JSON.stringify(value));
}
function inputDateToSerial3(value) {
  if (!value) return 0;
  const timestamp = Date.parse(`${value}T00:00:00Z`);
  if (!/^\d{4}-\d{2}-\d{2}$/.test(value) || !Number.isFinite(timestamp) || new Date(timestamp).toISOString().slice(0, 10) !== value) return Number.NaN;
  return (timestamp - Date.UTC(1899, 11, 30)) / 864e5;
}
function formatDate(value) {
  if (!value) return "\u2014";
  return new Intl.DateTimeFormat("tr-TR", { day: "2-digit", month: "short", year: "numeric", timeZone: "UTC" }).format(/* @__PURE__ */ new Date(`${value}T00:00:00Z`));
}
function metadataForCompletedRanges(optimizationGoal, ranges, policy, planId, version, createdAt, deliveryDeduction) {
  const first = ranges[0];
  const last = ranges.at(-1);
  if (!first || !last) throw new Error("Planlama i\xE7in tamamlanm\u0131\u015F hafta aral\u0131\u011F\u0131 bulunamad\u0131.");
  return {
    planId,
    version,
    engineVersion: PLAN_ENGINE_VERSION,
    optimizationGoal,
    includePriorBacklog: policy.includePriorBacklog,
    allowProductionBeforeScope: policy.allowProductionBeforeScope,
    shortageExtraCharge: { ...policy.shortageExtraCharge },
    deliveryDeduction,
    scope: {
      kind: "customer-weeks",
      startDate: first.startDate,
      endDate: last.endDate,
      label: ranges.map((range, index) => `${index + 1}. ${range.label}`).join(" \xB7 "),
      startWeekId: first.startWeekId,
      endWeekId: last.endWeekId,
      ranges: ranges.map((range) => ({ ...range }))
    },
    createdAt
  };
}
function customerStageSeed(seed, allRanges, completedRangeCount, optimizationGoal, policy, sequenceCreatedAt, updatedAt) {
  if (!seed.customerDemand) throw new Error("A\u015Famal\u0131 planlama i\xE7in m\xFC\u015Fteri hafta verisi bulunamad\u0131.");
  if (completedRangeCount < 1 || completedRangeCount > allRanges.length) throw new Error("Planlama aral\u0131\u011F\u0131 s\u0131ras\u0131 ge\xE7ersiz.");
  const completedRanges = allRanges.slice(0, completedRangeCount);
  const first = completedRanges[0];
  const last = completedRanges.at(-1);
  const stageSeed = clone3(seed);
  const state = buildWeeklyPlanningState(
    previewFromDataset(seed.customerDemand),
    seed.orders,
    { startWeekId: first.startWeekId, endWeekId: last.endWeekId },
    seed.customerOrderOverrides,
    { includePriorBacklog: policy.includePriorBacklog }
  );
  state.dataset.importedAt = seed.customerDemand.importedAt;
  const orderImport = orderImportMetadataForSeed(stageSeed);
  const deduction = policy.deliveryDeductionFilter && orderImport ? calculateDeliveryDeduction({
    orders: state.orders,
    productionHistory: stageSeed.productionHistory,
    orderImport,
    importProducts: seed.customerDemand.products.map((product) => product.product),
    filter: policy.deliveryDeductionFilter
  }) : null;
  if (deduction) state.orders = deduction.adjustedOrders;
  const filterStandard = seed.productionArea === "cubuk-filtre" && optimizationGoal === "coarse";
  if (filterStandard) {
    state.orders = state.orders.map((order) => ({
      ...order,
      dueDate: last.endDate,
      allowPartial: false,
      partialDeliveryQuantity: 0,
      partialDeliveryDate: "",
      deliveryMilestones: []
    }));
  }
  const metadata = metadataForCompletedRanges(optimizationGoal, completedRanges, policy, sequenceCreatedAt, completedRangeCount, updatedAt, deduction?.snapshot);
  const sequence = allRanges.length > 1 ? {
    planId: sequenceCreatedAt,
    engineVersion: PLAN_ENGINE_VERSION,
    optimizationGoal,
    includePriorBacklog: policy.includePriorBacklog,
    allowProductionBeforeScope: policy.allowProductionBeforeScope,
    shortageExtraCharge: { ...policy.shortageExtraCharge },
    deliveryDeductionFilter: policy.deliveryDeductionFilter,
    ranges: allRanges.map((range) => ({ ...range })),
    completedRangeCount,
    createdAt: sequenceCreatedAt,
    updatedAt
  } : void 0;
  const planEnd = inputDateToSerial3(filterStandard ? last.endDate : state.planEndDate);
  stageSeed.orders = state.orders;
  stageSeed.customerDemand = state.dataset;
  stageSeed.openingStock = {};
  stageSeed.orderCatalog = state.orderCatalog;
  stageSeed.demandTargets = void 0;
  stageSeed.activePlanRun = metadata;
  stageSeed.planNeedsRecalculation = false;
  stageSeed.planRunSequence = sequence;
  const productionStart = inputDateToSerial3(first.startDate);
  for (const machine of stageSeed.machines) {
    const operationalStart = machine.operationalAvailableStart ?? machine.availableStart;
    machine.operationalAvailableStart = operationalStart;
    machine.availableStart = filterStandard || !policy.allowProductionBeforeScope ? Math.max(operationalStart, productionStart) : operationalStart;
    machine.planEnd = planEnd;
  }
  return { seed: stageSeed, metadata, sequence, deliveryPreview: deduction ?? void 0 };
}
function defaultPlanRunShortagePolicy(seed) {
  return seed.productionArea === "cubuk-filtre" ? { enabled: true, thresholdPercent: 0 } : { enabled: false, thresholdPercent: 50 };
}
function planRunDeliveryHistory(seed) {
  const year = seed.monthlyCustomerDemand?.year;
  return year === void 0 ? seed.productionHistory : seed.productionHistory?.filter((entry) => {
    const instant = effectiveDeliveryTimestamp(entry);
    return instant && factoryDateInput(instant).startsWith(`${year}-`);
  });
}
function preparePlanRun(seed, request, createdAt = (/* @__PURE__ */ new Date()).toISOString()) {
  if ((seed.schemaVersion ?? 0) < CURRENT_PLANNING_SCHEMA_VERSION && (seed.productionArea !== "cubuk-filtre" || seed.processMasterData)) seed = migratePlanningSeed(seed);
  if (seed.customerDemand) {
    const weeks = seed.customerDemand.weeks;
    const requestedRanges = request.weekRanges?.length ? request.weekRanges : request.monthRange ? [weekScopeForPlanningMonthRange(weeks, request.monthRange)] : [];
    const completedRanges = request.appendToExistingPlan ? completedCustomerPlanRanges(seed) : [];
    const existingGoal = seed.planRunSequence?.optimizationGoal ?? seed.activePlanRun?.optimizationGoal;
    if (request.appendToExistingPlan && existingGoal && request.optimizationGoal !== existingGoal) {
      throw new Error("Plan\u0131n devam\u0131, mevcut planla ayn\u0131 optimizasyon hedefini kullanmal\u0131d\u0131r.");
    }
    const resolvedRanges = resolvePlanningWeekRanges(weeks, [...completedRanges, ...requestedRanges]);
    const allRanges = resolvedRanges.map((range) => ({
      startWeekId: range.startWeekId,
      endWeekId: range.endWeekId,
      startDate: range.startDate,
      endDate: range.endDate,
      label: range.label
    }));
    const completedRangeCount = completedRanges.length;
    const sequenceCreatedAt = request.appendToExistingPlan ? seed.planRunSequence?.planId ?? seed.planRunSequence?.createdAt ?? seed.activePlanRun?.planId ?? seed.activePlanRun?.createdAt ?? createdAt : createdAt;
    const orderImport = orderImportMetadataForSeed(seed);
    const requestedDeliveryFilter = orderImport ? { enabled: request.deliveryDeduction?.enabled ?? true, startAt: request.deliveryDeduction?.startAt ?? orderImport.shipmentsThrough ?? orderImport.importedAt, includeStart: request.deliveryDeduction?.includeStart ?? !orderImport.shipmentsThrough, endAt: createdAt } : void 0;
    const requestedShortageExtraCharge = normalizeShortageExtraChargePolicy(request.shortageExtraCharge ?? defaultPlanRunShortagePolicy(seed));
    const policy = request.appendToExistingPlan ? {
      includePriorBacklog: seed.planRunSequence?.includePriorBacklog ?? seed.activePlanRun?.includePriorBacklog ?? true,
      allowProductionBeforeScope: seed.planRunSequence?.allowProductionBeforeScope ?? seed.activePlanRun?.allowProductionBeforeScope ?? true,
      shortageExtraCharge: normalizeShortageExtraChargePolicy(seed.planRunSequence?.shortageExtraCharge ?? seed.activePlanRun?.shortageExtraCharge),
      deliveryDeductionFilter: seed.planRunSequence?.deliveryDeductionFilter ?? seed.activePlanRun?.deliveryDeduction?.filter ?? requestedDeliveryFilter
    } : {
      includePriorBacklog: request.includePriorBacklog ?? false,
      allowProductionBeforeScope: request.allowProductionBeforeScope ?? false,
      shortageExtraCharge: requestedShortageExtraCharge,
      deliveryDeductionFilter: requestedDeliveryFilter
    };
    if (seed.productionArea === "cubuk-filtre" && request.optimizationGoal === "coarse") policy.allowProductionBeforeScope = false;
    const preparedStages = allRanges.slice(completedRangeCount).map((_, index) => customerStageSeed(seed, allRanges, completedRangeCount + index + 1, request.optimizationGoal, policy, sequenceCreatedAt, createdAt));
    const first = preparedStages[0];
    if (!first) throw new Error("Planlama i\xE7in \xE7al\u0131\u015Ft\u0131r\u0131lacak hafta aral\u0131\u011F\u0131 bulunamad\u0131.");
    return {
      seed: first.seed,
      stages: preparedStages.map((stage) => stage.seed),
      metadata: first.metadata,
      scopeLabel: allRanges[completedRangeCount].label,
      sequence: first.sequence,
      deliveryPreview: first.deliveryPreview
    };
  } else {
    const planningSeed = clone3(seed);
    let startDate = request.productionStartDate ?? "";
    const endDate = request.productionEndDate ?? "";
    const previousRun = seed.activePlanRun;
    const monthlyContinuation = Boolean(request.appendToExistingPlan && seed.productionArea === "cubuk-filtre" && seed.monthlyCustomerDemand);
    if (request.appendToExistingPlan && !monthlyContinuation) throw new Error("Devam plan\u0131 i\xE7in ayl\u0131k \xC7ubuk Filtre verisi gerekir.");
    if (monthlyContinuation) {
      if (!previousRun || previousRun.scope.kind !== "production-dates") throw new Error("Devam ettirilecek kay\u0131tl\u0131 tarih plan\u0131 bulunamad\u0131.");
      if (request.optimizationGoal !== previousRun.optimizationGoal) throw new Error("Plan\u0131n devam\u0131, mevcut planla ayn\u0131 optimizasyon hedefini kullanmal\u0131d\u0131r.");
      if (inputDateToSerial3(endDate) <= inputDateToSerial3(previousRun.scope.endDate)) throw new Error("Kademeli plan\u0131n biti\u015Fi mevcut kapsamdan sonra olmal\u0131d\u0131r.");
      if (!inputDateToSerial3(startDate) || inputDateToSerial3(startDate) > inputDateToSerial3(previousRun.scope.endDate) + 1) throw new Error("Yeni kapsam mevcut plan\u0131n hemen arkas\u0131ndan ba\u015Flamal\u0131d\u0131r.");
      startDate = previousRun.scope.startDate;
    }
    const start = inputDateToSerial3(startDate);
    const end = inputDateToSerial3(endDate);
    if (!start || !end || start > end) throw new Error("Planlama ba\u015Flang\u0131\xE7 ve biti\u015F tarihini kontrol edin.");
    for (const machine of planningSeed.machines) {
      const operationalStart = machine.operationalAvailableStart ?? machine.availableStart;
      machine.operationalAvailableStart = operationalStart;
      machine.availableStart = Math.max(operationalStart, start);
      machine.planEnd = end;
    }
    if (planningSeed.monthlyCustomerDemand) {
      const source = planningSeed.monthlyCustomerDemand.openingStock;
      if (source && !(planningSeed.filterInitialStockSetup ?? planningSeed.monthlyCustomerDemand.stockReconciliation)) throw new Error("Ba\u015Flang\u0131\xE7 stoklar\u0131n\u0131 Sipari\u015Fler ekran\u0131nda uzla\u015Ft\u0131r\u0131n. Kaynak say\u0131m\u0131 hen\xFCz plana uygulanmad\u0131.");
      const data = { ...planningSeed.monthlyCustomerDemand, startDate, endDate };
      const monthly = buildFilterMonthlyOrders(planningSeed, data);
      planningSeed.monthlyCustomerDemand = data;
      planningSeed.orders = monthly.orders;
      planningSeed.orderImportGrossOrders = clone3(monthly.orders);
    }
    const orderImport = orderImportMetadataForSeed(planningSeed);
    const deliveryFilter = orderImport ? { enabled: planningSeed.monthlyCustomerDemand ? true : request.deliveryDeduction?.enabled ?? true, startAt: planningSeed.monthlyCustomerDemand ? orderImport.shipmentsThrough ?? orderImport.importedAt : request.deliveryDeduction?.startAt ?? orderImport.shipmentsThrough ?? orderImport.importedAt, includeStart: planningSeed.monthlyCustomerDemand ? false : request.deliveryDeduction?.includeStart ?? !orderImport.shipmentsThrough, endAt: createdAt } : void 0;
    const deduction = orderImport && deliveryFilter ? calculateDeliveryDeduction({
      orders: planningSeed.orderImportGrossOrders ?? planningSeed.orders,
      productionHistory: planRunDeliveryHistory(planningSeed),
      orderImport,
      importProducts: planningSeed.orderCatalog ?? planningSeed.orders.map((order) => order.product),
      filter: deliveryFilter
    }) : null;
    if (deduction) planningSeed.orders = deduction.adjustedOrders;
    const metadata = {
      ...seed.productionArea === "cubuk-filtre" ? { chargeIdNamespace: chargeIdNamespace() } : {},
      planId: monthlyContinuation ? previousRun.planId ?? previousRun.createdAt : createdAt,
      version: monthlyContinuation ? (previousRun.version ?? 1) + 1 : 1,
      engineVersion: PLAN_ENGINE_VERSION,
      optimizationGoal: request.optimizationGoal,
      shortageExtraCharge: normalizeShortageExtraChargePolicy(request.shortageExtraCharge ?? defaultPlanRunShortagePolicy(seed)),
      deliveryDeduction: deduction?.snapshot,
      scope: {
        kind: "production-dates",
        startDate,
        endDate,
        label: `${formatDate(startDate)}\u2013${formatDate(endDate)}`
      },
      createdAt
    };
    planningSeed.activePlanRun = metadata;
    planningSeed.planNeedsRecalculation = false;
    planningSeed.planRunSequence = void 0;
    return { seed: planningSeed, stages: [planningSeed], metadata, scopeLabel: metadata.scope.label, deliveryPreview: deduction ?? void 0 };
  }
}
function completedCustomerPlanRanges(seed) {
  if (!seed.customerDemand || seed.activePlanRun?.scope.kind !== "customer-weeks") {
    throw new Error("Devam\u0131na aral\u0131k eklenecek tamamlanm\u0131\u015F bir m\xFC\u015Fteri plan\u0131 bulunamad\u0131.");
  }
  const sequence = seed.planRunSequence;
  if (sequence && sequence.completedRangeCount < sequence.ranges.length) {
    throw new Error("\xD6nce bekleyen s\u0131radaki planlama aral\u0131\u011F\u0131n\u0131 tamamlay\u0131n.");
  }
  const metadataRanges = seed.activePlanRun.scope.ranges;
  const ranges = metadataRanges?.length ? metadataRanges.map((range) => ({ startWeekId: range.startWeekId, endWeekId: range.endWeekId })) : [{
    startWeekId: seed.activePlanRun.scope.startWeekId ?? seed.customerDemand.activeScope.startWeekId,
    endWeekId: seed.activePlanRun.scope.endWeekId ?? seed.customerDemand.activeScope.endWeekId
  }];
  if (!ranges[0]?.startWeekId || !ranges.at(-1)?.endWeekId) {
    throw new Error("Mevcut plan\u0131n ISO hafta kapsam\u0131 bulunamad\u0131.");
  }
  return ranges;
}

// lib/scenario-safety.ts
var officialInputFields = ["orders", "products", "preferences", "restrictions", "machines", "holidays", "calendarEvents", "setupSettings", "processMasterData", "processWaitSettings", "flowSettings", "productWeights", "rawMaterialSettings", "customerDemand", "openingStock", "productionArea", "processStockSettings", "dailyCustomerDemand", "filterMonthlyPlan", "monthlyCustomerDemand", "filterWaitShifts", "filterQualityShifts", "filterInitialStockSetup", "filterMonthlyDeliveryBaselines", "orderImport", "orderImportGrossOrders", "customerOrderOverrides", "orderCatalog", "orderCatalogName"];
var personalProposalFields = ["manualBatches", "savedBatches", "processOperationOverrides", "activePlanningScope", "demandTargets", "activePlanRun", "planRunSequence", "lastAutomaticPlan", "planningResetVersion", "plannedThroughProcess", "initialProcessPlanComplete"];
function officialInputValue(seed, field) {
  if (field !== "machines") return seed[field] ?? null;
  return seed.machines.map(({ availableStart: _available, operationalAvailableStart: _operational, currentJob: _current, ...machine }) => machine);
}
function changesOfficialInputs(next, current) {
  const stable2 = (value) => JSON.stringify(value ?? null, (_key, item) => item && typeof item === "object" && !Array.isArray(item) ? Object.fromEntries(Object.entries(item).sort(([a], [b]) => a < b ? -1 : a > b ? 1 : 0)) : item);
  const canonicalNext = migratePlanningSeed(next), canonicalCurrent = migratePlanningSeed(current);
  return officialInputFields.some((field) => stable2(officialInputValue(canonicalNext, field)) !== stable2(officialInputValue(canonicalCurrent, field)));
}
function copy(value) {
  return JSON.parse(JSON.stringify(value));
}
function emptyCurrentJob(machine) {
  const baseline = machine.operationalAvailableStart ?? machine.availableStart;
  return {
    workOrder: "",
    product: "",
    quantity: 0,
    originalQuantity: 0,
    remainingQuantity: 0,
    start: baseline,
    end: baseline,
    dailyRate: 0,
    diameter: ""
  };
}
function scenarioPlanningSeed(seed) {
  if (seed.initialProcessPlanComplete !== void 0 && typeof seed.initialProcessPlanComplete !== "boolean") throw new Error("\u0130lk plan durumu ge\xE7ersiz.");
  if (seed.plannedThroughProcess !== void 0 && !productionProcessOrder(seed).includes(seed.plannedThroughProcess)) throw new Error("Kay\u0131tl\u0131 planlama prosesi bu \xFCretim alan\u0131na ait de\u011Fil.");
  const scenario = copy(seed);
  delete scenario.filterInitialStockSetup;
  delete scenario.filterMonthlyDeliveryBaselines;
  if (scenario.monthlyCustomerDemand) {
    delete scenario.monthlyCustomerDemand.stockReconciliation;
    delete scenario.monthlyCustomerDemand.deliveryBaseline;
  }
  scenario.productionInterruptions = [];
  scenario.productionCancellations = [];
  scenario.productionHistory = [];
  scenario.wipLots = [];
  scenario.wipMovements = [];
  scenario.chargeJourneyNotes = [];
  scenario.planningEvents = [];
  scenario.processCurrentJobs = [];
  scenario.machines = scenario.machines.map((machine) => ({ ...machine, currentJob: emptyCurrentJob(machine) }));
  return scenario;
}
function mergeRemainderLocks(liveSeed, proposals, reset = false) {
  return withInterruptedBatches(liveSeed, proposals.filter((batch) => !hasProtectedProductionRemainder(liveSeed, batch.id, batch.interruptionId))).map((batch) => {
    if (!hasProtectedProductionRemainder(liveSeed, batch.id, batch.interruptionId)) return batch;
    const matches = proposals.filter((proposal2) => proposal2.id === batch.id);
    const proposal = matches.length === 1 ? matches[0] : void 0;
    const matchesIdentity = proposal && proposal.interruptionId === batch.interruptionId && proposal.quantity === batch.quantity && proposal.product === batch.product && (proposal.workOrder ?? "") === (batch.workOrder ?? "") && proposal.machineId === batch.machineId && typeof proposal.locked === "boolean";
    const retained = matchesIdentity ? { ...batch, locked: proposal.locked } : batch;
    if (!reset) return retained;
    const clean = withoutRouteChoices(retained);
    return matchesIdentity ? {
      ...clean,
      ...proposal.routeCommitted === void 0 ? {} : { routeCommitted: proposal.routeCommitted },
      ...proposal.routeTargetDate === void 0 ? {} : { routeTargetDate: proposal.routeTargetDate }
    } : clean;
  });
}
function mergeScenarioWithLiveOperations(scenarioSeed, liveSeed) {
  assertProductionArea(scenarioSeed, liveSeed.productionArea ?? "torna");
  const merged = copy(scenarioSeed);
  const changedOperations = ["productionHistory", "wipLots", "processCurrentJobs", "productionInterruptions", "productionCancellations"].some((field) => JSON.stringify(scenarioSeed[field] ?? []) !== JSON.stringify(liveSeed[field] ?? [])) || scenarioSeed.machines.some((machine) => {
    const live = liveSeed.machines.find((item) => item.id === machine.id);
    return live && (JSON.stringify(machine.currentJob) !== JSON.stringify(live.currentJob) || machine.operationalAvailableStart !== live.operationalAvailableStart);
  });
  if (changedOperations) merged.planNeedsRecalculation = true;
  if (JSON.stringify(scenarioSeed.flowSettings) !== JSON.stringify(liveSeed.flowSettings)) merged.planNeedsRecalculation = true;
  if (liveSeed.flowSettings) merged.flowSettings = copy(liveSeed.flowSettings);
  else delete merged.flowSettings;
  if (JSON.stringify(scenarioSeed.processStockSettings) !== JSON.stringify(liveSeed.processStockSettings) || scenarioSeed.filterWaitShifts !== liveSeed.filterWaitShifts || scenarioSeed.filterQualityShifts !== liveSeed.filterQualityShifts) merged.planNeedsRecalculation = true;
  merged.filterWaitShifts = liveSeed.filterWaitShifts;
  merged.filterQualityShifts = liveSeed.filterQualityShifts;
  if (liveSeed.processStockSettings) merged.processStockSettings = copy(liveSeed.processStockSettings);
  else delete merged.processStockSettings;
  const evidence = copy(liveSeed);
  promoteFilterMonthlyEvidence(evidence);
  for (const field of ["filterInitialStockSetup", "filterMonthlyDeliveryBaselines"]) {
    if (JSON.stringify(merged[field]) !== JSON.stringify(evidence[field])) merged.planNeedsRecalculation = true;
    if (field === "filterInitialStockSetup") merged.filterInitialStockSetup = evidence.filterInitialStockSetup;
    else merged.filterMonthlyDeliveryBaselines = evidence.filterMonthlyDeliveryBaselines;
  }
  if (merged.monthlyCustomerDemand) {
    const data = merged.monthlyCustomerDemand;
    const baseline = filterDeliveryBaselineFor(evidence, data.year);
    data.stockReconciliation = evidence.filterInitialStockSetup;
    if (evidence.filterInitialStockSetup?.sourceRows) data.openingStock = { cutoffDate: evidence.filterInitialStockSetup.cutoffDate, rows: copy(evidence.filterInitialStockSetup.sourceRows) };
    if (baseline) {
      if (JSON.stringify(data.handovers) !== JSON.stringify(baseline.handovers)) merged.planNeedsRecalculation = true;
      data.handovers = copy(baseline.handovers).filter((row) => data.rows.some((item) => item.product === row.product));
      data.deliveryBaseline = copy(baseline);
      data.snapshotDate = baseline.snapshotDate;
      if (Date.parse(data.importedAt) < Date.parse(baseline.importedAt)) data.importedAt = baseline.importedAt;
      if (merged.orderImport) merged.orderImport = { ...merged.orderImport, importedAt: data.importedAt, shipmentsThrough: baseline.shipmentsThrough };
    }
  }
  if (JSON.stringify(liveSeed.processWaitSettings) !== JSON.stringify(scenarioSeed.processWaitSettings)) merged.planNeedsRecalculation = true;
  merged.processWaitSettings = liveSeed.processWaitSettings ? copy(liveSeed.processWaitSettings) : void 0;
  merged.productWeights = copy(liveSeed.productWeights ?? []);
  merged.rawMaterialSettings = copy(liveSeed.rawMaterialSettings ?? { scrapPercent: 2, stockDate: "", stocks: [] });
  merged.productionInterruptions = copy(liveSeed.productionInterruptions ?? []);
  if (liveSeed.productionCancellations) merged.productionCancellations = copy(liveSeed.productionCancellations);
  else delete merged.productionCancellations;
  const proposals = merged.manualBatches ?? [];
  merged.manualBatches = mergeRemainderLocks(liveSeed, proposals, merged.planningResetVersion === 1);
  if (merged.planningResetVersion === 1) merged.processOperationOverrides = mergeResetProcessOverrides(merged, liveSeed);
  merged.productionHistory = copy(liveSeed.productionHistory ?? []);
  merged.wipLots = copy(liveSeed.wipLots ?? []);
  merged.wipMovements = copy(liveSeed.wipMovements ?? []);
  merged.chargeJourneyNotes = copy(liveSeed.chargeJourneyNotes ?? []);
  merged.planningEvents = copy(liveSeed.planningEvents ?? []);
  merged.processCurrentJobs = copy(liveSeed.processCurrentJobs ?? []);
  merged.machines = merged.machines.map((machine) => {
    const live = liveSeed.machines.find((item) => item.id === machine.id);
    if (!live) return machine;
    return {
      ...machine,
      currentJob: copy(live.currentJob),
      operationalAvailableStart: live.operationalAvailableStart,
      availableStart: Math.max(machine.availableStart, live.operationalAvailableStart ?? live.currentJob.end)
    };
  });
  const included = new Set(merged.machines.map((machine) => machine.id));
  const missing = liveSeed.machines.filter((machine) => !included.has(machine.id) && machine.currentJob.quantity > 0);
  if (missing.length) {
    merged.machines.push(...copy(missing));
    merged.planNeedsRecalculation = true;
  }
  return reconcileTurningSeed(merged);
}
function mergePublishedOverrides(draft, live) {
  if (draft.planningResetVersion === 1) return mergeResetProcessOverrides(draft, live);
  const physical = /* @__PURE__ */ new Set();
  for (const lot of live.wipLots ?? []) {
    physical.add(lot.id);
    if (lot.sourceBatchId) physical.add(lot.sourceBatchId);
  }
  for (const job of live.processCurrentJobs ?? []) physical.add(job.batchId);
  const isPhysical = (batchId) => batchId.startsWith("current:") || physical.has(batchId);
  return [
    ...(live.processOperationOverrides ?? []).filter((item) => isPhysical(item.batchId)),
    ...(draft.processOperationOverrides ?? []).filter((item) => !isPhysical(item.batchId))
  ];
}
function projectPlanningRunInputs(world, run) {
  if (!run) return world;
  const request = {
    optimizationGoal: run.optimizationGoal,
    includePriorBacklog: run.includePriorBacklog,
    allowProductionBeforeScope: run.allowProductionBeforeScope,
    shortageExtraCharge: run.shortageExtraCharge,
    deliveryDeduction: run.deliveryDeduction?.filter
  };
  if (run.scope.kind === "production-dates") {
    request.productionStartDate = run.scope.startDate;
    request.productionEndDate = run.scope.endDate;
  } else {
    request.weekRanges = [{
      startWeekId: run.scope.startWeekId ?? run.scope.ranges?.[0]?.startWeekId ?? "",
      endWeekId: run.scope.endWeekId ?? run.scope.ranges?.at(-1)?.endWeekId ?? ""
    }];
  }
  const prepared = preparePlanRun(world, request, run.createdAt).seed;
  const projected = copy(world);
  for (const field of ["orders", "customerDemand", "openingStock", "orderImportGrossOrders", "monthlyCustomerDemand", "orderCatalog"]) {
    if (Object.hasOwn(prepared, field)) projected[field] = structuredClone(prepared[field]);
    else delete projected[field];
  }
  projected.machines = projected.machines.map((machine) => {
    const planned = prepared.machines.find((row) => row.id === machine.id);
    return { ...machine, availableStart: planned.availableStart, planEnd: planned.planEnd };
  });
  return projected;
}
function mergePersonalDraftWithWorld(draft, world, worldChanged = false) {
  assertProductionArea(draft, world.productionArea ?? "torna");
  const currentInputs = migratePlanningSeed(world);
  const currentDraft = migratePlanningSeed(draft);
  let expectedInputs = currentInputs;
  let invalidRunScope = false;
  try {
    expectedInputs = projectPlanningRunInputs(currentInputs, draft.activePlanRun);
  } catch {
    invalidRunScope = true;
  }
  const next = copy(expectedInputs);
  for (const field of personalProposalFields) {
    if (Object.hasOwn(draft, field)) next[field] = structuredClone(draft[field]);
    else delete next[field];
  }
  if (Object.hasOwn(draft, "scenarioProvenance")) Object.defineProperty(next, "scenarioProvenance", {
    value: structuredClone(draft.scenarioProvenance),
    enumerable: true,
    writable: true,
    configurable: true
  });
  next.processOperationOverrides = mergePublishedOverrides(draft, world);
  next.planNeedsRecalculation = Boolean(currentDraft.planNeedsRecalculation || worldChanged || invalidRunScope || changesOfficialInputs(scenarioPlanningSeed(draft), scenarioPlanningSeed(expectedInputs)) && changesOfficialInputs(scenarioPlanningSeed(draft), scenarioPlanningSeed(world)));
  return mergeScenarioWithLiveOperations(next, world);
}
function rebaseScenarioPlan(seed, savedResult) {
  const result = recalculateManualScenario(seed, mergeRemainderLocks(seed, reconcileTurningQueue(seed, savedResult.batches), seed.planningResetVersion === 1), { allowPlanEndOverflow: true });
  const machines = new Map(seed.machines.map((machine) => [machine.id, machine]));
  const overflows = result.batches.filter((batch) => {
    const machine = machines.get(batch.machineId);
    return batch.status === "planned" && Boolean(machine) && batch.end >= Math.floor(machine.planEnd) + 1;
  }).map((batch) => {
    const machine = machines.get(batch.machineId);
    return {
      batchId: batch.id,
      workOrder: batch.workOrder?.trim() ?? "",
      product: batch.product,
      machineId: batch.machineId,
      queuePosition: Math.max(1, batch.planColumn - 12),
      locked: Boolean(batch.locked),
      start: batch.start,
      end: batch.end,
      windowStart: machine.availableStart,
      windowEnd: machine.planEnd
    };
  }).sort((left, right) => left.machineId.localeCompare(right.machineId, "tr", { numeric: true }) || left.queuePosition - right.queuePosition || left.batchId.localeCompare(right.batchId));
  return { result, overflows };
}

// lib/collaboration-runtime.ts
function stable(value) {
  if (Array.isArray(value)) return value.map(stable);
  if (value && typeof value === "object") return Object.fromEntries(Object.entries(value).sort(([a], [b]) => a < b ? -1 : a > b ? 1 : 0).map(([k, v]) => [k, stable(v)]));
  return value;
}
var lockedIdentity = (batch) => batch ? [batch.id, batch.machineId, batch.product, batch.workOrder ?? "", batch.quantity, batch.planColumn, Boolean(batch.routeCommitted), batch.routeTargetDate ?? null, batch.interruptionId ?? null, batch.sharedCharge ?? null] : null;
var hash = (value) => (0, import_node_crypto.createHash)("sha256").update(JSON.stringify(stable(value))).digest("hex");
function publicationProtectionMessage(batch, proposal) {
  const protection = "Kay\u0131tl\u0131 ak\u0131\u015F tercihi: Yay\u0131nlama ak\u0131\u015F tercihi olan \u015Farj\u0131 de\u011Fi\u015Ftiremez.";
  const difference = proposal ? "Ki\u015Fisel taslakta bu \u015Farj\u0131n korunan bilgileri de\u011Fi\u015Fmi\u015F." : "Ki\u015Fisel taslakta bu \u015Farj yok.";
  const position = queuePosition(batch.planColumn);
  return `${protection} Tezgah: ${batch.machineId} \xB7 \xDCr\xFCn: ${batch.product} \xB7 \u0130\u015F emri: ${batch.workOrder || "Yok"} \xB7 Miktar: ${formatDecimal(batch.quantity)} adet \xB7 Ortak plandaki s\u0131ra: ${position > 0 ? position : "Belirtilmemi\u015F"}. ${difference} Ortak plan ile ki\u015Fisel tasla\u011F\u0131 kar\u015F\u0131la\u015Ft\u0131r\u0131n.`;
}
var planNeutralCommands = ["saveJourneyNote", "setMachineQueueLock", "setAllMachineQueueLocks"];
try {
  const request = JSON.parse((0, import_node_fs.readFileSync)(0, "utf8"));
  const seed = request.seed;
  let response;
  if (request.action === "draft") {
    const clean = scenarioPlanningSeed(seed);
    const display = request.world ? mergePersonalDraftWithWorld(clean, request.world, Boolean(request.worldChanged)) : clean;
    response = { seed: scenarioPlanningSeed(display), result: scenarioResultFromBatches(display, display.manualBatches ?? []) };
  } else if (request.action === "compose") {
    const composed = mergePersonalDraftWithWorld(request.draft, seed, Boolean(request.worldChanged));
    response = { seed: composed, result: scenarioResultFromBatches(composed, composed.manualBatches ?? []) };
  } else if (request.action === "publish") {
    const draft = request.draft;
    if (draft.planningResetVersion !== void 0 && draft.planningResetVersion !== 1) throw Error("Plan temizleme s\xFCr\xFCm\xFC desteklenmiyor. Uygulamay\u0131 yenileyin.");
    const reset = draft.planningResetVersion === 1;
    if (draft.productionArea && draft.productionArea !== (seed.productionArea ?? "torna")) throw Error("Plan ba\u015Fka bir \xFCretim alan\u0131na ait.");
    if (draft.planNeedsRecalculation) throw Error("Taslak g\xFCncel de\u011Fil. Ortak \xFCretimle plan\u0131 yeniden inceleyip \xE7al\u0131\u015Ft\u0131r\u0131n.");
    const next = mergePersonalDraftWithWorld(draft, seed);
    const official = scenarioPlanningSeed(cloneSeed(next));
    const candidate = scenarioPlanningSeed(cloneSeed(draft));
    for (const field of officialInputFields) {
      if (hash(officialInputValue(candidate, field)) !== hash(officialInputValue(official, field))) throw Error("Taslak sipari\u015F veya parametreleri ortak kay\u0131tla farkl\u0131. \xD6nce ortak girdilerle plan\u0131 yeniden inceleyin.");
    }
    for (const batch of seed.manualBatches ?? []) {
      if (!batch.routeCommitted || reset) continue;
      const proposal = draft.manualBatches?.find((row) => row.id === batch.id);
      const identity = (row) => lockedIdentity(reset && row ? withoutRouteChoices(row) : row);
      if (hash(identity(proposal)) !== hash(identity(batch))) throw Error(publicationProtectionMessage(reset ? withoutRouteChoices(batch) : batch, proposal));
    }
    if (next.planNeedsRecalculation) throw Error("Taslak kapsam\u0131 g\xFCncel de\u011Fil. Ortak verilerle plan\u0131 yeniden inceleyin.");
    next.processOperationOverrides = mergePublishedOverrides(draft, seed);
    const merged = next;
    const rebased = rebaseScenarioPlan(merged, scenarioResultFromBatches(merged, merged.manualBatches ?? []));
    if (rebased.overflows.length) throw Error("Plan penceresini a\u015Fan i\u015Fler var. Yay\u0131nlamadan \xF6nce plan\u0131 inceleyin.");
    merged.manualBatches = rebased.result.batches;
    const published = structuredClone(seed);
    for (const field of personalProposalFields) {
      if (Object.hasOwn(merged, field)) published[field] = structuredClone(merged[field]);
      else delete published[field];
    }
    published.planNeedsRecalculation = false;
    delete published.planningResetVersion;
    assertTurningIdentityTransition(seed, published);
    response = { seed: published, result: rebased.result };
  } else if (request.action === "command") {
    const command = request.command;
    if (!productionCommandNames.includes(command.kind) || !Array.isArray(command.args) || command.args.length > 8) throw Error("\xDCretim komutu ge\xE7ersiz.");
    if (hash(productionCommandBasis(seed, command)) !== request.expectedBasis && (seed.productionArea === "cubuk-filtre" || hash(legacyProductionCommandBasis(seed, command)) !== request.expectedBasis)) {
      process.stdout.write(JSON.stringify({ error: "\u0130lgili \xFCretim kayd\u0131 de\u011Fi\u015Fti. G\xFCncel kay\u0131tla i\u015Flemi yeniden inceleyin.", conflict: true }));
      process.exit(0);
    }
    const result = scenarioResultFromBatches(seed, seed.manualBatches ?? []);
    let orderReview;
    let accepted;
    const actions = createProductionActions({
      seed,
      result,
      setDirty: () => {
      },
      setOperationAlert: (alert) => {
        throw Error(alert.message);
      },
      commitOperationalChange: (nextSeed, nextResult, message, event) => {
        nextSeed.manualBatches = nextResult.batches;
        nextSeed.planNeedsRecalculation = planNeutralCommands.includes(command.kind) ? Boolean(seed.planNeedsRecalculation) : true;
        if (event) nextSeed.planningEvents = [{ ...event, id: crypto.randomUUID(), createdAt: (/* @__PURE__ */ new Date()).toISOString() }, ...nextSeed.planningEvents ?? []].slice(0, 200);
        accepted = { seed: nextSeed, result: nextResult, message };
      }
    });
    if (command.kind === "recordManualArchiveReceipt") {
      const next = recordManualArchiveReceipt(seed, command.args[0]);
      accepted = { seed: next, result: scenarioResultFromBatches(next, next.manualBatches ?? []), message: "Manuel adet kayd\u0131 olu\u015Fturuldu \xB7 plan\u0131 yeniden inceleyin" };
    } else if (command.kind === "deactivateParameters") {
      const input = command.args[0];
      let next = { seed: structuredClone(seed), result };
      for (const reviewed of input.targets) {
        const impact = parameterDeactivationImpact(next.seed, next.result, reviewed.target);
        if (impact.signature !== reviewed.signature) throw Error("Pasif atama incelemesi de\u011Fi\u015Fti. Yeniden inceleyin.");
        const keys = new Set(impact.queued.map((job) => job.key));
        next = applyParameterDeactivation(next.seed, next.result, reviewed.target, input.decisions.filter((decision) => keys.has(decision.key)), impact.signature);
      }
      next.seed = applyPlanningDelta(next.seed, input.delta);
      assertParameterTransitionDecided(seed, next.seed, next.result.batches);
      next.seed.manualBatches = next.result.batches;
      next.seed.planNeedsRecalculation = true;
      accepted = { ...next, message: "Pasif atama kararlar\u0131 kaydedildi" };
    } else if (command.kind === "reviseOfficialOrder") {
      const preview = previewOrderRevision(seed, result, command.args[0], "optimized");
      const next = structuredClone(seed);
      next.orders = preview.seed.orders;
      orderReview = { requested: command.args[0], impact: preview.impact };
      next.planNeedsRecalculation = true;
      accepted = { seed: next, result: scenarioResultFromBatches(next, next.manualBatches ?? []), message: "Resmi sipari\u015F revizyonu onayland\u0131 \xB7 plan\u0131 yeniden inceleyin" };
    } else if (command.kind === "cancelRemainingProduction") {
      const next = cancelRemainingProduction(seed, result, command.args[0]);
      accepted = { ...next, message: "Kalan \xFCretim iptal edildi" };
    } else if (command.kind === "reviewProductionCancellation") {
      const next = reviewProductionCancellation(seed, command.args[0], command.args[1]);
      accepted = { seed: next, result, message: "\u0130ptal sonras\u0131 inceleme kaydedildi" };
    } else {
      actions[command.kind](...command.args);
    }
    if (!accepted) throw Error("\xDCretim i\u015Flemi tamamlanmad\u0131.");
    assertTurningIdentityTransition(seed, accepted.seed);
    if (["reviseOfficialOrder", "deactivateParameters", "cancelRemainingProduction", "reviewProductionCancellation"].includes(command.kind)) {
      accepted.seed.planningEvents = [{ id: crypto.randomUUID(), createdAt: (/* @__PURE__ */ new Date()).toISOString(), type: "wip", message: accepted.message }, ...accepted.seed.planningEvents ?? []].slice(0, 200);
    }
    response = { ...accepted, orderReview };
  } else throw Error("\u0130\u015Flem ge\xE7ersiz.");
  process.stdout.write(JSON.stringify(response));
} catch (error) {
  process.stdout.write(JSON.stringify({ error: error instanceof Error ? error.message : "\u0130\u015Flem do\u011Frulanamad\u0131." }));
}
