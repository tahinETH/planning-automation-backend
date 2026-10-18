"use strict";

// scripts/scenario-plan-runtime.ts
var import_node_fs = require("node:fs");

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
var FAMILY_VALUES = /* @__PURE__ */ new Set(["center-pin", "piston"]);
var catalog = product_setup_families_default;
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

// lib/weekly-demand.ts
var NET_SHORTAGE_CALCULATION_MODEL = "net-shortage-v1";
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
var PRODUCT_PROCESS_ORDER = ["turning", "drilling", "deburring", "gkm"];
function productProcessRoute(product) {
  return product.route ?? ["turning", ...product.processes.slice().sort((a, b) => a.sequence - b.sequence).map((item) => item.process)];
}
var FOUNDATIONAL_PROCESS_MASTER_DATA = process_master_data_default;
function cloneFoundationalProcessMasterData() {
  return JSON.parse(JSON.stringify(FOUNDATIONAL_PROCESS_MASTER_DATA));
}
function processMasterDataForProduct(master, productCode) {
  const code = productCode.trim().toUpperCase();
  return master?.products.find((product) => product.product.toUpperCase() === code);
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
  return { turning: "Torna", drilling: "Delme", deburring: "\xC7apak alma", gkm: "GKM" }[process2];
}

// lib/process-waits.ts
function processWaitWorkdays(seed, process2) {
  const item = seed.processWaitSettings?.[process2];
  return item?.enabled ? item.workdays : 0;
}

// lib/production-interruptions.ts
function activeLotInterruptions(seed, lot) {
  return (seed.productionInterruptions ?? []).filter((item) => isProductionInterruption(item) && !item.completedAt && lot?.interruptionIds?.includes(item.id));
}
function isProductionInterruption(item) {
  return item.producedQuantity !== 0 && item.kind !== "partial-completion";
}
function hasActiveProductionInterruption(seed, chargeId, interruptionId) {
  const records = seed.productionInterruptions ?? [];
  if (records.some((item) => isProductionInterruption(item) && !item.completedAt && (Boolean(chargeId && item.chargeId === chargeId) || item.id === interruptionId))) return true;
  return Boolean(interruptionId && !records.some((item) => item.id === interruptionId));
}

// lib/delivery-calendar.ts
var EXCEL_EPOCH = Date.UTC(1899, 11, 30);
var DAY_MS = 864e5;
function dayOfWeek(serial) {
  return new Date(EXCEL_EPOCH + Math.floor(serial) * DAY_MS).getUTCDay();
}
function isFactoryWorkday(seed, serialValue) {
  const serial = Math.floor(serialValue);
  const addedShift = (seed.calendarEvents ?? []).some(
    (event) => event.kind === "shift" && event.shiftCount > 0 && serial >= Math.floor(event.start) && serial <= Math.floor(event.end)
  );
  if (addedShift) return true;
  const holiday = seed.holidays.find((item) => Math.floor(item.serial) === serial);
  if (holiday) return (holiday.workingShifts ?? 0) > 0;
  return dayOfWeek(serial) !== 0;
}
function addFactoryWorkdays(seed, startValue, workdaysValue) {
  if (!Number.isFinite(startValue) || startValue <= 0) return startValue;
  const workdays = Math.max(0, Math.trunc(workdaysValue));
  if (!workdays) return startValue;
  let serial = Math.floor(startValue);
  let remaining = workdays;
  while (remaining > 0) {
    serial += 1;
    if (isFactoryWorkday(seed, serial)) remaining -= 1;
  }
  return serial;
}
function routedDeliveryReadyAt(seed, routeCompletionSerial, family, lastProcess = "gkm") {
  const rule = family ? flowRule(seed, family, lastProcess, "delivery") : void 0;
  if (rule?.mode === "static") return addDepartmentWorkMinutes(seed, routeCompletionSerial, rule.minutes);
  return addFactoryWorkdays(seed, routeCompletionSerial, processWaitWorkdays(seed, lastProcess));
}

