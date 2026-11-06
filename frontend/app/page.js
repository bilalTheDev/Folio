import Faq from "@/components/marketing/Faq";
import MarketingNav, { Footer } from "@/components/layout/MarketingNav";
import Atmosphere from "@/components/ui/Atmosphere";
import Button from "@/components/ui/Button";

const STEPS = [
  {
    n: "01",
    title: "Upload your documents",
    body: "Add PDFs, Word files, text, or Markdown up to 10 MB each. Folio splits them into passages and indexes them for your account only.",
  },
  {
    n: "02",
    title: "Connect your own key",
    body: "Paste a Hugging Face token and pick a provider such as Groq or Cerebras. You pay your provider directly, and the token is encrypted at rest.",
  },
  {
    n: "03",
    title: "Ask grounded questions",
    body: "Answers come only from your passages, with numbered citations. Open any citation to read the exact excerpt it came from.",
  },
];

const AUDIENCES = [
  {
    title: "Contracts and policy",
    body: "Ask for notice periods, renewal dates, or defined terms, then open the clause instead of trusting a paraphrase.",
  },
  {
    title: "Research and notes",
    body: "Keep papers, briefs, and meeting notes in one index. Folio points at the page, so you can quote with confidence.",
  },
  {
    title: "Internal docs",
    body: "Handbooks, specs, and runbooks stay in your account. Colleagues cannot search your files, and you cannot search theirs.",
  },
];

const PRODUCT = [
  {
    title: "Cited answers",
    body: "Every grounded claim is numbered. Click through to the filename, page or section, and the passage the model used.",
  },
  {
    title: "Your own index",
    body: "Retrieval only searches the files you uploaded. Folio does not mix accounts and does not train models on your text.",
  },
  {
    title: "Bring your own key",
    body: "Inference runs on a Hugging Face token you supply. Switch Groq, Cerebras, or Auto whenever you like.",
  },
  {
    title: "Chat history",
    body: "Sessions keep the thread. Rename or delete them from History without touching the documents they cited.",
  },
  {
    title: "Document control",
    body: "See indexing status, reindex a file after a change, or delete it so later answers cannot cite it.",
  },
  {
    title: "Settings that stay yours",
    body: "Replace the token, pick another model, or sign out. The last four characters of a saved token are all Folio will show.",
  },
];

const FILES = [
  { title: "PDF", body: "Contracts, papers, reports. Page numbers travel with citations." },
  { title: "Word", body: ".docx briefs, memos, and drafts, split into passages." },
  { title: "Text & Markdown", body: "Notes, READMEs, and exported docs up to 10 MB each." },
];

const PROVIDERS = [
  { title: "Groq", body: "Fast open models when you want a short wait on every turn." },
  { title: "Cerebras", body: "Another Hugging Face-routed option if Groq is not the right fit." },
  { title: "Auto", body: "Let Folio pick a working model from what your token can reach." },
];

const PRIVACY = [
  {
    title: "Isolated retrieval",
    body: "Your questions search only your index. Other accounts never retrieve your passages, even on the same deployment.",
  },
  {
    title: "Encrypted token",
    body: "The Hugging Face key is stored encrypted. Folio uses it to call the provider you chose, then shows only the last four characters.",
  },
  {
    title: "You keep the originals",
    body: "Delete a document and it leaves the index. Folio is not a public corpus and does not use your files to train a model.",
  },
];

