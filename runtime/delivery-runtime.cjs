"use strict";

// scripts/delivery-runtime.ts
var import_node_fs = require("node:fs");

// lib/production-interruptions.ts
function activeLotInterruptions(seed, lot) {
  return (seed.productionInterruptions ?? []).filter((item) => !item.completedAt && lot?.interruptionIds?.includes(item.id));
}

// lib/turning-queue-identity.ts
function reconcileTurningQueue(seed, batches) {
  const inspected = inspectTurningQueue(seed, batches);
  if (inspected.conflicts.length) throw new Error(inspected.conflicts[0].message);
  return inspected.reconciledBatches;
}
var identityKey = (value) => String(value ?? "").trim().toUpperCase();
var identityMessage = (batch) => `${batch.machineId} \xB7 ${batch.workOrder || batch.product}: mevcut \xFCretim/ar\u015Fiv ile kuyruktaki \u015Farj kimli\u011Fi belirsiz. \u0130\u015F emri ve \u015Farj kay\u0131tlar\u0131n\u0131 kontrol edin; i\u015Flem uygulanmad\u0131.`;
function inspectTurningQueue(seed, batches = seed.manualBatches ?? []) {
  const records = [
    ...seed.machines.filter((m) => m.currentJob.quantity > 0).map((m) => ({ kind: "current", id: m.id, chargeId: m.currentJob.batchId, machineId: m.id, product: m.currentJob.product, workOrder: m.currentJob.workOrder, quantity: m.currentJob.originalQuantity ?? m.currentJob.quantity })),
    ...(seed.productionHistory ?? []).filter((h) => (!h.process || h.process === "turning") && h.inventoryStatus !== "voided" && !h.interruptionIds?.length).map((h) => ({ kind: "history", id: h.id, chargeId: h.sourceBatchId === h.id ? void 0 : h.sourceBatchId, machineId: h.machineId, product: h.product, workOrder: h.workOrder, quantity: h.originalQuantity, status: h.inventoryStatus })),
    ...(seed.wipLots ?? []).filter((l) => l.sourceBatchId && l.sourceBatchId !== l.sourceHistoryEntryId && !seed.productionHistory?.some((h) => h.id === l.sourceHistoryEntryId && h.inventoryStatus === "voided")).map((l) => ({ kind: "wip", id: l.id, chargeId: l.sourceBatchId, machineId: "", product: l.product, workOrder: l.workOrder, quantity: l.originalQuantity, status: l.stage }))
  ];
  const conflicts = [];
  const reconciledBatches = batches.filter((batch) => {
    const duplicates = batches.filter((b) => b.id === batch.id);
    const exact = records.filter((r) => r.chargeId && r.chargeId === batch.id);
    const legacy = records.filter((r) => !r.chargeId && identityKey(r.workOrder) && identityKey(r.workOrder) === identityKey(batch.workOrder) && identityKey(r.product) === identityKey(batch.product));
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
    } else if (!batch.interruptionId && legacy.length) {
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

// lib/delivery-calendar.ts
var EXCEL_EPOCH = Date.UTC(1899, 11, 30);
var DAY_MS = 864e5;
var TURNING_DELIVERY_LEAD_WORKDAYS = 4;
var ROUTED_DELIVERY_BUFFER_WORKDAYS = 1;
function dayOfWeek(serial) {
  return new Date(EXCEL_EPOCH + Math.floor(serial) * DAY_MS).getUTCDay();
}
function addDeliveryWorkdays(completionSerial, workdays) {
  if (!Number.isFinite(completionSerial) || completionSerial <= 0) return completionSerial;
  const fraction = completionSerial - Math.floor(completionSerial);
  let serial = Math.floor(completionSerial);
  let remaining = Math.max(0, Math.trunc(workdays));
  while (remaining > 0) {
    serial += 1;
    if (dayOfWeek(serial) !== 0) remaining -= 1;
  }
  return serial + fraction;
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
function turningDeliveryReadyAt(completionSerial) {
  return addDeliveryWorkdays(completionSerial, TURNING_DELIVERY_LEAD_WORKDAYS);
}
function routedDeliveryReadyAt(seed, routeCompletionSerial) {
  return addFactoryWorkdays(seed, routeCompletionSerial, ROUTED_DELIVERY_BUFFER_WORKDAYS);
}

// lib/factory-time.ts
var FACTORY_TIME_ZONE = "Europe/Istanbul";
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

// lib/process-master-data.ts
var PRODUCT_PROCESS_ORDER = ["turning", "drilling", "deburring", "gkm"];
function productProcessRoute(product) {
  return product.route ?? ["turning", ...product.processes.slice().sort((a, b) => a.sequence - b.sequence).map((item) => item.process)];
}
function turningEnabled(master, product) {
  return processMasterDataForProduct(master, product)?.route?.includes("turning") ?? true;
}
function processMasterDataForProduct(master, productCode) {
  const code2 = productCode.trim().toUpperCase();
  return master?.products.find((product) => product.product.toUpperCase() === code2);
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

// lib/planning.ts
function diameterNumeric(value) {
  const match = value.replace(",", ".").match(/\d+(?:\.\d+)?/);
  return match ? Number(match[0]) : 0;
}
function excelSerialToDate(serial) {
  return new Date(Date.UTC(1899, 11, 30) + serial * 864e5);
}
function formatExcelDate(serial, options) {
  if (!serial || !Number.isFinite(serial)) return "\u2014";
  return new Intl.DateTimeFormat("tr-TR", { ...options ?? { day: "2-digit", month: "short", year: "numeric" }, timeZone: "UTC" }).format(excelSerialToDate(serial));
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
function normalizedDiameter(value) {
  return value.toUpperCase().replace("\xD8", "").replace(/MM/g, "").replace(/\s/g, "").replace(".", ",");
}
function isProductCode(value) {
  return /^R.{7,}$/i.test(value.trim());
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
  const code2 = productCode.trim().toUpperCase();
  const storedFamily = seed.products.find((product) => product.product.trim().toUpperCase() === code2)?.setupFamily;
  return resolvedProductSetupFamily(code2, storedFamily);
}
function calculateSetup(seed, previousProduct, previousDiameter, nextProduct, nextDiameter) {
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
function machineRunHours(seed, machine, productCode, quantity2) {
  const shiftRate = machine.rates[productCode.toUpperCase()] ?? 0;
  const hourlyRate = shiftRate / getSetupSettings(seed).shiftHours * machineCapacityFactor(machine);
  return hourlyRate > 0 ? quantity2 / hourlyRate : Number.POSITIVE_INFINITY;
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
var RESTRICTED_MACHINE_IDS = /* @__PURE__ */ new Set(["C-03", "C-04", "C-11", "C-12", "C-15", "C-16", "C-17"]);
var LARGE_DIAMETER_BLOCKED = /* @__PURE__ */ new Set(["C-01", "C-02", "C-04", "C-05"]);
function isMachineEligibleForProduct(seed, machineId, productCode) {
  if (!turningEnabled(seed.processMasterData, productCode)) return false;
  const code2 = productCode.toUpperCase();
  const product = seed.products.find((item) => item.product.toUpperCase() === code2);
  if (!product) return false;
  const preference = seed.preferences.find((rule) => rule.key.toUpperCase() === code2);
  if (preference) return preference.machines.includes(machineId);
  if (diameterNumeric(product.diameter) >= 25.5 && LARGE_DIAMETER_BLOCKED.has(machineId)) return false;
  if (!RESTRICTED_MACHINE_IDS.has(machineId)) return true;
  return seed.restrictions.some((rule) => rule.machineId === machineId && rule.product.toUpperCase() === code2);
}
function semiFinishedProduction(seed) {
  return (seed.productionHistory ?? []).filter((entry) => (entry.inventoryStatus ?? "semi-finished") === "semi-finished");
}
function currentJobRouteIdentity(machine) {
  const job = machine.currentJob;
  return JSON.stringify(job.batchId ? [machine.id, job.batchId, job.product] : [machine.id, job.product, job.workOrder, job.start, job.originalQuantity ?? job.quantity]);
}
function inputDateSerial(value) {
  return value ? (Date.parse(`${value}T00:00:00Z`) - Date.UTC(1899, 11, 30)) / 864e5 : 0;
}
function productionQuantityByDate(seed, batches, product, serial) {
  const code2 = product.toUpperCase();
  const dueDay = Math.floor(serial);
  const openingStock = seed.customerDemand ? 0 : Math.max(0, seed.openingStock?.[code2] ?? 0);
  const completed = semiFinishedProduction(seed).filter((entry) => entry.product.toUpperCase() === code2 && Math.floor(turningDeliveryReadyAt(entry.completedAt)) <= dueDay).reduce((sum, entry) => sum + entry.completedQuantity, 0);
  const current = seed.machines.filter((machine) => machine.currentJob.product.toUpperCase() === code2 && Math.floor(turningDeliveryReadyAt(machine.currentJob.end)) <= dueDay).reduce((sum, machine) => sum + machine.currentJob.quantity, 0);
  const planned = batches.filter((batch) => batch.status === "planned" && batch.product.toUpperCase() === code2 && Math.floor(turningDeliveryReadyAt(batch.end)) <= dueDay).reduce((sum, batch) => sum + batch.quantity, 0);
  return openingStock + completed + current + planned;
}
function productionQuantityByTurningDate(seed, batches, product, serial) {
  const code2 = product.toUpperCase();
  const dueDay = Math.floor(serial);
  const openingStock = seed.customerDemand ? 0 : Math.max(0, seed.openingStock?.[code2] ?? 0);
  const completed = semiFinishedProduction(seed).filter((entry) => entry.product.toUpperCase() === code2 && Math.floor(entry.completedAt) <= dueDay).reduce((sum, entry) => sum + entry.completedQuantity, 0);
  const current = seed.machines.filter((machine) => machine.currentJob.product.toUpperCase() === code2 && Math.floor(machine.currentJob.end) <= dueDay).reduce((sum, machine) => sum + machine.currentJob.quantity, 0);
  const planned = batches.filter((batch) => batch.status === "planned" && batch.product.toUpperCase() === code2 && Math.floor(batch.end) <= dueDay).reduce((sum, batch) => sum + batch.quantity, 0);
  return openingStock + completed + current + planned;
}
function orderProductionBreakdown(seed, batches, order) {
  const code2 = order.product.toUpperCase();
  const existingTotal = (seed.customerDemand ? 0 : Math.max(0, seed.openingStock?.[code2] ?? 0)) + semiFinishedProduction(seed).filter((entry) => entry.product.toUpperCase() === code2).reduce((sum, entry) => sum + entry.completedQuantity, 0) + seed.machines.filter((machine) => machine.currentJob.product.toUpperCase() === code2).reduce((sum, machine) => sum + machine.currentJob.quantity, 0);
  const plannedTotal = batches.filter((batch) => batch.status === "planned" && batch.product.toUpperCase() === code2).reduce((sum, batch) => sum + batch.quantity, 0);
  const dueSerial = inputDateSerial(order.dueDate);
  const onTimeTotal = dueSerial ? seed.activePlanRun?.optimizationGoal === "coarse" ? productionQuantityByTurningDate(seed, batches, order.product, dueSerial) : productionQuantityByDate(seed, batches, order.product, dueSerial) : null;
  const productOrders = seed.orders.filter((item) => item.product.toUpperCase() === code2).sort((a, b) => (a.dueDate || "9999").localeCompare(b.dueDate || "9999") || a.sourceRow - b.sourceRow || a.id.localeCompare(b.id));
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
function manualMachineAllowed(seed, machineId, productCode, diameter) {
  const machine = seed.machines.find((item) => item.id === machineId);
  if (!machine?.active) return false;
  return isMachineEligibleForProduct(seed, machineId, productCode);
}
function scenarioResultFromBatches(seed, batches) {
  const machinesByProduct = /* @__PURE__ */ new Map();
  for (const batch of batches.filter((item) => item.status === "planned")) {
    const code2 = batch.product.toUpperCase();
    machinesByProduct.set(code2, unique([...machinesByProduct.get(code2) ?? [], batch.machineId]));
  }
  const orders = seed.orders.map((order) => {
    const code2 = order.product.toUpperCase();
    const breakdown = orderProductionBreakdown(seed, batches, order);
    const planned2 = breakdown.existingProduction + breakdown.newlyPlanned;
    return { ...order, planned: planned2, difference: planned2 - order.quantity, ...breakdown, assignedMachines: machinesByProduct.get(code2) ?? order.savedMachines };
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
      plannedBatchCount: plannedBatches.length,
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
function recalculateManualScenario(seed, sourceBatches, options = { allowPlanEndOverflow: true }) {
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
      if (!manualMachineAllowed(seed, machine.id, batch.product, product.diameter)) {
        throw new Error(`${context}: \xFCr\xFCn bu tezgahta \xFCretime izinli de\u011Fil.`);
      }
      const shiftRate = machine.rates[batch.product.toUpperCase()] ?? 0;
      const dailyRate = shiftRate * machine.shiftFactor * machineCapacityFactor(machine);
      if (dailyRate <= 0) throw new Error(`${context}: \xFCretim h\u0131z\u0131 tan\u0131ml\u0131 de\u011Fil.`);
      const setup = calculateSetup(seed, previousProduct, previousDiameter, batch.product, product.diameter);
      const runHours = machineRunHours(seed, machine, batch.product, batch.quantity);
      const timeline = addMachineCapacityHours(seed, machine, previousEnd, setup.hours + runHours);
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
        explanation: `Manuel plan: ${machine.id} kuyru\u011Funda ${index + 1}. s\u0131ra. ${setup.label}: ${setup.hours.toFixed(1)} saat; \xFCretim: ${runHours.toFixed(1)} saat.`,
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
  return scenarioResultFromBatches(seed, [...recalculated, ...unplanned].sort((a, b) => a.sequence - b.sequence));
}
function rollForwardUnfinishedProduction(seed, asOf = inputDateSerial(factoryDateInput()), options = {}) {
  if (!Number.isFinite(asOf) || asOf <= 0) throw new Error("Devreden i\u015Fler i\xE7in ge\xE7erli bir ba\u015Flang\u0131\xE7 tarihi se\xE7in.");
  const rollTurning = options.turning ?? true;
  const rollDownstream = options.downstream ?? true;
  const rolledMachineIds = [];
  const shiftHours = getSetupSettings(seed).shiftHours;
  for (const machine of rollTurning ? seed.machines : []) {
    const current = machine.currentJob;
    const remaining = current.remainingQuantity ?? current.quantity;
    const originalCurrentBoundary = isProductCode(current.product) && remaining > 0 ? current.end : 0;
    const originalOperationalBoundary = Math.max(machine.operationalAvailableStart ?? machine.availableStart, originalCurrentBoundary);
    const planningWindowDays = Math.max(1, Math.floor(machine.planEnd) - Math.floor(originalOperationalBoundary));
    if (originalOperationalBoundary < asOf) {
      machine.planEnd = Math.max(machine.planEnd, Math.floor(asOf) + planningWindowDays);
    }
    const unfinishedPastJob = isProductCode(current.product) && remaining > 0 && current.end < asOf;
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
    const currentBoundary = isProductCode(current.product) && remaining > 0 ? current.end : 0;
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

// lib/wip-ledger.ts
var terminalStages = /* @__PURE__ */ new Set(["delivered", "scrapped"]);
function activeWipLots(seed) {
  return (seed.wipLots ?? []).filter((lot) => lot.availableQuantity > 0 && !terminalStages.has(lot.stage));
}

// lib/process-route-state.ts
function describeProcessRoute(seed, job, warnings) {
  const product = processMasterDataForProduct(seed.processMasterData, job.product);
  if (!product) return { routeSteps: [], readinessIssues: [{ code: "missing-product", message: "\xDCr\xFCn rotas\u0131 bulunamad\u0131; miktar korunuyor." }] };
  const route = productProcessRoute(product);
  const lot = seed.wipLots?.find((l) => l.id === job.wipLotId);
  const chargeId = job.source === "current-turning" ? seed.machines?.find((m) => m.id === job.turningMachineId)?.currentJob.batchId : job.batchId;
  const pause = seed.productionInterruptions?.find((p) => !p.completedAt && p.chargeId === chargeId);
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
    let code2 = state;
    if (lot?.stage === "on-hold" || lot?.stage === "unclassified") {
      code2 = lot.stage === "on-hold" ? "held" : "unclassified";
      state = "predecessor-pending";
      message = lot.stage === "on-hold" ? "Yar\u0131 mam\xFCl blokeli." : "Yar\u0131 mam\xFCl\xFCn ger\xE7ek konumu do\u011Frulanmal\u0131.";
    } else if (pause && route.indexOf(process2) >= route.indexOf(pause.process)) {
      state = process2 === pause.process ? "paused" : "predecessor-pending";
      code2 = state;
      message = process2 === pause.process ? "Ara verilen i\u015F kuyrukta korunuyor." : "Ara verilen \xF6nceki prosesin tamamlanmas\u0131 bekleniyor.";
    } else if (partial) {
      state = process2 === lot?.nextProcess ? "manual-required" : "predecessor-pending";
      code2 = state;
      message = state === "manual-required" ? "Yar\u0131m \xFCretim: bu prosesi Manuel \u015Farj ile kuyru\u011Fa ekleyin." : "\xD6nceki proses ve manuel \xFCretim onay\u0131 bekleniyor.";
    } else if (warnings.some((w) => w.product === job.product && (w.code === "invalid-route" || w.code === "missing-parameter" && !w.batchId))) {
      state = "invalid-route";
      code2 = state;
      message = "\xDCr\xFCn rotas\u0131 veya proses parametreleri eksik.";
    } else if (route.indexOf(process2) > 0 && !job.operations.some((o) => (o.recordedProcess ?? o.process) === route[route.indexOf(process2) - 1])) {
      state = "predecessor-pending";
      code2 = state;
      message = "\xD6nceki prosesin haz\u0131r olma tarihi belirlenemedi.";
    }
    issues.push({ code: code2, message, process: process2 });
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
    if (pause.completedAt || pause.process === "turning" || pause.process === "washing" || intents.some((i) => i.batchId === pause.chargeId && i.process === pause.process)) continue;
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
function calculateDownstreamSetup(process2, previous, next) {
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
  const quantity2 = current?.quantity ?? batch?.quantity ?? source.quantity;
  const product = current?.product ?? batch?.product ?? source.product;
  const diameter = current?.diameter ?? batch?.diameter ?? "";
  return {
    id: `${source.id}:turning`,
    batchId: source.id,
    product,
    family: masterProduct.family,
    quantity: quantity2,
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
function scheduleStage(seed, master, process2, sources, operationsByKey, warnings, includeInterruptedCandidates = false) {
  const queueByResource = /* @__PURE__ */ new Map();
  let d02SpareGaps;
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
    if (seed.productionInterruptions?.some((item) => !item.completedAt && item.chargeId === source.id && item.process === source.nextProcess) && !firstRemaining) return [];
    if (interrupted && !running && !explicitPlacement && !(includeInterruptedCandidates && firstRemaining)) return [];
    if (!predecessor && !firstRemaining) {
      warnings.push({ code: "missing-parameter", product: source.product, batchId: source.id, message: `${source.product} \xB7 ${process2} i\xE7in \xF6nceki rota ad\u0131m\u0131 bulunamad\u0131.` });
      return [];
    }
    const effectiveWaitWorkdays = source.masterProduct.route ? firstRemaining && source.source === "wip" ? 0 : parameter.waitWorkdaysBefore : process2 === "drilling" ? source.source === "wip" ? 0 : 1 : parameter.waitWorkdaysBefore;
    const readyAt = firstRemaining ? source.source === "wip" ? source.releaseAt : addProcessWaitWorkdays(seed, predecessor?.end ?? source.releaseAt, effectiveWaitWorkdays) : addProcessWaitWorkdays(seed, predecessor.end, effectiveWaitWorkdays);
    const storedOverride = processPlacementOverride(seed, source.id, source.product, process2, !interrupted);
    const override = storedOverride?.routeMode === "automatic" ? void 0 : storedOverride?.routeMode === "priority" ? { ...storedOverride, requestedStart: readyAt } : storedOverride;
    const currentJob = seed.processCurrentJobs?.find((item) => item.batchId === source.id && item.process === process2);
    return [{ source, parameter, predecessor, readyAt, override, currentJob, effectiveWaitWorkdays }];
  }).sort((left, right) => {
    if (Boolean(left.currentJob) !== Boolean(right.currentJob)) return left.currentJob ? -1 : 1;
    if (Boolean(left.override?.resumeAfterCurrent) !== Boolean(right.override?.resumeAfterCurrent)) return left.override?.resumeAfterCurrent ? -1 : 1;
    if (process2 === "drilling" && left.source.masterProduct.family !== right.source.masterProduct.family) {
      return left.source.masterProduct.family === "center-pin" ? -1 : 1;
    }
    const leftScheduleAt = Math.max(left.readyAt, left.override?.requestedStart ?? left.readyAt);
    const rightScheduleAt = Math.max(right.readyAt, right.override?.requestedStart ?? right.readyAt);
    const leftOrder = left.override?.queueOrder ?? Number.MAX_SAFE_INTEGER;
    const rightOrder = right.override?.queueOrder ?? Number.MAX_SAFE_INTEGER;
    if (leftOrder !== rightOrder) return leftOrder - rightOrder;
    if (Math.abs(leftScheduleAt - rightScheduleAt) > 1e-8) return leftScheduleAt - rightScheduleAt;
    if (left.source.source !== right.source.source) {
      const rank = (source) => source === "wip" ? 0 : source === "current-turning" ? 1 : 2;
      return rank(left.source.source) - rank(right.source.source);
    }
    if (strategy === "campaign") {
      const setupOrder = left.parameter.setupKey.localeCompare(right.parameter.setupKey, "tr", { numeric: true });
      if (setupOrder) return setupOrder;
      const productOrder = left.source.product.localeCompare(right.source.product, "tr", { numeric: true });
      if (productOrder) return productOrder;
    }
    return left.readyAt - right.readyAt || left.source.releaseAt - right.source.releaseAt || left.source.id.localeCompare(right.source.id);
  });
  const scheduled = [];
  for (const item of candidates) {
    const { source, parameter, predecessor, readyAt, override, currentJob, effectiveWaitWorkdays } = item;
    const nextSetup = { product: source.product, family: source.masterProduct.family, setupKey: parameter.setupKey };
    const resourceCandidates = currentJob ? [currentJob.resourceId] : override ? [override.resourceId] : parameter.resourcePriority;
    const evaluated = resourceCandidates.flatMap((resourceId, priority) => {
      const resource = processResource(master, resourceId);
      const unitsPerShift = parameter.unitsPerShift[resourceId];
      if (!resource || resource.process !== process2 || !resource.active || resource.defaultShifts <= 0 || !resourceSupportsProcessProduct(resource, source.masterProduct) || !Number.isFinite(unitsPerShift) || unitsPerShift <= 0) return [];
      const queue = queueByResource.get(resourceId);
      const setup = calculateDownstreamSetup(process2, queue, nextSetup);
      const runHours = currentJob ? Math.max(0, (currentJob.end - currentJob.start) * 24 - currentJob.setupHours) : source.quantity / unitsPerShift * getSetupSettings(seed).shiftHours;
      const requestedStart = Math.max(readyAt, queue?.tail ?? readyAt, override?.requestedStart ?? readyAt, currentJob ? readyAt : resource.availableStart ?? readyAt);
      const timeline = currentJob ? { start: currentJob.start, end: currentJob.end } : addMachineCapacityHours(
        processCalendarSeed(seed, resource.id),
        { id: resource.id, shiftFactor: resource.defaultShifts, finishOffset: 0 },
        requestedStart,
        setup.hours + runHours
      );
      if (!currentJob && resource.planEnd && timeline.end > Math.floor(resource.planEnd) + 1 + 1e-8) return [];
      const options = [{ resource, unitsPerShift, setupHours: setup.hours, protectedSetupHoursAfter: 0, runHours, priority, d02GapIndex: -1, ...timeline }];
      if (!currentJob && process2 === "drilling" && resource.id === "D-02" && source.masterProduct.family === "piston") {
        if (!d02SpareGaps) {
          const centerPinReservations = scheduled.filter((operation2) => operation2.resourceId === "D-02" && operation2.family === "center-pin").sort((left, right) => left.start - right.start || left.end - right.end || left.id.localeCompare(right.id));
          d02SpareGaps = centerPinReservations.map((nextCenterPin, index) => {
            const previousCenterPin = centerPinReservations[index - 1];
            return {
              nextCenterPin,
              cursor: Math.max(previousCenterPin?.end ?? 0, ...scheduled.filter((operation2) => operation2.current && operation2.resourceId === "D-02").map((operation2) => operation2.end)),
              tail: previousCenterPin ? setupSourceForOperation(previousCenterPin) : void 0
            };
          });
        }
        const calendarSeed = processCalendarSeed(seed, resource.id);
        for (const [gapIndex, gap] of d02SpareGaps.entries()) {
          const incomingSetup = calculateDownstreamSetup(process2, gap.tail, nextSetup);
          const gapTimeline = addMachineCapacityHours(
            calendarSeed,
            { id: resource.id, shiftFactor: resource.defaultShifts, finishOffset: 0 },
            Math.max(readyAt, gap.cursor, override?.requestedStart ?? readyAt, resource.availableStart ?? readyAt),
            incomingSetup.hours + runHours
          );
          if (resource.planEnd && gapTimeline.end > Math.floor(resource.planEnd) + 1 + 1e-8) continue;
          const requiredCenterPinSetup = calculateDownstreamSetup(process2, nextSetup, setupSourceForOperation(gap.nextCenterPin)).hours;
          const protectedSetupHoursAfter = Math.max(0, requiredCenterPinSetup - gap.nextCenterPin.setupHours);
          const restored = addMachineCapacityHours(
            calendarSeed,
            { id: resource.id, shiftFactor: resource.defaultShifts, finishOffset: 0 },
            gapTimeline.end,
            protectedSetupHoursAfter
          );
          if (restored.end > gap.nextCenterPin.start + 1e-8) continue;
          options.push({
            resource,
            unitsPerShift,
            setupHours: incomingSetup.hours,
            protectedSetupHoursAfter,
            runHours,
            priority,
            d02GapIndex: gapIndex,
            ...gapTimeline
          });
        }
      }
      return options;
    }).sort((left, right) => left.end - right.end || left.priority - right.priority || left.resource.id.localeCompare(right.resource.id));
    const chosen = evaluated[0];
    if (!chosen) {
      warnings.push({ code: "missing-resource", product: source.product, batchId: source.id, message: `${source.product} \xB7 ${process2} i\xE7in kullan\u0131labilir i\u015F merkezi veya vardiya kapasitesi yok.` });
      continue;
    }
    const operation = {
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
    scheduled.push(operation);
    if (override?.routeMode === "keep" && !currentJob && (Math.abs(operation.start - (override.preservedStart ?? override.requestedStart)) > 1e-8 || Math.abs(operation.end - (override.preservedEnd ?? operation.end)) > 1e-8)) warnings.push({ code: "placement-conflict", product: source.product, batchId: source.id, message: `${source.workOrder || source.product} \xB7 ${processLabelForError(process2)} mevcut yerle\u015Fimi de\u011Fi\u015Fen girdilerle korunam\u0131yor. \xDCretim ak\u0131\u015F\u0131n\u0131 d\xFCzenle ile yeniden inceleyin.` });
    operationsByKey.set(`${source.id}:${process2}`, operation);
    if (chosen.d02GapIndex >= 0 && d02SpareGaps) {
      const gap = d02SpareGaps[chosen.d02GapIndex];
      if (gap.lastInserted) gap.lastInserted.protectedSetupHoursAfter = void 0;
      gap.lastInserted = operation;
      gap.cursor = operation.end;
      gap.tail = nextSetup;
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
      let code2 = "no-eligible-wip";
      let message = `Bu aral\u0131kta ${resource.id} i\xE7in uygun ve haz\u0131r yar\u0131 mam\xFCl yoktu; s\u0131radaki i\u015F ${next.product} oldu.`;
      if (next.readyAt > previous.end + 1e-8) {
        if (next.waitWorkdaysBefore > 0) {
          code2 = "route-wait";
          message = `${next.product}, rota gere\u011Fi ${next.waitWorkdaysBefore} i\u015F g\xFCn\xFC bekledikten sonra ${resource.id} i\xE7in haz\u0131r oldu.`;
        } else {
          code2 = "upstream-not-ready";
          message = `${next.product} \xF6nceki operasyonu tamamlanmad\u0131\u011F\u0131 i\xE7in bu aral\u0131kta ${resource.id} \xFCzerinde ba\u015Flat\u0131lamad\u0131.`;
        }
      } else {
        const calendarSeed = processCalendarSeed(seed, resource.id);
        const startDay = Math.floor(previous.end);
        const endDay = Math.floor(next.start);
        const days = Array.from({ length: Math.max(1, endDay - startDay + 1) }, (_, offset) => startDay + offset);
        const closed = days.map((serial) => ({ serial, capacity: machineDayCapacity(calendarSeed, { id: resource.id, shiftFactor: resource.defaultShifts }, serial) })).find(({ capacity }) => capacity.shifts === 0);
        if (closed) {
          code2 = closed.capacity.kind === "maintenance" ? "maintenance" : closed.capacity.kind === "shift" ? "zero-shift" : "closed-day";
          message = `${closed.capacity.label} nedeniyle ${resource.id} kapasitesi kapal\u0131yd\u0131; i\u015F ilk \xE7al\u0131\u015F\u0131labilir zamana ta\u015F\u0131nd\u0131.`;
        } else {
          const capacity = machineDayCapacity(calendarSeed, { id: resource.id, shiftFactor: resource.defaultShifts }, startDay);
          const windowEnd = startDay + capacity.shifts * shiftHours / 24;
          if (capacity.shifts > 0 && previous.end >= windowEnd - 1e-8) {
            code2 = "daily-capacity";
            message = `${resource.id} i\xE7in g\xFCnl\xFCk ${capacity.shifts} vardiyal\u0131k kapasite doldu; s\u0131radaki i\u015F bir sonraki \xE7al\u0131\u015Fma penceresinde ba\u015Flad\u0131.`;
          }
        }
      }
      gaps.push({ id: `${resource.id}:${previous.id}:${next.id}`, process: resource.process, resourceId: resource.id, start: previous.end, end: next.start, code: code2, message });
    }
  }
  return gaps;
}
function buildDownstreamProcessPlan(seed, result, includeInterruptedCandidates = false) {
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
      nextProcess: machine.currentJob.interruptionId ? void 0 : productProcessRoute(masterProduct).find((process2) => process2 !== "turning"),
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
    sources.push({ id: batch.id, source: "turning-plan", product: batch.product, quantity: batch.quantity, workOrder: batch.workOrder ?? "", releaseAt: batch.end, nextProcess: batch.interruptionId ? void 0 : productProcessRoute(masterProduct).find((process2) => process2 !== "turning"), batch, masterProduct });
  }
  const sourceRank = (source) => source === "wip" ? 0 : source === "current-turning" ? 1 : 2;
  sources.sort((left, right) => sourceRank(left.source) - sourceRank(right.source) || left.releaseAt - right.releaseAt || left.id.localeCompare(right.id));
  const operationsByKey = /* @__PURE__ */ new Map();
  const baseOperations = sources.flatMap((source) => source.source === "wip" ? actualWipOperations(source.lot, source.masterProduct) : [turningOperation(seed, source)]);
  for (const operation of baseOperations) operationsByKey.set(`${operation.batchId}:${operation.process}`, operation);
  const downstream = ["drilling", "deburring", "gkm"].flatMap((process2) => scheduleStage(seed, master, process2, sources, operationsByKey, warnings, includeInterruptedCandidates));
  const operations = [...baseOperations, ...downstream].sort((left, right) => left.start - right.start || left.sequence - right.sequence || Number(right.actual) - Number(left.actual) || left.id.localeCompare(right.id));
  const jobs = sources.map((source) => {
    const route = operations.filter((operation) => operation.batchId === source.id).sort((left, right) => left.sequence - right.sequence || Number(right.actual) - Number(left.actual));
    const completion2 = route.at(-1)?.end ?? source.releaseAt;
    const customRouteComplete = !source.masterProduct.route || source.masterProduct.route.length > 0 && !warnings.some((warning) => warning.product === source.product && warning.code === "invalid-route") && source.masterProduct.route.every((process2) => route.some((operation) => (operation.recordedProcess ?? operation.process) === process2)) && source.lot?.stage !== "on-hold" && source.lot?.stage !== "unclassified";
    const deliveryReadyAt = !customRouteComplete ? 0 : source.lot?.stage === "delivery-ready" ? source.lot.readyAt : source.masterProduct.route || route.some((operation) => operation.process === "gkm") ? routedDeliveryReadyAt(seed, completion2) : 0;
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

// lib/delivery-readiness.ts
function datedEvents(seed, result, processPlan) {
  const representedBatchIds = /* @__PURE__ */ new Set([
    ...processPlan.jobs.filter((job) => job.source === "turning-plan" && Boolean(seed.processMasterData)).map((job) => job.batchId),
    ...(seed.wipLots ?? []).map((lot) => lot.sourceBatchId).filter(Boolean)
  ]);
  const representedLotIds = new Set(processPlan.jobs.filter((job) => job.source === "wip" && job.deliveryReadyAt > 0).map((job) => job.batchId));
  const routed = processPlan.jobs.filter((job) => {
    const lot = seed.wipLots?.find((item) => item.id === job.wipLotId);
    return !lot || lot.stage !== "on-hold" && lot.stage !== "unclassified";
  }).filter((job) => job.quantity > 0 && job.deliveryReadyAt > 0 && (Boolean(processMasterDataForProduct(seed.processMasterData, job.product)?.route) || job.operations.some((operation) => operation.process === "gkm") || (seed.wipLots ?? []).some((lot) => lot.id === job.wipLotId && lot.stage === "delivery-ready"))).map((job) => ({ id: `route:${job.batchId}`, product: job.product.toUpperCase(), quantity: job.quantity, readyAt: job.deliveryReadyAt, source: "routed", routeSource: job.source, wipLotId: job.wipLotId }));
  const fallbackBatches = result.batches.filter((batch) => !seed.processMasterData && batch.status === "planned" && !batch.interruptionId && batch.quantity > 0 && batch.end > 0 && !representedBatchIds.has(batch.id)).map((batch) => ({ id: `batch:${batch.id}`, product: batch.product.toUpperCase(), quantity: batch.quantity, readyAt: turningDeliveryReadyAt(batch.end), source: "turning-fallback" }));
  const fallbackReadyWip = (seed.wipLots ?? []).filter((lot) => !seed.processMasterData && lot.stage === "delivery-ready" && lot.availableQuantity > 0 && lot.readyAt > 0 && !representedLotIds.has(lot.id)).map((lot) => ({ id: `wip:${lot.id}`, product: lot.product.toUpperCase(), quantity: lot.availableQuantity, readyAt: lot.readyAt, source: "wip-fallback" }));
  return [...routed, ...fallbackBatches, ...fallbackReadyWip].filter((event) => Number.isFinite(event.readyAt) && event.readyAt > 0).sort((left, right) => left.readyAt - right.readyAt || left.id.localeCompare(right.id));
}
function buildDeliveryReadinessEvents(seed, result) {
  return datedEvents(seed, result, buildDownstreamProcessPlan(seed, result));
}
function buildDeliveryReadinessProjection(seed, result) {
  const plan = buildDownstreamProcessPlan(seed, result);
  const events = datedEvents(seed, result, plan);
  const subjects = /* @__PURE__ */ new Map();
  const put = (subject) => {
    if (!Number.isSafeInteger(subject.quantity) || subject.quantity < 0) throw new Error(`${subject.product} i\xE7in teslimat miktar\u0131 ge\xE7ersiz.`);
    if (subject.quantity > 0) subjects.set(subject.id, subject);
  };
  for (const job of plan.jobs) put({ id: job.batchId, product: job.product, quantity: job.quantity, workOrder: job.workOrder, source: job.source });
  const lots = seed.wipLots ?? [];
  for (const lot of lots.filter((lot2) => lot2.availableQuantity > 0 && lot2.stage !== "delivered" && lot2.stage !== "scrapped")) {
    put({ id: lot.id, product: lot.product, quantity: lot.availableQuantity, workOrder: lot.workOrder ?? "", source: "wip" });
  }
  for (const machine of seed.machines.filter((m) => m.currentJob.product && m.currentJob.quantity > 0)) {
    put({ id: `current:${machine.id}`, product: machine.currentJob.product, quantity: machine.currentJob.quantity, workOrder: machine.currentJob.workOrder ?? "", source: "current-turning" });
  }
  for (const batch of result.batches.filter((b) => b.status === "planned" && b.quantity > 0)) {
    if (!batch.interruptionId && lots.some((lot) => lot.sourceBatchId === batch.id)) continue;
    put({ id: batch.id, product: batch.product, quantity: batch.quantity, workOrder: batch.workOrder ?? "", source: "turning-plan" });
  }
  const datedIds = new Set(events.map((e) => e.id.replace(/^(route|batch|wip):/, "")));
  const undated = [...subjects.values()].filter((s) => !datedIds.has(s.id)).map((subject) => {
    const job = plan.jobs.find((j) => j.batchId === subject.id);
    const warnings = plan.warnings.filter((w) => w.batchId === subject.id || !w.batchId && w.product === subject.product);
    const reasons = job?.readinessIssues?.length ? job.readinessIssues : warnings.length ? warnings.map((w) => ({ code: w.code, message: w.message })) : [{ code: "missing-schedule", message: "Rota tamamlanmad\u0131; proses, kabul veya kapasite bekleniyor." }];
    return { ...subject, product: subject.product.trim().toUpperCase(), reasons };
  });
  return { events, undated, undatedQuantity: undated.reduce((sum, row) => sum + row.quantity, 0) };
}

// lib/delivery-deduction.ts
function effectiveDeliveryTimestamp(entry) {
  if (entry.deliveredAtTime && Number.isFinite(Date.parse(entry.deliveredAtTime))) return new Date(entry.deliveredAtTime).toISOString();
  const deliveryDate = entry.deliveredAt?.slice(0, 10) ?? "";
  if (deliveryDate && entry.statusChangedAt && factoryDateInput(entry.statusChangedAt) === deliveryDate) {
    return new Date(entry.statusChangedAt).toISOString();
  }
  if (deliveryDate) return (/* @__PURE__ */ new Date(`${deliveryDate}T00:00:00+03:00`)).toISOString();
  return entry.statusChangedAt && Number.isFinite(Date.parse(entry.statusChangedAt)) ? new Date(entry.statusChangedAt).toISOString() : "";
}

// lib/delivery-plan.ts
var DAY_MS2 = 864e5;
var MAX_DELIVERY_PLAN_WEEKS = 53;
function serialToIsoDate(serial) {
  return excelSerialToDate(Math.floor(serial)).toISOString().slice(0, 10);
}
function isoDateToSerial(value) {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(value)) return Number.NaN;
  const timestamp = Date.parse(`${value}T00:00:00Z`);
  if (!Number.isFinite(timestamp) || new Date(timestamp).toISOString().slice(0, 10) !== value) return Number.NaN;
  return (timestamp - Date.UTC(1899, 11, 30)) / DAY_MS2;
}
function isoWeek(serial) {
  const date = excelSerialToDate(Math.floor(serial));
  const day = date.getUTCDay() || 7;
  date.setUTCDate(date.getUTCDate() + 4 - day);
  const yearStart = new Date(Date.UTC(date.getUTCFullYear(), 0, 1));
  return Math.ceil(((date.getTime() - yearStart.getTime()) / DAY_MS2 + 1) / 7);
}
function weekStart(serial) {
  const date = excelSerialToDate(Math.floor(serial));
  const day = date.getUTCDay() || 7;
  return Math.floor(serial) - day + 1;
}
function deliveryPlanDefaultRange(today = factoryDateInput()) {
  const todaySerial = isoDateToSerial(today);
  const start = weekStart(todaySerial);
  return { startDate: serialToIsoDate(start), endDate: serialToIsoDate(start + 41) };
}
function scheduledCompletionEvents(seed, result) {
  return buildDeliveryReadinessEvents(seed, result);
}
function deliveryPlanRangeWeekCount(range) {
  const start = isoDateToSerial(range.startDate);
  const end = isoDateToSerial(range.endDate);
  if (!Number.isFinite(start) || !Number.isFinite(end)) throw new Error("Ba\u015Flang\u0131\xE7 ve biti\u015F tarihini se\xE7in.");
  if (end < start) throw new Error("Biti\u015F tarihi ba\u015Flang\u0131\xE7 tarihinden \xF6nce olamaz.");
  const weekCount = Math.floor((weekStart(end) - weekStart(start)) / 7) + 1;
  if (weekCount > MAX_DELIVERY_PLAN_WEEKS) throw new Error(`Teslimat plan\u0131 en fazla ${MAX_DELIVERY_PLAN_WEEKS} takvim haftas\u0131n\u0131 kapsayabilir.`);
  return weekCount;
}
function buildDeliveryPlanPayload(seed, result, range = deliveryPlanDefaultRange(), today = factoryDateInput(), readiness) {
  const start = isoDateToSerial(range.startDate);
  const end = isoDateToSerial(range.endDate);
  const weekCount = deliveryPlanRangeWeekCount(range);
  const firstWeek = weekStart(start);
  const currentWeekStart = weekStart(isoDateToSerial(today));
  const customerDemand = seed.customerDemand;
  const orderDate = customerDemand?.snapshotDate ?? "";
  const cutoff = customerDemand ? isoDateToSerial(orderDate) : Number.NaN;
  if (customerDemand && !Number.isFinite(cutoff)) throw new Error("M\xFC\u015Fteri dosyas\u0131n\u0131n sipari\u015F tarihi ge\xE7erli de\u011Fil. Dosyay\u0131 yeniden y\xFCkleyin.");
  const calendarWeeks = Array.from({ length: weekCount }, (_, index) => ({ start: firstWeek + index * 7, label: `KW${isoWeek(firstWeek + index * 7)}` }));
  const carryoverLots = activeWipLots(seed);
  const carryoverByProduct = /* @__PURE__ */ new Map();
  for (const lot of carryoverLots) {
    const product = lot.product.trim().toUpperCase();
    carryoverByProduct.set(product, (carryoverByProduct.get(product) ?? 0) + Math.max(0, Math.trunc(lot.availableQuantity)));
  }
  const completions = (readiness?.events ?? scheduledCompletionEvents(seed, result)).filter((completion) => completion.readyAt >= start && completion.readyAt < end + 1);
  const seenDeliveries = /* @__PURE__ */ new Set();
  const delivered = (seed.productionHistory ?? []).flatMap((entry) => {
    if (entry.inventoryStatus !== "delivered" || entry.completedQuantity <= 0) return [];
    if (seenDeliveries.has(entry.id)) return [];
    seenDeliveries.add(entry.id);
    const timestamp = effectiveDeliveryTimestamp(entry);
    const deliveredAt = timestamp ? isoDateToSerial(factoryDateInput(timestamp)) : Number.NaN;
    if (!Number.isFinite(deliveredAt) || deliveredAt < start || deliveredAt >= end + 1) return [];
    return [{ id: entry.id, product: entry.product.trim().toUpperCase(), quantity: Math.max(0, Math.trunc(entry.completedQuantity)), deliveredAt }];
  });
  const weeks = calendarWeeks.flatMap((week) => {
    const columns = [];
    const hasActual = delivered.some((entry) => weekStart(entry.deliveredAt) === week.start);
    if (customerDemand) {
      if (week.start <= weekStart(cutoff)) columns.push({ ...week, label: `${week.label}
Sipari\u015F \xF6ncesi
Ger\xE7ekle\u015Fen`, kind: "actual-before-order" });
      if (week.start >= weekStart(cutoff) && (week.start <= currentWeekStart || hasActual)) columns.push({ ...week, label: `${week.label}
Sipari\u015F sonras\u0131
Ger\xE7ekle\u015Fen`, kind: "actual-after-order" });
    } else if (week.start <= currentWeekStart || hasActual) {
      columns.push({ ...week, label: `${week.label}
Ger\xE7ekle\u015Fen`, kind: "actual" });
    }
    if (week.start === currentWeekStart) columns.push({ ...week, label: `${week.label}'e
Devreden`, kind: "carryover" });
    if (week.start >= currentWeekStart || completions.some((entry) => weekStart(entry.readyAt) === week.start)) columns.push({ ...week, label: `${week.label}
Plan`, kind: "plan" });
    return columns;
  });
  const orderHorizonEnd = weekStart(end) + 6;
  const orderQuantityByProduct = /* @__PURE__ */ new Map();
  const familyByProduct2 = /* @__PURE__ */ new Map();
  if (customerDemand) {
    const selectedWeek = customerDemand.weeks.find((week) => isoDateToSerial(week.weekStart) === weekStart(end));
    if (!selectedWeek) throw new Error("Se\xE7ilen biti\u015F haftas\u0131 m\xFC\u015Fteri dosyas\u0131nda yok. Dosyadaki haftalardan birini se\xE7in veya g\xFCncel dosyay\u0131 y\xFCkleyin.");
    for (const item of customerDemand.products) {
      const product = item.product.trim().toUpperCase();
      const point = item.weeklyDemands.find((week) => week.weekId === selectedWeek.id);
      if (!point || !Number.isFinite(point.balance)) throw new Error(`${product} i\xE7in se\xE7ilen haftan\u0131n m\xFC\u015Fteri ihtiyac\u0131 bulunamad\u0131.`);
      const quantity2 = Math.max(0, Math.trunc(-point.balance));
      if (quantity2 > 0) orderQuantityByProduct.set(product, quantity2);
      familyByProduct2.set(product, item.family.trim().toUpperCase());
    }
  } else for (const order of (seed.orderImportGrossOrders?.length ? seed.orderImportGrossOrders : seed.orders).filter((item) => {
    if (item.quantity <= 0) return false;
    const dueAt = isoDateToSerial(item.dueDate);
    return !Number.isFinite(dueAt) || dueAt < orderHorizonEnd + 1;
  })) {
    const product = order.product.trim().toUpperCase();
    orderQuantityByProduct.set(product, (orderQuantityByProduct.get(product) ?? 0) + Math.max(0, Math.trunc(order.quantity)));
  }
  const products = [.../* @__PURE__ */ new Set([
    ...orderQuantityByProduct.keys(),
    ...delivered.map((entry) => entry.product),
    ...carryoverByProduct.keys(),
    ...completions.map((completion) => completion.product),
    ...readiness?.products ?? []
  ])];
  return {
    startDate: range.startDate,
    endDate: range.endDate,
    category: "\xDCretim",
    orderDate,
    sourceFile: customerDemand?.sourceFile ?? seed.orderImport?.sourceFile ?? "",
    demandSource: customerDemand ? "customer-snapshot" : seed.orderImport ? "imported-orders" : "manual-orders",
    weeks: weeks.map(({ label, kind }) => ({ label, kind })),
    rows: products.map((product) => ({
      product,
      family: familyByProduct2.get(product) || (() => {
        const family = resolvedProductSetupFamily(product, seed.products?.find((item) => item.product === product)?.setupFamily);
        return family === "piston" ? "PISTON" : family === "center-pin" ? "CENTER PIN" : "";
      })(),
      orderQuantity: orderQuantityByProduct.get(product) ?? 0,
      weeklyQuantities: weeks.map((week) => {
        if (week.kind === "carryover") return carryoverByProduct.get(product) ?? 0;
        if (week.kind === "actual" || week.kind === "actual-before-order" || week.kind === "actual-after-order") return delivered.filter((entry) => week.kind === "actual" || (week.kind === "actual-before-order" ? entry.deliveredAt < cutoff : entry.deliveredAt >= cutoff)).filter((entry) => entry.product === product && entry.deliveredAt >= Math.max(start, week.start) && entry.deliveredAt < Math.min(end + 1, week.start + 7)).reduce((sum, entry) => sum + entry.quantity, 0);
        return completions.filter((completion) => completion.product === product && completion.readyAt >= Math.max(start, week.start) && completion.readyAt < Math.min(end + 1, week.start + 7)).reduce((sum, completion) => sum + Math.max(0, Math.trunc(completion.quantity)), 0);
      })
    }))
  };
}

// lib/plan-integrity.ts
var code = (value) => value.trim().toUpperCase();
function fail(message) {
  throw new Error(`Plan g\xFCvenilirlik kontrol\xFC: ${message}`);
}
function unique2(values, label) {
  if (values.some((value) => !value) || new Set(values).size !== values.length) fail(`${label} kimlikleri eksik veya tekrarl\u0131.`);
}
function quantity(value, label) {
  if (!Number.isFinite(value) || value < 0) fail(`${label} sonlu ve s\u0131f\u0131rdan b\xFCy\xFCk veya e\u015Fit olmal\u0131.`);
}
function assertPlanInputs(seed, fixed) {
  unique2(seed.orders.map((order) => order.id), "Sipari\u015F");
  unique2(seed.products.map((product) => code(product.product)), "\xDCr\xFCn");
  unique2(seed.machines.map((machine) => machine.id), "Tezgah");
  unique2((seed.productionHistory ?? []).map((entry) => entry.id), "\xDCretim ar\u015Fivi");
  unique2(fixed.map((batch) => batch.id), "Korunan \u015Farj");
  for (const order of seed.orders) {
    quantity(order.quantity, `${order.product} sipari\u015F adedi`);
    if (order.dueDate && !validDate(order.dueDate)) fail(`${order.product} termin tarihi ge\xE7ersiz.`);
    for (const milestone of order.deliveryMilestones ?? []) {
      quantity(milestone.quantity, `${order.product} ara teslim adedi`);
      if (!validDate(milestone.date) || milestone.quantity > order.quantity) fail(`${order.product} ara teslim bilgisi ge\xE7ersiz.`);
    }
  }
  for (const product of seed.products) quantity(product.batchSize, `${product.product} \u015Farj b\xFCy\xFCkl\xFC\u011F\xFC`);
  for (const [product, stock] of Object.entries(seed.openingStock ?? {})) quantity(stock, `${product} a\xE7\u0131l\u0131\u015F sto\u011Fu`);
  for (const entry of seed.productionHistory ?? []) quantity(entry.completedQuantity, `${entry.product} fiili \xFCretim`);
  for (const machine of seed.machines) {
    quantity(machine.currentJob.quantity, `${machine.id} mevcut i\u015F adedi`);
    if (machine.currentJob.quantity > 0 && (!Number.isFinite(machine.currentJob.start) || !Number.isFinite(machine.currentJob.end) || machine.currentJob.end < machine.currentJob.start)) fail(`${machine.id} mevcut i\u015F tarihleri ge\xE7ersiz.`);
    if (machine.active && ![machine.availableStart, machine.planEnd, machine.shiftFactor, machine.capacityFactor ?? 1, machine.finishOffset].every(Number.isFinite)) fail(`${machine.id} tarih veya kapasite girdisi ge\xE7ersiz.`);
    for (const rate of Object.values(machine.rates)) quantity(rate, `${machine.id} \xFCretim h\u0131z\u0131`);
  }
  for (const batch of fixed) {
    quantity(batch.quantity, `${batch.product} korunan \u015Farj adedi`);
    if (batch.status !== "planned" || !seed.machines.some((machine) => machine.id === batch.machineId) || !Number.isFinite(batch.start) || !Number.isFinite(batch.end) || batch.start <= 0 || batch.end < batch.start) fail(`${batch.product} korunan \u015Farj kayd\u0131 ge\xE7ersiz; mevcut plan korundu.`);
  }
}
function validDate(value) {
  const time = Date.parse(`${value}T00:00:00Z`);
  return /^\d{4}-\d{2}-\d{2}$/.test(value) && Number.isFinite(time) && new Date(time).toISOString().slice(0, 10) === value;
}

// lib/delivery-report.ts
function summarizeDeliveryPlan(payload) {
  const grouped = /* @__PURE__ */ new Map();
  for (const row of payload.rows) {
    const product = row.product.trim().toUpperCase();
    const item = grouped.get(product) ?? { product, demand: 0, delivered: 0, periodActual: 0, remaining: 0, total: 0, difference: 0, shortage: 0 };
    item.demand += row.orderQuantity;
    payload.weeks.forEach((week, index) => {
      const quantity2 = row.weeklyQuantities[index] ?? 0;
      if (week.kind === "plan") item.remaining += quantity2;
      if (week.kind === "actual" || week.kind === "actual-after-order") item.delivered += quantity2;
      if (week.kind === "actual" || week.kind === "actual-after-order" || week.kind === "actual-before-order") item.periodActual += quantity2;
    });
    grouped.set(product, item);
  }
  const rows = [...grouped.values()].map((row) => ({
    ...row,
    total: row.periodActual + row.remaining,
    difference: row.delivered + row.remaining - row.demand,
    shortage: Math.min(0, row.delivered + row.remaining - row.demand)
  }));
  const sum = (key) => rows.reduce((total, row) => total + row[key], 0);
  const demand = sum("demand"), shortage = sum("shortage");
  return {
    rows,
    demand,
    delivered: sum("delivered"),
    remaining: sum("remaining"),
    total: sum("total"),
    difference: sum("difference"),
    shortage,
    coverage: demand > 0 ? 1 + shortage / demand : null,
    types: {
      listed: rows.length,
      demand: rows.filter((r) => r.demand > 0).length,
      delivered: rows.filter((r) => r.delivered > 0).length,
      remaining: rows.filter((r) => r.remaining > 0).length,
      total: rows.filter((r) => r.total > 0).length,
      covered: rows.filter((r) => r.difference >= 0).length,
      surplus: rows.filter((r) => r.difference > 0).length,
      shortage: rows.filter((r) => r.shortage < 0).length
    }
  };
}
function buildDeliveryReport(inputSeed, result, range, today = factoryDateInput()) {
  try {
    const seed = structuredClone(inputSeed);
    rollForwardUnfinishedProduction(seed, (Date.parse(`${today}T00:00:00Z`) - Date.UTC(1899, 11, 30)) / 864e5, { turning: false });
    assertPlanInputs(seed, []);
    for (const records of [result.batches, seed.wipLots ?? []]) {
      const ids = records.map((row) => row.id);
      if (ids.some((id) => !id) || new Set(ids).size !== ids.length) throw new Error("Teslimat hesab\u0131nda malzeme kimlikleri eksik veya tekrarl\u0131.");
    }
    for (const batch of result.batches) if (!Number.isSafeInteger(batch.quantity) || batch.quantity < 0) throw new Error(`${batch.product}: \u015Farj adedi ge\xE7ersiz.`);
    for (const lot of seed.wipLots ?? []) {
      const amounts = [lot.availableQuantity, lot.deliveredQuantity ?? 0, lot.scrappedQuantity ?? 0];
      if (amounts.some((n) => !Number.isSafeInteger(n) || n < 0) || lot.originalQuantity != null && amounts.reduce((a, b) => a + b, 0) > lot.originalQuantity)
        throw new Error(`${lot.workOrder || lot.product}: yar\u0131 mam\xFCl miktarlar\u0131 uzla\u015Fm\u0131yor.`);
    }
    const reconciled = reconcileTurningQueue(seed, result.batches);
    if (reconciled.length !== result.batches.length) throw new Error("\u015Earj kimlikleri \xE7ak\u0131\u015F\u0131yor; teslimat raporu do\u011Frulanamad\u0131.");
    let projected = result;
    let turningIssue = "";
    if (seed.planNeedsRecalculation && result.batches.length) {
      try {
        projected = recalculateManualScenario(structuredClone(seed), structuredClone(result.batches));
      } catch (error) {
        turningIssue = error instanceof Error ? error.message : "Torna tarihleri hesaplanamad\u0131.";
      }
    }
    if (projected.batches.length !== result.batches.length) throw new Error("Teslimat hesab\u0131nda kay\u0131tl\u0131 \u015Farjlar korunamad\u0131.");
    for (const original of result.batches) {
      const next = projected.batches.find((b) => b.id === original.id);
      if (!next || next.quantity !== original.quantity || next.machineId !== original.machineId || next.product !== original.product)
        throw new Error("Teslimat hesab\u0131nda \u015Farj kimli\u011Fi veya miktar\u0131 korunamad\u0131.");
      if ((original.locked || original.manuallyPlaced) && (Math.abs(next.start - original.start) > 1e-7 || Math.abs(next.end - original.end) > 1e-7))
        turningIssue = `${original.workOrder || original.product}: g\xFCncel kapasite korunan yerle\u015Fimle uyu\u015Fmuyor. Yerle\u015Fimi inceleyin.`;
    }
    if (turningIssue) projected = { ...result, batches: result.batches.map((batch) => batch.status === "planned" ? { ...batch, start: 0, end: 0 } : batch) };
    else projected = { ...projected, batches: projected.batches.map((batch) => batch.status === "planned" && (!Number.isFinite(batch.start) || !Number.isFinite(batch.end) || batch.start <= 0 || batch.end < batch.start) ? { ...batch, start: 0, end: 0 } : batch) };
    const readiness = buildDeliveryReadinessProjection(seed, projected);
    if (turningIssue) for (const row of readiness.undated.filter((row2) => row2.source === "turning-plan")) row.reasons = [{ code: "turning-projection-blocked", message: turningIssue }];
    const payload = buildDeliveryPlanPayload(seed, projected, range, today, { events: readiness.events, products: readiness.undated.map((row) => row.product) });
    return { ...summarizeDeliveryPlan(payload), ...readiness, payload, error: "", complete: readiness.undated.length === 0 };
  } catch (error) {
    return { error: error instanceof Error ? error.message : "Teslimat bilgileri hesaplanamad\u0131.", payload: null, rows: [], events: [], undated: [], undatedQuantity: null, complete: false };
  }
}

// scripts/delivery-runtime.ts
try {
  const request = JSON.parse((0, import_node_fs.readFileSync)(0, "utf8"));
  const seed = request.seed;
  if (!seed || ![seed.orders, seed.products, seed.machines, seed.preferences].every(Array.isArray)) throw Error("Kay\u0131tl\u0131 plan \u015Femas\u0131 ge\xE7ersiz.");
  for (const key of ["orders", "products", "machines", "manualBatches", "wipLots", "productionHistory", "processOperationOverrides"]) {
    const rows = seed[key] ?? [];
    if (!Array.isArray(rows) || rows.length > 2e4) throw Error("Kay\u0131tl\u0131 plan boyutu veya \u015Femas\u0131 ge\xE7ersiz.");
  }
  for (const rows of [seed.wipLots ?? [], seed.productionHistory ?? []]) {
    const ids = rows.map((row) => row.id);
    if (ids.some((id) => !id) || new Set(ids).size !== ids.length) throw Error("Malzeme kimlikleri eksik veya tekrarl\u0131.");
  }
  if (!/^\d{4}-\d{2}-\d{2}$/.test(request.today)) throw Error("Hesaplama tarihi ge\xE7ersiz.");
  const result = scenarioResultFromBatches(seed, seed.manualBatches ?? []);
  process.stdout.write(JSON.stringify(buildDeliveryReport(seed, result, request.range, request.today)));
} catch {
  process.stdout.write(JSON.stringify({ error: "Kay\u0131tl\u0131 \xFCretim verisi teslimat hesab\u0131 i\xE7in do\u011Frulanamad\u0131.", payload: null, complete: false, rows: [], events: [], undated: [], undatedQuantity: null }));
}
