import { Suspense } from "react";
import TokenStep from "@/components/onboarding/TokenStep";
import { PageLoader } from "@/components/ui/Spinner";

export const instant = false;
export const metadata = { title: "Connect your key · Folio" };

export default function TokenStepPage() {
  return (
    <Suspense fallback={<PageLoader />}>
      <TokenStep />
    </Suspense>
  );
}
