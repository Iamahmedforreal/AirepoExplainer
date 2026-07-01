import Section from "./Section";
import { Link, Graph, Search } from "./icons";

const graphSteps = [
  {
    Icon: Link,
    title: "Service-to-service relationships",
    desc: "See which services and modules depend on each other across the whole repo.",
  },
  {
    Icon: Graph,
    title: "Function calls & import chains",
    desc: "Follow call edges and import chains from an entry point down to the database.",
  },
  {
    Icon: Search,
    title: "Queryable in plain English",
    desc: "Ask the graph how a flow works and get an answer grounded in real code paths.",
  },
];

export default function CodeGraphExample() {
  return (
    <Section
      id="graph"
      label="Architecture graph"
      title="Turn one repo URL into a map of the whole system."
      intro="CodeGrok parses every file and builds an interactive graph of how the code connects — services, function calls, import chains, and file dependencies."
    >
      <div className="grid items-start gap-6 lg:grid-cols-[1.15fr_0.85fr]">
        <GraphExample />

        <div className="space-y-4">
          {graphSteps.map((p) => (
            <div
              key={p.title}
              className="glass group flex gap-4 rounded-2xl p-5 transition-colors hover:border-white/25 hover:bg-white/[0.05]"
            >
              <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border border-white/12 text-ink transition-colors group-hover:border-white group-hover:bg-white group-hover:text-[#050609]">
                <p.Icon className="h-5 w-5" />
              </span>
              <div>
                <h3 className="text-base font-bold tracking-tight">{p.title}</h3>
                <p className="mt-1 text-sm leading-relaxed text-muted">
                  {p.desc}
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </Section>
  );
}

function GraphExample() {
  return (
    <div className="glass-strong overflow-hidden rounded-2xl shadow-[0_40px_90px_-50px_rgba(0,0,0,0.9)]">
      <div className="flex items-center justify-between border-b border-white/10 px-4 py-3">
        <div className="flex items-center gap-2">
          <span className="h-2.5 w-2.5 rounded-full bg-white/30" />
          <span className="h-2.5 w-2.5 rounded-full bg-white/20" />
          <span className="h-2.5 w-2.5 rounded-full bg-white/10" />
        </div>
        <span className="font-mono text-xs text-faint">
          github.com/acme/payments-api
        </span>
      </div>

      <div className="space-y-5 p-5 font-mono text-[0.82rem] leading-7 sm:p-6">
        <div>
          <p className="text-faint">input</p>
          <p className="text-ink">https://github.com/acme/payments-api</p>
        </div>

        <div className="rounded-xl border border-white/10 bg-white/[0.03] p-4">
          <p className="mb-3 text-faint">generated graph</p>
          <div className="space-y-2 text-ink-soft">
            <p>api.routes.checkout.create_order</p>
            <p className="pl-6 text-muted">
              imports services.payments.charge_card
            </p>
            <p className="pl-6 text-muted">
              calls repositories.orders.save_order
            </p>
            <p className="pl-12 text-faint">calls db.session.commit</p>
          </div>
        </div>

        <div>
          <p className="text-faint">query</p>
          <p className="text-ink">
            What happens when checkout creates an order?
          </p>
          <p className="mt-2 text-muted">
            CodeGrok answers from the traced modules, functions, imports, and
            call paths instead of only matching keywords.
          </p>
        </div>
      </div>
    </div>
  );
}
