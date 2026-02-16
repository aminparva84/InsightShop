import { useRef, useEffect, useState } from 'react';
import { gsap } from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import { useGSAP } from '@gsap/react';

gsap.registerPlugin(ScrollTrigger, useGSAP);

/**
 * SplitText – animated text split by chars/words/lines.
 * Uses GSAP + ScrollTrigger (no premium SplitText plugin).
 */
const SplitText = ({
  text,
  className = '',
  delay = 50,
  duration = 1.25,
  ease = 'power3.out',
  splitType = 'chars',
  from = { opacity: 0, y: 40 },
  to = { opacity: 1, y: 0 },
  threshold = 0.1,
  rootMargin = '-100px',
  textAlign = 'center',
  tag = 'p',
  onLetterAnimationComplete,
  showCallback = true,
}) => {
  const ref = useRef(null);
  const animationCompletedRef = useRef(false);
  const onCompleteRef = useRef(onLetterAnimationComplete);
  const [fontsLoaded, setFontsLoaded] = useState(false);

  useEffect(() => {
    onCompleteRef.current = onLetterAnimationComplete;
  }, [onLetterAnimationComplete]);

  useEffect(() => {
    if (document.fonts && document.fonts.status === 'loaded') {
      setFontsLoaded(true);
    } else if (document.fonts && document.fonts.ready) {
      document.fonts.ready.then(() => setFontsLoaded(true));
    } else {
      setFontsLoaded(true);
    }
  }, []);

  const splitIntoChunks = (str) => {
    if (splitType === 'chars') {
      return str.split('').map((char) => (char === ' ' ? '\u00A0' : char));
    }
    if (splitType === 'words') {
      return str.split(/(\s+)/).filter(Boolean);
    }
    if (splitType === 'lines') {
      return str.split(/\n/).filter((line) => line.length > 0);
    }
    return str.split('').map((char) => (char === ' ' ? '\u00A0' : char));
  };

  const chunks = text ? splitIntoChunks(text) : [];
  const isLines = splitType === 'lines';
  const wrapperClass = isLines ? 'split-line' : splitType === 'words' ? 'split-word' : 'split-char';

  useGSAP(
    () => {
      if (!ref.current || !chunks.length || !fontsLoaded) return;
      if (animationCompletedRef.current) return;

      const el = ref.current;
      const targets = el.querySelectorAll(`.${wrapperClass}`);

      if (!targets.length) return;

      const startPct = (1 - threshold) * 100;
      const marginMatch = /^(-?\d+(?:\.\d+)?)(px|em|rem|%)?$/.exec(rootMargin);
      const marginValue = marginMatch ? parseFloat(marginMatch[1]) : 0;
      const marginUnit = marginMatch ? marginMatch[2] || 'px' : 'px';
      const sign =
        marginValue === 0
          ? ''
          : marginValue < 0
            ? `-=${Math.abs(marginValue)}${marginUnit}`
            : `+=${marginValue}${marginUnit}`;
      const start = `top ${startPct}%${sign}`;

      const tween = gsap.fromTo(
        targets,
        { ...from },
        {
          ...to,
          duration,
          ease,
          stagger: delay / 1000,
          scrollTrigger: {
            trigger: el,
            start,
            once: true,
            fastScrollEnd: true,
            anticipatePin: 0.4,
          },
          onComplete: () => {
            animationCompletedRef.current = true;
            if (showCallback) {
              onCompleteRef.current?.();
            }
          },
          willChange: 'transform, opacity',
          force3D: true,
        }
      );

      return () => {
        ScrollTrigger.getAll().forEach((st) => {
          if (st.trigger === el) st.kill();
        });
        tween.kill();
      };
    },
    {
      dependencies: [
        text,
        delay,
        duration,
        ease,
        splitType,
        JSON.stringify(from),
        JSON.stringify(to),
        threshold,
        rootMargin,
        fontsLoaded,
      ],
      scope: ref,
    }
  );

  const style = {
    textAlign,
    overflow: 'hidden',
    display: isLines ? 'block' : 'inline-block',
    whiteSpace: isLines ? 'normal' : 'normal',
    wordWrap: 'break-word',
    willChange: 'transform, opacity',
  };

  const Tag = tag || 'p';
  const containerClass = `split-parent ${className}`.trim();

  if (!text) {
    return (
      <Tag ref={ref} style={style} className={containerClass}>
        {''}
      </Tag>
    );
  }

  return (
    <Tag ref={ref} style={style} className={containerClass}>
      {isLines
        ? chunks.map((line, i) => (
            <span key={i} className="split-line" style={{ display: 'block' }}>
              {line}
            </span>
          ))
        : chunks.map((chunk, i) => (
            <span key={i} className={wrapperClass} style={{ display: 'inline' }}>
              {chunk}
            </span>
          ))}
    </Tag>
  );
};

export default SplitText;
