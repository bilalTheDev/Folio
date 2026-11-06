"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import DocumentList from "@/components/documents/DocumentList";
import Dropzone from "@/components/documents/Dropzone";
import Alert from "@/components/ui/Alert";
import Button from "@/components/ui/Button";
import { PageLoader } from "@/components/ui/Spinner";
import { useAuth } from "@/hooks/useAuth";
import { useDocuments } from "@/hooks/useDocuments";
import { getErrorMessage } from "@/lib/api";
import { nextOnboardingRoute } from "@/lib/routes";

export default function UploadStep() {
  const router = useRouter();
  const { reloadUser } = useAuth();
  const { documents, loading, error, refresh, upload, remove } = useDocuments();
  const [continuing, setContinuing] = useState(false);
  const [continueError, setContinueError] = useState("");

  const usable = documents.filter((d) => d.status !== "failed");

  const handleContinue = async () => {
    setContinuing(true);
    setContinueError("");
    try {
      const user = await reloadUser();
      if (!user.onboarding?.has_document) {
        setContinueError("Upload at least one document before continuing.");
        return;
      }
      router.push(nextOnboardingRoute(user));
    } catch (err) {
      setContinueError(getErrorMessage(err));
    } finally {
      setContinuing(false);
    }
  };

  return (
    <div>
      <p className="caption-upper text-muted">Step 1 of 3</p>
      <h1 className="display-md mt-3 text-ink">Upload your documents</h1>
      <p className="mt-3 max-w-xl text-[15px] leading-relaxed text-body">
        Folio answers only from what you upload here. Files are stored privately for your account and indexed
        so answers can cite the exact passage. You can add or remove documents later.
      </p>

      <div className="mt-8">
        <Dropzone onUpload={upload} />
      </div>

      <div className="mt-8">
        {loading ? (
          <PageLoader label="Loading your documents…" />
        ) : error ? (
          <Alert
            action={
              <button onClick={refresh} className="shrink-0 font-medium underline">
                Retry
              </button>
            }
          >
            {error}
          </Alert>
        ) : (
          documents.length > 0 && (
            <>
              <h2 className="mb-3 text-sm font-medium text-ink">
                Uploaded <span className="text-muted-soft">({documents.length})</span>
              </h2>
              <DocumentList documents={documents} onRemove={remove} />
            </>
          )
        )}
      </div>

      <div className="mt-10 flex flex-col items-end gap-3 border-t border-hairline pt-6">
        <Alert className="w-full">{continueError}</Alert>
        <div className="flex items-center gap-4">
          {usable.length === 0 && !loading && (
            <span className="text-sm text-muted">Upload at least one document to continue.</span>
          )}
          <Button onClick={handleContinue} disabled={usable.length === 0} loading={continuing}>
            Continue
          </Button>
        </div>
      </div>
    </div>
  );
}
