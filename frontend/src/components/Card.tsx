import React from "react";

interface Props {
  children: React.ReactNode;
  className?: string;
  style?: React.CSSProperties;
  id?: string;
}

export default function Card({ children, className, style, id }: Props) {
  return (
    <div
      id={id}
      className={className}
      style={{
        background: "#fff",
        border: "1.5px solid #E2E8F0",
        borderRadius: 20,
        padding: 24,
        boxShadow: "0 1px 3px rgba(15,23,42,0.05)",
        ...style,
      }}
    >
      {children}
    </div>
  );
}
