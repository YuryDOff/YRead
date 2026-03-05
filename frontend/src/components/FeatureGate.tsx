import { useAuth } from '../context/AuthContext';

interface FeatureGateProps {
  plan: 'pro';
  fallback?: React.ReactNode;
  children: React.ReactNode;
}

/**
 * Gates children behind a plan tier check.
 * Reads user.plan from AuthContext — set by login response / JWT claim.
 *
 * Usage:
 *   <FeatureGate plan="pro" fallback={<UpgradeBanner feature="Advanced prompt editing" />}>
 *     <Panel A content />
 *   </FeatureGate>
 */
export function FeatureGate({ plan, fallback = null, children }: FeatureGateProps) {
  const { user } = useAuth();

  if (plan === 'pro' && user?.plan !== 'pro') {
    return <>{fallback}</>;
  }

  return <>{children}</>;
}

interface UpgradeBannerProps {
  feature: string;
}

export function UpgradeBanner({ feature }: UpgradeBannerProps) {
  return (
    <div className="rounded-md border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
      <span className="font-medium">{feature}</span> is available on the Pro plan.{' '}
      <a href="/upgrade" className="underline">
        Upgrade
      </a>
    </div>
  );
}
