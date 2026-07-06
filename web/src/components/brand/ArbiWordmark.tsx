import { NucleusMark } from './NucleusMark';

// Arbi wordmark: "Arbi" in Manrope 700 followed by the Nucleus mark as a brand
// accent. The mark sizes to ~0.4em so its core ≈ the x-height of the letters.
interface ArbiWordmarkProps {
  size?: number;
  spinSeconds?: number;
  className?: string;
}

export function ArbiWordmark({ size = 32, spinSeconds = 20, className = '' }: ArbiWordmarkProps) {
  const markSize = Math.round(size * 0.4);
  return (
    <span className={`wordmark ${className}`.trim()} style={{ fontSize: `${size}px` }} aria-label="Arbi">
      <span>Arbi</span>
      <span className="wordmark__mark">
        <NucleusMark size={markSize} spinSeconds={spinSeconds} />
      </span>
    </span>
  );
}
