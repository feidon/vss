// Build a focused PPT with diagrams that explain VSS concepts hard to convey in text.
// Run with: NODE_PATH=$(npm root -g) node build.js
// Output (VSS-Visual-Reference.pptx) is written next to this script.

const path = require("path");
const pptxgen = require("pptxgenjs");
const React = require("react");
const ReactDOMServer = require("react-dom/server");
const sharp = require("sharp");
const {
  FaCarSide,
  FaCubes,
  FaLock,
  FaBatteryQuarter,
  FaPlug,
  FaUserCog,
  FaUnlink,
} = require("react-icons/fa");

// =========================================================
// Theme - Ocean Gradient (transit-appropriate)
// =========================================================
const T = {
  BG_DARK: "0A1128",
  PRIMARY: "065A82",
  SECONDARY: "1C7293",
  ACCENT: "F18F01",
  BG_LIGHT: "F8FAFC",
  CARD: "FFFFFF",
  TEXT: "1E293B",
  MUTED: "64748B",
  BORDER: "CBD5E1",
  GREEN: "059669",
  RED: "DC2626",
};

const FONT_HEAD = "Calibri";
const FONT_BODY = "Calibri";

// =========================================================
// Helpers
// =========================================================

function renderIconSvg(IconComponent, color = "#000000", size = 256) {
  return ReactDOMServer.renderToStaticMarkup(
    React.createElement(IconComponent, { color, size: String(size) })
  );
}

async function iconPng(IconComponent, hexColor) {
  const svg = renderIconSvg(IconComponent, "#" + hexColor, 256);
  const buf = await sharp(Buffer.from(svg)).png().toBuffer();
  return "image/png;base64," + buf.toString("base64");
}

const shadow = () => ({
  type: "outer",
  color: "000000",
  blur: 10,
  offset: 2,
  angle: 90,
  opacity: 0.1,
});

// Small helper: top accent bar + slide title block
function addHeader(slide, title, subtitle) {
  slide.addShape("rect", {
    x: 0, y: 0, w: 13.3, h: 0.18,
    fill: { color: T.PRIMARY }, line: { color: T.PRIMARY, width: 0 },
  });
  slide.addText(title, {
    x: 0.6, y: 0.35, w: 12.1, h: 0.7,
    fontFace: FONT_HEAD, fontSize: 30, bold: true, color: T.TEXT, margin: 0,
  });
  if (subtitle) {
    slide.addText(subtitle, {
      x: 0.6, y: 1.0, w: 12.1, h: 0.4,
      fontFace: FONT_BODY, fontSize: 14, color: T.MUTED, italic: true, margin: 0,
    });
  }
}

// Boxed entity card for ER diagram
function addEntityBox(slide, x, y, w, h, name, fields, opts = {}) {
  const accent = opts.accent || T.PRIMARY;
  const headerH = 0.5;
  // Card body
  slide.addShape("rect", {
    x, y, w, h,
    fill: { color: T.CARD },
    line: { color: T.BORDER, width: 1 },
    shadow: shadow(),
  });
  // Header bar
  slide.addShape("rect", {
    x, y, w, h: headerH,
    fill: { color: accent }, line: { color: accent, width: 0 },
  });
  // Entity name
  slide.addText(name, {
    x: x + 0.1, y: y + 0.04, w: w - 0.2, h: headerH - 0.08,
    fontFace: FONT_HEAD, fontSize: 14, bold: true, color: "FFFFFF", margin: 0,
    valign: "middle",
  });
  // Field list
  const fieldRuns = fields.map((f, i) => ({
    text: f,
    options: {
      bullet: { code: "2022" },
      color: T.TEXT,
      breakLine: i < fields.length - 1,
    },
  }));
  slide.addText(fieldRuns, {
    x: x + 0.18, y: y + headerH + 0.05, w: w - 0.3, h: h - headerH - 0.1,
    fontFace: FONT_BODY, fontSize: opts.fontSize || 11, color: T.TEXT,
    paraSpaceAfter: 2, margin: 0, valign: "top",
  });
}

// Connector with optional label
function addConnector(slide, x1, y1, x2, y2, label) {
  slide.addShape("line", {
    x: x1, y: y1, w: x2 - x1, h: y2 - y1,
    line: { color: T.SECONDARY, width: 1.75, endArrowType: "triangle" },
  });
  if (label) {
    slide.addText(label, {
      x: (x1 + x2) / 2 - 0.5, y: (y1 + y2) / 2 - 0.18, w: 1.0, h: 0.32,
      fontFace: FONT_BODY, fontSize: 10, color: T.PRIMARY, bold: true,
      align: "center", valign: "middle", margin: 0,
      fill: { color: T.BG_LIGHT },
    });
  }
}

// Footer page number
function addFooter(slide, n, total) {
  slide.addText(`${n} / ${total}`, {
    x: 12.4, y: 7.1, w: 0.8, h: 0.3,
    fontFace: FONT_BODY, fontSize: 10, color: T.MUTED, align: "right", margin: 0,
  });
  slide.addText("VSS · Visual Reference", {
    x: 0.6, y: 7.1, w: 6.0, h: 0.3,
    fontFace: FONT_BODY, fontSize: 10, color: T.MUTED, align: "left", margin: 0,
  });
}

