import type { ReactNode } from 'react';

export default function FeatureGate({
  plan,
  allow,
  children,
  fallback = null,
}: {
  plan: 'simple' | 'pro';
  allow: Array<'simple' | 'pro'>;
  children: ReactNode;
  fallback?: ReactNode;
}) {
  if (!allow.includes(plan)) return <>{fallback}</>;
  return <>{children}</>;
}
