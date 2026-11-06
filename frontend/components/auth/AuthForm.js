"use client";

import Link from "next/link";
import { useState } from "react";
import { useForm } from "react-hook-form";
import Alert from "@/components/ui/Alert";
import Button from "@/components/ui/Button";
import Input, { Field } from "@/components/ui/Input";
import { useAuth } from "@/hooks/useAuth";
import { getErrorMessage } from "@/lib/api";

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

const COPY = {
  signup: {
    eyebrow: "Get started",
    title: "Create your Folio account",
    subtitle: "Upload documents, bring your own key, and get cited answers.",
    submit: "Create account",
    switchText: "Already have an account?",
    switchLabel: "Sign in",
    switchHref: "/signin",
  },
  signin: {
    eyebrow: "Welcome back",
    title: "Sign in to Folio",
    subtitle: "Continue chatting with your documents.",
    submit: "Sign in",
    switchText: "New to Folio?",
    switchLabel: "Create an account",
    switchHref: "/signup",
  },
};

export default function AuthForm({ mode }) {
  const copy = COPY[mode];
  const { signin, signup } = useAuth();
  const [serverError, setServerError] = useState("");
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm({ mode: "onTouched" });

  // On success the auth store updates and AuthGuard (guest mode) routes the user onward.
  const onSubmit = async ({ email, password }) => {
    setServerError("");
    try {
      if (mode === "signup") await signup(email, password);
      else await signin(email, password);
    } catch (error) {
      setServerError(getErrorMessage(error));
    }
  };

  return (
    <div className="w-full">
      <p className="caption-upper text-muted">{copy.eyebrow}</p>
      <h1 className="display-lg mt-3 text-ink">{copy.title}</h1>
      <p className="mt-3 text-[15px] leading-relaxed text-body">{copy.subtitle}</p>

      <form onSubmit={handleSubmit(onSubmit)} noValidate className="mt-8 space-y-5">
        <Alert>{serverError}</Alert>

        <Field label="Email" htmlFor="email" error={errors.email?.message}>
          <Input
            id="email"
            type="email"
            autoComplete="email"
            placeholder="you@company.com"
            invalid={!!errors.email}
            {...register("email", {
              required: "Enter your email address.",
              pattern: { value: EMAIL_PATTERN, message: "Enter a valid email address." },
            })}
          />
        </Field>

        <Field
          label="Password"
          htmlFor="password"
          error={errors.password?.message}
          hint={mode === "signup" ? "At least 8 characters." : undefined}
        >
          <Input
            id="password"
            type="password"
            autoComplete={mode === "signup" ? "new-password" : "current-password"}
            invalid={!!errors.password}
            {...register("password", {
              required: "Enter your password.",
              ...(mode === "signup" && {
                minLength: { value: 8, message: "Use at least 8 characters." },
                maxLength: { value: 128, message: "Use at most 128 characters." },
                validate: (v) => v.trim().length > 0 || "Password cannot be only spaces.",
              }),
            })}
          />
        </Field>

        {mode === "signup" && (
          <Field label="Confirm password" htmlFor="confirm" error={errors.confirm?.message}>
            <Input
              id="confirm"
              type="password"
              autoComplete="new-password"
              invalid={!!errors.confirm}
              {...register("confirm", {
                required: "Confirm your password.",
                validate: (value, values) => value === values.password || "Passwords don't match.",
              })}
            />
          </Field>
        )}

        <Button type="submit" loading={isSubmitting} className="w-full">
          {copy.submit}
        </Button>
      </form>

      <p className="mt-6 text-center text-sm text-muted">
        {copy.switchText}{" "}
        <Link href={copy.switchHref} className="font-medium text-ink underline decoration-hairline-strong underline-offset-4 hover:decoration-ink">
          {copy.switchLabel}
        </Link>
      </p>
    </div>
  );
}
