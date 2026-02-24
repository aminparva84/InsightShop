import React, { useRef, useState, useEffect } from 'react';
import WavyUnderline from './WavyUnderline';
import SectionTitleCurvedLine from './SectionTitleCurvedLine';

/**
 * Section title (e.g. "Featured Products", "Special offers") with a wavy underline
 * whose width matches the title text width. Uses ResizeObserver to keep in sync.
 */
const SectionTitleWithWavy = ({ title, wavyColor = '#373F2E' }) => {
  const titleRef = useRef(null);
  const [titleWidth, setTitleWidth] = useState(null);

  useEffect(() => {
    const el = titleRef.current;
    if (!el) return;

    const updateWidth = () => {
      setTitleWidth(el.offsetWidth);
    };

    updateWidth();
    const ro = new ResizeObserver(updateWidth);
    ro.observe(el);
    return () => ro.disconnect();
  }, [title]);

  return (
    <div className="section-title-row">
      <div className="section-title-and-wavy">
        <h2 ref={titleRef} className="section-title">
          {title}
        </h2>
        <WavyUnderline
          color={wavyColor}
          className="section-title-wavy"
          width={titleWidth != null ? titleWidth : '100%'}
        />
      </div>
      <SectionTitleCurvedLine color={wavyColor} />
    </div>
  );
};

export default SectionTitleWithWavy;
