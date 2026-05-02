"use client";

import { Fragment, useState } from "react";

const CONTRACT_ADDRESS = "0x9BaA24c3f0298423B6410C7b3a4b8Bc4B1c6919c" as const;
const DEFAULT_HASH =
  "0x272d2bbeb48df25aeecc7f1bd40c87bbac6880d884f105fbaa0ec6613bc7e2bb";
const PINATA_GW = "https://gateway.pinata.cloud/ipfs/";
const ETHERSCAN = "https://sepolia.etherscan.io";

const ABI = [
  {
    inputs: [{ name: "contentHash", type: "bytes32" }],
    name: "getSkill",
    outputs: [
      {
        components: [
          { name: "author", type: "address" },
          { name: "contentHash", type: "bytes32" },
          { name: "ipfsCid", type: "string" },
          { name: "registeredAt", type: "uint256" },
        ],
        name: "",
        type: "tuple",
      },
    ],
    stateMutability: "view",
    type: "function",
  },
] as const;

type SkillData = {
  author: string;
  contentHash: string;
  ipfsCid: string;
  registeredAt: bigint;
};

type VerifyState =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "trusted"; data: SkillData }
  | { status: "unclaimed" }
  | { status: "error"; message: string };

function Spinner() {
  return (
    <span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent" />
  );
}

const STEPS = [
  { id: "01", icon: "#️⃣", title: "Hash", desc: "keccak256 content fingerprint" },
  { id: "02", icon: "📤", title: "Upload", desc: "IPFS via Pinata" },
  { id: "03", icon: "⛓️", title: "Attest", desc: "On-chain registration" },
  { id: "04", icon: "🔍", title: "Verify", desc: "Anyone, anytime, forever" },
];

const VERDICTS = [
  {
    verdict: "TRUSTED_ORIGIN",
    icon: "✅",
    border: "border-green-500/40",
    bg: "bg-green-950/20",
    label: "text-green-400",
    desc: "Hash found on-chain. Author verified.",
  },
  {
    verdict: "UNCLAIMED_ARTIFACT",
    icon: "⚠️",
    border: "border-yellow-500/40",
    bg: "bg-yellow-950/20",
    label: "text-yellow-400",
    desc: "No attestation. Anyone can claim.",
  },
  {
    verdict: "HASH_MISMATCH",
    icon: "❌",
    border: "border-red-500/40",
    bg: "bg-red-950/20",
    label: "text-red-400",
    desc: "Content modified after attestation.",
  },
  {
    verdict: "CONFLICTING_CLAIMS",
    icon: "🔶",
    border: "border-orange-500/40",
    bg: "bg-orange-950/20",
    label: "text-orange-400",
    desc: "Reserved for v0.2.0",
  },
];

const EVIDENCE = [
  {
    icon: "📄",
    title: "Smart Contract",
    sub: "SkillRegistry.sol on Sepolia",
    href: `${ETHERSCAN}/address/${CONTRACT_ADDRESS}`,
    tag: `${CONTRACT_ADDRESS.slice(0, 10)}…${CONTRACT_ADDRESS.slice(-6)}`,
  },
  {
    icon: "🔗",
    title: "Latest Transaction",
    sub: "registerSkill() call",
    href: `${ETHERSCAN}/tx/0x9f1a911ffc245b06ca892486a7a7332654a2f4aafabaf634f1f9e0ce582aab61`,
    tag: "0x9f1a911f…2aab61",
  },
  {
    icon: "📦",
    title: "IPFS Archive",
    sub: "Skill bundle on Pinata",
    href: `${PINATA_GW}bafkreicuyparqmokss4swvspfss2s5b5lv7gwf26flvdcziff34mu5sx5a`,
    tag: "bafkrei…sx5a",
  },
];