// =========================================================
// Build presentation
// =========================================================
async function build() {
  const pres = new pptxgen();
  pres.layout = "LAYOUT_WIDE"; // 13.3 x 7.5
  pres.author = "VSS";
  pres.title = "Vehicle Scheduling System — Visual Reference";

  const TOTAL = 8;

  // Pre-render icons used in slide 7
  const ICON = {
    overlap: await iconPng(FaCarSide, T.PRIMARY),
    block: await iconPng(FaCubes, T.PRIMARY),
    interlock: await iconPng(FaLock, T.PRIMARY),
    lowBat: await iconPng(FaBatteryQuarter, T.PRIMARY),
    charge: await iconPng(FaPlug, T.PRIMARY),
    discontinuity: await iconPng(FaUnlink, T.PRIMARY),
    operator: await iconPng(FaUserCog, "FFFFFF"),
  };

  // ---------------------------------------------------------
  // Slide 1 — Title (dark)
  // ---------------------------------------------------------
  {
    const s = pres.addSlide();
    s.background = { color: T.BG_DARK };
    // Decorative accent bars
    s.addShape("rect", { x: 0, y: 0, w: 0.35, h: 7.5, fill: { color: T.PRIMARY }, line: { color: T.PRIMARY, width: 0 } });
    s.addShape("rect", { x: 0.35, y: 0, w: 0.08, h: 7.5, fill: { color: T.SECONDARY }, line: { color: T.SECONDARY, width: 0 } });
    s.addShape("rect", { x: 0.55, y: 6.55, w: 1.6, h: 0.08, fill: { color: T.ACCENT }, line: { color: T.ACCENT, width: 0 } });

    s.addText("Vehicle Scheduling System", {
      x: 0.9, y: 2.2, w: 12.0, h: 1.2,
      fontFace: FONT_HEAD, fontSize: 54, bold: true, color: "FFFFFF", margin: 0,
    });
    s.addText("Visual Reference", {
      x: 0.9, y: 3.4, w: 12.0, h: 0.8,
      fontFace: FONT_HEAD, fontSize: 32, color: T.SECONDARY, margin: 0,
    });
    s.addText("Diagrams for the parts that text alone can't carry.", {
      x: 0.9, y: 4.2, w: 12.0, h: 0.5,
      fontFace: FONT_BODY, fontSize: 18, italic: true, color: "CADCFC", margin: 0,
    });
    s.addText([
      { text: "Domain Model", options: {} },
      { text: "   ·   ", options: { color: T.ACCENT } },
      { text: "Use Cases", options: {} },
      { text: "   ·   ", options: { color: T.ACCENT } },
      { text: "Architecture", options: {} },
      { text: "   ·   ", options: { color: T.ACCENT } },
      { text: "Workflows", options: {} },
      { text: "   ·   ", options: { color: T.ACCENT } },
      { text: "Conflict Types", options: {} },
    ], {
      x: 0.9, y: 6.7, w: 12.0, h: 0.4,
      fontFace: FONT_BODY, fontSize: 13, color: "CADCFC", margin: 0,
    });
  }

  // ---------------------------------------------------------
  // Slide 2 — Use Cases
  // ---------------------------------------------------------
  {
    const s = pres.addSlide();
    s.background = { color: T.BG_LIGHT };
    addHeader(s, "Use Case Map", "Each page → its API operations → domain logic → the entities it touches");

    // Sticky-note-style category colors (4 tracks)
    const C_PAGE = "C03221";    // red — pages
    const C_OP = "5B5FAC";      // indigo — API operations
    const C_DOMAIN = T.SECONDARY; // teal — domain logic
    const C_ENT_BG = "FFF6D6";  // soft yellow card bg
    const C_ENT_BORDER = "CFA300";
    const C_ENT_TXT = "7A5A00";

    // Lane data — derived from actual frontend routes & component code
    const lanes = [
      {
        name: "Schedule List",
        path: "/schedule",
        role: "Browse · Create · Delete · Auto-generate",
        ops: [
          "GET  /services",
          "GET  /services/{id}",
          "POST  /services",
          "DELETE  /services/{id}",
          "POST  /schedules/generate",
        ],
        domain: [
          "Aggregate read (list + expanded detail)",
          "Cascade delete",
          "Auto-gen runs BFS + timetable + 6 conflict checks",
        ],
        entities: "Service · Vehicle · Block",
      },
      {
        name: "Schedule Editor",
        path: "/schedule/:id/edit",
        role: "Edit one service's route",
        ops: [
          "GET  /services/{id}",
          "PATCH  /services/{id}/route",
        ],
        domain: [
          "BFS connectivity check",
          "Compute timetable (dwell + traversal)",
          "Detect 6 conflict types  →  409 on failure",
        ],
        entities: "Service · Block · NodeConnection",
      },
      {
        name: "Config",
        path: "/config",
        role: "Block table + Vehicle list",
        ops: [
          "GET  /blocks",
          "PATCH  /blocks/{id}",
          "GET  /vehicles",
        ],
        domain: [
          "Update traversal_time_seconds",
          "(existing services keep their timetables until re-saved)",
        ],
        entities: "Block · Vehicle",
      },
    ];

    // Layout
    const laneStartY = 1.45;
    const laneH = 1.74;
    const laneGap = 0.15;

    const pageX = 0.35, pageW = 1.85;
    const opX = 2.45,  opW = 3.65;
    const domX = 6.35, domW = 3.20;
    const entX = 9.80, entW = 3.15;

    function addArrow(x1, y1, x2, y2) {
      s.addShape("line", {
        x: x1, y: y1, w: x2 - x1, h: y2 - y1,
        line: { color: T.MUTED, width: 1.5, endArrowType: "triangle" },
      });
    }

    lanes.forEach((lane, i) => {
      const y = laneStartY + i * (laneH + laneGap);
      const yMid = y + laneH / 2;

      // ── Page card ───────────────────────────────────────
      s.addShape("rect", {
        x: pageX, y, w: pageW, h: laneH,
        fill: { color: "FFFFFF" }, line: { color: C_PAGE, width: 2 },
        shadow: shadow(),
      });
      s.addShape("rect", {
        x: pageX, y, w: pageW, h: 0.30,
        fill: { color: C_PAGE }, line: { color: C_PAGE, width: 0 },
      });
      s.addText("PAGE", {
        x: pageX + 0.12, y: y + 0.01, w: pageW - 0.24, h: 0.28,
        fontFace: FONT_BODY, fontSize: 9, bold: true, color: "FFFFFF",
        charSpacing: 2, margin: 0, valign: "middle",
      });
      s.addText(lane.name, {
        x: pageX + 0.12, y: y + 0.36, w: pageW - 0.24, h: 0.40,
        fontFace: FONT_HEAD, fontSize: 13, bold: true, color: T.TEXT, margin: 0,
      });
      s.addText(lane.path, {
        x: pageX + 0.12, y: y + 0.76, w: pageW - 0.24, h: 0.30,
        fontFace: "Consolas", fontSize: 10, color: C_PAGE, margin: 0,
      });
      s.addText(lane.role, {
        x: pageX + 0.12, y: y + 1.07, w: pageW - 0.24, h: 0.60,
        fontFace: FONT_BODY, fontSize: 9, italic: true, color: T.MUTED, margin: 0,
      });

      addArrow(pageX + pageW + 0.04, yMid, opX - 0.04, yMid);

      // ── Operations column ──────────────────────────────
      s.addShape("rect", {
        x: opX, y, w: opW, h: laneH,
        fill: { color: "F1F5F9" }, line: { color: T.BORDER, width: 1 },
      });
      s.addText("API OPERATIONS", {
        x: opX + 0.12, y: y + 0.04, w: opW - 0.24, h: 0.26,
        fontFace: FONT_BODY, fontSize: 9, bold: true, color: C_OP,
        charSpacing: 1.5, margin: 0,
      });
      const chipH = 0.25, chipGap = 0.04;
      const totalChipBlock = lane.ops.length * chipH + (lane.ops.length - 1) * chipGap;
      const chipsStart = y + 0.32 + Math.max(0, (laneH - 0.32 - totalChipBlock) / 2);
      lane.ops.forEach((op, j) => {
        const cy = chipsStart + j * (chipH + chipGap);
        s.addShape("rect", {
          x: opX + 0.12, y: cy, w: opW - 0.24, h: chipH,
          fill: { color: C_OP }, line: { color: C_OP, width: 0 },
        });
        s.addText(op, {
          x: opX + 0.20, y: cy, w: opW - 0.40, h: chipH,
          fontFace: "Consolas", fontSize: 10, bold: true, color: "FFFFFF",
          margin: 0, valign: "middle",
        });
      });

      addArrow(opX + opW + 0.04, yMid, domX - 0.04, yMid);

      // ── Domain logic column ────────────────────────────
      s.addShape("rect", {
        x: domX, y, w: domW, h: laneH,
        fill: { color: "E0F2F1" }, line: { color: C_DOMAIN, width: 1.5 },
      });
      s.addText("DOMAIN LOGIC", {
        x: domX + 0.12, y: y + 0.04, w: domW - 0.24, h: 0.26,
        fontFace: FONT_BODY, fontSize: 9, bold: true, color: C_DOMAIN,
        charSpacing: 1.5, margin: 0,
      });
      const domainRuns = lane.domain.map((d, j) => ({
        text: d,
        options: {
          bullet: { code: "2022" },
          color: T.TEXT,
          breakLine: j < lane.domain.length - 1,
        },
      }));
      s.addText(domainRuns, {
        x: domX + 0.18, y: y + 0.36, w: domW - 0.32, h: laneH - 0.42,
        fontFace: FONT_BODY, fontSize: 11, color: T.TEXT,
        paraSpaceAfter: 2, margin: 0, valign: "middle",
      });

      addArrow(domX + domW + 0.04, yMid, entX - 0.04, yMid);

      // ── Entities touched column ────────────────────────
      s.addShape("rect", {
        x: entX, y, w: entW, h: laneH,
        fill: { color: C_ENT_BG }, line: { color: C_ENT_BORDER, width: 1.5 },
      });
      s.addText("ENTITIES TOUCHED", {
        x: entX + 0.12, y: y + 0.04, w: entW - 0.24, h: 0.26,
        fontFace: FONT_BODY, fontSize: 9, bold: true, color: C_ENT_TXT,
        charSpacing: 1.5, margin: 0,
      });
      s.addText(lane.entities, {
        x: entX + 0.15, y: y + 0.4, w: entW - 0.3, h: laneH - 0.5,
        fontFace: FONT_HEAD, fontSize: 13, bold: true, color: T.TEXT,
        align: "center", valign: "middle", margin: 0,
      });
    });

    addFooter(s, 2, TOTAL);
  }

  // ---------------------------------------------------------
  // Slide 3 — Service Lifecycle
  // ---------------------------------------------------------
  {
    const s = pres.addSlide();
    s.background = { color: T.BG_LIGHT };
    addHeader(s, "Service Lifecycle", "From creation to a validated, persisted route");

    // Vertical flow on left side; outcome branch on right
    const stepW = 5.5, stepH = 0.78, stepX = 0.6;
    const startY = 1.55;
    const gap = 0.20;

    const steps = [
      {
        title: "POST  /api/services",
        body: "Create with name + vehicle_id  →  empty route",
        accent: T.PRIMARY,
      },
      {
        title: "PATCH  /api/services/{id}/route",
        body: "Send stops, dwell times, start_time",
        accent: T.PRIMARY,
      },
      {
        title: "Validate connectivity   (BFS)",
        body: "Walk directed block graph between consecutive stops",
        accent: T.SECONDARY,
      },
      {
        title: "Compute timetable",
        body: "Arrival / departure per node from dwell + traversal",
        accent: T.SECONDARY,
      },
      {
        title: "Conflict detection",
        body: "Sweep against all other services in memory",
        accent: T.SECONDARY,
      },
    ];

    steps.forEach((step, i) => {
      const y = startY + i * (stepH + gap);
      // Card
      s.addShape("rect", {
        x: stepX, y, w: stepW, h: stepH,
        fill: { color: T.CARD }, line: { color: T.BORDER, width: 1 },
        shadow: shadow(),
      });
      // Accent bar
      s.addShape("rect", {
        x: stepX, y, w: 0.12, h: stepH,
        fill: { color: step.accent }, line: { color: step.accent, width: 0 },
      });
      // Step number circle
      s.addShape("ellipse", {
        x: stepX + 0.3, y: y + 0.18, w: 0.5, h: 0.5,
        fill: { color: step.accent }, line: { color: step.accent, width: 0 },
      });
      s.addText(String(i + 1), {
        x: stepX + 0.3, y: y + 0.18, w: 0.5, h: 0.5,
        fontFace: FONT_HEAD, fontSize: 14, bold: true, color: "FFFFFF",
        align: "center", valign: "middle", margin: 0,
      });
      // Title
      s.addText(step.title, {
        x: stepX + 0.95, y: y + 0.08, w: stepW - 1.1, h: 0.4,
        fontFace: FONT_HEAD, fontSize: 14, bold: true, color: T.TEXT, margin: 0,
      });
      // Body
      s.addText(step.body, {
        x: stepX + 0.95, y: y + 0.45, w: stepW - 1.1, h: 0.35,
        fontFace: FONT_BODY, fontSize: 11, color: T.MUTED, margin: 0,
      });

      // Down arrow between steps
      if (i < steps.length - 1) {
        s.addShape("line", {
          x: stepX + 0.55, y: y + stepH + 0.02, w: 0, h: gap - 0.04,
          line: { color: T.MUTED, width: 1.5, endArrowType: "triangle" },
        });
      }
    });

    // Outcome cards (right side)
    const outX = 6.85;
    const outW = 6.0;
    const okY = 1.6, okH = 2.10;
    const errY = 4.00, errH = 2.70;
    const lastStepCenterY = startY + (steps.length - 1) * (stepH + gap) + stepH / 2;

    // OK card
    s.addShape("rect", {
      x: outX, y: okY, w: outW, h: okH,
      fill: { color: T.CARD }, line: { color: T.GREEN, width: 2 },
      shadow: shadow(),
    });
    s.addShape("rect", {
      x: outX, y: okY, w: outW, h: 0.42,
      fill: { color: T.GREEN }, line: { color: T.GREEN, width: 0 },
    });
    s.addText("200  OK    ·    Persist", {
      x: outX + 0.15, y: okY + 0.02, w: outW - 0.3, h: 0.38,
      fontFace: FONT_HEAD, fontSize: 14, bold: true, color: "FFFFFF",
      margin: 0, valign: "middle",
    });
    s.addText([
      { text: "Service stored with route + timetable.", options: { breakLine: true } },
      { text: "Conflict detection passed.", options: {} },
    ], {
      x: outX + 0.2, y: okY + 0.55, w: outW - 0.4, h: okH - 0.7,
      fontFace: FONT_BODY, fontSize: 13, color: T.TEXT, margin: 0,
    });

    // 409 card
    s.addShape("rect", {
      x: outX, y: errY, w: outW, h: errH,
      fill: { color: T.CARD }, line: { color: T.RED, width: 2 },
      shadow: shadow(),
    });
    s.addShape("rect", {
      x: outX, y: errY, w: outW, h: 0.42,
      fill: { color: T.RED }, line: { color: T.RED, width: 0 },
    });
    s.addText("409  Conflict", {
      x: outX + 0.15, y: errY + 0.02, w: outW - 0.3, h: 0.38,
      fontFace: FONT_HEAD, fontSize: 14, bold: true, color: "FFFFFF",
      margin: 0, valign: "middle",
    });
    s.addText([
      { text: "Returned with structured details:", options: { breakLine: true } },
      { text: "  ·  vehicle overlap", options: { breakLine: true } },
      { text: "  ·  vehicle discontinuity", options: { breakLine: true } },
      { text: "  ·  block occupancy", options: { breakLine: true } },
      { text: "  ·  interlocking", options: { breakLine: true } },
      { text: "  ·  low battery", options: { breakLine: true } },
      { text: "  ·  insufficient charge", options: { breakLine: true } },
      { text: " ", options: { breakLine: true } },
      { text: "Request was valid in isolation; conflict arose from current state.", options: { italic: true } },
    ], {
      x: outX + 0.2, y: errY + 0.5, w: outW - 0.4, h: errH - 0.6,
      fontFace: FONT_BODY, fontSize: 11, color: T.TEXT, margin: 0,
    });

    // Branch from step 5 right edge → junction → OK / 409
    const branchX = stepX + stepW + 0.05;            // start arrow x
    const junctionX = outX - 0.25;                    // vertical line x
    const okCenterY = okY + okH / 2;
    const errCenterY = errY + errH / 2;

    // Horizontal arrow from last step right edge into junction column
    s.addShape("line", {
      x: branchX, y: lastStepCenterY,
      w: junctionX - branchX, h: 0,
      line: { color: T.MUTED, width: 1.5 },
    });
    // Vertical dashed line spanning OK center → last step center
    s.addShape("line", {
      x: junctionX, y: okCenterY,
      w: 0, h: lastStepCenterY - okCenterY,
      line: { color: T.MUTED, width: 1.25, dashType: "dash" },
    });
    // Arrow into OK card
    s.addShape("line", {
      x: junctionX, y: okCenterY,
      w: outX - junctionX, h: 0,
      line: { color: T.GREEN, width: 1.75, endArrowType: "triangle" },
    });
    // Arrow into 409 card (branch off the same vertical line)
    s.addShape("line", {
      x: junctionX, y: errCenterY,
      w: outX - junctionX, h: 0,
      line: { color: T.RED, width: 1.75, endArrowType: "triangle" },
    });

    addFooter(s, 3, TOTAL);
  }

  // ---------------------------------------------------------
  // Slide 4 — Route Building Flow
  // ---------------------------------------------------------
  {
    const s = pres.addSlide();
    s.background = { color: T.BG_LIGHT };
    addHeader(s, "Route Building & Timetable", "Users pick stops; the system fills the rest");

    // Three step cards
    const stepW = 3.85, stepH = 2.5, stepY = 1.7, gap = 0.35;
    const stepX = [0.6, 0.6 + (stepW + gap), 0.6 + 2 * (stepW + gap)];

    // Step 1
    s.addShape("rect", {
      x: stepX[0], y: stepY, w: stepW, h: stepH,
      fill: { color: T.CARD }, line: { color: T.BORDER, width: 1 },
      shadow: shadow(),
    });
    s.addShape("rect", {
      x: stepX[0], y: stepY, w: 0.1, h: stepH,
      fill: { color: T.PRIMARY }, line: { color: T.PRIMARY, width: 0 },
    });
    s.addText("1   User Input", {
      x: stepX[0] + 0.25, y: stepY + 0.15, w: stepW - 0.4, h: 0.4,
      fontFace: FONT_HEAD, fontSize: 15, bold: true, color: T.PRIMARY, margin: 0,
    });
    s.addText([
      { text: "stops = [", options: { breakLine: true } },
      { text: "    P1A  (dwell 60s),", options: { breakLine: true } },
      { text: "    P2A  (dwell 45s),", options: { breakLine: true } },
      { text: "]", options: { breakLine: true } },
      { text: "start_time = T", options: {} },
    ], {
      x: stepX[0] + 0.25, y: stepY + 0.65, w: stepW - 0.4, h: stepH - 0.8,
      fontFace: "Consolas", fontSize: 12, color: T.TEXT, margin: 0,
    });

    // Step 2
    s.addShape("rect", {
      x: stepX[1], y: stepY, w: stepW, h: stepH,
      fill: { color: T.CARD }, line: { color: T.BORDER, width: 1 },
      shadow: shadow(),
    });
    s.addShape("rect", {
      x: stepX[1], y: stepY, w: 0.1, h: stepH,
      fill: { color: T.SECONDARY }, line: { color: T.SECONDARY, width: 0 },
    });
    s.addText("2   BFS Inference", {
      x: stepX[1] + 0.25, y: stepY + 0.15, w: stepW - 0.4, h: 0.4,
      fontFace: FONT_HEAD, fontSize: 15, bold: true, color: T.SECONDARY, margin: 0,
    });
    s.addText([
      { text: "Walks the directed", options: { breakLine: true } },
      { text: "block adjacency graph,", options: { breakLine: true } },
      { text: "shortest chain between", options: { breakLine: true } },
      { text: "consecutive stops.", options: { breakLine: true } },
      { text: " ", options: { breakLine: true } },
      { text: "Most stop pairs have", options: { breakLine: true } },
      { text: "exactly one valid path.", options: {} },
    ], {
      x: stepX[1] + 0.25, y: stepY + 0.65, w: stepW - 0.4, h: stepH - 0.8,
      fontFace: FONT_BODY, fontSize: 11, color: T.TEXT, margin: 0,
    });

    // Step 3
    s.addShape("rect", {
      x: stepX[2], y: stepY, w: stepW, h: stepH,
      fill: { color: T.CARD }, line: { color: T.BORDER, width: 1 },
      shadow: shadow(),
    });
    s.addShape("rect", {
      x: stepX[2], y: stepY, w: 0.1, h: stepH,
      fill: { color: T.ACCENT }, line: { color: T.ACCENT, width: 0 },
    });
    s.addText("3   Full Route + Timetable", {
      x: stepX[2] + 0.25, y: stepY + 0.15, w: stepW - 0.4, h: 0.4,
      fontFace: FONT_HEAD, fontSize: 15, bold: true, color: T.ACCENT, margin: 0,
    });
    s.addText([
      { text: "P1A → B3 → B5 → P2A", options: { breakLine: true } },
      { text: " ", options: { breakLine: true } },
      { text: "Arrival/departure", options: { breakLine: true } },
      { text: "computed per node from", options: { breakLine: true } },
      { text: "dwell + traversal times.", options: {} },
    ], {
      x: stepX[2] + 0.25, y: stepY + 0.65, w: stepW - 0.4, h: stepH - 0.8,
      fontFace: FONT_BODY, fontSize: 11, color: T.TEXT, margin: 0,
    });

    // Arrows between cards
    const arrowY = stepY + stepH / 2;
    s.addShape("line", {
      x: stepX[0] + stepW + 0.02, y: arrowY, w: gap - 0.04, h: 0,
      line: { color: T.MUTED, width: 2, endArrowType: "triangle" },
    });
    s.addShape("line", {
      x: stepX[1] + stepW + 0.02, y: arrowY, w: gap - 0.04, h: 0,
      line: { color: T.MUTED, width: 2, endArrowType: "triangle" },
    });

    // Timeline visualization
    const tlY = 4.85;
    s.addText("Timeline (example):  T = start_time", {
      x: 0.6, y: tlY - 0.4, w: 12.0, h: 0.3,
      fontFace: FONT_BODY, fontSize: 12, bold: true, color: T.PRIMARY, margin: 0,
    });
    // Time axis
    s.addShape("line", {
      x: 1.6, y: tlY + 1.7, w: 11.0, h: 0,
      line: { color: T.MUTED, width: 1 },
    });
    // Tick marks: T, T+60, T+90, T+120, T+165
    const xT = 1.6, xEnd = 12.6;
    const totalSec = 165;
    const xAt = (t) => xT + ((xEnd - xT) * t) / totalSec;
    const ticks = [
      { t: 0, label: "T" },
      { t: 60, label: "T+60" },
      { t: 90, label: "T+90" },
      { t: 120, label: "T+120" },
      { t: 165, label: "T+165" },
    ];
    for (const tk of ticks) {
      const x = xAt(tk.t);
      s.addShape("line", {
        x, y: tlY + 1.65, w: 0, h: 0.1,
        line: { color: T.MUTED, width: 1 },
      });
      s.addText(tk.label, {
        x: x - 0.5, y: tlY + 1.78, w: 1.0, h: 0.3,
        fontFace: FONT_BODY, fontSize: 9, color: T.MUTED, align: "center", margin: 0,
      });
    }
    // Segments
    function addSeg(label, t1, t2, row, color) {
      const x = xAt(t1);
      const w = xAt(t2) - x;
      const y = tlY + row * 0.35;
      s.addShape("rect", {
        x, y, w, h: 0.3,
        fill: { color }, line: { color, width: 0 },
      });
      s.addText(label, {
        x: x, y: y, w: w, h: 0.3,
        fontFace: FONT_BODY, fontSize: 10, bold: true, color: "FFFFFF",
        align: "center", valign: "middle", margin: 0,
      });
    }
    function addRowLabel(label, row) {
      s.addText(label, {
        x: 0.6, y: tlY + row * 0.35, w: 0.95, h: 0.3,
        fontFace: FONT_BODY, fontSize: 10, bold: true, color: T.TEXT,
        align: "right", valign: "middle", margin: 0,
      });
    }
    addRowLabel("P1A", 0); addSeg("dwell 60s", 0, 60, 0, T.PRIMARY);
    addRowLabel("B3", 1); addSeg("30s", 60, 90, 1, T.SECONDARY);
    addRowLabel("B5", 2); addSeg("30s", 90, 120, 2, T.SECONDARY);
    addRowLabel("P2A", 3); addSeg("dwell 45s", 120, 165, 3, T.PRIMARY);

    addFooter(s, 4, TOTAL);
  }

  // ---------------------------------------------------------
  // Slide 5 — Conflict Types
  // ---------------------------------------------------------
  {
    const s = pres.addSlide();
    s.background = { color: T.BG_LIGHT };
    addHeader(s, "Conflict Detection — 6 Types", "Returned in the 409 response when a route is saved");

    const cards = [
      { icon: ICON.overlap, title: "Vehicle Overlap",
        body: "Same vehicle in two services with overlapping time windows." },
      { icon: ICON.discontinuity, title: "Vehicle Discontinuity",
        body: "Consecutive services on same vehicle don't connect spatially." },
      { icon: ICON.block, title: "Block Occupancy",
        body: "Two services occupy the same block at overlapping times." },
      { icon: ICON.interlock, title: "Interlocking",
        body: "Blocks in the same interlocking group occupied simultaneously." },
      { icon: ICON.lowBat, title: "Low Battery",
        body: "Battery drops below 30 outside the yard." },
      { icon: ICON.charge, title: "Insufficient Charge",
        body: "Vehicle departs the yard with battery below 80." },
    ];

    // 3 + 3 layout
    const cardW = 3.95, cardH = 2.3, gapX = 0.25;
    const row1Y = 1.85, row2Y = row1Y + cardH + 0.35;

    function drawCard(c, x, y) {
      s.addShape("rect", {
        x, y, w: cardW, h: cardH,
        fill: { color: T.CARD }, line: { color: T.BORDER, width: 1 },
        shadow: shadow(),
      });
      // top stripe
      s.addShape("rect", {
        x, y, w: cardW, h: 0.12,
        fill: { color: T.PRIMARY }, line: { color: T.PRIMARY, width: 0 },
      });
      // icon circle
      s.addShape("ellipse", {
        x: x + 0.35, y: y + 0.4, w: 0.95, h: 0.95,
        fill: { color: "E0F2F1" }, line: { color: "E0F2F1", width: 0 },
      });
      s.addImage({ data: c.icon, x: x + 0.55, y: y + 0.6, w: 0.55, h: 0.55 });
      // Title
      s.addText(c.title, {
        x: x + 1.45, y: y + 0.45, w: cardW - 1.55, h: 0.45,
        fontFace: FONT_HEAD, fontSize: 16, bold: true, color: T.TEXT, margin: 0,
        valign: "middle",
      });
      // Body
      s.addText(c.body, {
        x: x + 0.35, y: y + 1.5, w: cardW - 0.5, h: cardH - 1.6,
        fontFace: FONT_BODY, fontSize: 12, color: T.MUTED, margin: 0,
      });
    }

    // Row 1 (3 cards)
    const row1Start = (13.3 - (3 * cardW + 2 * gapX)) / 2;
    drawCard(cards[0], row1Start + 0 * (cardW + gapX), row1Y);
    drawCard(cards[1], row1Start + 1 * (cardW + gapX), row1Y);
    drawCard(cards[2], row1Start + 2 * (cardW + gapX), row1Y);

    // Row 2 (3 cards)
    drawCard(cards[3], row1Start + 0 * (cardW + gapX), row2Y);
    drawCard(cards[4], row1Start + 1 * (cardW + gapX), row2Y);
    drawCard(cards[5], row1Start + 2 * (cardW + gapX), row2Y);

    addFooter(s, 5, TOTAL);
  }

  // ---------------------------------------------------------
  // Slide 6 — Hexagonal Architecture
  // ---------------------------------------------------------
  {
    const s = pres.addSlide();
    s.background = { color: T.BG_LIGHT };
    addHeader(s, "Hexagonal Architecture", "Ports & adapters — dependencies always point inward");

    // Concentric layers
    // Outer (api + infra band)
    s.addShape("rect", {
      x: 1.6, y: 1.85, w: 10.1, h: 4.65,
      fill: { color: T.CARD }, line: { color: T.PRIMARY, width: 1.5 },
      shadow: shadow(),
    });
    s.addText("api/    (inbound adapter)", {
      x: 1.7, y: 1.95, w: 5.0, h: 0.35,
      fontFace: FONT_BODY, fontSize: 12, bold: true, color: T.PRIMARY, margin: 0,
    });
    s.addText("infra/    (outbound adapter)", {
      x: 6.6, y: 1.95, w: 5.0, h: 0.35,
      fontFace: FONT_BODY, fontSize: 12, bold: true, color: T.PRIMARY, align: "right", margin: 0,
    });

    // Middle - application
    s.addShape("rect", {
      x: 2.6, y: 2.55, w: 8.1, h: 3.25,
      fill: { color: "E0F2F1" }, line: { color: T.SECONDARY, width: 1.5 },
    });
    s.addText("application/    (use cases · workflow)", {
      x: 2.7, y: 2.63, w: 7.9, h: 0.35,
      fontFace: FONT_BODY, fontSize: 12, bold: true, color: T.SECONDARY, margin: 0,
    });

    // Inner - domain
    s.addShape("rect", {
      x: 4.5, y: 3.4, w: 4.3, h: 1.95,
      fill: { color: T.PRIMARY }, line: { color: T.PRIMARY, width: 0 },
      shadow: shadow(),
    });
    s.addText("domain/", {
      x: 4.5, y: 3.5, w: 4.3, h: 0.45,
      fontFace: FONT_HEAD, fontSize: 18, bold: true, color: "FFFFFF",
      align: "center", margin: 0,
    });
    s.addText([
      { text: "Entities · Value Objects", options: { breakLine: true } },
      { text: "Repository Interfaces", options: { breakLine: true } },
      { text: "Domain Services", options: {} },
    ], {
      x: 4.5, y: 3.95, w: 4.3, h: 1.3,
      fontFace: FONT_BODY, fontSize: 12, color: "CADCFC",
      align: "center", margin: 0,
    });

    // Inward arrows
    // Left: api → application → domain
    s.addShape("line", {
      x: 2.0, y: 4.4, w: 2.4, h: 0,
      line: { color: T.PRIMARY, width: 2.5, endArrowType: "triangle" },
    });
    // Right: infra → domain (port)
    s.addShape("line", {
      x: 11.3, y: 4.4, w: -2.4, h: 0,
      line: { color: T.PRIMARY, width: 2.5, endArrowType: "triangle" },
    });

    // Caption (positioned safely above footer)
    s.addText("Nothing in domain/ imports anything outside it. Enforced by import-linter at CI time.", {
      x: 1.6, y: 6.65, w: 10.1, h: 0.30,
      fontFace: FONT_BODY, fontSize: 11, italic: true, color: T.MUTED,
      align: "center", margin: 0,
    });

    addFooter(s, 6, TOTAL);
  }

  // ---------------------------------------------------------
  // Slide 7 — Domain Model: Entities
  // ---------------------------------------------------------
  {
    const s = pres.addSlide();
    s.background = { color: T.BG_LIGHT };
    addHeader(s, "Domain Model — Aggregates & Entities", "DDD building blocks and how they relate");

    const LX = 1.05, RX = 7.25, BW = 5.0, BH = 1.45;
    const Y1 = 1.65, Y2 = 3.40, Y3 = 5.15;

    // Row 1: Station (aggregate root) 1—* Platform (child entity)
    addEntityBox(s, LX, Y1, BW, BH, "Station   (aggregate root)", [
      "id (UUID)", "name", "is_yard : bool", "platforms[]"
    ]);
    addEntityBox(s, RX, Y1, BW, BH, "Platform   (entity)", [
      "id (UUID)", "name"
    ], { accent: T.SECONDARY });
    addConnector(s, LX + BW, Y1 + BH / 2, RX, Y1 + BH / 2, "1   *");

    // Row 2: Vehicle (aggregate root) 1—* Service (aggregate root)
    addEntityBox(s, LX, Y2, BW, BH, "Vehicle   (aggregate root)", [
      "id (UUID)", "name", "battery"
    ]);
    addEntityBox(s, RX, Y2, BW, BH, "Service   (aggregate root)", [
      "id, name, vehicle_id",
      "route : Node[]   (ordered: Platform | Block | Yard)",
      "timetable : TimetableEntry[]   (arr / dep per node)"
    ], { accent: T.ACCENT, fontSize: 11 });
    addConnector(s, LX + BW, Y2 + BH / 2, RX, Y2 + BH / 2, "1   *");

    // Row 3: Block (aggregate root) | NodeConnection (shared kernel)
    addEntityBox(s, LX, Y3, BW, BH, "Block   (aggregate root)", [
      "id, name", "group   (interlocking)", "traversal_time_seconds"
    ]);
    addEntityBox(s, RX, Y3, BW, BH, "NodeConnection   (shared kernel)", [
      "from_id  →  to_id     (directed graph edge)",
      "BFS over this graph fills the route between stops"
    ], { accent: T.MUTED, fontSize: 10 });

    s.addText("Service.route and Service.timetable are stored as JSONB — loaded and saved as a whole.", {
      x: 0.6, y: 6.78, w: 12.0, h: 0.3,
      fontFace: FONT_BODY, fontSize: 10, italic: true, color: T.MUTED, margin: 0,
      align: "center",
    });
    addFooter(s, 7, TOTAL);
  }

  // ---------------------------------------------------------
  // Slide 8 — Domain Model: Value Objects
  // ---------------------------------------------------------
  {
    const s = pres.addSlide();
    s.background = { color: T.BG_LIGHT };
    addHeader(s, "Domain Model — Value Objects & Read Models", "Immutable types embedded in aggregates, plus query-side projections");

    const LX = 1.05, RX = 7.25, BW = 5.0, BH = 1.45;
    const Y1 = 1.65, Y2 = 3.40;

    addEntityBox(s, LX, Y1, BW, BH, "Node   (value object)", [
      "id (UUID)", "type : NodeType   (BLOCK | PLATFORM | YARD)"
    ], { accent: T.MUTED });
    addEntityBox(s, RX, Y1, BW, BH, "TimetableEntry   (value object)", [
      "order", "node_id (UUID)", "arrival : EpochSeconds", "departure : EpochSeconds"
    ], { accent: T.MUTED });

    addEntityBox(s, LX, Y2, BW, BH, "LayoutData   (read model)", [
      "positions : dict[UUID, tuple[float, float]]",
      "junction_blocks : dict[tuple[UUID, UUID], UUID]"
    ], { accent: T.MUTED, fontSize: 10 });

    addFooter(s, 8, TOTAL);
  }

  const outFile = path.join(__dirname, "VSS-Visual-Reference.pptx");
  await pres.writeFile({ fileName: outFile });
  console.log("Wrote " + outFile);
}

build().catch((e) => {
  console.error(e);
  process.exit(1);
});
