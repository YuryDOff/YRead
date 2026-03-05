import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { FeatureGate } from '../components/FeatureGate';
import CreateBookPage from '../pages/SetupPage';
import { makeAuthWrapper, makeBookContextWrapper } from './test-wrappers';

describe('FeatureGate', () => {
  it('renders children for pro user', () => {
    const Wrapper = makeAuthWrapper({ plan: 'pro' });
    render(
      <Wrapper>
        <FeatureGate plan="pro">
          <span>Pro content</span>
        </FeatureGate>
      </Wrapper>
    );
    expect(screen.getByText('Pro content')).toBeInTheDocument();
  });

  it('renders fallback for simple user', () => {
    const Wrapper = makeAuthWrapper({ plan: 'simple' });
    render(
      <Wrapper>
        <FeatureGate plan="pro" fallback={<span>Upgrade banner</span>}>
          <span>Pro content</span>
        </FeatureGate>
      </Wrapper>
    );
    expect(screen.getByText('Upgrade banner')).toBeInTheDocument();
    expect(screen.queryByText('Pro content')).not.toBeInTheDocument();
  });

  it('workflow selector renders Full Book disabled for simple user', () => {
    const AuthWrapper = makeAuthWrapper({ plan: 'simple' });
    const BookWrapper = makeBookContextWrapper({ book: null });
    render(
      <AuthWrapper>
        <BookWrapper>
          <CreateBookPage />
        </BookWrapper>
      </AuthWrapper>
    );
    const fullBookRadio = screen.getByRole('radio', { name: /Full Book/i });
    expect(fullBookRadio).toBeDisabled();
  });
});
