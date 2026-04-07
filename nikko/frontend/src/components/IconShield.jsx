import React from "react";

function IconShield({ size = 26, color = "white" }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path
        d="M12 2.7c.2 0 .4.04.58.11l7 2.8c.54.22.9.75.9 1.33v5.52c0 5.2-3.55 9.5-8.35 10.94a1.9 1.9 0 0 1-1.06 0C6.27 21.97 2.72 17.67 2.72 12.46V6.94c0-.58.35-1.11.9-1.33l7-2.8c.18-.07.38-.11.58-.11Z"
        stroke={color}
        strokeWidth="2"
        strokeLinejoin="round"
      />
    </svg>
  );
}

export default IconShield;
