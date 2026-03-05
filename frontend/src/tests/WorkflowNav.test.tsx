import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import WorkflowNav from '../components/WorkflowNav';
import { makeBookContextWrapper } from './test-wrappers';

describe('WorkflowNav', () => {
  it('cover_only path shows Typography step not Preview', () => {
    const Wrapper = makeBookContextWrapper({ workflowType: 'cover_only' });
    render(
      <Wrapper>
        <WorkflowNav />
      </Wrapper>
    );
    expect(screen.getByText('Typography')).toBeInTheDocument();
    expect(screen.queryByText('Preview')).not.toBeInTheDocument();
  });

  it('full_book path includes Preview step', () => {
    const Wrapper = makeBookContextWrapper({ workflowType: 'full_book' });
    render(
      <Wrapper>
        <WorkflowNav />
      </Wrapper>
    );
    expect(screen.getByText('Preview')).toBeInTheDocument();
  });
});