function SampleAnswer() {
  return (
    <div className="rounded-2xl border border-hairline bg-card p-6 shadow-soft">
      <div className="flex justify-end">
        <p className="max-w-[85%] rounded-2xl rounded-br-md bg-primary px-4 py-2.5 text-sm text-on-primary">
          What is the notice period for ending the contract?
        </p>
      </div>
      <div className="mt-5 flex gap-3">
        <span className="grid size-8 shrink-0 place-items-center rounded-full bg-primary text-xs font-medium text-on-primary">
          F
        </span>
        <div className="text-sm leading-relaxed text-body">
          <p>
            Either party can end the agreement with <strong className="font-medium text-ink">60 days&apos; written notice</strong>
            <span className="mx-0.5 inline-grid h-[1.15rem] min-w-[1.15rem] place-items-center rounded-full bg-primary px-1 align-[0.1em] text-[0.7rem] font-medium text-on-primary">
              1
            </span>
            . Notice given during the first year also triggers the early-exit fee
            <span className="mx-0.5 inline-grid h-[1.15rem] min-w-[1.15rem] place-items-center rounded-full bg-strong px-1 align-[0.1em] text-[0.7rem] font-medium text-ink">
              2
            </span>
            .
          </p>
          <div className="mt-4 rounded-2xl border border-hairline bg-canvas-soft p-4">
            <p className="caption-upper text-muted">Source 1</p>
            <p className="mt-1 text-sm font-medium text-ink">master-services-agreement.pdf</p>
            <p className="text-xs text-muted">Page 7</p>
            <blockquote className="mt-3 border-l-2 border-hairline-strong pl-3 text-body">
              12.2 Either party may terminate this Agreement for convenience by giving the other party not less than
              sixty (60) days&apos; prior written notice…
            </blockquote>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function Home() {
  return (
    <div className="flex flex-1 flex-col">
      <MarketingNav />
      <main className="flex-1">
        <section className="relative overflow-hidden">
          <Atmosphere
            orbs={[
              { color: "mint", size: 420, left: "-8%", top: "-20%" },
              { color: "peach", size: 360, left: "55%", top: "-10%", opacity: 0.4 },
              { color: "lavender", size: 280, left: "78%", top: "40%", opacity: 0.35 },
              { color: "sky", size: 240, left: "18%", top: "55%", opacity: 0.3 },
            ]}
          />
          <div className="relative mx-auto grid max-w-[1200px] items-center gap-16 px-6 py-24 lg:grid-cols-2 lg:py-32">
            <div>
              <p className="caption-upper text-muted">Bring your own key</p>
              <h1 className="display-mega mt-5 text-ink">Chat with your documents. Check every answer.</h1>
              <p className="mt-6 max-w-xl text-base leading-relaxed text-body sm:text-lg">
                Folio answers questions using only the files you upload, with citations to the passages behind each
                claim. It runs on your own Hugging Face token and the provider you choose.
              </p>
              <div className="mt-10 flex flex-wrap gap-3">
                <Button href="/signup" size="lg">
                  Create a free account
                </Button>
                <Button href="/signin" size="lg" variant="secondary">
                  Sign in
                </Button>
              </div>
              <p className="mt-6 text-sm text-muted">PDF, Word, text, and Markdown · Groq or Cerebras · citations on every grounded claim.</p>
            </div>
            <SampleAnswer />
          </div>
        </section>

        <section id="how" className="relative scroll-mt-20 overflow-hidden">
          <Atmosphere orbs={[{ color: "rose", size: 320, left: "70%", top: "10%", opacity: 0.28 }]} />
          <div className="relative mx-auto max-w-[1200px] px-6 py-24">
            <p className="caption-upper text-muted">The path</p>
            <h2 className="display-lg mt-3 text-ink">How it works</h2>
            <p className="mt-4 max-w-2xl text-body">
              Folio is retrieval-augmented generation with the boring parts made explicit. Your files become an index,
              your token calls a model, and the answer has to point back at a passage.
            </p>
            <ol className="mt-12 grid gap-6 md:grid-cols-3">
              {STEPS.map((step) => (
                <li key={step.title} className="rounded-2xl border border-hairline bg-card p-6">
                  <span className="caption-upper text-muted">{step.n}</span>
                  <h3 className="display-sm mt-4 text-ink">{step.title}</h3>
                  <p className="mt-3 text-sm leading-relaxed text-body">{step.body}</p>
                </li>
              ))}
            </ol>
          </div>
        </section>

        <section className="mx-auto max-w-[1200px] px-6 py-24">
          <p className="caption-upper text-muted">Built for reading closely</p>
          <h2 className="display-lg mt-3 text-ink">When a summary is not enough</h2>
          <div className="mt-12 grid gap-10 md:grid-cols-3">
            {AUDIENCES.map((item) => (
              <div key={item.title}>
                <h3 className="display-sm text-ink">{item.title}</h3>
                <p className="mt-3 text-sm leading-relaxed text-body">{item.body}</p>
              </div>
            ))}
          </div>
        </section>

        <section id="product" className="relative scroll-mt-20 overflow-hidden">
          <Atmosphere orbs={[{ color: "mint", size: 280, left: "-8%", top: "20%", opacity: 0.28 }]} />
          <div className="relative mx-auto max-w-[1200px] px-6 py-24">
            <p className="caption-upper text-muted">The workspace</p>
            <h2 className="display-lg mt-3 max-w-2xl text-ink">What you get after the two-minute setup</h2>
            <p className="mt-4 max-w-2xl text-body">
              Chat, History, Documents, and Settings. Retrieval stays on your index; generation stays on the model you
              picked.
            </p>
            <div className="mt-12 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
              {PRODUCT.map((item) => (
                <div key={item.title} className="rounded-2xl border border-hairline bg-card p-6">
                  <h3 className="text-base font-medium text-ink">{item.title}</h3>
                  <p className="mt-3 text-sm leading-relaxed text-body">{item.body}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="mx-auto max-w-[1200px] px-6 py-24">
          <div className="grid gap-16 lg:grid-cols-2">
            <div>
              <p className="caption-upper text-muted">Files</p>
              <h2 className="display-lg mt-3 text-ink">What you can upload</h2>
              <p className="mt-4 text-body">
                Each file is split into passages, stored in an index that belongs to your account, and cited by filename
                and page or section.
              </p>
              <ul className="mt-8 space-y-6">
                {FILES.map((item) => (
                  <li key={item.title}>
                    <p className="font-medium text-ink">{item.title}</p>
                    <p className="mt-1 text-sm leading-relaxed text-body">{item.body}</p>
                  </li>
                ))}
              </ul>
            </div>
            <div>
              <p className="caption-upper text-muted">Inference</p>
              <h2 className="display-lg mt-3 text-ink">Your model, your bill</h2>
              <p className="mt-4 text-body">
                Folio never sells inference. A Hugging Face token you paste is what the provider sees. Change it in
                Settings without re-uploading documents.
              </p>
              <ul className="mt-8 space-y-6">
                {PROVIDERS.map((item) => (
                  <li key={item.title}>
                    <p className="font-medium text-ink">{item.title}</p>
                    <p className="mt-1 text-sm leading-relaxed text-body">{item.body}</p>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </section>

        <section id="privacy" className="relative scroll-mt-20 overflow-hidden">
          <Atmosphere
            orbs={[
              { color: "lavender", size: 300, left: "72%", top: "-8%", opacity: 0.3 },
              { color: "sky", size: 240, left: "8%", top: "40%", opacity: 0.25 },
            ]}
          />
          <div className="relative mx-auto max-w-[1200px] px-6 py-24">
            <p className="caption-upper text-muted">Private by design</p>
            <h2 className="display-lg mt-3 max-w-2xl text-ink">Your passages stay in your account</h2>
            <p className="mt-4 max-w-2xl text-body">
              Folio is not a shared knowledge base. Retrieval, storage, and the token you use to generate answers are
              scoped to you.
            </p>
            <div className="mt-12 grid gap-10 md:grid-cols-3">
              {PRIVACY.map((item) => (
                <div key={item.title}>
                  <h3 className="display-sm text-ink">{item.title}</h3>
                  <p className="mt-3 text-sm leading-relaxed text-body">{item.body}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section id="faq" className="scroll-mt-20">
          <div className="mx-auto max-w-[1200px] px-6 py-24">
            <p className="caption-upper text-muted">Questions</p>
            <h2 className="display-lg mt-3 text-ink">FAQ</h2>
            <p className="mt-4 max-w-2xl text-body">
              Short answers about keys, files, citations, and what Folio does not do.
            </p>
            <div className="mt-12">
              <Faq />
            </div>
          </div>
        </section>

        <section className="relative overflow-hidden">
          <Atmosphere
            orbs={[
              { color: "peach", size: 300, left: "-6%", top: "20%", opacity: 0.35 },
              { color: "sky", size: 260, left: "80%", top: "-10%", opacity: 0.3 },
            ]}
          />
          <div className="relative mx-auto max-w-[1200px] px-6 py-24 text-center">
            <h2 className="display-lg text-ink">Ready to ask your documents something?</h2>
            <p className="mx-auto mt-4 max-w-lg text-body">
              Setup takes about two minutes: upload, paste a token, pick a model. After that, every answer can be checked
              against the passage it came from.
            </p>
            <div className="mt-8">
              <Button href="/signup" size="lg">
                Get started
              </Button>
            </div>
          </div>
        </section>
      </main>
      <Footer />
    </div>
  );
}
