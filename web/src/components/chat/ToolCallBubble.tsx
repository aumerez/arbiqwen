import { AlertCircle, Check, Clock, Plug, Zap } from 'lucide-react';
import type { ChatToolCall } from '../../chat/types';

// Tool-call card, ported from the desktop ToolCallBubble (header only): an icon +
// type label (Integration / Skill / API Call) + the operation, with a status on
// the right — pending (clock), success (check + counts/timing), or error.
export function ToolCallBubble({ tool }: { tool: ChatToolCall }) {
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

  return (
    <div className={`toolcall${isError ? ' toolcall--error' : ''}`}>
      <div className="toolcall__left">
        <Icon size={14} className="toolcall__icon" />
        <span className="toolcall__label">{label}</span>
        {sublabel && <span className="toolcall__op">{sublabel}</span>}
      </div>
      <div className="toolcall__right">
        {!result && <Clock size={12} className="toolcall__pending" />}
        {result && !isError && (
          <>
            <Check size={12} className="toolcall__ok" />
            {result.recordCount != null && <span className="toolcall__meta">{result.recordCount} items</span>}
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
      </div>
    </div>
  );
}