export default function Home() {
  const [hash, setHash] = useState(DEFAULT_HASH);
  const [result, setResult] = useState<VerifyState>({ status: "idle" });

  async function handleValidate() {
    setResult({ status: "loading" });
    try {
      const { createPublicClient, http } = await import("viem");
      const { sepolia } = await import("viem/chains");

      const client = createPublicClient({
        chain: sepolia,
        transport: http("https://sepolia.gateway.tenderly.co"),
      });

      const bytes32 = (
        hash.startsWith("0x") ? hash : `0x${hash}`
      ) as `0x${string}`;

      const raw = await client.readContract({
        address: CONTRACT_ADDRESS,
        abi: ABI,
        functionName: "getSkill",
        args: [bytes32],
      });

      const skill = raw as unknown as SkillData;

      if (skill.author === "0x0000000000000000000000000000000000000000") {
        setResult({ status: "unclaimed" });
      } else {
        setResult({ status: "trusted", data: skill });
      }
    } catch (err) {
      setResult({
        status: "error",
        message: err instanceof Error ? err.message : String(err),
      });
    }
  }

  return (
    <main className="min-h-screen bg-[#080b14] text-white">
      {/* ── SECTION 1: HERO ──────────────────────────────── */}
      <section className="relative overflow-hidden px-6 py-24">
        <div className="pointer-events-none absolute inset-0 bg-gradient-to-b from-purple-900/25 via-transparent to-transparent" />
        <div className="relative mx-auto max-w-4xl text-center">
          <div className="mb-8 inline-flex items-center gap-2 rounded-full border border-purple-500/30 bg-purple-500/10 px-4 py-1.5 text-sm text-purple-300">
            🏆 Nous Research Hermes Agent Hackathon 2026
          </div>

          <h1 className="mb-4 bg-gradient-to-r from-purple-400 via-blue-400 to-cyan-400 bg-clip-text text-7xl font-black leading-tight text-transparent">
            SkillProof
          </h1>

          <p className="mb-3 text-2xl font-light text-gray-300">
            On-chain Attestation &amp; Provenance for Hermes Agent Skills
          </p>

          <p className="mb-16 font-mono text-lg text-gray-500">
            Register once. Verify forever. No central authority.
          </p>

          <div className="mx-auto grid max-w-xl grid-cols-3 gap-5">
            {[
              { icon: "⛓️", value: "3", label: "On-chain Attestations" },
              { icon: "✅", value: "15", label: "Tests Passing" },
              { icon: "🔍", value: "4", label: "Trust Verdicts" },
            ].map((s) => (
              <div
                key={s.label}
                className="rounded-xl border border-slate-800 bg-slate-900/80 p-6 backdrop-blur-sm"
              >
                <div className="mb-2 text-3xl">{s.icon}</div>
                <div className="mb-1 text-4xl font-bold">{s.value}</div>
                <div className="text-sm text-gray-400">{s.label}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── SECTION 2: LIVE VERIFY ────────────────────────── */}
      <section className="bg-slate-900/40 px-6 py-20">
        <div className="mx-auto max-w-2xl">
          <h2 className="mb-2 text-center text-3xl font-bold">
            Verify Skill Provenance
          </h2>
          <p className="mb-10 text-center text-gray-400">
            Query the Sepolia registry in real time
          </p>

          <div className="space-y-4">
            <div className="flex gap-3">
              <input
                type="text"
                value={hash}
                onChange={(e) => setHash(e.target.value)}
                placeholder="Enter skill content hash (0x...)"
                className="min-w-0 flex-1 rounded-lg border border-slate-700 bg-slate-800 px-4 py-3 font-mono text-sm text-gray-200 placeholder-gray-600 focus:border-purple-500 focus:outline-none"
              />
              <button
                onClick={handleValidate}
                disabled={result.status === "loading"}
                className="flex shrink-0 cursor-pointer items-center gap-2 rounded-lg bg-green-600 px-6 py-3 font-semibold transition-colors hover:bg-green-500 disabled:cursor-not-allowed disabled:bg-slate-700 disabled:text-gray-500"
              >
                {result.status === "loading" ? (
                  <>
                    <Spinner /> Querying…
                  </>
                ) : (
                  "Validate"
                )}
              </button>
            </div>

            {result.status === "trusted" && (
              <div className="rounded-xl border border-green-500/40 bg-green-950/30 p-6">
                <div className="mb-5 flex items-center gap-3">
                  <span className="text-2xl">✅</span>
                  <div>
                    <p className="font-mono text-lg font-bold text-green-400">
                      TRUSTED_ORIGIN
                    </p>
                    <p className="text-sm text-gray-400">
                      Skill provenance verified on Sepolia
                    </p>
                  </div>
                </div>
                <dl className="space-y-3 font-mono text-sm">
                  <div>
                    <dt className="mb-0.5 text-gray-500">Author</dt>
                    <dd>
                      <a
                        href={`${ETHERSCAN}/address/${result.data.author}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="break-all text-blue-400 hover:text-blue-300"
                      >
                        {result.data.author}
                      </a>
                    </dd>
                  </div>
                  <div>
                    <dt className="mb-0.5 text-gray-500">Registered</dt>
                    <dd className="text-gray-200">
                      {new Date(
                        Number(result.data.registeredAt) * 1000
                      ).toLocaleString("en-US", {
                        year: "numeric",
                        month: "long",
                        day: "numeric",
                        hour: "2-digit",
                        minute: "2-digit",
                      })}
                    </dd>
                  </div>
                  <div>
                    <dt className="mb-0.5 text-gray-500">IPFS CID</dt>
                    <dd>
                      <a
                        href={`${PINATA_GW}${result.data.ipfsCid}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="break-all text-blue-400 hover:text-blue-300"
                      >
                        {result.data.ipfsCid}
                      </a>
                    </dd>
                  </div>
                  <div className="pt-2">
                    <a
                      href={`${ETHERSCAN}/address/${CONTRACT_ADDRESS}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-purple-400 hover:text-purple-300"
                    >
                      View contract on Etherscan →
                    </a>
                  </div>
                </dl>
              </div>
            )}

            {result.status === "unclaimed" && (
              <div className="rounded-xl border border-yellow-500/40 bg-yellow-950/30 p-6">
                <div className="flex items-center gap-3">
                  <span className="text-2xl">⚠️</span>
                  <div>
                    <p className="font-mono text-lg font-bold text-yellow-400">
                      UNCLAIMED_ARTIFACT
                    </p>
                    <p className="text-sm text-gray-400">
                      No on-chain attestation found for this hash
                    </p>
                  </div>
                </div>
              </div>
            )}

            {result.status === "error" && (
              <div className="rounded-xl border border-red-500/40 bg-red-950/30 p-4">
                <p className="font-mono text-sm text-red-400">
                  Error: {result.message}
                </p>
              </div>
            )}
          </div>
        </div>
      </section>

      {/* ── SECTION 3: TRUST MODEL ───────────────────────── */}
      <section className="px-6 py-20">
        <div className="mx-auto max-w-4xl">
          <h2 className="mb-2 text-center text-3xl font-bold">Trust Verdicts</h2>
          <p className="mb-12 text-center text-gray-400">
            Four possible outcomes when verifying a skill
          </p>
          <div className="grid grid-cols-2 gap-5">
            {VERDICTS.map((v) => (
              <div
                key={v.verdict}
                className={`rounded-xl border ${v.border} ${v.bg} p-6`}
              >
                <div className="flex items-start gap-4">
                  <span className="mt-0.5 text-2xl">{v.icon}</span>
                  <div>
                    <p className={`mb-1 font-mono font-bold ${v.label}`}>
                      {v.verdict}
                    </p>
                    <p className="text-sm text-gray-400">{v.desc}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── SECTION 4: HOW IT WORKS ──────────────────────── */}
      <section className="bg-slate-900/30 px-6 py-20">
        <div className="mx-auto max-w-5xl">
          <h2 className="mb-2 text-center text-3xl font-bold">How It Works</h2>
          <p className="mb-16 text-center text-gray-400">
            From skill folder to immutable provenance in 4 steps
          </p>
          <div className="flex items-stretch gap-3">
            {STEPS.map((step, i) => (
              <Fragment key={step.id}>
                <div className="flex-1 rounded-xl border border-slate-800 bg-slate-900 p-6 text-center">
                  <div className="mb-3 text-3xl">{step.icon}</div>
                  <p className="mb-0.5 font-mono text-xs text-gray-600">
                    STEP {step.id}
                  </p>
                  <p className="mb-2 text-lg font-bold">{step.title}</p>
                  <p className="text-sm text-gray-400">{step.desc}</p>
                </div>
                {i < STEPS.length - 1 && (
                  <div className="flex shrink-0 items-center text-2xl text-gray-700">
                    →
                  </div>
                )}
              </Fragment>
            ))}
          </div>
        </div>
      </section>

      {/* ── SECTION 5: LIVE EVIDENCE ─────────────────────── */}
      <section className="px-6 py-20">
        <div className="mx-auto max-w-4xl">
          <h2 className="mb-2 text-center text-3xl font-bold">
            Live On-Chain Evidence
          </h2>
          <p className="mb-12 text-center text-gray-400">
            Deployed and verifiable on Ethereum Sepolia
          </p>
          <div className="grid grid-cols-3 gap-5">
            {EVIDENCE.map((e) => (
              <a
                key={e.title}
                href={e.href}
                target="_blank"
                rel="noopener noreferrer"
                className="group rounded-xl border border-slate-800 bg-slate-900 p-6 transition-colors hover:border-purple-500/50 hover:bg-slate-800"
              >
                <div className="mb-3 text-3xl">{e.icon}</div>
                <p className="mb-1 font-semibold">{e.title}</p>
                <p className="mb-3 text-sm text-gray-400">{e.sub}</p>
                <p className="font-mono text-xs text-purple-400 group-hover:text-purple-300">
                  {e.tag} →
                </p>
              </a>
            ))}
          </div>
        </div>
      </section>

      {/* ── SECTION 6: FOOTER ────────────────────────────── */}
      <footer className="border-t border-slate-800 bg-slate-900/50 px-6 py-10 text-center">
        <p className="mb-1 text-sm text-gray-400">
          Built for{" "}
          <span className="text-white">
            Nous Research Hermes Agent Creative Hackathon 2026
          </span>
        </p>
        <p className="mb-5 text-sm text-gray-400">
          By <span className="text-white">Gokmen</span> (
          <span className="text-purple-400">@GoGoSns</span>) from Turkey 🇹🇷
        </p>
        <a
          href="https://github.com/GoGoSns/skillproof"
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-2 rounded-lg border border-slate-700 bg-slate-800 px-4 py-2 text-sm text-gray-300 transition-colors hover:border-slate-600 hover:text-white"
        >
          ⭐ github.com/GoGoSns/skillproof
        </a>
      </footer>
    </main>
  );
}
