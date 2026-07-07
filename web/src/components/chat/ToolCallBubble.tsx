import { useState } from 'react';
import { AlertCircle, Check, ChevronDown, ChevronRight, Clock, Plug, Zap } from 'lucide-react';
import type { ChatToolCall } from '../../chat/types';

// Tool-call card, ported from the desktop ToolCallBubble: a header (icon + type
// label + operation) with a right-side status (pending clock / success check +
// counts/timing / error), expandable to show the call input and result preview.
function formatSize(chars: number): string {
  return chars < 1024 ? `${chars} chars` : `${(chars / 1024).toFixed(1)} KB`;
}

export function ToolCallBubble({ tool }: { tool: ChatToolCall }) {
  const [expanded, setExpanded] = useState(false);
  const isSkill = !!tool.skillKey || tool.toolName?.startsWith('skill_');
  const isIntegration = !!tool.integrationKey;
  const result = tool.result;
  const isError = !!result?.error;

  const label = isIntegration ? 'Integration' : isSkill ? 'Skill' : 'API Call';
  const Icon = isIntegration ? Plug : Zap;
  const sublabel = isSkill
    ? tool.toolName?.replace('skill_', '').replace(/_/g, ' ')
    : isIntegration
      ? tool.toolName?.replace(/_/g, ' ')
      : tool.operationId;

  const hasInput = !!tool.input && Object.keys(tool.input).length > 0;
  const hasDetails = hasInput || !!result?.preview || !!result?.rawPreview;

  return (
    <div className={`toolcall${isError ? ' toolcall--error' : ''}`}>
      <button type="button" className="toolcall__header" onClick={() => setExpanded((e) => !e)} aria-expanded={expanded}>
        <span className="toolcall__left">
          <Icon size={14} className="toolcall__icon" />
          <span className="toolcall__label">{label}</span>
          {sublabel && <span className="toolcall__op">{sublabel}</span>}
        </span>
        <span className="toolcall__right">
          {!result && <Clock size={12} className="toolcall__pending" />}
          {result && !isError && (
            <>
              <Check size={12} className="toolcall__ok" />
              {result.recordCount != null && <span className="toolcall__meta">{result.recordCount} items</span>}
              {result.sizeChars != null && result.sizeChars > 0 && (
                <span className="toolcall__meta">{formatSize(result.sizeChars)}</span>
              )}
              {!isSkill && !isIntegration && result.statusCode != null && (
                <span className="toolcall__status">{result.statusCode}</span>
              )}
              {result.durationMs != null && result.durationMs > 0 && (
                <span className="toolcall__meta">{result.durationMs}ms</span>
              )}
            </>
          )}
          {isError && (
            <>
              <AlertCircle size={12} className="toolcall__err" />
              <span className="toolcall__errtext">{result?.error}</span>
            </>
          )}
          {hasDetails && (expanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />)}
        </span>
      </button>

      {expanded && hasDetails && (
        <div className="toolcall__details">
          {hasInput && (
            <div className="toolcall__section">
              <span className="toolcall__seclabel">Input</span>
              <pre className="toolcall__code">{JSON.stringify(tool.input, null, 2)}</pre>
            </div>
          )}
          {result?.preview && (
            <div className="toolcall__section">
              <span className="toolcall__seclabel">Result preview</span>
              <pre className="toolcall__code">{result.preview}</pre>
            </div>
          )}
          {result?.rawPreview && (
            <details className="toolcall__raw">
              <summary className="toolcall__rawsummary">Raw response (JSON)</summary>
              <pre className="toolcall__code">{result.rawPreview}</pre>
            </details>
          )}
        </div>
      )}
    </div>
  );
}