// lib/wip-ledger.ts
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
function hydrateWipFromProductionHistory(seed) {
  seed.wipLots = seed.wipLots ?? [];
  seed.wipMovements = seed.wipMovements ?? [];
  for (const entry of seed.productionHistory ?? []) registerTurningCompletion(seed, entry, entry.statusChangedAt || entry.archivedAt, false);
}
function applyCustomRouteProgress(seed, lot, process2, completedAt) {
  const product = processMasterDataForProduct(seed.processMasterData, lot.product);
  const next = product.route[product.route.indexOf(process2) + 1];
  if (next && next !== "turning") {
    const parameter = product.processes.find((item) => item.process === next);
    lot.nextProcess = next;
    lot.stage = next === "drilling" ? processWaitWorkdays(seed, process2) > 0 ? "quality-hold" : "drilling-queue" : next === "deburring" ? "deburring-queue" : processWaitWorkdays(seed, process2) > 0 ? "gkm-buffer" : "gkm-queue";
    lot.readyAt = addWipWaitWorkdays(seed, completedAt, processWaitWorkdays(seed, process2));
  } else {
    lot.stage = "delivery-ready";
    delete lot.nextProcess;
    lot.readyAt = routedDeliveryReadyAt(seed, completedAt, void 0, process2);
  }
}
function applyCompletedFlow(seed, lot, process2, completedAt) {
  const rule = flowRule(seed, lot.family, process2, lot.nextProcess ?? "delivery");
  if (!rule) return;
  lot.readyAt = rule.mode === "static" ? addDepartmentWorkMinutes(seed, completedAt, rule.minutes) : completedAt;
  if (lot.nextProcess === "drilling") lot.stage = lot.readyAt > completedAt ? "quality-hold" : "drilling-queue";
  if (lot.nextProcess === "gkm") lot.stage = lot.readyAt > completedAt ? "washing-buffer" : "gkm-queue";
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
function inputDateToSerial(value) {
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
  const copy = JSON.parse(JSON.stringify(seed));
  if (copy.flowSettings !== void 0) copy.flowSettings = validateFlowSettings(copy.flowSettings);
  if (copy.productWeights === void 0) copy.productWeights = initialProductWeights();
  if (copy.rawMaterialSettings === void 0) copy.rawMaterialSettings = initialRawMaterialSettings();
  const previousSchemaVersion = Number(copy.schemaVersion ?? 0);
  if (previousSchemaVersion < 21 && copy.manualBatches?.length) copy.planNeedsRecalculation = true;
  if (previousSchemaVersion < 22 && copy.flowSettings?.enabled && copy.processWaitSettings && copy.manualBatches?.length) copy.planNeedsRecalculation = true;
  copy.schemaVersion = CURRENT_PLANNING_SCHEMA_VERSION;
  if (previousSchemaVersion < PROCESS_MASTER_DATA_VERSION || !copy.processMasterData) {
    copy.processMasterData = cloneFoundationalProcessMasterData();
  }
  if (copy.processMasterData) {
    copy.processMasterData.products = copy.processMasterData.products.map((product) => ({
      ...product,
      productGroup: product.productGroup?.trim() || product.family
    }));
    copy.processMasterData.planningStrategies = {
      drilling: copy.processMasterData.planningStrategies?.drilling ?? "campaign",
      deburring: copy.processMasterData.planningStrategies?.deburring ?? "earliest-ready",
      gkm: copy.processMasterData.planningStrategies?.gkm ?? "earliest-ready"
    };
    copy.processMasterData.transferBatchQuantities = {
      ...copy.processMasterData.transferBatchQuantities,
      drilling: copy.processMasterData.transferBatchQuantities?.drilling ?? 100
    };
    if (previousSchemaVersion < DRILLING_TRANSFER_FLOW_VERSION) {
      copy.processMasterData.products = copy.processMasterData.products.map((product) => ({
        ...product,
        processes: product.processes.map((parameter) => parameter.process === "drilling" ? { ...parameter, waitWorkdaysBefore: 0 } : parameter)
      }));
    }
    copy.processMasterData.resources = copy.processMasterData.resources.map((resource) => {
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
  copy.processOperationOverrides = (copy.processOperationOverrides ?? []).filter(
    (override) => Boolean(override.batchId && override.process && override.resourceId && Number.isFinite(override.requestedStart) && override.requestedStart > 0)
  );
  copy.products = copy.products.map((product) => {
    const setupFamily = resolvedProductSetupFamily(product.product, product.setupFamily);
    return setupFamily ? { ...product, setupFamily } : product;
  });
  if (previousSchemaVersion < DOOSAN_ALTERNATIVE_CONFIGURATION_VERSION) {
    const productCodes = ["R902970277", "R902719742", "R902970964"];
    const machineIds = ["C-11", "C-12", "C-08"];
    for (const productCode of productCodes) {
      const product = copy.products.find((item) => item.product.toUpperCase() === productCode);
      const fallbackShiftRate = machineIds.map((machineId) => Number(copy.machines.find((machine) => machine.id === machineId)?.rates[productCode]) || 0).find((rate) => rate > 0) ?? (Number(product?.shiftRate) > 0 ? Number(product?.shiftRate) : Number(product?.dailyRate) / 3);
      const preference = copy.preferences.find((item) => item.key.toUpperCase() === productCode);
      const repairedPreference = {
        key: productCode,
        machines: [...machineIds],
        ruleType: "operational-alternative",
        description: "C-11 ve C-12 i\xE7in C-08 Doosan alternatif tezgah\u0131",
        source: "Operasyon karar\u0131 \xB7 2026-08-27"
      };
      if (preference) Object.assign(preference, repairedPreference);
      else copy.preferences.push(repairedPreference);
      if (product) {
        product.eligibleMachines = [...machineIds];
        product.alternativeMachines = [...machineIds];
      }
      if (fallbackShiftRate > 0) {
        for (const machineId of machineIds) {
          const machine = copy.machines.find((item) => item.id === machineId);
          if (machine && !(Number(machine.rates[productCode]) > 0)) machine.rates[productCode] = fallbackShiftRate;
        }
      }
    }
  }
  if (previousSchemaVersion < PRODUCT_FAMILY_SETUP_VERSION) {
    const legacy = copy.setupSettings;
    copy.setupSettings = {
      model: "product-family",
      shiftHours: Number.isFinite(legacy?.shiftHours) ? Number(legacy?.shiftHours) : 8,
      sameDiameterHours: 1,
      differentDiameterHours: Number.isFinite(legacy?.differentDiameterHours) ? Number(legacy?.differentDiameterHours) : 3,
      sameFamilyDifferentDiameterHours: 2,
      crossFamilyHours: 5
    };
  }
  copy.orders = copy.orders.map((order) => ({
    ...order,
    periodId: isPeriodId(order.periodId) ? order.periodId : fallbackPeriod
  }));
  if (Array.isArray(copy.demandTargets)) {
    copy.demandTargets = copy.demandTargets.map((target) => ({
      ...target,
      periodId: isPeriodId(target.periodId) ? target.periodId : fallbackPeriod
    }));
  }
  copy.customerOrderOverrides = (copy.customerOrderOverrides ?? []).map((override) => ({
    product: String(override.product ?? "").trim().toUpperCase(),
    quantity: Math.max(0, Math.trunc(Number(override.quantity) || 0)),
    dueDate: String(override.dueDate ?? "").trim(),
    updatedAt: String(override.updatedAt ?? "")
  })).filter((override) => Boolean(override.product));
  copy.productionHistory = (copy.productionHistory ?? []).map((entry) => ({
    ...entry,
    process: entry.process ?? "turning",
    inventoryStatus: entry.inventoryStatus ?? "semi-finished",
    statusChangedAt: entry.statusChangedAt ?? entry.archivedAt
  }));
  copy.wipLots = (copy.wipLots ?? []).map((lot) => {
    const completedSteps = lot.completedSteps ?? [];
    const lastStep = completedSteps.at(-1);
    const legacyRouteReadyAt = previousSchemaVersion < FACTORY_ROUTE_CALENDAR_VERSION && lot.stage === "delivery-ready" && lastStep?.process === "gkm" ? addFactoryWorkdays(copy, lastStep.end, 1) : lot.readyAt;
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
  copy.productionInterruptions = copy.productionInterruptions ?? [];
  copy.wipMovements = copy.wipMovements ?? [];
  copy.chargeJourneyNotes = (copy.chargeJourneyNotes ?? []).filter((note) => Boolean(note.chargeKey && note.segmentId && note.note?.trim()));
  if (previousSchemaVersion < WIP_LEDGER_VERSION || !copy.wipLots.length) hydrateWipFromProductionHistory(copy);
  const activeScopeStart = copy.activePlanRun?.scope.kind === "customer-weeks" ? inputDateToSerial(copy.activePlanRun.scope.startDate) : 0;
  copy.machines = copy.machines.map((machine) => {
    if (Number.isFinite(machine.operationalAvailableStart)) return machine;
    let operationalAvailableStart = machine.availableStart;
    if (previousSchemaVersion < OPERATIONAL_AVAILABILITY_VERSION && activeScopeStart > 0) {
      const currentJobEnd = Number(machine.currentJob?.end) || 0;
      operationalAvailableStart = currentJobEnd > 0 ? Math.min(machine.availableStart, currentJobEnd) : Math.min(machine.availableStart, activeScopeStart);
    }
    return { ...machine, operationalAvailableStart };
  });
  if (copy.customerDemand) {
    const previousDemand = copy.customerDemand;
    copy.customerDemand = normalizeCustomerDemandDataset(copy.customerDemand);
    const dateReplacements = new Map([
      [previousDemand.baselineDueDate, copy.customerDemand.baselineDueDate],
      ...previousDemand.weeks.map((week, index) => [week.weekEnd, copy.customerDemand.weeks[index]?.weekEnd ?? week.weekEnd])
    ]);
    const overriddenProducts = new Set(copy.customerOrderOverrides.map((override) => override.product));
    const normalizedCustomerDate = (orderId, value) => dateReplacements.get(value) ?? (orderId.startsWith("confirmed-") ? previousSaturdayIfSunday(value) : value);
    copy.orders = copy.orders.map((order) => overriddenProducts.has(order.product.toUpperCase()) ? order : {
      ...order,
      dueDate: normalizedCustomerDate(order.id, order.dueDate),
      partialDeliveryDate: normalizedCustomerDate(order.id, order.partialDeliveryDate),
      deliveryMilestones: order.deliveryMilestones?.map((milestone) => ({
        ...milestone,
        date: normalizedCustomerDate(order.id, milestone.date)
      }))
    });
    if (previousSchemaVersion < CUSTOMER_DEMAND_PLAN_RESET_VERSION) {
      copy.manualBatches = [];
      copy.activePlanRun = void 0;
      copy.planRunSequence = void 0;
      copy.lastAutomaticPlan = void 0;
    }
  }
  copy.openingStock = copy.customerDemand ? {} : Object.entries(copy.openingStock ?? {}).reduce((stock, [product, quantity]) => {
    const code = product.trim().toUpperCase();
    const normalizedQuantity = Math.max(0, Number(quantity) || 0);
    if (code && normalizedQuantity > 0) stock[code] = normalizedQuantity;
    return stock;
  }, {});
  const existingScope = copy.activePlanningScope;
  copy.activePlanningScope = existingScope && isPeriodId(existingScope.startPeriod) && isPeriodId(existingScope.endPeriod) ? normalizePlanningScope(existingScope) : { startPeriod: fallbackPeriod, endPeriod: fallbackPeriod };
  return copy;
}

// lib/planning.ts
function excelSerialToDate(serial) {
  return new Date(Date.UTC(1899, 11, 30) + serial * 864e5);
}
function shiftCount(value) {
  if (!Number.isFinite(value)) return 0;
  return Math.max(0, Math.min(3, Math.trunc(value)));
}
function machineDayCapacity(seed, machine, serialValue) {
  const serial = Math.floor(serialValue);
  const events = (seed.calendarEvents ?? []).filter((event) => event.machineId === machine.id && serial >= Math.floor(event.start) && serial <= Math.floor(event.end));
  const maintenance = events.find((event) => event.kind === "maintenance");
  if (maintenance) return { shifts: 0, kind: "maintenance", label: maintenance.name || "Planl\u0131 bak\u0131m" };
  const shiftOverride = [...events].reverse().find((event) => event.kind === "shift");
  if (shiftOverride) return { shifts: shiftCount(shiftOverride.shiftCount), kind: "shift", label: shiftOverride.name || "Vardiya de\u011Fi\u015Fikli\u011Fi" };
  const holiday = seed.holidays.find((item) => Math.floor(item.serial) === serial);
  if (holiday) {
    const shifts = shiftCount(holiday.workingShifts);
    return { shifts, kind: "holiday", label: shifts ? `${holiday.name} \xB7 ${shifts} vardiya` : holiday.name };
  }
  if (excelSerialToDate(serial).getUTCDay() === 0) return { shifts: 0, kind: "sunday", label: "Pazar \xB7 \xFCretim yok" };
  return { shifts: shiftCount(machine.shiftFactor), kind: "normal", label: `${shiftCount(machine.shiftFactor)} vardiya` };
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
function addMachineCapacityHours(seed, machine, startValue, hoursValue) {
  let cursor = Math.max(0, startValue);
  let remaining = Math.max(0, hoursValue);
  let actualStart = 0;
  let guard = 0;
  const shiftHours = getSetupSettings(seed).shiftHours;
  while (remaining > 0 || !actualStart) {
    const day = Math.floor(cursor);
    const capacityHours = machineDayCapacity(seed, machine, day).shifts * shiftHours;
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
function currentJobRouteIdentity(machine) {
  const job = machine.currentJob;
  return JSON.stringify(job.batchId ? [machine.id, job.batchId, job.product] : [machine.id, job.product, job.workOrder, job.start, job.originalQuantity ?? job.quantity]);
}

// lib/process-flow.ts
function curve(seed, resource, start, end, setupHours, quantity) {
  const windows = [];
  let setup = setupHours, hours = 0;
  if (end - start > 36600 || end <= start || quantity <= 0) return void 0;
  for (let day = Math.floor(start); day <= Math.floor(end); day += 1) {
    const shifts = machineDayCapacity(seed, resource, day).shifts;
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
  const segments = windows.map((window) => {
    const segment = { ...window, before, rate };
    before += (window.end - window.start) * rate;
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
  const schedule = (start) => addMachineCapacityHours(calendarSeed, machine, start, setupHours + runHours);
  const targetEnd = predecessor.end + targetMinutes / 1440;
  const upstream = predecessor.process === "turning" ? seed.machines.find((item) => item.id === predecessor.resourceId) : seed.processMasterData?.resources.find((item) => item.id === predecessor.resourceId);
  const upstreamCalendar = predecessor.resourceId.startsWith("B-01-") ? { ...seed, calendarEvents: seed.calendarEvents?.map((event) => event.machineId === "B-01" ? { ...event, machineId: predecessor.resourceId } : event) } : seed;
  const supply = upstream && !predecessor.current && !(predecessor.process === "turning" && predecessor.source === "current-turning") && !predecessor.actual && predecessor.quantity === quantity ? curve(upstreamCalendar, { id: upstream.id, shiftFactor: "shiftFactor" in upstream ? upstream.shiftFactor : upstream.defaultShifts }, predecessor.start, predecessor.end, predecessor.setupHours, quantity) : void 0;
  if (!supply) return { ...schedule(Math.max(requestedStart, predecessor.end)), targetEnd, reason: "\xD6nceki prosesin g\xFCvenilir par\xE7a \xE7\u0131k\u0131\u015F e\u011Frisi yok; kay\u0131tl\u0131 biti\u015F sonras\u0131 g\xFCvenli ba\u015Flang\u0131\xE7 kullan\u0131ld\u0131." };
  const safe = (start) => {
    const timing = schedule(start);
    const consumption = curve(calendarSeed, machine, timing.start, timing.end, setupHours, quantity);
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

// lib/process-route-state.ts
function describeProcessRoute(seed, job, warnings) {
  const product = processMasterDataForProduct(seed.processMasterData, job.product);
  if (!product) return { routeSteps: [], readinessIssues: [{ code: "missing-product", message: "\xDCr\xFCn rotas\u0131 bulunamad\u0131; miktar korunuyor." }] };
  const route = productProcessRoute(product);
  const lot = seed.wipLots?.find((l) => l.id === job.wipLotId);
  const chargeId = job.source === "current-turning" ? seed.machines?.find((m) => m.id === job.turningMachineId)?.currentJob.batchId : job.batchId;
  const pause = seed.productionInterruptions?.find((p) => isProductionInterruption(p) && !p.completedAt && p.chargeId === chargeId);
  const partial = activeLotInterruptions(seed, lot).length > 0;
  const issues = [];
  const routeSteps = route.map((process2) => {
    const op = job.operations.find((o) => (o.recordedProcess ?? o.process) === process2);
    const base = { process: process2, quantity: job.quantity, operationId: op?.id, resourceId: op?.resourceId };
    if (op?.actual) return { ...base, state: "completed" };
    if (op?.current || job.source === "current-turning" && process2 === "turning" || seed.processCurrentJobs?.some((current) => current.batchId === job.batchId && current.process === process2)) return { ...base, state: "running" };
    if (op) return { ...base, state: "scheduled" };
    let state = "capacity-blocked";
    let message = `${processLabel(process2)} i\xE7in tarih hesaplanamad\u0131; kapasite ve kay\u0131tl\u0131 yerle\u015Fimi kontrol edin.`;
    let code = state;
    if (lot?.stage === "on-hold" || lot?.stage === "unclassified") {
      code = lot.stage === "on-hold" ? "held" : "unclassified";
      state = "predecessor-pending";
      message = lot.stage === "on-hold" ? "Yar\u0131 mam\xFCl blokeli." : "Yar\u0131 mam\xFCl\xFCn ger\xE7ek konumu do\u011Frulanmal\u0131.";
    } else if (pause && route.indexOf(process2) >= route.indexOf(pause.process)) {
      state = process2 === pause.process ? "paused" : "predecessor-pending";
      code = state;
      message = process2 === pause.process ? "Ara verilen i\u015F kuyrukta korunuyor." : "Ara verilen \xF6nceki prosesin tamamlanmas\u0131 bekleniyor.";
    } else if (partial) {
      state = process2 === lot?.nextProcess ? "manual-required" : "predecessor-pending";
      code = state;
      message = state === "manual-required" ? "Yar\u0131m \xFCretim: bu prosesi Manuel \u015Farj ile kuyru\u011Fa ekleyin." : "\xD6nceki proses ve manuel \xFCretim onay\u0131 bekleniyor.";
    } else if (warnings.some((w) => w.product === job.product && (w.code === "invalid-route" || w.code === "missing-parameter" && !w.batchId))) {
      state = "invalid-route";
      code = state;
      message = "\xDCr\xFCn rotas\u0131 veya proses parametreleri eksik.";
    } else if (route.indexOf(process2) > 0 && !job.operations.some((o) => (o.recordedProcess ?? o.process) === route[route.indexOf(process2) - 1])) {
      state = "predecessor-pending";
      code = state;
      message = "\xD6nceki prosesin haz\u0131r olma tarihi belirlenemedi.";
    }
    issues.push({ code, message, process: process2 });
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
    if (seed.processCurrentJobs?.some((c) => c.batchId === job.batchId && c.process === intent.process)) continue;
    const op = operations.find((o) => o.batchId === job.batchId && o.process === intent.process && !o.actual && !o.current);
    rows.set(`${job.batchId}:${intent.process}`, { id: `${job.batchId}:${intent.process}`, batchId: job.batchId, product: job.product, workOrder: job.workOrder, quantity: job.quantity, process: intent.process, resourceId: intent.resourceId, scheduled: Boolean(op), operationId: op?.id, reason: op ? void 0 : step?.reason ?? "Kay\u0131tl\u0131 i\u015F i\xE7in tarih hesaplanamad\u0131; rota ve kapasiteyi kontrol edin.", queueOrder: intent.queueOrder ?? Number.MAX_SAFE_INTEGER, resumeAfterCurrent: Boolean(intent.resumeAfterCurrent) });
  }
  return [...rows.values()].sort((a, b) => Number(b.resumeAfterCurrent) - Number(a.resumeAfterCurrent) || a.queueOrder - b.queueOrder || a.id.localeCompare(b.id));
}

// lib/process-planning.ts
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
    if (product.route && (!product.route.length || product.route.join("|") !== PRODUCT_PROCESS_ORDER.filter((process2) => product.route.includes(process2)).join("|"))) warnings.push({ code: "invalid-route", product: product.product, message: `${product.product} aktif proses s\u0131ras\u0131 ge\xE7ersiz.` });
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
    runHours: Math.max(0, (step.end - step.start) * 24),
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
  const identities = [batchId];
  const sourceBatchIds = /* @__PURE__ */ new Set();
  let lot = seed.wipLots?.find((item) => item.id === batchId);
  const machine = seed.machines?.find((item) => `current:${item.id}` === batchId);
  const visited = /* @__PURE__ */ new Set();
  while (allowInheritance && lot && !visited.has(lot.id)) {
    visited.add(lot.id);
    if (lot.sourceBatchId) sourceBatchIds.add(lot.sourceBatchId);
    if (lot.parentLotId) identities.push(lot.parentLotId);
    lot = seed.wipLots?.find((item) => item.id === lot.parentLotId);
  }
  identities.push(...sourceBatchIds);
  if (allowInheritance && machine?.currentJob.batchId) identities.push(machine.currentJob.batchId);
  return identities.flatMap((id) => seed.processOperationOverrides?.filter((item) => item.batchId === id && item.process === process2 && (!item.sourceProduct || item.sourceProduct === product) && (!item.sourceCurrentJobKey || machine && currentJobRouteIdentity(machine) === item.sourceCurrentJobKey)) ?? [])[0];
}
var inputDateSerial = (value) => value ? (Date.parse(`${value}T00:00:00Z`) - Date.UTC(1899, 11, 30)) / 864e5 : 0;
function sourceDueSerial(seed, source) {
  const own = source.batch?.demandDueDate ? inputDateSerial(source.batch.demandDueDate) : 0;
  if (own > 0) return own;
  const dates = seed.orders.filter((order) => order.product.toUpperCase() === source.product.toUpperCase() && order.quantity > 0 && order.dueDate).map((order) => inputDateSerial(order.dueDate)).filter((value) => value > 0);
  return dates.length ? Math.min(...dates) : void 0;
}
function scheduleStage(seed, master, process2, sources, operationsByKey, warnings, includeInterruptedCandidates = false, continuationControl = { enabled: false, used: false }) {
  const queueByResource = /* @__PURE__ */ new Map();
  const usableResources = (source, parameter) => activeProcessResourceIds(parameter).filter((id) => {
    const resource = processResource(master, id);
    return resource?.active && resource.process === process2 && resource.defaultShifts > 0 && resourceSupportsProcessProduct(resource, source.masterProduct) && parameter.unitsPerShift[id] > 0;
  });
  const strategy = master.planningStrategies?.[process2] ?? (process2 === "drilling" ? "campaign" : "earliest-ready");
  const candidates = sources.flatMap((source) => {
    if (!source.nextProcess) return [];
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
    const explicitPlacement = seed.processOperationOverrides?.some((item) => item.batchId === source.id && item.process === process2);
    const running = seed.processCurrentJobs?.some((item) => item.batchId === source.id && item.process === process2);
    if (seed.productionInterruptions?.some((item) => isProductionInterruption(item) && !item.completedAt && item.chargeId === source.id && item.process === source.nextProcess) && !firstRemaining) return [];
    if (interrupted && !running && !explicitPlacement && !(includeInterruptedCandidates && firstRemaining)) return [];
    if (!predecessor && !firstRemaining) {
      warnings.push({ code: "missing-parameter", product: source.product, batchId: source.id, message: `${source.product} \xB7 ${process2} i\xE7in \xF6nceki rota ad\u0131m\u0131 bulunamad\u0131.` });
      return [];
    }
    const effectiveWaitWorkdays = firstRemaining && source.source === "wip" ? 0 : processWaitWorkdays(seed, predecessorProcess);
    const rule = flowRule(seed, source.masterProduct.family, predecessorProcess, process2);
    const legacyReadyAt = firstRemaining && source.source === "wip" ? source.releaseAt : addProcessWaitWorkdays(seed, predecessor?.end ?? source.releaseAt, effectiveWaitWorkdays);
    const usesRule = rule && !(firstRemaining && source.source === "wip");
    const readyAt = usesRule ? rule.mode === "static" ? addDepartmentWorkMinutes(seed, predecessor?.end ?? source.releaseAt, rule.minutes) : predecessor?.start ?? source.releaseAt : legacyReadyAt;
    const storedOverride = processPlacementOverride(seed, source.id, source.product, process2, !interrupted);
    const override = storedOverride?.routeMode === "automatic" ? void 0 : storedOverride?.routeMode === "priority" ? { ...storedOverride, requestedStart: readyAt } : storedOverride;
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
    const currentEnds = (id, item) => seed.productionArea === "cubuk-filtre" ? [] : (seed.processCurrentJobs ?? []).filter((job) => job.resourceId === id && job.batchId !== item.source.id).map((job) => job.end);
    const machineFree = (item) => process2 === "drilling" ? Math.min(...usableResources(item.source, item.parameter).map((id) => Math.max(processResource(master, id)?.availableStart ?? 0, ...currentEnds(id, item))), Number.POSITIVE_INFINITY) : 0;
    const leftScheduleAt = Math.max(left.readyAt, left.override?.requestedStart ?? left.readyAt, Number.isFinite(machineFree(left)) ? machineFree(left) : 0);
    const rightScheduleAt = Math.max(right.readyAt, right.override?.requestedStart ?? right.readyAt, Number.isFinite(machineFree(right)) ? machineFree(right) : 0);
    const leftOrder = left.override?.queueOrder ?? Number.MAX_SAFE_INTEGER;
    const rightOrder = right.override?.queueOrder ?? Number.MAX_SAFE_INTEGER;
    if (leftOrder !== rightOrder) return leftOrder - rightOrder;
    if (Math.abs(leftScheduleAt - rightScheduleAt) > 1e-8) return leftScheduleAt - rightScheduleAt;
    const rank = (source) => source === "wip" ? 0 : source === "current-turning" ? 1 : 2;
    if (process2 !== "drilling" && left.source.source !== right.source.source) return rank(left.source.source) - rank(right.source.source);
    if (process2 === "drilling") {
      if (Boolean(left.override) !== Boolean(right.override)) return left.override ? -1 : 1;
      const leftDue = sourceDueSerial(seed, left.source) ?? Number.MAX_SAFE_INTEGER;
      const rightDue = sourceDueSerial(seed, right.source) ?? Number.MAX_SAFE_INTEGER;
      if (leftDue !== rightDue) return leftDue - rightDue;
      const feeds = (item) => productProcessRoute(item.source.masterProduct).includes("deburring") ? 0 : 1;
      if (feeds(left) !== feeds(right)) return feeds(left) - feeds(right);
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
  for (const item of candidates) {
    const { source, parameter, predecessor, readyAt, override, currentJob, effectiveWaitWorkdays, waitRuleLabel, rule } = item;
    const nextSetup = { product: source.product, family: source.masterProduct.family, setupKey: parameter.setupKey };
    const activeResources = activeProcessResourceIds(parameter);
    const resourceCandidates = currentJob ? [currentJob.resourceId] : override ? activeResources.filter((id) => id === override.resourceId) : activeResources;
    const evaluated = resourceCandidates.flatMap((resourceId, priority) => {
      const resource = processResource(master, resourceId);
      const unitsPerShift = parameter.unitsPerShift[resourceId];
      if (!resource || resource.process !== process2 || !resource.active || resource.defaultShifts <= 0 || !resourceSupportsProcessProduct(resource, source.masterProduct) || !Number.isFinite(unitsPerShift) || unitsPerShift <= 0) return [];
      const queue = queueByResource.get(resourceId);
      const setup = calculateDownstreamSetup(process2, queue, nextSetup, seed.flowSettings);
      if (!Number.isFinite(setup.hours)) return [];
      const runHours = currentJob ? Math.max(0, (currentJob.end - currentJob.start) * 24 - currentJob.setupHours) : source.quantity / unitsPerShift * getSetupSettings(seed).shiftHours;
      const requestedStart = Math.max(readyAt, queue?.tail ?? readyAt, override?.requestedStart ?? readyAt, currentJob ? readyAt : resource.availableStart ?? readyAt);
      const timeline = currentJob ? { start: currentJob.start, end: currentJob.end } : rule?.mode === "dynamic" && predecessor ? dynamicFlowTiming(seed, processCalendarSeed(seed, resource.id), resource, predecessor, requestedStart, setup.hours, runHours, source.quantity, rule.minutes) : addMachineCapacityHours(
        processCalendarSeed(seed, resource.id),
        { id: resource.id, shiftFactor: resource.defaultShifts, finishOffset: 0 },
        requestedStart,
        setup.hours + runHours
      );
      const options = [{ resource, unitsPerShift, setupHours: setup.hours, protectedSetupHoursAfter: 0, runHours, priority, gapIndex: -1, previousOperation: void 0, ...timeline }].filter((option) => currentJob || !resource.planEnd || option.end <= Math.floor(resource.planEnd) + 1 + 1e-8);
      if (!currentJob && process2 === "drilling") {
        const reservations = scheduled.filter((operation2) => operation2.resourceId === resource.id).sort((left, right) => left.start - right.start || left.end - right.end || left.id.localeCompare(right.id));
        const currentEnd = Math.max(0, ...reservations.filter((operation2) => operation2.current).map((operation2) => operation2.end));
        const gaps = reservations.map((nextReservation, index) => ({
          nextReservation,
          previousOperation: reservations[index - 1],
          cursor: Math.max(reservations[index - 1]?.end ?? 0, currentEnd),
          tail: reservations[index - 1] ? setupSourceForOperation(reservations[index - 1]) : void 0
        }));
        const calendarSeed = processCalendarSeed(seed, resource.id);
        for (const [gapIndex, gap] of gaps.entries()) {
          const nextOverride = processPlacementOverride(seed, gap.nextReservation.batchId, gap.nextReservation.product, process2);
          if (override?.queueOrder !== void 0 && nextOverride?.queueOrder !== void 0 && override.queueOrder > nextOverride.queueOrder) continue;
          const incomingSetup = calculateDownstreamSetup(process2, gap.tail, nextSetup, seed.productionArea === "cubuk-filtre" ? void 0 : seed.flowSettings);
          const gapStart = Math.max(readyAt, gap.cursor, override?.requestedStart ?? readyAt, resource.availableStart ?? readyAt);
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
    const earliestFinish = evaluated[0];
    const preferred = process2 === "drilling" && !currentJob && !override && earliestFinish ? evaluated.filter((option) => option.start <= earliestFinish.start + 1e-8).sort((left, right) => left.priority - right.priority || left.end - right.end || left.resource.id.localeCompare(right.resource.id))[0] : earliestFinish;
    const due = sourceDueSerial(seed, source);
    const continuation = continuationControl.enabled && process2 === "drilling" && !currentJob && !override && preferred && due !== void 0 && queueByResource.get(preferred.resource.id)?.product !== source.product ? evaluated.filter((option) => option.gapIndex < 0 && (queueByResource.get(option.resource.id)?.product === source.product || Boolean(pinnedProducts.get(option.resource.id)?.has(source.product)))).sort((left, right) => left.end - right.end || left.priority - right.priority)[0] : void 0;
    if (continuation && continuation !== preferred) continuationControl.used = true;
    const chosen = continuation ?? preferred;
    if (!chosen) {
      warnings.push({ code: "missing-resource", product: source.product, batchId: source.id, message: `${source.product} \xB7 ${process2} i\xE7in kullan\u0131labilir i\u015F merkezi veya vardiya kapasitesi yok.` });
      continue;
    }
    const operation = {
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
    scheduled.push(operation);
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
function processLabelForError(process2) {
  return process2 === "turning" ? "torna" : process2 === "drilling" ? "delme" : process2 === "deburring" ? "\xE7apak alma" : "GKM";
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
      let code = "no-eligible-wip";
      let message = `Bu aral\u0131kta ${resource.id} i\xE7in uygun ve haz\u0131r yar\u0131 mam\xFCl yoktu; s\u0131radaki i\u015F ${next.product} oldu.`;
      if (next.readyAt > previous.end + 1e-8) {
        if (next.waitWorkdaysBefore > 0) {
          code = "route-wait";
          message = `${next.product}, rota gere\u011Fi ${next.waitWorkdaysBefore} i\u015F g\xFCn\xFC bekledikten sonra ${resource.id} i\xE7in haz\u0131r oldu.`;
        } else {
          code = "upstream-not-ready";
          message = `${next.product} \xF6nceki operasyonu tamamlanmad\u0131\u011F\u0131 i\xE7in bu aral\u0131kta ${resource.id} \xFCzerinde ba\u015Flat\u0131lamad\u0131.`;
        }
      } else {
        const calendarSeed = processCalendarSeed(seed, resource.id);
        const startDay = Math.floor(previous.end);
        const endDay = Math.floor(next.start);
        const days = Array.from({ length: Math.max(1, endDay - startDay + 1) }, (_, offset) => startDay + offset);
        const closed = days.map((serial) => ({ serial, capacity: machineDayCapacity(calendarSeed, { id: resource.id, shiftFactor: resource.defaultShifts }, serial) })).find(({ capacity }) => capacity.shifts === 0);
        if (closed) {
          code = closed.capacity.kind === "maintenance" ? "maintenance" : closed.capacity.kind === "shift" ? "zero-shift" : "closed-day";
          message = `${closed.capacity.label} nedeniyle ${resource.id} kapasitesi kapal\u0131yd\u0131; i\u015F ilk \xE7al\u0131\u015F\u0131labilir zamana ta\u015F\u0131nd\u0131.`;
        } else {
          const capacity = machineDayCapacity(calendarSeed, { id: resource.id, shiftFactor: resource.defaultShifts }, startDay);
          const windowEnd = startDay + capacity.shifts * shiftHours / 24;
          if (capacity.shifts > 0 && previous.end >= windowEnd - 1e-8) {
            code = "daily-capacity";
            message = `${resource.id} i\xE7in g\xFCnl\xFCk ${capacity.shifts} vardiyal\u0131k kapasite doldu; s\u0131radaki i\u015F bir sonraki \xE7al\u0131\u015Fma penceresinde ba\u015Flad\u0131.`;
          }
        }
      }
      gaps.push({ id: `${resource.id}:${previous.id}:${next.id}`, process: resource.process, resourceId: resource.id, start: previous.end, end: next.start, code, message });
    }
  }
  return gaps;
}
function buildDownstreamProcessPlan(seed, result, includeInterruptedCandidates = false) {
  const control = { enabled: seed.productionArea !== "cubuk-filtre", used: false };
  const consolidated = buildDownstreamProcessPlanWith(seed, result, includeInterruptedCandidates, control);
  if (!control.used) return consolidated;
  const spread = buildDownstreamProcessPlanWith(seed, result, includeInterruptedCandidates, { enabled: false, used: false });
  const a = onTimeScore(seed, result, consolidated), b = onTimeScore(seed, result, spread);
  return a.latePieces > b.latePieces || a.latePieces === b.latePieces && a.lateDays > b.lateDays + 1e-8 ? spread : consolidated;
}
function onTimeScore(seed, result, plan) {
  let latePieces = 0, lateDays = 0;
  for (const job of plan.jobs) {
    const batch = result.batches.find((item) => item.id === job.batchId);
    const dueDate = batch?.demandDueDate || seed.orders.filter((order) => order.product.toUpperCase() === job.product.toUpperCase() && order.quantity > 0 && order.dueDate).map((order) => order.dueDate).sort()[0];
    if (!dueDate) continue;
    const due = inputDateSerial(dueDate) + 1;
    const ready = job.deliveryReadyAt > 0 ? job.deliveryReadyAt : Number.POSITIVE_INFINITY;
    if (ready > due + 1e-8) {
      latePieces += job.quantity;
      lateDays += Number.isFinite(ready) ? ready - due : 3650;
    }
  }
  return { latePieces, lateDays };
}
function buildDownstreamProcessPlanWith(seed, result, includeInterruptedCandidates, continuationControl) {
  const master = seed.processMasterData ?? { version: 0, source: { kind: "one-time-foundation", files: [], calculatedOnce: "" }, machineCodeStandard: [], products: [], resources: [] };
  const warnings = validateProcessMasterData(master);
  const sources = [];
  for (const lot of (seed.wipLots ?? []).filter((item) => item.availableQuantity > 0 && item.stage !== "delivered" && item.stage !== "scrapped")) {
    const masterProduct = processMasterDataForProduct(master, lot.product);
    if (!masterProduct) {
      warnings.push({ code: "missing-product", product: lot.product, batchId: lot.id, message: `${lot.product} yar\u0131 mam\xFCl\xFC i\xE7in downstream \xFCr\xFCn rotas\u0131 bulunamad\u0131.` });
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
      warnings.push({ code: "missing-product", product, batchId: `current:${machine.id}`, message: `${product} mevcut torna i\u015Fi i\xE7in downstream \xFCr\xFCn rotas\u0131 bulunamad\u0131.` });
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
      warnings.push({ code: "missing-product", product: batch.product, batchId: batch.id, message: `${batch.product} i\xE7in downstream \xFCr\xFCn rotas\u0131 bulunamad\u0131.` });
      continue;
    }
    sources.push({ id: batch.id, source: "turning-plan", product: batch.product, quantity: batch.quantity, workOrder: batch.workOrder ?? "", releaseAt: batch.end, nextProcess: hasActiveProductionInterruption(seed, batch.id, batch.interruptionId) ? void 0 : productProcessRoute(masterProduct).find((process2) => process2 !== "turning"), batch, masterProduct });
  }
  const sourceRank = (source) => source === "wip" ? 0 : source === "current-turning" ? 1 : 2;
  sources.sort((left, right) => sourceRank(left.source) - sourceRank(right.source) || left.releaseAt - right.releaseAt || left.id.localeCompare(right.id));
  const operationsByKey = /* @__PURE__ */ new Map();
  const baseOperations = sources.flatMap((source) => source.source === "wip" ? actualWipOperations(source.lot, source.masterProduct) : [turningOperation(seed, source)]);
  for (const operation of baseOperations) operationsByKey.set(`${operation.batchId}:${operation.process}`, operation);
  const downstream = ["drilling", "deburring", "gkm"].flatMap((process2) => scheduleStage(seed, master, process2, sources, operationsByKey, warnings, includeInterruptedCandidates, continuationControl));
  const operations = [...baseOperations, ...downstream].sort((left, right) => left.start - right.start || left.sequence - right.sequence || Number(right.actual) - Number(left.actual) || left.id.localeCompare(right.id));
  const jobs = sources.map((source) => {
    const route = operations.filter((operation) => operation.batchId === source.id).sort((left, right) => left.sequence - right.sequence || Number(right.actual) - Number(left.actual));
    const completion2 = route.at(-1)?.end ?? source.releaseAt;
    const customRouteComplete = !source.masterProduct.route || source.masterProduct.route.length > 0 && !warnings.some((warning) => warning.product === source.product && warning.code === "invalid-route") && source.masterProduct.route.every((process2) => route.some((operation) => (operation.recordedProcess ?? operation.process) === process2)) && source.lot?.stage !== "on-hold" && source.lot?.stage !== "unclassified";
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
  return { state: operations.length ? "planned" : "empty", operations, jobs, warnings, gaps, completion, deliveryCompletion, queueEntries };
}

// scripts/scenario-plan-runtime.ts
var MAX_SCENARIOS = 50;
var MAX_ROWS = 2e4;
var finite = (value) => typeof value === "number" && Number.isFinite(value) && value > 0 ? value : null;
var text = (value) => typeof value === "string" ? value.slice(0, 500) : value == null ? "" : String(value).slice(0, 500);
var SOURCE_LABEL = { wip: "Yar\u0131 mamul", "current-turning": "Mevcut Torna i\u015Fi", "turning-plan": "Torna plan\u0131" };
function planScenario(record) {
  const output = { id: text(record.id), name: text(record.name), createdAt: text(record.createdAt), status: "ok", rows: { turning: [], drilling: [], deburring: [], gkm: [] }, warnings: [] };
  try {
    const raw = record.seed;
    if (!raw || ![raw.orders, raw.products, raw.machines, raw.preferences].every(Array.isArray)) throw Error("Senaryo girdisi ge\xE7ersiz.");
    if (raw.productionArea === "cubuk-filtre") throw Error("\xC7ubuk Filtre senaryolar\u0131 bu plan sayfalar\u0131na al\u0131nmaz.");
    const batches = record.result?.batches;
    if (!Array.isArray(batches) || batches.length > MAX_ROWS) throw Error("Senaryo sonucu ge\xE7ersiz veya \xE7ok b\xFCy\xFCk.");
    const seed = migratePlanningSeed(structuredClone(raw));
    if (JSON.stringify(raw.processMasterData ?? null) !== JSON.stringify(seed.processMasterData ?? null)) {
      output.warnings.push({ code: "migrated-process-data", product: "", batchId: "", message: "Senaryo eski veri \u015Femas\u0131nda; Delme/\xC7apak Alma/GKM ana verisi uygulamada y\xFCkleme s\u0131ras\u0131ndaki gibi g\xFCncellenerek hesapland\u0131." });
    }
    for (const batch of batches) {
      const planned = batch.status === "planned";
      const start = planned ? finite(batch.start) : null, end = planned ? finite(batch.end) : null;
      output.rows.turning.push({
        id: text(batch.id),
        workOrder: text(batch.workOrder),
        product: text(batch.product),
        quantity: Number(batch.quantity) || 0,
        resourceId: text(batch.machineId),
        start,
        end,
        readyAt: null,
        setupHours: typeof batch.setupHours === "number" ? batch.setupHours : null,
        wait: "Bekleme yok",
        source: "Torna plan\u0131",
        status: !planned ? "Planlanamad\u0131" : start === null || end === null ? "Tarihsiz" : "Planland\u0131",
        note: [batch.locked ? "Kilitli" : "", batch.routeCommitted ? "Rota onayl\u0131" : "", !planned ? text(batch.reason) : ""].filter(Boolean).join(" \xB7 ")
      });
    }
    for (const machine of seed.machines ?? []) {
      const current = machine.currentJob;
      if (!current || !(current.quantity > 0) || !current.product) continue;
      output.rows.turning.push({
        id: text(current.batchId ?? `current:${machine.id}`),
        workOrder: text(current.workOrder),
        product: text(current.product),
        quantity: current.quantity,
        resourceId: text(machine.id),
        start: finite(current.start),
        end: finite(current.end),
        readyAt: null,
        setupHours: null,
        wait: "\xC7al\u0131\u015Fan i\u015F \xB7 kay\u0131tl\u0131 ba\u015Flang\u0131\xE7",
        source: "Mevcut Torna i\u015Fi",
        status: "\xC7al\u0131\u015F\u0131yor",
        note: current.remainingQuantity != null && current.remainingQuantity !== current.quantity ? `Kalan ${current.remainingQuantity}` : ""
      });
    }
    const lotHistory = /* @__PURE__ */ new Set();
    for (const lot of seed.wipLots ?? []) {
      if (lot.parentLotId) continue;
      if (lot.sourceHistoryEntryId) lotHistory.add(lot.sourceHistoryEntryId);
      for (const step of lot.completedSteps ?? []) if (step.process === "turning") output.rows.turning.push({
        id: text(lot.sourceBatchId ?? lot.id),
        workOrder: text(lot.workOrder),
        product: text(lot.product),
        quantity: step.quantity,
        resourceId: text(step.resourceId),
        start: finite(step.start),
        end: finite(step.end),
        readyAt: null,
        setupHours: null,
        wait: "Fiili kay\u0131t \xB7 kay\u0131tl\u0131 ba\u015Flang\u0131\xE7 ve biti\u015F",
        source: "Yar\u0131 mamul",
        status: "Fiili",
        note: ""
      });
    }
    for (const entry of seed.productionHistory ?? []) {
      if ((entry.process ?? "turning") !== "turning" || lotHistory.has(entry.id) || !(entry.completedQuantity > 0)) continue;
      output.rows.turning.push({
        id: text(entry.sourceBatchId ?? entry.id),
        workOrder: text(entry.workOrder),
        product: text(entry.product),
        quantity: entry.completedQuantity,
        resourceId: text(entry.machineId),
        start: finite(entry.start),
        end: finite(entry.completedAt),
        readyAt: null,
        setupHours: null,
        wait: "Fiili kay\u0131t \xB7 kay\u0131tl\u0131 ba\u015Flang\u0131\xE7 ve biti\u015F",
        source: "\xDCretim ar\u015Fivi",
        status: "Fiili",
        note: text(entry.inventoryStatus)
      });
    }
    const plan = buildDownstreamProcessPlan(seed, { batches });
    for (const operation of plan.operations) {
      if (operation.process !== "drilling" && operation.process !== "deburring" && operation.process !== "gkm") continue;
      const start = finite(operation.start), end = finite(operation.end);
      output.rows[operation.process].push({
        id: text(operation.batchId),
        workOrder: text(operation.workOrder),
        product: text(operation.product),
        quantity: operation.quantity,
        resourceId: text(operation.resourceId),
        start,
        end,
        readyAt: finite(operation.readyAt),
        setupHours: operation.setupHours,
        // The rule label from scheduleStage is the only wait text (no second legacy wait);
        // plans built before the label existed fall back to the workday value.
        wait: operation.waitRuleLabel ? text(operation.waitRuleLabel) : operation.waitWorkdaysBefore ? `${operation.waitWorkdaysBefore} i\u015F g\xFCn\xFC` : "Bekleme yok",
        source: SOURCE_LABEL[operation.source] ?? operation.source,
        status: operation.actual ? "Fiili" : operation.current ? "\xC7al\u0131\u015F\u0131yor" : start === null || end === null ? "Tarihsiz" : "Planland\u0131",
        note: [operation.manualOverride ? "Elle yerle\u015Fim" : "", operation.flowReason ? text(operation.flowReason) : ""].filter(Boolean).join(" \xB7 ")
      });
    }
    for (const warning of plan.warnings) output.warnings.push({ code: warning.code, product: text(warning.product), batchId: text(warning.batchId), message: text(warning.message) });
    for (const job of plan.jobs) if (!job.deliveryReadyAt && job.source !== "wip") output.warnings.push({ code: "undated", product: text(job.product), batchId: text(job.batchId), message: "Teslimata haz\u0131r tarihi hesaplanamad\u0131 (eksik veya ge\xE7ersiz rota)." });
    const total = Object.values(output.rows).reduce((sum, rows) => sum + rows.length, 0);
    if (total > MAX_ROWS * 4) throw Error("Senaryo plan\u0131 sat\u0131r s\u0131n\u0131r\u0131n\u0131 a\u015F\u0131yor.");
  } catch (error) {
    output.status = "invalid";
    output.error = error instanceof Error ? error.message.slice(0, 300) : "Senaryo plan\u0131 hesaplanamad\u0131.";
    output.rows = { turning: [], drilling: [], deburring: [], gkm: [] };
    output.warnings = [];
  }
  return output;
}
try {
  const request = JSON.parse((0, import_node_fs.readFileSync)(0, "utf8"));
  if (!request || !Array.isArray(request.scenarios) || request.scenarios.length > MAX_SCENARIOS) throw Error("Senaryo listesi ge\xE7ersiz.");
  process.stdout.write(JSON.stringify({ version: 1, scenarios: request.scenarios.map(planScenario) }));
} catch {
  process.stdout.write(JSON.stringify({ version: 1, error: "Senaryo planlar\u0131 hesaplanamad\u0131.", scenarios: [] }));
}
