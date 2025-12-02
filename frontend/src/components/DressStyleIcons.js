import React from 'react';
import './DressStyleIcons.css';

// SVG Icons for dress styles
export const ScoopIcon = ({ size = 24, className = '' }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" className={`dress-icon ${className}`} fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M12 4C8 4 6 6 6 10V20H18V10C18 6 16 4 12 4Z" stroke="currentColor" strokeWidth="2" fill="none"/>
    <path d="M6 10C6 8 7 7 9 7H15C17 7 18 8 18 10" stroke="currentColor" strokeWidth="2" fill="none"/>
  </svg>
);

export const BowIcon = ({ size = 24, className = '' }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" className={`dress-icon ${className}`} fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M12 6C10 6 9 7 9 9C9 11 10 12 12 12C14 12 15 11 15 9C15 7 14 6 12 6Z" stroke="currentColor" strokeWidth="2" fill="none"/>
    <path d="M9 9L7 11M15 9L17 11" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
    <path d="M7 11L7 13M17 11L17 13" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
  </svg>
);

export const PaddingIcon = ({ size = 24, className = '' }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" className={`dress-icon ${className}`} fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M12 4C8 4 6 6 6 10V20H18V10C18 6 16 4 12 4Z" stroke="currentColor" strokeWidth="2" fill="none"/>
    <path d="M8 8C8 9 9 10 10 10H14C15 10 16 9 16 8" stroke="currentColor" strokeWidth="2" fill="none"/>
    <circle cx="10" cy="9" r="1.5" fill="currentColor" opacity="0.3"/>
    <circle cx="14" cy="9" r="1.5" fill="currentColor" opacity="0.3"/>
  </svg>
);

export const SlitIcon = ({ size = 24, className = '' }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" className={`dress-icon ${className}`} fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M12 4C8 4 6 6 6 10V20H18V10C18 6 16 4 12 4Z" stroke="currentColor" strokeWidth="2" fill="none"/>
    <path d="M15 14L15 20" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
    <path d="M14 14L16 14" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
  </svg>
);

export const VNeckIcon = ({ size = 24, className = '' }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" className={`dress-icon ${className}`} fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M12 4C8 4 6 6 6 10V20H18V10C18 6 16 4 12 4Z" stroke="currentColor" strokeWidth="2" fill="none"/>
    <path d="M9 8L12 12L15 8" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
  </svg>
);

export const RoundNeckIcon = ({ size = 24, className = '' }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" className={`dress-icon ${className}`} fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M12 4C8 4 6 6 6 10V20H18V10C18 6 16 4 12 4Z" stroke="currentColor" strokeWidth="2" fill="none"/>
    <path d="M9 8C9 9 10 10 12 10C14 10 15 9 15 8" stroke="currentColor" strokeWidth="2" fill="none"/>
  </svg>
);

// Voice control icons
export const MicrophoneIcon = ({ size = 20, className = '' }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" className={`dress-icon ${className}`} fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M12 1C10.34 1 9 2.34 9 4V12C9 13.66 10.34 15 12 15C13.66 15 15 13.66 15 12V4C15 2.34 13.66 1 12 1Z" stroke="currentColor" strokeWidth="2" fill="none"/>
    <path d="M19 10V12C19 15.87 15.87 19 12 19C8.13 19 5 15.87 5 12V10" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
    <path d="M12 19V23M8 23H16" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
  </svg>
);

export const SpeakerIcon = ({ size = 20, className = '' }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" className={`dress-icon ${className}`} fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M3 9V15H7L12 20V4L7 9H3Z" stroke="currentColor" strokeWidth="2" fill="none"/>
    <path d="M16 10C16.5 10.5 17 11.5 17 12.5C17 13.5 16.5 14.5 16 15" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
    <path d="M19 7C20 8 21 10 21 12.5C21 15 20 17 19 18" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
  </svg>
);

export const SpeakerOffIcon = ({ size = 20, className = '' }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" className={`dress-icon ${className}`} fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M3 9V15H7L12 20V4L7 9H3Z" stroke="currentColor" strokeWidth="2" fill="none"/>
    <path d="M16 10L21 5M21 10L16 15" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
  </svg>
);

export const StopIcon = ({ size = 20, className = '' }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" className={`dress-icon ${className}`} fill="currentColor" xmlns="http://www.w3.org/2000/svg">
    <rect x="6" y="6" width="12" height="12" rx="2"/>
  </svg>
);

export const PlayIcon = ({ size = 20, className = '' }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" className={`dress-icon ${className}`} fill="currentColor" xmlns="http://www.w3.org/2000/svg">
    <path d="M8 5V19L19 12L8 5Z"/>
  </svg>
);

// Icon mapping for styles
export const getDressStyleIcon = (style) => {
  const styleLower = (style || '').toLowerCase();
  if (styleLower.includes('scoop')) return ScoopIcon;
  if (styleLower.includes('bow')) return BowIcon;
  if (styleLower.includes('padding') || styleLower.includes('padded')) return PaddingIcon;
  if (styleLower.includes('slit')) return SlitIcon;
  if (styleLower.includes('v-neck') || styleLower.includes('vneck')) return VNeckIcon;
  if (styleLower.includes('round') || styleLower.includes('crew')) return RoundNeckIcon;
  return null;
};

