#!/usr/bin/env node
/**
 * Prospect Pipeline Loader
 * Converts already-here-llc sales prospects into work opportunities
 * Usage: node scripts/load-prospects.js
 */

const prospects = [
  {
    title: "AZ Mobile Diesel Repair — Overflow Field Support",
    category: "Handyman",
    location: "Phoenix Metro, AZ",
    pay: 450,
    miles: 5,
    description: "Mobile diesel repair overflow support. Call first, then email same day. Lead with overflow field support positioning.",
    grade: "A",
    score: 94,
    status: "open",
    source: "sales-prospect",
  },
  {
    title: "Code 3 Junk Removal — Dispatch Support",
    category: "Junk Removal",
    location: "Phoenix Metro, AZ",
    pay: 350,
    miles: 8,
    description: "Junk removal / office cleanouts. Send overflow field support email first, follow with call/text asking if they need overflow coverage.",
    grade: "A",
    score: 92,
    status: "open",
    source: "sales-prospect",
  },
  {
    title: "Cam Fleet Care — Mechanic/Fleet Support",
    category: "Handyman",
    location: "Phoenix Metro, AZ",
    pay: 425,
    miles: 10,
    description: "Fleet mobile repair. Send mechanic/fleet support draft; call to ask for overflow dispatch or after-hours coverage.",
    grade: "A-",
    score: 90,
    status: "open",
    source: "sales-prospect",
  },
  {
    title: "AZ Junk Removal — Storage Property Overflow",
    category: "Junk Removal",
    location: "Phoenix Metro, AZ",
    pay: 375,
    miles: 6,
    description: "Junk removal / storage cleanouts. Email Jake with route guarantee support positioning.",
    grade: "A-",
    score: 88,
    status: "open",
    source: "sales-prospect",
  },
  {
    title: "Minutemen Junk Removal — Commercial Overflow",
    category: "Junk Removal",
    location: "Phoenix Metro, AZ",
    pay: 380,
    miles: 7,
    description: "Commercial cleanouts. Ask for same-week overflow coverage.",
    grade: "A-",
    score: 87,
    status: "open",
    source: "sales-prospect",
  },
  {
    title: "Intergalactic Junk Removal — Specialty Cleanouts",
    category: "Junk Removal",
    location: "Phoenix Metro, AZ",
    pay: 340,
    miles: 9,
    description: "Specialty cleanouts / foreclosure jobs. Call first, then email. Offer help when booked or need second set of hands.",
    grade: "B+",
    score: 84,
    status: "open",
    source: "sales-prospect",
  },
  {
    title: "F&H Junk Removal — Estate/Realty Cleanouts",
    category: "Junk Removal",
    location: "Phoenix Metro, AZ",
    pay: 360,
    miles: 8,
    description: "Estate / realty cleanouts. Send mechanic support email through contact form or available contact method.",
    grade: "B+",
    score: 82,
    status: "open",
    source: "sales-prospect",
  },
  {
    title: "Anyplace Auto Repair — Mobile Auto Dispatch",
    category: "Handyman",
    location: "Phoenix Metro, AZ",
    pay: 395,
    miles: 6,
    description: "Mobile auto repair overflow. Position as non-mechanic replacement / overflow not mechanic replacement.",
    grade: "B+",
    score: 80,
    status: "open",
    source: "sales-prospect",
  },
  {
    title: "Solterra Solutions 48 — Cleanouts/Storage/Office",
    category: "Junk Removal",
    location: "Phoenix Metro, AZ",
    pay: 330,
    miles: 12,
    description: "Cleanouts / storage / office. Contact form if available. Offer overflow support.",
    grade: "B+",
    score: 79,
    status: "open",
    source: "sales-prospect",
  },
  {
    title: "Cobra Tire & Auto Service — Fleet Overflow",
    category: "Handyman",
    location: "Phoenix Metro, AZ",
    pay: 320,
    miles: 8,
    description: "Auto repair / commercial fleet. Call service advisor; ask who handles fleet overflow/vendor management.",
    grade: "B",
    score: 76,
    status: "open",
    source: "sales-prospect",
  },
];

async function loadProspects() {
  console.log(`Loading ${prospects.length} prospects into job board...`);

  for (const prospect of prospects) {
    try {
      const response = await fetch("http://localhost:3000/api/jobs", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "x-user-id": "sales-system",
        },
        body: JSON.stringify(prospect),
      });

      if (!response.ok) {
        const error = await response.json();
        console.error(`❌ Failed to load "${prospect.title}":`, error);
        continue;
      }

      const job = await response.json();
      console.log(`✅ Loaded: ${prospect.title} (${prospect.grade} grade, margin: $${job.margin.toFixed(2)})`);
    } catch (error) {
      console.error(`❌ Error loading "${prospect.title}":`, error.message);
    }
  }

  console.log("\n📊 Prospect pipeline loaded. View at: http://localhost:3000/work");
}

loadProspects().catch(console.error);
