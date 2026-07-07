import type { CSSProperties } from 'react';

// The Nucleus mark, ported from the desktop brand: a teal core with three
// orbiting satellites that spin as ambient brand motion.
interface NucleusMarkProps {
  size?: number;
  color?: string;
  animated?: boolean;
  spinSeconds?: number;
}

export function NucleusMark({ size = 24, color = '#14B8A6', animated = true, spinSeconds = 20 }: NucleusMarkProps) {
  const style = animated ? ({ ['--arbi-spin-seconds']: `${spinSeconds}s` } as CSSProperties) : undefined;
  return (
    <svg className="nucleus" viewBox="0 0 100 100" width={size} height={size} aria-hidden="true" style={style}>
      <g className={animated ? 'nucleus__satellites' : undefined}>
        <circle cx="50" cy="8" r="6" fill={color} opacity="0.9" />
        <circle cx="90" cy="68" r="5" fill={color} opacity="0.7" />
        <circle cx="14" cy="74" r="4" fill={color} opacity="0.55" />
      </g>
      <circle cx="50" cy="50" r="28" fill={color} />
    </svg>
  );
}
