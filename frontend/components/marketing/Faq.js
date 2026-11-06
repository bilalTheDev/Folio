const FAQS = [
  {
    q: "What is Folio?",
    a: "Folio is a private chat over files you upload. It retrieves the relevant passages from your own documents, asks a model you pay for, and returns an answer with numbered citations so you can open the exact excerpt behind each claim.",
  },
  {
    q: "Do I need my own API key?",
    a: "Yes. Folio is bring-your-own-key. You paste a Hugging Face token during setup, pick Groq, Cerebras, or Auto, and Folio uses that token for every answer. You are billed by the provider, not by Folio for inference.",
  },
  {
    q: "Which files can I upload?",
    a: "PDF, Word (.docx), plain text, and Markdown, up to 10 MB each. Folio splits each file into passages, indexes them for your account only, and keeps the original filename and page or section for citations.",
  },
  {
    q: "How do citations work?",
    a: "Answers are grounded in retrieved passages. Each claim that comes from a file is marked with a number. Click the number to see the document name, page or section, and the passage itself. If the model cannot find it in your files, it should say so rather than invent a source.",
  },
  {
    q: "Who can see my documents?",
    a: "Only your account. Each user gets a separate index. Other people’s questions never search your passages, and your questions never search theirs. Folio does not train models on your files.",
  },
  {
    q: "How is my Hugging Face token stored?",
    a: "The token is encrypted at rest. After you save it, Folio only ever shows the last four characters. You can replace it at any time from Settings. Folio never stores it in plain text in the browser after you submit it.",
  },
  {
    q: "Which models can I use?",
    a: "Whatever the backend lists for Groq and Cerebras, plus Auto, which picks a working model for you. You can switch provider and model in Settings without re-uploading documents.",
  },
  {
    q: "What happens if I change providers?",
    a: "Your documents stay. Only the model that writes the next answer changes. Citations still point at the same passages because retrieval happens against your index, not the provider.",
  },
  {
    q: "Can I delete files or chats?",
    a: "Yes. Documents can be removed from the Documents page, which drops them from your index. Chat sessions can be renamed or deleted from History. Deleting a document means later answers will not cite it.",
  },
  {
    q: "What if a document is still indexing?",
    a: "Large files take a short while to split and index. You can keep chatting with files that are already ready. Folio shows indexing status on each document and warns in chat when some files are still processing.",
  },
];

export default function Faq() {
  return (
    <div className="divide-y divide-hairline border-y border-hairline">
      {FAQS.map((item) => (
        <details key={item.q} className="group py-6">
          <summary className="flex cursor-pointer list-none items-start justify-between gap-6 text-left marker:content-none [&::-webkit-details-marker]:hidden">
            <span className="display-sm text-ink">{item.q}</span>
            <span
              aria-hidden="true"
              className="mt-1 grid size-7 shrink-0 place-items-center rounded-full text-lg leading-none text-muted transition-transform group-open:rotate-45"
            >
              +
            </span>
          </summary>
          <p className="mt-4 max-w-2xl text-sm leading-relaxed text-body">{item.a}</p>
        </details>
      ))}
    </div>
  );
}
