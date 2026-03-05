import { describe, it, expect } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import CoverBriefEditor from '../components/CoverBriefEditor';
import { makeBookContextWrapper, makeAuthWrapper } from './test-wrappers';

const mockCoverAnalysis = {
  id: 1,
  book_id: 1,
  cover_t2i_prompt: 'A merged prompt',
  reference_style_template: 'Style template text',
  reference_image_url: null,
} as Parameters<typeof CoverBriefEditor>[0]['coverAnalysis'];

describe('CoverBriefEditor', () => {
  it('simple tier hides prompt panels', () => {
    const Wrapper = makeBookContextWrapper({ workflowType: 'cover_only' });
    render(
      <Wrapper>
        <CoverBriefEditor
          bookId={1}
          analysisMode="simple"
          coverAnalysis={mockCoverAnalysis}
          characters={[]}
          locations={[]}
          artefacts={[]}
        />
      </Wrapper>
    );
    expect(screen.queryByText(/Advanced/i)).not.toBeInTheDocument();
    expect(screen.queryByLabelText(/Merged Prompt/i)).not.toBeInTheDocument();
  });

  it('pro tier shows Panel B always visible', () => {
    const AuthW = makeAuthWrapper({ plan: 'pro' });
    const BookW = makeBookContextWrapper({ workflowType: 'full_book' });
    render(
      <AuthW>
        <BookW>
          <CoverBriefEditor
            bookId={1}
            analysisMode="pro"
            coverAnalysis={mockCoverAnalysis}
            characters={[]}
            locations={[]}
            artefacts={[]}
          />
        </BookW>
      </AuthW>
    );
    expect(screen.getByLabelText(/Merged Prompt/i)).toBeInTheDocument();
  });

  it('Advanced toggle expands Panel A', () => {
    const AuthW = makeAuthWrapper({ plan: 'pro' });
    const BookW = makeBookContextWrapper({ workflowType: 'full_book' });
    render(
      <AuthW>
        <BookW>
          <CoverBriefEditor
            bookId={1}
            analysisMode="pro"
            coverAnalysis={mockCoverAnalysis}
            characters={[]}
            locations={[]}
            artefacts={[]}
          />
        </BookW>
      </AuthW>
    );
    fireEvent.click(screen.getByText(/Advanced/i));
    expect(screen.getAllByText(/Style Template/i).length).toBeGreaterThan(0);
  });

  it('panel A expansion state saved to localStorage', () => {
    localStorage.removeItem('noctua_panel_a_expanded');
    const AuthW = makeAuthWrapper({ plan: 'pro' });
    const BookW = makeBookContextWrapper({ workflowType: 'full_book' });
    render(
      <AuthW>
        <BookW>
          <CoverBriefEditor
            bookId={1}
            analysisMode="pro"
            coverAnalysis={mockCoverAnalysis}
            characters={[]}
            locations={[]}
            artefacts={[]}
          />
        </BookW>
      </AuthW>
    );
    fireEvent.click(screen.getByText(/Advanced/i));
    expect(localStorage.getItem('noctua_panel_a_expanded')).toBe('true');
  });

  it('negative prompt field gated behind FeatureGate', () => {
    const AuthW = makeAuthWrapper({ plan: 'simple' });
    const BookW = makeBookContextWrapper({ workflowType: 'full_book' });
    render(
      <AuthW>
        <BookW>
          <CoverBriefEditor
            bookId={1}
            analysisMode="pro"
            coverAnalysis={mockCoverAnalysis}
            characters={[]}
            locations={[]}
            artefacts={[]}
          />
        </BookW>
      </AuthW>
    );
    expect(screen.queryByLabelText(/Negative prompt/i)).not.toBeInTheDocument();
  });
});
