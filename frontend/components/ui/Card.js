export default function Card({ className = "", children, ...props }) {
  return (
    <div className={`rounded-2xl border border-hairline bg-card ${className}`} {...props}>
      {children}
    </div>
  );
}
