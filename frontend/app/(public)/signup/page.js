import AuthPage from "@/components/auth/AuthPage";

export const metadata = { title: "Create account · Folio" };

export default function SignupPage() {
  return <AuthPage mode="signup" />;
}
